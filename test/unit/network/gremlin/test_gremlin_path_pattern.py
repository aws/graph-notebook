"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from gremlin_python.structure.graph import Path

from graph_notebook.network.gremlin.GremlinNetwork import GremlinNetwork, PathPattern


class TestAddResultsPathPattern(unittest.TestCase):
    def test_add_all_V_pattern(self):
        pattern = [PathPattern.V, PathPattern.V, PathPattern.V]
        path = Path([], ['SEA', 'DFW', 'AUS'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)
        self.assertEqual(3, len(gn.graph.nodes))
        self.assertEqual(2, len(gn.graph.edges))

    def test_add_v_and_inV_pattern(self):
        pattern = [PathPattern.V, PathPattern.IN_V, PathPattern.V]
        path = Path([], ['SEA', 'DFW', 'AUS'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)
        for tup in gn.graph.edges:
            self.assertEqual(tup[1], 'DFW')  # assert that DFW is the incoming vertex for both edges.
        self.assertEqual(3, len(gn.graph.nodes))
        self.assertEqual(2, len(gn.graph.edges))

    def test_add_v_and_outV_pattern(self):
        pattern = [PathPattern.V, PathPattern.OUT_V, PathPattern.V]
        path = Path([], ['SEA', 'DFW', 'AUS'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)
        for tup in gn.graph.edges:
            self.assertEqual(tup[0], 'DFW')  # assert that DFW is the incoming vertex for both edges.
        self.assertEqual(3, len(gn.graph.nodes))
        self.assertEqual(2, len(gn.graph.edges))

    def test_add_v_outV_inV_pattern(self):
        pattern = [PathPattern.V, PathPattern.OUT_V, PathPattern.IN_V]
        path = Path([], ['SEA', 'DFW', 'AUS'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)
        self.assertEqual(3, len(gn.graph.nodes))
        self.assertEqual(2, len(gn.graph.edges))

        edges = gn.graph.out_edges('DFW')
        self.assertEqual(2, len(edges))

    def test_add_v_inV_outV_pattern(self):
        pattern = [PathPattern.V, PathPattern.IN_V, PathPattern.OUT_V]
        path = Path([], ['SEA', 'DFW', 'AUS'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)
        self.assertEqual(3, len(gn.graph.nodes))
        self.assertEqual(2, len(gn.graph.edges))

        edges = gn.graph.in_edges('DFW')
        self.assertEqual(2, len(edges))

    def test_add_v_inV_outV_longer_path(self):
        pattern = [PathPattern.V, PathPattern.IN_V, PathPattern.OUT_V]
        path = Path([], ['SEA', 'DFW', 'AUS', 'LAX', 'JFK'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)
        self.assertEqual(5, len(gn.graph.nodes))
        self.assertEqual(4, len(gn.graph.edges))

        dfw_edges = gn.graph.in_edges('DFW')
        self.assertEqual(2, len(dfw_edges))

        lax_edges = gn.graph.in_edges('LAX')
        self.assertEqual(1, len(lax_edges))

        jfk_edges = gn.graph.in_edges('JFK')
        self.assertEqual(1, len(jfk_edges))

    def test_add_v_e_v_path(self):
        pattern = [PathPattern.V, PathPattern.E, PathPattern.V]
        path = Path([], ['SEA', 'route', 'DFW'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)

        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
        self.assertIsNotNone(gn.graph.edges[('SEA', 'DFW', 'route')])

    def test_add_v_inE_v_path(self):
        pattern = [PathPattern.V, PathPattern.E, PathPattern.V]
        path = Path([], ['SEA', 'route', 'DFW'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)

        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
        self.assertIsNotNone(gn.graph.edges[('SEA', 'DFW', 'route')])

    def test_add_v_outE_path(self):
        pattern = [PathPattern.V, PathPattern.OUT_E, PathPattern.V]
        path = Path([], ['SEA', 'route', 'DFW'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)

        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
        self.assertIsNotNone(gn.graph.edges[('SEA', 'DFW', 'route')])

    def test_add_v_inE_path(self):
        pattern = [PathPattern.V, PathPattern.IN_E, PathPattern.V]
        path = Path([], ['SEA', 'route', 'DFW'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)

        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
        self.assertIsNotNone(gn.graph.edges[('DFW', 'SEA', 'route')])

    def test_add_inV_E_V_path(self):
        pattern = [PathPattern.IN_V, PathPattern.E, PathPattern.V]
        path = Path([], ['SEA', 'route', 'DFW'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)

        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
        self.assertIsNotNone(gn.graph.edges[('DFW', 'SEA', 'route')])

    def test_add_outV_E_V_path(self):
        pattern = [PathPattern.OUT_V, PathPattern.E, PathPattern.V]
        path = Path([], ['SEA', 'route', 'DFW'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)

        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
        self.assertIsNotNone(gn.graph.edges[('SEA', 'DFW', 'route')])

    def test_add_outV_E_inV_path(self):
        pattern = [PathPattern.OUT_V, PathPattern.E, PathPattern.IN_V]
        path = Path([], ['SEA', 'route', 'DFW'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)

        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
        self.assertIsNotNone(gn.graph.edges[('SEA', 'DFW', 'route')])

    def test_add_V_inE_V_path(self):
        pattern = [PathPattern.V, PathPattern.IN_E, PathPattern.V]
        path = Path([], ['SEA', 'route', 'DFW'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)

        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
        self.assertIsNotNone(gn.graph.edges[('DFW', 'SEA', 'route')])

    def test_add_V_outE_V_path(self):
        pattern = [PathPattern.V, PathPattern.OUT_E, PathPattern.V]
        path = Path([], ['SEA', 'route', 'DFW'])
        gn = GremlinNetwork()
        gn.add_results_with_pattern([path], pattern)

        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
        self.assertIsNotNone(gn.graph.edges[('SEA', 'DFW', 'route')])
