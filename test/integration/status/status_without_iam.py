"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from graph_notebook.status.get_status import get_status

from test.integration import IntegrationTest


class TestStatusWithoutIAM(IntegrationTest):
    def test_do_status(self):
        status = get_status(self.host, self.port, self.ssl)
        self.assertEqual(status['status'], 'healthy')
