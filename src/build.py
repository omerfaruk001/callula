"""Callula statik site üreticisi.

Tek veri kaynağı: src/data/products.json + src/content/*.html (canlı siteden birebir alınmış metinler).
Çıktı: public/ (herhangi bir statik sunucuya olduğu gibi yüklenebilir).

Kullanım:  python src/images.py   (görseller değiştiyse)
           python src/build.py
"""
from __future__ import annotations

import html
from urllib.parse import quote
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageOps

from images import OUT as IMG_DIR, SRC as ORIG_DIR, WIDTHS, slug as img_slug

ROOT = Path(__file__).resolve().parent.parent
PUB = ROOT / "public"
CONTENT = ROOT / "src" / "content"
SITE = "https://www.callula.com.tr"
WHATSAPP = "905302023453"
INSTAGRAM = "https://www.instagram.com/callulatr/"
EMAIL = "info@callula.com.tr"
ASSET_V = date.today().strftime("%Y%m%d")

DATA = json.loads((ROOT / "src" / "data" / "products.json").read_text(encoding="utf-8"))
CATS = {c["slug"]: c for c in DATA["categories"]}
PRODUCTS = DATA["products"]
P = {p["slug"]: p for p in PRODUCTS}
SINGLES = [P[s] for s in ("yuz-kremi2", "yuz-temizleme-kopugu", "cicaplast-krem", "nemlendirici-serum")]

e = html.escape


# ---------------------------------------------------------------- yardımcılar
def tl(x: float) -> str:
    s = f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"₺{s}"


def discount(p) -> int:
    return round(100 - p["price"] * 100 / p["listPrice"])


def url(slug: str) -> str:
    return "/" if slug in ("", "index") else f"/{slug}"


def icon(name: str, cls: str = "i") -> str:
    return f'<svg class="{cls}" aria-hidden="true" focusable="false"><use href="/assets/icons.svg?v={ASSET_V}#{name}"/></svg>'


@lru_cache(None)
def _dims(name: str) -> tuple[int, int]:
    for f in ORIG_DIR.iterdir():
        if img_slug(f.name) == name:
            im = ImageOps.exif_transpose(Image.open(f))
            return im.size
    raise KeyError(name)


def img_src(name: str, w: int = 1200) -> str:
    avail = [x for x in WIDTHS if (IMG_DIR / f"{name}-{x}.webp").exists()]
    best = min((x for x in avail if x >= w), default=max(avail))
    return f"/assets/img/{name}-{best}.webp"


def img(name: str, alt: str, sizes: str, *, cls: str = "", lazy: bool = True, priority: bool = False,
        pos: str | None = None, max_w: int = 1800) -> str:
    w, h = _dims(name)
    avail = [x for x in WIDTHS if x <= max_w and (IMG_DIR / f"{name}-{x}.webp").exists()]
    srcset = ", ".join(f"/assets/img/{name}-{x}.webp {min(x, w)}w" for x in avail)
    mid = img_src(name, 800)
    attrs = [f'src="{mid}"', f'srcset="{srcset}"', f'sizes="{sizes}"', f'width="{w}"', f'height="{h}"', f'alt="{e(alt)}"']
    if cls:
        attrs.insert(0, f'class="{cls}"')
    if priority:
        attrs.append('fetchpriority="high"')
    elif lazy:
        attrs.append('loading="lazy"')
    attrs.append('decoding="async"')
    if pos:
        attrs.append(f'style="object-position:{pos}"')
    return "<img " + " ".join(attrs) + ">"


def cat_label(p) -> str:
    return CATS[p["category"]]["single"] if p.get("category") else "Set"


def price_html(p, cls: str = "price") -> str:
    return (
        f'<p class="{cls}"><span class="sr">İndirimli fiyat: </span><span class="now">{tl(p["price"])}</span>'
        f'<span class="sr">, liste fiyatı: </span><s class="was">{tl(p["listPrice"])}</s></p>'
    )


def sale_badge(p) -> str:
    return f'<span class="sale brush"><span class="sr">İndirim: </span>%{discount(p)}</span>'


def fav_button(p, label: bool = False) -> str:
    extra = '<span class="fav-label" aria-hidden="true">Favorilere ekle</span>' if label else ""
    return (
        f'<button class="icon-btn fav-btn" type="button" aria-pressed="false" data-fav="{p["slug"]}">'
        f'{icon("heart", "i off")}{icon("heart-fill", "i on")}{extra}'
        f'<span class="sr">{e(p["name"])} favorilere ekle</span></button>'
    )


def card(p, sizes="(max-width: 759px) 50vw, (max-width: 1023px) 50vw, 25vw", lazy=True, hidden=False) -> str:
    main = img(p["card"], f'{p["name"]} ürün fotoğrafı', sizes, cls="main" + ("" if p.get("hover") else " solo"),
               lazy=lazy, pos="45% 50%" if p["category"] in ("setler", None) else None, max_w=1200)
    alt = img(p["hover"], f'{p["name"]} kullanım fotoğrafı', sizes, cls="alt", max_w=1200, pos="50% 30%") if p.get("hover") else ""
    h = " hidden" if hidden else ""
    return f"""<li{h} data-card="{p['slug']}" data-price="{p['price']}" data-order="{PRODUCTS.index(p)}"><article class="card">
  <div class="card-media">{main}{alt}</div>
  {sale_badge(p)}
  {fav_button(p)}
  <div class="card-body">
    <p class="card-cat">{cat_label(p)}</p>
    <h3 class="card-title"><a href="{url(p['slug'])}">{e(p['name'])}</a></h3>
    {price_html(p)}
    <p class="card-ship">{icon('truck')}<span>Ücretsiz kargo</span></p>
    <div class="card-add"><button class="btn btn--line" type="button" data-add="{p['slug']}">Sepete ekle<span class="sr">: {e(p['name'])}</span></button></div>
  </div>
</article></li>"""


def catalog_json() -> str:
    cat = {
        p["slug"]: {
            "n": p["name"], "p": p["price"], "lp": p["listPrice"], "u": url(p["slug"]),
            "i": img_src(p["card"], 480), "c": cat_label(p),
            "q": " ".join([p["name"], cat_label(p), p.get("menuName", ""), p.get("lead", ""), p.get("ingredients") or "",
                           " ".join(p.get("tags", [])),
                           " ".join(b for c in ([p["slug"]] + p["contains"]) for s in P[c]["sections"] for b in s["benefits"]),
                           " ".join(P[c]["name"] + " " + (P[c]["ingredients"] or "") for c in p["contains"])]).lower(),
        }
        for p in PRODUCTS
    }
    return json.dumps(cat, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


# ---------------------------------------------------------------- iskelet
def head(path, title, desc, og_image, jsonld, noindex, og_type, preload):
    canonical = SITE + (path if path != "/" else "/")
    ld = "".join(
        f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False, separators=(",", ":"))}</script>'
        for x in jsonld
    )
    og_img = og_image or f"{SITE}/assets/img/og-callula.jpg"
    robots = '<meta name="robots" content="noindex, follow">' if noindex else '<meta name="robots" content="index, follow, max-image-preview:large">'
    pre = "".join(
        f'<link rel="preload" as="image" href="{p["href"]}" imagesrcset="{p["srcset"]}" imagesizes="{p["sizes"]}" fetchpriority="high">'
        for p in preload
    )
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{robots}
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#ffffff">
<meta property="og:site_name" content="Callula">
<meta property="og:locale" content="tr_TR">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/favicon-180.png">
<link rel="preload" href="/assets/fonts/jost-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/jost-latin-ext.woff2" as="font" type="font/woff2" crossorigin>
{pre}
<link rel="stylesheet" href="/assets/css/main.css?v={ASSET_V}">
{ld}
</head>"""


def header(active: str = "") -> str:
    def cur(k):
        return ' aria-current="page"' if active == k else ""

    cols = []
    for c in DATA["categories"]:
        items = "".join(
            f'<li><a href="{url(p["slug"])}">{e(p.get("menuName", p["name"]))}</a></li>'
            for p in PRODUCTS if p["category"] == c["slug"]
        )
        cols.append(f'<div class="mega-col"><h3><a href="{url(c["slug"])}">{c["name"]}</a></h3><ul>{items}</ul></div>')
    feat = "".join(
        f'<a href="{url(p["slug"])}">{img(p["hover"] or p["card"], "", "160px", max_w=480, pos="50% 30%")}{e(p["name"])}</a>'
        for p in (P["nemlendirici-serum"], P["yuz-kremi2"])
    )
    return f"""<a class="skip" href="#icerik">İçeriğe geç</a>
