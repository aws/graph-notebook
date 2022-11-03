"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import argparse
import json
import os
from enum import Enum

from graph_notebook.neptune.client import SPARQL_ACTION, DEFAULT_PORT, DEFAULT_REGION, DEFAULT_GREMLIN_SERIALIZER, \
    DEFAULT_GREMLIN_TRAVERSAL_SOURCE, DEFAULT_NEO4J_USERNAME, DEFAULT_NEO4J_PASSWORD, DEFAULT_NEO4J_DATABASE, \
    NEPTUNE_CONFIG_HOST_IDENTIFIERS, is_allowed_neptune_host, false_str_variants, \
    GRAPHSONV3_VARIANTS, GRAPHSONV2_VARIANTS, GRAPHBINARYV1_VARIANTS

DEFAULT_CONFIG_LOCATION = os.path.expanduser('~/graph_notebook_config.json')


class AuthModeEnum(Enum):
    DEFAULT = "DEFAULT"
    IAM = "IAM"


DEFAULT_AUTH_MODE = AuthModeEnum.DEFAULT


class SparqlSection(object):
    """
    Used for sparql-specific settings in a notebook's configuration
    """

    def __init__(self, path: str = SPARQL_ACTION, endpoint_prefix: str = ''):
        """
        :param path: used to specify the base-path of the api being connected to do get to its
                     corresponding sparql endpoint.
        """

        if endpoint_prefix != '':
            print('endpoint_prefix has been deprecated and will be removed in version 2.0.20 or greater.')
            if path == '':
                path = f'{endpoint_prefix}/sparql'

        self.path = path

    def to_dict(self):
        return self.__dict__


class GremlinSection(object):
    """
    Used for gremlin-specific settings in a notebook's configuration
    """

    def __init__(self, traversal_source: str = '', username: str = '', password: str = '',
                 message_serializer: str = ''):
        """
        :param traversal_source: used to specify the traversal source for a Gremlin traversal, in the case that we are
        connected to an endpoint that can access multiple graphs.
        :param username: used to specify a username for authenticating to Gremlin Server, if the endpoint supports it.
        :param password: used to specify a password for authenticating to Gremlin Server, if the endpoint supports it.
        :param message_serializer: used to specify a serializer for encoding the data to and from Gremlin Server.
        """

        if traversal_source == '':
            traversal_source = DEFAULT_GREMLIN_TRAVERSAL_SOURCE

        serializer_lower = message_serializer.lower()
        if serializer_lower == '':
            message_serializer = DEFAULT_GREMLIN_SERIALIZER
        elif serializer_lower in GRAPHSONV3_VARIANTS:
            message_serializer = 'graphsonv3'
        elif serializer_lower in GRAPHSONV2_VARIANTS:
            message_serializer = 'graphsonv2'
        elif serializer_lower in GRAPHBINARYV1_VARIANTS:
            message_serializer = 'graphbinaryv1'
        else:
            print(f'Invalid Gremlin serializer specified, defaulting to graphsonv3. '
                  f'Valid serializers: [graphsonv3, graphsonv2, graphbinaryv1].')
            message_serializer = DEFAULT_GREMLIN_SERIALIZER


        self.traversal_source = traversal_source
        self.username = username
        self.password = password
        self.message_serializer = message_serializer

    def to_dict(self):
        return self.__dict__


class Neo4JSection(object):
    """
    Used for Neo4J-specific settings in a notebook's configuration
    """

    def __init__(self, username: str = '', password: str = '', auth: bool = True, database: str = ''):
        """
        :param username: login user for the Neo4J endpoint
        :param password: login password for the Neo4J endpoint
        """

        if username == '':
            username = DEFAULT_NEO4J_USERNAME
        if password == '':
            password = DEFAULT_NEO4J_PASSWORD
        if database == '':
            database = DEFAULT_NEO4J_DATABASE

        self.username = username
        self.password = password
        self.auth = False if auth in [False, 'False', 'false', 'FALSE'] else True
        self.database = database

    def to_dict(self):
        return self.__dict__


