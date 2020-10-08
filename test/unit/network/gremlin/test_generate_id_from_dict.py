"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.network.gremlin.GremlinNetwork import generate_id_from_dict


class TestGenerateIDFromDict(unittest.TestCase):
    def test_generate_id_from_dict_is_persistent(self):
        data = {'foo': 'val1', 'bar': 123, 'baz': ['a', 1]}
        generated_id = generate_id_from_dict(data)

        data_copy = {'foo': 'val1', 'bar': 123, 'baz': ['a', 1]}
        generated_id_again = generate_id_from_dict(data_copy)
        self.assertEqual(generated_id, generated_id_again)
