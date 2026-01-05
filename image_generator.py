import os
import sys
import requests
import base64
import json
import textwrap
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageStat

load_dotenv()

# CONFIG VALUES
API_KEY = os.getenv("STABILITY_API_KEY")
API_HOST = "https://api.stability.ai"
WIDTH = 1024
HEIGHT = 1024
STEPS = 30
SAMPLES = 1

# Project paths
BASE_DIR = Path(__file__).resolve().parent
STORIES_DIR = BASE_DIR / "stories"
STORIES_ARCHIVE_DIR = BASE_DIR / "output" / "stories_archive"
OUT_DIR = BASE_DIR / "static" / "images"
PDF_DIR = BASE_DIR / "static" / "pdf"
FONTS_DIR = BASE_DIR / "static" / "fonts"
# Try to find a custom font or config
CUSTOM_FONT_PATH = os.getenv("FONT_PATH")

def get_latest_story_path():
    """Get story.json from stories folder"""
    story_path = STORIES_DIR / "story.json"
    
    if not story_path.exists():
        print(f"Story file not found at {story_path}")
        return None
    
    print(f"Found story: {story_path}")
    return story_path

def get_story_folder_for_path(story_path):
    """Get the story folder from a story.json path"""
    return story_path.parent

def archive_story(story_path):
    """Move story files to archive directory after images are generated"""
    try:
        story_folder = get_story_folder_for_path(story_path)
        
        # Create archive directory if it doesn't exist
        STORIES_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create a timestamped archive folder
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_destination = STORIES_ARCHIVE_DIR / f"story_{timestamp}"
        archive_destination.mkdir(parents=True, exist_ok=True)
        
        # Move only story-related files to archive (avoid moving unrelated files)
        import shutil
        patterns = ["story.json", "metadata.json", "story_structured.json", "page_*.json"]
        for pattern in patterns:
            for file in story_folder.glob(pattern):
                if file.is_file():
                    shutil.move(str(file), str(archive_destination / file.name))
        
        print(f"✓ Story archived to: {archive_destination}")
        return True
    except Exception as e:
        print(f"Warning: Failed to archive story: {e}")
        return False



def setup_environment():
    """Ensure API key is present and output directory exists."""
    if not API_KEY:
        print("Error: STABILITY_API_KEY environment variable not set.")
        print("Please set it in your .env file or export it.")
        sys.exit(1)
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

def list_engines():
    """List available engines from Stability AI API."""
    url = f"{API_HOST}/v1/engines/list"
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Warning: Failed to list engines: {e}")
        return []

def choose_engine(engines):
    """Choose the best available engine, preferring SDXL."""
    if isinstance(engines, dict) and "engines" in engines:
        engines_list = engines["engines"]
    elif isinstance(engines, list):
        engines_list = engines
    else:
        engines_list = []

    if not engines_list:
        return None

    # Prefer 'sdxl' or 'stable-diffusion-xl'
    sdxl = next((e for e in engines_list if "sdxl" in (e.get("id", "").lower())), None)
    if sdxl:
        return sdxl
    
    # Fallback to 'stable-diffusion'
    sd = next((e for e in engines_list if "stable-diffusion" in (e.get("id", "").lower())), None)
    if sd:
        return sd
        
    return engines_list[0] if engines_list else None

def generate_image(engine_id, prompt, output_path):
    """Generate an image using the text-to-image API and save it."""
    url = f"{API_HOST}/v1/generation/{engine_id}/text-to-image"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "text_prompts": [{"text": prompt}],
        "cfg_scale": 7,
        "height": HEIGHT,
        "width": WIDTH,
        "steps": STEPS,
        "samples": SAMPLES
    }

    print(f"Generating image logic...")
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if resp.status_code != 200:
            print(f"Generation failed: {resp.status_code}")
            try:
                print(resp.json())
            except:
                print(resp.text)
            return False

        data = resp.json()
        artifacts = data.get("artifacts", [])
        
        if not artifacts:
            print("No artifacts found in response.")
            return False

        # Save the first artifact
        image_b64 = artifacts[0].get("base64")
        if image_b64:
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image_b64))
            return True
            
    except Exception as e:
        print(f"An error occurred during generation: {str(e)}")
        return False

def build_prompt(page):
    """Construct a rich prompt from page details."""
    style = (
        "children's storybook illustration, soft watercolor, bright colors, image should support black fonts, "
        "cute, joyful, whimsical, kid-friendly"
    )
    
    character = page.get("character", {})
    if isinstance(character, dict):
        char_desc = character.get("description", "")
        char_name = character.get("name", "")
    else:
        char_desc = str(character)
        char_name = ""

    if page.get("type") == "title":
        # For title page
        overview = page.get("story_overview", "")
        prompt = f"{style}. {overview}. Main character: {char_desc}"
    else:
        # For story pages - let AI infer animals from scene description
        scene = page.get("scene", "")
        
        # Build the prompt with scene description
        prompt = f"{style}. Scene: {scene}"
        
        # Explicitly add main character
        if char_name:
            prompt += f". Main character {char_name}: {char_desc}"
        else:
            prompt += f". Main character: {char_desc}"
        
        # Ask AI to infer and include any animals/creatures from the scene description
        prompt += ". Based on the scene description above, identify and include ANY animals, creatures, or characters mentioned in the scene. Show the main character prominently and interacting with all creatures/characters in the scene. Only include what is mentioned in the scene - do not add other unmentioned elements."
    
    return prompt

