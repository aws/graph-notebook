"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.configuration.get_config import get_config
from graph_notebook.request_param_generator.factory import create_request_generator
from test.integration.NeptuneIntegrationWorkflowSteps import TEST_CONFIG_PATH


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        config = get_config(TEST_CONFIG_PATH)
        cls.config = config
        cls.host = config.host
        cls.port = config.port
        cls.auth_mode = config.auth_mode
        cls.ssl = config.ssl
        cls.iam_credentials_provider_type = config.iam_credentials_provider_type
        cls.load_from_s3_arn = config.load_from_s3_arn
        cls.request_generator = create_request_generator(cls.auth_mode, IAMAuthCredentialsProvider.ENV)
