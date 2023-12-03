import json
from typing import Callable, Dict
from pyld import jsonld
import rdflib
import zipfile
import os

domain = "kiprobatt.de"

# mappings used both for the SPARQL prefixes and the JSON-LD context
mappings = {
"swivt": "http://semantic-mediawiki.org/swivt/1.0#",
"kiprobatt": f"https://{domain}/id/",
"Property": f"https://{domain}/id/Property-3A",
"Category": f"https://{domain}/id/Category-3A",
"LabProcess": f"https://{domain}/id/LabProcess-3A",
"LabObject": f"https://{domain}/id/LabObject-3A",
"Material": f"https://{domain}/id/Material-3A",
"Device": f"https://{domain}/id/Device-3A",
"Term": f"https://{domain}/id/Term-3A",
"File": f"https://{domain}/id/File-3A",
}

# build SPARQL prefixes and JSON-LD context
prefixes = ""
context = {}
for key, value in mappings.items():
    prefixes += f"PREFIX {key}: <{value}>\n"
    context[key] = {"@id": value, "@prefix": True}

# from https://github.com/SemanticMediaWiki/SemanticMediaWiki/blob/e04b78ddbc0a1b2181b12f31a51d7f91e723336b/src/Exporter/Escaper.php#L61
smw_encoding_lists = {
            "in": [
                "*",
                ",",

                ";",
                "<",
                ">",
                "(",
                ")",
                "[",
                "]",
                "{",
                "}",
                "\\",
                "$",
                "^",
                ":",
                '"',
                "#",
                "&",
                "'",
                "+",
                "!",
                #"%",
                "-", # added
            ],
            "out": [
                "-2A",
                "-2C",
                "-3B",
                "-3C",
                "-3E",
                "-28",
                "-29",
                "-5B",
                "-5D",
                "-7B",
                "-7D",
                "-5C",
                "-24",
                "-5E",
                "-3A",
                "-22",
                "-23",
                "-26",
                "-27",
                "-2B",
                "-21",
                #"-",
                "-2D", # added
            ],
}
encoding_dict = dict(
zip(smw_encoding_lists["in"], smw_encoding_lists["out"])
)

def smw_encode(str):
    """Encode a string according to SMW's encoding rules

    Parameters
    ----------
    str
        the string to encode

    Returns
    -------
        the encoded string
    """
    for key, value in encoding_dict.items():
        str = str.replace(key, value)
    return str

def smw_decode(str):
    """Decode a string according to SMW's encoding rules

    Parameters
    ----------
    str
        the string to decode

    Returns
    -------
        the decoded string
    """
    for key, value in encoding_dict.items():
        str = str.replace(value, key)
    return str

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
        "Property:HasCreator",
        "Property:HasAgent",
        "Property:Display_title_of",
        "rdfs:label",
        "swivt:wikiPageSortKey",
        "swivt:wikiNamespace",
        "swivt:masterPage",
        "swivt:wikiPageContentLanguage",
        "Property:HasId",
        "Property:Has_query",
        "Property:Has_subobject",
        "Property:Debug",
        "Property:Has_parent_page",
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

def order_dict(d: dict) -> dict:
    """sorts dicts by keys and lists by value 
    (if lists contains dicts, they are sorted by @id or the first key)
    """
    def key(x):
        if isinstance(x, dict):
            if "@id" in x: 
                return x["@id"]
            else:
                first_key = next(iter(dict))
                if first_key in x: return x[first_key]
                else: return None
        else: return x
    def order_dict_recursiv(v):
        if isinstance(v, dict):
            for k in v:
                v[k] = order_dict_recursiv(v[k])
            v = dict(sorted(v.items()))
        elif isinstance(v, list):
            for i in v:
                i = order_dict_recursiv(i)
            v = sorted(v, key=key)
        return v

    return order_dict_recursiv(d)

def replace_values(d: dict, target_key: str, callback: Callable) -> None:
    """replace values in a dict recursivly
    """
    def replace_values_recursiv(v, parent_key):
        if isinstance(v, dict):
            for k in v:
                k_param = k
                if k_param == "@id": k_param = parent_key
                v[k] = replace_values_recursiv(v[k], k_param)
        elif isinstance(v, list):
            _v = []
            for i in v:
                _v.append(replace_values_recursiv(i, parent_key))
            v = _v
        elif (parent_key == target_key):
            _v = callback(v)
            if (v != _v): print(f"Replace {v} with {_v}")
            v = callback(v)
        return v

    return replace_values_recursiv(d, None)

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
        jsonld_dict["@context"]["File"] = {"@id": f"https://{domain}/wiki/Special:Redirect/file/", "@prefix": True}
        replace_values(jsonld_dict, "Property:HasFile", lambda x: smw_decode(x))
        jsonld_dict = order_dict(jsonld_dict)
        f.write(json.dumps(jsonld_dict, ensure_ascii=False, indent=4, sort_keys=True))

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