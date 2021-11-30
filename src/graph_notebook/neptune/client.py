"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json
import logging
import re

import requests
from SPARQLWrapper import SPARQLWrapper
from boto3 import Session
from botocore.session import Session as botocoreSession
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from gremlin_python.driver import client
from gremlin_python.driver.protocol import GremlinServerError
from neo4j import GraphDatabase
import nest_asyncio

# This patch is no longer needed when graph_notebook is using the a Gremlin Python
# client >= 3.5.0 as the HashableDict is now part of that client driver.
# import graph_notebook.neptune.gremlin.graphsonV3d0_MapType_objectify_patch  # noqa F401

DEFAULT_SPARQL_CONTENT_TYPE = 'application/x-www-form-urlencoded'
DEFAULT_PORT = 8182
DEFAULT_REGION = 'us-east-1'

NEPTUNE_SERVICE_NAME = 'neptune-db'
logger = logging.getLogger('client')

# TODO: Constants for states of each long-running job
# TODO: add doc links to each command

FORMAT_CSV = 'csv'
FORMAT_OPENCYPHER='opencypher'
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
VALID_FORMATS = [FORMAT_CSV, FORMAT_OPENCYPHER, FORMAT_NTRIPLE, FORMAT_NQUADS, FORMAT_RDFXML, FORMAT_TURTLE]
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

STREAM_AT = 'AT_SEQUENCE_NUMBER'
STREAM_AFTER = 'AFTER_SEQUENCE_NUMBER'
STREAM_TRIM = 'TRIM_HORIZON'
STREAM_EXCEPTION_NOT_FOUND = 'StreamRecordsNotFoundException'
STREAM_EXCEPTION_NOT_ENABLED = 'UnsupportedOperationException'


