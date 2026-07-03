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

net.show("graph.html")

print("graph.html created.")