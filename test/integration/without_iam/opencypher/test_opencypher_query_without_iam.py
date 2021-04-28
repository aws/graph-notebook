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

from test.integration.DataDrivenOpenCypherTest import DataDrivenOpenCypherTest

logger = logging.getLogger('TestOpenCypherStatusWithoutIam')


class TestOpenCypherStatusWithIam(DataDrivenOpenCypherTest):
    def do_opencypher_query_save_result(self, query, res):
        try:
            res['result'] = self.client.opencyper_bolt(query)
        except requests.HTTPError as exception:
            res['error'] = exception.response.json()

    def setUp(self) -> None:
        res = self.client.opencypher_status()
        for q in res['queries']:
            self.client.opencypher_cancel(q['queryId'])

    def test_do_opencypher_status_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        with self.assertRaises(HTTPError) as error:
            self.client.opencypher_status(query_id)
        err = json.loads(error.exception.response.content.decode('utf-8'))
        self.assertEqual(err['code'], "InvalidParameterException")
        expected_message = f'Supplied queryId {query_id} is invalid'
        self.assertEqual(err['detailedMessage'], expected_message)

    def test_do_opencypher_cancel_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        with self.assertRaises(HTTPError) as error:
            self.client.opencypher_cancel(query_id)
        err = json.loads(error.exception.response.content.decode('utf-8'))
        self.assertEqual(err['code'], "InvalidParameterException")
        expected_message = f'Supplied queryId {query_id} is invalid'
        self.assertEqual(err['detailedMessage'], expected_message)

    def test_do_opencypher_cancel_empty_query_id(self):
        with self.assertRaises(ValueError):
            self.client.opencypher_cancel('')

    def test_do_opencypher_cancel_non_str_query_id(self):
        with self.assertRaises(ValueError):
            self.client.opencypher_cancel(42)

    def test_do_opencypher_status_and_cancel(self):
        query = '''MATCH(a)-->(b)
                    MATCH(c)-->(d)
                    RETURN a,b,c,d'''
        query_res = {}
        oc_query_thread = threading.Thread(target=self.do_opencypher_query_save_result, args=(query, query_res,))
        oc_query_thread.start()
        time.sleep(3)

        status_res = self.client.opencypher_status()
        assert type(status_res) is dict
        assert 'acceptedQueryCount' in status_res
        assert 'runningQueryCount' in status_res
        assert 1 == status_res['runningQueryCount']
        assert 'queries' in status_res

        query_id = ''
        for q in status_res['queries']:
            if query in q['queryString']:
                query_id = q['queryId']

        assert query_id != ''

        cancel_res = self.client.opencypher_cancel(query_id)
        assert type(cancel_res) is dict
        assert cancel_res['status'] == '200 OK'

        oc_query_thread.join()
        assert 'result' not in query_res
        assert 'error' in query_res
        assert 'code' in query_res['error']
        assert 'requestId' in query_res['error']
        assert 'detailedMessage' in query_res['error']
        assert 'CancelledByUserException' == query_res['error']['code']

    def test_do_sparql_status_and_cancel_silently(self):
        query = '''MATCH(a)-->(b)
                    MATCH(c)-->(d)
                    RETURN a,b,c,d'''

        query_res = {}
        oc_query_thread = threading.Thread(target=self.do_opencypher_query_save_result, args=(query, query_res,))
        oc_query_thread.start()
        time.sleep(3)

        query_id = ''
        status = self.client.opencypher_status(query_id)
        assert status.status_code == 200

        status_res = status.json()
        assert type(status_res) is dict
        assert 'acceptedQueryCount' in status_res
        assert 'runningQueryCount' in status_res
        assert 1 == status_res['runningQueryCount']
        assert 'queries' in status_res

        query_id = ''
        for q in status_res['queries']:
            if query in q['queryString']:
                query_id = q['queryId']

        assert query_id != ''
        self.assertNotEqual(query_id, '')

        cancel = self.client.opencypher_cancel(query_id)
        cancel_res = cancel.json()
        assert type(cancel_res) is dict
        assert cancel_res['status'] == '200 OK'

        oc_query_thread.join()
        assert type(query_res['result']) is dict
        assert 'a' in query_res['result']['head']['vars']
        assert 'b' in query_res['result']['head']['vars']
        assert 'c' in query_res['result']['head']['vars']
        assert 'd' in query_res['result']['head']['vars']
        assert [] == query_res['result']['results']['bindings']
