"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.request_param_generator.sparql_request_generator import SPARQLRequestGenerator
from graph_notebook.sparql.query import do_sparql_query, do_sparql_explain

from test.integration import IntegrationTest


class TestSparqlQuery(IntegrationTest):
    def test_do_sparql_query(self):
        query = "SELECT * WHERE {?s ?p ?o} LIMIT 1"
        request_generator = SPARQLRequestGenerator()

        res = do_sparql_query(query, self.host, self.port, self.ssl, request_generator)
        self.assertEqual(type(res), dict)
        self.assertTrue('s' in res['head']['vars'])
        self.assertTrue('p' in res['head']['vars'])
        self.assertTrue('o' in res['head']['vars'])

    def test_do_sparql_explain(self):
        query = "SELECT * WHERE {?s ?p ?o} LIMIT 1"
        request_generator = SPARQLRequestGenerator()
        res = do_sparql_explain(query, self.host, self.port, self.ssl, request_generator)
        self.assertEqual(type(res), str)
        self.assertTrue(res.startswith('<!DOCTYPE html>'))
