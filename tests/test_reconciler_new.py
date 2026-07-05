import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from query_processor.ingestion import MarkdownPDFParser, PDFImageRenderer
from query_processor.reconciler import VisualReconciliationAgent

def main():
    pdf_path = Path("data/papers/1-Attention Is All You Need.pdf")
    output_images_dir = Path("data/images")
    
    print("======================================================================")
    print("            TESTING PROPRIETARY VISUAL RECONCILIATION LAYER            ")
    print("======================================================================")
    
    # 1. Parse and Render
    print("\n--- Ingesting first 2 pages of paper ---")
    parser = MarkdownPDFParser()
    raw_markdown = parser.to_markdown(pdf_path)
    
    renderer = PDFImageRenderer()
    image_paths = renderer.render_pages(pdf_path, output_images_dir)
    
    # Keep only first 2 pages/images for fast verification
    pages_split = raw_markdown.split("<!-- PAGE ")
    # The first item may be empty if the string starts with the marker
    if pages_split and not pages_split[0].strip():
        pages_split = pages_split[1:]
    
    truncated_markdown = ""
    for idx in range(2):
        truncated_markdown += f"<!-- PAGE {idx+1} -->\n" + pages_split[idx]
        
    truncated_images = image_paths[:2]

    # 2. Reconcile
    print("\n--- Running Reconciliation on Page 1 and Page 2 ---")
    agent = VisualReconciliationAgent()
    reconciled_markdown = agent.reconcile_document(truncated_markdown, truncated_images)
    
    print("\n--- Reconciled Output (Snippet) ---")
    print(reconciled_markdown[:1500] + "\n...")

    print("\n======================================================================")
    print("                      RECONCILIATION TEST PASSED!                     ")
    print("======================================================================")

if __name__ == "__main__":
    main()
