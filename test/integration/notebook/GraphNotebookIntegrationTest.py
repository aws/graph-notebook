"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""


import json

from test.unit.graph_magic.GraphNotebookTest import GraphNotebookTest


class GraphNotebookIntegrationTest(GraphNotebookTest):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def setUp(self) -> None:
        super().setUp()
        self.ip.run_cell_magic('graph_notebook_config', '', json.dumps(self.config.to_dict()))
