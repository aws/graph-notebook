"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json
import requests
from requests_aws4auth import AWS4Auth

from graph_notebook.authentication.iam_credentials_provider.credentials_provider import Credentials
from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response

EXPORT_SERVICE_NAME = 'execute-api'
EXPORT_ACTION = 'neptune-export'
EXTRA_HEADERS = {'content-type': 'application/json'}
UPDATE_DELAY_SECONDS = 60


def start_export(export_host: str, export_params: dict, use_ssl: bool,
                 creds: Credentials = None) -> dict:
    auth = None
    if creds is not None:
        auth = AWS4Auth(creds.key, creds.secret, creds.region, EXPORT_SERVICE_NAME,
                        session_token=creds.token)

    protocol = 'https' if use_ssl else 'http'
    url = f'{protocol}://{export_host}/{EXPORT_ACTION}'
    res = requests.post(url, json=export_params, headers=EXTRA_HEADERS, auth=auth)
    res.raise_for_status()
    job = res.json()
    return job


def get_export_status(export_host: str, use_ssl: bool, job_id: str, creds: Credentials = None):
    auth = None
    if creds is not None:
        auth = AWS4Auth(creds.key, creds.secret, creds.region, EXPORT_SERVICE_NAME,
                        session_token=creds.token)

    protocol = 'https' if use_ssl else 'http'
    url = f'{protocol}://{export_host}/{EXPORT_ACTION}/{job_id}'
    res = requests.get(url, headers=EXTRA_HEADERS, auth=auth)
    res.raise_for_status()
    job = res.json()
    return job


def get_processing_status(host: str, port: str, use_ssl: bool, request_param_generator, job_name: str):
    res = call_and_get_response('get', f'ml/dataprocessing/{job_name}', host, port, request_param_generator,
                                use_ssl, extra_headers=EXTRA_HEADERS)
    status = res.json()
    return status


def start_processing_job(host: str, port: str, use_ssl: bool, request_param_generator, params: dict):
    params_raw = json.dumps(params) if type(params) is dict else params
    res = call_and_get_response('post', 'ml/dataprocessing', host, port, request_param_generator, use_ssl, params_raw,
                                EXTRA_HEADERS)
    job = res.json()
    return job


def start_training(host: str, port: str, use_ssl: bool, request_param_generator, params):
    params_raw = json.dumps(params) if type(params) is dict else params
    res = call_and_get_response('post', 'ml/modeltraining', host, port, request_param_generator, use_ssl, params_raw,
                                EXTRA_HEADERS)
    return res.json()


def get_training_status(host: str, port: str, use_ssl: bool, request_param_generator, training_job_name: str):
    res = call_and_get_response('get', f'ml/modeltraining/{training_job_name}', host, port,
                                request_param_generator, use_ssl, extra_headers=EXTRA_HEADERS)
    return res.json()


def start_create_endpoint(host: str, port: str, use_ssl: bool, request_param_generator, params):
    params_raw = json.dumps(params) if type(params) is dict else params
    res = call_and_get_response('post', 'ml/endpoints', host, port, request_param_generator, use_ssl, params_raw,
                                EXTRA_HEADERS)
    return res.json()


def get_endpoint_status(host: str, port: str, use_ssl: bool, request_param_generator, training_job_name: str):
    res = call_and_get_response('get', f'ml/endpoints/{training_job_name}', host, port, request_param_generator,
                                use_ssl, extra_headers=EXTRA_HEADERS)
    return res.json()
