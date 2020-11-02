"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import requests


def call_and_get_response(method: str, action: str, host: str, port: str, request_param_generator, use_ssl: bool, query='', extra_headers={}):
    method = method.upper()
    protocol = 'https' if use_ssl else 'http'

    request_params = request_param_generator.generate_request_params(method=method, action=action, query=query, host=host, port=port, protocol=protocol, headers=extra_headers)
    headers = request_params['headers'] if request_params['headers'] is not None else {}

    if method == 'GET':
        res = requests.get(url=request_params['url'], params=request_params['params'], headers=headers)
    elif method == 'DELETE':
        res = requests.delete(url=request_params['url'], params=request_params['params'], headers=headers)
    elif method == 'POST':
        res = requests.post(url=request_params['url'], data=request_params['params'], headers=headers)
    else:
        raise NotImplementedError(f'Use of method {method} has not been implemented in call_and_get_response')

    res.raise_for_status()
    return res