<p class="announce" data-announce>Tüm ürünlerde ücretsiz kargo</p>
<header class="site-header" data-header>
  <div class="wrap header-bar">
    <button class="icon-btn menu-toggle" type="button" data-open="mobil-menu" aria-haspopup="dialog">{icon('list')}<span class="sr">Menüyü aç</span></button>
    <a class="logo" href="/"><img src="/assets/img/callula-logo-260.webp" srcset="/assets/img/callula-logo-260.webp 260w, /assets/img/callula-logo-520.webp 520w" sizes="156px" width="260" height="67" alt="Callula"></a>
    <nav class="main-nav" aria-label="Ana menü">
      <ul>
        <li><button class="nav-link" type="button" aria-expanded="false" aria-controls="urun-paneli" data-mega{' aria-current="page"' if active == 'urunler' else ''}>Ürünler{icon('caret-down')}</button></li>
        <li><a class="nav-link" href="/setler"{cur('setler')}>Setler</a></li>
        <li><a class="nav-link" href="/hakkimizda"{cur('hakkimizda')}>Hakkımızda</a></li>
        <li><a class="nav-link" href="/adres-ve-iletisim"{cur('iletisim')}>İletişim</a></li>
      </ul>
    </nav>
    <div class="header-actions">
      <button class="icon-btn" type="button" aria-expanded="false" aria-controls="arama-paneli" data-search-toggle>{icon('magnifying-glass')}<span class="sr">Ürün ara</span></button>
      <a class="icon-btn fav-link" href="/favoriler">{icon('heart')}<span class="count" data-fav-count></span><span class="sr">Favorilerim</span></a>
      <button class="icon-btn" type="button" data-open="sepet" aria-haspopup="dialog">{icon('handbag-simple')}<span class="count" data-cart-count></span><span class="sr">Sepetim</span></button>
    </div>
  </div>
  <div class="mega" id="urun-paneli" hidden>
    <div class="wrap mega-grid">
      {''.join(cols)}
      <div class="mega-feature">{feat}</div>
      <div class="mega-all"><a class="link-arrow" href="/urunler">Tüm ürünler {icon('arrow-right')}</a></div>
    </div>
  </div>
  <div class="search-panel" id="arama-paneli" hidden>
    <div class="wrap">
      <form class="search-form" action="/arama" method="get" role="search">
        {icon('magnifying-glass')}
        <label class="sr" for="q-header">Ürün ara</label>
        <input id="q-header" name="q" type="search" autocomplete="off" placeholder="Ürün ya da içerik ara" data-search-input>
        <button class="icon-btn" type="button" data-search-close>{icon('x')}<span class="sr">Aramayı kapat</span></button>
      </form>
      <ul class="search-results" data-search-results aria-live="polite"></ul>
    </div>
  </div>
</header>"""


def mobile_menu() -> str:
    cats = "".join(
        f'<li><a href="{url(c["slug"])}"><span class="mm-cat-img">{img(c["image"], "", "45vw", max_w=480, pos=c["focus"])}</span>'
        f'<span class="mm-cat-nm">{c["name"]}</span><span class="mm-ct">{sum(1 for p in PRODUCTS if p["category"] == c["slug"])} ürün</span></a></li>'
        for c in DATA["categories"]
    )
    prods = "".join(
        f'<li><a href="{url(p["slug"])}"><span class="thumb">{img(p["card"], "", "120px", max_w=480)}</span>'
        f'<span class="mm-p-nm">{e(p.get("menuName", p["name"]))}</span><span class="mm-p-pr">{tl(p["price"])}</span></a></li>'
        for p in PRODUCTS
    )
    links = "".join(
        f'<li><a href="{h}">{n}{icon("arrow-right")}</a></li>'
        for h, n in (("/urunler", "Tüm ürünler"), ("/setler", "Setler"), ("/hakkimizda", "Hakkımızda"), ("/adres-ve-iletisim", "İletişim"))
    )
    return f"""<dialog class="sheet mm" id="mobil-menu" aria-label="Menü">
  <div class="drawer-head"><a href="/"><img src="/assets/img/callula-logo-260.webp" width="124" height="32" alt="Callula ana sayfa"></a><button class="icon-btn" type="button" data-close>{icon('x')}<span class="sr">Menüyü kapat</span></button></div>
  <div class="mm-body">
    <p class="mm-promo"><span class="brush">%50 indirim</span> Tüm ürünlerde ücretsiz kargo</p>
    <form class="mm-search" action="/arama" method="get" role="search">
      {icon('magnifying-glass')}<label class="sr" for="q-menu">Ürün ara</label>
      <input id="q-menu" name="q" type="search" autocomplete="off" placeholder="Ürün ya da içerik ara" enterkeyhint="search">
    </form>
    <section class="mm-sec" aria-labelledby="mm-kat"><h2 id="mm-kat">Kategoriler</h2><ul class="mm-cats">{cats}</ul></section>
    <section class="mm-sec" aria-labelledby="mm-urun"><h2 id="mm-urun">Ürünler</h2><ul class="mm-prods">{prods}</ul></section>
    <nav class="mm-sec" aria-label="Sayfalar"><ul class="mm-links">{links}</ul></nav>
    <p class="mm-social"><a href="{INSTAGRAM}" rel="noopener" target="_blank">{icon('instagram-logo')}@callulatr</a></p>
  </div>
  <div class="mm-bar">
    <a href="/favoriler">{icon('heart')}<span>Favorilerim</span><span class="count" data-fav-count></span></a>
    <button type="button" data-open="sepet">{icon('handbag-simple')}<span>Sepetim</span><span class="count" data-cart-count></span></button>
    <a href="https://wa.me/{WHATSAPP}" rel="noopener" target="_blank">{icon('whatsapp-logo')}<span>WhatsApp</span></a>
  </div>
