"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response

logging.basicConfig()
logger = logging.getLogger("opencypher")

OPENCYPHER_ACTION = 'openCypher'


def do_opencypher_query(query, host, port, use_ssl, request_param_generator, extra_headers=None):
    if extra_headers is None:
        extra_headers = {}

    if 'content-type' not in extra_headers:
        extra_headers['content-type'] = 'application/x-www-form-urlencoded'

    data = {
        'query': query
    }

    res = call_and_get_response('post', OPENCYPHER_ACTION, host, port, request_param_generator, use_ssl, data,
                                extra_headers)
    return res.json()
