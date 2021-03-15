"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import time
from threading import Thread

from requests import HTTPError

from graph_notebook.opencypher import do_opencypher_query
from test.integration.notebook.GraphNotebookIntegrationTest import GraphNotebookIntegrationTest


class TestGraphMagicGremlin(GraphNotebookIntegrationTest):
    def handle_cancelled_query(self, query):
        with self.assertRaises(HTTPError) as http_error:
            do_opencypher_query(query, self.host, self.port, self.ssl, self.request_generator)
        res = http_error.exception.response.json()
        self.assertEqual('CancelledByUserException', res['code'])

    def test_oc_query(self):
        query = 'MATCH(n) RETURN n LIMIT 1'
        store_to_var = 'oc_res'
        self.ip.run_cell_magic('oc', f'--store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        oc_res = self.ip.user_ns[store_to_var]
        self.assertTrue('n' in oc_res['head']['vars'])

    def test_oc_query_bolt(self):
        query = 'MATCH(n) RETURN n LIMIT 100'
        store_to_var = 'oc_res'
        self.ip.run_cell_magic('oc', f'bolt --store-to {store_to_var}', query)
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        oc_res = self.ip.user_ns[store_to_var]
        self.assertTrue('n' in oc_res['head']['vars'])

    def test_oc_query_malformed(self):
        query = 'This is invalid'
        self.ip.run_cell_magic('oc', '', query)
        self.assertTrue('graph_notebook_error' in self.ip.user_ns)
        err: HTTPError = self.ip.user_ns['graph_notebook_error']
        err_js = err.response.json()
        self.assertEqual('MalformedQueryException', err_js['code'])

    def test_oc_status(self):
        store_to_var = 'oc_status'
        self.ip.run_cell(f'%oc_status --store-to {store_to_var}')
        self.assertFalse('graph_notebook_error' in self.ip.user_ns)
        oc_res = self.ip.user_ns[store_to_var]
        self.assertTrue('acceptedQueryCount' in oc_res)
        self.assertTrue('runningQueryCount' in oc_res)
        self.assertTrue('queries' in oc_res)

    def test_oc_status_and_cancel(self):
        status_var = 'status_res'
        cancel_var = 'cancel_res'
        long_running_query = 'MATCH(a)-->(b)\nMATCH(c)-->(d)\nRETURN a,b,c,d'

        query_thread = Thread(target=self.handle_cancelled_query, args=(long_running_query,))
        query_thread.start()
        time.sleep(1)

        status_cell = f'%oc_status --store-to {status_var}'
        self.ip.run_cell(status_cell)
        status = self.ip.user_ns[status_var]

        query_id = ''
        for q in status['queries']:
            if q['queryString'] == long_running_query:
                query_id = q['queryId']
                break

        self.assertNotEqual(query_id, '')
        cancel_cell = f'%oc_status --queryId {query_id} -c  --store-to {cancel_var}'
        self.ip.run_cell(cancel_cell)
        cancel_res = self.ip.user_ns[cancel_var]
        self.assertEqual(cancel_res['status'], '200 OK')
        self.assertTrue(cancel_res['payload'])
        query_thread.join()

    def test_cancel_query_invalid_id(self):
        if 'graph_notebook_error' in self.ip.user_ns:
            del self.ip.user_ns['graph_notebook_error']
        cancel_var = 'res'
        cancel_cell = f'%oc_status --queryId this-is-invalid -c  --store-to {cancel_var}'
        self.ip.run_cell(cancel_cell)
        err: HTTPError = self.ip.user_ns['graph_notebook_error']
        err_js = err.response.json()
        self.assertEqual(err_js['code'], 'InvalidParameterException')