</dialog>"""


def cart_drawer() -> str:
    return f"""<dialog class="drawer" id="sepet" aria-labelledby="sepet-baslik">
  <div class="drawer-head"><h2 id="sepet-baslik">Sepetim <span data-cart-count-text></span></h2><button class="icon-btn" type="button" data-close>{icon('x')}<span class="sr">Sepeti kapat</span></button></div>
  <p class="drawer-note">{icon('truck')}Tüm ürünlerde ücretsiz kargo</p>
  <div class="drawer-body" data-cart-lines></div>
  <div class="drawer-foot" data-cart-foot></div>
</dialog>"""


def footer() -> str:
    return f"""<footer class="site-footer">
  <div class="wrap footer-top">
    <div class="footer-brand">
      <img src="/assets/img/callula-logo-260.webp" srcset="/assets/img/callula-logo-260.webp 260w, /assets/img/callula-logo-520.webp 520w" sizes="168px" width="260" height="67" alt="Callula" loading="lazy">
      <p>Nazik, etkili ve güvenilir bakım.</p>
    </div>
    <nav aria-labelledby="f-kurumsal"><h2 id="f-kurumsal">KURUMSAL</h2>
      <ul class="footer-links"><li><a href="/hakkimizda">Hakkımızda</a></li><li><a href="/adres-ve-iletisim">Adres ve İletişim</a></li></ul></nav>
    <nav aria-labelledby="f-musteri"><h2 id="f-musteri">MÜŞTERİ HİZMETLERİ</h2>
      <ul class="footer-links">
        <li><a href="/iptalveiadebilgilendirmesi">İptal İade Koşulları</a></li>
        <li><a href="/cerez-politikasi">Çerez Politikası</a></li>
        <li><a href="/gizlilik-ve-guvenlik-politikasi">Gizlilik Sözleşmesi</a></li>
        <li><a href="/odeme-yontemlerimiz">Güvenli Ödeme</a></li>
        <li><a href="/ucretsiz-kargo">Ücretsiz Kargo</a></li>
      </ul></nav>
    <nav class="social-col" aria-labelledby="f-sosyal"><h2 id="f-sosyal">SOSYAL MEDYA</h2>
      <ul class="footer-links"><li><a href="{INSTAGRAM}" rel="noopener" target="_blank">Instagram</a></li><li><a href="https://wa.me/{WHATSAPP}" rel="noopener" target="_blank">WhatsApp</a></li></ul></nav>
    <div class="newsletter-col">
      <h2 id="f-bulten">E-BÜLTEN ÜYELİK</h2>
      <form class="newsletter" action="/api/bulten" method="post" data-newsletter novalidate aria-labelledby="f-bulten">
        <label for="bulten-eposta">Kampanyalardan ve yeni ürünlerden e-posta ile haberdar olun.</label>
        <div class="row"><input id="bulten-eposta" name="email" type="email" autocomplete="email" required placeholder="ornek@eposta.com" aria-describedby="bulten-mesaj"><button type="submit">Abone ol</button></div>
        <p class="form-msg" id="bulten-mesaj" role="status"></p>
        <small>Aboneliğinizi dilediğiniz zaman sonlandırabilirsiniz. <a href="/gizlilik-ve-guvenlik-politikasi">Gizlilik Sözleşmesi</a></small>
      </form>
    </div>
  </div>
  <div class="wrap footer-bottom">
    <div class="secure"><span>İnternette güvenli alışveriş</span><img src="/assets/img/odeme-kartlari.png" width="118" height="30" alt="Mastercard ve Visa ile ödeme" loading="lazy"></div>
    <p>Copyright © 2024 Callula Kozmetik İthalat İhracat LTD.Şti. Tüm hakları saklıdır.</p>
  </div>
</footer>"""


def page(path: str, title: str, desc: str, main: str, *, active: str = "", og_image: str | None = None,
         jsonld: list | None = None, noindex: bool = False, og_type: str = "website", preload: list | None = None,
         extra: str = "", body_class: str = "") -> str:
    bc = f' class="{body_class}"' if body_class else ""
    return f"""{head(path, title, desc, og_image, jsonld or [], noindex, og_type, preload or [])}
<body{bc}>
{header(active)}
<main id="icerik">
{main}
</main>
{footer()}
{mobile_menu()}
{cart_drawer()}
{extra}
<script type="application/json" id="catalog">{catalog_json()}</script>
<script src="/assets/js/app.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


def write(path: str, html_text: str) -> None:
    out = PUB / "index.html" if path == "/" else PUB / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(re.sub(r"\n\s*\n", "\n", html_text), encoding="utf-8")


def crumbs(items: list[tuple[str, str | None]]) -> tuple[str, dict]:
    lis = []
    for name, href in items:
        lis.append(f'<li><a href="{href}">{e(name)}</a></li>' if href else f'<li aria-current="page">{e(name)}</li>')
    ld = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, **({"item": SITE + h} if h else {})}
            for i, (n, h) in enumerate(items)
        ],
    }
    return f'<nav class="crumbs wrap" aria-label="Sayfa konumu"><ol>{"".join(lis)}</ol></nav>', ld


def preload_for(name: str, sizes: str) -> dict:
    avail = [x for x in WIDTHS if (IMG_DIR / f"{name}-{x}.webp").exists()]
    w, _ = _dims(name)
    return {"href": img_src(name, 800), "srcset": ", ".join(f"/assets/img/{name}-{x}.webp {min(x, w)}w" for x in avail), "sizes": sizes}


ORG_LD = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Callula",
    "legalName": "Callula Kozmetik İthalat İhracat Ltd. Şti.",
    "url": SITE,
    "logo": f"{SITE}/assets/img/callula-logo-520.png",
    "email": EMAIL,
    "telephone": "+90 530 202 34 53",
    "sameAs": [INSTAGRAM],
    "address": {
        "@type": "PostalAddress", "streetAddress": "Çenedağ Mah., Alçicek Sok. No:25/1",
        "addressLocality": "Derince", "addressRegion": "Kocaeli", "addressCountry": "TR",
    },
}


# ---------------------------------------------------------------- ana sayfa
INGREDIENTS = [
    ("Hyaluronik asit", "Hyaluronic Acid, Sodium Hyaluronate", ("hyaluronic acid", "sodium hyaluronate")),
    ("Niacinamide", "Niacinamide", ("niacinamide",)),
    ("Kolajen", "Hydrolyzed Collagen", ("collagen",)),
    ("Retinol", "Retinol", ("retinol",)),
    ("Meyan kökü", "Glycyrrhiza Glabra Root", ("glycyrrhiza",)),
    ("Panthenol", "Panthenol", ("panthenol", "pantenol")),
    ("E vitamini", "Tocopherol", ("tocopherol",)),
    ("Shea yağı", "Butyrospermum Parkii Butter", ("butyrospermum",)),
]


def ingredient_index() -> str:
    lis = []
    for name, inci, keys in INGREDIENTS:
        found = [p for p in SINGLES if any(k in (p["ingredients"] or "").lower() for k in keys)]
        links = ", ".join(f'<a href="{url(p["slug"])}">{e(p["name"])}</a>' for p in found)
        lis.append(f'<li><span class="nm">{name}</span><span class="inci">{inci}</span><span class="in">{links}</span></li>')
    return "".join(lis)


