import os
import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any

class MarkdownPDFParser:
    """
    Parses a PDF file page-by-page, identifying tables using PyMuPDF's
    table finder and converting them to Markdown tables to preserve formatting,
    while extracting the remaining text as clean Markdown.
    """
    def to_markdown(self, pdf_path: str | Path) -> str:
        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)
        markdown_pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Find tables on the page
            tabs = page.find_tables()
            table_rects = []
            markdown_tables = []
            
            # Process extracted tables into markdown representations
            if tabs:
                for tab in tabs:
                    table_rects.append(tab.bbox)
                    
                    # Construct markdown table from table grid cells
                    grid = tab.extract()
                    if not grid:
                        continue
                        
                    md_rows = []
                    # Filter out None and strip spaces
                    header = [str(cell or "").strip() for cell in grid[0]]
                    md_rows.append("| " + " | ".join(header) + " |")
                    md_rows.append("| " + " | ".join(["---"] * len(header)) + " |")
                    
                    for row in grid[1:]:
                        row_cells = [str(cell or "").strip() for cell in row]
                        # Match columns size of header
                        if len(row_cells) < len(header):
                            row_cells += [""] * (len(header) - len(row_cells))
                        else:
                            row_cells = row_cells[:len(header)]
                        md_rows.append("| " + " | ".join(row_cells) + " |")
                        
                    markdown_tables.append("\n" + "\n".join(md_rows) + "\n")
            
            # Extract page blocks
            blocks = page.get_text("blocks")
            # Sort blocks top-to-bottom, left-to-right
            blocks.sort(key=lambda b: (b[1], b[0]))
            
            page_text_blocks = []
            current_table_idx = 0
            
            for block in blocks:
                bbox = block[:4]
                text = block[4].strip()
                
                # Check if block falls inside any table bbox
                inside_table = False
                for tab_idx, rect in enumerate(table_rects):
                    # Check overlap/intersection
                    if (bbox[0] >= rect[0] - 2 and bbox[2] <= rect[2] + 2 and
                        bbox[1] >= rect[1] - 2 and bbox[3] <= rect[3] + 2):
                        inside_table = True
                        break
                
                if inside_table:
                    # Place the table markdown in the flow at the first intersection block
                    if current_table_idx < len(markdown_tables):
                        page_text_blocks.append(markdown_tables[current_table_idx])
                        current_table_idx += 1
                    continue
                
                # Add headers, bullet points or normal paragraphs based on layout heuristic
                if text:
                    # Heuristic: large/short bold text blocks as markdown headers
                    if len(text) < 100 and (text.isupper() or len(text.split('\n')) == 1):
                        # Convert to headings if it matches typical section indicators
                        if re.match(r'^\d+(\.\d+)*\s+[A-Z]', text) or text.startswith("Abstract") or text.startswith("Introduction") or text.startswith("Conclusion"):
                            page_text_blocks.append(f"\n## {text}\n")
                        else:
                            page_text_blocks.append(f"\n### {text}\n")
                    else:
                        page_text_blocks.append(text)
            
            # Join and clean spacing
            joined_page_content = "\n\n".join(page_text_blocks)
            markdown_pages.append(f"<!-- PAGE {page_num + 1} -->\n{joined_page_content}")

        doc.close()
        return "\n\n".join(markdown_pages)


class PDFImageRenderer:
    """
    Renders PDF pages into PNG images using PyMuPDF pixmap capability.
    This runs locally and requires no external binary dependencies.
    """
    def render_pages(self, pdf_path: str | Path, output_dir: str | Path) -> List[Path]:
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        doc = fitz.open(pdf_path)
        image_paths = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Zoom level for high quality image rendering (150 DPI equivalent zoom=2)
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            img_filename = f"{pdf_path.stem}_page_{page_num + 1}.png"
            img_path = output_dir / img_filename
            pix.save(img_path)
            image_paths.append(img_path)
            
        doc.close()
        return image_paths
