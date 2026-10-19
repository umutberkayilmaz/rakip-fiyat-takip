import importlib.util
import io
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import altair as alt
import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

# tasarim.py her zaman bu dosyanın yanındaki kopyadan ve güncel haliyle yüklenir
# (repoda başka bir yerde eski bir tasarim.py olsa ya da sunucu eski sürümü hafızada tutsa bile).
_TASARIM_YOLU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasarim.py")


def _tasarim_yukle():
    zaman = os.path.getmtime(_TASARIM_YOLU)
    modul = sys.modules.get("rakip_tasarim")
    if modul is None or getattr(modul, "_yuklenme_zamani", None) != zaman:
        spec = importlib.util.spec_from_file_location("rakip_tasarim", _TASARIM_YOLU)
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        modul._yuklenme_zamani = zaman
        sys.modules["rakip_tasarim"] = modul
    return modul


tasarim = _tasarim_yukle()

# ================= SAYFA AYARLARI =================
st.set_page_config(page_title="Rakip Fiyat Takibi", page_icon="📊", layout="wide")

GSHEET_NAME = "Rakip_Fiyat_Takip"      # tarama script'inin yazdığı Google Sheet
WS_GUNCEL = "Guncel"
WS_GECMIS = "Gecmis"
WS_DURUM = "Durum"
GECIKME_ESIGI_DK = 120                 # tarama (saat başı) bundan eskiyse panel uyarı gösterir
ACILIS_ANIMASYONU = True               # sayfa açılınca/yenilenince düello animasyonu (kapatmak için False)

# Bilgisayarda Google bağlantısı olmadan denemek için: RAKIP_YEREL_EXCEL=..\Rakip_Fiyat_Guncel.xlsx
YEREL_EXCEL = os.environ.get("RAKIP_YEREL_EXCEL", "")

# Sheet başlığı -> panelin kullandığı alan adı (rakip_script.py'deki GUNCEL_BASLIKLAR ile aynı)
ALANLAR = {
    "Model": "model", "Ürün Adı": "ad", "Pazaryeri": "platform", "Satıcı": "satici",
    "Sayfadaki Satıcı Adı": "sayfa_satici", "Durum": "durum", "Liste Fiyatı": "liste", "Satış Fiyatı": "satis",
    "Sepette Fiyat": "sepette", "Sepet İndirimi": "sepet_indirimi", "Sepet Kampanyası": "sepet_kampanyasi",
    "Kupon": "kupon", "Kupon İndirimi": "kupon_indirimi", "Kuponlu Fiyat": "kuponlu", "Efektif Fiyat": "efektif",
    "Diğer Kampanyalar": "diger_kampanya", "Önceki Efektif Fiyat": "onceki_efektif",
    "Son Fiyat Değişimi": "son_degisim", "BuyBox Sahibi": "bb_sahibi", "BuyBox Fiyatı": "bb_fiyat",
    "BuyBox Bu Satıcıda": "bb_bizde", "Satıcı Sırası": "sira", "Satıcı Sayısı": "satici_sayisi",
    "Sayfadaki En Ucuz": "en_ucuz", "Sayfadaki En Ucuz Satıcı": "en_ucuz_satici",
    "Resmi Satıcı BuyBox'ta": "resmi_bb", "Link": "link", "Görsel": "gorsel", "Veri Zamanı": "veri_zamani",
    "Eski Veri": "eski_veri",
}
SAYI_ALANLARI = {"liste", "satis", "sepette", "sepet_indirimi", "kupon_indirimi", "kuponlu", "efektif",
                 "onceki_efektif", "bb_fiyat", "sira", "satici_sayisi", "en_ucuz"}


def simdi_tr():
    return (datetime.now(timezone.utc) + timedelta(hours=3)).replace(tzinfo=None)


# ================= GOOGLE SHEETS BAĞLANTISI =================
@st.cache_resource
def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except Exception as e:
        if not YEREL_EXCEL:
            st.error(f"Google Sheets bağlantı hatası: {e}")
        return None


