from requests.exceptions import HTTPError

from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.request_param_generator.factory import create_request_generator
from graph_notebook.system.database_reset import initiate_database_reset, perform_database_reset
from test.integration import IntegrationTest


class TestStatusWithIAM(IntegrationTest):
    def test_do_db_reset_initiate_with_iam_credentials(self):
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        result = initiate_database_reset(self.host, self.port, self.ssl, request_generator)
        self.assertNotEqual(result['payload']['token'], '')

    def test_do_db_reset_perform_with_wrong_token_with_iam_credentials(self):
        request_generator = create_request_generator(AuthModeEnum.IAM, IAMAuthCredentialsProvider.ENV)
        with self.assertRaises(HTTPError) as cm:
            perform_database_reset('x', self.host, self.port, self.ssl, request_generator)
        expected_message = "System command parameter 'token' : 'x' does not match database reset token"
        self.assertEqual(expected_message, str(cm.exception.response.json()['detailedMessage']))

    def test_do_db_reset_initiate_without_iam_credentials(self):
        with self.assertRaises(HTTPError):
            initiate_database_reset(self.host, self.port, self.ssl)
