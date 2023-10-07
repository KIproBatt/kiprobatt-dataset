import os
import rdflib
from base import prefixes, dump, mappings

# interate over directory and import all jsonld files into a rdflib graph
def import_jsonld() -> rdflib.Graph:
    graph = rdflib.Graph()

    for filename in os.listdir("data"):
        if filename.endswith(".jsonld"):
            with open("data/" + filename) as f:
                graph.parse(data=f.read(), format="json-ld")
    for key, value in mappings.items():
        graph.namespace_manager.bind(key, rdflib.Namespace(value))
    return graph

# print graph statistics
def print_graph_stats(graph):
    print(f"statements/triples | {len(graph)}")
    print(f"subjects | {len(set(graph.subjects()))}")
    print(f"predicates | {len(set(graph.predicates()))}")
    print(f"objects | {len(set(graph.objects()))}")

graph = import_jsonld()
print_graph_stats(graph)

# optional: dump the full graph to a file
#dump(graph, 'full.jsonld')

# example usecase: query for all instances of a finished battery cell
q = prefixes + """SELECT ?s
WHERE {
    ?s Property:IsInstanceOf Material:OSLd14c860458ea4b9aaf93a4bf64838ac7.
}
LIMIT 10
"""

res = graph.query(q)
for row in res:
    print(f"{row.s}")