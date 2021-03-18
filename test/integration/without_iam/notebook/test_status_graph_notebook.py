"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest
from botocore.session import get_session

from test.integration.without_iam.notebook import GraphNotebookIntegrationTest


class TestGraphMagicStatus(GraphNotebookIntegrationTest):
    def setUp(self) -> None:
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.jupyter
    @pytest.mark.neptune
    def test_status(self):
        res = self.ip.run_line_magic('status', '')
        self.assertEqual('healthy', res['status'])
