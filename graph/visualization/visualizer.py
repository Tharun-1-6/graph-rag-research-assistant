"""
visualizer.py

Generates PyVis interactive visualizations of the GraphRAG knowledge graph,
customized with node/edge group coloring, size scaling, tooltips, and custom filters.
"""

import logging
from pathlib import Path
import re
from typing import Union
import networkx as nx
from pyvis.network import Network

logger = logging.getLogger(__name__)


class GlobalVisualizer:
    """
    Handles generation of interactive PyVis HTML visualizations.
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

    EDGE_COLORS = {
        "AUTHORED": "#3498db",
        "PROPOSES": "#2ecc71",
        "USES": "#e67e22",
        "EVALUATED_ON": "#9b59b6",
        "IMPROVES_UPON": "#1abc9c",
        "PUBLISHED_AT": "#8e44ad",
        "RELATED_TO": "#7f8c8d",
    }

    def __init__(self, bgcolor: str = "#111111", font_color: str = "white"):
        self.bgcolor = bgcolor
        self.font_color = font_color

    def visualize(self, graph: nx.MultiDiGraph, output_path: Union[str, Path]) -> Path:
        """
        Builds a customized PyVis visualization of the graph and saves it to output_path.

        Parameters
        ----------
        graph : nx.MultiDiGraph
            The knowledge graph.
        output_path : Union[str, Path]
            The location where the interactive HTML is saved.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating PyVis visualization for graph with {graph.number_of_nodes()} nodes.")

        # Instantiate Network
        net = Network(
            height="900px",
            width="100%",
            bgcolor=self.bgcolor,
            font_color=self.font_color,
            directed=True,
            notebook=False,
        )
        net.barnes_hut()

        # 1. Add Nodes
        for node, data in graph.nodes(data=True):
            node_type = data.get("type", "Unknown")
            name = data.get("name") or data.get("title") or node
            description = data.get("description") or data.get("abstract") or "No description available."
            paper_count = data.get("paper_count", 1)
            degree = graph.degree(node)

            # Assign colors & sizes
            color = self.NODE_COLORS.get(node_type, "#7f8c8d")
            size = 15 + 3 * degree
            # Cap node size to prevent huge components from blocking the view
            size = min(size, 65)

            # Construct HTML hover tooltip
            hover_tooltip = f"""
            <div style="font-family: Arial, sans-serif; font-size: 13px; color: white; background: #222; padding: 10px; border-radius: 5px;">
                <b>ID:</b> {node}<br/>
                <b>Name:</b> {name}<br/>
                <b>Type:</b> {node_type}<br/>
                <b>Description:</b> {description}<br/>
                <b>Papers:</b> {paper_count}<br/>
                <b>Degree (Connections):</b> {degree}
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

        # 2. Add Edges
        for source, target, data in graph.edges(data=True):
            relation = data.get("relationship", "RELATED_TO")
            color = self.EDGE_COLORS.get(relation, "#7f8c8d")
            confidence = data.get("confidence", 1.0)

            net.add_edge(
                source,
                target,
                title=f"Relationship: {relation} (Confidence: {confidence})",
                label=relation,
                color=color,
            )

        # 3. Save standard HTML
        temp_file = output_path.with_name(f"_temp_{output_path.name}")
        net.write_html(str(temp_file))

        # 4. Read generated HTML and post-process to inject custom controls & LCC node set
        with open(temp_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Calculate LCC nodes to pass to JS connected components filter
        lcc_js_set = "var lccNodeIds = new Set();"
        if graph.number_of_nodes() > 0:
            try:
                undirected = graph.to_undirected()
                components = list(nx.connected_components(undirected))
                if components:
                    lcc = max(components, key=len)
                    lcc_js_set = "var lccNodeIds = new Set([" + ",".join(f'"{n}"' for n in lcc) + "]);"
            except Exception as e:
                logger.error(f"Error calculating LCC components for JS injection: {e}")

        # Inject CSS controls and HTML Panel
        style_inject = """
        <style type="text/css">
        #control-panel {
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background-color: rgba(30, 30, 30, 0.95);
            color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            font-family: Arial, sans-serif;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            border: 1px solid #333333;
            max-width: 320px;
        }
        #control-panel h3 {
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 18px;
            border-bottom: 1px solid #444;
            padding-bottom: 8px;
            color: #00bcd4;
        }
        #control-panel label {
            display: block;
            margin-bottom: 5px;
            font-size: 12px;
            color: #aaaaaa;
        }
        #control-panel select, #control-panel input {
            width: 100%;
            padding: 8px;
            margin-bottom: 12px;
            background-color: #222222;
            color: #ffffff;
            border: 1px solid #444444;
            border-radius: 5px;
            box-sizing: border-box;
        }
        #control-panel button {
            width: 100%;
            padding: 10px;
            background-color: #00838f;
            color: #ffffff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin-bottom: 8px;
            transition: background-color 0.2s;
        }
        #control-panel button:hover {
            background-color: #00acc1;
        }
        #control-panel .secondary-btn {
            background-color: #424242;
        }
        #control-panel .secondary-btn:hover {
            background-color: #616161;
        }
        #control-panel .reset-btn {
            background-color: #c62828;
        }
        #control-panel .reset-btn:hover {
            background-color: #e53935;
        }
        </style>
        """

        panel_html = """
        <div id="control-panel">
            <h3>GraphRAG Explorer</h3>
            
            <label for="search-input">Search Entities:</label>
            <input type="text" id="search-input" placeholder="Enter keyword or name..." onkeydown="if(event.key === 'Enter') searchNode()" />
            <button onclick="searchNode()">Search & Zoom</button>
            
            <label for="type-filter">Filter by Type:</label>
            <select id="type-filter" onchange="filterNodes()">
                <option value="all">Show All Nodes</option>
                <option value="Paper">Papers Only</option>
                <option value="Author">Authors Only</option>
                <option value="Method">Methods Only</option>
                <option value="Dataset">Datasets Only</option>
                <option value="Institution">Institutions Only</option>
                <option value="Benchmark">Benchmarks Only</option>
            </select>
            
            <button class="secondary-btn" onclick="showNeighborsOnly()">Show Neighbors of Selected</button>
            <button class="secondary-btn" onclick="highlightLCC()">Highlight Largest Component</button>
            <button class="reset-btn" onclick="resetFilters()">Reset Visualization</button>
        </div>
        """

        js_controls = f"""
        <script type="text/javascript">
        var originalNodes = null;
        var originalEdges = null;

        function saveOriginalState() {{
            if (!originalNodes) {{
                originalNodes = nodes.get();
            }}
            if (!originalEdges) {{
                originalEdges = edges.get();
            }}
        }}

        function searchNode() {{
            saveOriginalState();
            var query = document.getElementById("search-input").value.trim().toLowerCase();
            if (!query) {{
                alert("Please enter a search term.");
                return;
            }}
            
            var found = originalNodes.find(function(node) {{
                var label = (node.label || "").toLowerCase();
                var title = (node.title || "").toLowerCase();
                return label.includes(query) || title.includes(query) || node.id.toLowerCase().includes(query);
            }});
            
            if (found) {{
                network.selectNodes([found.id]);
                network.focus(found.id, {{
                    scale: 1.2,
                    animation: {{ duration: 800 }}
                }});
            }} else {{
                alert("No entity matching '" + query + "' found.");
            }}
        }}

        function filterNodes() {{
            saveOriginalState();
            var selectedType = document.getElementById("type-filter").value;
            
            if (selectedType === "all") {{
                nodes.update(originalNodes.map(function(n) {{ return {{ id: n.id, hidden: false }}; }}));
                return;
            }}
            
            var updated = originalNodes.map(function(n) {{
                var nType = n.group || "";
                return {{ id: n.id, hidden: nType !== selectedType }};
            }});
            nodes.update(updated);
        }}

        function showNeighborsOnly() {{
            saveOriginalState();
            var selected = network.getSelectedNodes();
            if (selected.length === 0) {{
                alert("Please select a node in the graph first.");
                return;
            }}
            var targetId = selected[0];
            var connected = network.getConnectedNodes(targetId);
            var neighborSet = new Set(connected);
            neighborSet.add(targetId);
            
            var updated = originalNodes.map(function(n) {{
                return {{ id: n.id, hidden: !neighborSet.has(n.id) }};
            }});
            nodes.update(updated);
        }}

        function highlightLCC() {{
            saveOriginalState();
            if (typeof lccNodeIds === "undefined") {{
                alert("Largest Connected Component data not loaded.");
                return;
            }}
            var updated = originalNodes.map(function(n) {{
                return {{ id: n.id, hidden: !lccNodeIds.has(n.id) }};
            }});
            nodes.update(updated);
        }}

        function resetFilters() {{
            saveOriginalState();
            document.getElementById("type-filter").value = "all";
            document.getElementById("search-input").value = "";
            network.unselectAll();
            
            var reset = originalNodes.map(function(n) {{
                return {{ id: n.id, hidden: false }};
            }});
            nodes.update(reset);
        }}

        // Injected LCC node IDs
        {lcc_js_set}
        </script>
        """

        # Append style tag before </head>
        html_content = html_content.replace("</head>", f"{style_inject}\n</head>")

        # Inject panel div right inside body
        html_content = re.sub(r"(<body[^>]*>)", r"\1\n" + panel_html, html_content)

        # Inject JS before </body>
        html_content = html_content.replace("</body>", f"{js_controls}\n</body>")

        # Save to output path
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()

        logger.info(f"Interactive PyVis HTML visualization saved to {output_path}")
        return output_path
