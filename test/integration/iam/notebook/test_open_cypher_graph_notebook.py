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
        cell = f'''%%oc query --store-to {store_to_var}
        {query}'''
        self.ip.run_cell(cell)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        res = self.ip.user_ns[store_to_var]

        # TODO: how can we get a look at the objects which were displayed?
        assert len(res['results']) == 1
        assert 'b' in res['results'][0]

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
                    "auth": true
                  }
                }'''

        self.ip.run_cell_magic('graph_notebook_config', '', config)
