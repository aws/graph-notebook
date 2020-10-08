"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import argparse
import json
import os
from enum import Enum

from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider

DEFAULT_IAM_CREDENTIALS_PROVIDER = IAMAuthCredentialsProvider.ROLE
DEFAULT_CONFIG_LOCATION = os.path.expanduser('~/graph_notebook_config.json')


class AuthModeEnum(Enum):
    DEFAULT = "DEFAULT"
    IAM = "IAM"


DEFAULT_AUTH_MODE = AuthModeEnum.DEFAULT


class Configuration(object):
    def __init__(self, host: str, port: int,
                 auth_mode: AuthModeEnum = AuthModeEnum.DEFAULT,
                 iam_credentials_provider_type: IAMAuthCredentialsProvider = DEFAULT_IAM_CREDENTIALS_PROVIDER,
                 load_from_s3_arn='', ssl: bool = True, aws_region: str = 'us-east-1'):
        self.host = host
        self.port = port
        self.auth_mode = auth_mode
        self.iam_credentials_provider_type = iam_credentials_provider_type
        self.load_from_s3_arn = load_from_s3_arn
        self.ssl = ssl
        self.aws_region = aws_region

    def to_dict(self) -> dict:
        return {
            'host': self.host,
            'port': self.port,
            'auth_mode': self.auth_mode.value,
            'iam_credentials_provider_type': self.iam_credentials_provider_type.value,
            'load_from_s3_arn': self.load_from_s3_arn,
            'ssl': self.ssl,
            'aws_region': self.aws_region
        }

    def write_to_file(self, file_path=DEFAULT_CONFIG_LOCATION):
        data = self.to_dict()

        with open(file_path, mode='w+') as file:
            json.dump(data, file, indent=2)
        return


def generate_config(host, port, auth_mode, ssl, iam_credentials_provider_type, load_from_s3_arn, aws_region):
    use_ssl = False if ssl in [False, 'False', 'false', 'FALSE'] else True

    if iam_credentials_provider_type not in [IAMAuthCredentialsProvider.ENV,
                                             IAMAuthCredentialsProvider.ROLE]:
        iam_credentials_provider_type = DEFAULT_IAM_CREDENTIALS_PROVIDER

    config = Configuration(host, port, auth_mode, iam_credentials_provider_type, load_from_s3_arn, use_ssl, aws_region)
    return config


def generate_default_config():
    config = generate_config('change-me', 8182, AuthModeEnum.DEFAULT, True, DEFAULT_IAM_CREDENTIALS_PROVIDER, '',
                             'us-east-1')
    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="the host url to form a connection with", required=True)
    parser.add_argument("--port", help="the port to use when creating a connection", default="8182")
    parser.add_argument("--auth_mode", default=AuthModeEnum.DEFAULT.value,
                        help="type of authentication the cluster being connected to is using. Can be DEFAULT or IAM")
    parser.add_argument("--iam_credentials_provider", default='ROLE',
                        help="The mode used to obtain credentials for IAM Authentication. Can be ROLE or ENV")
    parser.add_argument("--ssl",
                        help="whether to make connections to the created endpoint with ssl or not [True|False]",
                        default=True)
    parser.add_argument("--config_destination", help="location to put generated config",
                        default=DEFAULT_CONFIG_LOCATION)
    parser.add_argument("--load_from_s3_arn", help="arn of role to use for bulk loader", default='')
    parser.add_argument("--aws_region", help="aws region your neptune cluster is in.", default='us-east-1')
    args = parser.parse_args()

    auth_mode_arg = args.auth_mode if args.auth_mode != '' else AuthModeEnum.DEFAULT.value
    iam_credentials_provider_arg = args.iam_credentials_provider if args.iam_credentials_provider != '' else IAMAuthCredentialsProvider.ROLE.value

    config = generate_config(args.host, int(args.port), AuthModeEnum(auth_mode_arg), args.ssl,
                             IAMAuthCredentialsProvider(iam_credentials_provider_arg),
                             args.load_from_s3_arn, args.aws_region)
    config.write_to_file(args.config_destination)

    exit(0)
