"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.gremlin.client_provider.default_client import ClientProvider
from graph_notebook.gremlin.query import do_gremlin_query, do_gremlin_explain, do_gremlin_profile
from graph_notebook.request_param_generator.default_request_generator import DefaultRequestGenerator

from test.integration import IntegrationTest


class TestGremlin(IntegrationTest):
    def test_do_gremlin_query(self):
        client_provider = ClientProvider()
        query = 'g.V().limit(1)'
        results = do_gremlin_query(query, self.host, self.port, self.ssl, client_provider)

        self.assertEqual(type(results), list)

    def test_do_gremlin_explain(self):
        query = 'g.V().limit(1)'
        request_generator = DefaultRequestGenerator()
        results = do_gremlin_explain(query, self.host, self.port, self.ssl, request_generator)

        self.assertEqual(type(results), dict)
        self.assertTrue('explain' in results)

    def test_do_gremlin_profile(self):
        query = 'g.V().limit(1)'
        request_generator = DefaultRequestGenerator()
        results = do_gremlin_profile(query, self.host, self.port, self.ssl, request_generator)

        self.assertEqual(type(results), dict)
        self.assertTrue('profile' in results)
