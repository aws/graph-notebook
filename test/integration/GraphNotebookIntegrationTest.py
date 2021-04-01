"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json

from IPython import get_ipython
from IPython.terminal.interactiveshell import TerminalInteractiveShell

from test.integration import IntegrationTest


class GraphNotebookIntegrationTest(IntegrationTest):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def setUp(self) -> None:
        super().setUp()

        ip = get_ipython()
        if ip is None:
            ip = TerminalInteractiveShell().instance()
        self.ip = ip

        self.ip.magic('load_ext graph_notebook.magics')
        self.ip.run_cell_magic('graph_notebook_config', '', json.dumps(self.config.to_dict()))