def home() -> None:
    hero_img = "title-553cd388-0"
    serum = P["nemlendirici-serum"]
    d4 = P["dortlu-set"]
    cats = []
    rail = []
    visuals = []
    for i, c in enumerate(DATA["categories"]):
        items = [p for p in PRODUCTS if p["category"] == c["slug"]]
        names = ", ".join(p.get("menuName", p["name"]) for p in items)
        cats.append(
            f'<li><a class="cat-link{" is-active" if i == 0 else ""}" href="{url(c["slug"])}" data-cat="{i}">'
            f'<span class="nm">{c["name"]}</span><span class="ct">{len(items)} ürün</span><span class="items">{e(names)}</span></a></li>'
        )
        visuals.append(img(c["image"], "", "(max-width: 1023px) 50vw, 55vw", cls="is-active" if i == 0 else "", pos=c["focus"]))
        rail.append(
            f'<li><a href="{url(c["slug"])}">{img(c["image"], "", "66vw", pos=c["focus"], max_w=800)}'
            f'<span class="nm">{c["name"]}</span><span class="ct">{len(items)} ürün</span></a></li>'
        )
    set_items = "".join(
        f'<li><a href="{url(s)}"><span class="thumb">{img(P[s]["card"], "", "52px", max_w=480)}</span><span>{e(P[s]["name"])}</span></a></li>'
        for s in d4["contains"]
    )
    more = "".join(
        f"""<li class="set-row">{img(p['card'], f"{p['name']} ürün fotoğrafı", "(max-width: 759px) 112px, 20vw", pos="40% 50%", max_w=800)}
        <div class="set-row-body"><h3><a href="{url(p['slug'])}">{e(p['name'])}</a></h3>{price_html(p)}<p class="card-ship">{icon('truck')}<span>Ücretsiz kargo</span></p></div></li>"""
        for p in (P["ikili-set"], P["nemlendirici-serum-ve-yuz-kremi"])
    )
    hid, notab = ' aria-hidden="true"', ' tabindex="-1"'
    chip_order = [serum] + [p for p in PRODUCTS if p is not serum]
    chip_items = "".join(
        f'<li class="chip-item"{"" if i == 0 else hid}><a href="{url(p["slug"])}"{"" if i == 0 else notab}>'
        f'<span class="thumb">{img(p["card"], "", "72px", max_w=480, lazy=i > 0)}</span>'
        f'<span><small>{"Fotoğraftaki ürün" if p is serum else cat_label(p)}</small><strong title="{e(p["name"])}">{e(p["name"])}</strong>{price_html(p)}</span></a></li>'
        for i, p in enumerate(chip_order)
    )
    gram = [
        ("title-35b5a05d-4", "Callula Nemlendirici Serum ve Yüz Kremi masa üzerinde"),
        ("title-0a84e074-6", "Yüz Temizleme Köpüğü ile temizlenen eller"),
        ("title-a17d9edd-2", "Nemlendirici Serum damlalığı"),
        ("title-4f758f5c-c", "Yüz Temizleme Köpüğü ve Yüz Kremi tutan kadın"),
    ]
    gram_html = "".join(
        f'<a href="{INSTAGRAM}" rel="noopener" target="_blank">{img(n, a, "(max-width: 759px) 62vw, 25vw", max_w=1200)}</a>'
        for n, a in gram
    )
    main = f"""
<section class="hero" aria-labelledby="hero-baslik">
  <div class="hero-copy">
    <p class="brush">Tüm ürünlerde %50 indirim</p>
    <h1 id="hero-baslik">Cildiniz için en zarif dokunuş.</h1>
    <p class="sub">Nem ihtiyacı olan ciltlere uygun, doğal içerikli Callula serisini keşfedin.</p>
    <div class="hero-cta"><a class="btn" href="/urunler">Ürünleri keşfet</a><a class="link-arrow" href="/setler">Setleri incele {icon('arrow-right')}</a></div>
  </div>
  <div class="hero-media">
    {img(hero_img, "Nemlendirici Serum'u yüzüne uygulayan kadın", "(max-width: 759px) 100vw, 60vw", lazy=False, priority=True)}
    <div class="shop-chip" data-chip aria-label="Callula ürünleri" role="region">
      <ul class="chip-track">{chip_items}</ul>
    </div>
  </div>
</section>

<div class="assure"><ul class="wrap">
  <li><a href="/ucretsiz-kargo">{icon('truck')}<span>Tüm ürünlerde ücretsiz kargo</span></a></li>
  <li><a href="https://utsuygulama.saglik.gov.tr/UTS/" rel="noopener" target="_blank">{icon('seal-check')}<span>Sağlık Bakanlığı onaylı, ÜTS kayıtlı</span></a></li>
  <li><a href="/odeme-yontemlerimiz">{icon('shield-check')}<span>Güvenli ödeme</span></a></li>
  <li><a href="/iptalveiadebilgilendirmesi">{icon('package')}<span>14 gün içinde cayma hakkı</span></a></li>
</ul></div>

<section class="section wrap" aria-labelledby="kategoriler">
  <div class="section-head"><h2 id="kategoriler">Kategoriler</h2><a class="link-arrow" href="/urunler">Tüm ürünler {icon('arrow-right')}</a></div>
  <div class="cat-index" data-cat-index>
    <ul class="cat-list">{''.join(cats)}</ul>
    <div class="cat-visual" aria-hidden="true">{''.join(visuals)}</div>
  </div>
  <ul class="cat-rail">{''.join(rail)}</ul>
</section>

<section class="section section--mist" aria-labelledby="urunlerimiz">
  <div class="wrap">
    <div class="section-head"><h2 id="urunlerimiz">Ürünlerimiz</h2><a class="link-arrow" href="/urunler">Tümünü gör {icon('arrow-right')}</a></div>
    <ul class="grid-products">{''.join(card(p) for p in SINGLES)}</ul>
  </div>
</section>

<section class="section wrap" aria-labelledby="set-baslik">
  <div class="set-band">
    <div class="set-band-media">{img(d4['card'], 'Muhteşem Dörtlü Set taş duvar üzerinde', '(max-width: 1023px) 100vw, 58vw', pos='38% 50%')}</div>
    <div class="set-band-body">
      <p class="card-cat">Setler</p>
      <h2 id="set-baslik">{d4['name']}</h2>
      <ul class="set-items">{set_items}</ul>
      <div>{sale_badge(d4)}</div>
      {price_html(d4)}
      <div class="set-actions"><button class="btn" type="button" data-add="{d4['slug']}">Sepete ekle</button><a class="link-arrow" href="{url(d4['slug'])}">Seti incele {icon('arrow-right')}</a></div>
    </div>
  </div>
  <ul class="set-more">{more}</ul>
</section>

<section class="section section--mist" aria-labelledby="icerikler">
  <div class="wrap">
    <div class="section-head"><h2 id="icerikler">İçerikler</h2></div>
    <ul class="ingredients">{ingredient_index()}</ul>
    <p class="note">Liste, ürün etiketlerinde yer alan içerik maddelerinden hazırlanmıştır. Tam içerik listeleri ürün sayfalarındadır.</p>
  </div>
</section>

<section class="section wrap" aria-labelledby="hikaye">
  <div class="story">
    <div class="story-media">{img('title-feeb8944-b', 'Yüz Temizleme Köpüğü kullanan gülümseyen kadın', '(max-width: 759px) 100vw, 40vw', pos='50% 30%')}</div>
    <div>
      <h2 class="sr" id="hikaye">Hikayemiz</h2>
      <blockquote><p>Güzelliğin yalnızca dış görünüşten ibaret olmadığını, aynı zamanda iyi hissetmekle başladığını biliyoruz.</p></blockquote>
      <a class="link-arrow" href="/hakkimizda">Hakkımızda {icon('arrow-right')}</a>
    </div>
  </div>
</section>

<section class="section section--mist" aria-labelledby="instagram">
  <div class="wrap">
    <div class="gram-head"><h2 id="instagram"><a href="{INSTAGRAM}" rel="noopener" target="_blank">@callulatr</a></h2><a class="link-arrow" href="{INSTAGRAM}" rel="noopener" target="_blank">{icon('instagram-logo')} Instagram'da takip edin</a></div>
    <div class="gram">{gram_html}</div>
  </div>
</section>
"""
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Callula", "url": SITE,
               "potentialAction": {"@type": "SearchAction", "target": f"{SITE}/arama?q={{search_term_string}}",
                                   "query-input": "required name=search_term_string"}}
    write("/", page("/", "Callula | Nazik, etkili ve güvenilir cilt bakımı",
                    "Nem ihtiyacı olan ciltlere uygun, doğal içerikli Callula serisini keşfedin. Yüz kremi, serum, yüz temizleme köpüğü ve setler. Tüm ürünlerde ücretsiz kargo.",
                    main, jsonld=[ORG_LD, site_ld],
                    preload=[preload_for(hero_img, "(max-width: 759px) 100vw, 60vw")]))


