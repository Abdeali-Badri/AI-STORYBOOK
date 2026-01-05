# AI Storybook Project - Fixed Directory Structure

## Project Root: `c:\Users\KIIT\Documents\AI STORYBOOK`

```
AI STORYBOOK/
├── app.py                          # Flask web app (currently empty)
├── gist_to_story.py               # Generates story from gist using OpenAI
├── image_generator.py             # Generates images and adds text overlays
├── pdf_generstor.py               # Creates PDF from generated images
├── split_pages.py                 # Splits story into page JSON files
├── test.py                        # Test script
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables (API keys)
├── .gitignore
├── .git/
│
├── stories/                       # Story input storage
│   └── story.json                # Main story file (input for image_generator.py)
│
├── static/                        # All web assets
│   ├── fonts/                    # Custom fonts for text overlay
│   │   └── *.ttf
│   ├── images/                   # Generated images from Stability AI
│   │   ├── page_1.png
│   │   ├── page_2.png
│   │   └── ...
│   ├── pdf/                      # Final PDF output
│   │   └── storybook.pdf
│   ├── pages/                    # Individual page JSON files
│   ├── stories/                  # Story variants (organized by story_ID)
│   │   ├── story_8768a39b/
│   │   │   ├── metadata.json
│   │   │   ├── story.json
│   │   │   ├── page_1.json
│   │   │   └── ...
│   │   └── story_9c423e01/
│   │       └── ...
│   └── (other static assets)
│
├── output/                        # Archive & legacy outputs (optional)
│   ├── final_pdf/
│   └── prev_img_dataset/         # Previous image archives
│
├── venv/                          # Python virtual environment
└── __pycache__/                  # Python cache files

```

## Key Path Fixes Applied

### image_generator.py
- ✅ `BASE_DIR` → `Path(__file__).resolve().parent` (AI STORYBOOK folder)
- ✅ `STORY_PATH` → `BASE_DIR / "stories" / "story.json"` (Input story file)
- ✅ `OUT_DIR` → `BASE_DIR / "static" / "images"` (Generated images)
- ✅ `PDF_DIR` → `BASE_DIR / "static" / "pdf"` (Output PDF)
- ✅ `FONTS_DIR` → `BASE_DIR / "static" / "fonts"` (Custom fonts)
- ✅ PDF script reference → `"pdf_generstor.py"` (correct file name)

### pdf_generstor.py
- ✅ `BASE_DIR` → `Path(__file__).resolve().parent` (AI STORYBOOK folder, NOT parent.parent)
- ✅ Image source → `BASE_DIR / "static" / "images"`
- ✅ PDF output → `BASE_DIR / "static" / "pdf" / "storybook.pdf"`
- ✅ Archive destination → `BASE_DIR / "output" / "prev_img_dataset"`

### split_pages.py
- ✅ `base_dir` default → `Path(__file__).resolve().parent / "static" / "stories"`
- ✅ All file operations use `Path` objects instead of `os.path`
- ✅ Proper directory creation with `mkdir(parents=True, exist_ok=True)`

## Workflow

1. **Generate Story** (`gist_to_story.py`)
   - Input: Gist string
   - Output: Story JSON with pages
   - Save to: `stories/story.json`

2. **Generate Images** (`image_generator.py`)
   - Input: `stories/story.json`
   - Process: Create image prompts + generate via Stability AI + add text overlays
   - Output: `static/images/page_X.png`
   - Auto-triggers: PDF generation

3. **Create PDF** (`pdf_generstor.py`)
   - Input: All PNG files from `static/images/`
   - Process: Combine images into single PDF
   - Output: `static/pdf/storybook.pdf`
   - Archive: Move old images to `output/prev_img_dataset/`

4. **Split Pages** (`split_pages.py`) - Alternative organization
   - Saves organized story structures to `static/stories/story_XXXXX/`

## Environment Requirements

Create `.env` file in project root:
```
STABILITY_API_KEY=your_api_key_here
FONT_PATH=/path/to/custom/font.ttf  # Optional
```

## All Errors Fixed ✅

- ❌ ~~Hardcoded path: `C:/hsz_projects/story_maker_project`~~
- ❌ ~~Double assignment: `BASE_DIR = BASE_DIR =`~~
- ❌ ~~Wrong parent directory references~~
- ❌ ~~Path pointing to non-existent `output/` folder for images~~
- ❌ ~~Wrong PDF generator script path~~
- ✅ All paths now use relative Path objects
- ✅ All directories exist and are correctly referenced
- ✅ Consistent path handling throughout codebase
