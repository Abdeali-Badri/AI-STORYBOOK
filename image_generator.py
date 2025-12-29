import os
import sys
import json
import base64
import requests
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent

JSON_FILE = BASE_DIR / "static" / "stories" / "story_9c423e01" / "story.json"
OUT_DIR = BASE_DIR / "stability_outputs"
OUT_DIR.mkdir(exist_ok=True)

FONT_PATH = BASE_DIR / "static" / "fonts" / "Baloo2-Bold.ttf"

API_KEY = os.getenv("sk-vxgrlZwwQoMAiMhyZUgQERsK8VEUflL25yfg9JCqbpZ1GHwA") or "sk-vxgrlZwwQoMAiMhyZUgQERsK8VEUflL25yfg9JCqbpZ1GHwA"  # <-- put key here or export STABILITY_API_KEY
API_HOST = "https://api.stability.ai"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

WIDTH = 1024
HEIGHT = 1024
STEPS = 30
SAMPLES = 1

if not API_KEY:
    print(" API KEY missing")
    sys.exit(1)

if not FONT_PATH.exists():
    print(" Font not found:", FONT_PATH)
    sys.exit(1)

if not JSON_FILE.exists():
    print(" Story JSON not found:", JSON_FILE)
    sys.exit(1)

def list_engines():
    r = requests.get(f"{API_HOST}/v1/engines/list", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def choose_engine(engines):
    for e in engines:
        if "sdxl" in e.get("id", "").lower():
            return e
    return engines[0]


def generate_image(engine_id, prompt, page_key):
    url = f"{API_HOST}/v1/generation/{engine_id}/text-to-image"

    payload = {
        "text_prompts": [{"text": prompt}],
        "cfg_scale": 7,
        "width": WIDTH,
        "height": HEIGHT,
        "steps": STEPS,
        "samples": SAMPLES
    }

    print(f"🎨 Generating image for {page_key}")
    r = requests.post(url, headers=HEADERS, json=payload, timeout=120)
    if r.status_code != 200:
        print("❌ Generation failed:", r.text)
        sys.exit(1)

    image_b64 = r.json()["artifacts"][0]["base64"]
    out_path = OUT_DIR / f"{page_key}.png"

    with open(out_path, "wb") as f:
        f.write(base64.b64decode(image_b64))

    return out_path


def build_prompt(page):
    style = (
        "children's storybook illustration, soft watercolor, bright colors, "
        "cute, joyful, whimsical, kid-friendly"
    )

    character = page.get("character", {}).get("description", "")

    if page["type"] == "title":
        return f"{style}. {page.get('story_overview', '')}. Main character: {character}"
    else:
        return f"{style}. {page.get('scene', '')}. Main character: {character}"


def add_text(img_path, page):
    img = Image.open(img_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    font_title = ImageFont.truetype(str(FONT_PATH), 64)
    font_story = ImageFont.truetype(str(FONT_PATH), 40)
    font_moral = ImageFont.truetype(str(FONT_PATH), 36)

    
    if page["type"] == "title":
        text = page.get("title", "")
        font = font_title
        y = 40
        wrap = 22

    
    else:
        text = page.get("text", "")
        font = font_story
        y = 30
        wrap = 38

    lines = textwrap.wrap(text, wrap)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (img.width - w) // 2
        draw.text((x, y), line, fill=(20, 20, 20), font=font)
        y += (bbox[3] - bbox[1]) + 14

    # -------- MORAL --------
    if page.get("moral"):
        moral_text = "Moral: " + page["moral"]
        y = img.height - 160
        for line in textwrap.wrap(moral_text, 45):
            bbox = draw.textbbox((0, 0), line, font=font_moral)
            w = bbox[2] - bbox[0]
            x = (img.width - w) // 2
            draw.text((x, y), line, fill=(40, 40, 40), font=font_moral)
            y += (bbox[3] - bbox[1]) + 10

    img.save(img_path)
    print(f"🖋 Text added: {img_path}")
    
from PIL import Image

def pngs_to_pdf(image_dir: Path, output_pdf: Path):
    """
    Convert all PNG images in image_dir into a single PDF.
    Images are sorted by filename (page_1.png, page_2.png, ...)
    """

    png_files = sorted(image_dir.glob("*.png"))

    if not png_files:
        print(" No PNG files found for PDF conversion")
        return

    images = []
    for png in png_files:
        img = Image.open(png).convert("RGB")
        images.append(img)

    images[0].save(
        output_pdf,
        save_all=True,
        append_images=images[1:]
    )

    print(f" PDF created successfully → {output_pdf}")


def main():
    
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        story = json.load(f)

    engines_raw = list_engines()
    engines = engines_raw["engines"] if isinstance(engines_raw, dict) else engines_raw
    engine = choose_engine(engines)
    engine_id = engine["id"]

    print(" Using engine:", engine_id)

    for page_key in sorted(story.keys()):
        page = story[page_key]
        prompt = build_prompt(page)
        img_path = generate_image(engine_id, prompt, page_key)
        add_text(img_path, page)

    print(" Storybook generation complete!")
def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        story = json.load(f)

    engines_raw = list_engines()
    engines = engines_raw["engines"] if isinstance(engines_raw, dict) else engines_raw
    engine = choose_engine(engines)
    engine_id = engine["id"]

    print(" Using engine:", engine_id)

 
    for page_key in sorted(story.keys()):
        page = story[page_key]
        prompt = build_prompt(page)
        img_path = generate_image(engine_id, prompt, page_key)
        add_text(img_path, page)

    
    pdf_path = BASE_DIR / "storybook.pdf"
    pngs_to_pdf(OUT_DIR, pdf_path)


if __name__ == "__main__":
    main()


