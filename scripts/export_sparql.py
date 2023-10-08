import getpass
import json
from osw.sparql_client_smw import SmwSparqlClient
from pyld import jsonld

from base import prefixes, context, dump, cleanup, zip_data_folder 

client = SmwSparqlClient(
    "https://blazegraph.kiprobatt.de/blazegraph/namespace/kb/sparql",
    domain = "kiprobatt.de",
    auth="basic",
    user='user',
    password=getpass.getpass(),
)

def export_iri(iri: str):
    """Export a single iri.

    Parameters
    ----------
    iri
        the IRI of the process

    """
    
    client.sparql.setQuery(prefixes + """    
    CONSTRUCT {
      ?s ?p ?o.
    }
    WHERE {
      ?s ?p ?o.                 
      VALUES ?s { """ + iri + """ }
    }
    """)
    results = client.sparql.queryAndConvert()
    dump(results, "data/"  + iri.split(":")[1] + ".jsonld")

def export_process(iri: str):
    """Export a process and all its sub-processes, objects and parameters.

    Parameters
    ----------
    iri
        the IRI of the process

    """

    # first query for all process, objects and steps
    # all triples that are connected are returned
    client.sparql.setQuery(prefixes + """    
    CONSTRUCT {
        ?process ?pp ?po.
        ?pobject ?op ?oo.    
        ?pstep ?sp ?so.
    }
    WHERE {
        ?process ?pp ?po.
        ?pobject ?op ?oo.    
        ?pstep ?sp ?so.     
        ?process property:HasObject ?pobject.
        ?pstep property:IsSubprocessOf ?process.
        VALUES ?process { """ + iri + """ }
    }
    """)
    results = client.sparql.queryAndConvert()

    # second query for all process parameters to avoid to large responses
    client.sparql.setQuery(prefixes + """    
    CONSTRUCT {
        ?pparam ?ppp ?ppo. 
    }
    WHERE {
        ?pparam ?ppp ?ppo.       
        ?pparam property:IsProcessParameterOf/property:IsSubprocessOf ?process.
        VALUES ?process { """ + iri + """ }
    }
    """)
    results += client.sparql.queryAndConvert()
    dump(results, "data/"  + iri.split(":")[1] + ".jsonld")


def get_instances(rdf_type: str, restrictions: str = "") -> list[str]:
    """get all instances of a rdf type, e.g. all process instances

    Parameters
    ----------
    rdf_type
        the rdf type
    restrictions
        additional restrictions for the query

    Returns
    -------
        the list of all instance iris

    """
    client.sparql.setQuery(prefixes + """    
    CONSTRUCT {
        ?s ?p ?o. 
    }
    WHERE {
        ?s ?p ?o.
        ?s rdf:type|property:IsInstanceOf """ + rdf_type + """.
        """ + restrictions + """
    }
    """)
    results = client.sparql.queryAndConvert()
    jsonld_dict = json.loads(results.serialize(format="json-ld", auto_compact=True))
    for key, value in context.items():
        jsonld_dict["@context"][key] = value
    jsonld_dict = jsonld.compact(jsonld_dict, jsonld_dict["@context"])
    if "@graph" in jsonld_dict:
        for node in jsonld_dict["@graph"]:
            print(f'"{node["@id"]}" # {node["rdfs:label"]}')
        # return the the @id property of all nodes as list
        return [node["@id"] for node in jsonld_dict["@graph"]]
    elif "@id" in jsonld_dict: 
        print(f'"{jsonld_dict["@id"]}" # {jsonld_dict["rdfs:label"]}')
        return [jsonld_dict["@id"]]
    else: return []

# cleanup the data directory
cleanup()

# query all process types / templates
# get_instances("Category:LabProcess-2FTemplate")

# this will result in the following list
process_types = [
"labprocess:OSLbc089261bd1b470c9ec5e159ce3442c6", # KIproBatt v1 Filling
"labprocess:OSL9a645a64b15442398ad3c057e1b64d87", # KIproBatt v1 Separation
"labprocess:OSL6d6a05be73d64293a34654c6b9b48eb0", # KIproBatt v1 Formation and EoL-Test
"labprocess:OSLd0c734a239844a0d8820856add12aeca", # KIproBatt v1 Stacking
"labprocess:OSLdc7b328d2c0b4348ae5e60e2ee7b9fb8", # KIproBatt v1 Degassing
"labprocess:OSL7ca64bd792e648f181b881525e621ee4", # AI Image Analysis
"labprocess:OSLce4377780d0a40bb883c48d698f0b9de", # KIproBatt v2 Stacking
"labprocess:OSL8d3ddce404964e89b37e6368071a822b", # Electrochemical Feature Extraction
"labprocess:OSLdec1088137c143a5bab6495efe873fdb", # KIproBatt v2 Separation
"labprocess:OSL4c1f7444e389471a8250f53407191735", # KIproBatt v1 Drying
]

# query all instances of a process type
#get_instances("labprocess:OSLdec1088137c143a5bab6495efe873fdb", restrictions="?s property:HasProject kiprobatt:KIproBatt.")

# export a single process instance
#export_process("labobject:OSLa9c51bbca9a843359472ed748fa9ed33")

# export all process instances
for pt in process_types:
    print("exporting " + pt)
    for pi in get_instances(pt, restrictions="?s property:HasProject kiprobatt:KIproBatt."):
        print("exporting " + pi)
        try:
            export_process(pi)
        except Exception as e:
            print("Error: " + str(e))
            pass

# zip the data directory
zip_data_folder()