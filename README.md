# Callula web sitesi

Callula'nın mevcut ürünleri, fiyatları, görselleri ve metinleriyle yeniden tasarlanmış statik e-ticaret sitesi. Analiz ve tasarım kararları için bkz. [docs/TASARIM.md](docs/TASARIM.md).

## Yapı

```
src/data/products.json   Tek veri kaynağı: ürünler, fiyatlar, barkodlar, açıklamalar (canlı siteden birebir)
src/content/*.html       Kurumsal ve yasal sayfaların metinleri (birebir)
src/originals/           Callula'nın orijinal fotoğrafları
src/images.py            WebP varyantları, şeffaf logo, fırça maskesi, favicon
src/build.py             Tüm sayfaları public/ altına üretir (SEO, JSON-LD, sitemap)
public/                  Yayına alınacak klasör
public/assets/css/main.css   Tüm stiller
public/assets/js/app.js      Sepet, favoriler, arama, galeri, menüler (bağımlılık yok)
```

## Komutlar

```bash
pip install pillow
python src/images.py
python src/build.py
python -m http.server 5180 --directory public
```

Ürün, fiyat veya metin değiştiğinde `src/data/products.json` dosyasını düzenleyip `python src/build.py` komutunu çalıştırmak yeterlidir.

## Yayına almadan önce bağlanması gerekenler

- **Ödeme:** Statik sitenin arkasında bir ödeme altyapısı yok. Sepet tam çalışıyor (localStorage). "Siparişi tamamla" adımı şu an siparişi WhatsApp mesajı olarak hazırlıyor (`app.js`, `checkout()`). Ticimax, iyzico veya PayTR bağlanınca yalnızca bu fonksiyon değişecek.
- **E-bülten:** Form `POST /api/bulten` adresine JSON gönderiyor. Uç nokta yoksa kullanıcıya hata mesajı gösteriliyor; sahte bir "kaydedildi" mesajı yok.
- **Üyelik:** Hesap sistemi yok; bu yüzden header'da kullanıcı simgesi bulunmuyor.
- **Sunucu:** URL'ler canlı siteyle aynı (`/yuz-kremi2`, `/kremler` ...). `404.html` sunucu ayarlarında hata sayfası olarak tanımlanmalı. Eski `/Iletisim` linki `/adres-ve-iletisim` adresine yönlendiriliyor.
