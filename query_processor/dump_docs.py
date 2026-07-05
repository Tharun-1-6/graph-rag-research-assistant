import os
import json
from pathlib import Path
from ingestion import MarkdownPDFParser

def main():
    base_dir = Path(__file__).resolve().parents[1]
    papers_dir = base_dir / "data" / "papers"
    output_file = base_dir / "raw_docs.json"
    
    parser = MarkdownPDFParser()
    pdf_files = list(papers_dir.glob("*.pdf"))
    
    print(f"Scanning {len(pdf_files)} PDF files in {papers_dir}...")
    documents = []
    
    for pdf_path in pdf_files:
        print(f"Parsing '{pdf_path.name}' to markdown...")
        try:
            markdown_text = parser.to_markdown(pdf_path)
            
            documents.append({
                "doc_id": pdf_path.stem.lower().replace(" ", "_"),
                "title": pdf_path.stem,
                "text": markdown_text
            })
        except Exception as e:
            print(f"Error parsing {pdf_path.name}: {e}")
            
    print(f"Writing parsed documents to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=4, ensure_ascii=False)
        
    print("Done! Upload 'raw_docs.json' to your Colab notebook to generate embeddings.")

if __name__ == "__main__":
    main()
