"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import unittest

from graph_notebook.configuration.get_config import get_config, get_config_from_dict
from graph_notebook.configuration.generate_config import Configuration, DEFAULT_AUTH_MODE, AuthModeEnum, \
    generate_config, generate_default_config, GremlinSection
from graph_notebook.neptune.client import NEPTUNE_DB_SERVICE_NAME, NEPTUNE_ANALYTICS_SERVICE_NAME, \
    DEFAULT_WS_PROTOCOL, DEFAULT_HTTP_PROTOCOL, NEPTUNE_CONFIG_HOST_IDENTIFIERS


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
        cls.neptune_service_db = NEPTUNE_DB_SERVICE_NAME
        cls.neptune_service_db_short = 'db'
        cls.neptune_service_graph = NEPTUNE_ANALYTICS_SERVICE_NAME
        cls.neptune_service_graph_short = 'graph'

    def tearDown(self) -> None:
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_generate_default_config(self):
        config = generate_default_config()
        self.assertEqual(True, config.is_neptune_config)
        self.assertEqual('change-me', config.host)
        self.assertEqual(8182, config.port)
        self.assertEqual('', config._proxy_host)
        self.assertEqual(8182, config.proxy_port)
        self.assertEqual(DEFAULT_AUTH_MODE, config.auth_mode)
        self.assertEqual(True, config.ssl)
        self.assertEqual(True, config.ssl_verify)
        self.assertEqual('neptune-db', config.neptune_service)
        self.assertEqual('', config.load_from_s3_arn)
        self.assertEqual('us-east-1', config.aws_region)
        self.assertEqual('sparql', config.sparql.path)
        self.assertEqual('g', config.gremlin.traversal_source)
        self.assertEqual('', config.gremlin.username)
        self.assertEqual('', config.gremlin.password)
        self.assertEqual(DEFAULT_WS_PROTOCOL, config.gremlin.connection_protocol)
        self.assertEqual('GraphSONMessageSerializerV3', config.gremlin.message_serializer)
        self.assertEqual('neo4j', config.neo4j.username)
        self.assertEqual('password', config.neo4j.password)
        self.assertEqual(True, config.neo4j.auth)
        self.assertEqual(None, config.neo4j.database)

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

    def test_get_configuration_empty_input(self):
        input_config = {}
        with self.assertRaises(KeyError):
            get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)

    def test_get_configuration_no_host(self):
        input_config = {
            "port": 8182,
            "ssl": True
        }
        with self.assertRaises(KeyError):
            get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)

    def test_get_configuration_generic_no_port(self):
        input_config = {
            "host": "localhost",
            "ssl": True
        }
        with self.assertRaises(KeyError):
            get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)

    def test_get_configuration_generic_no_ssl(self):
        input_config = {
            "host": "localhost",
            "port": 8182
        }
        with self.assertRaises(KeyError):
            get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)

    def test_get_configuration_generic_required_input(self):
        input_config = {
            "host": "localhost",
            "port": 8182,
            "ssl": True
        }
        expected_config = {
            'host': 'localhost',
            'port': 8182,
            'proxy_host': '',
            'proxy_port': 8182,
            'ssl': True,
            'ssl_verify': True,
            'sparql': {
                'path': ''
            },
            'gremlin': {
                'traversal_source': 'g',
                'username': '',
                'password': '',
                'message_serializer': 'GraphSONMessageSerializerV3'
            },
            'neo4j': {
                'username': 'neo4j',
                'password': 'password',
                'auth': True,
                'database': None
            }
        }
        config = get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)
        self.assertEqual(config.to_dict(), expected_config)

    def test_get_configuration_generic_all_input(self):
        input_and_expected_config = {
            'host': 'a_host',
            'port': 9999,
            'proxy_host': 'a_proxy_host',
            'proxy_port': 9999,
            'ssl': False,
            'ssl_verify': False,
            'sparql': {
                'path': 'a_path'
            },
            'gremlin': {
                'traversal_source': 'a',
                'username': 'user',
                'password': 'pass',
                'message_serializer': 'GraphBinaryMessageSerializerV1'
            },
            'neo4j': {
                'username': 'neo_user',
                'password': 'neo_pass',
                'auth': False,
                'database': 'neo_db'
            }
        }
        config = get_config_from_dict(input_and_expected_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)
        self.assertEqual(config.to_dict(), input_and_expected_config)

    def test_get_configuration_neptune_no_auth_mode(self):
        input_config = {
            "host": "db.cluster-xxxxxxxxx.us-west-2.neptune.amazonaws.com",
            "port": 8182,
            "ssl": True,
            "load_from_s3_arn": "",
            "aws_region": "us-west-2"
        }
        with self.assertRaises(KeyError):
            get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)

    def test_get_configuration_neptune_no_load_arn(self):
        input_config = {
            "host": "db.cluster-xxxxxxxxx.us-west-2.neptune.amazonaws.com",
            "port": 8182,
            "ssl": True,
            "aws_region": "us-west-2"
        }
        with self.assertRaises(KeyError):
            get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)

    def test_get_configuration_neptune_no_region(self):
        input_config = {
            "host": "db.cluster-xxxxxxxxx.us-west-2.neptune.amazonaws.com",
            "port": 8182,
            "ssl": True,
            "load_from_s3_arn": ""
        }
        with self.assertRaises(KeyError):
            get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)

    def test_get_configuration_neptune_required_input(self):
        input_config = {
            "host": "db.cluster-xxxxxxxxx.us-west-2.neptune.amazonaws.com",
            "port": 8182,
            "auth_mode": "IAM",
            "load_from_s3_arn": "",
            "ssl": True,
            "aws_region": "us-west-2"
        }
        expected_config = {
            'host': 'db.cluster-xxxxxxxxx.us-west-2.neptune.amazonaws.com',
            'neptune_service': 'neptune-db',
            'port': 8182,
            'proxy_host': '',
            'proxy_port': 8182,
            'auth_mode': 'IAM',
            'load_from_s3_arn': '',
            'ssl': True,
            'ssl_verify': True,
            'aws_region': 'us-west-2',
            'sparql': {
                'path': ''
            },
            'gremlin': {
                'traversal_source': 'g',
                'username': '',
                'password': '',
                'message_serializer': 'GraphSONMessageSerializerV3',
                'connection_protocol': 'websockets'
            },
            'neo4j': {
                'username': 'neo4j',
                'password': 'password',
                'auth': True,
                'database': None
            }
        }

        config = get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)
        self.assertEqual(config.to_dict(), expected_config)

    def test_get_configuration_neptune_all_input(self):
        input_config = {
            'host': 'db.cluster-xxxxxxxxx.us-west-2.neptune.amazonaws.com',
            'neptune_service': 'neptune-graph',
            'port': 9999,
            'proxy_host': 'a_proxy+port',
            'proxy_port': 9999,
            'auth_mode': 'DEFAULT',
            'load_from_s3_arn': 'a_role',
            'ssl': False,
            'ssl_verify': False,
            'aws_region': 'us-west-2',
            'sparql': {
                'path': 'a_path'
            },
            'gremlin': {
                'traversal_source': 'a',
                'username': 'a_user',
                'password': 'a_pass',
                'message_serializer': 'GraphSONUntypedMessageSerializerV3',
                'connection_protocol': 'http'
            },
            'neo4j': {
                'username': 'a_user',
                'password': 'a_pass',
                'auth': False,
                'database': 'a_db'
            }
        }
        expected_config = {
            'host': 'db.cluster-xxxxxxxxx.us-west-2.neptune.amazonaws.com',
            'neptune_service': 'neptune-graph',
            'port': 9999,
            'proxy_host': 'a_proxy+port',
            'proxy_port': 9999,
            'auth_mode': 'DEFAULT',
            'load_from_s3_arn': 'a_role',
            'ssl': False,
            'ssl_verify': False,
            'aws_region': 'us-west-2',
            'sparql': {
                'path': 'a_path'
            },
            'gremlin': {
                'traversal_source': 'g',
                'username': '',
                'password': '',
                'message_serializer': 'GraphSONUntypedMessageSerializerV3',
                'connection_protocol': 'http'
            },
            'neo4j': {
                'username': 'neo4j',
                'password': 'password',
                'auth': True,
                'database': None
            }
        }

        config = get_config_from_dict(input_config, neptune_hosts=NEPTUNE_CONFIG_HOST_IDENTIFIERS)
        self.assertEqual(config.to_dict(), expected_config)

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
        print(config_from_file.to_dict())
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

    def test_configuration_gremlinsection_generic_default(self):
        config = Configuration('localhost', self.port)
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONMessageSerializerV3')
        self.assertFalse(hasattr(config.gremlin, "connection_protocol"))

    def test_configuration_gremlinsection_generic_override_protocol(self):
        config = Configuration('localhost',
                               self.port,
                               gremlin_section=GremlinSection(connection_protocol='http'),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONMessageSerializerV3')
        self.assertFalse(hasattr(config.gremlin, "connection_protocol"))

    def test_configuration_gremlinsection_generic_override_serializer_invalid(self):
        config = Configuration('localhost',
                               self.port,
                               gremlin_section=GremlinSection(message_serializer='not_a_serializer'),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONMessageSerializerV3')
        self.assertFalse(hasattr(config.gremlin, "connection_protocol"))

    def test_configuration_gremlinsection_generic_override_serializer_http_only(self):
        config = Configuration('localhost',
                               self.port,
                               gremlin_section=GremlinSection(traversal_source='t',
                                                              username='foo',
                                                              password='bar',
                                                              message_serializer='GraphSONUntypedMessageSerializerV1'),
                               )
        self.assertEqual(config.gremlin.traversal_source, 't')
        self.assertEqual(config.gremlin.username, 'foo')
        self.assertEqual(config.gremlin.password, 'bar')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONMessageSerializerV3')
        self.assertFalse(hasattr(config.gremlin, "connection_protocol"))

    def test_configuration_gremlinsection_neptune_default(self):
        config = Configuration(self.neptune_host_reg, self.port)
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONMessageSerializerV3')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_WS_PROTOCOL)

    def test_configuration_gremlinsection_neptune_override_all(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               gremlin_section=GremlinSection(traversal_source='t',
                                                              username='foo',
                                                              password='bar',
                                                              message_serializer='graphbinary',
                                                              connection_protocol='http',
                                                              include_protocol=True),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV3')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_default_db(self):
        config = Configuration(self.neptune_host_reg, self.port, neptune_service=NEPTUNE_DB_SERVICE_NAME)
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONMessageSerializerV3')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_WS_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_protocol(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='http',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV3')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_protocol_invalid(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='not_a_protocol',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONMessageSerializerV3')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_WS_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_serializer(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(message_serializer='graphbinary',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphBinaryMessageSerializerV1')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_WS_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_serializer_invalid(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(message_serializer='not_a_serializer',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONMessageSerializerV3')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_WS_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_http_protocol_and_serializer(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='http',
                                                              message_serializer='graphsonv1untyped',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV1')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_http_protocol_and_serializer_invalid(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='http',
                                                              message_serializer='not_a_serializer',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV3')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_http_protocol_and_serializer_not_graphson_untyped(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='http',
                                                              message_serializer='graphbinaryv1',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV3')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_ws_protocol_and_serializer(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='ws',
                                                              message_serializer='graphbinaryv1',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphBinaryMessageSerializerV1')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_WS_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_ws_protocol_and_serializer_invalid(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='ws',
                                                              message_serializer='graphbinaryv1',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphBinaryMessageSerializerV1')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_WS_PROTOCOL)

    def test_configuration_gremlinsection_neptune_db_override_ws_protocol_and_serializer_http_only(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_DB_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='ws',
                                                              message_serializer='graphsonv3untyped',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_DB_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONMessageSerializerV3')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_WS_PROTOCOL)

    def test_configuration_gremlinsection_neptune_default_analytics(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME)
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV4')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_analytics_override_ws_protocol(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='ws',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV4')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_analytics_override_serializer(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME,
                               gremlin_section=GremlinSection(message_serializer='graphsonv1untyped',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV1')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_analytics_override_serializer_invalid(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME,
                               gremlin_section=GremlinSection(message_serializer='not_a_serializer',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV4')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_analytics_override_serializer_not_graphson_untyped(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME,
                               gremlin_section=GremlinSection(message_serializer='graphbinaryv1',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV4')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_neptune_analytics_override_http_protocol(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME,
                               gremlin_section=GremlinSection(connection_protocol='http',
                                                              include_protocol=True,
                                                              neptune_service=NEPTUNE_ANALYTICS_SERVICE_NAME),
                               )
        self.assertEqual(config.gremlin.traversal_source, 'g')
        self.assertEqual(config.gremlin.username, '')
        self.assertEqual(config.gremlin.password, '')
        self.assertEqual(config.gremlin.message_serializer, 'GraphSONUntypedMessageSerializerV4')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_gremlinsection_protocol_neptune_default_with_proxy(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               proxy_host='test_proxy')
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_WS_PROTOCOL)

    def test_configuration_gremlinsection_protocol_neptune_override_with_proxy(self):
        config = Configuration(self.neptune_host_reg,
                               self.port,
                               proxy_host='test_proxy',
                               gremlin_section=GremlinSection(connection_protocol='ws',
                                                              include_protocol=True)
                               )
        self.assertEqual(config.gremlin.connection_protocol, DEFAULT_HTTP_PROTOCOL)

    def test_configuration_neptune_service_default(self):
        config = Configuration(self.neptune_host_reg, self.port)
        self.assertEqual(config.neptune_service, self.neptune_service_db)

    def test_configuration_neptune_service_db(self):
        config = Configuration(self.neptune_host_reg, self.port, neptune_service=self.neptune_service_db)
        self.assertEqual(config.neptune_service, self.neptune_service_db)

    def test_configuration_neptune_service_graph(self):
        config = Configuration(self.neptune_host_reg, self.port, neptune_service=self.neptune_service_graph)
        self.assertEqual(config.neptune_service, self.neptune_service_graph)

    def test_configuration_neptune_service_db_short(self):
        config = Configuration(self.neptune_host_reg, self.port, neptune_service=self.neptune_service_db_short)
        self.assertEqual(config.neptune_service, self.neptune_service_db)

    def test_configuration_neptune_service_graph_short(self):
        config = Configuration(self.neptune_host_reg, self.port, neptune_service=self.neptune_service_graph_short)
        self.assertEqual(config.neptune_service, self.neptune_service_graph)

    def test_configuration_neptune_service_empty(self):
        config = Configuration(self.neptune_host_reg, self.port, neptune_service='')
        self.assertEqual(config.neptune_service, self.neptune_service_db)

    def test_configuration_neptune_service_invalid(self):
        config = Configuration(self.neptune_host_reg, self.port, neptune_service='rds')
        self.assertEqual(config.neptune_service, self.neptune_service_db)