# ---------------------------------------------------------------- listeleme
def listing(slug: str, title: str, items: list, *, tile: tuple[str, str] | None = None, lead: str = "",
            desc: str = "") -> None:
    path = url(slug)
    chips = [("urunler", "Tümü")] + [(c["slug"], c["name"]) for c in DATA["categories"]]
    cur = ' aria-current="page"'
    chips_html = "".join(f'<li><a href="{url(s)}"{cur if s == slug else ""}>{n}</a></li>' for s, n in chips)
    crumb_html, crumb_ld = crumbs([("Anasayfa", "/"), (title, None)] if slug == "urunler"
                                  else [("Anasayfa", "/"), ("Ürünler", "/urunler"), (title, None)])
    list_ld = {
        "@context": "https://schema.org", "@type": "ItemList", "name": title,
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + url(p["slug"]), "name": p["name"]}
                            for i, p in enumerate(items)],
    }
    if len(items) == 1:
        p = items[0]
        others = [x for x in SINGLES + [P["dortlu-set"]] if x is not p][:4]
        body = f"""
<section class="wrap solo-product" aria-label="{e(p['name'])}">
  <div class="solo-media">
    <a href="{url(p['slug'])}">{img(p['images'][0], f"{p['name']} kullanım fotoğrafı", '(max-width: 759px) 50vw, 28vw', lazy=False, priority=True, pos='50% 30%')}</a>
    <a href="{url(p['slug'])}">{img(p['card'], f"{p['name']} ürün fotoğrafı", '(max-width: 759px) 50vw, 28vw', lazy=False)}</a>
  </div>
  <div class="solo-body">
    <p class="card-cat">{cat_label(p)}</p>
    <h2><a href="{url(p['slug'])}" style="text-decoration:none">{e(p['name'])}</a></h2>
    <p class="lead">{e(p['lead'])}</p>
    <div>{sale_badge(p)}</div>
    {price_html(p)}
    <p class="card-ship">{icon('truck')}<span>Ücretsiz kargo</span></p>
    <div class="set-actions"><button class="btn" type="button" data-add="{p['slug']}">Sepete ekle</button><a class="link-arrow" href="{url(p['slug'])}">Ürünü incele {icon('arrow-right')}</a></div>
  </div>
</section>
<section class="section wrap" aria-labelledby="diger"><div class="section-head"><h2 id="diger">Diğer Callula ürünleri</h2></div>
<ul class="rail">{''.join(card(x, '(max-width: 759px) 64vw, 25vw') for x in others)}</ul></section>"""
        sort = ""
    else:
        tile_html = ""
        if tile:
            wide = " tile--wide" if len(items) == 2 else ""
            tile_html = f'<li class="tile{wide}" aria-hidden="true">{img(tile[0], "", "(max-width: 759px) 100vw, 50vw", lazy=False, pos=tile[1])}</li>'
        body = f'<div class="wrap"><ul class="grid-products" data-sortable>{tile_html}{"".join(card(p, lazy=i > 3) for i, p in enumerate(items))}</ul></div><div class="section" style="padding-top:0"></div>'
        sort = """<label class="sort">Sırala<select data-sort><option value="order">Önerilen</option><option value="asc">Fiyat: artan</option><option value="desc">Fiyat: azalan</option></select></label>"""
    main = f"""{crumb_html}
<div class="wrap page-head"><h1>{e(title)}</h1>{f'<p class="lead">{e(lead)}</p>' if lead else ''}</div>
<div class="wrap listing-bar"><nav aria-label="Kategoriler"><ul class="chips">{chips_html}</ul></nav>{sort}</div>
{body}"""
    active = "setler" if slug == "setler" else "urunler"
    write(path, page(path, f"{title} | Callula", desc, main, active=active, jsonld=[crumb_ld, list_ld]))


