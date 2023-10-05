"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json
import logging
import re

import requests
import urllib3
from urllib.parse import urlparse, urlunparse
from SPARQLWrapper import SPARQLWrapper
from boto3 import Session
from botocore.session import Session as botocoreSession
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError
from gremlin_python.driver.aiohttp.transport import AiohttpTransport
from neo4j import GraphDatabase, DEFAULT_DATABASE
from neo4j.exceptions import AuthError
from base64 import b64encode
import nest_asyncio

from graph_notebook.neptune.bolt_auth_token import NeptuneBoltAuthToken

# This patch is no longer needed when graph_notebook is using the a Gremlin Python
# client >= 3.5.0 as the HashableDict is now part of that client driver.
# import graph_notebook.neptune.gremlin.graphsonV3d0_MapType_objectify_patch  # noqa F401

DEFAULT_GREMLIN_SERIALIZER = 'graphsonv3'
DEFAULT_GREMLIN_TRAVERSAL_SOURCE = 'g'
DEFAULT_SPARQL_CONTENT_TYPE = 'application/x-www-form-urlencoded'
DEFAULT_PORT = 8182
DEFAULT_REGION = 'us-east-1'
DEFAULT_NEO4J_USERNAME = 'neo4j'
DEFAULT_NEO4J_PASSWORD = 'password'
DEFAULT_NEO4J_DATABASE = DEFAULT_DATABASE

NEPTUNE_SERVICE_NAME = 'neptune-db'
logger = logging.getLogger('client')

# TODO: Constants for states of each long-running job
# TODO: add doc links to each command

FORMAT_CSV = 'csv'
FORMAT_OPENCYPHER = 'opencypher'
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

# Constants used by the Stream Viewer.
STREAM_AT = 'AT_SEQUENCE_NUMBER'
STREAM_AFTER = 'AFTER_SEQUENCE_NUMBER'
STREAM_TRIM = 'TRIM_HORIZON'
STREAM_LATEST = 'LATEST'
STREAM_COMMIT_TIMESTAMP = 'commitTimestamp'
STREAM_IS_LASTOP = 'isLastOp'
STREAM_EXCEPTION_NOT_FOUND = 'StreamRecordsNotFoundException'
STREAM_EXCEPTION_NOT_ENABLED = 'UnsupportedOperationException'

# A mapping from the name in the stream_viewer widget dropdown, to the actual Neptune
# Streams endpoint (API) name. We do not map 'PropertyGraph' to 'pg' to maintain
# compatability with older engine releases that did not have a 'pg' endpoint.

STREAM_PG = 'PropertyGraph'
STREAM_RDF = 'RDF'
STREAM_ENDPOINTS = {STREAM_PG: 'gremlin', STREAM_RDF: 'sparql'}

NEPTUNE_CONFIG_HOST_IDENTIFIERS = ["neptune.amazonaws.com", "neptune.*.amazonaws.com.cn",
                                   "api.aws", "on.aws", "aws.dev",
                                   "sc2s.sgov.gov", "c2s.ic.gov"]

false_str_variants = [False, 'False', 'false', 'FALSE']

GRAPHSONV3_VARIANTS = ['graphsonv3', 'graphsonv3d0', 'graphsonserializersv3d0']
GRAPHSONV2_VARIANTS = ['graphsonv2', 'graphsonv2d0', 'graphsonserializersv2d0']
GRAPHBINARYV1_VARIANTS = ['graphbinaryv1', 'graphbinary', 'graphbinaryserializersv1']

STATISTICS_MODES = ["", "status", "disableAutoCompute", "enableAutoCompute", "refresh", "delete"]
SUMMARY_MODES = ["", "basic", "detailed"]
STATISTICS_LANGUAGE_INPUTS = ["propertygraph", "pg", "gremlin", "oc", "opencypher", "sparql", "rdf"]

SPARQL_EXPLAIN_MODES = ['dynamic', 'static', 'details']
OPENCYPHER_EXPLAIN_MODES = ['dynamic', 'static', 'details']


