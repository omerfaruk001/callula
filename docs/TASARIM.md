# Callula yeniden tasarım: analiz ve tasarım kararları

## 1. Mevcut site analizi (callula.com.tr, 06.10.2026)

**Altyapı:** Ticimax `elittema5` hazır teması. Montserrat yazı tipi, siyah/beyaz arayüz, temanın varsayılan bileşenleri.

**Bilgi mimarisi (canlı):**

| Sayfa | URL | Not |
|---|---|---|
| Ana sayfa | `/` | 5'li slider, 4 banner, 3 ürünlük "Ürünlerimiz" rafı |
| Ürünler | `/urunler` | 5 ürün (setler hariç) |
| Kremler | `/kremler` | Cicaplast Krem, Yüz Kremi |
| Serumlar | `/serumlar` | Nemlendirici Serum |
| Yüz Temizleme | `/yuztemizleme` | Yüz Temizleme Köpüğü |
| Setler | `/setler` | İkili Set, Dörtlü Set |
| Ürün detay | `/yuz-kremi2`, `/cicaplast-krem`, `/nemlendirici-serum`, `/yuz-temizleme-kopugu`, `/ikili-set`, `/dortlu-set`, `/nemlendirici-serum-ve-yuz-kremi` | |
| Kurumsal | `/hakkimizda`, `/adres-ve-iletisim`, `/ucretsiz-kargo`, `/odeme-yontemlerimiz` | |
| Yasal | `/iptalveiadebilgilendirmesi`, `/cerez-politikasi`, `/gizlilik-ve-guvenlik-politikasi` | |

**Ürün ve fiyatlar (KDV dahil, ürün modelinden):**

| Ürün | Liste | İndirimli | Barkod |
|---|---|---|---|
| Yüz Kremi | ₺1.800 | ₺900 | 8682520195637 |
| Yüz Temizleme Köpüğü | ₺1.100 | ₺550 | 8682520195590 |
| Cicaplast Krem | ₺1.950 | ₺975 | 8682520195576 |
| Nemlendirici Serum | ₺1.700 | ₺850 | 8682520195569 |
| Cicaplast Krem & Nemlendirici Serumu (İkili Set) | ₺3.650 | ₺1.825 | |
| Muhteşem Dörtlü Set | ₺6.550 | ₺3.275 | |
| Nemlendirici Serum Ve Yüz Kremi | ₺4.200 | ₺2.100 | canlıda "₺1.750 + KDV" |

Tüm ürünlerde %50 indirim ve ücretsiz kargo var.

**Canlı sitede tespit edilen hatalar:**
- Header'daki `İletişim` linki (`/Iletisim`) 404 veriyor.
- Footer'daki `İptal İade Koşulları` linki `http://iptalveiadebilgilendirmesi`. Bu bozuk bir mutlak URL.
- `/odeme-yontemlerimiz` sayfasının içeriği yok, ana sayfanın kopyasını gösteriyor.
- WhatsApp butonu `https://wa.me/+90/` adresine gidiyor, numara eksik.
- Banner linklerinin hepsi `#`.
- Ürün modelinde `rating: 5` var ama yorum sayısı 0. Yeni sitede puan gösterilmiyor, şemaya da eklenmiyor.
- Meta description'da ham `<br />` ve `&nbsp;` var.

## 2. Callula görsel kimliği

Kimlik, temanın kendisinden değil **logodan, ambalajdan ve fotoğraflardan** çıkarıldı:

| Token | Değer | Kaynak |
|---|---|---|
| `--ink` | `#1A2640` | Logodaki "CALLULA" yazısının lacivert rengi (piksel medyanı) |
| `--rose` | `#EE9899` | Logodaki fırça darbesi (piksel medyanı) |
| `--mist` | `#E7EFF8` | Ürün packshot'larının buz mavisi fon rengi |
| `--paper` | `#FFFFFF` | Mevcut site zemini |

