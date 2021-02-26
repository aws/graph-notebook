"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.request_param_generator.sparql_request_generator import SPARQLRequestGenerator


class TestSparqlRequestGenerator(unittest.TestCase):
    def test_generate_request_params(self):
        method = 'post'
        action = 'foo'  # action is a no-op since we know it is sparql
        query = {
            'bar': 'baz'
        }
        host = 'host_endpoint'
        port = 8182
        protocol = 'https'
        headers = {
            'header1': 'header_value_1'
        }

        rpg = SPARQLRequestGenerator()
        request_params = rpg.generate_request_params(method, action, query, host, port, protocol, headers)
        expected_headers = {
            'header1': 'header_value_1',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        expected_url = f'{protocol}://{host}:{port}/{action}'
        self.assertEqual(request_params['method'], method)
        self.assertEqual(request_params['url'], expected_url)
        self.assertEqual(request_params['headers'], expected_headers)
        self.assertEqual(request_params['params'], query)

    def test_generate_request_params_no_headers(self):
        method = 'post'
        action = 'foo'  # action is a no-op since we know it is sparql
        query = {
            'bar': 'baz'
        }
        host = 'host_endpoint'
        port = 8182
        protocol = 'https'

        rpg = SPARQLRequestGenerator()
        request_params = rpg.generate_request_params(method, action, query, host, port, protocol, headers=None)
        expected_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        expected_url = f'{protocol}://{host}:{port}/{action}'
        self.assertEqual(request_params['method'], method)
        self.assertEqual(request_params['url'], expected_url)
        self.assertEqual(request_params['headers'], expected_headers)
        self.assertEqual(request_params['params'], query)
