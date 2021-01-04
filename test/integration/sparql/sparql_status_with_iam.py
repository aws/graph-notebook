"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import threading
import time
import requests

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.sparql.query import do_sparql_query
from graph_notebook.sparql.status import do_sparql_status, do_sparql_cancel
from graph_notebook.request_param_generator.factory import create_request_generator

from test.integration import DataDrivenSparqlTest


class TestSparqlStatusWithIam(DataDrivenSparqlTest):
    def do_sparql_query_save_result(self, query, res):
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        try:
            res['result'] = do_sparql_query(query, self.host, self.port, self.ssl, request_generator)
        except requests.HTTPError as exception:
            res['error'] = exception.response.json()

    def setUp(self) -> None:
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        res = do_sparql_status(self.host, self.port, self.ssl, request_generator)
        for q in res['queries']:
            do_sparql_cancel(self.host, self.port, self.ssl, request_generator, q['queryId'], False)

    def test_do_sparql_status_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        res = do_sparql_status(self.host, self.port, self.ssl, request_generator, query_id)
        self.assertEqual(type(res), dict)
        self.assertTrue('acceptedQueryCount' in res)
        self.assertTrue('runningQueryCount' in res)
        self.assertTrue('queries' in res)

    def test_do_sparql_cancel_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        res = do_sparql_cancel(self.host, self.port, self.ssl, request_generator, query_id, False)
        self.assertEqual(type(res), dict)
        self.assertTrue('acceptedQueryCount' in res)
        self.assertTrue('runningQueryCount' in res)
        self.assertTrue('queries' in res)

    def test_do_sparql_cancel_empty_query_id(self):
        with self.assertRaises(ValueError):
            query_id = ''
            request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
            do_sparql_cancel(self.host, self.port, self.ssl, request_generator, query_id, False)

    def test_do_sparql_cancel_non_str_query_id(self):
        with self.assertRaises(ValueError):
            query_id = 42
            request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
            do_sparql_cancel(self.host, self.port, self.ssl, request_generator, query_id, False)

    def test_do_sparql_status_and_cancel(self):
        query = "SELECT * WHERE { ?s ?p ?o . ?s2 ?p2 ?o2 .?s3 ?p3 ?o3 .} ORDER BY DESC(?s) LIMIT 100"
        query_res = {}
        sparql_query_thread = threading.Thread(target=self.do_sparql_query_save_result, args=(query, query_res,))
        sparql_query_thread.start()
        time.sleep(1)

        query_id = ''
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        status_res = do_sparql_status(self.host, self.port, self.ssl, self.request_generator, query_id)
        self.assertEqual(type(status_res), dict)
        self.assertTrue('acceptedQueryCount' in status_res)
        self.assertTrue('runningQueryCount' in status_res)
        self.assertTrue('queries' in status_res)

        time.sleep(1)

        query_id = ''
        for q in status_res['queries']:
            if query in q['queryString']:
                query_id = q['queryId']

        self.assertNotEqual(query_id, '')

        cancel_res = do_sparql_cancel(self.host, self.port, self.ssl, request_generator, query_id, False)
        self.assertEqual(type(cancel_res), dict)
        self.assertTrue('acceptedQueryCount' in cancel_res)
        self.assertTrue('runningQueryCount' in cancel_res)
        self.assertTrue('queries' in cancel_res)

        sparql_query_thread.join()
        self.assertFalse('result' in query_res)
        self.assertTrue('error' in query_res)
        self.assertTrue('code' in query_res['error'])
        self.assertTrue('requestId' in query_res['error'])
        self.assertTrue('detailedMessage' in query_res['error'])
        self.assertEqual('CancelledByUserException', query_res['error']['code'])

    def test_do_sparql_status_and_cancel_silently(self):
        query = "SELECT * WHERE { ?s ?p ?o . ?s2 ?p2 ?o2 .?s3 ?p3 ?o3 .} ORDER BY DESC(?s) LIMIT 100"
        query_res = {}
        sparql_query_thread = threading.Thread(target=self.do_sparql_query_save_result, args=(query, query_res,))
        sparql_query_thread.start()
        time.sleep(1)

        query_id = ''
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        status_res = do_sparql_status(self.host, self.port, self.ssl, request_generator, query_id)
        self.assertEqual(type(status_res), dict)
        self.assertTrue('acceptedQueryCount' in status_res)
        self.assertTrue('runningQueryCount' in status_res)
        self.assertTrue('queries' in status_res)

        query_id = ''
        for q in status_res['queries']:
            if query in q['queryString']:
                query_id = q['queryId']

        self.assertNotEqual(query_id, '')

        cancel_res = do_sparql_cancel(self.host, self.port, self.ssl, request_generator, query_id, True)
        self.assertEqual(type(cancel_res), dict)
        self.assertTrue('acceptedQueryCount' in cancel_res)
        self.assertTrue('runningQueryCount' in cancel_res)
        self.assertTrue('queries' in cancel_res)

        sparql_query_thread.join()
        self.assertEqual(type(query_res['result']), dict)
        self.assertTrue('s3' in query_res['result']['head']['vars'])
        self.assertTrue('p3' in query_res['result']['head']['vars'])
        self.assertTrue('o3' in query_res['result']['head']['vars'])
        self.assertEqual([], query_res['result']['results']['bindings'])
