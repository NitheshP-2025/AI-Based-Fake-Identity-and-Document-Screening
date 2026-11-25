import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.validation.mrz_checksum import build_td3_line1, build_td3_line2   # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "samples"
WIDTH, HEIGHT = 1500, 1060

MONO_FONTS = [
    "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/lucon.ttf", "C:/Windows/Fonts/cour.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]
TEXT_FONTS = ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def find_font(candidates, size):
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def mrz_font(target_width):
    """Pick the largest monospaced font size where 44 characters fit the target width."""
    size = 20
    while find_font(MONO_FONTS, size + 1).getlength("<" * 44) <= target_width and size < 90:
        size += 1
    return find_font(MONO_FONTS, size)


def build_image(line1, line2, label_fields):
    """Draw a simple passport data page with the two MRZ lines at the bottom."""
    img = Image.new("RGB", (WIDTH, HEIGHT), (232, 238, 245))
    draw = ImageDraw.Draw(img)
    title, label, value = (find_font(TEXT_FONTS, s) for s in (46, 24, 34))

    draw.text((60, 30), "PASSPORT  -  REPUBLIC OF UTOPIA", font=title, fill=(20, 40, 90))
    draw.text((60, 85), "SAMPLE IMAGE - NOT A REAL DOCUMENT", font=label, fill=(150, 40, 40))
    draw.rectangle((60, 130, 400, 560), outline=(80, 80, 80), width=3, fill=(205, 212, 222))
    draw.text((150, 330), "PHOTO", font=title, fill=(110, 110, 110))

    y = 140
    for name, text in label_fields:
        draw.text((450, y), name, font=label, fill=(90, 90, 90))
        draw.text((450, y + 28), text, font=value, fill=(10, 10, 10))
        y += 85

    band_top = HEIGHT - 300
    draw.rectangle((0, band_top, WIDTH, HEIGHT), fill=(250, 250, 250))
    font = mrz_font(WIDTH - 120)
    draw.text((60, band_top + 60), line1, font=font, fill=(0, 0, 0))
    draw.text((60, band_top + 60 + int(font.size * 1.6)), line2, font=font, fill=(0, 0, 0))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def make_noisy(image, angle=1.5, noise=9, seed=1):
    """Rotate slightly, blur a little, and add noise to imitate a phone photo."""
    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    out = cv2.warpAffine(image, matrix, (w, h), borderValue=(232, 238, 245))
    out = cv2.GaussianBlur(out, (3, 3), 0)
    rng = np.random.default_rng(seed)
    noisy = out.astype(np.int16) + rng.normal(0, noise, out.shape).astype(np.int16)
    return np.clip(noisy, 0, 255).astype(np.uint8)


def save(name, image):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError(f"Could not encode {name}")
    encoded.tofile(str(path))
    print("saved", path)


if __name__ == "__main__":
    line1 = build_td3_line1("P", "UTO", "SHARMA", "PRIYA")
    good = build_td3_line2("K1234567", "UTO", "900515", "F", "310915")
    fields = [("Surname", "SHARMA"), ("Given names", "PRIYA"), ("Nationality", "UTOPIAN"),
              ("Date of birth", "15 MAY 1990"), ("Passport no.", "K1234567"), ("Date of expiry", "15 SEP 2031")]

    valid_image = build_image(line1, good, fields)
    save("sample_valid.png", valid_image)

    edited = good[:13] + "900516" + good[19:]          # day of birth changed, check digit not updated
    edited_fields = [f if f[0] != "Date of birth" else ("Date of birth", "16 MAY 1990") for f in fields]
    save("sample_edited_dob.png", build_image(line1, edited, edited_fields))

    expired = build_td3_line2("K1234567", "UTO", "900515", "F", "200915")
    expired_fields = [f if f[0] != "Date of expiry" else ("Date of expiry", "15 SEP 2020") for f in fields]
    save("sample_expired.png", build_image(line1, expired, expired_fields))

    save("sample_noisy_valid.png", make_noisy(valid_image))
