"""
explorer.py

Generates advanced Graph Explorer visualization HTML dashboards with shortest path trace,
relationship filters, node collapses, statistics sidebars, and custom visual legends.
"""

import logging
from pathlib import Path
import re
from typing import Union
import networkx as nx
from pyvis.network import Network

from graph.statistics import generate_graph_statistics

logger = logging.getLogger(__name__)


class ExplorerVisualizer:
    """
    Constructs high-end interactive Graph Explorers with advanced filters and shortest path highlighting.
    """

    NODE_COLORS = {
        "Paper": "#e74c3c",       # Red
        "Author": "#3498db",      # Blue
        "Method": "#2ecc71",      # Green
        "Dataset": "#9b59b6",     # Purple
        "Institution": "#f1c40f", # Yellow
        "Metric": "#1abc9c",      # Teal
        "Task": "#e67e22",        # Orange
        "Topic": "#34495e",       # Dark blue-gray
        "Architecture": "#d35400",# Dark orange
        "Benchmark": "#95a5a6",   # Gray
        "Conference": "#8e44ad",  # Dark purple
    }

    def visualize_explorer(self, graph: nx.MultiDiGraph, output_path: Union[str, Path]) -> Path:
        """
        Creates a custom Graph Explorer HTML visualization and saves it to output_path.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating advanced Graph Explorer visualizer for {graph.number_of_nodes()} nodes.")

        # Compute graph stats to display in the visualizer sidebar
        stats = generate_graph_statistics(graph)

        # 1. Setup PyVis Network
        net = Network(
            height="950px",
            width="100%",
            bgcolor="#0c0f12",
            font_color="white",
            directed=True,
            notebook=False,
        )
        net.barnes_hut()

        # 2. Add Nodes
        for node, data in graph.nodes(data=True):
            node_type = data.get("type", "Unknown")
            name = data.get("name") or data.get("title") or node
            description = data.get("description") or data.get("abstract") or "No description available."
            paper_count = data.get("paper_count", 1)
            degree = graph.degree(node)

            color = self.NODE_COLORS.get(node_type, "#7f8c8d")
            size = min(60, 15 + 3 * degree)

            hover_tooltip = f"""
            <div style="font-family: Arial, sans-serif; font-size: 13px; color: white; background: #1c2024; padding: 10px; border-radius: 5px; border: 1px solid #333;">
                <b>ID:</b> {node}<br/>
                <b>Name:</b> {name}<br/>
                <b>Type:</b> {node_type}<br/>
                <b>Description:</b> {description}<br/>
                <b>Papers:</b> {paper_count}<br/>
                <b>Degree:</b> {degree}
            </div>
            """

            net.add_node(
                node,
                label=name,
                title=hover_tooltip,
                group=node_type,
                color=color,
                size=size,
            )

        # 3. Add Edges
        # Get unique relationship types for the HTML filter dropdown
        unique_relationships = set()
        for source, target, data in graph.edges(data=True):
            relation = data.get("relationship", "RELATED_TO")
            unique_relationships.add(relation)
            confidence = data.get("confidence", 1.0)

            net.add_edge(
                source,
                target,
                title=f"Relationship: {relation} (Confidence: {confidence})",
                label=relation,
            )

        # 4. Save standard HTML file
        temp_file = output_path.with_name(f"_temp_explorer_{output_path.name}")
        net.write_html(str(temp_file))

        # 5. Read generated file for injection
        with open(temp_file, "r", encoding="utf-8") as f:
            html = f.read()

        # Build legend HTML block
        legend_items = []
        for ntype, color in self.NODE_COLORS.items():
            legend_items.append(
                f'<div class="legend-row">'
                f'<span class="legend-color" style="background-color: {color};"></span>'
                f'<span>{ntype}</span>'
                f'</div>'
            )
        legend_html = "\n".join(legend_items)

        # Build relationships options list
        rel_options = []
        for rel in sorted(list(unique_relationships)):
            rel_options.append(f'<option value="{rel}">{rel}</option>')
        rel_options_html = "\n".join(rel_options)

        # Custom CSS Panel and Sidebar
        style_inject = """
        <style type="text/css">
        #explorer-panel {
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background-color: rgba(18, 22, 28, 0.95);
            color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            font-family: 'Segoe UI', Arial, sans-serif;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6);
            border: 1px solid #00bcd4;
            width: 320px;
            max-height: 85vh;
            overflow-y: auto;
        }
        #explorer-panel h3 {
            margin-top: 0;
            margin-bottom: 12px;
            font-size: 20px;
            color: #00bcd4;
            border-bottom: 1px solid #334;
            padding-bottom: 8px;
            letter-spacing: 0.5px;
        }
        #explorer-panel label {
            display: block;
            margin-bottom: 5px;
            font-size: 11px;
            color: #8892b0;
            text-transform: uppercase;
            font-weight: bold;
        }
        #explorer-panel select, #explorer-panel input {
            width: 100%;
            padding: 8px;
            margin-bottom: 12px;
            background-color: #161b22;
            color: #ffffff;
            border: 1px solid #30363d;
            border-radius: 6px;
            box-sizing: border-box;
        }
        #explorer-panel button {
            width: 100%;
            padding: 10px;
            background-color: #006064;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 8px;
            transition: background-color 0.2s;
        }
        #explorer-panel button:hover {
            background-color: #00838f;
        }
        #explorer-panel .secondary-btn {
            background-color: #333a42;
        }
        #explorer-panel .secondary-btn:hover {
            background-color: #48525d;
        }
        #explorer-panel .reset-btn {
            background-color: #b71c1c;
        }
        #explorer-panel .reset-btn:hover {
            background-color: #d32f2f;
        }
        .legend-section {
            border-top: 1px solid #334;
            margin-top: 15px;
            padding-top: 10px;
        }
        .legend-row {
            display: flex;
            align-items: center;
            margin-bottom: 6px;
            font-size: 12px;
            color: #cbd5e1;
        }
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 3px;
            margin-right: 8px;
            display: inline-block;
        }
        .stats-section {
            border-top: 1px solid #334;
            margin-top: 15px;
            padding-top: 10px;
            font-size: 12px;
            color: #a0aec0;
        }
        .stats-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
        }
        </style>
        """

        panel_html = f"""
        <div id="explorer-panel">
            <h3>GraphRAG Explorer</h3>
            
            <label for="search-input">Search Entities:</label>
            <input type="text" id="search-input" placeholder="Enter node ID or name..." onkeydown="if(event.key === 'Enter') searchNode()" />
            <button onclick="searchNode()">Search & Center</button>
            
            <label for="type-filter">Filter Node Type:</label>
            <select id="type-filter" onchange="filterNodes()">
                <option value="all">Show All Node Types</option>
                <option value="Paper">Papers Only</option>
                <option value="Author">Authors Only</option>
                <option value="Method">Methods Only</option>
                <option value="Dataset">Datasets Only</option>
                <option value="Institution">Institutions Only</option>
            </select>
            
            <label for="rel-filter">Filter Relationship:</label>
            <select id="rel-filter" onchange="filterEdges()">
                <option value="all">Show All Relationships</option>
                {rel_options_html}
            </select>
            
            <button class="secondary-btn" onclick="highlightShortestPath()">Trace Shortest Path</button>
            <button class="secondary-btn" onclick="toggleSelectedNeighbors()">Toggle Selected Neighbors</button>
            <button class="reset-btn" onclick="resetExplorer()">Reset Dashboard</button>
            
            <div class="legend-section">
                <label>Color Legend</label>
                {legend_html}
            </div>
            
            <div class="stats-section">
                <label>Graph Statistics</label>
                <div class="stats-row"><span>Total Nodes:</span> <span>{stats['summary']['total_nodes']}</span></div>
                <div class="stats-row"><span>Total Edges:</span> <span>{stats['summary']['total_edges']}</span></div>
                <div class="stats-row"><span>Average Degree:</span> <span>{stats['summary']['average_degree']}</span></div>
                <div class="stats-row"><span>Components Count:</span> <span>{stats['connected_components']['count']}</span></div>
                <div class="stats-row"><span>LCC Size:</span> <span>{stats['connected_components']['largest_connected_component_size']}</span></div>
            </div>
        </div>
        """

        js_controls = """
        <script type="text/javascript">
        var originalNodes = null;
        var originalEdges = null;

        function saveState() {
            if (!originalNodes) {
                originalNodes = nodes.get();
            }
            if (!originalEdges) {
                originalEdges = edges.get();
            }
        }

        function searchNode() {
            saveState();
            var query = document.getElementById("search-input").value.trim().toLowerCase();
            if (!query) {
                alert("Please enter a search keyword.");
                return;
            }
            var matched = originalNodes.find(function(n) {
                var name = (n.label || "").toLowerCase();
                return name.includes(query) || n.id.toLowerCase().includes(query);
            });
            if (matched) {
                network.selectNodes([matched.id]);
                network.focus(matched.id, {
                    scale: 1.2,
                    animation: { duration: 800 }
                });
            } else {
                alert("Entity not found!");
            }
        }

        function filterNodes() {
            saveState();
            var type = document.getElementById("type-filter").value;
            if (type === "all") {
                nodes.update(originalNodes.map(function(n) { return { id: n.id, hidden: false }; }));
            } else {
                var updated = originalNodes.map(function(n) {
                    return { id: n.id, hidden: n.group !== type };
                });
                nodes.update(updated);
            }
        }

        function filterEdges() {
            saveState();
            var rel = document.getElementById("rel-filter").value;
            if (rel === "all") {
                edges.update(originalEdges.map(function(e) { return { id: e.id, hidden: false }; }));
            } else {
                var updated = originalEdges.map(function(e) {
                    return { id: e.id, hidden: e.label !== rel };
                });
                edges.update(updated);
            }
        }

        function highlightShortestPath() {
            saveState();
            var selected = network.getSelectedNodes();
            if (selected.length < 2) {
                alert("Please select exactly two nodes (hold Shift/Ctrl to select multiple) to trace the path.");
                return;
            }
            var start = selected[0];
            var end = selected[selected.length - 1];

            // Client-side BFS shortest path discovery
            var queue = [[start, [start]]];
            var visited = new Set([start]);
            var path = null;

            while (queue.length > 0) {
                var current = queue.shift();
                var node = current[0];
                var currentPath = current[1];

                if (node === end) {
                    path = currentPath;
                    break;
                }

                var neighbors = network.getConnectedNodes(node);
                for (var i = 0; i < neighbors.length; i++) {
                    var neighbor = neighbors[i];
                    if (!visited.has(neighbor)) {
                        visited.add(neighbor);
                        queue.push([neighbor, currentPath.concat([neighbor])]);
                    }
                }
            }

            if (path) {
                var pathSet = new Set(path);
                // Hide nodes not in path and fade them out
                var nodeUpdates = originalNodes.map(function(n) {
                    if (pathSet.has(n.id)) {
                        return { id: n.id, hidden: false, borderWidth: 3, size: 45 };
                    } else {
                        return { id: n.id, hidden: false, opacity: 0.15 };
                    }
                });
                nodes.update(nodeUpdates);
            } else {
                alert("No routing path connects these nodes.");
            }
        }

        function toggleSelectedNeighbors() {
            saveState();
            var selected = network.getSelectedNodes();
            if (selected.length === 0) {
                alert("Please select a node to expand/collapse neighbors.");
                return;
            }
            var center = selected[0];
            var neighbors = new Set(network.getConnectedNodes(center));
            neighbors.add(center);

            var updated = originalNodes.map(function(n) {
                return { id: n.id, hidden: !neighbors.has(n.id) };
            });
            nodes.update(updated);
        }

        function resetExplorer() {
            saveState();
            document.getElementById("search-input").value = "";
            document.getElementById("type-filter").value = "all";
            document.getElementById("rel-filter").value = "all";
            network.unselectAll();
            
            nodes.update(originalNodes.map(function(n) {
                return { id: n.id, hidden: false, opacity: 1.0, borderWidth: 1, size: n.size };
            }));
            edges.update(originalEdges.map(function(e) {
                return { id: e.id, hidden: false };
            }));
        }
        </script>
        """

        # Injections
        html = html.replace("</head>", f"{style_inject}\n</head>")
        html = re.sub(r"(<body[^>]*>)", r"\1\n" + panel_html, html)
        html = html.replace("</body>", f"{js_controls}\n</body>")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        if temp_file.exists():
            temp_file.unlink()

        logger.info(f"Interactive Graph Explorer HTML visualizer saved to {output_path}")
        return output_path