class Configuration(object):
    def __init__(self, host: str, port: int,
                 auth_mode: AuthModeEnum = DEFAULT_AUTH_MODE,
                 load_from_s3_arn='', ssl: bool = True, ssl_verify: bool = True, aws_region: str = DEFAULT_REGION,
                 proxy_host: str = '', proxy_port: int = DEFAULT_PORT,
                 sparql_section: SparqlSection = None, gremlin_section: GremlinSection = None,
                 neo4j_section: Neo4JSection = None,
                 neptune_hosts: list = NEPTUNE_CONFIG_HOST_IDENTIFIERS):
        self._host = host.strip()
        self.port = port
        self.ssl = ssl
        self.ssl_verify = ssl_verify
        self._proxy_host = proxy_host.strip()
        self.proxy_port = proxy_port
        self.sparql = sparql_section if sparql_section is not None else SparqlSection()

        is_neptune_host = is_allowed_neptune_host(hostname=self.host, host_allowlist=neptune_hosts) \
            or is_allowed_neptune_host(hostname=self.proxy_host, host_allowlist=neptune_hosts)
        if is_neptune_host:
            self.is_neptune_config = True
            self.auth_mode = auth_mode
            self.load_from_s3_arn = load_from_s3_arn
            self.aws_region = aws_region
            self.gremlin = GremlinSection()
            self.neo4j = Neo4JSection()
        else:
            self.is_neptune_config = False
            self.gremlin = gremlin_section if gremlin_section is not None else GremlinSection()
            self.neo4j = neo4j_section if neo4j_section is not None else Neo4JSection()

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value: str):
        self._host = value.strip()

    @property
    def proxy_host(self):
        return self._proxy_host

    @proxy_host.setter
    def proxy_host(self, value: str):
        self._proxy_host = value.strip()

    def to_dict(self) -> dict:
        if self.is_neptune_config:
            return {
                'host': self.host,
                'port': self.port,
                'proxy_host': self.proxy_host,
                'proxy_port': self.proxy_port,
                'auth_mode': self.auth_mode.value,
                'load_from_s3_arn': self.load_from_s3_arn,
                'ssl': self.ssl,
                'ssl_verify': self.ssl_verify,
                'aws_region': self.aws_region,
                'sparql': self.sparql.to_dict(),
                'gremlin': self.gremlin.to_dict(),
                'neo4j': self.neo4j.to_dict()
            }
        else:
            return {
                'host': self.host,
                'port': self.port,
                'proxy_host': self.proxy_host,
                'proxy_port': self.proxy_port,
                'ssl': self.ssl,
                'ssl_verify': self.ssl_verify,
                'sparql': self.sparql.to_dict(),
                'gremlin': self.gremlin.to_dict(),
                'neo4j': self.neo4j.to_dict()
            }

    def write_to_file(self, file_path=DEFAULT_CONFIG_LOCATION):
        data = self.to_dict()

        with open(file_path, mode='w+') as file:
            json.dump(data, file, indent=2)
        return


def generate_config(host, port, auth_mode: AuthModeEnum = AuthModeEnum.DEFAULT, ssl: bool = True,
                    ssl_verify: bool = True, load_from_s3_arn='',
                    aws_region: str = DEFAULT_REGION, proxy_host: str = '', proxy_port: int = DEFAULT_PORT,
                    sparql_section: SparqlSection = SparqlSection(), gremlin_section: GremlinSection = GremlinSection(),
                    neo4j_section=Neo4JSection(), neptune_hosts: list = NEPTUNE_CONFIG_HOST_IDENTIFIERS):
    use_ssl = False if ssl in false_str_variants else True
    verify_ssl = False if ssl_verify in false_str_variants else True
    c = Configuration(host, port, auth_mode, load_from_s3_arn, use_ssl, verify_ssl, aws_region, proxy_host, proxy_port,
                      sparql_section, gremlin_section, neo4j_section, neptune_hosts)
    return c


