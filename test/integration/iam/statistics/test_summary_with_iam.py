"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest
from botocore.session import get_session

from test.integration import IntegrationTest
from parameterized import parameterized

lang_list = ["pg", "sparql"]
summary_detailed_fields_pg = ["nodeStructures", "edgeStructures"]
summary_detailed_fields_rdf = ["subjectStructures"]


class TestSummaryWithIAM(IntegrationTest):
    def setUp(self) -> None:
        super().setUp()
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.neptune
    @pytest.mark.iam
    @parameterized.expand(lang_list)
    def test_summary_default(self, lang):
        expected_payload_fields = ['version', 'lastStatisticsComputationTime', 'graphSummary']
        res = self.client.statistics(lang, True)
        assert res.status_code == 200
        summary_default = res.json()
        self.assertEqual(summary_default['status'], '200 OK')
        res_payload_fields = list(summary_default['payload'].keys())
        for x in expected_payload_fields:
            self.assertIn(x, res_payload_fields)

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_summary_basic_pg(self):
        res = self.client.statistics("pg", True, "basic")
        assert res.status_code == 200
        summary_pg_basic = res.json()
        self.assertEqual(summary_pg_basic['status'], '200 OK')
        summary_pg_fields = list(summary_pg_basic['payload']['graphSummary'].keys())

        self.assertIn("numNodes", summary_pg_fields)
        for x in summary_detailed_fields_pg:
            self.assertNotIn(x, summary_pg_fields)

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_summary_basic_rdf(self):
        res = self.client.statistics("rdf", True, "basic")
        assert res.status_code == 200
        summary_rdf_basic = res.json()
        self.assertEqual(summary_rdf_basic['status'], '200 OK')
        summary_rdf_fields = list(summary_rdf_basic['payload']['graphSummary'].keys())

        self.assertIn("numDistinctSubjects", summary_rdf_fields)
        for x in summary_detailed_fields_rdf:
            self.assertNotIn(x, summary_rdf_fields)

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_summary_detailed_pg(self):
        res = self.client.statistics("pg", True, "detailed")
        assert res.status_code == 200
        summary_pg_detailed = res.json()
        self.assertEqual(summary_pg_detailed['status'], '200 OK')
        summary_pg_fields = list(summary_pg_detailed['payload']['graphSummary'].keys())

        for x in summary_detailed_fields_pg:
            self.assertIn(x, summary_pg_fields)

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_summary_detailed_rdf(self):
        res = self.client.statistics("rdf", True, "detailed")
        assert res.status_code == 200
        summary_rdf_detailed = res.json()
        self.assertEqual(summary_rdf_detailed['status'], '200 OK')
        summary_rdf_fields = list(summary_rdf_detailed['payload']['graphSummary'].keys())

        for x in summary_detailed_fields_rdf:
            self.assertIn(x, summary_rdf_fields)
