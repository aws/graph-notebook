"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.network.gremlin.GremlinNetwork import parse_pattern_list_str
from graph_notebook.network.gremlin.GremlinNetwork import PathPattern


class TestPatternListParser(unittest.TestCase):
    def test_parse_v_e_v(self):
        pattern_str = " v ,e ,v "
        expected = [PathPattern.V, PathPattern.E, PathPattern.V]
        pattern = parse_pattern_list_str(pattern_str)
        self.assertEqual(expected, pattern)
