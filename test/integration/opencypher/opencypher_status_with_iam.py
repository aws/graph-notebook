"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import json
import threading

import logging
import time
import requests
from requests import HTTPError

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.opencypher import do_opencypher_query, do_opencypher_status
from graph_notebook.opencypher.status import do_opencypher_cancel
from graph_notebook.request_param_generator.factory import create_request_generator

from test.integration.DataDrivenOpenCypherTest import DataDrivenOpenCypherTest

logger = logging.getLogger('TestOpenCypherStatusWithoutIam')


class TestOpenCypherStatusWithIam(DataDrivenOpenCypherTest):
    def do_opencypher_query_save_result(self, query, res):
        try:
            res['result'] = do_opencypher_query(query, self.host, self.port, self.ssl, self.request_generator)
        except requests.HTTPError as exception:
            res['error'] = exception.response.json()

    def setUp(self) -> None:
        self.request_generator = create_request_generator(AuthModeEnum.IAM)
        res = do_opencypher_status(self.host, self.port, self.ssl, AuthModeEnum.IAM, self.request_generator)
        for q in res['queries']:
            do_opencypher_cancel(self.host, self.port, self.ssl, self.request_generator, q['queryId'], False)

    def test_do_opencypher_status_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        with self.assertRaises(HTTPError) as error:
            do_opencypher_status(self.host, self.port, self.ssl, AuthModeEnum.IAM, self.request_generator, query_id)
        err = json.loads(error.exception.response.content.decode('utf-8'))
        self.assertEqual(err['code'], "InvalidParameterException")
        expected_message = f'Supplied queryId {query_id} is invalid'
        self.assertEqual(err['detailedMessage'], expected_message)

    def test_do_opencypher_cancel_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        with self.assertRaises(HTTPError) as error:
            do_opencypher_cancel(self.host, self.port, self.ssl, AuthModeEnum.IAM, self.request_generator, query_id,
                                 False)
        err = json.loads(error.exception.response.content.decode('utf-8'))
        self.assertEqual(err['code'], "InvalidParameterException")
        expected_message = f'Supplied queryId {query_id} is invalid'
        self.assertEqual(err['detailedMessage'], expected_message)

    def test_do_opencypher_cancel_empty_query_id(self):
        with self.assertRaises(ValueError):
            query_id = ''
            do_opencypher_cancel(query_id, False, self.host, self.port, self.ssl, self.request_generator)

    def test_do_opencypher_cancel_non_str_query_id(self):
        with self.assertRaises(ValueError):
            query_id = 42
            do_opencypher_cancel(query_id, False, self.host, self.port, self.ssl, self.request_generator)

    def test_do_opencypher_status_and_cancel(self):
        query = '''MATCH(a)-->(b)
                    MATCH(c)-->(d)
                    RETURN a,b,c,d'''
        query_res = {}
        oc_query_thread = threading.Thread(target=self.do_opencypher_query_save_result, args=(query, query_res,))
        oc_query_thread.start()
        time.sleep(3)

        query_id = ''
        status_res = do_opencypher_status(self.host, self.port, self.ssl, AuthModeEnum.IAM, self.request_generator, query_id)
        self.assertEqual(type(status_res), dict)
        self.assertTrue('acceptedQueryCount' in status_res)
        self.assertTrue('runningQueryCount' in status_res)
        self.assertEqual(1, status_res['runningQueryCount'])
        self.assertTrue('queries' in status_res)

        query_id = ''
        for q in status_res['queries']:
            if query in q['queryString']:
                query_id = q['queryId']

        self.assertNotEqual(query_id, '')

        cancel_res = do_opencypher_cancel(self.host, self.port, self.ssl, AuthModeEnum.IAM, self.request_generator, query_id,
                                          False)
        self.assertEqual(type(cancel_res), dict)
        self.assertEqual(cancel_res['status'], '200 OK')

        oc_query_thread.join()
        self.assertFalse('result' in query_res)
        self.assertTrue('error' in query_res)
        self.assertTrue('code' in query_res['error'])
        self.assertTrue('requestId' in query_res['error'])
        self.assertTrue('detailedMessage' in query_res['error'])
        self.assertEqual('CancelledByUserException', query_res['error']['code'])

    def test_do_sparql_status_and_cancel_silently(self):
        query = '''MATCH(a)-->(b)
                    MATCH(c)-->(d)
                    RETURN a,b,c,d'''

        query_res = {}
        oc_query_thread = threading.Thread(target=self.do_opencypher_query_save_result, args=(query, query_res,))
        oc_query_thread.start()
        time.sleep(3)

        query_id = ''
        status_res = do_opencypher_status(self.host, self.port, self.ssl, AuthModeEnum.IAM, self.request_generator, query_id)
        self.assertEqual(type(status_res), dict)
        self.assertTrue('acceptedQueryCount' in status_res)
        self.assertTrue('runningQueryCount' in status_res)
        self.assertEqual(1, status_res['runningQueryCount'])
        self.assertTrue('queries' in status_res)

        query_id = ''
        for q in status_res['queries']:
            if query in q['queryString']:
                query_id = q['queryId']

        self.assertNotEqual(query_id, '')

        cancel_res = do_opencypher_cancel(self.host, self.port, self.ssl, AuthModeEnum.IAM, self.request_generator, query_id,
                                          True)
        self.assertEqual(type(cancel_res), dict)
        self.assertEqual(cancel_res['status'], '200 OK')

        oc_query_thread.join()
        self.assertEqual(type(query_res['result']), dict)
        self.assertTrue('a' in query_res['result']['head']['vars'])
        self.assertTrue('b' in query_res['result']['head']['vars'])
        self.assertTrue('c' in query_res['result']['head']['vars'])
        self.assertTrue('d' in query_res['result']['head']['vars'])
        self.assertEqual([], query_res['result']['results']['bindings'])
