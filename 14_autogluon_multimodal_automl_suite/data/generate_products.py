"""Synthesize a small multimodal product catalog (image + text + tabular + label).

Each modality is *partially* informative on purpose so fusion has room to beat
single-modality baselines — and so a null lift on tiny data is still honest.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / "images"
OUT = ROOT / "processed" / "products.csv"
META = ROOT / "processed" / "dataset_meta.json"

CATEGORIES = ["electronics", "apparel", "home", "beauty", "sports"]

# Dominant RGB + geometric motif per category (image signal)
PALETTE = {
    "electronics": ((40, 90, 200), "rect"),
    "apparel": ((200, 70, 120), "triangle"),
    "home": ((90, 160, 80), "circle"),
    "beauty": ((180, 110, 200), "oval"),
    "sports": ((230, 140, 40), "stripe"),
}

# Overlapping price bands (tabular signal is noisy)
PRICE_BANDS = {
    "electronics": (40, 420),
    "apparel": (12, 180),
    "home": (15, 260),
    "beauty": (8, 95),
    "sports": (18, 220),
}

BRAND_TIERS = ["budget", "mid", "premium"]

TITLE_BITS = {
    "electronics": ["Wireless earbuds", "USB-C hub", "Bluetooth speaker", "LED monitor stand", "Power bank"],
    "apparel": ["Cotton tee", "Denim jacket", "Running shorts", "Wool scarf", "Linen shirt"],
    "home": ["Ceramic mug", "Desk lamp", "Throw pillow", "Storage bin", "Cutting board"],
    "beauty": ["Face serum", "Matte lipstick", "Hair oil", "Sunscreen SPF50", "Clay mask"],
    "sports": ["Yoga mat", "Resistance band", "Water bottle", "Foam roller", "Jump rope"],
}

BLURB_BITS = {
    "electronics": [
        "compact gadget with rechargeable battery and aluminum housing",
        "plug-and-play accessory for laptops and phones",
        "noise-isolating audio with fast charging",
    ],
    "apparel": [
        "soft everyday wear with a relaxed fit",
        "machine-washable fabric for casual outfits",
        "seasonal wardrobe staple in multiple sizes",
    ],
    "home": [
        "kitchen and living-room essential for daily use",
        "durable household piece with a clean look",
        "space-saving organizer for apartments",
    ],
    "beauty": [
        "skincare formula for daily routines",
        "cosmetic finish that lasts through the day",
        "gentle ingredients for sensitive skin",
    ],
    "sports": [
        "training gear for home workouts",
        "lightweight fitness accessory for the gym",
        "durable equipment for outdoor sessions",
    ],
}

# Cross-category distractors so text alone is imperfect
DISTRACTORS = [
    "gift-ready packaging",
    "limited seasonal drop",
    "ships in two days",
    "customer favorite this month",
    "pairs well with other items",
]


def _mix(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a * (1 - t) + b * t) for a, b in zip(c1, c2))


def render_image(path: Path, category: str, rng: random.Random, confuse: bool = False) -> None:
    """Draw a simple category motif; optionally paint a wrong-category color."""
    w = h = 128
    base_color, motif = PALETTE[category]
    if confuse:
        other = rng.choice([c for c in CATEGORIES if c != category])
        base_color = PALETTE[other][0]
        # Keep true motif so image still carries a weak true signal
    bg = _mix(base_color, (245, 245, 245), 0.55)
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)
    accent = _mix(base_color, (20, 20, 20), 0.25)
    margin = 18
    if motif == "rect":
        draw.rectangle([margin, margin, w - margin, h - margin], outline=accent, width=6)
        draw.rectangle([40, 50, 88, 78], fill=accent)
    elif motif == "triangle":
        draw.polygon([(64, 20), (108, 108), (20, 108)], fill=accent)
    elif motif == "circle":
        draw.ellipse([28, 28, 100, 100], fill=accent)
    elif motif == "oval":
        draw.ellipse([36, 22, 92, 106], fill=accent)
        draw.ellipse([48, 40, 80, 88], fill=bg)
    else:  # stripe
        for y in range(16, 112, 14):
            draw.rectangle([16, y, 112, y + 7], fill=accent)

    # Speckle / blur so pixels are not trivially separable
    pixels = img.load()
    for _ in range(180):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        noise = tuple(max(0, min(255, pixels[x, y][i] + rng.randint(-35, 35))) for i in range(3))
        pixels[x, y] = noise
    if rng.random() < 0.35:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="JPEG", quality=88)


def make_row(i: int, category: str, rng: random.Random, images_dir: Path) -> dict:
    confuse_img = rng.random() < 0.22
    confuse_text = rng.random() < 0.18
    img_name = f"{category}_{i:04d}.jpg"
    img_path = images_dir / img_name
    render_image(img_path, category, rng, confuse=confuse_img)

    title = rng.choice(TITLE_BITS[category])
    blurb = rng.choice(BLURB_BITS[category])
    if confuse_text:
        fake = rng.choice([c for c in CATEGORIES if c != category])
        blurb = f"{blurb}; also similar to {rng.choice(TITLE_BITS[fake]).lower()}"
    description = f"{title}. {blurb}. {rng.choice(DISTRACTORS)}."

    lo, hi = PRICE_BANDS[category]
    price = round(rng.uniform(lo, hi), 2)
    # Inject overlap: occasionally sample from a neighbor band
    if rng.random() < 0.2:
        other = rng.choice(CATEGORIES)
        lo2, hi2 = PRICE_BANDS[other]
        price = round(rng.uniform(lo2, hi2), 2)

    brand_tier = rng.choices(BRAND_TIERS, weights=[0.45, 0.35, 0.2], k=1)[0]
    rating = round(min(5.0, max(1.0, rng.gauss(3.9, 0.55))), 1)
    weight_oz = round(rng.uniform(1.5, 64.0), 1)
    # Weak tabular cue: electronics/home a bit more fragile
    fragile_p = 0.55 if category in ("electronics", "home", "beauty") else 0.2
    is_fragile = int(rng.random() < fragile_p)

    return {
        "image": str(img_path.resolve()),
        "description": description,
        "price": price,
        "rating": rating,
        "brand_tier": brand_tier,
        "weight_oz": weight_oz,
        "is_fragile": is_fragile,
        "category": category,
    }


def generate(n: int = 400, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    images_dir = IMAGES
    if images_dir.exists():
        for p in images_dir.glob("*.jpg"):
            p.unlink()
    images_dir.mkdir(parents=True, exist_ok=True)

    per = n // len(CATEGORIES)
    rows: list[dict] = []
    idx = 0
    for cat in CATEGORIES:
        for _ in range(per):
            rows.append(make_row(idx, cat, rng, images_dir))
            idx += 1
    # Fill remainder
    while len(rows) < n:
        cat = CATEGORIES[len(rows) % len(CATEGORIES)]
        rows.append(make_row(idx, cat, rng, images_dir))
        idx += 1

    rng.shuffle(rows)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=400, help="Number of product rows")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = generate(args.n, args.seed)
    df.to_csv(OUT, index=False)
    meta = {
        "n": len(df),
        "categories": CATEGORIES,
        "columns": list(df.columns),
        "label": "category",
        "modalities": {
            "image": "image",
            "text": "description",
            "tabular": ["price", "rating", "brand_tier", "weight_oz", "is_fragile"],
        },
        "class_counts": df["category"].value_counts().to_dict(),
    }
    META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {len(df):,} rows -> {OUT}")
    print(f"Images -> {IMAGES}")
    print(df["category"].value_counts().to_string())


if __name__ == "__main__":
    main()
