"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import unittest

from graph_notebook.configuration.generate_config import AuthModeEnum, Configuration, GremlinSection
from graph_notebook.configuration.get_config import get_config
from graph_notebook.neptune.client import (NEPTUNE_DB_SERVICE_NAME, NEPTUNE_ANALYTICS_SERVICE_NAME,
                                           DEFAULT_HTTP_PROTOCOL, DEFAULT_WS_PROTOCOL)


class TestGenerateConfigurationMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generic_host = 'blah'
        cls.neptune_host_reg = 'instance.cluster.us-west-2.neptune.amazonaws.com'
        cls.neptune_host_cn = 'instance.cluster.neptune.cn-north-1.amazonaws.com.cn'
        cls.neptune_host_custom = 'localhost'
        cls.port = 8182
        cls.test_file_path = f'{os.path.abspath(os.path.curdir)}/test_generate_from_main.json'
        cls.custom_hosts_list = ['localhost']
        cls.python_cmd = os.environ.get('PYTHON_CMD', 'python3')  # environment variable to let ToD hosts specify
        # where the python command is that is being used for testing.

    def tearDown(self) -> None:
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_generate_configuration_main_defaults_neptune_reg(self):
        expected_config = Configuration(self.neptune_host_reg,
                                        self.port,
                                        neptune_service='neptune-db',
                                        auth_mode=AuthModeEnum.DEFAULT,
                                        load_from_s3_arn='',
                                        ssl=True)
        self.generate_config_from_main_and_test(expected_config, host_type='neptune')

    def test_generate_configuration_main_defaults_neptune_cn(self):
        expected_config = Configuration(self.neptune_host_cn,
                                        self.port,
                                        auth_mode=AuthModeEnum.DEFAULT,
                                        load_from_s3_arn='',
                                        ssl=True)
        self.generate_config_from_main_and_test(expected_config, host_type='neptune')

    def test_generate_configuration_main_defaults_generic(self):
        expected_config = Configuration(self.generic_host, self.port, ssl=True)
        self.generate_config_from_main_and_test(expected_config)

    def test_generate_configuration_main_override_defaults_neptune_reg(self):
        expected_config = Configuration(self.neptune_host_reg,
                                        self.port,
                                        neptune_service='neptune-graph',
                                        auth_mode=AuthModeEnum.IAM,
                                        load_from_s3_arn='loader_arn',
                                        ssl=False,
                                        gremlin_section=GremlinSection(
                                            connection_protocol=DEFAULT_HTTP_PROTOCOL,
                                            include_protocol=True
                                        )
                                        )
        self.generate_config_from_main_and_test(expected_config, host_type='neptune')

    def test_generate_configuration_main_override_defaults_neptune_no_verify(self):
        expected_config = Configuration(self.neptune_host_reg,
                                        self.port,
                                        neptune_service='neptune-graph',
                                        auth_mode=AuthModeEnum.IAM,
                                        load_from_s3_arn='loader_arn',
                                        ssl=True,
                                        ssl_verify=False,
                                        gremlin_section=GremlinSection(
                                            connection_protocol=DEFAULT_HTTP_PROTOCOL,
                                            include_protocol=True
                                        )
                                        )
        self.generate_config_from_main_and_test(expected_config, host_type='neptune')

    def test_generate_configuration_main_override_defaults_neptune_with_serializer(self):
        expected_config = Configuration(self.neptune_host_reg,
                                        self.port,
                                        neptune_service='neptune-graph',
                                        auth_mode=AuthModeEnum.IAM,
                                        load_from_s3_arn='loader_arn',
                                        ssl=False,
                                        gremlin_section=GremlinSection(
                                            message_serializer='graphbinary',
                                            connection_protocol=DEFAULT_HTTP_PROTOCOL,
                                            include_protocol=True
                                        )
                                        )
        self.generate_config_from_main_and_test(expected_config, host_type='neptune')

    def test_generate_configuration_main_override_defaults_neptune_cn(self):
        expected_config = Configuration(self.neptune_host_cn,
                                        self.port,
                                        neptune_service='neptune-graph',
                                        auth_mode=AuthModeEnum.IAM,
                                        load_from_s3_arn='loader_arn',
                                        ssl=False,
                                        gremlin_section=GremlinSection(
                                            connection_protocol=DEFAULT_HTTP_PROTOCOL,
                                            include_protocol=True
                                        )
                                        )
        self.generate_config_from_main_and_test(expected_config, host_type='neptune')

    def test_generate_configuration_main_override_defaults_generic(self):
        expected_config = Configuration(self.generic_host, self.port, ssl=False)
        self.generate_config_from_main_and_test(expected_config)

    def test_generate_configuration_main_empty_args_neptune(self):
        expected_config = Configuration(self.neptune_host_reg, self.port)
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{expected_config.host}" --port "{expected_config.port}" '
                           f'--auth_mode "" --ssl "" '
                           f'--load_from_s3_arn "" --config_destination="{self.test_file_path}" '
                           f'--neptune_service ""')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        self.assertEqual(expected_config.to_dict(), config.to_dict())

    def test_generate_configuration_main_gremlin_protocol_no_service(self):
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{self.neptune_host_reg}" '
                           f'--port "{self.port}" '
                           f'--neptune_service "" '
                           f'--auth_mode "" '
                           f'--ssl "" '
                           f'--load_from_s3_arn "" '
                           f'--config_destination="{self.test_file_path}" ')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        config_dict = config.to_dict()
        self.assertEqual(DEFAULT_WS_PROTOCOL, config_dict['gremlin']['connection_protocol'])

    def test_generate_configuration_main_gremlin_protocol_db(self):
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{self.neptune_host_reg}" '
                           f'--port "{self.port}" '
                           f'--neptune_service "{NEPTUNE_DB_SERVICE_NAME}" '
                           f'--auth_mode "" '
                           f'--ssl "" '
                           f'--load_from_s3_arn "" '
                           f'--config_destination="{self.test_file_path}" ')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        config_dict = config.to_dict()
        self.assertEqual(DEFAULT_WS_PROTOCOL, config_dict['gremlin']['connection_protocol'])

    def test_generate_configuration_main_gremlin_protocol_analytics(self):
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{self.neptune_host_reg}" '
                           f'--port "{self.port}" '
                           f'--neptune_service "{NEPTUNE_ANALYTICS_SERVICE_NAME}" '
                           f'--auth_mode "" '
                           f'--ssl "" '
                           f'--load_from_s3_arn "" '
                           f'--config_destination="{self.test_file_path}" ')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        config_dict = config.to_dict()
        self.assertEqual(DEFAULT_HTTP_PROTOCOL, config_dict['gremlin']['connection_protocol'])

    def test_generate_configuration_main_gremlin_serializer_no_service(self):
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{self.neptune_host_reg}" '
                           f'--port "{self.port}" '
                           f'--neptune_service "" '
                           f'--auth_mode "" '
                           f'--ssl "" '
                           f'--load_from_s3_arn "" '
                           f'--config_destination="{self.test_file_path}" ')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        config_dict = config.to_dict()
        self.assertEqual('GraphSONMessageSerializerV3', config_dict['gremlin']['message_serializer'])

    def test_generate_configuration_main_gremlin_serializer_db(self):
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{self.neptune_host_reg}" '
                           f'--port "{self.port}" '
                           f'--neptune_service "{NEPTUNE_DB_SERVICE_NAME}" '
                           f'--auth_mode "" '
                           f'--ssl "" '
                           f'--load_from_s3_arn "" '
                           f'--config_destination="{self.test_file_path}" ')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        config_dict = config.to_dict()
        self.assertEqual('GraphSONMessageSerializerV3', config_dict['gremlin']['message_serializer'])

    def test_generate_configuration_main_gremlin_serializer_analytics(self):
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{self.neptune_host_reg}" '
                           f'--port "{self.port}" '
                           f'--neptune_service "{NEPTUNE_ANALYTICS_SERVICE_NAME}" '
                           f'--auth_mode "" '
                           f'--ssl "" '
                           f'--load_from_s3_arn "" '
                           f'--config_destination="{self.test_file_path}" ')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        config_dict = config.to_dict()
        self.assertEqual('GraphSONUntypedMessageSerializerV4', config_dict['gremlin']['message_serializer'])

    def test_generate_configuration_main_empty_args_custom(self):
        expected_config = Configuration(self.neptune_host_custom, self.port, neptune_hosts=self.custom_hosts_list)
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{expected_config.host}" --port "{expected_config.port}" --auth_mode "" --ssl "" '
                           f'--load_from_s3_arn "" --config_destination="{self.test_file_path}" '
                           f'--neptune_hosts {self.custom_hosts_list[0]} '
                           f'--neptune_service ""')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path, neptune_hosts=self.custom_hosts_list)
        self.assertEqual(expected_config.to_dict(), config.to_dict())

    def test_generate_configuration_main_empty_args_generic(self):
        expected_config = Configuration(self.generic_host, self.port)
        result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                           f'--host "{expected_config.host}" --port "{expected_config.port}" --ssl "" '
                           f'--config_destination="{self.test_file_path}" '
                           f'--neptune_service ""')
        self.assertEqual(0, result)
        config = get_config(self.test_file_path)
        self.assertEqual(expected_config.to_dict(), config.to_dict())

    def generate_config_from_main_and_test(self, source_config: Configuration, host_type=None):
        # This will run the main method that our install script runs on a Sagemaker notebook.
        # The return code should be 0, but more importantly, we need to assert that the
        # Configuration object we get from the resulting file is what we expect.
        if host_type == 'neptune':
            result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                               f'--host "{source_config.host}" '
                               f'--port "{source_config.port}" '
                               f'--neptune_service "{source_config.neptune_service}" '
                               f'--auth_mode "{source_config.auth_mode.value}" '
                               f'--ssl "{source_config.ssl}" '
                               f'--ssl-verify "{source_config.ssl_verify}" '
                               f'--load_from_s3_arn "{source_config.load_from_s3_arn}" '
                               f'--proxy_host "{source_config.proxy_host}" '
                               f'--proxy_port "{source_config.proxy_port}" '
                               f'--gremlin_serializer "{source_config.gremlin.message_serializer}" '
                               f'--config_destination="{self.test_file_path}"')
        else:
            result = os.system(f'{self.python_cmd} -m graph_notebook.configuration.generate_config '
                               f'--host "{source_config.host}" --port "{source_config.port}" '
                               f'--proxy_host "{source_config.proxy_host}" '
                               f'--proxy_port "{source_config.proxy_port}" '
                               f'--ssl "{source_config.ssl}" '
                               f'--ssl-verify "{source_config.ssl_verify}" '
                               f'--config_destination="{self.test_file_path}" ')
        self.assertEqual(result, 0)
        config = get_config(self.test_file_path)
        self.assertEqual(source_config.to_dict(), config.to_dict())
