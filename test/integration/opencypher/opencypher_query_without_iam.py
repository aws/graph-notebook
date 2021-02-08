"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.opencypher import do_opencypher_query
from graph_notebook.sparql.query import do_sparql_query, do_sparql_explain
from graph_notebook.request_param_generator.factory import create_request_generator

from test.integration import IntegrationTest


class TestOpenCypherQueryWithoutIam(IntegrationTest):
    def test_do_opencypher_query(self):
        create_query = 'CREATE (p:Person {test: true})-[:LIKES]->(t:Technology)'
        request_generator = create_request_generator(AuthModeEnum.DEFAULT)
        res = do_opencypher_query(create_query, self.host, self.port, self.ssl, request_generator)
        self.assertEqual(type(res), dict)

        match_query = '''MATCH (p:Person)
        RETURN p'''
        request_generator = create_request_generator(AuthModeEnum.DEFAULT)
        res = do_opencypher_query(match_query, self.host, self.port, self.ssl, request_generator)
        self.assertEqual(type(res), dict)
        self.assertTrue('p' in res['head']['vars'])

    def tearDown(self) -> None:
        delete_query = '''MATCH (p: Person {test: true)-[l:LIKES]->(t:Technology)
        DELETE p, l, t'''
        request_generator = create_request_generator(AuthModeEnum.DEFAULT)
        do_opencypher_query(delete_query, self.host, self.port, self.ssl, request_generator)

    # def test_do_opencypher_explain(self):
    #     query = "SELECT * WHERE {?s ?p ?o} LIMIT 1"
    #     request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
    #
    #     res = do_sparql_explain(query, self.host, self.port, self.ssl, request_generator)
    #     self.assertEqual(type(res), str)
    #     self.assertTrue(res.startswith('<!DOCTYPE html>'))