def get_font_paths():
    """Resolve font path based on env, fonts dir, or fallback."""
    # 1. Check Env Var
    if CUSTOM_FONT_PATH and Path(CUSTOM_FONT_PATH).exists():
        return Path(CUSTOM_FONT_PATH)
    
    # 2. Check fonts directory for any .ttf
    if FONTS_DIR.exists():
        ttfs = list(FONTS_DIR.glob("*.ttf"))
        if ttfs:
            return ttfs[0]
            
    # 3. Fallback (if no font found in folder or env)
    return None

def add_text_to_image(img_path, page):
    """Overlay title or story text onto the image."""
    try:
        img = Image.open(img_path).convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")
        
        font_path = get_font_paths()

        # Helper to load fonts with fallback
        def load_fonts(path):
            try:
                if path is None:
                    if FONTS_DIR.exists():
                        fonts = list(FONTS_DIR.glob("*.ttf")) + list(FONTS_DIR.glob("*.otf"))
                        if fonts:
                            fonts.sort()
                            path = fonts[0]
                        else:
                            raise IOError("No .ttf or .otf fonts found in fonts folder")
                    else:
                        raise IOError("Fonts folder does not exist")

                return (ImageFont.truetype(str(path), 60),
                        ImageFont.truetype(str(path), 36),
                        ImageFont.truetype(str(path), 32))
            except Exception as e:
                d = ImageFont.load_default()
                return d, d, d

        font_title, font_story, font_moral = load_fonts(font_path)

        # Helper: sample average background color in a bbox
        def sample_avg_color(image, bbox):
            try:
                crop = image.crop(bbox).convert("RGB")
                stat = ImageStat.Stat(crop)
                r, g, b = [int(x) for x in stat.mean[:3]]
                # Lighten the color by shifting toward white for a lighter shade
                r = min(255, int(r * 0.5 + 255 * 0.5))
                g = min(255, int(g * 0.5 + 255 * 0.5))
                b = min(255, int(b * 0.5 + 255 * 0.5))
                return (r, g, b)
            except Exception:
                return (250, 250, 250)

        # Helper: choose text color (black/white) based on luminance
        def choose_text_color(rgb):
            r, g, b = rgb
            luminance = (0.299*r + 0.587*g + 0.114*b)/255
            return (0, 0, 0, 255) if luminance > 0.6 else (255, 255, 255, 255)

        # Draw a rounded rect with alpha
        def draw_box(x0, y0, x1, y1, fill):
            draw.rounded_rectangle([x0, y0, x1, y1], radius=15, fill=fill)

        # Decide layout
        if page.get("type") == "title":
            text = page.get("title", "")
            font = font_title
            wrap_width = 28
            lines = textwrap.wrap(text, width=wrap_width)

            # Compute text block size
            padding = 20
            line_heights = [draw.textbbox((0,0), l, font=font)[3] - draw.textbbox((0,0), l, font=font)[1] for l in lines]
            text_h = sum(line_heights) + (len(lines)-1)*8
            text_w = max([draw.textbbox((0,0), l, font=font)[2] for l in lines]) if lines else 0
            box_w = min(img.width - 60, text_w + padding*2)
            box_h = text_h + padding*2
            box_x = (img.width - box_w)//2
            box_y = 30

            # Sample background under box to pick a harmonious color
            sample_bbox = (max(0, box_x), max(0, box_y), min(img.width, box_x+box_w), min(img.height, box_y+box_h))
            bg = sample_avg_color(img, sample_bbox)
            text_color = choose_text_color(bg)
            box_color = (bg[0], bg[1], bg[2], 220)

            # Draw box and text
            draw_box(box_x, box_y, box_x+box_w, box_y+box_h, box_color)
            cur_y = box_y + padding
            for line in lines:
                bbox = draw.textbbox((0,0), line, font=font)
                t_w = bbox[2] - bbox[0]
                x = box_x + (box_w - t_w)//2
                draw.text((x, cur_y), line, font=font, fill=text_color)
                cur_y += (bbox[3] - bbox[1]) + 8

        else:
            text = page.get("text", "")
            moral = page.get("moral")
            font = font_story
            wrap_width = 40
            lines = textwrap.wrap(text, width=wrap_width)
            if moral:
                moral_lines = textwrap.wrap(f"Moral: {moral}", width=wrap_width)
            else:
                moral_lines = []

            # Compute text block size
            padding = 20
            all_lines = lines + ([] if not moral_lines else [""] + moral_lines)
            line_heights = [draw.textbbox((0,0), l, font=font)[3] - draw.textbbox((0,0), l, font=font)[1] for l in all_lines]
            text_h = sum(line_heights) + (len(all_lines)-1)*8
            text_w = max([draw.textbbox((0,0), l, font=font)[2] for l in all_lines]) if all_lines else 0
            box_w = min(img.width - 60, text_w + padding*2)
            box_h = text_h + padding*2
            box_x = (img.width - box_w)//2
            box_y = img.height - box_h - 30

            # Sample background under box to pick a harmonious color
            sample_bbox = (max(0, box_x), max(0, box_y), min(img.width, box_x+box_w), min(img.height, box_y+box_h))
            bg = sample_avg_color(img, sample_bbox)
            text_color = choose_text_color(bg)
            box_color = (bg[0], bg[1], bg[2], 220)

            # Draw box and text
            draw_box(box_x, box_y, box_x+box_w, box_y+box_h, box_color)
            cur_y = box_y + padding
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0,0), line, font=font)
                t_w = bbox[2] - bbox[0]
                x = box_x + (box_w - t_w)//2
                draw.text((x, cur_y), line, font=font, fill=text_color)
                cur_y += (bbox[3] - bbox[1]) + 8

            if moral_lines:
                # Add a small separator line
                cur_y += 6
                for line in moral_lines:
                    bbox = draw.textbbox((0,0), line, font=font_moral)
                    t_w = bbox[2] - bbox[0]
                    x = box_x + (box_w - t_w)//2
                    draw.text((x, cur_y), line, font=font_moral, fill=text_color)
                    cur_y += (bbox[3] - bbox[1]) + 6

        # Save back to same path
        img.save(img_path)
        print(f"Added text to {img_path.name}")
    except Exception as e:
        print(f"Failed to add text to image: {e}")

