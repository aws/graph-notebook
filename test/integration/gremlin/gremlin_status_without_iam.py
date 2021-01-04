"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import threading
import time
import requests
from os import cpu_count

from gremlin_python.driver.protocol import GremlinServerError

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.gremlin.query import do_gremlin_query
from graph_notebook.gremlin.status import do_gremlin_status, do_gremlin_cancel
from graph_notebook.request_param_generator.factory import create_request_generator

from test.integration import DataDrivenGremlinTest


class TestGremlinStatusWithoutIam(DataDrivenGremlinTest):
    def do_gremlin_query_save_results(self, query, res):
        try:
            res['result'] = do_gremlin_query(query, self.host, self.port, self.ssl, self.client_provider)
        except GremlinServerError as exception:
            res['error'] = str(exception)

    def test_do_gremlin_status_nonexistent(self):
        with self.assertRaises(requests.HTTPError):
            query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
            request_generator = create_request_generator(AuthModeEnum.DEFAULT)
            try:
                do_gremlin_status(self.host, self.port, self.ssl, self.auth_mode, request_generator, query_id, False)
            except requests.HTTPError as exception:
                content = exception.response.json()
                self.assertTrue('requestId' in content)
                self.assertTrue('code' in content)
                self.assertTrue('detailedMessage' in content)
                self.assertEqual('InvalidParameterException', content['code'])
                raise exception

    def test_do_gremlin_cancel_nonexistent(self):
        with self.assertRaises(requests.HTTPError):
            query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
            request_generator = create_request_generator(AuthModeEnum.DEFAULT)
            try:
                do_gremlin_cancel(self.host, self.port, self.ssl, self.auth_mode, request_generator, query_id)
            except requests.HTTPError as exception:
                content = exception.response.json()
                self.assertTrue('requestId' in content)
                self.assertTrue('code' in content)
                self.assertTrue('detailedMessage' in content)
                self.assertEqual('InvalidParameterException', content['code'])
                raise exception

    def test_do_gremlin_cancel_empty_query_id(self):
        with self.assertRaises(ValueError):
            query_id = ''
            request_generator = create_request_generator(AuthModeEnum.DEFAULT)
            do_gremlin_cancel(self.host, self.port, self.ssl, self.auth_mode, request_generator, query_id)

    def test_do_gremlin_cancel_non_str_query_id(self):
        with self.assertRaises(ValueError):
            query_id = 42
            request_generator = create_request_generator(AuthModeEnum.DEFAULT)
            do_gremlin_cancel(self.host, self.port, self.ssl, self.auth_mode, request_generator, query_id)

    def test_do_gremlin_status_and_cancel(self):
        query = "g.V().out().out().out().out()"
        query_res = {}
        gremlin_query_thread = threading.Thread(target=self.do_gremlin_query_save_results, args=(query, query_res,))
        gremlin_query_thread.start()
        time.sleep(3)

        query_id = ''
        request_generator = create_request_generator(AuthModeEnum.DEFAULT)
        status_res = do_gremlin_status(self.host, self.port, self.ssl, self.auth_mode,
                                       request_generator, query_id, False)
        self.assertEqual(type(status_res), dict)
        self.assertTrue('acceptedQueryCount' in status_res)
        self.assertTrue('runningQueryCount' in status_res)
        self.assertTrue(status_res['runningQueryCount'] == 1)
        self.assertTrue('queries' in status_res)

        query_id = ''
        for q in status_res['queries']:
            if query in q['queryString']:
                query_id = q['queryId']

        self.assertNotEqual(query_id, '')

        cancel_res = do_gremlin_cancel(self.host, self.port, self.ssl, self.auth_mode, request_generator, query_id)
        self.assertEqual(type(cancel_res), dict)
        self.assertTrue('status' in cancel_res)
        self.assertTrue('payload' in cancel_res)
        self.assertEqual('200 OK', cancel_res['status'])

        gremlin_query_thread.join()
        self.assertFalse('result' in query_res)
        self.assertTrue('error' in query_res)
        self.assertTrue('code' in query_res['error'])
        self.assertTrue('requestId' in query_res['error'])
        self.assertTrue('detailedMessage' in query_res['error'])
        self.assertTrue('TimeLimitExceededException' in query_res['error'])

    def test_do_gremlin_status_include_waiting(self):
        query = "g.V().out().out().out().out()"
        num_threads = 4 * cpu_count()
        threads = []
        for x in range(0, num_threads):
            gremlin_query_thread = threading.Thread(target=self.do_gremlin_query_save_results, args=(query, {}))
            threads.append(gremlin_query_thread)
            gremlin_query_thread.start()

        time.sleep(5)

        query_id = ''
        request_generator = create_request_generator(AuthModeEnum.DEFAULT)
        status_res = do_gremlin_status(self.host, self.port, self.ssl, self.auth_mode,
                                       request_generator, query_id, True)

        self.assertEqual(type(status_res), dict)
        self.assertTrue('acceptedQueryCount' in status_res)
        self.assertTrue('runningQueryCount' in status_res)
        self.assertTrue('queries' in status_res)
        self.assertEqual(status_res['acceptedQueryCount'], len(status_res['queries']))

        for gremlin_query_thread in threads:
            gremlin_query_thread.join()
