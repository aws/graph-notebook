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
    logger.debug(f'query={query}, endpoint={host}, port={port}')
    logger.debug('Here')
    data = {'query': query}

    res = call_and_get_response('post', OPENCYPHER_ACTION, host, port, request_param_generator, use_ssl, data,
                                extra_headers)
    try:
        content = res.json()  # attempt to return json, otherwise we will return the content string.
    except:
        content = res.content.decode('utf-8')
    return content


def do_opencypher_explain(query: str, host: str, port: str, use_ssl: bool, request_param_generator,
                          accept_type='text/html'):
    data = {
        'query': query,
        'explain': 'dynamic',
    }

    extra_headers = {
        'Accept': accept_type
    }

    res = call_and_get_response('post', OPENCYPHER_ACTION, host, port, request_param_generator, use_ssl, data,
                                extra_headers)
    return res.content.decode('utf-8')
