"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import neo4j
from neo4j import ResultSummary

from graph_notebook.opencypher import do_opencypher_query
from graph_notebook.opencypher.client_provider.factory import create_opencypher_client_provider
from graph_notebook.opencypher.query import do_opencypher_bolt_query

from test.integration import IntegrationTest
from test.integration.DataDrivenOpenCypherTest import DataDrivenOpenCypherTest


class TestOpenCypherQueryWithoutIam(DataDrivenOpenCypherTest):
    def test_do_opencypher_query(self):
        match_query = 'MATCH (p) RETURN p LIMIT 10'
        res = do_opencypher_query(match_query, self.host, self.port, self.ssl, self.request_generator)
        self.assertEqual(type(res), dict)
        self.assertTrue('p' in res['head']['vars'])

    def test_do_opencypher_bolt_query(self):
        client_provider = create_opencypher_client_provider(self.auth_mode, self.iam_credentials_provider_type)

        query = 'MATCH (p) RETURN p LIMIT 10'
        res = do_opencypher_bolt_query(query, self.host, self.port, self.ssl, client_provider)
        self.assertEqual(len(res[0]), 10)
        self.assertEqual(type(res[1]), ResultSummary)

    # TODO: DELETE is not supported yet
    # def tearDown(self) -> None:
    #     delete_query = '''MATCH (p: Person {test: true})-[l:LIKES]->(t:Technology)
    #                     DELETE l, p, t'''
    #     do_opencypher_query(delete_query, self.host, self.port, self.ssl)
