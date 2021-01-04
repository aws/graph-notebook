"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import unittest

from graph_notebook.configuration.get_config import get_config
from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.configuration.generate_config import Configuration, DEFAULT_AUTH_MODE, \
    DEFAULT_IAM_CREDENTIALS_PROVIDER, AuthModeEnum, generate_config


class TestGenerateConfiguration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.host = 'blah'
        cls.port = 8182
        cls.test_file_path = f'{os.path.abspath(os.path.curdir)}/test_configuration_file.json'

    def tearDown(self) -> None:
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_configuration_default_auth_defaults(self):
        config = Configuration(self.host, self.port)
        self.assertEqual(self.host, config.host)
        self.assertEqual(self.port, config.port)
        self.assertEqual(DEFAULT_AUTH_MODE, config.auth_mode)
        self.assertEqual(DEFAULT_IAM_CREDENTIALS_PROVIDER, config.iam_credentials_provider_type)
        self.assertEqual(True, config.ssl)
        self.assertEqual('', config.load_from_s3_arn)

    def test_configuration_override_defaults(self):
        auth_mode = AuthModeEnum.IAM
        credentials_provider = IAMAuthCredentialsProvider.ENV
        ssl = False
        loader_arn = 'foo'
        config = Configuration(self.host, self.port, auth_mode, credentials_provider, loader_arn, ssl)
        self.assertEqual(auth_mode, config.auth_mode)
        self.assertEqual(credentials_provider, config.iam_credentials_provider_type)
        self.assertEqual(ssl, config.ssl)
        self.assertEqual(loader_arn, config.load_from_s3_arn)

    def test_generate_configuration_with_defaults(self):
        config = Configuration(self.host, self.port)
        c = generate_config(config.host, config.port, config.auth_mode, config.ssl,
                            config.iam_credentials_provider_type,
                            config.load_from_s3_arn, config.aws_region)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_generate_configuration_override_defaults(self):
        auth_mode = AuthModeEnum.IAM
        credentials_provider = IAMAuthCredentialsProvider.ENV
        ssl = False
        loader_arn = 'foo'
        aws_region = 'us-west-2'
        config = Configuration(self.host, self.port, auth_mode, credentials_provider, loader_arn, ssl, aws_region)

        c = generate_config(config.host, config.port, config.auth_mode, config.ssl,
                            config.iam_credentials_provider_type,
                            config.load_from_s3_arn, config.aws_region)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())
