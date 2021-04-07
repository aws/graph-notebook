"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.magics.graph_magic import get_query_type, query_type_to_action


class TestSparql(unittest.TestCase):
    def test_get_query_type(self):
        test_cases = [
            {
                'query': 'SELECT * WHERE { ?s ?p ?o }',
                'expected': 'SELECT'
            }
        ]

        for t in test_cases:
            query_type = get_query_type(t['query'])
            self.assertEqual(t['expected'], query_type)

    def test_query_type_to_action(self):
        test_cases = [
            {
                'type': 'SELECT',
                'expected': 'sparql'
            },
            {
                'type': 'INSERT',
                'expected': 'sparqlupdate'
            }
        ]

        for t in test_cases:
            action = query_type_to_action(t['type'])
            self.assertEqual(t['expected'], action)
