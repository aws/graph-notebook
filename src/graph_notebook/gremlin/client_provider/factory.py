"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.gremlin.client_provider.default_client import ClientProvider
from graph_notebook.gremlin.client_provider.iam_client import IamClientProvider
from graph_notebook.authentication.iam_credentials_provider.credentials_factory import credentials_provider_factory, \
    IAMAuthCredentialsProvider


def create_client_provider(mode: AuthModeEnum,
                           credentials_provider_mode: IAMAuthCredentialsProvider = IAMAuthCredentialsProvider.ROLE):
    if mode == AuthModeEnum.DEFAULT:
        return ClientProvider()
    elif mode == AuthModeEnum.IAM:
        credentials_provider = credentials_provider_factory(credentials_provider_mode)
        return IamClientProvider(credentials_provider)
    else:
        raise NotImplementedError(f"invalid client mode {mode} provided")
