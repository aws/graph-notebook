"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import concurrent.futures

import logging
import time
import pytest

from graph_notebook.neptune.client import Client
from test.integration import DataDrivenSparqlTest

logger = logging.getLogger('TestSparqlStatusWithoutIam')


def long_running_sparql_query(c: Client, query: str):
    res = c.sparql(query)
    return res


class TestSparqlStatusWithoutIam(DataDrivenSparqlTest):
    @pytest.mark.neptune
    def test_do_sparql_status_nonexistent(self):
        query_id = "invalid-guid"
        status_res = self.client.sparql_status(query_id)
        assert status_res.status_code == 200
        assert status_res.content == b''

    @pytest.mark.neptune
    def test_do_sparql_cancel_nonexistent(self):
        query_id = "invalid-guid"
        cancel_res = self.client.sparql_cancel(query_id)
        assert cancel_res.status_code == 400
        assert cancel_res.content == b'Invalid queryId (not a UUID): invalid-guid'

    @pytest.mark.neptune
    def test_do_sparql_cancel_empty_query_id(self):
        with pytest.raises(ValueError):
            self.client.sparql_cancel('')

    @pytest.mark.neptune
    def test_do_sparql_cancel_non_str_query_id(self):
        with pytest.raises(ValueError):
            self.client.sparql_cancel(42)

    @pytest.mark.neptune
    def test_do_sparql_status_and_cancel(self):
        query = "SELECT * WHERE { ?s ?p ?o . ?s2 ?p2 ?o2 .?s3 ?p3 ?o3 . ?s4 ?s5 ?s6 .} ORDER BY DESC(?s)"
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(long_running_sparql_query, self.client, query)
            time.sleep(1)

            status = self.client.sparql_status()
            status_res = status.json()
            assert 'acceptedQueryCount' in status_res
            assert 'runningQueryCount' in status_res
            assert 'queries' in status_res

            time.sleep(1)

            query_id = ''
            for q in status_res['queries']:
                if query in q['queryString']:
                    query_id = q['queryId']

            self.assertNotEqual(query_id, '')

            cancel = self.client.sparql_cancel(query_id, False)
            cancel_res = cancel.json()

            assert 'acceptedQueryCount' in cancel_res
            assert 'acceptedQueryCount' in cancel_res
            assert 'runningQueryCount' in cancel_res
            assert 'queries' in cancel_res

            res = future.result()
            assert res.status_code == 500
            raw = res.json()
            assert raw['code'] == 'CancelledByUserException'
            assert raw['detailedMessage'] == 'Operation terminated (cancelled by user)'

    @pytest.mark.neptune
    def test_do_sparql_status_and_cancel_silently(self):
        query = "SELECT * WHERE { ?s ?p ?o . ?s2 ?p2 ?o2 .?s3 ?p3 ?o3 . ?s4 ?s5 ?s6 .} ORDER BY DESC(?s)"
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(long_running_sparql_query, self.client, query)
            time.sleep(1)

            status = self.client.sparql_status()
            status_res = status.json()
            assert 'acceptedQueryCount' in status_res
            assert 'runningQueryCount' in status_res
            assert 'queries' in status_res

            time.sleep(1)

            query_id = ''
            for q in status_res['queries']:
                if query in q['queryString']:
                    query_id = q['queryId']

            assert query_id != ''

            cancel = self.client.sparql_cancel(query_id, True)
            cancel_res = cancel.json()
            assert 'acceptedQueryCount' in cancel_res
            assert 'runningQueryCount' in cancel_res
            assert 'queries' in cancel_res

            res = future.result()
            query_res = res.json()
            assert type(query_res) is dict
            assert 's3' in query_res['head']['vars']
            assert 'p3' in query_res['head']['vars']
            assert 'o3' in query_res['head']['vars']
            assert [] == query_res['results']['bindings']
