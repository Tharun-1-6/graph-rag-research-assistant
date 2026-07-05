"""
updater.py

Responsible for incrementally updating the existing global GraphRAG knowledge graph
with new papers and extraction results, without rebuilding the graph from scratch.
"""

import logging
from pathlib import Path
from typing import Union

from graph.extraction.models import ExtractionResult
from graph.graph_builder.graph_manager import GraphManager

logger = logging.getLogger(__name__)


class GraphUpdater:
    """
    Handles incremental updates to the global NetworkX knowledge graph.
    """

    def __init__(self, graph_path: Union[str, Path]):
        """
        Initializes the updater with a target file path.

        Parameters
        ----------
        graph_path : Union[str, Path]
            The location where the consolidated global GraphML graph is saved.
        """
        self.graph_path = Path(graph_path)
        self.manager = GraphManager()

        # Load existing graph if it exists
        if self.graph_path.exists() and self.graph_path.stat().st_size > 0:
            try:
                logger.info(f"Loading existing graph from {self.graph_path}")
                self.manager.load_graph(self.graph_path)
                logger.info(f"Existing graph loaded successfully with {self.manager.num_nodes} nodes.")
            except Exception as e:
                logger.error(f"Failed to load existing graph from {self.graph_path}: {e}. Initializing a new graph.")

    def update(self, extraction_result: ExtractionResult) -> None:
        """
        Merges new extraction results into the existing graph and saves it back.

        Parameters
        ----------
        extraction_result : ExtractionResult
            The normalized extraction results from a new research paper.
        """
        paper_title = extraction_result.paper.title
        logger.info(f"Merging extraction results from paper: '{paper_title}'")

        # Use the updated GraphManager's merging logic
        self.manager.add_extraction(extraction_result)

        # Save back to the disk
        logger.info(f"Saving consolidated graph back to {self.graph_path}")
        self.manager.save_graph(self.graph_path)
        logger.info("Incremental update completed successfully.")
