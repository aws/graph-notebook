"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest
from botocore.session import get_session

from test.integration import GraphNotebookIntegrationTest


class TestGraphMagicOpenCypher(GraphNotebookIntegrationTest):
    def setUp(self) -> None:
        super().setUp()
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.jupyter
    @pytest.mark.opencypher
    def test_opencypher_query(self):
        query = '''MATCH(a)-->(b)
                    RETURN b
                    LIMIT 1'''

        store_to_var = 'res'
        cell = f'''%%oc --store-to {store_to_var}
        {query}'''
        self.ip.run_cell(cell)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        res = self.ip.user_ns[store_to_var]

        # TODO: how can we get a look at the objects which were displayed?
        assert len(res['results']) == 1
        assert 'b' in res['results'][0]

    @pytest.mark.jupyter
    @pytest.mark.opencypher
    def test_opencypher_bolt(self):
        query = '''MATCH(a)-->(b)
                        RETURN b
                        LIMIT 1'''

        store_to_var = 'res'
        cell = f'''%%oc bolt --store-to {store_to_var}
            {query}'''
        self.ip.run_cell(cell)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        res = self.ip.user_ns[store_to_var]

        assert len(res) == 1
        assert 'b' in res[0]

    @pytest.mark.jupyter
    @pytest.mark.opencypher
    def test_opencypher_query_parameterized_with_var_input(self):
        expected_league_name = "English Premier League"
        query = 'MATCH (l:League {nickname: $LEAGUE_NICKNAME}) RETURN l.name'

        store_to_var = 'res'
        self.ip.user_ns['params_var'] = {'LEAGUE_NICKNAME': 'EPL'}
        cell = f'''%%oc --query-parameters params_var --store-to {store_to_var}
                        {query}'''
        self.ip.run_cell(cell)
        res = self.ip.user_ns[store_to_var]

        assert len(res['results']) == 1
        assert expected_league_name == res['results'][0]['l.name']

    @pytest.mark.jupyter
    @pytest.mark.opencypher
    def test_opencypher_query_parameterized_with_str_input(self):
        expected_league_name = "English Premier League"
        query = 'MATCH (l:League {nickname: $LEAGUE_NICKNAME}) RETURN l.name'

        store_to_var = 'res'
        params_str = '{"LEAGUE_NICKNAME":"EPL"}'
        cell = f'''%%oc --query-parameters {params_str} --store-to {store_to_var}
                {query}'''
        self.ip.run_cell(cell)
        res = self.ip.user_ns[store_to_var]

        assert len(res['results']) == 1
        assert expected_league_name == res['results'][0]['l.name']

    @pytest.mark.jupyter
    @pytest.mark.opencypher
    def test_opencypher_query_parameterized_invalid(self):
        query = 'MATCH (l:League {nickname: $LEAGUE_NICKNAME}) RETURN l.name'

        self.ip.user_ns['params_var'] = ['LEAGUE_NICKNAME']
        cell = f'''%%oc --query-parameters params_var 
                    {query}'''
        self.ip.run_cell(cell)
        self.assertTrue('graph_notebook_error' in self.ip.user_ns)

    @pytest.mark.jupyter
    @pytest.mark.opencypher
    def test_opencypher_bolt_parameterized(self):
        expected_league_name = "English Premier League"
        query = 'MATCH (l:League {nickname: $LEAGUE_NICKNAME}) RETURN l.name'

        store_to_var = 'res'
        params_var = '{"LEAGUE_NICKNAME":"EPL"}'
        cell = f'''%%oc bolt --query-parameters {params_var} --store-to {store_to_var}
                    {query}'''
        self.ip.run_cell(cell)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        res = self.ip.user_ns[store_to_var]

        assert len(res) == 1
        assert expected_league_name == res[0]['l.name']

    @pytest.mark.jupyter
    def test_load_opencypher_config(self):
        config = '''{
                  "host": "localhost",
                  "port": 8182,
                  "auth_mode": "DEFAULT",
                  "load_from_s3_arn": "",
                  "ssl": true,
                  "aws_region": "us-west-2",
                  "neo4j": {
                    "username": "neo4j",
                    "password": "password",
                    "auth": true,
                    "database": ""
                  }
                }'''

        self.ip.run_cell_magic('graph_notebook_config', '', config)
