"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest

from test.integration import IntegrationTest


class TestSparqlQuery(IntegrationTest):
    @pytest.mark.sparql
    @pytest.mark.neptune
    def test_do_sparql_query(self):
        query = "SELECT * WHERE {?s ?p ?o} LIMIT 1"

        sparql_res = self.client.sparql(query)
        assert sparql_res.status_code == 200
        res = sparql_res.json()

        self.assertEqual(type(res), dict)
        self.assertTrue('s' in res['head']['vars'])
        self.assertTrue('p' in res['head']['vars'])
        self.assertTrue('o' in res['head']['vars'])

    @pytest.mark.sparql
    @pytest.mark.neptune
    def test_do_sparql_explain(self):
        query = "SELECT * WHERE {?s ?p ?o} LIMIT 1"
        query_res = self.client.sparql_explain(query)
        assert query_res.status_code == 200
        res = query_res.content.decode('utf-8')
        self.assertEqual(type(res), str)
        self.assertTrue(res.startswith('<!DOCTYPE html>'))
