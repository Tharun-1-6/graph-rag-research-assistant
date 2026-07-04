# pyrefly: ignore [missing-import]
from pyvis.network import Network

from graph.graph_builder.serializer import GraphSerializer


graph = GraphSerializer("data/graphs").load_graphml(
    "attention.graphml"
)

net = Network(
    height="900px",
    width="100%",
    bgcolor="#111111",
    font_color="white",
    directed=True,
    notebook=False,
)

net.barnes_hut()

for node, data in graph.nodes(data=True):

    label = data.get("name", node)

    node_type = data.get("type", "")

    net.add_node(
        node,
        label=label,
        title=node_type,
        group=node_type,
    )


for source, target, data in graph.edges(data=True):

    relation = data.get("relationship", "")

    net.add_edge(
        source,
        target,
        title=relation,
        label=relation,
    )

net.write_html("tests/graph.html")

print("tests/graph.html created.")