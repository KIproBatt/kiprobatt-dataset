import json
from typing import Dict
from pyld import jsonld
import rdflib
import zipfile
import os

domain = "kiprobatt.de"

# mappings used both for the SPARQL prefixes and the JSON-LD context
mappings = {
"swivt": "http://semantic-mediawiki.org/swivt/1.0#",
"kiprobatt": f"https://{domain}/id/",
"property": f"https://{domain}/id/Property-3A",
"category": f"https://{domain}/id/Category-3A",
"labprocess": f"https://{domain}/id/LabProcess-3A",
"labobject": f"https://{domain}/id/LabObject-3A",
"material": f"https://{domain}/id/Material-3A",
"device": f"https://{domain}/id/Device-3A",
"term": f"https://{domain}/id/Term-3A",
"file": f"https://{domain}/id/File-3A",
}

# build SPARQL prefixes and JSON-LD context
prefixes = ""
context = {}
for key, value in mappings.items():
    prefixes += f"PREFIX {key}: <{value}>\n"
    context[key] = {"@id": value, "@prefix": True}

def filter_internal_properties(jsonld_dict: Dict):
    """remove internal properties from the graph

    Parameters
    ----------
    jsonld_dict
        the graph / node as python dict

    Returns
    -------
        the modified dict
    """
    properties = [
        "property:HasCreator",
        "property:HasAgent",
        "property:Display_title_of",
        "rdfs:label",
        "swivt:wikiPageSortKey",
        "swivt:wikiNamespace",
        "swivt:masterPage",
        "swivt:wikiPageContentLanguage",
        "property:HasId",
        "property:Has_query",
        "property:Has_subobject",
        "property:Debug",
        "property:Has_parent_page",
    ]
    def apply(node):
        for p in properties:
            if p in node:
                del node[p]
    if "@graph" in jsonld_dict:
        for node in jsonld_dict["@graph"]:
            apply(node)
    else: apply(jsonld_dict)
    return jsonld_dict

def dump(graph: rdflib.Graph, filepath: str):
    """Dump a rdflib graph to a jsonld file within the data directory

    Parameters
    ----------
    graph
        the rdflib graph
    filepath
        the path to the file
    """
    with open(filepath, "w") as f:
        jsonld_dict = json.loads(graph.serialize(format="json-ld", auto_compact=True))
        jsonld_dict["@context"]["@version"] =  1.1 # make sure the context is 1.1 to use @prefix
        for key, value in context.items():
            jsonld_dict["@context"][key] = value
        jsonld_dict = jsonld.compact(jsonld_dict, jsonld_dict["@context"])
        jsonld_dict = filter_internal_properties(jsonld_dict)
        f.write(json.dumps(jsonld_dict, ensure_ascii=False, indent=4))

def cleanup():
    """purge the data directory"""
    for filename in os.listdir("data"):
        os.remove("data/" + filename)
    if os.path.exists("data.zip"):
        os.remove("data.zip")
    if os.path.exists("full.jsonld"):
        os.remove("full.jsonld")

def zip_data_folder():
    """compress the data folder to a zip file"""

    zipf = zipfile.ZipFile('data.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('data/'):
        for file in files:
            zipf.write(os.path.join(root, file))
    zipf.close()