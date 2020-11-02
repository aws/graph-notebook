"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response

SPARQL_STATUS_ACTION = 'sparql/status'


def do_sparql_status(host, port, use_ssl, request_param_generator, query_id=None):
    data = {}
    if query_id != '' and query_id is not None:
        data['queryId'] = query_id

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = call_and_get_response('post', SPARQL_STATUS_ACTION, host, port, request_param_generator, use_ssl, data,
                                headers)
    try:
        content = res.json()  # attempt to return json, otherwise we will return the content string.
    except Exception:
        """When a invalid UUID is supplied, status servlet returns an empty string.
        See https://sim.amazon.com/issues/NEPTUNE-16137
        """
        content = 'UUID is invalid.'
    return content


def do_sparql_cancel(host, port, use_ssl, request_param_generator, query_id, silent=False):
    if type(query_id) is not str or query_id == '':
        raise ValueError("query id must be a non-empty string")

    data = {'cancelQuery': True, 'queryId': query_id, 'silent': silent}

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = call_and_get_response('post', SPARQL_STATUS_ACTION, host, port, request_param_generator, use_ssl, data,
                                headers)
    try:
        content = res.json()
    except Exception:
        """When a invalid UUID is supplied, status servlet returns an empty string.
        See https://sim.amazon.com/issues/NEPTUNE-16137
        """
        content = 'UUID is invalid.'
    return content
