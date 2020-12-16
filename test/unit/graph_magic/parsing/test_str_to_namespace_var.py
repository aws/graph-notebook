import unittest

from graph_notebook.magics.parsing import str_to_namespace_var


class TestParsingStrToNamespaceVar(unittest.TestCase):
    def test_none_dict(self):
        key = 'foo'
        local_ns = None
        res = str_to_namespace_var(key, local_ns)
        self.assertEqual(key, res)

    def test_encapsulated_key(self):
        key = '${foo}'
        expected_value = 'test'
        local_ns = {
            'foo': expected_value
        }

        res = str_to_namespace_var(key, local_ns)
        self.assertEqual(expected_value, res)
