import os
import json
import uuid

def split_pages(story_data, base_dir="static/stories"):
    """Split story into separate JSON files with page numbers as main categories"""
    
    # Generate a unique story ID
    story_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join(base_dir, f"story_{story_id}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Main JSON file that contains all pages with page numbers as keys
    main_json = {}
    
    # Page 1: Title Page
    main_json["page_1"] = {
        "type": "title",
        "title": story_data["title"],
        "story_overview": story_data["story_overview"],
        "character": story_data["character"]
    }
    
    # Story Pages (2 to N)
    for i, page in enumerate(story_data["pages"], start=2):
        page_data = {
            "type": "story",
            "text": page["text"],
            "scene": page["scene"],
            "character": story_data["character"]
        }
        
        # Add moral to the last page
        if i == len(story_data["pages"]) + 1:
            page_data["moral"] = story_data["moral"]
        
        main_json[f"page_{i}"] = page_data
    
    # Save all pages in one JSON file
    with open(os.path.join(output_dir, "story.json"), "w", encoding="utf-8") as f:
        json.dump(main_json, f, indent=4, ensure_ascii=False)
    
    # Also create individual page files (optional)
    for page_key, page_data in main_json.items():
        page_num = page_key.split("_")[1]
        with open(os.path.join(output_dir, f"page_{page_num}.json"), "w", encoding="utf-8") as f:
            json.dump({page_key: page_data}, f, indent=4, ensure_ascii=False)
    
    # Create metadata file
    metadata = {
        "story_id": story_id,
        "title": story_data["title"],
        "total_pages": len(main_json),
        "pages": list(main_json.keys()),
        "main_file": "story.json"
    }
    
    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    
    return {
        "story_id": story_id,
        "output_dir": output_dir,
        "total_pages": len(main_json),
        "main_json_file": os.path.join(output_dir, "story.json")
    }


def split_pages_alternative(story_data, base_dir="static/stories"):
    """Alternative: Single JSON file with nested structure"""
    
    story_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join(base_dir, f"story_{story_id}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Structure with pages as main object
    story_structure = {
        "metadata": {
            "story_id": story_id,
            "title": story_data["title"],
            "total_pages": len(story_data["pages"]) + 1
        },
        "pages": {}  # Pages will be added here with page numbers as keys
    }
    
    # Add page 1
    story_structure["pages"]["page_1"] = {
        "page_number": 1,
        "type": "title",
        "title": story_data["title"],
        "story_overview": story_data["story_overview"],
        "character": story_data["character"]
    }
    
    # Add story pages
    for i, page in enumerate(story_data["pages"], start=2):
        page_data = {
            "page_number": i,
            "type": "story",
            "text": page["text"],
            "scene": page["scene"],
            "character": story_data["character"]
        }
        
        # Add moral to last page
        if i == len(story_data["pages"]) + 1:
            page_data["moral"] = story_data["moral"]
        
        story_structure["pages"][f"page_{i}"] = page_data
    
    # Save to file
    with open(os.path.join(output_dir, "story_structured.json"), "w", encoding="utf-8") as f:
        json.dump(story_structure, f, indent=4, ensure_ascii=False)
    
    return story_structure
