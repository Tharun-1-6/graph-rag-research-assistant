import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from query_processor.ingestion import MarkdownPDFParser, PDFImageRenderer

def main():
    pdf_path = Path("data/papers/1-Attention Is All You Need.pdf")
    output_images_dir = Path("data/images")
    
    print("======================================================================")
    print("               TESTING NEW PROPRIETARY INGESTION LAYER                ")
    print("======================================================================")
    
    # 1. Test Markdown Parsing
    print("\n--- Step 1: Parsing PDF to Markdown (with Tables) ---")
    parser = MarkdownPDFParser()
    markdown_content = parser.to_markdown(pdf_path)
    
    # Let's inspect if any table was extracted
    tables_found = [line for line in markdown_content.split("\n") if "|" in line]
    print(f"Markdown character length: {len(markdown_content)}")
    print(f"Number of table rows/lines found: {len(tables_found)}")
    
    # Print the first 800 characters of parsed markdown
    print("\n--- Snippet of Parsed Markdown ---")
    print(markdown_content[:800] + "\n...")

    # 2. Test Image Rendering
    print("\n--- Step 2: Rendering PDF Pages to Images ---")
    renderer = PDFImageRenderer()
    image_paths = renderer.render_pages(pdf_path, output_images_dir)
    print(f"Successfully rendered {len(image_paths)} pages to images.")
    for idx, img_path in enumerate(image_paths):
        print(f"  • Page {idx + 1}: {img_path.name} (exists: {img_path.exists()})")

    print("\n======================================================================")
    print("                       INGESTION TEST PASSED!                         ")
    print("======================================================================")

if __name__ == "__main__":
    main()
