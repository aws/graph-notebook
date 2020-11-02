"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.network.Network import Network, network_to_json, network_from_json, ERROR_EDGE_NOT_FOUND, \
    ERROR_INVALID_DATA


def get_seed_network() -> Network:
    network = Network()
    node_1_data = {'foo': 'bar'}
    node_2_data = {'foo': 'baz'}
    network.add_node_data('1', node_1_data)
    network.add_node_data('2', node_2_data)

    network.add_edge('1', '2', '1_to_2', 'lorem')
    network.add_edge('2', '1', '2_to_1', 'ipsum')
    return network


class TestNetwork(unittest.TestCase):
    def test_add_node(self):
        network = Network()
        node_id = '1'
        network.add_node(node_id)
        self.assertTrue(network.graph.has_node(node_id))

    def test_add_node_with_properties(self):
        network = Network()
        node_id = '1'
        kwargs = {
            'foo': 'bar'
        }
        network.add_node(node_id, kwargs)
        self.assertEqual('bar', network.graph.nodes[node_id]['foo'])

    def test_add_edge_data_does_not_exist(self):
        network = Network()
        network.add_node('1')
        network.add_node('2')
        with self.assertRaises(ValueError) as context:
            network.add_edge_data('1', '2', 'na', {'foo': 'bar'})

        self.assertEqual(context.exception, ERROR_EDGE_NOT_FOUND)

    def test_add_edge_data_not_a_dict(self):
        network = Network()
        network.add_node('1')
        network.add_node('2')
        network.add_edge('1', '2', '1_to_2', '1_to_2')

        with self.assertRaises(ValueError) as context:
            network.add_edge_data('1', '2', '1_to_2', None)

        self.assertEqual(context.exception, ERROR_INVALID_DATA)

    def test_add_no_data_not_a_dict(self):
        network = Network()
        with self.assertRaises(ValueError) as context:
            network.add_node_data('1', None)

        self.assertEqual(context.exception, ERROR_INVALID_DATA)

    def test_network_to_json(self):
        network = get_seed_network()

        expected_nodes = [
            {'foo': 'bar', 'id': '1'},
            {'foo': 'baz', 'id': '2'}
        ]

        expected_edges = [
            {'label': 'lorem', 'source': '1', 'target': '2', 'key': '1_to_2'},
            {'label': 'ipsum', 'source': '2', 'target': '1', 'key': '2_to_1'}
        ]

        js = network.to_json()
        self.assertEqual(expected_nodes, js['graph']['nodes'])
        self.assertEqual(expected_edges, js['graph']['links'])

    def test_network_from_json(self):
        network = get_seed_network()
        js = network_to_json(network)
        loaded_network = network_from_json(js)
        self.assertEqual(network.to_json(), loaded_network.to_json())


if __name__ == '__main__':
    unittest.main()
