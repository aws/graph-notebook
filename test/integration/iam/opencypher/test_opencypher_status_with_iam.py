"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import threading

import logging
import time

import pytest
import requests
from botocore.session import get_session

from test.integration.DataDrivenOpenCypherTest import DataDrivenOpenCypherTest

logger = logging.getLogger('TestOpenCypherStatusWithoutIam')


class TestOpenCypherStatusWithIam(DataDrivenOpenCypherTest):
    def do_opencypher_query_save_result(self, query, res):
        try:
            result = self.client.opencypher_http(query)
            result.raise_for_status()
            res['result'] = result.json()
        except requests.HTTPError as exception:
            res['error'] = exception.response.json()

    def setUp(self) -> None:
        super().setUp()
        self.client = self.client_builder.with_iam(get_session()).build()

        status_res = self.client.opencypher_status()
        assert status_res.status_code == 200
        res = status_res.json()
        for q in res['queries']:
            self.client.opencypher_cancel(q['queryId'])

    def test_do_opencypher_status_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        status_res = self.client.opencypher_status(query_id)
        assert status_res.status_code != 200
        err = status_res.json()
        self.assertEqual(err['code'], "InvalidParameterException")
        expected_message = f'Supplied queryId {query_id} is invalid'
        self.assertEqual(err['detailedMessage'], expected_message)

    def test_do_opencypher_cancel_nonexistent(self):
        query_id = "ac7d5a03-00cf-4280-b464-edbcbf51ffce"
        cancel_res = self.client.opencypher_cancel(query_id)
        assert cancel_res.status_code != 200
        err = cancel_res.json()
        self.assertEqual(err['code'], "InvalidParameterException")
        expected_message = f'Supplied queryId {query_id} is invalid'
        self.assertEqual(err['detailedMessage'], expected_message)

    def test_do_opencypher_cancel_empty_query_id(self):
        with pytest.raises(ValueError) as err:
            self.client.opencypher_cancel('')
        assert err.type is ValueError

    def test_do_opencypher_cancel_non_str_query_id(self):
        with pytest.raises(ValueError) as err:
            self.client.opencypher_cancel(42)
        assert err.type is ValueError

    def test_do_opencypher_status_and_cancel(self):
        query = '''MATCH(a)-->(b)
                    MATCH(c)-->(d)
                    MATCH(e)-->(f)
                    RETURN a,b,c,d,e,f
                    ORDER BY a'''
        query_res = {}
        oc_query_thread = threading.Thread(target=self.do_opencypher_query_save_result, args=(query, query_res,))
        oc_query_thread.start()
        time.sleep(1)

        status = self.client.opencypher_status()
        status_res = status.json()
        assert type(status_res) is dict
        assert 'acceptedQueryCount' in status_res
        assert 'runningQueryCount' in status_res
        assert status_res['runningQueryCount'] >= 1
        assert 'queries' in status_res

        query_id = ''
        for q in status_res['queries']:
            if query in q['queryString']:
                query_id = q['queryId']

        assert query_id != ''

        cancel = self.client.opencypher_cancel(query_id)
        assert cancel.status_code == 200
        cancel_res = cancel.json()
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
                    MATCH(e)-->(f)
                    RETURN a,b,c,d,e,f
                    ORDER BY a'''

        query_res = {}
        oc_query_thread = threading.Thread(target=self.do_opencypher_query_save_result, args=(query, query_res,))
        oc_query_thread.start()
        time.sleep(1)

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

        cancel = self.client.opencypher_cancel(query_id, silent=True)
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
