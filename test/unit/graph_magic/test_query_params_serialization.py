"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json
import unittest

from graph_notebook.neptune.utils import serialize_query_params


class TestSerializeQueryParams(unittest.TestCase):
    """Tests for serialize_query_params.
    See: https://github.com/aws/graph-notebook/issues/733
    """

    # --- Dict input ---

    def test_dict_with_quotes_in_values(self):
        params = {'key': """He said "I'm here" """}
        result = serialize_query_params(params)
        self.assertEqual(json.loads(result)['key'], """He said "I'm here" """)

    def test_dict_with_various_types(self):
        params = {'name': 'AUS', 'limit': 10, 'active': True, 'label': None}
        result = serialize_query_params(params)
        self.assertEqual(json.loads(result), params)

    def test_dict_with_nested_structures(self):
        params = {'filters': [{'field': 'name', 'value': "O'Brien"}]}
        result = serialize_query_params(params)
        self.assertEqual(json.loads(result)['filters'][0]['value'], "O'Brien")

    # --- JSON string input ---

    def test_json_string_passthrough(self):
        json_str = '{"text": "I\'m happy", "num": 42}'
        result = serialize_query_params(json_str)
        self.assertEqual(result, json_str)
        self.assertEqual(json.loads(result)['text'], "I'm happy")

    # --- Python dict literal string input ---

    def test_python_dict_literal_string(self):
        result = serialize_query_params("{'text': \"I'm a string with 'quotes'\"}")
        self.assertEqual(json.loads(result)['text'], "I'm a string with 'quotes'")

    # --- Invalid input ---

    def test_invalid_string_returns_none(self):
        self.assertIsNone(serialize_query_params("not a dict at all {{{"))

    # --- End-to-end (magic layer → client layer, called twice) ---

    def test_end_to_end_idempotent(self):
        params = {'inputs': [{'text': "I'm a string with 'single quotes'"}]}
        magic_result = serialize_query_params(params)
        client_result = serialize_query_params(magic_result)
        self.assertEqual(json.loads(client_result)['inputs'][0]['text'], "I'm a string with 'single quotes'")


if __name__ == '__main__':
    unittest.main()
