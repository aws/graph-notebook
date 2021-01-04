"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import graph_notebook.gremlin.client_provider.graphsonV3d0_MapType_objectify_patch  # noqa F401
import hashlib
import hmac
import logging

from gremlin_python.driver import client
from gremlin_python.driver.client import Client
from tornado import httpclient

from graph_notebook.authentication.iam_credentials_provider.credentials_provider import CredentialsProviderBase
from graph_notebook.authentication.iam_headers import make_signed_request

logging.basicConfig()
logger = logging.getLogger("iam_client")


def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature_key(key, date_stamp, region_name, service_name):
    k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing


class IamClientProvider(object):
    def __init__(self, credentials_provider: CredentialsProviderBase):
        self.credentials_provider = credentials_provider

    def get_client(self, host, port, use_ssl) -> Client:
        credentials = self.credentials_provider.get_iam_credentials()
        request_params = make_signed_request('get', 'gremlin', '', host, port, credentials.key,
                                             credentials.secret, credentials.region, use_ssl,
                                             credentials.token)
        ws_url = request_params['url'].strip('/').replace('http', 'ws')
        signed_ws_request = httpclient.HTTPRequest(ws_url, headers=request_params['headers'])

        try:
            c = client.Client(signed_ws_request, 'g')
            return c
        # TODO: handle exception explicitly
        except Exception as e:
            logger.error(f'error while creating client {e}')
            raise e
