"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from botocore.session import get_session

from graph_notebook.configuration.generate_config import Configuration, AuthModeEnum
from graph_notebook.configuration.get_config import get_config
from graph_notebook.neptune.client import ClientBuilder
from test.integration.NeptuneIntegrationWorkflowSteps import TEST_CONFIG_PATH


def setup_client_builder(config: Configuration) -> ClientBuilder:
    if "amazonaws.com" in config.host:
        builder = ClientBuilder() \
            .with_host(config.host) \
            .with_port(config.port) \
            .with_region(config.aws_region) \
            .with_tls(config.ssl) \
            .with_proxy_host(config.proxy_host) \
            .with_proxy_port(config.proxy_port) \
            .with_sparql_path(config.sparql.path) \
            .with_gremlin_traversal_source(config.gremlin.traversal_source) \
            .with_neo4j_login(config.neo4j.username, config.neo4j.password, config.neo4j.auth)
        if config.auth_mode == AuthModeEnum.IAM:
            builder = builder.with_iam(get_session())
    else:
        builder = ClientBuilder() \
            .with_host(config.host) \
            .with_port(config.port) \
            .with_tls(config.ssl) \
            .with_proxy_host(config.proxy_host) \
            .with_proxy_port(config.proxy_port) \
            .with_sparql_path(config.sparql.path) \
            .with_gremlin_traversal_source(config.gremlin.traversal_source) \
            .with_neo4j_login(config.neo4j.username, config.neo4j.password, config.neo4j.auth)

    return builder


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = get_config(TEST_CONFIG_PATH)
        cls.client_builder = setup_client_builder(cls.config)

    def setUp(self) -> None:
        self.client = self.client_builder.build()
