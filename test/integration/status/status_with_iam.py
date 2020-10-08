"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from requests.exceptions import HTTPError

from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.request_param_generator.factory import create_request_generator
from graph_notebook.status.get_status import get_status

from test.integration import IntegrationTest


class TestStatusWithIAM(IntegrationTest):
    def test_do_status_with_iam_credentials(self):
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        status = get_status(self.host, self.port, self.ssl, request_generator)
        self.assertEqual(status['status'], 'healthy')

    def test_do_status_without_iam_credentials(self):
        with self.assertRaises(HTTPError):
            get_status(self.host, self.port, self.ssl)
