"""
watcher.py

Monitors the papers directory for new PDF additions and triggers the GraphRAG
ingestion, LLM extraction, validation, normalization, and merge updater pipeline.
"""

import logging
import os
from pathlib import Path
import time
import threading
from typing import Callable, List, Set

from graph.ingestion.loader import PDFLoader
from graph.ingestion.cleaner import TextCleaner
from graph.extraction.extractor import GraphExtractor
from graph.updater import GraphUpdater
from graph.extraction.normalizer import EntityNormalizer

logger = logging.getLogger(__name__)


class GraphWatcher:
    """
    Scans a directory for new PDF files and merges them into the global graph.
    """

    def __init__(
        self,
        graph_path: str | Path,
        papers_dir: str | Path,
        on_update_callback: Callable[[str], None] = None
    ):
        self.graph_path = Path(graph_path)
        self.papers_dir = Path(papers_dir)
        self.on_update = on_update_callback
        
        self.loader = PDFLoader()
        self.cleaner = TextCleaner()
        self.extractor = GraphExtractor()
        self.updater = GraphUpdater(self.graph_path)
        
        self._stop_event = threading.Event()
        self._watcher_thread: threading.Thread | None = None

    def scan_and_update(self) -> List[Path]:
        """
        Scans papers_dir for PDFs that are not yet registered as Paper nodes in the graph.
        """
        new_papers: List[Path] = []
        if not self.papers_dir.exists():
            logger.warning(f"Papers directory {self.papers_dir} does not exist.")
            return []

        # Find all PDFs
        pdf_files = list(self.papers_dir.glob("*.pdf"))

        # Find currently indexed paper IDs in the graph
        indexed_ids: Set[str] = set()
        if self.graph_path.exists() and self.graph_path.stat().st_size > 0:
            for node_id, attrs in self.updater.manager.graph.nodes(data=True):
                if attrs.get("type") == "Paper":
                    indexed_ids.add(node_id)

        # Scan for new files
        for pdf_path in pdf_files:
            # Replicate standard paper ID generation (lowercased stem with underscores)
            import re
            paper_id = pdf_path.stem.lower()
            paper_id = re.sub(r"[^\w\s-]", "", paper_id)
            paper_id = re.sub(r"[-\s]+", "_", paper_id).strip("_")

            if paper_id not in indexed_ids:
                logger.info(f"Detected new paper: {pdf_path.name} (ID: {paper_id})")
                new_papers.append(pdf_path)

        # Ingest, extract, and merge each new paper
        for pdf_path in new_papers:
            try:
                # Ingest & Clean
                raw_doc = self.loader.load(pdf_path)
                doc = self.cleaner.clean(raw_doc)

                # Extract
                result = self.extractor.extract(doc)

                # Update/Merge
                self.updater.update(result)
                logger.info(f"Successfully indexed and merged {pdf_path.name}")

                if self.on_update:
                    self.on_update(str(pdf_path))
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.error(f"Failed to automatically index {pdf_path.name}: {e}")

        return new_papers

    def start_watching(self, interval_seconds: int = 5) -> None:
        """
        Launches the background polling watcher loop.
        """
        if self._watcher_thread is not None and self._watcher_thread.is_alive():
            return

        self._stop_event.clear()
        self._watcher_thread = threading.Thread(
            target=self._watch_loop,
            args=(interval_seconds,),
            daemon=True,
            name="GraphWatcherThread"
        )
        self._watcher_thread.start()
        logger.info(f"GraphWatcher background polling started with {interval_seconds}s interval.")

    def stop_watching(self) -> None:
        """
        Stops the background folder polling.
        """
        self._stop_event.set()
        if self._watcher_thread:
            self._watcher_thread.join(timeout=2.0)
        logger.info("GraphWatcher background polling stopped.")

    def _watch_loop(self, interval_seconds: int) -> None:
        """
        Background execution block polling for folder edits.
        """
        while not self._stop_event.is_set():
            try:
                self.scan_and_update()
            except Exception as e:
                logger.error(f"Error during folder watcher poll: {e}")
            
            # Sleep in tiny steps to check stop flag responsively
            for _ in range(interval_seconds * 2):
                if self._stop_event.is_set():
                    break
                time.sleep(0.5)
