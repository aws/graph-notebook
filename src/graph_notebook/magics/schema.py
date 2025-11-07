import logging
from graph_notebook.neptune.client import Client, NEPTUNE_DB_SERVICE_NAME, NEPTUNE_ANALYTICS_SERVICE_NAME
from graph_notebook.configuration.generate_config import Configuration
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("graph_magic")

@dataclass
class Property:
    """Represents a property definition for nodes and relationships in the graph.

    Properties are key-value pairs that can be attached to both nodes and
    relationships, storing additional metadata about these graph elements.

    Attributes:
        name (str): The name/key of the property
        type (str): The data type of the property value
    """

    name: str
    type: List[str]


@dataclass
class Node:
    """Defines a node type in the graph schema.

    Nodes represent entities in the graph database and can have labels
    and properties that describe their characteristics.

    Attributes:
        labels (str): The label(s) that categorize this node type
        properties (List[Property]): List of properties that can be assigned to this node type
    """

    labels: str
    properties: List[Property] = field(default_factory=list)


@dataclass
class Relationship:
    """Defines a relationship type in the graph schema.

    Relationships represent connections between nodes in the graph and can
    have their own properties to describe the nature of the connection.

    Attributes:
        type (str): The type/category of the relationship
        properties (List[Property]): List of properties that can be assigned to this relationship type
    """

    type: str
    properties: List[Property] = field(default_factory=list)


@dataclass
class RelationshipPattern:
    """Defines a valid relationship pattern between nodes in the graph.

    Relationship patterns describe the allowed connections between different
    types of nodes in the graph schema.

    Attributes:
        left_node (str): The label of the source/starting node
        right_node (str): The label of the target/ending node
        relation (str): The type of relationship connecting the nodes
    """

    left_node: str
    right_node: str
    relation: str


@dataclass
class GraphSchema:
    """Represents the complete schema definition for the graph database.

    The graph schema defines all possible node types, relationship types,
    and valid patterns of connections between nodes.

    Attributes:
        nodes (List[Node]): List of all node types defined in the schema
        relationships (List[Relationship]): List of all relationship types defined in the schema
        relationship_patterns (List[RelationshipPattern]): List of valid relationship patterns
    """

    nodes: List[Node]
    relationships: List[Relationship]
    relationship_patterns: List[RelationshipPattern]


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

def _get_triples(client:Client, e_labels: List[str]) -> List[RelationshipPattern]:
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
                triple = RelationshipPattern(d["from"][0], d["to"][0], d["edge"])
                triple_schema.append(triple)

        return triple_schema

def _get_node_properties(client:Client,
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
        data = {"label": label, "properties": client.opencypher_http(q).json()['results']}
        s = set({})
        for p in data["properties"]:            
            props = {}

            for k, v in p['props'].items():
                prop_type = types[type(v).__name__]
                if k not in props:
                    props[k] = {prop_type}
                else:
                    props[k].update([prop_type])

            properties = []
            for k, v in props.items():
                properties.append(Property(name=k, type=list(v)))

        np = {
            "properties": [{"property": k, "type": v} for k, v in s],
            "labels": label,
        }
        nodes.append(Node(labels=label, properties=properties))

    return nodes

def _get_edge_properties(client:Client, 
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
        data = {"label": label, "properties": client.opencypher_http(q).json()['results']}
        s = set({})
        for p in data["properties"]:
            from typing import cast

            p_dict = cast(Dict[str, Any], p)
            props = cast(Dict[str, Any], p_dict["props"])

            props = {}
            for k, v in p['props'].items():
                prop_type = types[type(v).__name__]
                if k not in props:
                    props[k] = {prop_type}
                else:
                    props[k].update([prop_type])
            properties = []
            for k, v in props.items():
                properties.append(Property(name=k, type=list(v)))

        edges.append(Relationship(type=label, properties=properties))

    return edges

def get_schema(client:Client, config:Configuration) -> GraphSchema:
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