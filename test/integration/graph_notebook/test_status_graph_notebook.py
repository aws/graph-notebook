"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from test.integration.graph_notebook.GraphNotebookIntegrationTest import GraphNotebookIntegrationTest


class TestGraphMagicStatus(GraphNotebookIntegrationTest):
    def test_status(self):
        res = self.ip.run_line_magic('status', '')
        self.assertEqual('healthy', res['status'])
