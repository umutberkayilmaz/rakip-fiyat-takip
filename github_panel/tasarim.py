"""
tasarim.py — Rakip Fiyat Takibi paneli için görsel katman.

Veri okuma / hesaplama app.py'de; bu dosya yalnızca görünümü üretir.
Satır biçimi (her takip edilen ilan bir sözlük, app.py'deki ilanlari_donustur() üretir):

    {"model": "BRI951/03", "ad": "...", "platform": "Trendyol", "satici": "Teknosa", "durum": "Satışta",
     "liste": 24999, "satis": 23999, "sepette": 23499, "sepet_kampanyasi": "Sepette 500 TL İndirim",
     "kupon": "%5 kupon (alt limit 1.000 TL, maks. 1.000 TL)", "kuponlu": 22499, "efektif": 22499,
     "onceki_efektif": 23999, "son_degisim": "19.10.2026 14:00", "bb_sahibi": "Philips", "bb_fiyat": 21999,
     "bb_bizde": False, "sira": 3, "satici_sayisi": 12, "link": "https://...", "gorsel": "https://...",
     "eski_veri": ""}
"""
from __future__ import annotations

import html
import streamlit as st

PLATFORMLAR = ["Trendyol", "Hepsiburada"]

# Pazaryeri logoları (sitelerin kendi sunucularındaki güncel logolar). Boş kalırsa adı yazılır.
KANAL_LOGOLARI: dict[str, str] = {
    "Trendyol": '<img src="https://cdn.dsmcdn.com/sfweb-browsing/images/trendyol-logo_1761301016237.svg" '
                'height="22" alt="Trendyol" referrerpolicy="no-referrer" style="max-width:120px;object-fit:contain">',
    "Hepsiburada": '<img src="https://images.hepsiburada.net/storefront/storefront/www/assets/images/hepsiburada.svg" '
                   'height="22" alt="Hepsiburada" referrerpolicy="no-referrer" style="max-width:120px;object-fit:contain">',
}

