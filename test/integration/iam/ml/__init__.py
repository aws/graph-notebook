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
        .with_region(config.aws_region) \
        .with_tls(config.ssl) \
        .with_proxy_host(config.proxy_host) \
        .with_proxy_port(config.proxy_port) \
        .with_sparql_path(config.sparql.path) \
        .with_gremlin_traversal_source(config.gremlin.traversal_source) \
        .with_iam(get_session()) \
        .build()

    assert client.host == config.host
    assert client.port == config.port
    assert client.region == config.aws_region
    assert client.proxy_host == config.proxy_host
    assert client.proxy_port == config.proxy_port
    assert client.sparql_path == config.sparql.path
    assert client.gremlin_traversal_source == config.gremlin.traversal_source
    assert client.ssl is config.ssl
    return client
