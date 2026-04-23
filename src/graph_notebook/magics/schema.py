import logging
from graph_notebook.neptune.client import Client, NEPTUNE_DB_SERVICE_NAME, NEPTUNE_ANALYTICS_SERVICE_NAME
from graph_notebook.configuration.generate_config import Configuration
from graph_notebook.schema_model import Property, Node, Relationship, RelationshipPattern, GraphSchema
from typing import Dict, List, Tuple

logger = logging.getLogger("graph_magic")


def _get_labels(summary) -> Tuple[List[str], List[str]]:
    """Get node and edge labels from the Neptune statistics summary.

    Returns:
        Tuple[List[str], List[str]]: A tuple containing two lists:
            1. List of node labels
            2. List of edge labels
    """
    n_labels = summary['nodeLabels']
    e_labels = summary['edgeLabels']
    return n_labels, e_labels

def _get_triples(client: Client, e_labels: List[str]) -> List[RelationshipPattern]:
    triple_query = """
    MATCH (a)-[e:`{e_label}`]->(b)
    WITH a,e,b LIMIT 3000
    RETURN DISTINCT labels(a) AS from, type(e) AS edge, labels(b) AS to
    LIMIT 10
    """

    triple_schema = []
    for label in e_labels:
        logger.debug(f'Running get triples for {label}')
        q = triple_query.format(e_label=label)
        data = client.opencypher_http(q).json()

        for d in data['results']:
            left = ":".join(sorted(d["from"]))
            right = ":".join(sorted(d["to"]))
            triple = RelationshipPattern(left, right, d["edge"])
            triple_schema.append(triple)

    return triple_schema

def _get_node_properties(client: Client,
    n_labels: List[str], types: Dict[str, str]
) -> List:
    node_properties_query = """
    MATCH (a:`{n_label}`)
    RETURN properties(a) AS props
    LIMIT 100
    """
    nodes = []
    for label in n_labels:
        logger.debug(f'Running get node properties for {label}')
        q = node_properties_query.format(n_label=label)
        data = client.opencypher_http(q).json()['results']
        props = {}
        for p in data:
            for k, v in p['props'].items():
                prop_type = types[type(v).__name__]
                if k not in props:
                    props[k] = {prop_type}
                else:
                    props[k].add(prop_type)

        properties = [Property(name=k, type=list(v)) for k, v in props.items()]
        nodes.append(Node(labels=label, properties=properties))

    return nodes

def _get_edge_properties(client: Client,
    e_labels: List[str], types: Dict[str, str]
) -> List:
    edge_properties_query = """
    MATCH ()-[e:`{e_label}`]->()
    RETURN properties(e) AS props
    LIMIT 100
    """
    edges = []
    for label in e_labels:
        logger.debug(f'Running get edge properties for {label}')
        q = edge_properties_query.format(e_label=label)
        data = client.opencypher_http(q).json()['results']
        props = {}
        for p in data:
            for k, v in p['props'].items():
                prop_type = types[type(v).__name__]
                if k not in props:
                    props[k] = {prop_type}
                else:
                    props[k].add(prop_type)

        properties = [Property(name=k, type=list(v)) for k, v in props.items()]
        edges.append(Relationship(type=label, properties=properties))

    return edges

SPARQL_TYPE_MAP = {
    'http://www.w3.org/2001/XMLSchema#integer': 'INTEGER',
    'http://www.w3.org/2001/XMLSchema#int': 'INTEGER',
    'http://www.w3.org/2001/XMLSchema#long': 'INTEGER',
    'http://www.w3.org/2001/XMLSchema#short': 'INTEGER',
    'http://www.w3.org/2001/XMLSchema#byte': 'INTEGER',
    'http://www.w3.org/2001/XMLSchema#decimal': 'DOUBLE',
    'http://www.w3.org/2001/XMLSchema#float': 'DOUBLE',
    'http://www.w3.org/2001/XMLSchema#double': 'DOUBLE',
    'http://www.w3.org/2001/XMLSchema#date': 'DATE',
    'http://www.w3.org/2001/XMLSchema#dateTime': 'DATE',
    'http://www.w3.org/2001/XMLSchema#boolean': 'BOOLEAN',
    'http://www.w3.org/2001/XMLSchema#string': 'STRING',
}

