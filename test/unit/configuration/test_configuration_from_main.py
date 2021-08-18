"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import unittest

from graph_notebook.configuration.generate_config import AuthModeEnum, Configuration
from graph_notebook.configuration.get_config import get_config


class TestGenerateConfigurationMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generic_host = 'blah'
        cls.neptune_host = 'instance.cluster.us-west-2.neptune.amazonaws.com'
        cls.port = 8182
        cls.test_file_path = f'{os.path.abspath(os.path.curdir)}/test_generate_from_main.json'
        cls.python_cmd = os.environ.get('PYTHON_CMD', 'python3')  # environment variable to let ToD hosts specify
        # where the python command is that is being used for testing.

    def tearDown(self) -> None:
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_generate_configuration_main_defaults_neptune(self):
        expected_config = Configuration(self.neptune_host, self.port, auth_mode=AuthModeEnum.DEFAULT,
                                        load_from_s3_arn='', ssl=True)
        self.generate_config_from_main_and_test(expected_config, host_type='neptune')

    def test_generate_configuration_main_defaults_generic(self):
        expected_config = Configuration(self.generic_host, self.port, ssl=True)
        self.generate_config_from_main_and_test(expected_config)

    def test_generate_configuration_main_override_defaults_neptune(self):
        expected_config = Configuration(self.neptune_host, self.port, auth_mode=AuthModeEnum.IAM,
                                        load_from_s3_arn='loader_arn', ssl=False)
        self.generate_config_from_main_and_test(expected_config, host_type='neptune')

    def test_generate_configuration_main_override_defaults_generic(self):
        expected_config = Configuration(self.generic_host, self.port, ssl=False)
        self.generate_config_from_main_and_test(expected_config)

    def test_generate_configuration_main_empty_args_neptune(self):
        expected_config = Configuration(self.neptune_host, self.port)
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{expected_config.host}" --port "{expected_config.port}" --auth_mode "" --ssl "" '
                           f'--load_from_s3_arn "" --config_destination="{self.test_file_path}" ')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        self.assertEqual(expected_config.to_dict(), config.to_dict())

    def test_generate_configuration_main_empty_args_generic(self):
        expected_config = Configuration(self.generic_host, self.port)
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{expected_config.host}" --port "{expected_config.port}" --ssl "" '
                           f'--config_destination="{self.test_file_path}" ')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        self.assertEqual(expected_config.to_dict(), config.to_dict())

    def generate_config_from_main_and_test(self, source_config: Configuration, host_type=None):
        # This will run the main method that our install script runs on a Sagemaker notebook.
        # The return code should be 0, but more importantly, we need to assert that the
        # Configuration object we get from the resulting file is what we expect.
        if host_type == 'neptune':
            result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                               f'--host "{source_config.host}" --port "{source_config.port}" '
                               f'--auth_mode "{source_config.auth_mode.value}" --ssl "{source_config.ssl}" '
                               f'--load_from_s3_arn "{source_config.load_from_s3_arn}" '
                               f'--config_destination="{self.test_file_path}" ')
        else:
            result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                               f'--host "{source_config.host}" --port "{source_config.port}" '
                               f'--ssl "{source_config.ssl}" --config_destination="{self.test_file_path}" ')
        self.assertEqual(result, 0)
        config = get_config(self.test_file_path)
        self.assertEqual(source_config.to_dict(), config.to_dict())
