"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response
from graph_notebook.request_param_generator.default_request_generator import DefaultRequestGenerator


def get_status(host, port, use_ssl, request_param_generator=DefaultRequestGenerator()):
    res = call_and_get_response('get', 'status', host, port, request_param_generator, use_ssl)
    return res.json()