- **Fırça darbesi** markanın imzası. Logoda, kutuların üstünde ve şişelerin etiketinde aynı fırça var. Yeni sitede bu fırça, logonun kendisinden çıkarılan bir maske olarak kullanılıyor (`assets/img/brush.png`). İndirim etiketinde, aktif menüde, kampanya satırında ve madde işaretlerinde görünüyor. Elle çizilmiş bir SVG kullanılmadı.
- **Packshot fonu = arayüz yüzeyi.** Ürün kartlarının ve galerinin zemini, fotoğrafların çekildiği buz mavisi fonla aynı renkte. Bu yüzden ürün fotoğrafı kutu içinde durmuyor, sayfaya karışıyor.
- **Fotoğraf dili:** bordo atlet, pembe oje, sıcak iç mekân ve çerçeveli duvar. Sayfaya yeni bir renk eklenmedi; sıcaklık fotoğraflardan geliyor.
- **Köşeler:** ambalaj dikdörtgen kutulardan oluşuyor, bu yüzden radius 0. Sistem tamamen keskin köşeli.

## 3. Tipografi kararı

Mevcut sitede kullanılan Montserrat, Ticimax temasının varsayılan fontu. Markaya ait bir tercih değil; brief'te de yasaklı listede yer alıyor. Callula'nın asıl yazı karakteri **logodaki wordmark**: geometrik, Futura ailesinden, sivri A'lı ve geniş aralıklı.

Bu yüzden logo ile aynı aileden olan **Jost** seçildi. Jost, açık lisanslı bir Futura yorumu. Sitede tek aile kullanılıyor; hiyerarşi ağırlık, boyut ve harf aralığıyla kuruluyor. Font self-host ediliyor (`woff2`; latin ve latin-ext, Türkçe karakterler ve ₺ için).

## 4. Bilgi mimarisi ve wireframe

```
HEADER   [logo]          Ürünler▾  Setler  Hakkımızda  İletişim        [ara] [♡] [sepet]
         Ürünler paneli: 4 kategori + her kategorinin ürünleri + kategori görseli

ANA SAYFA
┌──────────────────────────────┬─────────────────────────────────┐
│ fırça: Tüm ürünlerde %50      │                                 │
│ Cildiniz için en zarif        │   lifestyle portre (serum)      │
│ dokunuş.                      │                                 │
│ alt metin (mevcut marka dili) │        ┌───────────────┐        │
│ [Ürünleri keşfet]  Setler     │        │ fotoğraftaki  │        │
│                               │        │ ürün + fiyat  │        │
└──────────────────────────────┴────────┴───────────────┴────────┘
 güven satırı: ücretsiz kargo | Sağlık Bakanlığı onaylı, ÜTS kayıtlı | güvenli ödeme | 14 gün cayma
 KATEGORİ İNDEKSİ: solda büyük kategori adları, sağda üzerine gelince değişen görsel
 ÜRÜNLER: mist zemin, kartlar kutusuz, hover'da lifestyle görsel
 SETLER: tam genişlik taş duvar fotoğrafı + set içeriği listesi + fiyat
 İÇERİK İNDEKSİ: içerik maddesi → hangi üründe (etiketlerden, yeni iddia yok)
 MARKA: Hakkımızda metninden alıntı + görsel
 INSTAGRAM: @callulatr şeridi
FOOTER  logo | Kurumsal | Müşteri hizmetleri | Sosyal medya | E-bülten | güvenli alışveriş | ©
```

**Mobil:**
- Header iki satırdan tek satıra iniyor: menü, logo, arama ve sepet. Menü alttan açılan bir panelde.
- Hero'da önce görsel, sonra metin geliyor. CTA başparmak bölgesinde.
- Kategoriler yatay kaydırılan bir şerit.
- Ürün detayında galeri kaydırmalı. Ana CTA ekrandan çıkınca altta sabit bir "Sepete ekle" çubuğu beliriyor.
- Sepet, alttan açılan bir panel.

## 5. Dial değerleri

`DESIGN_VARIANCE 6 / MOTION_INTENSITY 3 / VISUAL_DENSITY 3`

Animasyonlar hover'da görsel geçişi, galeride zoom, çekmece ve panel açılışlarıyla sınırlı. Sayfa yüklenirken animasyon yok. `prefers-reduced-motion` destekleniyor.

## 6. Bilinçli olarak yapılmayanlar

- Sahte yorum, puan, istatistik ve işbirliği yok. Product şemasında `aggregateRating` yok.
- Yeni sağlık veya etki iddiası yok. Ürün metinleri birebir korundu. İçerik indeksi yalnızca etiketlerdeki INCI listelerinden türetildi.
- Koyu tema yok. Marka ve packshot'lar açık zemine göre üretilmiş. `color-scheme: light`.
- Hesap/üyelik yok. Statik sitede bunun arkasında bir sistem bulunmadığı için sahte bir giriş ekranı konmadı.
