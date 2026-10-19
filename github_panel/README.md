# Halka Açık Ürün Bilgileri

Pazaryerleri ve mağaza sitelerinin herkese açık ürün sayfalarındaki bilgileri (satış fiyatı, sepette fiyat,
kupon, kampanya ve satıcı bilgisi) gösteren Streamlit paneli.

Veriler `Rakip_Fiyat_Takip` adlı Google Sheet'ten okunur (`Guncel`, `Gecmis`, `Durum` sayfaları).

## Sekmeler
- **Ürün Bilgileri:** model bazında her ilan için satış fiyatı, sepette fiyat, kupon (tutar, alt limit,
  maks. indirim, son tarih), efektif fiyat, son fiyat değişimi ve BuyBox sahibi. Arama, pazaryeri/satıcı
  filtresi, Kuponlu / Sepet indirimli / Fiyatı değişen / BuyBox'ta filtreleri, Excel'e aktarma.
- **Değişim Geçmişi:** seçilen modelin efektif fiyat grafiği ve tüm değişim kayıtları, Excel'e aktarma.

## Kurulum (Streamlit Community Cloud)
1. share.streamlit.io → **Create app** → bu repo, `main`, Main file path: `github_panel/app.py`.
2. **Advanced settings → Secrets** alanına service account bilgilerini (`[gcp_service_account]`) yaz.

Google Sheet bu service account'un e-posta adresiyle **Düzenleyici** olarak paylaşılmış olmalı.

## Bilgisayarda deneme (Google bağlantısı olmadan)
```
set RAKIP_YEREL_EXCEL=..\Rakip_Fiyat_Guncel.xlsx
streamlit run app.py
```
