from requests.exceptions import HTTPError
from graph_notebook.system.database_reset import initiate_database_reset, perform_database_reset
from test.integration import IntegrationTest


class TestStatusWithoutIAM(IntegrationTest):
    def test_do_database_reset_initiate(self):
        result = initiate_database_reset(self.host, self.port, self.ssl)
        self.assertNotEqual(result['payload']['token'], '')

    def test_do_database_reset_perform_with_wrong_token(self):
        with self.assertRaises(HTTPError) as cm:
            perform_database_reset('x', self.host, self.port, self.ssl)
        expected_message = "System command parameter 'token' : 'x' does not match database reset token"
        self.assertEqual(expected_message, str(cm.exception.response.json()['detailedMessage']))
