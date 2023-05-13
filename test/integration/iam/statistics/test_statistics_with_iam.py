"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest
from botocore.session import get_session

from test.integration import IntegrationTest
from parameterized import parameterized

lang_list = ["pg", "sparql"]


class TestStatisticsWithIAM(IntegrationTest):
    def setUp(self) -> None:
        super().setUp()
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.neptune
    @pytest.mark.iam
    @parameterized.expand(lang_list)
    def test_statistics_status(self, lang):
        expected_payload_fields = ['autoCompute', 'active', 'statisticsId']
        res = self.client.statistics(lang)
        assert res.status_code == 200
        statistics_status = res.json()
        self.assertEqual(statistics_status['status'], '200 OK')
        res_payload_fields = list(statistics_status['payload'].keys())
        for x in expected_payload_fields:
            self.assertIn(x, res_payload_fields)

    @pytest.mark.neptune
    @pytest.mark.iam
    @parameterized.expand(lang_list)
    def test_statistics_disable_autocompute(self, lang):
        expected = {
            "status": "200 OK"
        }
        disable_res = self.client.statistics(lang, False, 'disableAutoCompute')
        assert disable_res.status_code == 200
        disable_status = disable_res.json()
        self.assertEqual(disable_status, expected)

        status_res = self.client.statistics(lang)
        statistics_status = status_res.json()
        self.assertEqual(statistics_status['payload']['autoCompute'], False)

    @pytest.mark.neptune
    @pytest.mark.iam
    @parameterized.expand(lang_list)
    def test_statistics_enable_autocompute(self, lang):
        expected = {
            "status": "200 OK"
        }
        enable_res = self.client.statistics(lang, False, 'enableAutoCompute')
        assert enable_res.status_code == 200
        enable_status = enable_res.json()
        self.assertEqual(enable_status, expected)

        status_res = self.client.statistics(lang)
        statistics_status = status_res.json()
        self.assertEqual(statistics_status['payload']['autoCompute'], True)

    @pytest.mark.neptune
    @pytest.mark.iam
    @parameterized.expand(lang_list)
    def test_statistics_refresh(self, lang):
        res = self.client.statistics(lang)
        assert res.status_code == 200
        statistics_status = res.json()
        self.assertEqual(statistics_status['status'], '200 OK')
        self.assertIn("statisticsId", statistics_status['payload'])

    @pytest.mark.neptune
    @pytest.mark.iam
    @parameterized.expand(lang_list)
    def test_statistics_delete(self, lang):
        expected = {
            "status": "200 OK",
            "payload": {
                "active": False,
                "statisticsId": -1
            }
        }
        res = self.client.statistics(lang, False, 'delete')
        assert res.status_code == 200
        statistics_status = res.json()
        self.assertEqual(statistics_status, expected)
