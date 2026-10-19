# Rakip Fiyat Takibi

Trendyol ve Hepsiburada'daki rakip ilanların fiyatlarını, sepette indirimlerini, kuponlarını ve BuyBox
durumunu gösteren Streamlit paneli.

Veriyi bilgisayarda saat başı çalışan `rakip_script.py` toplar ve `Rakip_Fiyat_Takip` adlı Google Sheet'e yazar
(`Guncel`, `Gecmis`, `Durum` sayfaları). Bu panel sadece o Sheet'i okur.

## Sekmeler
- **Rakip Fiyatları:** model bazında her takip edilen satıcı için satış fiyatı, sepette fiyat, kupon
  (tutar, alt limit, maks. indirim, son tarih), efektif fiyat, son fiyat değişimi ve BuyBox sahibi.
  Arama, pazaryeri/satıcı filtresi, Kuponlu / Sepet indirimli / Fiyatı değişen / BuyBox'ta filtreleri,
  Excel'e aktarma.
- **Değişim Geçmişi:** seçilen modelin efektif fiyat grafiği ve tüm değişim kayıtları, Excel'e aktarma.

## Kurulum (Streamlit Community Cloud)
1. Bu repoyu GitHub'a yükle (`app.py`, `tasarim.py`, `requirements.txt`, `.streamlit/config.toml`).
2. share.streamlit.io → **Create app** → bu repo, `main`, `app.py`.
3. **Advanced settings → Secrets** alanına service account bilgilerini yaz:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

`Rakip_Fiyat_Takip` Sheet'i bu service account'un e-posta adresiyle **Düzenleyici** olarak paylaşılmış olmalı.

## Bilgisayarda deneme (Google bağlantısı olmadan)
```
set RAKIP_YEREL_EXCEL=..\Rakip_Fiyat_Guncel.xlsx
streamlit run app.py
```
