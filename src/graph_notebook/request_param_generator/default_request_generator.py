"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

class DefaultRequestGenerator(object):
    @staticmethod
    def generate_request_params(method, action, query, host, port, protocol, headers=None):
        return {
            'method': method,
            'url': f'{protocol}://{host}:{port}/{action}',
            'headers': headers,
            'params': query,
        }