def _sayfa_degerleri(ad):
    """Sheet sayfasını ham değerleriyle (sayılar sayı olarak) okur."""
    if YEREL_EXCEL:
        try:
            df = pd.read_excel(YEREL_EXCEL, sheet_name=ad, header=None, dtype=object)
            return [[("" if pd.isna(v) else v) for v in satir] for satir in df.values.tolist()]
        except Exception:
            return []
    client = get_gspread_client()
    if not client:
        return []
    try:
        return client.open(GSHEET_NAME).worksheet(ad).get_all_values(value_render_option="UNFORMATTED_VALUE")
    except gspread.WorksheetNotFound:
        return []


def _sayi(v):
    if v is None or v == "" or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("₺", "").replace("TL", "").strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


@st.cache_data(ttl=180)
def load_guncel():
    try:
        degerler = _sayfa_degerleri(WS_GUNCEL)
    except Exception as e:
        st.error(f"Veri okunurken hata: {e}")
        return [], ""
    if not degerler:
        return [], ""
    bas = [str(h).strip() for h in degerler[0]]
    guncelleme = next((h for h in bas if h.startswith("Son Güncelleme")), "")
    satirlar = []
    for ham in degerler[1:]:
        d = {}
        for i, h in enumerate(bas):
            alan = ALANLAR.get(h)
            if alan:
                v = ham[i] if i < len(ham) else ""
                d[alan] = _sayi(v) if alan in SAYI_ALANLARI else ("" if v is None else str(v).strip())
        if not d.get("model"):
            continue
        d["bb_bizde"] = d.get("bb_bizde") == "Evet"
        d["resmi_bb"] = d.get("resmi_bb") == "Evet"
        if d.get("sira") is not None:
            d["sira"] = int(d["sira"])
        if d.get("satici_sayisi") is not None:
            d["satici_sayisi"] = int(d["satici_sayisi"])
        d["_id"] = f'{d.get("platform")}|{d.get("model")}|{d.get("satici")}'
        d["_arama"] = " ".join(str(d.get(k, "")) for k in ("model", "ad", "satici", "sayfa_satici", "platform")).casefold()
        satirlar.append(d)
    return satirlar, guncelleme


@st.cache_data(ttl=180)
def load_gecmis():
    try:
        degerler = _sayfa_degerleri(WS_GECMIS)
    except Exception as e:
        st.error(f"Geçmiş okunurken hata: {e}")
        return pd.DataFrame()
    if not degerler or len(degerler) < 2:
        return pd.DataFrame()
    bas = [str(h).strip() for h in degerler[0]]
    df = pd.DataFrame([r + [""] * (len(bas) - len(r)) for r in degerler[1:]], columns=bas)
    df["Zaman_dt"] = pd.to_datetime(df["Zaman"].astype(str), format="%d.%m.%Y %H:%M", errors="coerce")
    for c in ("Satış Fiyatı", "Sepette Fiyat", "Kuponlu Fiyat", "Efektif Fiyat", "BuyBox Fiyatı"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].apply(_sayi), errors="coerce")
    for c in ("Kupon", "Sepet Kampanyası", "BuyBox Sahibi", "Değişen"):
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str)
    return df.dropna(subset=["Zaman_dt"])


@st.cache_data(ttl=180)
def load_durum():
    """Pazaryeri -> {durum, son_basarili, aciklama}. Sayfa yoksa boş."""
    try:
        degerler = _sayfa_degerleri(WS_DURUM)
    except Exception:
        return {}
    if not degerler or len(degerler) < 2:
        return {}
    h = [str(x).strip() for x in degerler[0]]
    sonuc = {}
    for satir in degerler[1:]:
        d = dict(zip(h, satir))
        ad = str(d.get("Platform", "")).strip()
        if ad:
            sonuc[ad] = {"durum": str(d.get("Durum", "Tamam")).strip() or "Tamam",
                         "son_basarili": str(d.get("Son Başarılı Tarama", "")).strip(),
                         "aciklama": str(d.get("Açıklama", "")).strip()}
    return sonuc


