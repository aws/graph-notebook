"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import requests

from graph_notebook.authentication.iam_credentials_provider.credentials_provider import CredentialsProviderBase, \
    Credentials

region_url = 'http://169.254.169.254/latest/meta-data/placement/availability-zone'
iam_url = 'http://169.254.169.254/latest/meta-data/iam/security-credentials/neptune-db'


class MetadataCredentialsProvider(CredentialsProviderBase):
    def __init__(self):
        res = requests.get(region_url)
        zone = res.content.decode('utf-8')
        region = zone[0:len(zone) - 1]
        self.region = region

    def get_iam_credentials(self) -> Credentials:
        res = requests.get(iam_url)
        if res.status_code != 200:
            raise Exception(f'unable to get iam credentials {res.content}')

        js = res.json()
        creds = Credentials(key=js['AccessKeyId'], secret=js['SecretAccessKey'], token=js['Token'], region=self.region)
        return creds
