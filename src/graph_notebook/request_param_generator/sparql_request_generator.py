"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""


class SPARQLRequestGenerator(object):
    @staticmethod
    def generate_request_params(method, action, query, host, port, protocol, headers=None):
        if headers is None:
            headers = {}

        if 'Content-Type' not in headers:
            headers['Content-Type'] = "application/x-www-form-urlencoded"

        url = f'{protocol}://{host}:{port}/{action}'
        return {
            'method': method,
            'url': url,
            'headers': headers,
            'params': query,
        }
