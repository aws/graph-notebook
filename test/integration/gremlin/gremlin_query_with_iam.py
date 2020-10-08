"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.gremlin.query import do_gremlin_query, do_gremlin_explain, do_gremlin_profile
from graph_notebook.gremlin.client_provider.factory import create_client_provider
from graph_notebook.request_param_generator.factory import create_request_generator

from test.integration import IntegrationTest


class TestGremlinWithIam(IntegrationTest):
    def test_do_gremlin_query_with_iam(self):
        client_provider = create_client_provider(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        query = 'g.V().limit(1)'
        results = do_gremlin_query(query, self.host, self.port, self.ssl, client_provider)

        self.assertEqual(type(results), list)

    def test_do_gremlin_explain_with_iam(self):
        query = 'g.V().limit(1)'
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        results = do_gremlin_explain(query, self.host, self.port, self.ssl, request_generator)

        self.assertEqual(type(results), dict)
        self.assertTrue('explain' in results)

    def test_do_gremlin_profile_with_iam(self):
        query = 'g.V().limit(1)'
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        results = do_gremlin_profile(query, self.host, self.port, self.ssl, request_generator)

        self.assertEqual(type(results), dict)
        self.assertTrue('profile' in results)
