"""Callula görsel hattı.

src/originals içindeki mevcut Callula fotoğraflarından responsive WebP varyantları,
şeffaf logo, logodaki fırça darbesinden CSS maskesi ve favicon üretir.
Görsellerin kendisi değiştirilmez: yalnızca yeniden boyutlandırılır ve sıkıştırılır.

Kullanım:  python src/images.py
"""
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "originals"
OUT = ROOT / "public" / "assets" / "img"
WIDTHS = (480, 800, 1200, 1800)
QUALITY = 80


def slug(name: str) -> str:
    stem = Path(name).stem.lower()
    return "-".join(p for p in stem.replace("_", "-").split("-") if p)


def variants(path: Path) -> list[int]:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    made = []
    for w in WIDTHS:
        if w > im.width and made:
            break
        target = min(w, im.width)
        h = round(im.height * target / im.width)
        out = OUT / f"{slug(path.name)}-{w}.webp"
        if not out.exists():
            im.resize((target, h), Image.LANCZOS).save(out, "WEBP", quality=QUALITY, method=6)
        made.append(w)
    return made


def logo_assets() -> None:
    src = Image.open(SRC / "callula-1-jpg.jpg").convert("RGB")
    rgba = Image.new("RGBA", src.size)
    mask = Image.new("RGBA", src.size)
    px, lp, mp = src.load(), rgba.load(), mask.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b = px[x, y]
            # Beyaz zemin -> şeffaf. Kenarlarda yumuşak geçiş için mesafeye göre alfa.
            dist = 765 - (r + g + b)
            a = max(0, min(255, int(dist * 2.2)))
            lp[x, y] = (r, g, b, a)
            mp[x, y] = (255, 255, 255, a)
    box = rgba.getbbox()
    logo = rgba.crop(box)
    for w in (260, 520):
        h = round(logo.height * w / logo.width)
        im = logo.resize((w, h), Image.LANCZOS)
        im.save(OUT / f"callula-logo-{w}.png", optimize=True)
        im.save(OUT / f"callula-logo-{w}.webp", "WEBP", quality=90, method=6)
    brush = mask.crop(box)
    brush.resize((900, round(brush.height * 900 / brush.width)), Image.LANCZOS).save(
        OUT / "brush.png", optimize=True
    )
    # Favicon: logodaki fırça ve "C" harfi.
    lw = logo.width
    sq = logo.crop((int(lw * 0.13), 0, int(lw * 0.13) + logo.height, logo.height))
    bg = Image.new("RGBA", sq.size, (255, 255, 255, 0))
    bg.alpha_composite(sq)
    for s in (32, 180, 512):
        bg.resize((s, s), Image.LANCZOS).save(OUT / f"favicon-{s}.png", optimize=True)


def og_image() -> None:
    """1200x630 paylaşım görseli: mevcut ürün fotoğrafının kırpılmış hali."""
    im = ImageOps.exif_transpose(Image.open(SRC / "dortlu-set-8aa-9a.jpg")).convert("RGB")
    ratio = 1200 / 630
    w = im.width
    h = round(w / ratio)
    top = (im.height - h) // 2
    im.crop((0, top, w, top + h)).resize((1200, 630), Image.LANCZOS).save(
        OUT / "og-callula.jpg", quality=82, optimize=True, progressive=True
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for p in sorted(SRC.iterdir()):
        if p.suffix.lower() in (".jpg", ".jpeg") and p.name != "callula-1-jpg.jpg":
            report[slug(p.name)] = variants(p)
    logo_assets()
    og_image()
    Image.open(SRC / "Kart.png").save(OUT / "odeme-kartlari.png", optimize=True)
    for k, v in report.items():
        print(k, v)


if __name__ == "__main__":
    main()
