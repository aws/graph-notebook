"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
from json import JSONDecodeError

import pytest
from botocore.session import get_session

from test.integration import DataDrivenSparqlTest


class TestSparqlQueryWithIam(DataDrivenSparqlTest):
    def setUp(self) -> None:
        super().setUp()
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.iam
    @pytest.mark.sparql
    def test_do_sparql_query(self):
        query = "SELECT * WHERE {?s ?p ?o} LIMIT 1"
        query_res = self.client.sparql(query)
        assert query_res.status_code == 200
        res = query_res.json()

        self.assertEqual(type(res), dict)
        self.assertTrue('s' in res['head']['vars'])
        self.assertTrue('p' in res['head']['vars'])
        self.assertTrue('o' in res['head']['vars'])

    @pytest.mark.iam
    @pytest.mark.sparql
    def test_do_sparql_explain(self):
        query = "SELECT * WHERE {?s ?p ?o} LIMIT 1"
        query_res = self.client.sparql_explain(query)
        assert query_res.status_code == 200
        res = query_res.content.decode('utf-8')
        self.assertEqual(type(res), str)
        self.assertTrue(res.startswith('<!DOCTYPE html>'))

    @pytest.mark.iam
    @pytest.mark.sparql
    def test_iam_describe(self):
        query = '''PREFIX soccer: <http://www.example.com/soccer#>
        DESCRIBE soccer:Arsenal'''
        res = self.client.sparql(query)
        assert res.status_code == 200

        # test that we do not get back json
        with pytest.raises(JSONDecodeError):
            res.json()

        content = res.content.decode('utf-8')
        assert len(content.splitlines()) == 6
