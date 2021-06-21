"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest

from test.integration import GraphNotebookIntegrationTest


class TestGraphMagicGremlin(GraphNotebookIntegrationTest):
    def tearDown(self) -> None:
        delete_query = "g.V('graph-notebook-test').drop()"
        self.ip.run_cell_magic('gremlin', 'query', delete_query)

    @pytest.mark.jupyter
    @pytest.mark.gremlin
    def test_gremlin_query(self):
        label = 'graph-notebook-test'
        query = f"g.addV('{label}')"

        store_to_var = 'gremlin_res'
        self.ip.run_cell_magic('gremlin', f'query --store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        gremlin_res = self.ip.user_ns[store_to_var]

        # TODO: how can we get a look at the objects which were displayed?
        self.assertEqual(gremlin_res[0].label, label)

    @pytest.mark.jupyter
    @pytest.mark.gremlin
    def test_gremlin_query_with_variables(self):
        label = 'graph-notebook-test'
        self.ip.user_ns['test_var'] = label
        query = "g.addV('${test_var}')"

        store_to_var = 'gremlin_res'
        self.ip.run_cell_magic('gremlin', f'query --store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        gremlin_res = self.ip.user_ns[store_to_var]

        self.assertEqual(gremlin_res[0].label, label)

    @pytest.mark.jupyter
    @pytest.mark.gremlin
    def test_gremlin_query_with_variables_and_dict_access(self):
        label = {'key1': {'key2': {'key3': 'value'}}}
        self.ip.user_ns['test_dict'] = label
        query = "g.addV('${test_dict['key1']['key2']['key3']}')"

        store_to_var = 'gremlin_res'
        self.ip.run_cell_magic('gremlin', f'query --store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        gremlin_res = self.ip.user_ns[store_to_var]

        self.assertEqual(gremlin_res[0].label, 'value')
