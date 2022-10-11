"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest
from botocore.session import get_session

from test.integration import IntegrationTest


class TestPropertyGraphStatisticsWithIAM(IntegrationTest):
    def setUp(self) -> None:
        super().setUp()
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_propertygraph_statistics_status(self):
        expected_payload_fields = ['autoCompute', 'active', 'statisticsId']
        res = self.client.statistics('pg')
        assert res.status_code == 200
        statistics_status = res.json()
        self.assertEqual(statistics_status['status'], '200 OK')
        res_payload_fields = list(statistics_status['payload'].keys())
        for x in expected_payload_fields:
            self.assertIn(x, res_payload_fields)

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_propertygraph_statistics_disable_autocompute(self):
        expected = {
            "status": "200 OK"
        }
        disable_res = self.client.statistics('pg', 'disableAutoCompute')
        assert disable_res.status_code == 200
        disable_status = disable_res.json()
        self.assertEqual(disable_status, expected)

        status_res = self.client.statistics('pg')
        statistics_status = status_res.json()
        self.assertEqual(statistics_status['payload']['autoCompute'], False)

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_propertygraph_statistics_enable_autocompute(self):
        expected = {
            "status": "200 OK"
        }
        enable_res = self.client.statistics('pg', 'enableAutoCompute')
        assert enable_res.status_code == 200
        enable_status = enable_res.json()
        self.assertEqual(enable_status, expected)

        status_res = self.client.statistics('pg')
        statistics_status = status_res.json()
        self.assertEqual(statistics_status['payload']['autoCompute'], True)

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_propertygraph_statistics_refresh(self):
        res = self.client.statistics('pg')
        assert res.status_code == 200
        statistics_status = res.json()
        self.assertEqual(statistics_status['status'], '200 OK')
        self.assertIn("statisticsId", statistics_status['payload'])

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_propertygraph_statistics_delete(self):
        expected = {
            "status": "200 OK",
            "payload": {
                "active": False,
                "statisticsId": -1
            }
        }
        res = self.client.statistics('pg', 'delete')
        assert res.status_code == 200
        statistics_status = res.json()
        self.assertEqual(statistics_status, expected)

