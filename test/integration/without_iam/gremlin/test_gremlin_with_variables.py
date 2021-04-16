"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import pytest

from test.integration import DataDrivenGremlinTest
from graph_notebook.magics.graph_magic import inject_vars_into_query


class TestGremlinQueryWithVariables(DataDrivenGremlinTest):

    @pytest.mark.gremlin
    def test_gremlin_query_with_variables(self):

        expected_result = "['DFW', 'LAX', 'PHX', 'DEN']"

        test_ns = {'c': 'code', 'r': 'route', 'santa_fe': 'SAF'}
        test_cell = "g.V().has('${c}','${santa_fe}').out('${r}').values('${c}')"
        new_cell = inject_vars_into_query(test_cell, test_ns)
        query_res = self.client.gremlin_query(new_cell)

        self.assertEqual(set(query_res), set(expected_result))
