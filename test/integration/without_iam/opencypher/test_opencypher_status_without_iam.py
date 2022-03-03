"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import threading

import logging
import time
import requests
from os import cpu_count

from graph_notebook.neptune.client import Client
from test.integration.DataDrivenOpenCypherTest import DataDrivenOpenCypherTest

logger = logging.getLogger('TestOpenCypherStatusWithoutIam')


def long_running_opencypher_query(c: Client, query: str):
    res = c.opencypher_http(query)
    return res


class TestOpenCypherStatusWithoutIam(DataDrivenOpenCypherTest):
    def do_opencypher_query_save_result(self, query, res):
        try:
            res = self.client.opencypher_http(query)
            res.raise_for_status()
            res['result'] = res.json()
        except requests.HTTPError as exception:
            res['error'] = exception.response.json()

    def setUp(self) -> None:
        super().setUp()

        res = self.client.opencypher_status()
        res.raise_for_status()

        status = res.json()
        for q in status['queries']:
            self.client.opencypher_cancel(q['queryId'])

    def test_do_opencypher_status_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        status = self.client.opencypher_status(query_id)
        assert status.status_code != 200
        err = status.json()
        self.assertEqual(err['code'], "InvalidParameterException")
        expected_message = f'Supplied queryId {query_id} is invalid'
        self.assertEqual(err['detailedMessage'], expected_message)

    def test_do_opencypher_cancel_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        res = self.client.opencypher_cancel(query_id)
        assert res.status_code != 200
        err = res.json()
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
                    MATCH(e)-->(f)
                    RETURN a,b,c,d,e,f'''
        query_res = {}
        oc_query_thread = threading.Thread(target=self.do_opencypher_query_save_result, args=(query, query_res,))
        oc_query_thread.start()
        time.sleep(1)

        res = self.client.opencypher_status()
        res.raise_for_status()
        status_res = res.json()
        assert 'acceptedQueryCount' in status_res
        assert 'runningQueryCount' in status_res
        assert status_res['runningQueryCount'] >= 1
        assert 'queries' in status_res

        query_id = ''
        for q in status_res['queries']:
            if query in q['queryString']:
                query_id = q['queryId']

        assert query_id != ''

        res = self.client.opencypher_cancel(query_id)
        res.raise_for_status()
        cancel_res = res.json()
        assert cancel_res['status'] == '200 OK'

        oc_query_thread.join()
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

    def test_do_opencypher_status_include_waiting(self):
        query = '''MATCH(a)-->(b)-->(c)-->(d)-->(e)
                    RETURN a,b,c,d,e'''

        num_threads = cpu_count() * 4
        threads = []
        for x in range(0, num_threads):
            thread = threading.Thread(target=long_running_opencypher_query, args=(self.client, query))
            thread.start()
            threads.append(thread)

        time.sleep(5)

        res = self.client.opencypher_status(include_waiting=True)
        assert res.status_code == 200
        status_res = res.json()

        self.assertEqual(type(status_res), dict)
        self.assertTrue('acceptedQueryCount' in status_res)
        self.assertTrue('runningQueryCount' in status_res)
        self.assertTrue('queries' in status_res)
        self.assertEqual(status_res['acceptedQueryCount'], len(status_res['queries']))

        for q in status_res['queries']:
            if q['queryString'] == query:
                self.client.opencypher_cancel(q['queryId'])

        for t in threads:
            t.join()

    def test_opencypher_bolt_query_with_cancellation(self):
        pass
