"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json

from networkx import MultiDiGraph
from networkx.readwrite import json_graph

ERROR_EDGE_NOT_FOUND = ValueError("Edge was not found on network graph")
ERROR_INVALID_DATA = ValueError("Data must be a dict")


class Network:
    """
    Network wraps a Networkx MultiDiGraph and provides some utilities
    to add nodes and edges to the graph. For use each language meant to use it,
    the Network class will be extended to ensure that we are adding the data needed to ensure that
    we maintain the properties inside each node and edge appropriately.
    """

    def __init__(self, graph: MultiDiGraph = None):
        if graph is None:
            graph = MultiDiGraph()
        self.graph = graph

    def add_node_property(self, node_id: str, key: str, value: str):
        """
        updates the "properties" key on the given :param node_id. For instance, if key=foo, and value=bar,
        then the given node would now be guaranteed to have the entry node['properties']['foo'] = bar
        :param node_id: id of the node to update
        :param key: the key to update under this nodes' properties dict
        :param value: the value to set
        """
        node = self.graph.nodes.get(node_id)
        if node is None:
            node = self.graph.add_node(node_id)

        if 'properties' not in node:
            node['properties'] = {key: value}
        else:
            node['properties'][key] = value

    def add_node(self, node_id: str, data=None):
        if data is None:
            data = {}
        self.graph.add_node(node_id, **data)

    def add_edge(self, from_id: str, to_id: str, edge_id: str, label: str, data: dict = None):
        if data is None:
            data = {}

        data['label'] = label
        self.graph.add_edge(from_id, to_id, edge_id, **data)

    def add_node_data(self, node_id: str, data: dict):
        """
        overrides the keys on a node with the data found in :param data
        :param node_id: the id of the node to update
        :param data: key-value dictionary to update node with
        """

        if type(data) is not dict:
            raise ERROR_INVALID_DATA

        node = self.graph.nodes.get(node_id)
        if node is None:
            self.add_node(node_id, data)
            return

        for key in data:
            node[key] = data[key]

    def add_edge_data(self, from_id: str, to_id: str, edge_id, data: dict):
        if not self.graph.has_edge(from_id, to_id, edge_id):
            raise ERROR_EDGE_NOT_FOUND

        if type(data) is not dict:
            raise ERROR_INVALID_DATA

        edge = self.graph.edges[from_id, to_id, edge_id]
        for key in data:
            edge[key] = data[key]

    def add_results(self, results):
        """
        base method to be overridden by implementations to add results.
        For SPARQL, these results are a dict with bindings, for Gremlin, they are paths
        :param results:
        :return:
        """
        pass

    def to_json(self) -> dict:
        return {
            'graph': json_graph.node_link_data(self.graph)
        }


def network_to_json(network: Network) -> str:
    return json.dumps(network.to_json())


def network_from_json(raw) -> Network:
    data = json.loads(raw)
    network = Network()
    if 'graph' in data:
        network.graph = json_graph.node_link_graph(data['graph'], directed=True)
    return network
