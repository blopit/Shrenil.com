#!/usr/bin/env python3
"""Render the 1200x630 link-preview (Open Graph) images into public/images/.

    python3 scripts/make_og.py        # needs Pillow; uses the macOS system font

One card per indexed page. Re-run after changing a headline or proof point below.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "images"
FONT = "/System/Library/Fonts/SFNS.ttf"
W, H = 1200, 630

CARDS = {
    "og-home.png": dict(
        kicker="shrenp.com",
        title="Shren Patel",
        sub="AI agent engineer & consultant",
        lines=["Multi-agent systems · RAG · evals · human approval gates",
               "CentrOS in production · 10+ years at Coursera, Faire, D2L"],
        foot="Open to Staff AI roles and consulting work · Canada, remote",
        photo=True),
    "og-centros.png": dict(
        kicker="shrenp.com/centros",
        title="CentrOS",
        sub="AI agent orchestration platform",
        lines=["Typed contracts · eval gates · policy lanes · owner inbox",
               "In production at a 23-unit hospitality operation"],
        foot="Built by Shren Patel · 3,980+ tests on main",
        photo=False),
    "og-axed.png": dict(
        kicker="shrenp.com/axed",
        title="AXED",
        sub="WEBTOON Original by Shren Patel",
        lines=["40M+ reads · 492K+ subscribers",
               "IP rights deal with Wattpad WEBTOON Studios"],
        foot="Book + 2-season animated TV adaptation",
        photo=False),
}


def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def background():
    # Night-sky gradient in the site's colours: deep navy with blue / violet glows.
    img = Image.new("RGB", (W, H), "#07091F")
    glow = Image.new("RGB", (W, H), "#07091F")
    px = glow.load()
    for y in range(H):
        for x in range(W):
            a = max(0.0, 1 - (((x - 1050) / 700) ** 2 + ((y + 40) / 520) ** 2) ** 0.5)
            b = max(0.0, 1 - (((x - 120) / 620) ** 2 + ((y - 700) / 460) ** 2) ** 0.5)
            px[x, y] = (int(7 + 111 * a * .55 + 0 * b), int(9 + 80 * a * .55 + 100 * b * .5),
                        int(31 + 204 * a * .55 + 224 * b * .5))
    return Image.blend(img, glow, 1.0)


def render(name, c):
    img = background()
    d = ImageDraw.Draw(img)
    x = 80
    d.text((x, 70), c["kicker"], font=font(28, 600), fill="#8FB8FF")
    d.text((x, 150), c["title"], font=font(104, 800), fill="#FFFFFF")
    d.text((x, 280), c["sub"], font=font(48, 600), fill="#E6E9FF")
    y = 378
    for line in c["lines"]:
        d.text((x, y), line, font=font(30, 400), fill="#B9C0E6")
        y += 46
    d.rounded_rectangle((x, 520, x + 64, 526), 3, fill="#3CD3FE")
    d.text((x, 546), c["foot"], font=font(28, 600), fill="#FFFFFF")
    if c["photo"]:
        size = 196
        ph = Image.open(OUT / "shrenp.jpg").convert("RGB")
        s = min(ph.size)
        ph = ph.crop((0, 0, s, s)).resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size * 4, size * 4), fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)
        px, py = W - size - 84, 56
        d.ellipse((px - 6, py - 6, px + size + 6, py + size + 6), fill="#3CD3FE")
        img.paste(ph, (px, py), mask)
    img.save(OUT / name, optimize=True)
    print("wrote", (OUT / name).relative_to(ROOT))


if __name__ == "__main__":
    for name, card in CARDS.items():
        render(name, card)
