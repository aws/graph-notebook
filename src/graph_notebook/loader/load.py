"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response

FORMAT_CSV = 'csv'
FORMAT_NTRIPLE = 'ntriples'
FORMAT_NQUADS = 'nquads'
FORMAT_RDFXML = 'rdfxml'
FORMAT_TURTLE = 'turtle'

VALID_FORMATS = [FORMAT_CSV, FORMAT_NTRIPLE, FORMAT_NQUADS, FORMAT_RDFXML, FORMAT_TURTLE]
LOADER_ACTION = 'loader'


def do_load(host, port, load_format, use_ssl, source, region, arn, fail_on_error, parallelism, update_single_cardinality, request_param_generator):
    payload = {
        'source': source,
        'format': load_format,
        'region': region,
        'failOnError': fail_on_error,
        'parallelism': parallelism,
        'updateSingleCardinalityProperties': update_single_cardinality
    }

    if arn != '':
        payload['iamRoleArn'] = arn

    res = call_and_get_response('post', LOADER_ACTION, host, port, request_param_generator, use_ssl, payload)
    return res.json()


def get_loader_jobs(host, port, use_ssl, request_param_generator):
    res = call_and_get_response('get', LOADER_ACTION, host, port, request_param_generator, use_ssl)
    return res.json()


def get_load_status(host, port, use_ssl, request_param_generator, id):
    payload = {
        'loadId': id
    }
    res = call_and_get_response('get', LOADER_ACTION, host, port, request_param_generator, use_ssl, payload)
    return res.json()


def cancel_load(host, port, use_ssl, request_param_generator, load_id):
    payload = {
        'loadId': load_id
    }

    res = call_and_get_response('get', LOADER_ACTION, host, port, request_param_generator, use_ssl, payload)
    return res.status_code == 200
