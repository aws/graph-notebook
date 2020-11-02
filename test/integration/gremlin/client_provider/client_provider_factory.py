"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.gremlin.client_provider.default_client import ClientProvider
from graph_notebook.gremlin.client_provider.factory import create_client_provider
from graph_notebook.gremlin.client_provider.iam_client import IamClientProvider


class TestClientProviderFactory(unittest.TestCase):
    def test_create_default_client(self):
        client_provider = create_client_provider(AuthModeEnum.DEFAULT)
        self.assertEqual(ClientProvider, type(client_provider))

    def test_create_iam_client_from_env(self):
        client_provider = create_client_provider(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        self.assertEqual(IamClientProvider, type(client_provider))
