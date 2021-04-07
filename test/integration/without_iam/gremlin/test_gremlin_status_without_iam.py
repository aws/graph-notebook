"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import threading
import time

import pytest
import concurrent.futures
from os import cpu_count

from gremlin_python.driver.protocol import GremlinServerError

from graph_notebook.neptune.client import Client
from test.integration import DataDrivenGremlinTest


def long_running_gremlin_query(c: Client, query: str):
    res = c.gremlin_query(query)
    return res


class TestGremlinStatusWithoutIam(DataDrivenGremlinTest):
    @pytest.mark.neptune
    def test_do_gremlin_status_nonexistent(self):
        query_id = "some-guid-here"
        res = self.client.gremlin_status(query_id)
        assert res.status_code == 400
        js = res.json()
        assert js['code'] == 'InvalidParameterException'
        assert js['detailedMessage'] == f'Supplied queryId {query_id} is invalid'

    @pytest.mark.neptune
    def test_do_gremlin_cancel_nonexistent(self):
        query_id = "some-guid-here"
        res = self.client.gremlin_cancel(query_id)
        assert res.status_code == 400
        js = res.json()
        assert js['code'] == 'InvalidParameterException'
        assert js['detailedMessage'] == f'Supplied queryId {query_id} is invalid'

    @pytest.mark.neptune
    def test_do_gremlin_cancel_empty_query_id(self):
        with self.assertRaises(ValueError):
            self.client.gremlin_cancel('')

    @pytest.mark.neptune
    def test_do_gremlin_cancel_non_str_query_id(self):
        with self.assertRaises(ValueError):
            self.client.gremlin_cancel(42)

    @pytest.mark.neptune
    def test_do_gremlin_status_and_cancel(self):
        long_running_query = "g.V().out().out().out().out().out().out().out().out()"
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(long_running_gremlin_query, self.client, long_running_query)

            time.sleep(1)
            status_res = self.client.gremlin_status()
            assert status_res.status_code == 200

            status_js = status_res.json()
            query_id = ''
            for q in status_js['queries']:
                if q['queryString'] == long_running_query:
                    query_id = q['queryId']

            assert query_id != ''

            cancel_res = self.client.gremlin_cancel(query_id)
            assert cancel_res.status_code == 200
            assert cancel_res.json()['status'] == '200 OK'

            time.sleep(1)
            status_after_cancel = self.client.gremlin_status(query_id)
            assert status_after_cancel.status_code == 400  # check that the query is no longer valid
            assert status_after_cancel.json()['code'] == 'InvalidParameterException'

            with pytest.raises(GremlinServerError):
                # this result corresponds to the cancel query, so our gremlin client will raise an exception
                future.result()

    @pytest.mark.iam
    @pytest.mark.neptune
    def test_do_gremlin_status_include_waiting(self):
        query = "g.V().out().out().out().out()"
        num_threads = cpu_count() * 4
        threads = []
        for x in range(0, num_threads):
            thread = threading.Thread(target=long_running_gremlin_query, args=(self.client, query))
            thread.start()
            threads.append(thread)

        time.sleep(5)

        res = self.client.gremlin_status(include_waiting=True)
        assert res.status_code == 200
        status_res = res.json()

        self.assertEqual(type(status_res), dict)
        self.assertTrue('acceptedQueryCount' in status_res)
        self.assertTrue('runningQueryCount' in status_res)
        self.assertTrue('queries' in status_res)
        self.assertEqual(status_res['acceptedQueryCount'], len(status_res['queries']))

        for q in status_res['queries']:
            # cancel all the queries we executed since they can take a very long time.
            if q['queryString'] == query:
                self.client.gremlin_cancel(q['queryId'])

        for t in threads:
            t.join()
