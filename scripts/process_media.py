"""Turn the owner's raw files into web-ready media in site/assets.

Usage:
  FFMPEG=/path/to/ffmpeg python3 -I scripts/process_media.py

Reads:  "Carril Diamante content/" (owner originals, never modified)
Writes: site/assets/img/*, site/assets/video/*, site/favicon*.png, site/og-image.jpg

Re-run after changing a pick below. Photos are re-encoded with Pillow, which drops
EXIF (camera data, GPS) because no exif= argument is passed when saving.
"""
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Carril Diamante content"
IMG = ROOT / "site" / "assets" / "img"
VID = ROOT / "site" / "assets" / "video"
SITE = ROOT / "site"
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")

WA = "WhatsApp Image 2023-01-17 at 8.12.{}.jpeg"

# output name -> source file. Index numbers refer to the contact sheet (sorted WhatsApp files).
PHOTOS = {
    "match-race": WA.format("09 PM (2)"),       # 23 two horses head to head
    "open-race": WA.format("05 PM (1)"),        # 1  three horses charging
    "starting-gate": WA.format("11 PM (1)"),    # 32 six-lane gate, numbered 1-6
    "g-dust-walk": WA.format("11 PM (4)"),      # 36
    "g-blue-silks": WA.format("09 PM (3)"),     # 26
    "g-rockies": WA.format("08 PM (3)"),        # 20
    "g-pony-up": WA.format("09 PM (1)"),        # 24
    "g-two-turn": WA.format("09 PM"),           # 22
    "g-grey-chase": WA.format("07 PM (3)"),     # 15
    "g-field": WA.format("07 PM (1)"),          # 11
    "g-finish-crowd": WA.format("06 PM (3)"),   # 10
    "g-break": WA.format("12 PM (1)"),          # 37
    "g-late-sun": WA.format("12 PM"),           # 38
}


def sorted_wa():
    return sorted(p.name for p in SRC.glob("WhatsApp*.jpeg"))


def save_webp(im, path, width, quality=78):
    im = im.copy()
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, "WEBP", quality=quality, method=6)


def photos():
    names = sorted_wa()
    for out, name in PHOTOS.items():
        src = SRC / name
        if not src.exists():
            sys.exit(f"missing photo: {name} (have {len(names)} WhatsApp files)")
        im = Image.open(src).convert("RGB")
        save_webp(im, IMG / f"{out}-1600.webp", 1600)
        save_webp(im, IMG / f"{out}-800.webp", 800)
    print(f"photos: {len(PHOTOS)} x 2 sizes")


def logo():
    im = Image.open(SRC / "1621_Carril Diamante_FLAT_DT_P_01.png").convert("RGBA")
    im = im.crop(im.getbbox())
    for w in (480, 960):
        h = round(im.height * w / im.width)
        im.resize((w, h), Image.LANCZOS).save(IMG / f"logo-carril-{w}.png", optimize=True)
    print("logo:", im.size, "->", (960, round(im.height * 960 / im.width)))
    return im


def icons(wordmark):
    # The lockup is CARRIL (with the diamond replacing "RR") over a white DIAMANTE line.
    # The diamond spans ~37-77% of the width and the top ~22% of the width in height.
    w, h = wordmark.size
    diamond = wordmark.crop((round(w * 0.392), 0, round(w * 0.752), round(w * 0.225)))
    diamond = diamond.crop(diamond.getbbox())
    for size, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png"), (512, "icon-512.png")):
        canvas = Image.new("RGBA", (size, size), (17, 16, 14, 255))
        d = diamond.copy()
        d.thumbnail((round(size * 0.84), round(size * 0.84)), Image.LANCZOS)
        canvas.alpha_composite(d, ((size - d.width) // 2, (size - d.height) // 2))
        canvas.convert("RGB").save(SITE / name, optimize=True)
    print("icons: 32, 180, 512")


def og_image(wordmark):
    base = Image.open(SRC / PHOTOS["starting-gate"]).convert("RGB")
    base = base.resize((1200, round(base.height * 1200 / base.width)), Image.LANCZOS)
    top = (base.height - 630) // 2
    base = base.crop((0, top, 1200, top + 630)).convert("RGBA")
    shade = Image.new("RGBA", base.size, (12, 11, 9, 150))
    base.alpha_composite(shade)
    mark = wordmark.copy()
    mark.thumbnail((760, 400), Image.LANCZOS)
    base.alpha_composite(mark, ((1200 - mark.width) // 2, (630 - mark.height) // 2))
    base.convert("RGB").save(SITE / "og-image.jpg", quality=85, optimize=True)
    print("og-image: 1200x630")


def video():
    src = SRC / "CarrilDiamante3.mp4"
    # Source is 1280x720 with the logo burned into the lower-right corner from y~540.
    # Keep the top 512 rows: a 2.5:1 cinema band with no logo.
    common = ["-v", "error", "-y", "-i", str(src), "-an", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    subprocess.run([FFMPEG, *common, "-vf", "crop=1280:512:0:0", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "27", "-profile:v", "high", str(VID / "hero-band.mp4")], check=True)
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", "4", "-i", str(src), "-frames:v", "1",
                    "-vf", "crop=1280:512:0:0", str(IMG / "hero-poster.jpg")], check=True)
    Image.open(IMG / "hero-poster.jpg").save(IMG / "hero-poster.webp", "WEBP", quality=72, method=6)
    (IMG / "hero-poster.jpg").unlink()
    print("video: hero-band.mp4", round((VID / "hero-band.mp4").stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    for d in (IMG, VID):
        d.mkdir(parents=True, exist_ok=True)
    photos()
    mark = logo()
    icons(mark)
    og_image(mark)
    video()