class Client(object):
    def __init__(self, host: str, port: int = DEFAULT_PORT, ssl: bool = True, region: str = DEFAULT_REGION,
                 sparql_path: str = '/sparql', gremlin_traversal_source: str = 'g', auth=None, session: Session = None):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.sparql_path = sparql_path
        self.gremlin_traversal_source = gremlin_traversal_source
        self.region = region
        self._auth = auth
        self._session = session

        self._http_protocol = 'https' if self.ssl else 'http'
        self._ws_protocol = 'wss' if self.ssl else 'ws'

        self._http_session = None

    def get_uri_with_port(self):
        uri = f'{self._http_protocol}://{self.host}:{self.port}'
        return uri

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

        if path != '':
            sparql_path = f'/{path}'
        elif self.sparql_path != '':
            sparql_path = f'/{self.sparql_path}'
        elif "amazonaws.com" in self.host:
            sparql_path = f'/{SPARQL_ACTION}'
        else:
            sparql_path = ''

        uri = f'{self._http_protocol}://{self.host}:{self.port}{sparql_path}'
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
        nest_asyncio.apply()

        uri = f'{self._http_protocol}://{self.host}:{self.port}/gremlin'
        request = self._prepare_request('GET', uri)

        ws_url = f'{self._ws_protocol}://{self.host}:{self.port}/gremlin'

        traversal_source = 'g' if "neptune.amazonaws.com" in self.host else self.gremlin_traversal_source
        return client.Client(ws_url, traversal_source, headers=dict(request.headers))

    def gremlin_query(self, query, bindings=None):
        c = self.get_gremlin_connection()
        try:
            result = c.submit(query, bindings)
            future_results = result.all()
            results = future_results.result()
            c.close()
            return results
        except Exception as e:
            if isinstance(e, GremlinServerError):
                source_err = re.compile('The traversal source \\[.] for alias \\[.] is not configured on the server\\.')
                if e.status_code == 499 and source_err.search(str(e)):
                    print("Error returned by the Gremlin Server for the traversal_source specified in notebook "
                          "configuration. Please ensure that your graph database endpoint supports re-naming of "
                          "GraphTraversalSource from the default of 'g' in Gremlin Server.")
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

    def gremlin_explain(self, query: str, args={}) -> requests.Response:
        return self._gremlin_query_plan(query=query, plan_type='explain', args=args)

    def gremlin_profile(self, query: str, args={}) -> requests.Response:
        return self._gremlin_query_plan(query=query, plan_type='profile', args=args)

    def _gremlin_query_plan(self, query: str, plan_type: str, args: dict, ) -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/gremlin/{plan_type}'
        data = {'gremlin': query}
        if args:
            for param, value in args.items():
                data[param] = value
        req = self._prepare_request('POST', url, data=json.dumps(data))
        res = self._http_session.send(req)
        return res

    def opencypher_http(self, query: str, headers: dict = None) -> requests.Response:
        if headers is None:
            headers = {}

        if 'content-type' not in headers:
            headers['content-type'] = 'application/x-www-form-urlencoded'

        url = f'{self._http_protocol}://{self.host}:{self.port}/openCypher'
        data = {
            'query': query
        }

        req = self._prepare_request('POST', url, data=data, headers=headers)
        res = self._http_session.send(req)
        return res

    def opencyper_bolt(self, query: str, **kwargs):
        driver = self.get_opencypher_driver()
        with driver.session() as session:
            res = session.run(query, kwargs)
            data = res.data()
        driver.close()
        return data

    def opencypher_status(self, query_id: str = ''):
        return self._query_status('openCypher', query_id=query_id)

    def opencypher_cancel(self, query_id, silent: bool = False):
        if type(query_id) is not str or query_id == '':
            raise ValueError('query_id must be a non-empty string')

        return self._query_status('openCypher', query_id=query_id, cancelQuery=True, silent=silent)

    def get_opencypher_driver(self, user: str = 'neo4j', password: str = 'password'):
        url = f'bolt://{self.host}:{self.port}'

        if self._session:
            method = 'POST'
            headers = {
                'HttpMethod': method,
                'Host': url
            }
            aws_request = self._get_aws_request('POST', url)
            for item in aws_request.headers.items():
                headers[item[0]] = item[1]

            auth_str = json.dumps(headers)
            password = auth_str

        driver = GraphDatabase.driver(url, auth=(user, password), encrypted=self.ssl)
        return driver

    def stream(self, url, **kwargs) -> requests.Response: 
        params = {}
        for k, v in kwargs.items():
            params[k] = v
        req = self._prepare_request('GET', url, params=params,data='')
        res = self._http_session.send(req)
        return res.json()

    def status(self) -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/status'
        req = self._prepare_request('GET', url, data='')
        res = self._http_session.send(req)
        return res

    def load(self, source: str, source_format: str, iam_role_arn: str = None, **kwargs) -> requests.Response:
        """
        For a full list of allowed parameters, see aws documentation on the Neptune loader
        endpoint: https://docs.aws.amazon.com/neptune/latest/userguide/load-api-reference-load.html
        """

        payload = {
            'source': source,
            'format': source_format,
            'region': self.region
        }

        if iam_role_arn:
            payload['iamRoleArn'] = iam_role_arn

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

    def dataprocessing_list(self, max_items: int = 10, neptune_iam_role_arn: str = '') -> requests.Response:
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
                            max_hpo_number_of_training_jobs: int, max_hpo_parallel_training_jobs: int,
                            **kwargs) -> requests.Response:
        """
        for a full list of supported parameters, see:
        https://docs.aws.amazon.com/neptune/latest/userguide/machine-learning-api-modeltraining.html
        """
        data = {
            'dataProcessingJobId': data_processing_job_id,
            'trainModelS3Location': train_model_s3_location,
            'maxHPONumberOfTrainingJobs': max_hpo_number_of_training_jobs,
            'maxHPOParallelTrainingJobs': max_hpo_parallel_training_jobs
        }

        for k, v in kwargs.items():
            data[k] = v

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltraining'
        req = self._prepare_request('POST', url, data=json.dumps(data), headers={'content-type': 'application/json'})
        res = self._http_session.send(req)
        return res

    def modeltraining_list(self, max_items: int = 10, neptune_iam_role_arn: str = '') -> requests.Response:
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

    def modeltransform_create(self, output_s3_location: str, dataprocessing_job_id: str = '',
                              modeltraining_job_id: str = '', training_job_name: str = '',
                              **kwargs) -> requests.Response:
        logger.debug("modeltransform_create initiated with params:"
                     f"output_s3_location: {output_s3_location}\n"
                     f"dataprocessing_job_id: {dataprocessing_job_id}\n"
                     f"modeltraining_job_id: {modeltraining_job_id}\n"
                     f"training_job_name: {training_job_name}\n"
                     f"kwargs: {kwargs}")
        data = {
            'modelTransformOutputS3Location': output_s3_location
        }
        if not dataprocessing_job_id and not modeltraining_job_id and training_job_name:
            data['trainingJobName'] = training_job_name
        elif dataprocessing_job_id and modeltraining_job_id and not training_job_name:
            data['dataProcessingJobId'] = dataprocessing_job_id
            data['mlModelTrainingJobId'] = modeltraining_job_id
        else:
            raise ValueError(
                'Invalid input. Must only specify either dataprocessing_job_id and modeltraining_job_id or only '
                'training_job_name')

        for k, v in kwargs.items():
            data[k] = v

        headers = {
            'content-type': 'application/json'
        }

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltransform'
        req = self._prepare_request('POST', url, data=json.dumps(data), headers=headers)
        res = self._http_session.send(req)
        return res

    def modeltransform_status(self, job_id: str, iam_role: str = '') -> requests.Response:
        data = {}
        if iam_role != '':
            data['neptuneIamRoleArn'] = iam_role

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltransform/{job_id}'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req)
        return res

    def modeltransform_list(self, iam_role: str = '', max_items: int = 10) -> requests.Response:
        data = {
            'maxItems': max_items
        }

        if iam_role != '':
            data['neptuneIamRoleArn'] = iam_role

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltransform'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req)
        return res

    def modeltransform_stop(self, job_id: str, iam_role: str = '', clean: bool = False) -> requests.Response:
        data = {
            'clean': 'TRUE' if clean else 'FALSE'
        }
        if iam_role != '':
            data['neptuneIamRoleArn'] = iam_role

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltransform/{job_id}'
        req = self._prepare_request('DELETE', url, params=data)
        res = self._http_session.send(req)
        return res

    def endpoints_create(self, model_training_job_id: str = '', model_transform_job_id: str = '',
                         **kwargs) -> requests.Response:
        data = {}

        if model_training_job_id and not model_transform_job_id:
            data['mlModelTrainingJobId'] = model_training_job_id
        elif model_transform_job_id and not model_training_job_id:
            data['mlModelTransformJobId'] = model_transform_job_id
        else:
            raise ValueError('Invalid input. Must either specify model_training_job_id or model_transform_job_id, '
                             'and not both.')

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

    def endpoints(self, max_items: int = 10, neptune_iam_role_arn: str = '') -> requests.Response:
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
        request = requests.Request(method=method, url=url, data=data, params=params, headers=headers, auth=self._auth)
        if self._session is not None:
            aws_request = self._get_aws_request(method=method, url=url, data=data, params=params, headers=headers,
                                                service=service)
            request.headers = dict(aws_request.headers)

        return request.prepare()

    def _get_aws_request(self, method, url, *, data=None, params=None, headers=None, service=NEPTUNE_SERVICE_NAME):
        req = AWSRequest(method=method, url=url, data=data, params=params, headers=headers)
        if self.iam_enabled:
            credentials = self._session.get_credentials()
            try:
                frozen_creds = credentials.get_frozen_credentials()
            except AttributeError:
                print("Could not find valid IAM credentials in any the following locations:\n")
                print("env, assume-role, assume-role-with-web-identity, sso, shared-credential-file, custom-process, "
                      "config-file, ec2-credentials-file, boto-config, container-role, iam-role\n")
                print("Go to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html for more "
                      "details on configuring your IAM credentials.")
                return req
            SigV4Auth(frozen_creds, service, self.region).add_auth(req)
            prepared_iam_req = req.prepare()
            return prepared_iam_req
        else:
            return req

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
        return type(self._session) in [Session, botocoreSession]


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

    def with_gremlin_traversal_source(self, traversal_source: str):
        self.args['gremlin_traversal_source'] = traversal_source
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
