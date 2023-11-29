"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest
from botocore.session import get_session

from test.integration.DataDrivenOpenCypherTest import DataDrivenOpenCypherTest


class TestOpenCypherQueryWithIam(DataDrivenOpenCypherTest):
    def setUp(self) -> None:
        super().setUp()
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.neptune
    @pytest.mark.opencypher
    def test_do_opencypher_query(self):
        expected_league_name = 'English Premier League'
        query = 'MATCH (l:League) RETURN l.name'
        oc_res = self.client.opencypher_http(query)
        assert oc_res.status_code == 200

        res = oc_res.json()
        assert isinstance(res, dict)
        assert expected_league_name == res['results'][0]['l.name']

    @pytest.mark.opencypher
    @pytest.mark.bolt
    def test_do_opencypher_bolt_query(self):
        query = 'MATCH (p) RETURN p LIMIT 10'
        res = self.client.opencyper_bolt(query)
        assert len(res) == 10
