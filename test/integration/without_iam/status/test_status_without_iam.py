"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest

from test.integration import IntegrationTest


class TestStatusWithoutIAM(IntegrationTest):

    @pytest.mark.neptune
    def test_do_status(self):
        res = self.client.status()
        status = res.json()
        self.assertEqual(status['status'], 'healthy')
