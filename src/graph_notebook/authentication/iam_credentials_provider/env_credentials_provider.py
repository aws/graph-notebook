"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os

from graph_notebook.authentication.iam_credentials_provider.credentials_provider import CredentialsProviderBase, \
    Credentials

ACCESS_ENV_KEY = 'AWS_ACCESS_KEY_ID'
SECRET_ENV_KEY = 'AWS_SECRET_ACCESS_KEY'
REGION_ENV_KEY = 'AWS_REGION'
AWS_TOKEN_ENV_KEY = 'AWS_SESSION_TOKEN'


class EnvCredentialsProvider(CredentialsProviderBase):
    def __init__(self):
        self.creds = Credentials(key='', secret='', region='', token='')
        self.loaded = False

    def load_iam_credentials(self):
        access_key = os.environ.get(ACCESS_ENV_KEY, '')
        secret_key = os.environ.get(SECRET_ENV_KEY, '')
        region = os.environ.get(REGION_ENV_KEY, '')
        token = os.environ.get(AWS_TOKEN_ENV_KEY, '')
        self.creds = Credentials(access_key, secret_key, region, token)
        self.loaded = True
        return

    def get_iam_credentials(self) -> Credentials:
        if not self.loaded:
            self.load_iam_credentials()

        return self.creds
