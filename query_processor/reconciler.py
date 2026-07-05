import re
import logging
from pathlib import Path
from typing import List
from PIL import Image
from google import genai
from llm.config import LLM_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)

import time

class VisualReconciliationAgent:
    """
    Multimodal Agent that compares parsed Markdown text with rendered page images,
    using Gemini to reconstruct figures, charts, and layout anomalies into
    high-fidelity Markdown representations.
    """
    def __init__(self, api_key: str = None, model: str = None):
        # Initialize the standard Google GenAI client
        self.api_key = api_key or LLM_API_KEY
        self.model = model or LLM_MODEL or "gemini-2.5-flash"
        self.client = genai.Client(api_key=self.api_key)

    def reconcile_page(self, page_markdown: str, image_path: Path) -> str:
        """
        Sends page text and page image to Gemini Vision to reconcile and refine formatting.
        Handles API rate limits with automatic retry backoffs.
        """
        if not image_path.exists():
            logger.warning(f"Image not found at {image_path}. Returning raw text.")
            return page_markdown

        # Load page image
        img = Image.open(image_path)
        
        prompt = f"""You are a document reconciliation agent.
We have parsed text from a page of a PDF paper into raw Markdown, but standard text parsing loses diagrams, flowcharts, mathematical structures, or formatting inside visual figures.

Your task:
1. Compare the provided raw Markdown text against the actual page image.
2. If there are tables in the image, check if the Markdown tables match them accurately. Correct any broken table cells or misaligned columns.
3. If there are figures, graphs, flowcharts, or equations in the image, write a concise textual description of their logical contents (e.g., summary of a plot, steps in a flowchart, or LaTeX format for equations) and insert it at the appropriate location in the Markdown.
4. If there is text inside shapes/drawings that was not extracted in the raw Markdown, append it gracefully.
5. Retain the exact original text and headers. Do not summarize or omit the actual paper text.

Raw Markdown Text:
---
{page_markdown}
---

Return the finalized, reconciled, high-fidelity Markdown content for this page.
Do NOT include any extra notes, conversations, or surrounding code block wrappers like ```markdown. Just return the clean, updated Markdown string.
"""
        max_retries = 3
        backoff = 5.0
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[img, prompt]
                )
                return response.text.strip()
            except Exception as e:
                err_msg = str(e)
                # Check for rate limit or quota exceeded
                if ("429" in err_msg or "quota" in err_msg.lower() or "limit" in err_msg.lower()) and attempt < max_retries - 1:
                    print(f"\n[VisualReconciliationAgent] Rate limit hit. Sleeping {backoff}s before retry (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(backoff)
                    backoff *= 1.5
                    continue
                
                logger.error(f"Error during visual reconciliation for {image_path.name}: {e}")
                return page_markdown

    def reconcile_document(self, raw_markdown: str, image_paths: List[Path]) -> str:
        """
        Parses the raw document markdown page-by-page, matches them with images,
        and runs reconciliation.
        """
        # Split markdown into pages based on <!-- PAGE X --> markers
        pages_split = re.split(r'<!-- PAGE \d+ -->', raw_markdown)
        # The first split element is empty/intro if the marker started the string
        if pages_split and not pages_split[0].strip():
            pages_split = pages_split[1:]
            
        reconciled_pages = []
        total_pages = min(len(pages_split), len(image_paths))
        
        print(f"Beginning visual reconciliation of {total_pages} pages...")
        
        for i in range(total_pages):
            page_content = pages_split[i].strip()
            img_path = image_paths[i]
            
            print(f"  • Reconciling Page {i + 1}/{total_pages} ({img_path.name})...")
            reconciled_text = self.reconcile_page(page_content, img_path)
            
            reconciled_pages.append(f"<!-- PAGE {i + 1} -->\n{reconciled_text}")
            
        return "\n\n".join(reconciled_pages)
