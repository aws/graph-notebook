"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import pytest

from test.integration import GraphNotebookIntegrationTest


class TestGraphMagicStatus(GraphNotebookIntegrationTest):
    @pytest.mark.jupyter
    @pytest.mark.neptune
    def test_status(self):
        res = self.ip.run_line_magic('status', '')
        self.assertEqual('healthy', res['status'])
