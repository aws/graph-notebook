"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""


import unittest

from IPython import get_ipython
from IPython.terminal.interactiveshell import TerminalInteractiveShell


class GraphNotebookTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        ip = get_ipython()
        if ip is None:
            ip = TerminalInteractiveShell().instance()

        ip.magic('load_ext graph_notebook.magics')
        cls.config = ip.run_line_magic('graph_notebook_config', '')
        cls.ip = ip
