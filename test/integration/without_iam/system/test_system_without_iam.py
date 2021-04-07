import pytest
from test.integration import IntegrationTest


class TestStatusWithoutIAM(IntegrationTest):

    @pytest.mark.neptune
    def test_do_database_reset_initiate(self):
        res = self.client.initiate_reset()
        result = res.json()
        self.assertNotEqual(result['payload']['token'], '')

    @pytest.mark.neptune
    def test_do_database_reset_perform_with_wrong_token(self):
        res = self.client.perform_reset('invalid')
        assert res.status_code == 400
        expected_message = "System command parameter 'token' : 'invalid' does not match database reset token"
        assert expected_message == res.json()['detailedMessage']