# ---------------------------------------------------------------- ürün detay
def pdp(p) -> None:
    path = url(p["slug"])
    cat = CATS.get(p["category"]) if p["category"] else None
    trail = [("Anasayfa", "/"), ("Ürünler", "/urunler")]
    if cat:
        trail.append((cat["name"], url(cat["slug"])))
    trail.append((p["name"], None))
    crumb_html, crumb_ld = crumbs(trail)

    imgs = p["images"]
    sizes = "(max-width: 759px) 100vw, (max-width: 1023px) 50vw, 52vw"
    focus = "45% 50%" if p["category"] in (None, "setler") else "50% 30%"
    slides = "".join(
        '<div class="slide" data-slide="%d">%s</div>'
        % (i, img(n, "%s fotoğraf %d" % (p["name"], i + 1), sizes, lazy=i > 0, priority=i == 0, pos=focus))
        for i, n in enumerate(imgs)
    )
    thumbs = ""
    dots = ""
    if len(imgs) > 1:
        on_t, on_d = ' aria-current="true"', ' class="is-on"'
        thumbs = '<ul class="thumbs">' + "".join(
            f'<li><button type="button" data-thumb="{i}"{on_t if i == 0 else ""}>{img(n, "", "76px", max_w=480)}<span class="sr">{i + 1}. fotoğrafı göster</span></button></li>'
            for i, n in enumerate(imgs)
        ) + "</ul>"
        dots = '<div class="dots" aria-hidden="true">' + "".join(f'<span{on_d if i == 0 else ""}></span>' for i in range(len(imgs))) + "</div>"

    # Detay bölümleri (metinler birebir)
    if p["contains"]:
        parts = []
        for s in p["contains"]:
            q = P[s]
            for sec in q["sections"]:
                ticks = "".join(f"<li>{e(b)}</li>" for b in sec["benefits"])
                parts.append(f'<h3><a href="{url(q["slug"])}">{e(q["name"])}</a></h3><ul class="ticks">{ticks}</ul>')
        benefits = "".join(parts)
        inci = "".join(
            f'<h3>{e(P[s]["name"])}</h3><p class="inci">{e(P[s]["ingredients"])}</p>' for s in p["contains"] if P[s]["ingredients"]
        )
        set_list = "".join(
            f'<li><a href="{url(s)}"><span class="thumb">{img(P[s]["card"], "", "52px", max_w=480)}</span><span>{e(P[s]["name"])}</span></a></li>' for s in p["contains"]
        )
    else:
        benefits = "".join(
            f'<ul class="ticks">{"".join(f"<li>{e(b)}</li>" for b in sec["benefits"])}</ul>' for sec in p["sections"]
        )
        inci = f'<p class="inci">{e(p["ingredients"])}</p>'
        set_list = ""

    acc = [("Faydaları", benefits, True)]
    if set_list:
        acc.insert(0, ("Set içeriği", f'<ul class="set-items">{set_list}</ul>', True))
    if p["usage"]:
        note = f'<h3>{e(p["usageNote"])}</h3>' if p.get("usageNote") else ""
        acc.append(("Kullanım şekli", note + '<ul class="ticks">' + "".join(f"<li>{e(u)}</li>" for u in p["usage"]) + "</ul>", False))
    acc.append(("İçerikler", inci, False))
    if p["warnings"]:
        acc.append(("Uyarılar", '<ul class="ticks">' + "".join(f"<li>{e(w)}</li>" for w in p["warnings"]) + "</ul>", False))
    spec = [("Marka", "Callula"), ("Stok kodu", p["stockCode"]), ("Barkod", p["barcode"])]
    if cat:
        spec.append(("Kategori", f'<a href="{url(cat["slug"])}">{cat["name"]}</a>'))
    spec.append(("Kargo", "Ücretsiz"))
    spec_html = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in spec)
    acc.append(("Ürün bilgileri", f"""<p class="approval">Ürünlerimiz <a href="https://www.saglik.gov.tr/" rel="noopener" target="_blank">Sağlık Bakanlığı</a> Onaylı ve <a href="https://utsuygulama.saglik.gov.tr/UTS/" rel="noopener" target="_blank">Ürün takip Sistemine</a> Kayıtlıdır.</p><dl class="spec">{spec_html}</dl>""", False))
    acc.append(("Ödeme seçenekleri", f'<dl class="spec"><dt>Havale ile Ödeme</dt><dd>{tl(p["price"])}</dd><dt>Kredi Kartı Tek Çekim</dt><dd>{tl(p["price"])}</dd></dl><p><a href="/odeme-yontemlerimiz">Güvenli ödeme hakkında</a></p>', False))
    acc_html = "".join(
        f'<details{" open" if o else ""}><summary><h2 style="font:inherit">{t}</h2>{icon("plus")}</summary><div class="body">{b}</div></details>'
        for t, b, o in acc
    )
    detail_img = imgs[1] if len(imgs) > 1 else imgs[0]

    others = [x for x in PRODUCTS if x is not p and x["slug"] not in p["contains"]]
    others = sorted(others, key=lambda x: (x["category"] != p["category"], PRODUCTS.index(x)))[:4]

    main = f"""{crumb_html}
<div class="wrap pdp">
  <div class="gallery" data-gallery>
    {thumbs}
    <div>
      <div class="stage">
        <div class="track" data-track tabindex="0" aria-label="{e(p['name'])} fotoğrafları">{slides}</div>
        <button class="icon-btn zoom-btn" type="button" data-lightbox-open>{icon('arrows-out')}<span class="sr">Fotoğrafı büyüt</span></button>
      </div>
      {dots}
    </div>
  </div>
  <div class="buy">
    {f'<a class="buy-cat" href="{url(cat["slug"])}">{cat["single"]}</a>' if cat else '<span class="buy-cat">Set</span>'}
    <h1>{e(p['name'])}</h1>
    <p class="lead">{e(p['lead'])}</p>
    <div class="buy-price">
      <div>{sale_badge(p)}</div>
      {price_html(p)}
      <p class="meta-line">KDV dahil</p>
    </div>
    <form class="buy-row" data-buy="{p['slug']}">
      <div class="qty" data-qty><button type="button" data-step="-1">{icon('minus')}<span class="sr">Adedi azalt</span></button><input type="number" name="adet" value="1" min="1" max="10" inputmode="numeric" aria-label="Adet"><button type="button" data-step="1">{icon('plus')}<span class="sr">Adedi artır</span></button></div>
      <button class="btn" type="submit" data-main-cta>Sepete ekle</button>
      {fav_button(p, label=True)}
    </form>
    <ul class="perks">
      <li>{icon('truck')}<div><a href="/ucretsiz-kargo">Ücretsiz kargo</a><br><span>Sitemizden alınan her ürün ücretsiz olarak kargolanmaktadır.</span></div></li>
      <li>{icon('seal-check')}<div>Sağlık Bakanlığı onaylı ve <a href="https://utsuygulama.saglik.gov.tr/UTS/" rel="noopener" target="_blank">ÜTS'ye kayıtlı</a></div></li>
      <li>{icon('package')}<div><a href="/iptalveiadebilgilendirmesi">14 gün içinde cayma hakkı</a></div></li>
      <li>{icon('whatsapp-logo')}<div>Sorunuz mu var? <a href="https://wa.me/{WHATSAPP}?text={quote(p['name'] + ' hakkında bilgi almak istiyorum.')}" rel="noopener" target="_blank">WhatsApp'tan yazın</a></div></li>
    </ul>
    <p class="meta-line">Barkod: {p['barcode']}</p>
  </div>
</div>

<section class="section wrap" aria-label="Ürün detayları">
  <div class="details">
    <div class="details-media">{img(detail_img, f"{p['name']} fotoğrafı", '40vw', pos='50% 30%')}</div>
    <div class="acc">{acc_html}</div>
  </div>
</section>

<section class="section section--mist" aria-labelledby="oneriler">
  <div class="wrap"><div class="section-head"><h2 id="oneriler">Diğer Callula ürünleri</h2><a class="link-arrow" href="/urunler">Tüm ürünler {icon('arrow-right')}</a></div>
  <ul class="rail">{''.join(card(x, '(max-width: 759px) 64vw, 25vw') for x in others)}</ul></div>
</section>

<div class="buybar" data-buybar aria-hidden="true">
  {price_html(p)}
  <button class="btn" type="button" data-add="{p['slug']}" tabindex="-1">Sepete ekle</button>
</div>"""

    lightbox = f"""<dialog class="lightbox" data-lightbox aria-label="{e(p['name'])} fotoğrafları">
  <img src="" alt="" data-lightbox-img>
  <button class="icon-btn close" type="button" data-close>{icon('x')}<span class="sr">Kapat</span></button>
  {'' if len(imgs) < 2 else f'<button class="icon-btn nav prev" type="button" data-lb="-1">{icon("arrow-left")}<span class="sr">Önceki</span></button><button class="icon-btn nav next" type="button" data-lb="1">{icon("arrow-right")}<span class="sr">Sonraki</span></button>'}
  <script type="application/json" data-lightbox-list>{json.dumps([img_src(n, 1800) for n in imgs])}</script>
</dialog>"""

    desc_text = p["lead"] if len(p["lead"]) > 60 else f'{p["lead"]} {cat["name"] if cat else "Callula setleri"}.'
    desc_text = f'{p["name"]}: {desc_text} {tl(p["price"])}, ücretsiz kargo.'
    product_ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["name"],
        "image": [SITE + img_src(n, 1200) for n in imgs],
        "description": " ".join(b for sec in (p["sections"] or [s for c in p["contains"] for s in P[c]["sections"]]) for b in sec["benefits"])[:5000],
        "sku": p["stockCode"],
        "brand": {"@type": "Brand", "name": "Callula"},
        "offers": {
            "@type": "Offer",
            "url": SITE + path,
            "priceCurrency": "TRY",
            "price": f'{p["price"]:.2f}',
            "availability": "https://schema.org/InStock" if p["inStock"] else "https://schema.org/OutOfStock",
            "itemCondition": "https://schema.org/NewCondition",
            "seller": {"@type": "Organization", "name": "Callula"},
            "shippingDetails": {
                "@type": "OfferShippingDetails",
                "shippingRate": {"@type": "MonetaryAmount", "value": "0", "currency": "TRY"},
                "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "TR"},
            },
            "hasMerchantReturnPolicy": {
                "@type": "MerchantReturnPolicy",
                "applicableCountry": "TR",
                "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                "merchantReturnDays": 14,
                "merchantReturnLink": SITE + "/iptalveiadebilgilendirmesi",
            },
        },
    }
    if p.get("gtin13"):
        product_ld["gtin13"] = p["gtin13"]
    if p["category"]:
        product_ld["category"] = cat["name"]
    write(path, page(path, f'{p["name"]} | Callula', desc_text, main, active="setler" if p["category"] == "setler" else "urunler",
                     og_image=SITE + img_src(imgs[0], 1200), og_type="product", jsonld=[product_ld, crumb_ld],
                     preload=[preload_for(imgs[0], sizes)], extra=lightbox, body_class="has-buybar"))


