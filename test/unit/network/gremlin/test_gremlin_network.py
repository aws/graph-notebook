"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.network.EventfulNetwork import EVENT_ADD_NODE
from graph_notebook.network.gremlin.GremlinNetwork import GremlinNetwork
from gremlin_python.structure.graph import Path


class TestGremlinNetwork(unittest.TestCase):
    def test_add_vertex_with_callback(self):
        vertex = {
            'T.id': '1234',
            'T.label': 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        reached_callback = {}
        expected_data = {
            'data': {
                'label': 'airport',
                'properties': {
                    'T.id': '1234',
                    'T.label': 'airport',
                    'code': 'SEA',
                    'runways': '4',
                    'type': 'Airport'},
                'title': 'airport'},
            'node_id': '1234'}

        def add_node_callback(network, event_name, data):
            self.assertEqual(event_name, EVENT_ADD_NODE)
            self.assertEqual(expected_data, data)
            reached_callback[event_name] = True

        gn = GremlinNetwork(callbacks={EVENT_ADD_NODE: [add_node_callback]})
        gn.add_vertex(vertex)
        self.assertTrue(reached_callback[EVENT_ADD_NODE])
        node = gn.graph.nodes.get(vertex['T.id'])
        self.assertEqual(expected_data['data']['properties'], node['properties'])

    def test_add_path_with_integer(self):
        path = Path([], ['ANC', 3030, 'DFW'])
        gn = GremlinNetwork()
        gn.add_results([path])
        self.assertEqual(len(path), len(gn.graph.nodes))


if __name__ == '__main__':
    unittest.main()