# --------------------------------------------------------------------------
# Tema (mevcut raporla aynı görsel dil)
# --------------------------------------------------------------------------
_TEMA_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="st-"], .stApp { font-family: "Plus Jakarta Sans", system-ui, sans-serif; }
.stApp { background: linear-gradient(180deg, #FFFFFF 0%, #F6FAF8 30%, #EAF5EE 68%, #DDF1E5 100%) fixed; color: #15261D; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1440px; }
.num { font-variant-numeric: tabular-nums; }

.pt-card { background:#fff; border:1px solid #DCE9E1; border-radius:18px; box-shadow:0 4px 18px rgba(20,70,45,.05); padding:20px 22px; }
.pt-title h1 { margin:0; font-size:32px; font-weight:800; color:#10281B; letter-spacing:-.01em; padding:0; }
.pt-title p { margin:4px 0 0; font-size:15px; color:#52675A; }
.pt-legend { display:flex; gap:10px; align-items:center; justify-content:flex-end; font-size:13px; font-weight:600; flex-wrap:wrap; }
.pt-chip { display:inline-flex; align-items:center; gap:6px; padding:6px 12px; border-radius:999px; border:1px solid; }
.pt-dot { width:8px; height:8px; border-radius:50%; display:inline-block; }

.pt-kpis { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:20px; margin:14px 0 22px; }
.pt-kpi { display:flex; flex-direction:column; gap:8px; }
.pt-kpi .lbl { font-size:13px; font-weight:600; color:#5E7366; }
.pt-kpi .val { display:flex; align-items:baseline; gap:8px; }
.pt-kpi .val b { font-size:38px; font-weight:800; color:#10281B; line-height:1.1; }
.pt-kpi .val span { font-size:14px; font-weight:600; color:#6A7E72; }
.pt-kpi .sub { font-size:12px; color:#6A7E72; }
.pt-kpi.bad { background:#FFF9F8; border-color:#F3CFC8; }
.pt-kpi.bad .lbl { color:#8A3A2F; } .pt-kpi.bad .val b { color:#B3291B; } .pt-kpi.bad .sub, .pt-kpi.bad .val span { color:#8A5A52; }
.pt-bar { display:flex; height:6px; border-radius:999px; overflow:hidden; background:#EEF2EF; }

.pt-table-head h2, .pt-side h2 { margin:0; font-size:17px; font-weight:700; color:#10281B; padding:0; }
.pt-grid { display:grid; grid-template-columns:236px 124px repeat(5,minmax(0,1fr)); gap:8px; align-items:center; }
.pt-thead { padding:10px 0; border-top:1px solid #E6EEE9; border-bottom:1px solid #E6EEE9; align-items:end; }
.pt-thead .h { font-size:11px; font-weight:700; color:#6A7E72; letter-spacing:.06em; text-transform:uppercase; }
.pt-thead .ch b { display:block; font-size:13px; font-weight:700; color:#15261D; }
.pt-thead .ch small { font-size:11px; color:#7A8C81; }
.pt-row { padding:9px 0; border-bottom:1px solid #EEF3F0; }
.pt-row .nm { font-size:14px; font-weight:600; color:#15261D; line-height:1.3; }
.pt-row .mt { font-size:12px; color:#6A7E72; }
.pt-row .tsf { font-size:15px; font-weight:700; color:#10281B; }
.pt-cell { display:flex; flex-direction:column; gap:4px; padding:8px 10px; border-radius:11px; border:1px solid; }
.pt-cell .p { display:flex; align-items:center; gap:5px; font-size:15px; font-weight:700; }
.pt-cell .d { display:flex; align-items:center; justify-content:space-between; font-size:11px; font-weight:700; }
.pt-ok   { background:#E6F5EC; border-color:#C3E5D0; color:#14693A; }
.pt-warn { background:#FFF5DA; border-color:#F0D68E; color:#7F5300; }
.pt-bad  { background:#FDE6E2; border-color:#F3BDB4; color:#A3261A; }
.pt-none { background:#F4F6F5; border:1px dashed #C9D3CD; color:#7A8680; font-size:13px; font-weight:600; }
/* [eklendi] TSF'si olmayan urun, tiklanabilir hucre, gorsel ve TSF notlari */
.pt-nt { background:#F4F6F5; border-color:#DCE3DF; color:#3E4A44; }
a.pt-link { text-decoration:none !important; color:inherit !important; display:block; }
a.pt-link .pt-cell { transition:box-shadow .15s, transform .15s; }
a.pt-link:hover .pt-cell { box-shadow:0 4px 12px rgba(20,70,45,.14); transform:translateY(-1px); }
.pt-urun { display:flex; align-items:center; gap:10px; }
.pt-thumb { position:relative; flex-shrink:0; }
.pt-thumb > img { width:40px; height:40px; object-fit:contain; background:#fff; border-radius:8px; border:1px solid #E1EAE4; display:block; }
.pt-thumb .buyuk { visibility:hidden; opacity:0; position:absolute; left:110%; top:50%; transform:translateY(-50%); z-index:9999;
                   background:#fff; padding:6px; border-radius:12px; box-shadow:0 10px 35px rgba(0,0,0,.25); transition:opacity .15s; }
.pt-thumb .buyuk img { width:170px; height:170px; object-fit:contain; display:block; }
.pt-thumb:hover .buyuk { visibility:visible; opacity:1; }
/* [eklendi] Urun tablosu: beyaz kart (st.container key="pt_urun_tablosu") ve eski duzende tablo */
.st-key-pt_urun_tablosu, .st-key-pt_bb_tablosu { background:#FFFFFF; border:1px solid #DCE9E1; border-radius:20px;
                          box-shadow:0 6px 24px rgba(20,70,45,.06); padding:20px 22px 12px; }
table.pt-tablo { width:100%; border-collapse:separate !important; border-spacing:0; margin:0 !important; font-size:13px; color:#15261D; }
table.pt-tablo tr { border:0 !important; }
table.pt-tablo th, table.pt-tablo td { border:0 !important; border-bottom:1px solid #EEF3F0 !important; padding:6px 8px !important;
                                       text-align:center !important; vertical-align:middle; }
table.pt-tablo th { vertical-align:bottom; padding-bottom:8px !important; border-bottom-color:#E1EAE4 !important;
                    font-size:11px; font-weight:700; color:#6A7E72; letter-spacing:.05em; text-transform:uppercase; }
table.pt-tablo th small { display:block; font-size:10.5px; font-weight:700; color:#8A9A90; letter-spacing:0; text-transform:none; margin-top:3px; }
table.pt-tablo th.ch { cursor:help; }
table.pt-tablo th .logo { height:28px; display:flex; align-items:center; justify-content:center; }
table.pt-tablo th .logo img, table.pt-tablo th .logo svg { height:22px; max-width:112px; object-fit:contain; }
/* [eklendi] Donuk başlık satırı (Excel'deki "bölmeleri dondur" gibi): kaydırınca logolu satır üstte kalır.
   60px = Streamlit'in üst çubuğunun yüksekliği. */
table.pt-tablo thead th { position:sticky; top:60px; z-index:3; background:#FFFFFF;
                          box-shadow:0 8px 10px -10px rgba(20,70,45,.28); }
/* Üst çubuk sayfa en üstteyken saydam; kaydırma başlayınca yumuşakça beyazlaşır (desteklemeyen tarayıcıda saydam kalır) */
@supports (animation-timeline: scroll()) {
  [data-testid="stAppViewContainer"] { timeline-scope: --pt-kaydirma; }
  [data-testid="stMain"] { scroll-timeline: --pt-kaydirma block; }
  @keyframes ptUstCubuk { from { background: rgba(255,255,255,0); backdrop-filter: blur(0px); box-shadow: none; }
                          to { background: rgba(255,255,255,.99); backdrop-filter: blur(8px);
                               box-shadow: 0 1px 0 rgba(20,70,45,.07); } }
  header[data-testid="stHeader"] { animation: ptUstCubuk linear both; animation-timeline: --pt-kaydirma;
                                   animation-range: 0 90px; }
}
table.pt-tablo tbody tr:last-child td { border-bottom:0 !important; }
table.pt-tablo tbody tr:hover td { background:#FAFCFB; }
.pt-bk { font-variant-numeric:tabular-nums; color:#3E4A44; white-space:nowrap; cursor:help; font-size:12.5px; }
.pt-grp { color:#52675A; font-size:12.5px; white-space:nowrap; }
.pt-kod { position:relative; display:inline-block; font-weight:700; color:#10281B; white-space:nowrap; }
.pt-kod.resimli { cursor:zoom-in; border-bottom:1px dotted #9FB5A8; }
.pt-kod .buyuk { visibility:hidden; opacity:0; position:absolute; left:calc(100% + 12px); top:50%; transform:translateY(-50%);
                 width:184px; box-sizing:border-box; z-index:9999; background:#fff; padding:6px; border-radius:12px;
                 border:1px solid #DCE9E1; box-shadow:0 10px 35px rgba(20,40,30,.25); transition:opacity .15s; }
.pt-kod .buyuk img { width:170px !important; height:170px !important; max-width:none !important; object-fit:contain; display:block; }
.pt-kod:hover .buyuk { visibility:visible; opacity:1; }
.pt-ref { font-variant-numeric:tabular-nums; white-space:nowrap; color:#52675A; font-weight:500; font-size:13px; }
.pt-ref.aktif { color:#10281B; font-weight:800; }
.pt-ref small { display:block; font-size:10px; font-weight:500; color:#8A9A90; }
.pt-pill { display:inline-flex; align-items:center; gap:5px; padding:3px 10px; border-radius:999px; border:0 !important;
           font-size:12.5px; font-weight:700; line-height:1.45; white-space:nowrap; font-variant-numeric:tabular-nums; }
.pt-pill.pt-ok { background:#E3F4EA; color:#166B3D; }
.pt-pill.pt-warn { background:#FFF1CC; color:#7A5200; }
.pt-pill.pt-bad { background:#FBDCD8; color:#9E2418; }
.pt-pill.pt-nt { background:#F1F4F2; color:#3E4A44; }
.pt-pill .bb { font-size:9px; line-height:13px; padding:0 3px; border-radius:4px; }
.pt-pill .kupa { font-size:11px; }
.pt-yok { color:#A7B4AC; font-weight:600; cursor:help; }
/* [eklendi] "veri alinamadi" ile "satista yok" ayrimi */
.pt-veriyok { display:inline-block; min-width:22px; padding:1px 8px; border-radius:999px; background:#FFF1E6; color:#B4531A;
              font-weight:800; font-size:12px; cursor:help; border:1px dashed #F0B48A; line-height:1.45; }
.pt-pill.eski { outline:1.5px dashed rgba(127,83,0,.55); outline-offset:1px; opacity:.8; }
.pt-kanal-uyari { display:inline-block; margin-top:4px; font-size:10px; font-weight:800; padding:1px 7px; border-radius:999px;
                  text-transform:none; letter-spacing:0; white-space:nowrap; }
.pt-kanal-uyari.eski { background:#FFF5DA; color:#7F5300; }
.pt-kanal-uyari.yok { background:#FDE6E2; color:#A3261A; }
.pt-bant ul { margin:4px 0 0 0; padding-left:18px; }
.pt-bant li { margin:1px 0; }
a.pt-link { text-decoration:none !important; }
a.pt-link .pt-pill { transition:box-shadow .15s, transform .15s; }
a.pt-link:hover .pt-pill { box-shadow:0 3px 10px rgba(20,70,45,.16); transform:translateY(-1px); }
.pt-bant { display:flex; gap:12px; align-items:flex-start; padding:12px 16px; border-radius:14px; border:1px solid;
           margin:2px 0 14px; font-size:13.5px; line-height:1.5; }
.pt-bant .ik { font-size:16px; line-height:1.3; }
.pt-bant b { font-weight:800; }
.pt-bant.bilgi { background:#EEF5FC; border-color:#CFE0F3; color:#1D3F66; }
.pt-bant.basari { background:#E6F5EC; border-color:#C3E5D0; color:#14693A; }
.pt-bant.uyari { background:#FFF5DA; border-color:#F3DC9B; color:#7F5300; }
.pt-bant.normal { background:#F4F6F5; border-color:#DCE3DF; color:#3E4A44; }
.pt-rakip-ad { display:block; font-size:11px; color:#6A7E72; margin-top:3px; white-space:nowrap; max-width:140px;
               overflow:hidden; text-overflow:ellipsis; margin-left:auto; margin-right:auto; }
.pt-pill.pt-oneri { font-size:13.5px; padding:4px 12px; }
.pt-fark { font-weight:700; white-space:nowrap; font-variant-numeric:tabular-nums; font-size:12.5px; color:#3E4A44; }
.pt-fark small { display:block; font-size:10.5px; color:#8A9A90; font-weight:600; }
.pt-bbs { font-size:11.5px; white-space:nowrap; color:#3E4A44; line-height:1.7; }
.pt-bbs .pl { display:inline-block; min-width:22px; font-size:9.5px; font-weight:800; color:#8A9A90; letter-spacing:.04em; margin-right:4px; }
.pt-bbs.bizde { color:#166B3D; font-weight:700; }
/* [eklendi] BuyBox sirasi hucresi */
.pt-bbl-kutu { display:inline-flex; flex-direction:column; min-width:190px; text-align:left; }
.pt-bbl { display:grid; grid-template-columns:14px minmax(0,1fr) auto; column-gap:7px; align-items:center;
          font-size:11.5px; line-height:1.6; color:#3E4A44; white-space:nowrap; }
.pt-bbl .no { font-size:9.5px; font-weight:800; color:#9AA8A0; text-align:right; }
.pt-bbl .ad { overflow:hidden; text-overflow:ellipsis; }
.pt-bbl .f { font-weight:700; font-variant-numeric:tabular-nums; }
.pt-bbl.ilk .ad, .pt-bbl.ilk .f { color:#10281B; font-weight:800; }
.pt-bbl .ucuz { font-size:8.5px; font-weight:800; color:#52675A; background:#EEF3F0; border-radius:4px; padding:0 4px;
                margin-left:5px; letter-spacing:.02em; }
.pt-bbl a { color:inherit !important; text-decoration:none !important; border-bottom:1px dotted #9FB5A8; }
.pt-bbl-ayrac { border-top:1px dashed #E1EAE4; margin:2px 0 1px; }
.pt-alt-paneller { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:20px; }
.pt-row .tsf-alt { display:block; font-size:11px; font-weight:500; color:#6A7E72; margin-top:3px; line-height:1.35; }
.bb { font-size:10px; font-weight:800; letter-spacing:.04em; padding:2px 6px; border-radius:6px; }
.bb.own { background:#178A4E; color:#fff; }
.bb.lost { border:1px solid currentColor; opacity:.75; text-decoration:line-through; padding:1px 5px; }
.pt-foot-note { display:flex; gap:18px; align-items:center; padding:12px 0 2px; font-size:12px; color:#6A7E72; }

.pt-side { display:flex; flex-direction:column; gap:16px; }
.pt-chrow { display:flex; flex-direction:column; gap:6px; }
.pt-chrow .t { display:flex; justify-content:space-between; align-items:baseline; font-size:14px; font-weight:700; }
.pt-chrow .t span { font-size:13px; color:#178A4E; }
.pt-chrow small { font-size:12px; color:#6A7E72; }
.pt-alert { display:flex; flex-direction:column; gap:4px; padding:12px 14px; border-radius:12px; background:#FFF7F5; border:1px solid #F6DAD4; }
.pt-alert .t { display:flex; justify-content:space-between; gap:8px; font-size:13px; font-weight:700; color:#15261D; }
.pt-alert .t span { color:#A3261A; font-weight:800; font-size:12px; }
.pt-alert small { font-size:12px; color:#6A5A56; }

[data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border-radius:20px !important; border-color:#DCE9E1 !important; box-shadow:0 6px 24px rgba(20,70,45,.06); }
.pt-footer { margin-top:24px; padding:20px 28px; background:rgba(255,255,255,.6); border:1px solid #D8E3EC; border-radius:20px; }
.pt-footer .top { display:flex; justify-content:space-between; font-size:11px; font-weight:700; color:#6A7B88; letter-spacing:.08em; text-transform:uppercase; margin-bottom:14px; }
.pt-logos { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:16px; }
.pt-logo { height:72px; display:flex; align-items:center; justify-content:center; border-radius:14px; background:rgba(255,255,255,.7); border:1px solid #DCE5EC; font-size:15px; font-weight:700; color:#8796A2; }
</style>
"""

_EK_CSS = """
<style>
/* Rakip paneline özel eklemeler */
.st-key-pt_rakip_tablosu, .st-key-pt_gecmis_kart { background:#FFFFFF; border:1px solid #DCE9E1; border-radius:20px;
                          box-shadow:0 6px 24px rgba(20,70,45,.06); padding:20px 22px 12px; }
table.pt-tablo td.grp-ilk { border-top:2px solid #E1EAE4 !important; }
table.pt-tablo tbody tr:first-child td.grp-ilk { border-top:0 !important; }
table.pt-tablo td.model { text-align:left !important; vertical-align:top; padding-top:10px !important;
                          border-right:1px solid #EEF3F0 !important; background:#FCFDFC; }
.pt-model-ad { display:block; font-size:11px; color:#6A7E72; max-width:190px; white-space:normal; line-height:1.35; margin-top:3px; }
.pt-plat img { height:16px; max-width:92px; object-fit:contain; display:block; margin:0 auto; }
.pt-satici { font-weight:700; color:#15261D; white-space:nowrap; font-size:13px; }
.pt-satici small { display:block; font-size:10.5px; color:#8A9A90; font-weight:600; margin-top:2px; }
.pt-liste { display:block; font-size:10.5px; color:#9AA8A0; text-decoration:line-through; margin-bottom:2px; }
.pt-pill.pt-sepet { background:#E4EEFB; color:#1D4F91; }
.pt-pill.pt-kupon { background:#FFF1CC; color:#7A5200; }
.pt-pill.pt-gri { background:#F1F4F2; color:#3E4A44; }
.pt-etiket { display:block; font-size:10.5px; font-weight:700; margin-top:3px; white-space:nowrap; }
.pt-etiket.sepet { color:#1D4F91; } .pt-etiket.kupon { color:#7A5200; }
.pt-kupon-kutu { display:inline-flex; flex-direction:column; gap:3px; text-align:left; max-width:230px; }
.pt-kupon-sat { display:block; font-size:11px; line-height:1.35; color:#5C4300; background:#FFF8E1;
                border:1px dashed #E8C66A; border-radius:8px; padding:3px 8px; white-space:normal; }
.pt-kupon-sat b { color:#7A5200; }
.pt-kupon-sat.plus { opacity:.6; }
.pt-sepet-sat { display:block; font-size:11px; line-height:1.35; color:#1D3F66; background:#EEF5FC;
                border:1px solid #CFE0F3; border-radius:8px; padding:3px 8px; white-space:normal; max-width:210px; margin:0 auto; }
.pt-degisim { font-weight:800; font-size:12.5px; white-space:nowrap; font-variant-numeric:tabular-nums; }
.pt-degisim.dus { color:#B3291B; } .pt-degisim.art { color:#166B3D; }
.pt-degisim small { display:block; font-size:10px; font-weight:600; color:#8A9A90; }
.pt-bbh { font-size:12px; white-space:nowrap; color:#3E4A44; line-height:1.45; }
.pt-bbh b { font-variant-numeric:tabular-nums; }
.pt-bbh.bizde { color:#166B3D; font-weight:800; }
.pt-bbh .resmi { font-size:9px; font-weight:800; background:#EEF3F0; color:#52675A; border-radius:4px; padding:0 4px; margin-left:4px; }
.pt-durum { display:inline-block; font-size:11.5px; font-weight:700; color:#7A8680; background:#F4F6F5;
            border:1px dashed #C9D3CD; border-radius:999px; padding:2px 10px; white-space:nowrap; cursor:help; }
.pt-baslik-alt { font-size:15px; color:#52675A; font-weight:500; }
.ust-baslik-yazi { text-align:center; line-height:1.15; }
.ust-baslik-yazi b { display:block; font-size:30px; font-weight:800; color:#10281B; letter-spacing:-.01em; }
.ust-baslik-yazi span { display:block; font-size:13px; font-weight:600; color:#6A7E72; letter-spacing:.06em;
                        text-transform:uppercase; margin-top:4px; }
.pt-logos.iki { grid-template-columns:repeat(2,minmax(0,1fr)); }
</style>
"""


def tema_uygula() -> None:
    """Sayfanın başında bir kez çağırın."""
    st.markdown(_TEMA_CSS + _EK_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Yardımcılar
# --------------------------------------------------------------------------
def _fmt(n) -> str:
    return f"{n:,.0f}".replace(",", ".") + " ₺"


def _fmt2(v) -> str:
    """Kuruşlu fiyatı kuruşuyla, tam fiyatı kuruşsuz gösterir: 5.586,23 ₺ / 5.759 ₺"""
    if abs(v - round(v)) < 0.005:
        return _fmt(v)
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " ₺"


def _e(x) -> str:
    return html.escape(str(x if x is not None else ""), quote=True)


def _link(ic: str, link) -> str:
    link = str(link or "")
    if link.startswith("http"):
        return f'<a class="pt-link" href="{_e(link)}" target="_blank" title="İlanı aç">{ic}</a>'
    return ic


# --------------------------------------------------------------------------
# Üst kart: solda sekmeler, ortada başlık, sağda canlı takip + son tarama
# --------------------------------------------------------------------------
_UST_CSS = """<style>
[data-testid="stIconMaterial"]{font-family:"Material Symbols Rounded" !important;}
.st-key-ust_baslik{background:#ffffff;border:1px solid #e3ebe6;border-radius:28px;
  box-shadow:0 6px 20px rgba(28,60,42,.06);padding:14px 28px;}
.st-key-ust_baslik [data-testid="stHorizontalBlock"]{align-items:center;}
.st-key-sekme [data-testid="stButtonGroup"] > div:last-child{display:inline-flex !important;flex-wrap:nowrap !important;
  width:auto !important;max-width:none !important;overflow:visible !important;gap:4px;background:#ffffff;
  border:1.5px solid #121212;border-radius:999px;padding:5px;}
.st-key-sekme button{flex-shrink:0;white-space:nowrap;height:44px;padding:0 20px !important;border:0 !important;outline:none;
  border-radius:999px !important;background:transparent !important;box-shadow:none !important;color:#121212 !important;}
.st-key-sekme button p{color:#121212 !important;font-size:15px;font-weight:500;}
.st-key-sekme button:hover{background:#FFF8B3 !important;}
.st-key-sekme button[aria-checked="true"],.st-key-sekme button[kind="segmented_controlActive"]{
  background:#F4E300 !important;box-shadow:inset 0 0 0 1.5px #121212 !important;}
.st-key-sekme button[aria-checked="true"] p,.st-key-sekme button[kind="segmented_controlActive"] p{font-weight:700;}
.st-key-ust_baslik [data-testid="stMarkdownContainer"]{margin-bottom:0 !important;}
.st-key-ust_baslik [data-testid="stElementContainer"]{margin-bottom:0 !important;}
.st-key-ust_baslik [data-testid="stColumn"]{display:flex;flex-direction:column;justify-content:center;}
.ust-durum{display:flex;white-space:nowrap;justify-content:flex-end;align-items:center;gap:16px;}
.ust-canli{display:inline-flex;align-items:center;gap:8px;height:38px;padding:0 16px;border-radius:999px;
  font-size:15px;font-weight:600;line-height:38px;}
.ust-canli.ok{background:#e8f4ec;color:#1e6b40;} .ust-canli.gec{background:#FFF5DA;color:#7F5300;}
.ust-canli span{width:9px;height:9px;border-radius:50%;display:inline-block;}
.ust-canli.ok span{background:#1e7a46;animation:ustNabiz 1.8s ease-out infinite;} .ust-canli.gec span{background:#D08A00;}
@keyframes ustNabiz{0%{box-shadow:0 0 0 0 rgba(23,138,78,.45)}70%{box-shadow:0 0 0 8px rgba(23,138,78,0)}100%{box-shadow:0 0 0 0 rgba(23,138,78,0)}}
.ust-tarama{display:flex;flex-direction:column;gap:2px;line-height:1.2;}
.ust-tarama small{font-size:12px;letter-spacing:.06em;color:#4f6359;font-weight:600;text-transform:uppercase;}
.ust-tarama b{font-size:18px;color:#16231c;}
</style>"""


def ust_baslik(sekmeler: list[str], son_tarama_fn) -> str:
    """son_tarama_fn(aktif_sekme) -> (tarih_metni, canli_mi, etiket). Seçili sekmeyi döndürür."""
    if st.session_state.get("aktif_sekme") not in sekmeler:
        st.session_state["aktif_sekme"] = sekmeler[0]
        st.session_state["sekme"] = sekmeler[0]

    def _degisti():                      # seçili sekmeye tekrar tıklanınca seçim kalkmasın
        if st.session_state.get("sekme") is None:
            st.session_state["sekme"] = st.session_state["aktif_sekme"]
        else:
            st.session_state["aktif_sekme"] = st.session_state["sekme"]

    st.markdown(_UST_CSS, unsafe_allow_html=True)
    aktif = st.session_state["aktif_sekme"]
    tarih, canli, etiket = son_tarama_fn(aktif)
    with st.container(key="ust_baslik"):
        sol, orta, sag = st.columns([1.15, 2.3, 1.05], gap="small")
        with sol:
            st.segmented_control("Sekme", sekmeler, key="sekme", on_change=_degisti, label_visibility="collapsed")
        with orta:
            st.markdown('<div class="ust-baslik-yazi"><b>Rakip Fiyat Takibi</b>'
                        '<span>Trendyol · Hepsiburada · saat başı</span></div>', unsafe_allow_html=True)
        with sag:
            rozet = ('<div class="ust-canli ok"><span></span>Canlı takip</div>' if canli
                     else '<div class="ust-canli gec"><span></span>Tarama gecikti</div>')
            st.markdown(f'<div class="ust-durum">{rozet}<div class="ust-tarama"><small>{_e(etiket)}</small>'
                        f'<b>{_e(tarih or "–")}</b></div></div>', unsafe_allow_html=True)
    return st.session_state["aktif_sekme"]


def lejant() -> None:
    st.markdown("""<div class="pt-legend" style="padding-top:18px"><span style="color:#6A7E72">Gösterim</span>
<span class="pt-chip" style="background:#E4EEFB;border-color:#CFE0F3;color:#1D4F91"><span class="pt-dot" style="background:#2F6DB5"></span>Sepette indirim</span>
<span class="pt-chip pt-warn"><span class="pt-dot" style="background:#E0A800"></span>Kupon</span>
<span class="pt-chip pt-ok"><span class="pt-dot" style="background:#1F9D57"></span>🏆 Modelin en ucuzu</span>
<span class="pt-chip pt-bad"><span class="pt-dot" style="background:#D2402F"></span>▼ Fiyat düştü</span></div>""",
                unsafe_allow_html=True)


def bant(tur: str, baslik_: str, metin: str, ikon: str = "") -> None:
    """tur = bilgi | basari | uyari | normal"""
    st.markdown(f'<div class="pt-bant {tur}"><span class="ik">{ikon}</span><div><b>{html.escape(baslik_)}</b> '
                f'{html.escape(metin)}</div></div>', unsafe_allow_html=True)


def veri_uyarilari(kanal_durumu, son_tarama_yasi_dk=None, gecikme_esigi_dk: int = 120) -> None:
    """Tablonun üstünde: gecikmiş tarama ve sorunlu pazaryerleri için açıklama bandı."""
    if son_tarama_yasi_dk is not None and son_tarama_yasi_dk > gecikme_esigi_dk:
        saat, dk = divmod(int(son_tarama_yasi_dk), 60)
        sure = f"{saat} saat {dk} dakika" if saat else f"{dk} dakika"
        st.markdown(f'<div class="pt-bant uyari"><span class="ik">⏱️</span><div><b>Son tarama {sure} önce yapıldı.</b> '
                    "Tarama bilgisayarı kapalı olabilir ya da zamanlanmış görev çalışmıyor olabilir; "
                    "aşağıdaki fiyatlar son taramanın verisidir.</div></div>", unsafe_allow_html=True)
    sorunlu = [(ad, d) for ad, d in (kanal_durumu or {}).items() if d.get("durum") in ("Eski veri", "Veri alınamadı")]
    if sorunlu:
        maddeler = ""
        for ad, d in sorunlu:
            neden = html.escape(d.get("aciklama") or "")
            if d["durum"] == "Eski veri":
                maddeler += (f"<li><b>{html.escape(ad)}:</b> bazı ürün sayfaları son taramada okunamadı ({neden}). "
                             "Bu ilanlarda son başarılı veri kesikli çerçeveyle gösteriliyor.</li>")
            else:
                maddeler += (f"<li><b>{html.escape(ad)}:</b> veri alınamadı ({neden}). Bu pazaryerindeki "
                             "<b>?</b> işaretleri satıcının satış yapmadığı anlamına gelmez.</li>")
        st.markdown(f'<div class="pt-bant uyari"><span class="ik">⚠️</span><div><b>Bazı pazaryerlerinden güncel veri '
                    f"alınamadı.</b><ul>{maddeler}</ul></div></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# KPI kartları
# --------------------------------------------------------------------------
def kpi_kartlari(satirlar: list[dict], degisen_24s: int, dusen_24s: int) -> None:
    satista = [r for r in satirlar if r.get("efektif") is not None]
    kuponlu = [r for r in satista if r.get("kupon")]
    sepetli = [r for r in satista if r.get("sepette")]
    modeller = len({r["model"] for r in satirlar})
    sayfalar = {(r["platform"], r["model"]): r for r in satirlar if r.get("bb_sahibi")}
    resmi = sum(1 for r in sayfalar.values() if r.get("resmi_bb"))
    en_kupon = max((r.get("kupon_indirimi") or 0 for r in kuponlu), default=0)
    st.markdown(f"""<div class="pt-kpis">
<div class="pt-card pt-kpi"><span class="lbl">Takip edilen ilan</span>
  <div class="val"><b class="num">{len(satirlar)}</b><span>ilan · {modeller} model</span></div>
  <span class="sub">{len(satista)} ilan satışta · resmi satıcı {resmi}/{len(sayfalar)} sayfada BuyBox'ta</span></div>
<div class="pt-card pt-kpi"><span class="lbl">Kuponlu ilan</span>
  <div class="val"><b class="num" style="color:#9A6A00">{len(kuponlu)}</b><span>/ {len(satista)} ilan</span></div>
  <span class="sub">{"En yüksek kupon indirimi " + _fmt2(en_kupon) if en_kupon else "Şu an geçerli kupon indirimi yok"}</span></div>
<div class="pt-card pt-kpi"><span class="lbl">Sepette indirimli ilan</span>
  <div class="val"><b class="num" style="color:#1D4F91">{len(sepetli)}</b><span>/ {len(satista)} ilan</span></div>
  <span class="sub">Sepete eklenince fiyatı düşen ilanlar</span></div>
<div class="pt-card pt-kpi bad"><span class="lbl">Son 24 saatte fiyatı değişen</span>
  <div class="val"><b class="num">{degisen_24s}</b><span>ilan</span></div>
  <span class="sub">{dusen_24s} ilanda fiyat düştü</span></div>
</div>""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Rakip tablosu
# --------------------------------------------------------------------------
def _model_hucre(r: dict, satir_sayisi: int) -> str:
    g = str(r.get("gorsel") or "")
    kod = _e(r.get("model") or "-")
    ad = _e(" ".join(str(r.get("ad") or "").split()))
    if g.startswith("http"):
        kod_html = (f'<span class="pt-kod resimli" title="{ad}">{kod}<span class="buyuk">'
                    f'<img src="{_e(g)}" referrerpolicy="no-referrer"></span></span>')
    else:
        kod_html = f'<span class="pt-kod" title="{ad}">{kod}</span>'
    return (f'<td class="model grp-ilk" rowspan="{satir_sayisi}">{kod_html}'
            f'<span class="pt-model-ad">{ad}</span></td>')


def _platform_hucre(r: dict) -> str:
    logo = KANAL_LOGOLARI.get(r["platform"], "")
    return f'<span class="pt-plat" title="{_e(r["platform"])}">{logo or _e(r["platform"])}</span>'


def _satici_hucre(r: dict) -> str:
    alt = []
    if r.get("sira"):
        alt.append(f'{r["sira"]}. sıra' + (f' · {r["satici_sayisi"]} satıcı' if r.get("satici_sayisi") else ""))
    bb = ' <span class="bb own" title="BuyBox bu satıcıda">BB</span>' if r.get("bb_bizde") else ""
    sayfa_ad = str(r.get("sayfa_satici") or "")
    ipucu = f"Sayfadaki adı: {sayfa_ad}" if sayfa_ad and sayfa_ad != r.get("satici") else ""
    return (f'<span class="pt-satici" title="{_e(ipucu)}">{_e(r.get("satici") or sayfa_ad or "-")}{bb}'
            + (f"<small>{' · '.join(alt)}</small>" if alt else "") + "</span>")


def _durum_hucre(r: dict) -> str | None:
    """Satışta değilse satış/fiyat hücreleri yerine gösterilecek etiket."""
    d = r.get("durum") or ""
    if d == "Okunamadı":
        return '<span class="pt-veriyok" title="Ürün sayfası okunamadı; satıcının satış yapmadığı anlamına gelmez">?</span>'
    if d == "Satıcı listede yok":
        return '<span class="pt-durum" title="Bu satıcı şu an ürün sayfasındaki satıcılar arasında yok">Satıcı listede yok</span>'
    if d == "Stokta yok" and r.get("satis") is None:
        return '<span class="pt-durum" title="Satıcı listeliyor ama stokta yok">Stokta yok</span>'
    return None


def _satis_hucre(r: dict) -> str:
    liste = f'<span class="pt-liste">{_fmt2(r["liste"])}</span>' if r.get("liste") else ""
    eski = " eski" if r.get("eski_veri") else ""
    ipucu = "Sayfada görünen satış fiyatı" + (f" · Eski veri: {r['eski_veri']}" if r.get("eski_veri") else "")
    stok = '<span class="pt-etiket" style="color:#A3261A">Stokta yok</span>' if r.get("durum") == "Stokta yok" else ""
    pill = f'<span class="pt-pill pt-gri{eski}" title="{_e(ipucu)}">{_fmt2(r["satis"])}</span>'
    return liste + _link(pill, r.get("link")) + stok


def _sepet_hucre(r: dict) -> str:
    if not r.get("sepette"):
        kamp = str(r.get("sepet_kampanyasi") or "")
        return f'<span class="pt-sepet-sat">{_e(kamp)}</span>' if kamp else '<span class="pt-yok" title="Sepette indirim yok">–</span>'
    fark = (r.get("satis") or 0) - r["sepette"]
    kamp = str(r.get("sepet_kampanyasi") or "")
    return (f'<span class="pt-pill pt-sepet" title="{_e(kamp or "Sepette indirimli fiyat")}">{_fmt2(r["sepette"])}</span>'
            f'<span class="pt-etiket sepet">−{_fmt2(fark)} sepette</span>')


def _kupon_hucre(r: dict) -> str:
    metin = str(r.get("kupon") or "").strip()
    if not metin:
        return '<span class="pt-yok" title="Kupon yok">–</span>'
    satirlar = ""
    for k in metin.split(" · "):
        k = k.strip()
        if not k:
            continue
        plus = "Plus" in k
        ana, _, detay = k.partition(" kupon")
        satirlar += (f'<span class="pt-kupon-sat{" plus" if plus else ""}" title="{_e(k)}"><b>{_e(ana)} kupon</b>'
                     f'{_e(detay)}</span>')
    ek = ""
    if r.get("kupon_indirimi"):
        ek = f'<span class="pt-etiket kupon">−{_fmt2(r["kupon_indirimi"])} kuponla</span>'
    else:
        ek = '<span class="pt-etiket" style="color:#8A9A90" title="Alt limit karşılanmıyor ya da Plus\'a özel">fiyata etkisi yok</span>'
    return f'<div class="pt-kupon-kutu">{satirlar}{ek}</div>'


def _efektif_hucre(r: dict, en_ucuz: bool) -> str:
    v = r.get("efektif")
    if v is None:
        return '<span class="pt-yok">–</span>'
    parcalar = []
    if r.get("sepette"):
        parcalar.append("sepet indirimi")
    if r.get("kupon_indirimi"):
        parcalar.append("kupon")
    ipucu = "Satış fiyatı" + (" + " + " + ".join(parcalar) if parcalar else "") + " sonrası ödenen fiyat"
    if en_ucuz:
        ipucu += " · Bu modelde takip edilen ilanların en ucuzu"
    sinif = "pt-ok" if en_ucuz else "pt-nt"
    eski = " eski" if r.get("eski_veri") else ""
    kupa = '<span class="kupa">🏆</span>' if en_ucuz else ""
    return f'<span class="pt-pill {sinif}{eski}" style="font-size:13.5px" title="{_e(ipucu)}">{_fmt2(v)}{kupa}</span>'


def _degisim_hucre(r: dict) -> str:
    once, simdi = r.get("onceki_efektif"), r.get("efektif")
    if once is None or simdi is None or abs(once - simdi) < 0.5:
        return '<span class="pt-yok" title="Takip başladığından beri fiyat değişmedi">–</span>'
    fark = simdi - once
    yuzde = fark / once * 100 if once else 0
    sinif, ok = ("dus", "▼") if fark < 0 else ("art", "▲")
    zaman = str(r.get("son_degisim") or "")
    kisa = zaman[:5] + zaman[10:] if len(zaman) >= 16 else zaman
    ipucu = f"Önceki efektif fiyat {_fmt2(once)} · değişim {zaman}"
    yz = f"{abs(yuzde):.1f}".replace(".", ",")
    return (f'<span class="pt-degisim {sinif}" title="{_e(ipucu)}">'
            f'{ok} {_fmt2(abs(fark))}<small>%{yz} · {_e(kisa)}</small></span>')


def _bb_hucre(r: dict) -> str:
    sahip = str(r.get("bb_sahibi") or "")
    if not sahip:
        return '<span class="pt-yok">–</span>'
    fiyat = f' <b>{_fmt2(r["bb_fiyat"])}</b>' if r.get("bb_fiyat") else ""
    resmi = '<span class="resmi" title="BuyBox resmi satıcıda">RESMİ</span>' if r.get("resmi_bb") else ""
    if r.get("bb_bizde"):
        return f'<span class="pt-bbh bizde" title="BuyBox bu satıcıda">✓ Bu satıcıda{resmi}</span>'
    return f'<span class="pt-bbh" title="BuyBox sahibi ve fiyatı">{_e(sahip)}{fiyat}{resmi}</span>'


def rakip_tablosu(satirlar: list[dict], not_: str = "") -> None:
    gruplar: dict[str, list[dict]] = {}
    for r in satirlar:
        gruplar.setdefault(r["model"], []).append(r)
    bas = ("<th>Model</th><th>Pazaryeri</th><th>Satıcı</th><th>Satış Fiyatı<small>Sayfada görünen</small></th>"
           "<th>Sepette<small>Sepet indirimi</small></th><th>Kupon<small>Tutar · alt limit · son tarih</small></th>"
           "<th>Efektif Fiyat<small>Sepet + kupon sonrası</small></th><th>Değişim<small>Son fiyat değişimi</small></th>"
           "<th>BuyBox<small>Sayfadaki sahibi</small></th>")
    govde = ""
    for model, grup in gruplar.items():
        fiyatlar = [r["efektif"] for r in grup if r.get("efektif") is not None]
        en_dusuk = min(fiyatlar) if len(fiyatlar) > 1 else None
        for i, r in enumerate(grup):
            ilk = " grp-ilk" if i == 0 else ""
            satir = _model_hucre(r, len(grup)) if i == 0 else ""
            satir += f'<td class="{ilk.strip()}">{_platform_hucre(r)}</td><td class="{ilk.strip()}">{_satici_hucre(r)}</td>'
            durum = _durum_hucre(r)
            if durum:
                satir += f'<td class="{ilk.strip()}" colspan="5">{durum}</td>'
            else:
                en_ucuz = en_dusuk is not None and r.get("efektif") is not None and abs(r["efektif"] - en_dusuk) < 0.01
                satir += "".join(f'<td class="{ilk.strip()}">{h}</td>' for h in (
                    _satis_hucre(r), _sepet_hucre(r), _kupon_hucre(r), _efektif_hucre(r, en_ucuz), _degisim_hucre(r)))
            satir += f'<td class="{ilk.strip()}">{_bb_hucre(r)}</td>'
            govde += f"<tr>{satir}</tr>"
    if not govde:
        govde = '<tr><td colspan="9" style="padding:28px !important;color:#8A9A90">Bu filtreye uyan ilan yok.</td></tr>'
    st.markdown(
        f'<table class="pt-tablo" lang="tr"><thead><tr>{bas}</tr></thead><tbody>{govde}</tbody></table>'
        '<div class="pt-foot-note" style="flex-wrap:wrap">'
        '<span><span class="bb own">BB</span> BuyBox bu satıcıda</span>'
        "<span>🏆 Modelde takip edilen ilanların en ucuzu (efektif fiyata göre)</span>"
        '<span><span class="pt-veriyok">?</span> sayfa okunamadı · <span class="pt-pill pt-gri eski" style="padding:0 6px">kesikli</span> eski veri</span>'
        "<span>Efektif fiyat: sepet indirimi ve alt limiti karşılanan kupon düşüldükten sonra ödenen fiyat. "
        "Plus'a özel ve kişiye özel fiyatlar dahil değildir.</span>"
        + (f"<span>{html.escape(not_)}</span>" if not_ else "") + "</div>",
        unsafe_allow_html=True)


def rakip_govde(satirlar: list[dict], degisen_ids: set, dusen_ids: set, not_: str = "") -> None:
    kpi_kartlari(satirlar, len(degisen_ids), len(dusen_ids))
    with st.container(key="pt_rakip_tablosu"):
        a, b = st.columns([1.1, 1.3])
        with a:
            st.markdown('<div class="pt-table-head"><h2>İlan bazlı rakip fiyatları</h2></div>', unsafe_allow_html=True)
        with b:
            secenekler = ["Tümü", "Kuponlu", "Sepet indirimli", "Fiyatı değişen", "BuyBox'ta"]
            filtre = st.segmented_control("Filtre", secenekler, default="Tümü",
                                          label_visibility="collapsed", key="pt_filtre") or "Tümü"
        if filtre == "Kuponlu":
            satirlar = [r for r in satirlar if r.get("kupon")]
        elif filtre == "Sepet indirimli":
            satirlar = [r for r in satirlar if r.get("sepette")]
        elif filtre == "Fiyatı değişen":
            satirlar = [r for r in satirlar if r["_id"] in degisen_ids]
        elif filtre == "BuyBox'ta":
            satirlar = [r for r in satirlar if r.get("bb_bizde")]
        rakip_tablosu(satirlar, not_)


# --------------------------------------------------------------------------
# Alt bant
# --------------------------------------------------------------------------
def alt_bant() -> None:
    kutular = ""
    for k in PLATFORMLAR:
        logo = KANAL_LOGOLARI.get(k, "").replace('height="22"', 'height="38"')
        kutular += '<div class="pt-logo">' + (logo or html.escape(k)) + "</div>"
    st.markdown(
        '<div class="pt-footer" lang="tr"><div class="top"><span>Takip edilen pazaryerleri</span>'
        '<span style="text-transform:none;letter-spacing:0;font-weight:500">Rakip Fiyat Takibi · saat başı güncellenir</span></div>'
        f'<div class="pt-logos iki">{kutular}</div></div>',
        unsafe_allow_html=True)