def main():
    setup_environment()

    # 1. Select Engine
    print("Fetching available engines...")
    engines = list_engines()
    chosen_engine = choose_engine(engines)
    
    # Use a default if API listing fails, assuming user has access
    engine_id = chosen_engine.get("id") if chosen_engine else "stable-diffusion-xl-1024-v1-0"
    print(f"Using engine: {engine_id}")

    # 2. Load Story - Find the latest story automatically
    story_path = get_latest_story_path()
    if not story_path:
        print("Could not find any story to process.")
        sys.exit(1)
        
    with open(story_path, "r", encoding="utf-8") as f:
        story_data = json.load(f)

    # 3. Iterate and Generate
    print("Starting image generation...")
    
    # Sort keys to process in order page_1
    
    page_keys = [k for k in story_data.keys() if k.startswith("page_")]
    try:
        page_keys.sort(key=lambda x: int(x.split('_')[1]))
    except:
        page_keys.sort() # Fallback

    images_generated = False
    for key in page_keys:
        print(f"\nProcessing {key}...")
        page = story_data[key]
        
        # Build prompt
        prompt = build_prompt(page)
        
        # Define output path
        output_file = OUT_DIR / f"{key}.png"
        archived_base = BASE_DIR / "output" / "prev_img_dataset" / f"{key}.png"
        
        # Generate Image Run every time as per automation request, or we can skip strictly if desired, but user probably wants fresh run)
        # If an output already exists, try to avoid overlaying text on top of previous text.
        if output_file.exists():
             # If we have a clean base image in archive, restore it and apply text
             if archived_base.exists():
                 try:
                     from shutil import copy2
                     copy2(str(archived_base), str(output_file))
                     print(f"Restored clean base image for {key} from archive. Re-applying text...")
                     add_text_to_image(output_file, page)
                     images_generated = True
                     continue
                 except Exception as e:
                     print(f"Warning: Failed to restore archived base image: {e}")

             # No clean base available — remove and regenerate to avoid stacking text
             try:
                 output_file.unlink()
                 print(f"Removed existing image {output_file.name} to regenerate cleanly.")
             except Exception:
                 pass

        success = generate_image(engine_id, prompt, output_file)
        
        if success:
            print(f"Generated image at {output_file}")
            # Overlay Text
            add_text_to_image(output_file, page)
            images_generated = True
        else:
            print(f"Failed to generate image for {key}")

    print("\nImage generation complete!")
    
    # 4. Automate PDF Generation
    if images_generated:
        print("\nStarting PDF generation...")
        pdf_script = BASE_DIR / "pdf_generstor.py"
        try:
            # Check if pdf script exists
            if not pdf_script.exists():
                 print(f"Error: PDF generator script not found at {pdf_script}")
            else:
                subprocess.run([sys.executable, str(pdf_script)], check=True)
                print("PDF generation finished.")
                # After PDF generation (and image archiving inside pdf_generstor), archive JSON story files
                print("\nArchiving story JSON files...")
                archive_story(story_path)
        except subprocess.CalledProcessError as e:
            print(f"Error running PDF generator: {e}")
    else:
        print("No images were generated or found, skipping PDF generation.")

if __name__ == "__main__":
    main()