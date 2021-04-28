import datetime
import time

import pytest
from botocore.session import get_session
from test.integration import IntegrationTest


class TestStatusWithIAM(IntegrationTest):
    def setUp(self) -> None:
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.iam
    @pytest.mark.neptune
    def test_do_db_reset_initiate_with_iam_credentials(self):
        token = self.client.initiate_reset()
        result = token.json()
        self.assertNotEqual(result['payload']['token'], '')

    @pytest.mark.iam
    @pytest.mark.neptune
    def test_do_db_reset_perform_with_wrong_token_with_iam_credentials(self):
        res = self.client.perform_reset('invalid')
        assert res.status_code == 400

        expected_message = "System command parameter 'token' : 'invalid' does not match database reset token"
        assert expected_message == res.json()['detailedMessage']

    @pytest.mark.iam
    @pytest.mark.neptune
    def test_do_db_reset_initiate_without_iam_credentials(self):
        client = self.client_builder.with_iam(None).build()
        res = client.initiate_reset()
        assert res.status_code == 403

    @pytest.mark.iam
    @pytest.mark.neptune
    @pytest.mark.reset
    def test_iam_fast_reset(self):
        initiate_reset_res = self.client.initiate_reset()
        assert initiate_reset_res.status_code == 200

        token = initiate_reset_res.json()['payload']['token']
        reset_res = self.client.perform_reset(token)
        assert reset_res.json()['status'] == '200 OK'

        # check for status for 5 minutes while reset is performed
        end_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        status = None
        while end_time >= datetime.datetime.now():
            try:
                status = self.client.status()
                if status.status_code != 200:
                    time.sleep(5)  # wait momentarily until we obtain the status again
                else:
                    break
            except Exception:
                time.sleep(5)

        assert status.status_code == 200