# ---------------------------------------------------------------- kurumsal
def content(name: str) -> str:
    return (CONTENT / f"{name}.html").read_text(encoding="utf-8")


def text_page(slug: str, title: str, desc: str, body: str, *, active: str = "", lead: str = "") -> None:
    path = url(slug)
    crumb_html, crumb_ld = crumbs([("Anasayfa", "/"), (title, None)])
    main = f"""{crumb_html}
<div class="wrap page-head"><h1>{e(title)}</h1>{f'<p class="lead">{lead}</p>' if lead else ''}</div>
<div class="wrap"><div class="prose">{body}</div></div>"""
    write(path, page(path, f"{title} | Callula", desc, main, active=active, jsonld=[crumb_ld]))


def legal(slug: str, title: str, desc: str) -> None:
    body = content(slug)
    body = re.sub(r"<(/?)h1>", r"<\1h2>", body)
    body = body.replace("<a>", "<span>").replace("</a>", "</span>") if "<a>" in body else body
    body = body.replace("İnfo@callula.com.tr", "info@callula.com.tr")
    text_page(slug, title, desc, body)


def about() -> None:
    paras = [
        "Kozmetik dünyasına adım atarken amacımız yalnızca ürünleri sunmak değil; doğallığı, özgüveni ve kişisel bakımın keyfini herkese ulaştırmaktı.",
        "Geliştirdiğimiz her ürün, titizlikle seçilmiş içerikler ve modern formüllerle hazırlanıyor. Çünkü güzelliğin yalnızca dış görünüşten ibaret olmadığını, aynı zamanda iyi hissetmekle başladığını biliyoruz.",
        "Kendi yolculuğumuzdan ilham alarak, yenilikçi ve ulaşılabilir bir marka oluşturduk. Bizim için en büyük motivasyon; ürünlerimizi kullanan herkesin kendini daha özgür, daha güçlü ve daha özel hissetmesi.",
        "Bu yolculukta samimiyet, kalite ve sürdürülebilirliği bir araya getiriyor; güzellik anlayışını genç, dinamik ve ilham verici bir bakış açısıyla yeniden tanımlıyoruz.",
        "Özetle; geniş ve amatör ruhunun enerjisini, profesyonel bir hizmet anlayışıyla bütünleştiren Callula Kozmetik siz değerli müşterilerimize geleceğin dünya markasını önermektedir.",
    ]
    crumb_html, crumb_ld = crumbs([("Anasayfa", "/"), ("Hakkımızda", None)])
    main = f"""{crumb_html}
<section class="wrap about-hero" aria-labelledby="hk">
  <div><h1 id="hk">Hakkımızda</h1></div>
  <div class="media">
    {img('title-35b5a05d-4', 'Callula Nemlendirici Serum ve Yüz Kremi masa üzerinde', '(max-width: 759px) 50vw, 25vw', lazy=False, priority=True)}
    {img('title-82d9d25d-2', 'Nemlendirici Serum kullanan kadın', '(max-width: 759px) 50vw, 25vw', lazy=False, pos='50% 30%')}
  </div>
</section>
<section class="wrap about-text" aria-label="Callula hikayesi">
  <p class="first">{paras[1].split('. ')[1]}</p>
  <div class="rest">{''.join(f'<p>{x}</p>' for x in paras)}<p class="sign">Daha fazlasını isteyenler için CALLULA!</p></div>
</section>
<section class="section section--mist" aria-labelledby="hk-urun"><div class="wrap">
  <div class="section-head"><h2 id="hk-urun">Ürünlerimiz</h2><a class="link-arrow" href="/urunler">Tüm ürünler {icon('arrow-right')}</a></div>
  <ul class="rail">{''.join(card(p, '(max-width: 759px) 64vw, 25vw') for p in SINGLES)}</ul></div></section>"""
    write("/hakkimizda", page("/hakkimizda", "Hakkımızda | Callula",
                              "Callula'nın amacı doğallığı, özgüveni ve kişisel bakımın keyfini herkese ulaştırmak. Titizlikle seçilmiş içerikler ve modern formüller.",
                              main, active="hakkimizda", jsonld=[crumb_ld, ORG_LD]))


def contact() -> None:
    crumb_html, crumb_ld = crumbs([("Anasayfa", "/"), ("Adres ve İletişim", None)])
    main = f"""{crumb_html}
<div class="wrap page-head"><h1>Adres ve İletişim</h1></div>
<div class="wrap contact">
  <dl class="contact-list">
    <div><dt>WHATSAPP</dt><dd><a href="https://wa.me/{WHATSAPP}" rel="noopener" target="_blank">0530 202 34 53</a></dd></div>
    <div><dt>E-POSTA</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd></div>
    <div><dt>ADRES</dt><dd>Callula Kozmetik İthalat İhracat Ltd.Şti.<br>Çenedağ Mah., Alçicek Sok. No:25/1<br>Derince, Kocaeli</dd></div>
    <div><dt>VERGİ BİLGİLERİ</dt><dd>Derince Vergi Dairesi<br>1950909929</dd></div>
    <div><dt>KEP ADRESİ</dt><dd>callulakozmetik@hs02.kep.tr</dd></div>
    <div><dt>INSTAGRAM</dt><dd><a href="{INSTAGRAM}" rel="noopener" target="_blank">@callulatr</a></dd></div>
  </dl>
  <div class="contact-media">{img('title-80b9f272-8', 'Callula ürünleri dizüstü bilgisayar ve gözlükle', '(max-width: 759px) 100vw, 55vw', lazy=False)}</div>
</div>"""
    write("/adres-ve-iletisim", page("/adres-ve-iletisim", "Adres ve İletişim | Callula",
                                     "Callula Kozmetik iletişim bilgileri: WhatsApp 0530 202 34 53, info@callula.com.tr, Çenedağ Mah. Alçicek Sok. No:25/1 Derince, Kocaeli.",
                                     main, active="iletisim", jsonld=[crumb_ld, ORG_LD]))
    # Eski bozuk linkler için yönlendirme
    for old in ("Iletisim", "iletisim"):
        (PUB / old).mkdir(exist_ok=True)
        (PUB / old / "index.html").write_text(
            f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Adres ve İletişim | Callula</title>'
            f'<meta name="robots" content="noindex"><link rel="canonical" href="{SITE}/adres-ve-iletisim">'
            f'<meta http-equiv="refresh" content="0; url=/adres-ve-iletisim"></head><body><a href="/adres-ve-iletisim">Adres ve İletişim</a></body></html>',
            encoding="utf-8")


