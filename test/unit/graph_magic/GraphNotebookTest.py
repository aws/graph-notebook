"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""


import unittest

from IPython import get_ipython
from IPython.terminal.interactiveshell import TerminalInteractiveShell

from graph_notebook.configuration.get_config import get_config
from test.integration import TEST_CONFIG_PATH


class GraphNotebookTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        ip = get_ipython()
        if ip is None:
            ip = TerminalInteractiveShell().instance()

        ip.magic('load_ext graph_notebook.magics')
        cls.config = get_config(TEST_CONFIG_PATH)
        cls.ip = ip
