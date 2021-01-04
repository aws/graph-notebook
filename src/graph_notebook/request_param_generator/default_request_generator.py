"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""


class DefaultRequestGenerator(object):
    @staticmethod
    def generate_request_params(method, action, query, host, port, protocol, headers=None):
        url = f'{protocol}://{host}:{port}/{action}' if port != '' else f'{protocol}://{host}/{action}'
        params = {
            'method': method,
            'url': url,
            'headers': headers,
            'params': query,
        }

        return params
