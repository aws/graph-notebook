"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from botocore.session import get_session

from graph_notebook.configuration.generate_config import Configuration
from graph_notebook.neptune.client import Client, ClientBuilder


def setup_iam_client(config: Configuration) -> Client:
    client = ClientBuilder() \
        .with_host(config.host) \
        .with_port(config.port) \
        .with_neptune_service(config.neptune_service) \
        .with_region(config.aws_region) \
        .with_tls(config.ssl) \
        .with_ssl_verify(config.ssl_verify) \
        .with_proxy_host(config.proxy_host) \
        .with_proxy_port(config.proxy_port) \
        .with_sparql_path(config.sparql.path) \
        .with_gremlin_traversal_source(config.gremlin.traversal_source) \
        .with_gremlin_login(config.gremlin.username, config.gremlin.password) \
        .with_gremlin_serializer(config.gremlin.message_serializer) \
        .with_neo4j_login(config.neo4j.username, config.neo4j.password, config.neo4j.auth, config.neo4j.database) \
        .with_iam(get_session()) \
        .build()

    assert client.host == config.host
    assert client.port == config.port
    assert client.neptune_service == config.neptune_service
    assert client.region == config.aws_region
    assert client.proxy_host == config.proxy_host
    assert client.proxy_port == config.proxy_port
    assert client.sparql_path == config.sparql.path
    assert client.gremlin_traversal_source == config.gremlin.traversal_source
    assert client.gremlin_username == config.gremlin.username
    assert client.gremlin_password == config.gremlin.password
    assert client.gremlin_serializer == config.gremlin.message_serializer
    assert client.neo4j_username == config.neo4j.username
    assert client.neo4j_password == config.neo4j.password
    assert client.neo4j_auth == config.neo4j.auth
    assert client.neo4j_database == config.neo4j.database
    assert client.ssl is config.ssl
    assert client.ssl_verify is config.ssl_verify
    return client
