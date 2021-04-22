"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json

import botocore
import requests
from SPARQLWrapper import SPARQLWrapper
from boto3 import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from gremlin_python.driver import client
from tornado import httpclient

import graph_notebook.neptune.gremlin.graphsonV3d0_MapType_objectify_patch  # noqa F401

DEFAULT_SPARQL_CONTENT_TYPE = 'application/x-www-form-urlencoded'
DEFAULT_PORT = 8182
DEFAULT_REGION = 'us-east-1'

NEPTUNE_SERVICE_NAME = 'neptune-db'

# TODO: Constants for states of each long-running job
# TODO: add doc links to each command

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

EXPORT_SERVICE_NAME = 'execute-api'
EXPORT_ACTION = 'neptune-export'
EXTRA_HEADERS = {'content-type': 'application/json'}
SPARQL_ACTION = 'sparql'


class Client(object):
    def __init__(self, host: str, port: int = DEFAULT_PORT, ssl: bool = True, region: str = DEFAULT_REGION,
                 sparql_path: str = '/sparql', session: Session = None):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.sparql_path = sparql_path
        self.region = region
        self._session = session

        self._http_protocol = 'https' if self.ssl else 'http'
        self._ws_protocol = 'wss' if self.ssl else 'ws'

        self._http_session = None

    def sparql_query(self, query: str, headers=None, explain: str = '', path: str = '') -> requests.Response:
        if headers is None:
            headers = {}

        data = {'query': query}
        return self.do_sparql_request(data, headers, explain, path=path)

    def sparql_update(self, update: str, headers=None, explain: str = '', path: str = '') -> requests.Response:
        if headers is None:
            headers = {}

        data = {'update': update}
        return self.do_sparql_request(data, headers, explain, path=path)

    def do_sparql_request(self, data: dict, headers=None, explain: str = '', path: str = ''):
        if 'content-type' not in headers:
            headers['content-type'] = DEFAULT_SPARQL_CONTENT_TYPE

        explain = explain.lower()
        if explain != '':
            if explain not in ['static', 'dynamic', 'details']:
                raise ValueError('explain mode not valid, must be one of "static", "dynamic", or "details"')
            else:
                data['explain'] = explain

        sparql_path = path if path != '' else self.sparql_path
        uri = f'{self._http_protocol}://{self.host}:{self.port}/{sparql_path}'
        req = self._prepare_request('POST', uri, data=data, headers=headers)
        res = self._http_session.send(req)
        return res

    def sparql(self, query: str, headers=None, explain: str = '', path: str = '') -> requests.Response:
        if headers is None:
            headers = {}

        s = SPARQLWrapper('')
        s.setQuery(query)
        query_type = s.queryType.upper()
        if query_type in ['SELECT', 'CONSTRUCT', 'ASK', 'DESCRIBE']:
            return self.sparql_query(query, headers, explain, path=path)
        else:
            return self.sparql_update(query, headers, explain, path=path)

    # TODO: enum/constants for supported types
    def sparql_explain(self, query: str, explain: str = 'dynamic', output_format: str = 'text/html',
                       headers=None, path: str = '') -> requests.Response:
        if headers is None:
            headers = {}

        if 'Accept' not in headers:
            headers['Accept'] = output_format

        return self.sparql(query, headers, explain, path=path)

    def sparql_status(self, query_id: str = ''):
        return self._query_status('sparql', query_id=query_id)

    def sparql_cancel(self, query_id: str, silent: bool = False):
        if type(query_id) is not str or query_id == '':
            raise ValueError('query_id must be a non-empty string')
        return self._query_status('sparql', query_id=query_id, silent=silent, cancelQuery=True)

    def get_gremlin_connection(self) -> client.Client:
        uri = f'{self._http_protocol}://{self.host}:{self.port}/gremlin'
        request = self._prepare_request('GET', uri)

        ws_url = f'{self._ws_protocol}://{self.host}:{self.port}/gremlin'
        ws_request = httpclient.HTTPRequest(ws_url, headers=dict(request.headers))
        return client.Client(ws_request, 'g')

    def gremlin_query(self, query, bindings=None):
        c = self.get_gremlin_connection()
        try:
            result = c.submit(query, bindings)
            future_results = result.all()
            results = future_results.result()
            c.close()
            return results
        except Exception as e:
            c.close()
            raise e

    def gremlin_http_query(self, query, headers=None) -> requests.Response:
        if headers is None:
            headers = {}

        uri = f'{self._http_protocol}://{self.host}:{self.port}/gremlin'
        data = {'gremlin': query}
        req = self._prepare_request('POST', uri, data=json.dumps(data), headers=headers)
        res = self._http_session.send(req)
        return res

    def gremlin_status(self, query_id: str = '', include_waiting: bool = False):
        kwargs = {}
        if include_waiting:
            kwargs['includeWaiting'] = True
        return self._query_status('gremlin', query_id=query_id, **kwargs)

    def gremlin_cancel(self, query_id: str):
        if type(query_id) is not str or query_id == '':
            raise ValueError('query_id must be a non-empty string')
        return self._query_status('gremlin', query_id=query_id, cancelQuery=True)

    def gremlin_explain(self, query: str) -> requests.Response:
        return self._gremlin_query_plan(query, 'explain')

    def gremlin_profile(self, query: str) -> requests.Response:
        return self._gremlin_query_plan(query, 'profile')

    def _gremlin_query_plan(self, query: str, plan_type: str, ) -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/gremlin/{plan_type}'
        data = {'gremlin': query}
        req = self._prepare_request('POST', url, data=json.dumps(data))
        res = self._http_session.send(req)
        return res

    def status(self) -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/status'
        req = self._prepare_request('GET', url, data='')
        res = self._http_session.send(req)
        return res

    def load(self, source: str, source_format: str, iam_role_arn: str, region: str, **kwargs) -> requests.Response:
        """
        For a full list of allowed parameters, see aws documentation on the Neptune loader
        endpoint: https://docs.aws.amazon.com/neptune/latest/userguide/load-api-reference-load.html
        """
        payload = {
            'source': source,
            'format': source_format,
            'region': self.region,
            'iamRoleArn': iam_role_arn
        }

        for key, value in kwargs.items():
            payload[key] = value

        url = f'{self._http_protocol}://{self.host}:{self.port}/loader'
        raw = json.dumps(payload)
        req = self._prepare_request('POST', url, data=raw, headers={'content-type': 'application/json'})
        res = self._http_session.send(req)
        return res

    def load_status(self, load_id: str = '', **kwargs) -> requests.Response:
        params = {}
        for k, v in kwargs.items():
            params[k] = v

        if load_id != '':
            params['loadId'] = load_id

        url = f'{self._http_protocol}://{self.host}:{self.port}/loader'
        req = self._prepare_request('GET', url, params=params)
        res = self._http_session.send(req)
        return res

    def cancel_load(self, load_id: str) -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/loader'
        params = {'loadId': load_id}
        req = self._prepare_request('DELETE', url, params=params)
        res = self._http_session.send(req)
        return res

    def initiate_reset(self) -> requests.Response:
        data = {
            'action': 'initiateDatabaseReset'
        }
        url = f'{self._http_protocol}://{self.host}:{self.port}/system'
        req = self._prepare_request('POST', url, data=data)
        res = self._http_session.send(req)
        return res

    def perform_reset(self, token: str) -> requests.Response:
        data = {
            'action': 'performDatabaseReset',
            'token': token
        }
        url = f'{self._http_protocol}://{self.host}:{self.port}/system'
        req = self._prepare_request('POST', url, data=data)
        res = self._http_session.send(req)
        return res

    def dataprocessing_start(self, s3_input_uri: str, s3_output_uri: str, **kwargs) -> requests.Response:
        data = {
            'inputDataS3Location': s3_input_uri,
            'processedDataS3Location': s3_output_uri,
        }

        for k, v in kwargs.items():
            data[k] = v

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/dataprocessing'
        req = self._prepare_request('POST', url, data=json.dumps(data), headers={'content-type': 'application/json'})
        res = self._http_session.send(req)
        return res

    def dataprocessing_job_status(self, job_id: str, neptune_iam_role_arn: str = '') -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/dataprocessing/{job_id}'
        data = {}
        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req)
        return res

    def dataprocessing_status(self, max_items: int = 10, neptune_iam_role_arn: str = '') -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/dataprocessing'
        data = {
            'maxItems': max_items
        }

        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req)
        return res

    def dataprocessing_stop(self, job_id: str, clean=False, neptune_iam_role_arn: str = '') -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/dataprocessing/{job_id}'
        data = {
            'clean': clean
        }
        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn

        req = self._prepare_request('DELETE', url, params=data)
        res = self._http_session.send(req)
        return res

    def modeltraining_start(self, data_processing_job_id: str, train_model_s3_location: str,
                            **kwargs) -> requests.Response:
        """
        for a full list of supported parameters, see:
        https://docs.aws.amazon.com/neptune/latest/userguide/machine-learning-api-modeltraining.html
        """
        data = {
            'dataProcessingJobId': data_processing_job_id,
            'trainModelS3Location': train_model_s3_location
        }

        for k, v in kwargs.items():
            data[k] = v

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltraining'
        req = self._prepare_request('POST', url, data=json.dumps(data), headers={'content-type': 'application/json'})
        res = self._http_session.send(req)
        return res

    def modeltraining_status(self, max_items: int = 10, neptune_iam_role_arn: str = '') -> requests.Response:
        data = {
            'maxItems': max_items
        }

        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltraining'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req)
        return res

    def modeltraining_job_status(self, training_job_id: str, neptune_iam_role_arn: str = '') -> requests.Response:
        data = {} if neptune_iam_role_arn == '' else {'neptuneIamRoleArn': neptune_iam_role_arn}
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltraining/{training_job_id}'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req)
        return res

    def modeltraining_stop(self, training_job_id: str, neptune_iam_role_arn: str = '',
                           clean: bool = False) -> requests.Response:
        data = {
            'clean': "TRUE" if clean else "FALSE",
        }

        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltraining/{training_job_id}'
        req = self._prepare_request('DELETE', url, params=data)
        res = self._http_session.send(req)
        return res

    def endpoints_create(self, training_job_id: str, **kwargs) -> requests.Response:
        data = {
            'mlModelTrainingJobId': training_job_id
        }

        for k, v in kwargs.items():
            data[k] = v

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/endpoints'
        req = self._prepare_request('POST', url, data=json.dumps(data), headers={'content-type': 'application/json'})
        res = self._http_session.send(req)
        return res

    def endpoints_status(self, endpoint_id: str, neptune_iam_role_arn: str = '') -> requests.Response:
        data = {} if neptune_iam_role_arn == '' else {'neptuneIamRoleArn': neptune_iam_role_arn}
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/endpoints/{endpoint_id}'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req)
        return res

    def endpoints_delete(self, endpoint_id: str, neptune_iam_role_arn: str = '') -> requests.Response:
        data = {} if neptune_iam_role_arn == '' else {'neptuneIamRoleArn': neptune_iam_role_arn}
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/endpoints/{endpoint_id}'
        req = self._prepare_request('DELETE', url, params=data)
        res = self._http_session.send(req)
        return res

    def endpoints(self, max_items: int = 10, neptune_iam_role_arn: str = ''):
        data = {
            'maxItems': max_items
        }
        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/endpoints'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req)
        return res

    def export(self, host: str, params: dict, ssl: bool = True) -> requests.Response:
        protocol = 'https' if ssl else 'http'
        url = f'{protocol}://{host}/{EXPORT_ACTION}'
        req = self._prepare_request('POST', url, data=json.dumps(params), service="execute-api")
        res = self._http_session.send(req)
        return res

    def export_status(self, host, job_id, ssl: bool = True) -> requests.Response:
        protocol = 'https' if ssl else 'http'
        url = f'{protocol}://{host}/{EXPORT_ACTION}/{job_id}'
        req = self._prepare_request('GET', url, service="execute-api")
        res = self._http_session.send(req)
        return res

    def _query_status(self, language: str, *, query_id: str = '', **kwargs) -> requests.Response:
        data = {}
        if query_id != '':
            data['queryId'] = query_id

        for k, v in kwargs.items():
            data[k] = v

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        url = f'{self._http_protocol}://{self.host}:{self.port}/{language}/status'
        req = self._prepare_request('POST', url, data=data, headers=headers)
        res = self._http_session.send(req)
        return res

    def _prepare_request(self, method, url, *, data=None, params=None, headers=None, service=NEPTUNE_SERVICE_NAME):
        self._ensure_http_session()
        request = requests.Request(method=method, url=url, data=data, params=params, headers=headers)
        if self._session is not None:
            credentials = self._session.get_credentials()
            frozen_creds = credentials.get_frozen_credentials()

            req = AWSRequest(method=method, url=url, data=data, params=params, headers=headers)
            SigV4Auth(frozen_creds, service, self.region).add_auth(req)
            prepared_iam_req = req.prepare()
            request.headers = dict(prepared_iam_req.headers)

        return request.prepare()

    def _ensure_http_session(self):
        if not self._http_session:
            self._http_session = requests.Session()

    def set_session(self, session: Session):
        self._session = session

    def close(self):
        if self._http_session:
            self._http_session.close()
            self._http_session = None

    @property
    def iam_enabled(self):
        return type(self._session) is botocore.session.Session


class ClientBuilder(object):
    def __init__(self, args: dict = None):
        if args is None:
            args = {}
        self.args = args

    def with_host(self, host: str):
        self.args['host'] = host
        return ClientBuilder(self.args)

    def with_port(self, port: int):
        self.args['port'] = port
        return ClientBuilder(self.args)

    def with_sparql_path(self, path: str):
        self.args['sparql_path'] = path
        return ClientBuilder(self.args)

    def with_tls(self, tls: bool):
        self.args['ssl'] = tls
        return ClientBuilder(self.args)

    def with_region(self, region: str):
        self.args['region'] = region
        return ClientBuilder(self.args)

    def with_iam(self, session: Session):
        self.args['session'] = session
        return ClientBuilder(self.args)

    def build(self) -> Client:
        return Client(**self.args)
