"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest

from test.integration import GraphNotebookIntegrationTest


class TestGraphMagicGremlin(GraphNotebookIntegrationTest):

    @pytest.mark.jupyter
    @pytest.mark.sparql
    def test_sparql_query(self):
        query = 'SELECT * WHERE {?s ?o ?p } LIMIT 1'
        store_to_var = 'sparql_res'
        self.ip.run_cell_magic('sparql', f'--store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        sparql_res = self.ip.user_ns[store_to_var]
        self.assertEqual(['s', 'o', 'p'], sparql_res['head']['vars'])

    @pytest.mark.jupyter
    @pytest.mark.sparql
    def test_sparql_query_with_variables(self):
        self.ip.user_ns['subj_var'] = 's'
        query = 'SELECT * WHERE {?${subj_var} ?o ?p } LIMIT 1'
        store_to_var = 'sparql_res'
        self.ip.run_cell_magic('sparql', f'--store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        sparql_res = self.ip.user_ns[store_to_var]
        self.assertEqual(['s', 'o', 'p'], sparql_res['head']['vars'])

    @pytest.mark.jupyter
    @pytest.mark.sparql
    def test_sparql_query_with_variables_and_dict_access(self):
        self.ip.user_ns['subj_var'] = {'key1': {'key2': {'key3': 's'}}}
        query = 'SELECT * WHERE {?${subj_var["key1"]["key2"]["key3"]} ?o ?p } LIMIT 1'
        store_to_var = 'sparql_res'
        self.ip.run_cell_magic('sparql', f'--store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        sparql_res = self.ip.user_ns[store_to_var]
        self.assertEqual(['s', 'o', 'p'], sparql_res['head']['vars'])

    @pytest.mark.jupyter
    @pytest.mark.sparql
    def test_sparql_query_explain(self):
        query = 'SELECT * WHERE {?s ?o ?p } LIMIT 1'
        store_to_var = 'sparql_res'
        self.ip.run_cell_magic('sparql', f'explain --store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        sparql_res = self.ip.user_ns[store_to_var]
        self.assertTrue(sparql_res.startswith('<!DOCTYPE html>'))
        self.assertTrue('</table>' in sparql_res)

    @pytest.mark.jupyter
    def test_load_sparql_config(self):
        config = '''{
              "host": "localhost",
              "port": 3030,
              "auth_mode": "DEFAULT",
              "iam_credentials_provider_type": "ENV",
              "load_from_s3_arn": "",
              "ssl": false,
              "aws_region": "us-west-2",
              "sparql": {
                "path": "/query"
              }
            }'''

        self.ip.run_cell_magic('graph_notebook_config', '', config)
