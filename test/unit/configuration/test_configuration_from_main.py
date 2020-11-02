"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import unittest

from graph_notebook.configuration.generate_config import AuthModeEnum, Configuration
from graph_notebook.configuration.get_config import get_config
from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider


class TestGenerateConfigurationMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.host = 'blah'
        cls.port = 8182
        cls.test_file_path = f'{os.path.abspath(os.path.curdir)}/test_generate_from_main.json'
        cls.python_cmd = os.environ.get('PYTHON_CMD', 'python3')  # environment variable to let ToD hosts specify where the python command is that is being used for testing.

    def tearDown(self) -> None:
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_generate_configuration_main_defaults(self):
        expected_config = Configuration(self.host, self.port, AuthModeEnum.DEFAULT, IAMAuthCredentialsProvider.ROLE, '', True)
        self.generate_config_from_main_and_test(expected_config)

    def test_generate_configuration_main_override_defaults(self):
        expected_config = Configuration(self.host, self.port, AuthModeEnum.IAM, IAMAuthCredentialsProvider.ROLE, 'loader_arn', False)
        self.generate_config_from_main_and_test(expected_config)

    def test_generate_configuration_main_empty_args(self):
        expected_config = Configuration(self.host, self.port)
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config --host "{expected_config.host}" --port "{expected_config.port}" --auth_mode "" --ssl "" --iam_credentials_provider "" --load_from_s3_arn "" --config_destination="{self.test_file_path}" ')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        self.assert_configs_are_equal(expected_config, config)

    def generate_config_from_main_and_test(self, source_config: Configuration):
        # This will run the main method that our install script runs on a Sagemaker notebook.
        # The return code should be 0, but more importantly, we need to assert that the
        # Configuration object we get from the resulting file is what we expect.
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config --host "{source_config.host}" --port "{source_config.port}" --auth_mode "{source_config.auth_mode.value}" --ssl "{source_config.ssl}" --iam_credentials_provider "{source_config.iam_credentials_provider_type.value}" --load_from_s3_arn "{source_config.load_from_s3_arn}" --config_destination="{self.test_file_path}" ')
        self.assertEqual(result, 0)
        config = get_config(self.test_file_path)
        self.assert_configs_are_equal(source_config, config)

    def assert_configs_are_equal(self, config1: Configuration, config2: Configuration):
        for k in config1.__dict__:
            self.assertEqual(config1.__dict__[k], config2.__dict__[k])
