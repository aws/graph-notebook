"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest

from test.integration import GraphNotebookIntegrationTest


<<<<<<< HEAD
class TestGraphMagicGremlin(GraphNotebookIntegrationTest):
=======
class TestGraphMagicSparql(GraphNotebookIntegrationTest):
>>>>>>> rebase from 2.1.2

    @pytest.mark.jupyter
    @pytest.mark.sparql
    def test_sparql_query(self):
<<<<<<< HEAD
        query = 'SELECT * WHERE {?s ?o ?p } LIMIT 1'
=======
        query = 'SELECT ?s ?o ?p WHERE {?s ?p ?o } LIMIT 1'
        store_to_var = 'sparql_res'
        self.ip.run_cell_magic('sparql', f'--store-to {store_to_var}', query)
        assert 'graph_notebook_error' not in self.ip.user_ns
        sparql_res = self.ip.user_ns[store_to_var]
        assert ['s', 'o', 'p'] == sparql_res['head']['vars'] or ['subject', 'predicate', 'object', 'context'] == sparql_res['head']['vars']

    @pytest.mark.jupyter
    @pytest.mark.sparql
    def test_sparql_update_and_query(self):
        update = 'INSERT DATA { <https://test.com/s> <https://test.com/p> <https://test.com/o> . }'
        self.ip.run_cell_magic('sparql', '', update)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)

        query = 'SELECT ?o WHERE {<https://test.com/s> ?p ?o } LIMIT 1'
        store_to_var = 'sparql_res'
        self.ip.run_cell_magic('sparql', f'--store-to {store_to_var}', query)

        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        sparql_res = self.ip.user_ns[store_to_var]
        assert 'o' in sparql_res['head']['vars'] or 'object' in sparql_res['head']['vars']

    @pytest.mark.jupyter
    @pytest.mark.sparql
    @pytest.mark.neptune  # marking this for neptune since blazegraph is returning subject, predicate, object bindings
    def test_sparql_query_with_variables(self):
        self.ip.user_ns['subj_var'] = 's'
        query = 'SELECT ?s ?p ?o WHERE {?${subj_var} ?o ?p } LIMIT 1'
>>>>>>> rebase from 2.1.2
        store_to_var = 'sparql_res'
        self.ip.run_cell_magic('sparql', f'--store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        sparql_res = self.ip.user_ns[store_to_var]
        self.assertEqual(['s', 'o', 'p'], sparql_res['head']['vars'])

    @pytest.mark.jupyter
    @pytest.mark.sparql
<<<<<<< HEAD
    def test_sparql_query_explain(self):
        query = 'SELECT * WHERE {?s ?o ?p } LIMIT 1'
=======
    @pytest.mark.neptune
    def test_sparql_query_explain(self):
        query = 'SELECT ?s ?o ?p WHERE {?s ?o ?p } LIMIT 1'
>>>>>>> rebase from 2.1.2
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
