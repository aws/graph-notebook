"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

from graph_notebook.gremlin.client_provider.default_client import ClientProvider
from graph_notebook.request_param_generator.default_request_generator import DefaultRequestGenerator
from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response

logging.basicConfig()
logger = logging.getLogger("gremlin")


def do_gremlin_query(query_str, host, port, use_ssl, client_provider=ClientProvider()):
    c = client_provider.get_client(host, port, use_ssl)

    try:
        result = c.submit(query_str)
        future_results = result.all()
        results = future_results.result()
    except Exception as e:
        raise e  # let the upstream decide what to do with this error.
    finally:
        c.close()  # no matter the outcome we need to close the websocket connection

    return results


def do_gremlin_explain(query_str, host, port, use_ssl, request_param_generator=DefaultRequestGenerator()):
    data = {
        'gremlin': query_str
    }

    action = 'gremlin/explain'
    res = call_and_get_response('get', action, host, port, request_param_generator, use_ssl, data)
    content = res.content.decode('utf-8')
    result = {
        'explain': content
    }
    return result


def do_gremlin_profile(query_str, host, port, use_ssl, request_param_generator=DefaultRequestGenerator()):
    data = {
        'gremlin': query_str
    }

    action = 'gremlin/profile'
    res = call_and_get_response('get', action, host, port, request_param_generator, use_ssl, data)
    content = res.content.decode('utf-8').strip(' ')
    result = {
        'profile': content
    }

    return result
