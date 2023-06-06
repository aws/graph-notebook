"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import unittest

from graph_notebook.configuration.get_config import get_config
from graph_notebook.configuration.generate_config import Configuration, DEFAULT_AUTH_MODE, AuthModeEnum, generate_config


class TestGenerateConfiguration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generic_host = 'blah'
        cls.neptune_host_reg = 'instance.cluster.us-west-2.neptune.amazonaws.com'
        cls.neptune_host_cn = 'instance.cluster.neptune.cn-north-1.amazonaws.com.cn'
        cls.neptune_host_with_whitespace = '\t\v\n\r\v instance.cluster.us-west-2.neptune.amazonaws.com '
        cls.neptune_host_custom = 'localhost'
        cls.port = 8182
        cls.custom_hosts_list = ['localhost']
        cls.test_file_path = f'{os.path.abspath(os.path.curdir)}/test_configuration_file.json'

    def tearDown(self) -> None:
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_configuration_default_auth_defaults_neptune_reg(self):
        config = Configuration(self.neptune_host_reg, self.port)
        self.assertEqual(self.neptune_host_reg, config.host)
        self.assertEqual(self.port, config.port)
        self.assertEqual(DEFAULT_AUTH_MODE, config.auth_mode)
        self.assertEqual(True, config.ssl)
        self.assertEqual('', config.load_from_s3_arn)

    def test_configuration_default_auth_defaults_neptune_cn(self):
        config = Configuration(self.neptune_host_cn, self.port)
        self.assertEqual(self.neptune_host_cn, config.host)
        self.assertEqual(self.port, config.port)
        self.assertEqual(DEFAULT_AUTH_MODE, config.auth_mode)
        self.assertEqual(True, config.ssl)
        self.assertEqual('', config.load_from_s3_arn)

    def test_configuration_default_auth_defaults_neptune_custom(self):
        config = Configuration(self.neptune_host_custom, self.port, neptune_hosts=self.custom_hosts_list)
        self.assertEqual(self.neptune_host_custom, config.host)
        self.assertEqual(self.port, config.port)
        self.assertEqual(DEFAULT_AUTH_MODE, config.auth_mode)
        self.assertEqual(True, config.ssl)

    def test_configuration_default_auth_defaults_generic(self):
        config = Configuration(self.generic_host, self.port)
        self.assertEqual(self.generic_host, config.host)
        self.assertEqual(self.port, config.port)
        self.assertEqual(True, config.ssl)

    def test_configuration_override_defaults_neptune_reg(self):
        auth_mode = AuthModeEnum.IAM
        ssl = False
        loader_arn = 'foo'
        config = Configuration(self.neptune_host_reg, self.port, auth_mode=auth_mode, load_from_s3_arn=loader_arn,
                               ssl=ssl)
        self.assertEqual(auth_mode, config.auth_mode)
        self.assertEqual(ssl, config.ssl)
        self.assertEqual(loader_arn, config.load_from_s3_arn)

    def test_configuration_override_defaults_neptune_cn(self):
        auth_mode = AuthModeEnum.IAM
        ssl = False
        loader_arn = 'foo'
        config = Configuration(self.neptune_host_cn, self.port, auth_mode=auth_mode, load_from_s3_arn=loader_arn,
                               ssl=ssl)
        self.assertEqual(auth_mode, config.auth_mode)
        self.assertEqual(ssl, config.ssl)
        self.assertEqual(loader_arn, config.load_from_s3_arn)

    def test_configuration_override_defaults_neptune_custom(self):
        auth_mode = AuthModeEnum.IAM
        ssl = False
        loader_arn = 'foo'
        config = Configuration(self.neptune_host_custom, self.port, auth_mode=auth_mode, load_from_s3_arn=loader_arn,
                               ssl=ssl, neptune_hosts=self.custom_hosts_list)
        self.assertEqual(auth_mode, config.auth_mode)
        self.assertEqual(ssl, config.ssl)
        self.assertEqual(loader_arn, config.load_from_s3_arn)

    def test_configuration_override_defaults_generic(self):
        ssl = False
        config = Configuration(self.generic_host, self.port, ssl=ssl)
        self.assertEqual(ssl, config.ssl)

    def test_generate_configuration_with_defaults_neptune_reg(self):
        config = Configuration(self.neptune_host_reg, self.port)
        c = generate_config(config.host, config.port, auth_mode=config.auth_mode, ssl=config.ssl,
                            load_from_s3_arn=config.load_from_s3_arn, aws_region=config.aws_region)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_generate_configuration_with_defaults_neptune_cn(self):
        config = Configuration(self.neptune_host_cn, self.port)
        c = generate_config(config.host, config.port, auth_mode=config.auth_mode, ssl=config.ssl,
                            load_from_s3_arn=config.load_from_s3_arn, aws_region=config.aws_region)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_generate_configuration_with_defaults_neptune_custom(self):
        config = Configuration(self.neptune_host_custom, self.port, neptune_hosts=self.custom_hosts_list)
        c = generate_config(config.host, config.port, auth_mode=config.auth_mode, ssl=config.ssl,
                            load_from_s3_arn=config.load_from_s3_arn, aws_region=config.aws_region,
                            neptune_hosts=self.custom_hosts_list)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path, neptune_hosts=self.custom_hosts_list)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_generate_configuration_with_defaults_generic(self):
        config = Configuration(self.generic_host, self.port)
        c = generate_config(config.host, config.port, ssl=config.ssl)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_generate_configuration_override_defaults_neptune_reg(self):
        auth_mode = AuthModeEnum.IAM
        ssl = False
        loader_arn = 'foo'
        aws_region = 'us-west-2'
        config = Configuration(self.neptune_host_reg, self.port, auth_mode=auth_mode, load_from_s3_arn=loader_arn, ssl=ssl,
                               aws_region=aws_region)

        c = generate_config(config.host, config.port, auth_mode=config.auth_mode, ssl=config.ssl,
                            load_from_s3_arn=config.load_from_s3_arn, aws_region=config.aws_region)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_generate_configuration_override_defaults_neptune_no_verify(self):
        auth_mode = AuthModeEnum.IAM
        ssl = True
        ssl_verify = False
        loader_arn = 'foo'
        aws_region = 'us-iso-east-1'
        config = Configuration(self.neptune_host_reg, self.port, auth_mode=auth_mode,
                               load_from_s3_arn=loader_arn,
                               ssl=ssl, ssl_verify=ssl_verify,
                               aws_region=aws_region)

        c = generate_config(config.host, config.port, auth_mode=config.auth_mode,
                            load_from_s3_arn=config.load_from_s3_arn,
                            ssl=config.ssl, ssl_verify=config.ssl_verify,
                            aws_region=config.aws_region)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_generate_configuration_override_defaults_neptune_cn(self):
        auth_mode = AuthModeEnum.IAM
        ssl = False
        loader_arn = 'foo'
        aws_region = 'cn-north-1'
        config = Configuration(self.neptune_host_cn, self.port, auth_mode=auth_mode, load_from_s3_arn=loader_arn, ssl=ssl,
                               aws_region=aws_region)

        c = generate_config(config.host, config.port, auth_mode=config.auth_mode, ssl=config.ssl,
                            load_from_s3_arn=config.load_from_s3_arn, aws_region=config.aws_region)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_generate_configuration_override_defaults_neptune_custom(self):
        auth_mode = AuthModeEnum.IAM
        ssl = False
        loader_arn = 'foo'
        aws_region = 'cn-north-1'
        config = Configuration(self.neptune_host_custom, self.port, auth_mode=auth_mode, load_from_s3_arn=loader_arn,
                               ssl=ssl, aws_region=aws_region, neptune_hosts=self.custom_hosts_list)

        c = generate_config(config.host, config.port, auth_mode=config.auth_mode, ssl=config.ssl,
                            load_from_s3_arn=config.load_from_s3_arn, aws_region=config.aws_region,
                            neptune_hosts=self.custom_hosts_list)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path, neptune_hosts=self.custom_hosts_list)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_generate_configuration_override_defaults_generic(self):
        ssl = False
        config = Configuration(self.generic_host, self.port, ssl=ssl)
        c = generate_config(config.host, config.port, ssl=config.ssl)
        c.write_to_file(self.test_file_path)
        config_from_file = get_config(self.test_file_path)
        self.assertEqual(config.to_dict(), config_from_file.to_dict())

    def test_configuration_neptune_host_with_whitespace(self):
        config = Configuration(self.neptune_host_with_whitespace, self.port)
        self.assertEqual(config.host, self.neptune_host_reg)
        self.assertEqual(config._host, self.neptune_host_reg)

    def test_configuration_neptune_host_with_whitespace_using_setter(self):
        config = Configuration("localhost", self.port)
        config.host = self.neptune_host_with_whitespace
        self.assertEqual(config.host, self.neptune_host_reg)
        self.assertEqual(config._host, self.neptune_host_reg)

    def test_configuration_neptune_proxy_host_with_whitespace(self):
        config = Configuration("localhost", self.port, proxy_host=self.neptune_host_with_whitespace)
        self.assertEqual(config.proxy_host, self.neptune_host_reg)
        self.assertEqual(config._proxy_host, self.neptune_host_reg)

    def test_configuration_neptune_proxy_host_with_whitespace_using_setter(self):
        config = Configuration("localhost", self.port)
        config.proxy_host = self.neptune_host_with_whitespace
        self.assertEqual(config.proxy_host, self.neptune_host_reg)
        self.assertEqual(config._proxy_host, self.neptune_host_reg)
