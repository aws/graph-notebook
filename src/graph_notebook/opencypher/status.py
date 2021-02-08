"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response

OPENCYPHER_STATUS_ACTION = 'opencypher/status'


def do_opencypher_status(query_id, host, port, use_ssl, mode, request_param_generator):
    data = {}
    if query_id is not '':
        data['queryId'] = query_id

    headers = {}
    if mode == AuthModeEnum.DEFAULT:
        """Add correct content-type header for the request.
        This is needed because call_and_get_response requires custom headers to be set.
        """
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    res = call_and_get_response('post', OPENCYPHER_STATUS_ACTION, host, port, request_param_generator, use_ssl, data,
                                headers)
    try:
        content = res.json()  # attempt to return json, otherwise we will return the content string.
    except:
        """When a invalid UUID is supplied, status servlet returns an empty string.
        See https://sim.amazon.com/issues/NEPTUNE-16137
        """
        content = 'UUID is invalid.'
    return content


'''
# I am not sure if this exists yet
def do_sparql_cancel(query_id, silent, host, port, use_ssl, mode, request_param_generator):
    if type(query_id) is not str or query_id is '':
        raise ValueError("query id must be a non-empty string")

    data = {'cancelQuery': True, 'queryId': query_id, 'silent': silent}

    headers = {}
    if mode == AuthModeEnum.DEFAULT:
        """Add correct content-type header for the request.
        This is needed because call_and_get_response requires custom headers to be set.
        """
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    res = call_and_get_response('post', OPENCYPHER_STATUS_ACTION, host, port, request_param_generator, use_ssl, data,
                                headers)
    try:
        content = res.json()
    except:
        """When a invalid UUID is supplied, status servlet returns an empty string.
        See https://sim.amazon.com/issues/NEPTUNE-16137
        """
        content = 'UUID is invalid.'
    return content
'''
