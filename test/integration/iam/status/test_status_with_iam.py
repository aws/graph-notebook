"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest
from botocore.session import get_session

from test.integration import IntegrationTest


class TestStatusWithIAM(IntegrationTest):
    def setUp(self) -> None:
        super().setUp()
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_do_status_with_iam_credentials(self):
        res = self.client.status()
        assert res.status_code == 200
        status = res.json()
        self.assertEqual(status['status'], 'healthy')

    @pytest.mark.neptune
    @pytest.mark.iam
    def test_do_status_without_iam_credentials(self):
        client = self.client_builder.with_iam(None).build()
        res = client.status()
        assert res.status_code != 200
