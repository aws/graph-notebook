"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.opencypher import do_opencypher_query
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

