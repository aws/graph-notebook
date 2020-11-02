"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.network.sparql.SPARQLNetwork import SPARQLNetwork
from test.unit.network.sparql.data.get_sparql_result import get_sparql_result


class TestSPARQLNetworkToJSON(unittest.TestCase):
    def test_sparql_network_to_json(self):
        data = get_sparql_result("001_kelvin-airroutes.json")

        sparql_network = SPARQLNetwork()
        sparql_network.add_results(data)
        js = sparql_network.to_json()
        self.assertTrue('graph' in js)
