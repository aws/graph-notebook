"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest

from graph_notebook.network.gremlin.GremlinNetwork import GremlinNetwork

from test.integration import DataDrivenGremlinTest


class TestGremlinNetwork(DataDrivenGremlinTest):

    @pytest.mark.gremlin
    def test_add_paths_to_network(self):
        airports_path_query = "g.V().has('code', 'SEA').outE().inV().path()"
        results = self.client.gremlin_query(airports_path_query)
        gremlin_network = GremlinNetwork()
        gremlin_network.add_results(results)
        sea_code = '22'
        jnu_code = '1102'
        edge_id = '7527'
        expected_label = 'route'
        actual_label = gremlin_network.graph[sea_code][jnu_code][edge_id]['label']
        self.assertEqual(expected_label, actual_label)

    @pytest.mark.gremlin
    def test_add_value_map_to_network(self):
        airports_path_query = "g.V().has('code', 'SEA').outE().inV().path().by(valueMap(true))"
        results = self.client.gremlin_query(airports_path_query)
        gremlin_network = GremlinNetwork()
        gremlin_network.add_results(results)
        edge_id = '7473'
        expected_label = 'route'
        actual_label = gremlin_network.graph.nodes.get(edge_id)['label']
        self.assertEqual(expected_label, actual_label)

    @pytest.mark.gremlin
    def test_add_entire_path(self):
        sea_to_bmi = "g.V().has('code', 'SEA').outE().inV().has('code', 'ORD').outE().inV().has('code', 'BMI').path()"
        results = self.client.gremlin_query(sea_to_bmi)

        gremlin_network = GremlinNetwork()
        gremlin_network.add_results(results)
        self.assertEqual(3, len(gremlin_network.graph.nodes))
        self.assertEqual(2, len(gremlin_network.graph.edges))
        self.assertIsNotNone(gremlin_network.graph.nodes.get('22'))
        self.assertIsNotNone(gremlin_network.graph.nodes.get('18'))
        self.assertIsNotNone(gremlin_network.graph.nodes.get('359'))
        self.assertTrue(gremlin_network.graph.has_edge('22', '18', '4480'))
        self.assertTrue(gremlin_network.graph.has_edge('18', '359', '7208'))

    @pytest.mark.gremlin
    def test_add_paths_with_bad_pattern(self):
        query = "g.V().out().out().path().limit(10)"
        results = self.client.gremlin_query(query)

        gremlin_network = GremlinNetwork()
        gremlin_network.add_results(results)

        # confirm that all edges have empty labels and are undirected
        for e in gremlin_network.graph.edges:
            edge = gremlin_network.graph.edges[e]
            self.assertEqual('', edge['label'])
            self.assertFalse(edge['arrows']['to']['enabled'])

    @pytest.mark.gremlin
    def test_add_path_with_repeat(self):
        query = "g.V().has('airport', 'code', 'ANC').repeat(outE().inV().simplePath()).times(2).path().by('code').by()"
        results = self.client.gremlin_query(query)

        gremlin_network = GremlinNetwork()
        gremlin_network.add_results(results)
        self.assertEqual('route', gremlin_network.graph.edges[('ANC', 'BLI', '5339')]['label'])

    @pytest.mark.gremlin
    def test_valuemap_without_ids(self):
        query = "g.V().has('code', 'ANC').out().path().by(valueMap()).limit(10)"
        results = self.client.gremlin_query(query)

        gremlin_network = GremlinNetwork()
        gremlin_network.add_results(results)
        for n in gremlin_network.graph.nodes:
            node = gremlin_network.graph.nodes.get(n)
            self.assertEqual(gremlin_network.label_max_length, len(node['label']))

    @pytest.mark.gremlin
    def test_path_without_by_nodes_have_ids(self):
        query = "g.V().has('code', 'AUS').outE().inV().outE().inV().has('code', 'SEA').path()"
        results = self.client.gremlin_query(query)
        gremlin_network = GremlinNetwork()
        gremlin_network.add_results(results)
        node = gremlin_network.graph.nodes.get('9')
        self.assertIsNotNone(node)

    @pytest.mark.gremlin
    def test_path_without_by_oute_has_arrows(self):
        query = "g.V().hasLabel('airport').has('code', 'SEA').outE().inV().path()"
        results = self.client.gremlin_query(query)
        gremlin_network = GremlinNetwork()
        gremlin_network.add_results(results)
        edge = gremlin_network.graph.edges[('22', '151', '7474')]
        self.assertTrue('arrows' not in edge)

    @pytest.mark.gremlin
    def test_path_without_by_ine_has_arrows(self):
        query = "g.V().hasLabel('airport').has('code', 'SEA').inE().outV().path()"
        results = self.client.gremlin_query(query)
        gremlin_network = GremlinNetwork()
        gremlin_network.add_results(results)
        edge = gremlin_network.graph.edges[('3728', '22', '54424')]
        self.assertTrue('arrows' not in edge)
