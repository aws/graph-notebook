"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from gremlin_python.structure.graph import Path

from graph_notebook.network.gremlin.GremlinNetwork import GremlinNetwork


class TestAddResults(unittest.TestCase):
    def test_add_primitive_path(self):
        a = 'a'
        edge = 'a_to_b'
        b = 'b'

        p = Path([], [a, edge, b])
        paths = [p]

        gn = GremlinNetwork()
        gn.add_results(paths)

        self.assertTrue(gn.graph.has_node(a))
        self.assertTrue(gn.graph.has_node(b))
        self.assertTrue(gn.graph.has_node(edge))  # note, this is not of type Edge so we assume it is a node
        self.assertEqual(2, len(gn.graph.edges))

    def test_add_dicts_without_ids(self):
        dict_1 = {'foo': 'value', 'bar': 'something'}
        dict_2 = {'foo': 'other_value'}
        p = Path([], [dict_1, dict_2])
        gn = GremlinNetwork()
        gn.add_results([p])
        self.assertEqual(len(p), len(gn.graph.nodes))