def tarama_yasi_dk(guncelleme_metni):
    """'Son Güncelleme: 19.10.2026 12:30' -> kaç dakika önce (Türkiye saati). Okunamazsa None."""
    m = re.search(r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})", str(guncelleme_metni or ""))
    if not m:
        return None
    try:
        t = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%d.%m.%Y %H:%M")
    except ValueError:
        return None
    return max(0, (simdi_tr() - t).total_seconds() / 60)


def _tarih_metni(guncelleme):
    m = re.search(r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})", str(guncelleme or ""))
    return f"{m.group(1)} · {m.group(2)}" if m else ""


def _zaman(metin):
    try:
        return datetime.strptime(str(metin)[:16], "%d.%m.%Y %H:%M")
    except ValueError:
        return None


def son_24s_degisenler(satirlar):
    sinir = simdi_tr() - timedelta(hours=24)
    degisen, dusen = set(), set()
    for r in satirlar:
        z = _zaman(r.get("son_degisim"))
        if z and z >= sinir and r.get("onceki_efektif") is not None and r.get("efektif") is not None:
            degisen.add(r["_id"])
            if r["efektif"] < r["onceki_efektif"]:
                dusen.add(r["_id"])
    return degisen, dusen


# ================= EXCEL =================
EXCEL_SUTUNLARI = [
    ("Model", "model"), ("Ürün Adı", "ad"), ("Pazaryeri", "platform"), ("Satıcı", "satici"), ("Durum", "durum"),
    ("Liste Fiyatı", "liste"), ("Satış Fiyatı", "satis"), ("Sepette Fiyat", "sepette"),
    ("Sepet İndirimi", "sepet_indirimi"), ("Sepet Kampanyası", "sepet_kampanyasi"), ("Kupon", "kupon"),
    ("Kupon İndirimi", "kupon_indirimi"), ("Kuponlu Fiyat", "kuponlu"), ("Efektif Fiyat", "efektif"),
    ("Diğer Kampanyalar", "diger_kampanya"), ("Önceki Efektif Fiyat", "onceki_efektif"),
    ("Son Fiyat Değişimi", "son_degisim"), ("BuyBox Sahibi", "bb_sahibi"), ("BuyBox Fiyatı", "bb_fiyat"),
    ("BuyBox Bu Satıcıda", "bb_bizde"), ("Satıcı Sırası", "sira"), ("Satıcı Sayısı", "satici_sayisi"),
    ("Resmi Satıcı BuyBox'ta", "resmi_bb"), ("Veri Zamanı", "veri_zamani"), ("Link", "link"),
]


def _excel(df: pd.DataFrame, sayfa: str) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=sayfa)
        ws = w.sheets[sayfa]
        for i, c in enumerate(df.columns, 1):
            uzun = max([len(str(c))] + [len(str(v)) for v in df[c].head(200)])
            ws.column_dimensions[ws.cell(1, i).column_letter].width = min(max(10, uzun + 2), 60)
        ws.freeze_panes = "B2"
    return out.getvalue()


def _guncel_excel(satirlar):
    kayit = []
    for r in satirlar:
        s = {}
        for b, a in EXCEL_SUTUNLARI:
            v = r.get(a)
            if a in ("bb_bizde", "resmi_bb"):
                v = "Evet" if v else ("Hayır" if r.get("bb_sahibi") else "")
            s[b] = v
        kayit.append(s)
    return _excel(pd.DataFrame(kayit, columns=[b for b, _ in EXCEL_SUTUNLARI]), "Rakip_Fiyatlari")


