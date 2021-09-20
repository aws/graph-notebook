"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest

from test.integration import IntegrationTest


class TestOpenCypher(IntegrationTest):
    @pytest.mark.opencypher
    @pytest.mark.neptune
    def test_do_oc_query(self):
        query = 'MATCH (n) RETURN n LIMIT 1'
        oc_http = self.client.opencypher_http(query)
        assert oc_http.status_code == 200
        results = oc_http.json()
        assert type(results["results"]) is list

        for r in results["results"]:
            assert type(r) is dict

        self.assertEqual(type(results["results"]), list)

    @pytest.mark.opencypher
    @pytest.mark.bolt
    def test_do_oc_bolt_query(self):
        query = 'MATCH (p) RETURN p LIMIT 10'
        res = self.client.opencyper_bolt(query)
        assert len(res) == 10
