"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.opencypher import do_opencypher_query

from test.integration import IntegrationTest


class TestOpenCypherQueryWithoutIam(IntegrationTest):
    def test_do_opencypher_query(self):
        create_query = 'CREATE (p:Person {test: true})-[:LIKES]->(t:Technology)'
        res = do_opencypher_query(create_query, self.host, self.port, self.ssl, self.request_generator)
        self.assertEqual(type(res), dict)

        match_query = '''MATCH (p:Person)
        RETURN p'''
        res = do_opencypher_query(match_query, self.host, self.port, self.ssl, self.request_generator)
        self.assertEqual(type(res), dict)
        self.assertTrue('p' in res['head']['vars'])

    # TODO: DELETE is not supported yet
    # def tearDown(self) -> None:
    #     delete_query = '''MATCH (p: Person {test: true})-[l:LIKES]->(t:Technology)
    #                     DELETE l, p, t'''
    #     do_opencypher_query(delete_query, self.host, self.port, self.ssl)