METADATA_CLASS_PREFIXES = [
    'http://www.w3.org/2000/01/rdf-schema',
    'http://www.w3.org/2002/07/owl',
]

RDF_TYPE_URI = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'


def _uri_local_name(uri: str) -> str:
    """Extract the local name from a URI (after last # or /)."""
    for sep in ('#', '/'):
        idx = uri.rfind(sep)
        if idx != -1:
            return uri[idx + 1:]
    return uri


def _is_metadata_uri(uri: str) -> bool:
    return any(uri.startswith(p) for p in METADATA_CLASS_PREFIXES)


def _sparql_get_classes(client: Client) -> List[str]:
    """Discover RDF classes via SPARQL. From graph-explorer classesWithCountsTemplates.ts"""
    query = """
    SELECT ?class (COUNT(?s) AS ?count)
    WHERE { ?s a ?class }
    GROUP BY ?class
    """
    bindings = client.sparql(query).json()['results']['bindings']
    return [b['class']['value'] for b in bindings if not _is_metadata_uri(b['class']['value'])]


def _sparql_get_predicates_by_class(client: Client, class_uri: str) -> List[Property]:
    """Sample one instance and return literal predicates with types.
    From graph-explorer predicatesByClassTemplate.ts"""
    query = f"""
    SELECT ?pred (SAMPLE(?object) AS ?sample)
    WHERE {{
        {{ SELECT ?subject WHERE {{ ?subject a <{class_uri}>. }} LIMIT 1 }}
        ?subject ?pred ?object.
        FILTER(!isBlank(?object) && isLiteral(?object))
    }}
    GROUP BY ?pred
    """
    bindings = client.sparql(query).json()['results']['bindings']
    return [
        Property(
            name=_uri_local_name(b['pred']['value']),
            type=[SPARQL_TYPE_MAP.get(b.get('sample', {}).get('datatype', ''), 'STRING')]
        )
        for b in bindings
    ]


def _sparql_get_predicates_with_counts(client: Client) -> List[str]:
    """Fetch all predicates to non-literals (relationships).
    From graph-explorer predicatesWithCountsTemplate.ts"""
    query = """
    SELECT ?predicate (COUNT(?predicate) AS ?count)
    WHERE {
        [] ?predicate ?object
        FILTER(!isLiteral(?object))
    }
    GROUP BY ?predicate
    """
    bindings = client.sparql(query).json()['results']['bindings']
    return [
        b['predicate']['value'] for b in bindings
        if b['predicate']['value'] != RDF_TYPE_URI and not _is_metadata_uri(b['predicate']['value'])
    ]


def _sparql_get_relationship_patterns(client: Client, pred_uri: str) -> List[RelationshipPattern]:
    """For a predicate, discover which class pairs it connects."""
    query = f"""
    SELECT DISTINCT ?fromClass ?toClass
    WHERE {{
        ?s a ?fromClass .
        ?s <{pred_uri}> ?o .
        ?o a ?toClass .
    }}
    LIMIT 50
    """
    bindings = client.sparql(query).json()['results']['bindings']
    return [
        RelationshipPattern(
            left_node=_uri_local_name(b['fromClass']['value']),
            right_node=_uri_local_name(b['toClass']['value']),
            relation=_uri_local_name(pred_uri),
        )
        for b in bindings
    ]


