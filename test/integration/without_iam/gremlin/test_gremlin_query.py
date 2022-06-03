"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest
from gremlin_python.structure.graph import Vertex

from test.integration import IntegrationTest


class TestGremlin(IntegrationTest):
    @pytest.mark.gremlin
    def test_do_gremlin_query(self):
        query = 'g.V().limit(1)'
        results = self.client.gremlin_query(query)
        assert type(results) is list
        for r in results:
            assert type(r) is Vertex

        self.assertEqual(type(results), list)

    @pytest.mark.gremlin
    def test_do_gremlin_query_with_content_limit_exceeded(self):
        query = 'g.V().limit(1)'
        transport_args = {'max_content_length': 1}
        with self.assertRaises(RuntimeError):
            self.client.gremlin_query(query, transport_args=transport_args)

    @pytest.mark.gremlin
    def test_do_gremlin_query_with_content_limit_not_exceeded(self):
        query = 'g.V().limit(1)'
        transport_args = {'max_content_length': 10240}
        results = self.client.gremlin_query(query, transport_args=transport_args)
        self.assertEqual(type(results), list)

    @pytest.mark.gremlin
    @pytest.mark.neptune
    def test_do_gremlin_explain(self):
        query = 'g.V().limit(1)'
        res = self.client.gremlin_explain(query)
        assert res.status_code == 200
        results = res.content.decode('utf-8')
        self.assertTrue('Explain' in results)

    @pytest.mark.gremlin
    @pytest.mark.neptune
    def test_do_gremlin_profile(self):
        query = 'g.V().limit(1)'
        res = self.client.gremlin_profile(query)
        assert res.status_code == 200

        results = res.content.decode('utf-8')
        self.assertTrue('Profile' in results)
