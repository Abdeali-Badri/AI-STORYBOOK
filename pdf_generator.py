import os 
import shutil
import sys 
from pathlib import Path
from PIL import Image 

BASE_DIR = Path(__file__).resolve().parent

def img_to_pdf(images_folder, output_pdfName):
    # Ensure paths are Path objects
    images_folder = Path(images_folder)
    output_pdfName = Path(output_pdfName)
    
    if not images_folder.exists():
        print(f"Error: Images folder not found at {images_folder}")
        return

    # Filter for standard image extensions
    valid_extensions = {".png", ".jpg", ".jpeg", ".bmp"}
    file_list = sorted([f for f in os.listdir(images_folder) if Path(f).suffix.lower() in valid_extensions])
    
    if not file_list : 
        print("Folder is empty or contains no images!")
        return
        
    img_list = []   
    for f in file_list :  
        img_path = images_folder / f
        try:
            image = Image.open(img_path).convert("RGB")
            img_list.append(image)
        except Exception as e:
            print(f"Warning: Failed to load image {f}: {e}")

    if not img_list :
        print("Error: No valid images could be loaded.")
        return 
        
    first_img = img_list[0]
    remaining_img = img_list[1:] 

    # Ensure output directory exists for the PDF
    output_pdfName.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        first_img.save(output_pdfName, "PDF", resolution=100.0, save_all=True, append_images=remaining_img)
        print(f"PDF successfully created at: {output_pdfName}")
    except Exception as e:
        print(f"Error saving PDF: {e}")

def archive_images():
    """Move images to archive folder."""
    current_folder = BASE_DIR / "static" / "images"
    destination_folder = BASE_DIR / "output" / "prev_img_dataset"
    
    if not current_folder.exists():
         return

    destination_folder.mkdir(parents=True, exist_ok=True)

    files = os.listdir(current_folder)
    print(f"Moving images to {destination_folder}...")
    for f in files :
        src = current_folder / f
        dst = destination_folder / f
        if src.is_file():
            try:
                shutil.move(str(src), str(dst))
            except Exception as e:
                print(f"Warning: Failed to move {f}: {e}")
    
    print(f"Moved images to {destination_folder}")

def main():
    img_folder = BASE_DIR / "static" / "images"
    pdf_file = BASE_DIR / "static" / "pdf" / "storybook.pdf"
    
    print("Starting PDF generation...")
    img_to_pdf(img_folder, pdf_file) 
    
    print("Archiving images...")
    archive_images()

if __name__ == "__main__":
    main()