def _get_rdf_schema(client: Client, config: Configuration) -> GraphSchema:
    """Build a GraphSchema from an RDF/SPARQL endpoint."""
    logger.info("Finding Schema for RDF/SPARQL endpoint")

    class_uris = None
    pred_uris = None

    # Use Neptune summary API if available
    if config.neptune_service == NEPTUNE_DB_SERVICE_NAME:
        try:
            summary = client.statistics('sparql', True, 'basic', False).json()['payload']['graphSummary']
            logger.info("Using Neptune RDF summary for class/predicate discovery")
            class_uris = [c for c in summary.get('classes', []) if not _is_metadata_uri(c)]
            pred_uris = [
                uri for pred_map in summary.get('predicates', [])
                for uri in pred_map
                if uri != RDF_TYPE_URI and not _is_metadata_uri(uri)
            ]
        except Exception as e:
            logger.warning(f"Neptune RDF summary unavailable, falling back to SPARQL discovery: {e}")

    # Fall back to SPARQL queries
    if class_uris is None:
        class_uris = _sparql_get_classes(client)
    if pred_uris is None:
        pred_uris = _sparql_get_predicates_with_counts(client)

    # Get properties per class
    nodes = []
    for class_uri in class_uris:
        logger.info(f"Fetching predicates for class {class_uri}")
        props = _sparql_get_predicates_by_class(client, class_uri)
        nodes.append(Node(labels=_uri_local_name(class_uri), properties=props))

    # Get relationships and patterns
    relationships = []
    relationship_patterns = []
    for uri in pred_uris:
        relationships.append(Relationship(type=_uri_local_name(uri), properties=[]))
        logger.info(f"Fetching relationship patterns for {uri}")
        relationship_patterns.extend(_sparql_get_relationship_patterns(client, uri))

    return GraphSchema(nodes=nodes, relationships=relationships, relationship_patterns=relationship_patterns)


def get_schema(client: Client, config: Configuration, language: str = 'propertygraph') -> GraphSchema:
    if language in ('sparql', 'rdf'):
        return _get_rdf_schema(client, config)

    if config.neptune_service == NEPTUNE_DB_SERVICE_NAME:
        logger.info("Finding Schema for Neptune Database")
        summary = client.statistics('propertygraph', True, 'basic', False)
        logger.info("Summary retrieved")
        logger.debug(summary.json()['payload']['graphSummary'])
        summary=summary.json()['payload']['graphSummary']
        types = {
            'str': 'STRING',
            'float': 'DOUBLE',
            'int': 'INTEGER',
            'list': 'LIST',
            'dict': 'MAP',
            'bool': 'BOOLEAN',
        }
        n_labels, e_labels = _get_labels(summary)
        logger.info("Getting Triples")
        triple_schema = _get_triples(client, e_labels)
        logger.debug(triple_schema)
        logger.info("Node Properties retrieved")
        nodes = _get_node_properties(client, n_labels, types)
        logger.debug(nodes)
        logger.info("Edge Properties retrieved")
        rels = _get_edge_properties(client, e_labels, types)
        logger.debug(rels)
        graph = GraphSchema(nodes=nodes, relationships=rels, relationship_patterns=triple_schema)
        return graph
    elif config.neptune_service == NEPTUNE_ANALYTICS_SERVICE_NAME:
        logger.info("Finding Schema for Neptune Analytics")
        res = client.opencypher_http("CALL neptune.graph.pg_schema()")
        raw_schema = res.json()['results'][0]['schema']
        graph = GraphSchema(nodes=[], relationships=[], relationship_patterns=[])
        for i in raw_schema['labelTriples']:
            graph.relationship_patterns.append(
                RelationshipPattern(left_node=i['~from'], relation=i['~type'], right_node=i['~to'])
            )

        # Process node labels and properties
        for l in raw_schema['nodeLabels']:
            details = raw_schema['nodeLabelDetails'][l]
            props = []
            for p in details['properties']:
                props.append(Property(name=p, type=details['properties'][p]['datatypes']))
            graph.nodes.append(Node(labels=l, properties=props))

        # Process edge labels and properties
        for l in raw_schema['edgeLabels']:
            details = raw_schema['edgeLabelDetails'][l]
            props = []
            for p in details['properties']:
                props.append(Property(name=p, type=details['properties'][p]['datatypes']))
            graph.relationships.append(Relationship(type=l, properties=props))
        return graph
    else:
        raise NotImplementedError