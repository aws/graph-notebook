"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest
from botocore.session import get_session
from gremlin_python.structure.graph import Vertex

from test.integration import IntegrationTest


class TestGremlinWithIam(IntegrationTest):
    def setUp(self) -> None:
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.iam
    @pytest.mark.gremlin
    def test_do_gremlin_query_with_iam(self):
        query = 'g.V().limit(1)'
        results = self.client.gremlin_query(query)
        assert type(results) is list
        for r in results:
            assert type(r) is Vertex

    @pytest.mark.iam
    @pytest.mark.gremlin
    def test_do_gremlin_explain_with_iam(self):
        query = 'g.V().limit(1)'
        res = self.client.gremlin_explain(query)
        assert res.status_code == 200
        results = res.content.decode('utf-8')
        self.assertTrue('Explain' in results)

    @pytest.mark.iam
    @pytest.mark.gremlin
    def test_do_gremlin_profile_with_iam(self):
        query = 'g.V().limit(1)'
        res = self.client.gremlin_profile(query)
        assert res.status_code == 200

        results = res.content.decode('utf-8')
        self.assertTrue('Profile' in results)

    @pytest.mark.iam
    @pytest.mark.gremlin
    def test_iam_gremlin_http_query(self):
        query = 'g.V().limit(1)'
        res = self.client.gremlin_http_query(query)
        assert res.status_code == 200
        assert 'result' in res.json()

    def test_iam_gremlin_connection(self):
        conn = self.client.get_gremlin_connection()
        conn.submit('g.V().limit(1)')
        assert True  # if we got here then everything worked
