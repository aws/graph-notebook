"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest
import os

from graph_notebook.seed.load_query import get_data_sets, get_queries


class TestGetDataSets(unittest.TestCase):
    def test_get_data_sets_gremlin(self):
        data_sets = get_data_sets('gremlin')
        self.assertTrue('airports' in data_sets)

    def test_get_sample_queries_gremlin(self):
        language = 'gremlin'
        name = 'airports'
        location = 'samples'
        queries = get_queries(language, name, location)
        self.assertEqual(3, len(queries))
        self.assertEqual('0_nodes.txt', queries[0]['name'])

    def test_get_custom_queries_from_directory_gremlin(self):
        language = ''
        name = 'local_seed_test_propertygraph'
        location = 'Custom'
        name_full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), name)
        queries = get_queries(language, name_full_path, location)
        self.assertEqual(2, len(queries))
        self.assertEqual('0_test_nodes.txt', queries[0]['name'])
        self.assertEqual('1_test_edges.txt', queries[1]['name'])

    def test_get_custom_queries_from_file_gremlin(self):
        language = ''
        name = 'local_seed_test_propertygraph/0_test_nodes.txt'
        location = 'Custom'
        name_full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), name)
        queries = get_queries(language, name_full_path, location)
        self.assertEqual(1, len(queries))
        self.assertEqual('0_test_nodes.txt', queries[0]['name'])

    def test_get_data_sets_sparql(self):
        data_sets = get_data_sets('sparql')
        self.assertTrue('airports' in data_sets)

    def test_get_sample_queries_sparql(self):
        language = 'sparql'
        name = 'airports'
        location = 'samples'
        queries = get_queries(language, name, location)
        self.assertEqual(3, len(queries))
        self.assertEqual('0_nodes.txt', queries[0]['name'])

    def test_get_custom_queries_from_directory_sparql(self):
        language = ''
        name = 'local_seed_test_rdf'
        location = 'Custom'
        name_full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), name)
        queries = get_queries(language, name_full_path, location)
        self.assertEqual(1, len(queries))
        self.assertEqual('0_test_data.txt', queries[0]['name'])

    def test_get_custom_queries_from_file_sparql(self):
        language = ''
        name = 'local_seed_test_rdf/0_test_data.txt'
        location = 'Custom'
        name_full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), name)
        queries = get_queries(language, name_full_path, location)
        self.assertEqual(1, len(queries))
        self.assertEqual('0_test_data.txt', queries[0]['name'])

    def test_get_data_sets_cypher(self):
        data_sets = get_data_sets('opencypher')
        self.assertTrue('airports' in data_sets)

    def test_get_sample_queries_cypher(self):
        language = 'opencypher'
        name = 'airports'
        location = 'samples'
        queries = get_queries(language, name, location)
        self.assertEqual(1, len(queries))
        self.assertEqual('airports_full.txt', queries[0]['name'])

    def test_get_custom_queries_from_directory_cypher(self):
        language = ''
        name = 'local_seed_test_cypher'
        location = 'Custom'
        name_full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), name)
        queries = get_queries(language, name_full_path, location)
        self.assertEqual(1, len(queries))
        self.assertEqual('0_test_data.txt', queries[0]['name'])

    def test_get_custom_queries_from_file_cypher(self):
        language = ''
        name = 'local_seed_test_cypher/0_test_data.txt'
        location = 'Custom'
        name_full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), name)
        queries = get_queries(language, name_full_path, location)
        self.assertEqual(1, len(queries))
        self.assertEqual('0_test_data.txt', queries[0]['name'])
