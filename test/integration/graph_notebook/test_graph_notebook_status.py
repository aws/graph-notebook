"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from test.integration.graph_notebook.GraphNotebookIntegrationTest import GraphNotebookIntegrationTest


class TestGraphMagic(GraphNotebookIntegrationTest):
    def tearDown(self) -> None:
        delete_query = "g.V('graph-notebook-test').drop()"
        self.ip.run_cell_magic('gremlin', f'query', delete_query)

    def test_status(self):
        res = self.ip.run_line_magic('status', '')
        self.assertEqual('healthy', res['status'])

    def test_gremlin_query(self):
        label = 'graph-notebook-test'
        query = f"g.addV('{label}')"

        store_to_var = 'gremlin_res'
        self.ip.run_cell_magic('gremlin', f'query --store-to {store_to_var}', query)
        gremlin_res = self.ip.user_ns[store_to_var]

        # TODO: how can we get a look at the objects which were displayed?
        self.assertEqual(gremlin_res[0].label, label)
