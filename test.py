from gist_to_story import generate_story_with_moral
from split_pages import split_pages  


def main():
    """Main function to generate and save a story"""
    print(" Starting story generation...")
    
    # Generate story from gist
    print("\n Generating story...")
    result = generate_story_with_moral(
        "Story book about zebra and tiger playing chess together"
    )
    
    print(f"Story generated: '{result['title']}'")
    print(f" {len(result['pages'])} pages created")
    print(f" Main character: {result['character']['name']}")
    
    # Split and save pages
    print("\n Saving pages to JSON files...")
    output = split_pages(result)
    
    print("\n Story created successfully!")
    print(" Saved at:", output['output_dir'])
    print(f" Main JSON file: {output['main_json_file']}")
    print(f" Total pages: {output['total_pages']}")
    
    return output


if __name__ == "__main__":
    main()

