"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json

from IPython.testing.globalipapp import get_ipython

from graph_notebook.configuration.generate_config import Configuration
from test.unit.graph_magic.GraphNotebookTest import GraphNotebookTest


class TestGraphMagicLoadExt(GraphNotebookTest):
    def test_load_graph_magic_succeeds(self):
        res = self.ip.run_line_magic('lsmagic', '')
        self.assertTrue('graph_notebook_config' in res.magics_manager.magics['line'])

    def test_graph_notebook_config(self):
        ip = get_ipython()
        ip.magic('load_ext graph_notebook.magics')

        res: Configuration = ip.run_line_magic('graph_notebook_config', '')
        config_dict = res.to_dict()
        self.assertEqual(self.config.to_dict(), res.to_dict())

        config_dict['host'] = 'this-was-changed'
        res2: Configuration = ip.run_cell_magic('graph_notebook_config', '', json.dumps(config_dict))
        config_dict2 = res2.to_dict()

        res3: Configuration = ip.run_line_magic('graph_notebook_config', '')
        config_dict3 = res3.to_dict()

        self.assertEqual(config_dict2, config_dict3)
