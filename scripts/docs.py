import getpass
import json
from arrow import get
from osw.sparql_client_smw import SmwSparqlClient
from pyld import jsonld
from base import prefixes, context

client = SmwSparqlClient(
    "https://blazegraph.kiprobatt.de/blazegraph/namespace/kb/sparql",
    domain = "kiprobatt.de",
    auth="basic",
    user='user',
    password=getpass.getpass(),
)

def get_materials() -> None:
    """Get all materials from the knowledge base and print them as markdown table."""

    client.sparql.setQuery(prefixes + """    
    CONSTRUCT {
        ?s ?p ?o. 
    }
    WHERE {
        ?s ?p ?o.
        ?s rdfs:subClassOf+ category:Material.
    }
    """)
    results = client.sparql.queryAndConvert()
    jsonld_dict = json.loads(results.serialize(format="json-ld", auto_compact=True))
    for key, value in context.items():
        jsonld_dict["@context"][key] = value
    jsonld_dict = jsonld.compact(jsonld_dict, jsonld_dict["@context"])

    def handle_node(node):
        if isinstance(node["rdfs:subClassOf"], list):
            subClassOf = node["rdfs:subClassOf"][0]["@id"]
        else: subClassOf = node["rdfs:subClassOf"]["@id"]
        if "@graph" in jsonld_dict:
            for node2 in jsonld_dict["@graph"]:
                if node2["@id"] == subClassOf:
                    subClassOf = node2["rdfs:label"]
        print(f'| {node["@id"]} | {node["rdfs:label"]} | {subClassOf} | [url](https://kiprobatt.de/id/{node["@id"]})')

    if "@graph" in jsonld_dict:
        for node in jsonld_dict["@graph"]:
            handle_node(node)
    elif "@id" in jsonld_dict: 
        handle_node(jsonld_dict)

def get_material_types() -> None:
    """Get all material types from the knowledge base and print them as markdown table."""

    client.sparql.setQuery(prefixes + """    
    CONSTRUCT {
        ?s ?p ?o. 
    }
    WHERE {
        ?s ?p ?o.
        ?s rdf:type/rdfs:subClassOf+ category:Material.
    }
    """)
    results = client.sparql.queryAndConvert()
    jsonld_dict = json.loads(results.serialize(format="json-ld", auto_compact=True))
    for key, value in context.items():
        jsonld_dict["@context"][key] = value
    jsonld_dict = jsonld.compact(jsonld_dict, jsonld_dict["@context"])

    def handle_node(node):
        print(f'| {node["@id"]} | {node["rdfs:label"]} | [url](https://kiprobatt.de/id/{node["@id"]})')

    if "@graph" in jsonld_dict:
        for node in jsonld_dict["@graph"]:
            handle_node(node)
    elif "@id" in jsonld_dict: 
        handle_node(jsonld_dict)

get_materials()
get_material_types()