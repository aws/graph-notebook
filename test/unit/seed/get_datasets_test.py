"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.seed.load_query import get_data_sets, get_queries


class TestGetDataSets(unittest.TestCase):
    def test_get_data_sets_gremlin(self):
        data_sets = get_data_sets('gremlin')
        self.assertTrue('airports' in data_sets)

    def test_get_queries_gremlin(self):
        language = 'gremlin'
        name = 'airports'
        queries = get_queries(language, name)
        self.assertEqual(3, len(queries))
        self.assertEqual('0_nodes.txt', queries[0]['name'])

    def test_get_data_sets_sparql(self):
        data_sets = get_data_sets('sparql')
        self.assertTrue('airports' in data_sets)

    def test_get_queries_sparql(self):
        language = 'sparql'
        name = 'airports'
        queries = get_queries(language, name)
        self.assertEqual(3, len(queries))
        self.assertEqual('0_nodes.txt', queries[0]['name'])