def is_allowed_neptune_host(hostname: str, host_allowlist: list):
    for host_snippet in host_allowlist:
        if re.search(host_snippet, hostname):
            return True
    return False


def get_gremlin_serializer(serializer_str: str):
    serializer_lower = serializer_str.lower()
    if serializer_lower == 'graphbinaryv1':
        return serializer.GraphBinarySerializersV1()
    elif serializer_lower == 'graphsonv2':
        return serializer.GraphSONSerializersV2d0()
    else:
        return serializer.GraphSONSerializersV3d0()


class Client(object):
    def __init__(self, host: str, port: int = DEFAULT_PORT, ssl: bool = True, ssl_verify: bool = True,
                 region: str = DEFAULT_REGION, sparql_path: str = '/sparql',
                 gremlin_traversal_source: str = DEFAULT_GREMLIN_TRAVERSAL_SOURCE,
                 gremlin_username: str = '', gremlin_password: str = '',
                 gremlin_serializer: str = DEFAULT_GREMLIN_SERIALIZER,
                 neo4j_username: str = DEFAULT_NEO4J_USERNAME, neo4j_password: str = DEFAULT_NEO4J_PASSWORD,
                 neo4j_auth: bool = True, neo4j_database: str = DEFAULT_NEO4J_DATABASE,
                 auth=None, session: Session = None,
                 proxy_host: str = '', proxy_port: int = DEFAULT_PORT,
                 neptune_hosts: list = None):
        self.target_host = host
        self.target_port = port
        self.ssl = ssl
        self.ssl_verify = ssl_verify
        if not self.ssl_verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.sparql_path = sparql_path
        self.gremlin_traversal_source = gremlin_traversal_source
        self.gremlin_username = gremlin_username
        self.gremlin_password = gremlin_password
        self.gremlin_serializer = get_gremlin_serializer(gremlin_serializer)
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password
        self.neo4j_auth = neo4j_auth
        self.neo4j_database = neo4j_database
        self.region = region
        self._auth = auth
        self._session = session
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.neptune_hosts = NEPTUNE_CONFIG_HOST_IDENTIFIERS if neptune_hosts is None else neptune_hosts

        self._http_protocol = 'https' if self.ssl else 'http'
        self._ws_protocol = 'wss' if self.ssl else 'ws'

        self._http_session = None

    @property
    def host(self):
        if self.proxy_host != '':
            return self.proxy_host
        return self.target_host

    @property
    def port(self):
        if self.proxy_host != '':
            return self.proxy_port
        return self.target_port

    def is_neptune_domain(self):
        return is_allowed_neptune_host(hostname=self.target_host, host_allowlist=self.neptune_hosts)

    def get_uri_with_port(self, use_websocket=False, use_proxy=False):
        if use_websocket is True:
            protocol = self._ws_protocol
        else:
            protocol = self._http_protocol

        if use_proxy is True:
            uri_host = self.proxy_host
            uri_port = self.proxy_port
        else:
            uri_host = self.target_host
            uri_port = self.target_port

        uri = f'{protocol}://{uri_host}:{uri_port}'
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

        if explain != '':
            data['explain'] = explain

        if path != '':
            sparql_path = f'/{path}'
        elif self.sparql_path != '':
            sparql_path = f'/{self.sparql_path}'
        elif self.is_neptune_domain():
            sparql_path = f'/{SPARQL_ACTION}'
        else:
            sparql_path = ''

        uri = f'{self._http_protocol}://{self.host}:{self.port}{sparql_path}'
        req = self._prepare_request('POST', uri, data=data, headers=headers)
        res = self._http_session.send(req, verify=self.ssl_verify)
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

    def get_gremlin_connection(self, transport_kwargs) -> client.Client:
        nest_asyncio.apply()

        ws_url = f'{self.get_uri_with_port(use_websocket=True, use_proxy=False)}/gremlin'
        if self.proxy_host != '':
            proxy_http_url = f'{self.get_uri_with_port(use_websocket=False, use_proxy=True)}/gremlin'
            transport_factory_args = lambda: AiohttpTransport(call_from_event_loop=True, proxy=proxy_http_url,
                                                              **transport_kwargs)
            request = self._prepare_request('GET', proxy_http_url)
        else:
            transport_factory_args = lambda: AiohttpTransport(**transport_kwargs)
            request = self._prepare_request('GET', ws_url)

        traversal_source = 'g' if self.is_neptune_domain() else self.gremlin_traversal_source
        return client.Client(ws_url, traversal_source, transport_factory=transport_factory_args,
                             username=self.gremlin_username, password=self.gremlin_password,
                             message_serializer=self.gremlin_serializer,
                             headers=dict(request.headers), **transport_kwargs)

    def gremlin_query(self, query, transport_args=None, bindings=None):
        if transport_args is None:
            transport_args = {}
        c = self.get_gremlin_connection(transport_args)
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

        use_proxy = True if self.proxy_host != '' else False
        uri = f'{self.get_uri_with_port(use_websocket=False, use_proxy=use_proxy)}/gremlin'
        data = {'gremlin': query}
        req = self._prepare_request('POST', uri, data=json.dumps(data), headers=headers)
        res = self._http_session.send(req, verify=self.ssl_verify)
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
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def opencypher_http(self, query: str, headers: dict = None, explain: str = None,
                        query_params: dict = None) -> requests.Response:
        if headers is None:
            headers = {}

        url = f'{self._http_protocol}://{self.host}:{self.port}/'

        if self.is_neptune_domain():
            if 'content-type' not in headers:
                headers['content-type'] = 'application/x-www-form-urlencoded'
            url += 'openCypher'
            data = {
                'query': query
            }
            if explain:
                data['explain'] = explain
                headers['Accept'] = "text/html"
            if query_params:
                data['parameters'] = str(query_params).replace("'", '"')  # '{"AUS_code":"AUS","WLG_code":"WLG"}'
        else:
            url += 'db/neo4j/tx/commit'
            headers['content-type'] = 'application/json'
            headers['Accept'] = 'application/vnd.neo4j.jolt+json-seq'

            data_dict = {
                "statements": [
                    {
                        "statement": query
                    }
                ]
            }
            data = json.dumps(data_dict)
            if self.neo4j_auth:
                user_and_pass = self.neo4j_username + ":" + self.neo4j_password
                user_and_pass_base64 = b64encode(user_and_pass.encode())
                headers['authorization'] = user_and_pass_base64

        req = self._prepare_request('POST', url, data=data, headers=headers)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def opencyper_bolt(self, query: str, **kwargs):
        driver = self.get_opencypher_driver()
        with driver.session(database=self.neo4j_database) as session:
            try:
                res = session.run(query, kwargs)
                data = res.data()
            except AuthError:
                print("Neo4J Bolt request failed with an authentication error. Please ensure that the 'neo4j' section "
                      "of your %graph_notebook_config contains the correct credentials and auth setting.")
                data = []
        driver.close()
        return data

    def opencypher_status(self, query_id: str = '', include_waiting: bool = False):
        kwargs = {}
        if include_waiting:
            kwargs['includeWaiting'] = True
        return self._query_status('openCypher', query_id=query_id, **kwargs)

    def opencypher_cancel(self, query_id, silent: bool = False):
        if type(query_id) is not str or query_id == '':
            raise ValueError('query_id must be a non-empty string')

        return self._query_status('openCypher', query_id=query_id, cancelQuery=True, silent=silent)

    def get_opencypher_driver(self):
        url = f'bolt://{self.host}:{self.port}'

        if self.is_neptune_domain():
            if self._session and self.iam_enabled:
                # check engine version via status API to determine if we need the OC endpoint path
                status_res = self.status()
                status_res.raise_for_status()
                status_res_json = status_res.json()
                engine_version_raw = status_res_json["dbEngineVersion"]
                engine_version = int(engine_version_raw.rsplit('.', 1)[0].replace('.', ''))
                if engine_version >= 1200:
                    url += "/opencypher"

                credentials = self._session.get_credentials()
                frozen_creds = credentials.get_frozen_credentials()
                auth_final = NeptuneBoltAuthToken(frozen_creds, self.region, url)
            else:
                user = 'username'
                password = DEFAULT_NEO4J_PASSWORD
                auth_final = (user, password)
        else:
            if self.neo4j_auth:
                auth_final = (self.neo4j_username, self.neo4j_password)
            else:
                auth_final = None

        driver = GraphDatabase.driver(url, auth=auth_final, encrypted=self.ssl)
        return driver

    def stream(self, url, **kwargs) -> requests.Response:
        params = {}
        for k, v in kwargs.items():
            params[k] = v
        req = self._prepare_request('GET', url, params=params, data='')
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res.json()

    def status(self) -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/status'
        req = self._prepare_request('GET', url, data='')
        res = self._http_session.send(req, verify=self.ssl_verify)
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
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def load_status(self, load_id: str = '', **kwargs) -> requests.Response:
        params = {}
        for k, v in kwargs.items():
            params[k] = v

        if load_id != '':
            params['loadId'] = load_id

        url = f'{self._http_protocol}://{self.host}:{self.port}/loader'
        req = self._prepare_request('GET', url, params=params)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def cancel_load(self, load_id: str) -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/loader'
        params = {'loadId': load_id}
        req = self._prepare_request('DELETE', url, params=params)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def initiate_reset(self) -> requests.Response:
        data = {
            'action': 'initiateDatabaseReset'
        }
        url = f'{self._http_protocol}://{self.host}:{self.port}/system'
        req = self._prepare_request('POST', url, data=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def perform_reset(self, token: str) -> requests.Response:
        data = {
            'action': 'performDatabaseReset',
            'token': token
        }
        url = f'{self._http_protocol}://{self.host}:{self.port}/system'
        req = self._prepare_request('POST', url, data=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
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
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def dataprocessing_job_status(self, job_id: str, neptune_iam_role_arn: str = '') -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/dataprocessing/{job_id}'
        data = {}
        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def dataprocessing_list(self, max_items: int = 10, neptune_iam_role_arn: str = '') -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/dataprocessing'
        data = {
            'maxItems': max_items
        }

        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def dataprocessing_stop(self, job_id: str, clean=False, neptune_iam_role_arn: str = '') -> requests.Response:
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/dataprocessing/{job_id}'
        data = {
            'clean': clean
        }
        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn

        req = self._prepare_request('DELETE', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
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
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def modeltraining_list(self, max_items: int = 10, neptune_iam_role_arn: str = '') -> requests.Response:
        data = {
            'maxItems': max_items
        }

        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltraining'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def modeltraining_job_status(self, training_job_id: str, neptune_iam_role_arn: str = '') -> requests.Response:
        data = {} if neptune_iam_role_arn == '' else {'neptuneIamRoleArn': neptune_iam_role_arn}
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltraining/{training_job_id}'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
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
        res = self._http_session.send(req, verify=self.ssl_verify)
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
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def modeltransform_status(self, job_id: str, iam_role: str = '') -> requests.Response:
        data = {}
        if iam_role != '':
            data['neptuneIamRoleArn'] = iam_role

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltransform/{job_id}'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def modeltransform_list(self, iam_role: str = '', max_items: int = 10) -> requests.Response:
        data = {
            'maxItems': max_items
        }

        if iam_role != '':
            data['neptuneIamRoleArn'] = iam_role

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltransform'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def modeltransform_stop(self, job_id: str, iam_role: str = '', clean: bool = False) -> requests.Response:
        data = {
            'clean': 'TRUE' if clean else 'FALSE'
        }
        if iam_role != '':
            data['neptuneIamRoleArn'] = iam_role

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/modeltransform/{job_id}'
        req = self._prepare_request('DELETE', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
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
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def endpoints_status(self, endpoint_id: str, neptune_iam_role_arn: str = '') -> requests.Response:
        data = {} if neptune_iam_role_arn == '' else {'neptuneIamRoleArn': neptune_iam_role_arn}
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/endpoints/{endpoint_id}'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def endpoints_delete(self, endpoint_id: str, neptune_iam_role_arn: str = '') -> requests.Response:
        data = {} if neptune_iam_role_arn == '' else {'neptuneIamRoleArn': neptune_iam_role_arn}
        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/endpoints/{endpoint_id}'
        req = self._prepare_request('DELETE', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def endpoints(self, max_items: int = 10, neptune_iam_role_arn: str = '') -> requests.Response:
        data = {
            'maxItems': max_items
        }
        if neptune_iam_role_arn != '':
            data['neptuneIamRoleArn'] = neptune_iam_role_arn

        url = f'{self._http_protocol}://{self.host}:{self.port}/ml/endpoints'
        req = self._prepare_request('GET', url, params=data)
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def export(self, host: str, params: dict, ssl: bool = True) -> requests.Response:
        protocol = 'https' if ssl else 'http'
        url = f'{protocol}://{host}/{EXPORT_ACTION}'
        req = self._prepare_request('POST', url, data=json.dumps(params), service="execute-api")
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def export_status(self, host, job_id, ssl: bool = True) -> requests.Response:
        protocol = 'https' if ssl else 'http'
        url = f'{protocol}://{host}/{EXPORT_ACTION}/{job_id}'
        req = self._prepare_request('GET', url, service="execute-api")
        res = self._http_session.send(req, verify=self.ssl_verify)
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
        res = self._http_session.send(req, verify=self.ssl_verify)
        return res

    def statistics(self, language: str, summary: bool = False, mode: str = '') -> requests.Response:
        headers = {
            'Accept': 'application/json'
        }
        if language in ["gremlin", "oc", "opencypher"]:
            language = "pg"
        elif language == "sparql":
            language = "rdf"

        url = f'{self._http_protocol}://{self.host}:{self.port}/{language}/statistics'
        data = {'mode': mode}

        if summary:
            summary_url = url + '/summary'
            if mode:
                summary_mode_param = '?mode=' + mode
                summary_url += summary_mode_param
            req = self._prepare_request('GET', summary_url, headers=headers)
        else:
            if mode in ['', 'status']:
                req = self._prepare_request('GET', url, headers=headers)
            elif mode == 'delete':
                req = self._prepare_request('DELETE', url, headers=headers)
            else:
                req = self._prepare_request('POST', url, data=json.dumps(data), headers=headers)
        res = self._http_session.send(req)
        return res

    def _prepare_request(self, method, url, *, data=None, params=None, headers=None, service=NEPTUNE_SERVICE_NAME):
        self._ensure_http_session()
        if self.proxy_host != '':
            headers = {} if headers is None else headers
            headers["Host"] = self.target_host
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

    def with_gremlin_login(self, username: str, password: str):
        self.args['gremlin_username'] = username
        self.args['gremlin_password'] = password
        return ClientBuilder(self.args)

    def with_gremlin_serializer(self, message_serializer: str):
        self.args['gremlin_serializer'] = message_serializer
        return ClientBuilder(self.args)

    def with_neo4j_login(self, username: str, password: str, auth: bool, database: str):
        self.args['neo4j_username'] = username
        self.args['neo4j_password'] = password
        self.args['neo4j_auth'] = auth
        self.args['neo4j_database'] = database
        return ClientBuilder(self.args)

    def with_tls(self, tls: bool):
        self.args['ssl'] = tls
        return ClientBuilder(self.args)

    def with_ssl_verify(self, ssl_verify: bool):
        self.args['ssl_verify'] = ssl_verify
        return ClientBuilder(self.args)

    def with_region(self, region: str):
        self.args['region'] = region
        return ClientBuilder(self.args)

    def with_iam(self, session: Session):
        self.args['session'] = session
        return ClientBuilder(self.args)

    def with_proxy_host(self, host: str):
        self.args['proxy_host'] = host
        return ClientBuilder(self.args)

    def with_proxy_port(self, proxy_port: int):
        self.args['proxy_port'] = proxy_port
        return ClientBuilder(self.args)

    def with_custom_neptune_hosts(self, neptune_hosts: list):
        self.args['neptune_hosts'] = neptune_hosts
        return ClientBuilder(self.args)

    def build(self) -> Client:
        return Client(**self.args)
