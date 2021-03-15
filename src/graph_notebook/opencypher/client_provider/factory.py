"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.authentication.iam_credentials_provider.credentials_factory import credentials_provider_factory, \
    IAMAuthCredentialsProvider
from graph_notebook.opencypher.client_provider.default_client import CypherClientProvider
from graph_notebook.opencypher.client_provider.iam_client import IAMCypherClientProvider


def create_opencypher_client_provider(mode: AuthModeEnum, credentials_provider_mode: IAMAuthCredentialsProvider = IAMAuthCredentialsProvider.ROLE):
    if mode == AuthModeEnum.DEFAULT:
        return CypherClientProvider()
    elif mode == AuthModeEnum.IAM:
        credentials_provider = credentials_provider_factory(credentials_provider_mode)
        return IAMCypherClientProvider(credentials_provider)
    else:
        raise NotImplementedError(f"invalid client mode {mode} provided")
