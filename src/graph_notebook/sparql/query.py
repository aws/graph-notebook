"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

from SPARQLWrapper import SPARQLWrapper
from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response

logging.basicConfig()
logger = logging.getLogger("sparql")

ACTION_TO_QUERY_TYPE = {
    'sparql': 'application/sparql-query',
    'sparqlupdate': 'application/sparql-update'
}

SPARQL_ACTION = 'sparql'


def get_query_type(query):
    s = SPARQLWrapper('')
    s.setQuery(query)
    return s.queryType


def query_type_to_action(query_type):
    query_type = query_type.upper()
    if query_type in ['SELECT', 'CONSTRUCT', 'ASK', 'DESCRIBE']:
        return 'sparql'
    else:
        # TODO: check explicitly for all query types, raise exception for invalid query
        return 'sparqlupdate'


def do_sparql_query(query, host, port, use_ssl, request_param_generator, extra_headers=None):
    if extra_headers is None:
        extra_headers = {}
    logger.debug(f'query={query}, endpoint={host}, port={port}')
    query_type = get_query_type(query)
    action = query_type_to_action(query_type)

    data = {}
    if action == 'sparql':
        data['query'] = query
    elif action == 'sparqlupdate':
        data['update'] = query

    res = call_and_get_response('post', SPARQL_ACTION, host, port, request_param_generator, use_ssl, data, extra_headers)
    try:
        content = res.json()  # attempt to return json, otherwise we will return the content string.
    except Exception:
        content = res.content.decode('utf-8')
    return content


def do_sparql_explain(query: str, host: str, port: str, use_ssl: bool, request_param_generator,
                      accept_type='text/html'):
    query_type = get_query_type(query)
    action = query_type_to_action(query_type)

    data = {
        'explain': 'dynamic',
    }

    if action == 'sparql':
        data['query'] = query
    elif action == 'sparqlupdate':
        data['update'] = query

    extra_headers = {
        'Accept': accept_type
    }

    res = call_and_get_response('post', SPARQL_ACTION, host, port, request_param_generator, use_ssl, data,
                                extra_headers)
    return res.content.decode('utf-8')
