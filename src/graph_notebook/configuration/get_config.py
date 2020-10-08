"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json

from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.configuration.generate_config import DEFAULT_CONFIG_LOCATION, Configuration, AuthModeEnum


def get_config_from_dict(data: dict) -> Configuration:
    config = Configuration(host=data['host'], port=data['port'], auth_mode=AuthModeEnum(data['auth_mode']),
                           iam_credentials_provider_type=IAMAuthCredentialsProvider(
                               data['iam_credentials_provider_type']),
                           ssl=data['ssl'],
                           load_from_s3_arn=data['load_from_s3_arn'], aws_region=data['aws_region'])
    return config


def get_config(path: str = DEFAULT_CONFIG_LOCATION) -> Configuration:
    with open(path) as config_file:
        data = json.load(config_file)
        return get_config_from_dict(data)
