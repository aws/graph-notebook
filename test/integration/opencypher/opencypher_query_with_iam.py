"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
from neo4j import ResultSummary

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.opencypher import do_opencypher_query
from graph_notebook.opencypher.client_provider.factory import create_opencypher_client_provider
from graph_notebook.opencypher.query import do_opencypher_bolt_query
from test.integration.DataDrivenOpenCypherTest import DataDrivenOpenCypherTest


class TestOpenCypherQueryWithIam(DataDrivenOpenCypherTest):
    def test_do_opencypher_query(self):
        expected_league_name = 'English Premier League'

        '''
        {
          "head": {
            "vars": [
              "l.name"
            ]
          },
          "results": {
            "bindings": [
              {
                "l.name": {
                  "type": "string",
                  "value": "English Premier League"
                }
              }
            ]
          }
        }'''
        query = 'MATCH (l:League) RETURN l.name'
        res = do_opencypher_query(query, self.host, self.port, self.ssl, self.request_generator)
        self.assertEqual(type(res), dict)
        self.assertEqual(expected_league_name, res['results']['bindings'][0]['l.name']['value'])

    def test_do_opencypher_bolt_query(self):
        client_provider = create_opencypher_client_provider(AuthModeEnum.IAM, self.iam_credentials_provider_type)

        query = 'MATCH (p) RETURN p LIMIT 10'
        res = do_opencypher_bolt_query(query, self.host, self.port, self.ssl, client_provider)
        self.assertEqual(len(res[0]), 10)
        self.assertEqual(type(res[1]), ResultSummary)
