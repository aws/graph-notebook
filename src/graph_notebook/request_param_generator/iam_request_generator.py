"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.authentication.iam_headers import make_signed_request


class IamRequestGenerator(object):
    def __init__(self, credentials_provider):
        self.credentials_provider = credentials_provider

    def generate_request_params(self, method, action, query, host, port, protocol, headers=None):
        credentials = self.credentials_provider.get_iam_credentials()
        if protocol in ['https', 'wss']:
            use_ssl = True
        else:
            use_ssl = False

        return make_signed_request(method, action, query, host, port, credentials.key, credentials.secret, credentials.region, use_ssl, credentials.token, additional_headers=headers)
