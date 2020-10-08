"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.request_param_generator.default_request_generator import DefaultRequestGenerator


class TestDefaultRequestGenerator(unittest.TestCase):
    def test_generate_request_params(self):
        method = 'post'
        action = 'foo'
        query = {
            'bar': 'baz'
        }
        host = 'host_endpoint'
        port = 8182
        protocol = 'https'
        headers = {
            'header1': 'header_value_1'
        }

        rpg = DefaultRequestGenerator()
        request_params = rpg.generate_request_params(method, action, query, host, port, protocol, headers)

        expected_url = f'{protocol}://{host}:{port}/{action}'
        self.assertEqual(request_params['method'], method)
        self.assertEqual(request_params['url'], expected_url)
        self.assertEqual(request_params['headers'], headers)
        self.assertEqual(request_params['params'], query)