def generate_default_config():
    c = generate_config('change-me', 8182, AuthModeEnum.DEFAULT, True, True, '', DEFAULT_REGION)
    return c


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="the host url to form a connection with", required=True)
    parser.add_argument("--port", help="the port to use when creating a connection", default=8182)
    parser.add_argument("--auth_mode", default=AuthModeEnum.DEFAULT.value,
                        help="type of authentication the cluster being connected to is using. Can be DEFAULT or IAM")
    parser.add_argument("--ssl",
                        help="whether to make connections to the created endpoint with ssl or not [True|False]",
                        default=True)
    parser.add_argument("--ssl-verify",
                        help="whether to verify the server's TLS certificate or not [True|False]",
                        default=True)
    # TODO: Remove this after we fix the LC script in S3.
    parser.add_argument("--iam_credentials_provider", default='ROLE',
                        help="The mode used to obtain credentials for IAM Authentication. Can be ROLE or ENV")
    parser.add_argument("--config_destination", help="location to put generated config",
                        default=DEFAULT_CONFIG_LOCATION)
    parser.add_argument("--load_from_s3_arn", help="arn of role to use for bulk loader", default='')
    parser.add_argument("--aws_region", help="aws region your ml cluster is in.", default=DEFAULT_REGION)
    parser.add_argument("--proxy_host", help="the proxy host url to route a connection through", default='')
    parser.add_argument("--proxy_port", help="the proxy port to use when creating proxy connection", default=8182)
    parser.add_argument("--neptune_hosts", nargs="*",
                        help="list of host snippets to use for identifying neptune endpoints",
                        default=NEPTUNE_CONFIG_HOST_IDENTIFIERS)
    parser.add_argument("--sparql_path", help="the namespace path to append to the SPARQL endpoint",
                        default=SPARQL_ACTION)
    parser.add_argument("--gremlin_traversal_source", help="the traversal source to use for Gremlin queries",
                        default=DEFAULT_GREMLIN_TRAVERSAL_SOURCE)
    parser.add_argument("--gremlin_username", help="the username to use when creating Gremlin connections", default='')
    parser.add_argument("--gremlin_password", help="the password to use when creating Gremlin connections", default='')
    parser.add_argument("--gremlin_serializer",
                        help="the serializer to use as the encoding format when creating Gremlin connections",
                        default=DEFAULT_GREMLIN_SERIALIZER)
    parser.add_argument("--neo4j_username", help="the username to use for Neo4J connections",
                        default=DEFAULT_NEO4J_USERNAME)
    parser.add_argument("--neo4j_password", help="the password to use for Neo4J connections",
                        default=DEFAULT_NEO4J_PASSWORD)
    parser.add_argument("--neo4j_auth", help="whether to use auth for Neo4J connections or not [True|False]",
                        default=True)
    parser.add_argument("--neo4j_database", help="the name of the database to use for Neo4J",
                        default=DEFAULT_NEO4J_DATABASE)
    args = parser.parse_args()

    auth_mode_arg = args.auth_mode if args.auth_mode != '' else AuthModeEnum.DEFAULT.value
    config = generate_config(args.host, int(args.port), AuthModeEnum(auth_mode_arg), args.ssl, args.ssl_verify,
                             args.load_from_s3_arn, args.aws_region, args.proxy_host, int(args.proxy_port),
                             SparqlSection(args.sparql_path, ''),
                             GremlinSection(args.gremlin_traversal_source, args.gremlin_username,
                                            args.gremlin_password, args.gremlin_serializer),
                             Neo4JSection(args.neo4j_username, args.neo4j_password,
                                          args.neo4j_auth, args.neo4j_database),
                             args.neptune_hosts)
    config.write_to_file(args.config_destination)

    exit(0)