def utility_pages() -> None:
    all_cards = "".join(card(p, hidden=True) for p in PRODUCTS)
    write("/sepet", page("/sepet", "Sepetim | Callula", "Callula alışveriş sepetiniz.", f"""
<div class="wrap page-head"><h1>Sepetim</h1></div>
<div class="wrap pdp" style="padding-bottom:96px" data-cart-page>
  <div><div data-cart-lines></div></div>
  <aside class="buy" aria-label="Sipariş özeti"><h2 class="sr">Sipariş özeti</h2><p class="drawer-note">{icon('truck')}Tüm ürünlerde ücretsiz kargo</p><div class="drawer-foot" style="padding:0;border:0" data-cart-foot></div></aside>
</div>
<noscript><p class="wrap">Sepeti görüntülemek için tarayıcınızda JavaScript açık olmalıdır.</p></noscript>""", noindex=True))
    write("/favoriler", page("/favoriler", "Favorilerim | Callula", "Favorilere eklediğiniz Callula ürünleri.", f"""
<div class="wrap page-head"><h1>Favorilerim</h1></div>
<div class="wrap" style="padding-bottom:96px"><ul class="grid-products" data-fav-page>{all_cards}</ul>
<div class="empty" data-fav-empty hidden><p>Henüz favorilere eklediğiniz bir ürün yok. Ürünlerdeki kalp simgesiyle favorilerinizi burada toplayabilirsiniz.</p><a class="btn" href="/urunler">Ürünleri keşfet</a></div></div>""", noindex=True))
    write("/arama", page("/arama", "Arama | Callula", "Callula ürünlerinde arama.", f"""
<div class="wrap page-head"><h1>Arama</h1></div>
<div class="wrap" style="padding-bottom:96px">
  <form class="search-form" action="/arama" method="get" role="search" style="max-width:720px;margin-bottom:32px">{icon('magnifying-glass')}<label class="sr" for="q-page">Ürün ara</label><input id="q-page" name="q" type="search" placeholder="Ürün ya da içerik ara" data-search-page></form>
  <p class="search-empty" data-search-summary role="status"></p>
  <ul class="grid-products" data-search-grid>{all_cards}</ul>
</div>""", noindex=True))
    notfound = page("/404", "Sayfa bulunamadı | Callula", "Aradığınız sayfa bulunamadı.", """
<div class="wrap notice"><h1>Bu sayfa bulunamadı.</h1><p class="lead">Adres değişmiş ya da yanlış yazılmış olabilir. Ürünlerimize buradan ulaşabilirsiniz.</p><a class="btn" href="/urunler">Ürünleri keşfet</a></div>""", noindex=True)
    (PUB / "404.html").write_text(notfound, encoding="utf-8")


def seo_files() -> None:
    paths = ["/", "/urunler"] + [url(c["slug"]) for c in DATA["categories"]] + [url(p["slug"]) for p in PRODUCTS] + [
        "/hakkimizda", "/adres-ve-iletisim", "/ucretsiz-kargo", "/odeme-yontemlerimiz",
        "/iptalveiadebilgilendirmesi", "/cerez-politikasi", "/gizlilik-ve-guvenlik-politikasi"]
    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{SITE}{p if p != '/' else '/'}</loc><lastmod>{today}</lastmod></url>" for p in paths)
    (PUB / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (PUB / "robots.txt").write_text(
        f"User-agent: *\nDisallow: /sepet\nDisallow: /favoriler\nDisallow: /arama\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")


def icons_sprite() -> None:
    syms = []
    for f in sorted((ROOT / "src" / "icons").glob("*.svg")):
        s = f.read_text(encoding="utf-8")
        vb = re.search(r'viewBox="([^"]+)"', s).group(1)
        inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", s, flags=re.S)
        inner = re.sub(r'<rect width="256" height="256" fill="none"\s*/>', "", inner)
        syms.append(f'<symbol id="{f.stem}" viewBox="{vb}">{inner}</symbol>')
    (PUB / "assets" / "icons.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">' + "".join(syms) + "</svg>", encoding="utf-8")


def main() -> None:
    icons_sprite()
    home()
    listing("urunler", "Ürünler", PRODUCTS, tile=("title-553cd388-0", "50% 25%"),
            desc="Callula ürünlerinin tamamı: Yüz Kremi, Cicaplast Krem, Nemlendirici Serum, Yüz Temizleme Köpüğü ve setler. Tüm ürünlerde ücretsiz kargo.")
    for c in DATA["categories"]:
        items = [p for p in PRODUCTS if p["category"] == c["slug"]]
        names = ", ".join(p["name"] for p in items)
        tile = (c["image"], c["focus"]) if len(items) > 1 else None
        listing(c["slug"], c["name"], items, tile=tile,
                desc=f"Callula {c['name'].lower()}: {names}. %50 indirim ve ücretsiz kargo.")
    for p in PRODUCTS:
        pdp(p)
    about()
    contact()
    text_page("ucretsiz-kargo", "Ücretsiz Kargo", "Callula'dan alınan her ürün ücretsiz olarak kargolanır.",
              f'<p>Sitemizden alınan her ürün ücretsiz olarak kargolanmaktadır.</p><p><a class="link-arrow" href="/urunler">Ürünleri keşfet {icon("arrow-right")}</a></p>')
    text_page("odeme-yontemlerimiz", "Güvenli Ödeme", "Callula ödeme seçenekleri: havale ile ödeme ve kredi kartı ile tek çekim.",
              """<p>Callula'da siparişlerinizi aşağıdaki yöntemlerle ödeyebilirsiniz.</p>
<h2>Kredi Kartı Tek Çekim</h2><p><img src="/assets/img/odeme-kartlari.png" width="118" height="30" alt="Mastercard ve Visa" loading="lazy"></p>
<h2>Havale ile Ödeme</h2>
<p>Siparişinizle ilgili sorularınız için <a href="/adres-ve-iletisim">bize ulaşabilirsiniz</a>.</p>""")
    legal("iptalveiadebilgilendirmesi", "İptal İade Koşulları", "Callula tüketici hakları, cayma, iptal ve iade koşulları.")
    legal("cerez-politikasi", "Çerez Politikası", "Callula çerez (cookie) kullanımına ilişkin aydınlatma metni.")
    legal("gizlilik-ve-guvenlik-politikasi", "Gizlilik Sözleşmesi", "Callula gizlilik ve güvenlik politikası.")
    utility_pages()
    seo_files()
    print("ok:", len(list(PUB.rglob("index.html"))), "sayfa")


if __name__ == "__main__":
    main()
