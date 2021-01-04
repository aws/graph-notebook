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

        action_segment = 'sparql' if not action.endswith('sparql') else action
        url = f'{protocol}://{host}:{port}/{action_segment}'
        return {
            'method': method,
            'url': url,
            'headers': headers,
            'params': query,
        }
