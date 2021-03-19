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

PARALLELISM_LOW = 'LOW'
PARALLELISM_MEDIUM = 'MEDIUM'
PARALLELISM_HIGH = 'HIGH'
PARALLELISM_OVERSUBSCRIBE = 'OVERSUBSCRIBE'

MODE_RESUME = 'RESUME'
MODE_NEW = 'NEW'
MODE_AUTO = 'AUTO'

LOAD_JOB_MODES = [MODE_RESUME, MODE_NEW, MODE_AUTO]
VALID_FORMATS = [FORMAT_CSV, FORMAT_NTRIPLE, FORMAT_NQUADS, FORMAT_RDFXML, FORMAT_TURTLE]
PARALLELISM_OPTIONS = [PARALLELISM_LOW, PARALLELISM_MEDIUM, PARALLELISM_HIGH, PARALLELISM_OVERSUBSCRIBE]
LOADER_ACTION = 'loader'

FINAL_LOAD_STATUSES = ['LOAD_COMPLETED',
                       'LOAD_COMMITTED_W_WRITE_CONFLICTS',
                       'LOAD_CANCELLED_BY_USER',
                       'LOAD_CANCELLED_DUE_TO_ERRORS',
                       'LOAD_FAILED',
                       'LOAD_UNEXPECTED_ERROR',
                       'LOAD_DATA_DEADLOCK',
                       'LOAD_DATA_FAILED_DUE_TO_FEED_MODIFIED_OR_DELETED',
                       'LOAD_S3_READ_ERROR',
                       'LOAD_S3_ACCESS_DENIED_ERROR',
                       'LOAD_IN_QUEUE',
                       'LOAD_FAILED_BECAUSE_DEPENDENCY_NOT_SATISFIED',
                       'LOAD_FAILED_INVALID_REQUEST', ]

def do_load(host, port, load_format, use_ssl, source, region, arn, mode, fail_on_error, parallelism,
            update_single_cardinality, queue_request, dependencies, request_param_generator):

    payload = {
        'source': source,
        'format': load_format,
        'mode': mode,
        'region': region,
        'failOnError': fail_on_error,
        'parallelism': parallelism,
        'updateSingleCardinalityProperties': update_single_cardinality,
        'queueRequest': queue_request
    }

    if arn != '':
        payload['iamRoleArn'] = arn

    if dependencies != '':
        payload['dependencies'] = dependencies

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