# ================= RAKİP FİYATLARI SEKMESİ =================
def rakip_sayfasi(satirlar, guncelleme, yas_dk):
    tasarim.lejant()
    kanal_durumu = load_durum()
    tasarim.veri_uyarilari(kanal_durumu, yas_dk, GECIKME_ESIGI_DK)
    if not satirlar:
        st.warning("Henüz veri yok. Bilgisayarda rakip_script.py çalıştıktan sonra burada görünecek "
                   f"(Google Sheet: {GSHEET_NAME} · {WS_GUNCEL}).")
        return

    c1, c2, c3, c_yenile, c4 = st.columns([2.1, 1.3, 1.8, 0.9, 1])
    with c1:
        ara = st.text_input("Ara", placeholder="Model, ürün adı ya da satıcı", key="rk_ara")
    with c2:
        platformlar = sorted({r["platform"] for r in satirlar if r.get("platform")})
        sec_p = st.multiselect("Pazaryeri", platformlar, placeholder="Tümü", key="rk_platform")
    with c3:
        saticilar = sorted({r["satici"] for r in satirlar if r.get("satici")}, key=str.casefold)
        sec_s = st.multiselect("Satıcı", saticilar, placeholder="Tümü", key="rk_satici")
    if ara and ara.strip():
        aranan = ara.strip().casefold()
        satirlar = [r for r in satirlar if aranan in r["_arama"]]
    if sec_p:
        satirlar = [r for r in satirlar if r["platform"] in sec_p]
    if sec_s:
        satirlar = [r for r in satirlar if r["satici"] in sec_s]
    with c_yenile:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🔄 Verileri yenile", key="rk_yenile",
                     help="Elle tarama yaptıysan 3 dakikalık önbelleği beklemeden güncel veriyi getirir"):
            st.cache_data.clear()
            st.rerun()
    with c4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        zaman = simdi_tr().strftime("%d-%m-%Y_%H-%M")
        st.download_button("📥 Excel'e Aktar", _guncel_excel(satirlar), f"Rakip_Fiyatlari_{zaman}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="rk_excel")

    degisen, dusen = son_24s_degisenler(satirlar)
    notu = (f"Veri: {_tarih_metni(guncelleme)} taraması." if guncelleme else "") + \
        " Fiyatlar oturum açılmamış bir müşterinin gördüğü fiyatlardır."
    tasarim.rakip_govde(satirlar, degisen, dusen, notu)


# ================= DEĞİŞİM GEÇMİŞİ SEKMESİ =================
def gecmis_sayfasi(satirlar):
    df = load_gecmis()
    st.markdown('<div class="pt-legend" style="padding-top:18px;justify-content:flex-start">'
                '<span class="pt-baslik-alt">Her ilanın fiyatı, sepet indirimi, kuponu ya da BuyBox sahibi değiştiğinde '
                'bir satır eklenir.</span></div>', unsafe_allow_html=True)
    if df.empty:
        st.info("Henüz değişim kaydı yok. İlk taramadan sonra burada görünecek.")
        return

    modeller = sorted({str(m) for m in df["Model"] if str(m)})
    c1, c2, c3, c4 = st.columns([1.6, 1.8, 1.6, 1])
    with c1:
        varsayilan = modeller.index(satirlar[0]["model"]) if satirlar and satirlar[0]["model"] in modeller else 0
        model = st.selectbox("Model", modeller, index=varsayilan, key="gc_model")
    alt_df = df[df["Model"].astype(str) == model].copy()
    alt_df["İlan"] = alt_df["Pazaryeri"].astype(str) + " · " + alt_df["Satıcı"].astype(str)
    with c2:
        ilanlar = sorted(alt_df["İlan"].unique())
        sec = st.multiselect("İlan", ilanlar, placeholder="Tümü", key="gc_ilan")
    with c3:
        donem = st.segmented_control("Dönem", ["Son 7 gün", "Son 30 gün", "Tümü"], default="Son 30 gün",
                                     key="gc_donem") or "Son 30 gün"
    if sec:
        alt_df = alt_df[alt_df["İlan"].isin(sec)]
    if donem != "Tümü":
        alt_df = alt_df[alt_df["Zaman_dt"] >= simdi_tr() - timedelta(days=7 if donem == "Son 7 gün" else 30)]
    tablo = alt_df.sort_values("Zaman_dt", ascending=False)
    gosterilen = [c for c in ("Zaman", "Pazaryeri", "Satıcı", "Durum", "Satış Fiyatı", "Sepette Fiyat",
                              "Kuponlu Fiyat", "Efektif Fiyat", "Kupon", "Sepet Kampanyası", "BuyBox Sahibi",
                              "BuyBox Fiyatı", "Değişen") if c in tablo.columns]
    with c4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.download_button("📥 Excel'e Aktar", _excel(tablo[["Model"] + gosterilen], "Degisim_Gecmisi"),
                           f"Rakip_Degisim_{model.replace('/', '-')}_{simdi_tr():%d-%m-%Y}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="gc_excel")

    with st.container(key="pt_gecmis_kart"):
        st.markdown(f'<div class="pt-table-head"><h2>{model} · efektif fiyat seyri</h2></div>', unsafe_allow_html=True)
        grafik = alt_df.dropna(subset=["Efektif Fiyat"])[["Zaman_dt", "İlan", "Efektif Fiyat", "Kupon",
                                                          "Sepet Kampanyası", "Satış Fiyatı"]].copy()
        if grafik.empty:
            st.caption("Bu dönemde fiyat kaydı yok.")
        else:
            # her ilanın son değeri bugüne kadar uzatılır (geçmiş sadece değişimleri tutar)
            son = grafik.sort_values("Zaman_dt").groupby("İlan").tail(1).copy()
            son["Zaman_dt"] = simdi_tr()
            grafik = pd.concat([grafik, son], ignore_index=True)
            ch = (alt.Chart(grafik).mark_line(interpolate="step-after", strokeWidth=2.2, point=True)
                  .encode(x=alt.X("Zaman_dt:T", title=None, axis=alt.Axis(format="%d.%m %H:%M")),
                          y=alt.Y("Efektif Fiyat:Q", title="Efektif fiyat (₺)", scale=alt.Scale(zero=False)),
                          color=alt.Color("İlan:N", title=None, legend=alt.Legend(orient="bottom")),
                          tooltip=[alt.Tooltip("İlan:N"), alt.Tooltip("Zaman_dt:T", title="Zaman", format="%d.%m.%Y %H:%M"),
                                   alt.Tooltip("Efektif Fiyat:Q", format=",.2f"),
                                   alt.Tooltip("Satış Fiyatı:Q", format=",.2f"), alt.Tooltip("Kupon:N"),
                                   alt.Tooltip("Sepet Kampanyası:N")])
                  .properties(height=340))
            st.altair_chart(ch, use_container_width=True)

        st.markdown('<div class="pt-table-head" style="margin-top:8px"><h2>Değişim kayıtları</h2></div>',
                    unsafe_allow_html=True)
        para = st.column_config.NumberColumn(format="%.2f ₺")
        st.dataframe(tablo[gosterilen], hide_index=True, use_container_width=True, height=420,
                     column_config={c: para for c in ("Satış Fiyatı", "Sepette Fiyat", "Kuponlu Fiyat",
                                                       "Efektif Fiyat", "BuyBox Fiyatı")})


# ================= SAYFA =================
tasarim.tema_uygula()
# Animasyon sadece sayfa açıldığında / yenilendiğinde oynar; filtre ya da sekme değişince tekrar oynamaz
if ACILIS_ANIMASYONU and not st.session_state.get("acilis_gosterildi"):
    st.session_state["acilis_gosterildi"] = True
    tasarim.acilis_animasyonu()
FIYAT_SEKMESI, GECMIS_SEKMESI = ":material/sell: Rakip Fiyatları", ":material/history: Değişim Geçmişi"

_satirlar, _guncelleme = load_guncel()
_yas = tarama_yasi_dk(_guncelleme)


def _son_tarama(aktif):
    return _tarih_metni(_guncelleme), (_yas is None or _yas <= GECIKME_ESIGI_DK), "Son tarama"


_aktif = tasarim.ust_baslik([FIYAT_SEKMESI, GECMIS_SEKMESI], _son_tarama)
if _aktif == GECMIS_SEKMESI:
    gecmis_sayfasi(_satirlar)
else:
    rakip_sayfasi(_satirlar, _guncelleme, _yas)
tasarim.alt_bant(sorted({r["platform"] for r in _satirlar if r.get("platform")}))
