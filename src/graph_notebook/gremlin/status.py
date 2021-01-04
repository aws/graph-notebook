"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response

GREMLIN_STATUS_ACTION = 'gremlin/status'


def do_gremlin_status(host, port, use_ssl, mode, request_param_generator, query_id: str, include_waiting: bool):
    data = {'includeWaiting': include_waiting}
    if query_id != '':
        data['queryId'] = query_id

    headers = {}
    if mode == AuthModeEnum.DEFAULT:
        """Add correct content-type header for the request.
        This is needed because call_and_get_response requires custom headers to be set.
        """
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    res = call_and_get_response('post', GREMLIN_STATUS_ACTION, host, port, request_param_generator, use_ssl, data,
                                headers)
    content = res.json()
    return content


def do_gremlin_cancel(host, port, use_ssl, mode, request_param_generator, query_id):
    if type(query_id) != str or query_id == '':
        raise ValueError("query id must be a non-empty string")

    data = {'cancelQuery': True, 'queryId': query_id}

    headers = {}
    if mode == AuthModeEnum.DEFAULT:
        """Add correct content-type header for the request.
        This is needed because call_and_get_response requires custom headers to be set.
        """
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    res = call_and_get_response('post', GREMLIN_STATUS_ACTION, host, port, request_param_generator, use_ssl, data,
                                headers)
    content = res.json()
    return content
