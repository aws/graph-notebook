"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import botocore.session
import requests


from graph_notebook.authentication.iam_credentials_provider.credentials_provider import CredentialsProviderBase, \
    Credentials

region_url = 'http://169.254.169.254/latest/meta-data/placement/availability-zone'


class MetadataCredentialsProvider(CredentialsProviderBase):
    def __init__(self):
        res = requests.get(region_url)
        zone = res.content.decode('utf-8')
        region = zone[0:len(zone) - 1]
        self.region = region

    def get_iam_credentials(self) -> Credentials:
        session = botocore.session.get_session()
        creds = session.get_credentials()
        return Credentials(key=creds.access_key, secret=creds.secret_key, token=creds.token, region=self.region)
