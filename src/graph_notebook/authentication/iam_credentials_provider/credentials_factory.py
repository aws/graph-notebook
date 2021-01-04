"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from enum import Enum

from graph_notebook.authentication.iam_credentials_provider.credentials_provider import CredentialsProviderBase
from graph_notebook.authentication.iam_credentials_provider.env_credentials_provider import EnvCredentialsProvider
from graph_notebook.authentication.iam_credentials_provider.ec2_metadata_credentials_provider import MetadataCredentialsProvider


class IAMAuthCredentialsProvider(Enum):
    ROLE = "ROLE"
    ENV = "ENV"


def credentials_provider_factory(mode: IAMAuthCredentialsProvider) -> CredentialsProviderBase:
    if mode == IAMAuthCredentialsProvider.ENV:
        return EnvCredentialsProvider()
    elif mode == IAMAuthCredentialsProvider.ROLE:
        return MetadataCredentialsProvider()
    else:
        raise NotImplementedError(f'the provided mode of {mode} has not been implemented by credentials_provider_factory')
