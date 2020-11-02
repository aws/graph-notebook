"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.network.sparql.SPARQLNetwork import SPARQLNetwork
from test.unit.network.sparql.data.get_sparql_result import get_sparql_result


class TestSPARQLNetworkLabelExtraction(unittest.TestCase):
    def test_node_and_edge_label_extraction(self):
        data = get_sparql_result("003_large_binding_set.json")

        sn = SPARQLNetwork()
        sn.add_results(data)
        self.assertEqual(443, len(sn.graph.nodes))

        # pick out a few random nodes and ensure that they match the expected result from json file
        node_108 = sn.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/108')
        self.assertEqual('NCE', node_108['label'])

        node_1265 = sn.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/1265')
        self.assertEqual('resourc...', node_1265['label'])

    def test_highly_connected_node(self):
        data = get_sparql_result('002_airroutes-labels.json')
        sn = SPARQLNetwork()
        sn.add_results(data)
        center_node = sn.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/12')
        self.assertEqual('JFK', center_node['label'])
        self.assertEqual(14, len(center_node['properties']))
