"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.request_param_generator.default_request_generator import DefaultRequestGenerator
from graph_notebook.request_param_generator.iam_request_generator import IamRequestGenerator
from graph_notebook.request_param_generator.sparql_request_generator import SPARQLRequestGenerator
from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider, credentials_provider_factory


def create_request_generator(mode: AuthModeEnum,
                             credentials_provider_mode: IAMAuthCredentialsProvider = IAMAuthCredentialsProvider.ROLE,
                             command: str = ''):

    if mode == AuthModeEnum.DEFAULT and command == 'sparql':
        return SPARQLRequestGenerator()
    elif mode == AuthModeEnum.IAM:
        credentials_provider_mode = credentials_provider_factory(credentials_provider_mode)
        return IamRequestGenerator(credentials_provider_mode)
    else:
        return DefaultRequestGenerator()
