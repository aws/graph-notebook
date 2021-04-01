import time

import pytest
import unittest

from botocore.session import get_session

from test.integration import IntegrationTest

TEST_BULKLOAD_SOURCE = 's3://aws-ml-customer-samples-%s/bulkload-datasets/%s/airroutes/v01'


@unittest.skip
class TestLoadWithIAM(IntegrationTest):
    def setUp(self) -> None:
        assert self.config.load_from_s3_arn != ''
        self.client = self.client_builder.with_iam(get_session()).build()

    @pytest.mark.neptune
    def test_iam_load(self):
        load_format = 'turtle'
        source = TEST_BULKLOAD_SOURCE % (self.config.aws_region, 'turtle')

        # for a full list of options, see https://docs.aws.amazon.com/neptune/latest/userguide/bulk-load-data.html
        kwargs = {
            'failOnError': "TRUE",
        }
        res = self.client.load(source, load_format, self.config.load_from_s3_arn, **kwargs)
        assert res.status_code == 200

        load_js = res.json()
        assert 'loadId' in load_js['payload']
        load_id = load_js['payload']['loadId']

        time.sleep(1)  # brief wait to ensure the load job can be obtained

        res = self.client.load_status(load_id, details="TRUE")
        assert res.status_code == 200

        load_status = res.json()
        assert 'overallStatus' in load_status['payload']
        status = load_status['payload']['overallStatus']
        assert status['fullUri'] == source

        res = self.client.cancel_load(load_id)
        assert res.status_code == 200

        time.sleep(5)
        res = self.client.load_status(load_id, details="TRUE")
        cancelled_status = res.json()
        assert 'LOAD_CANCELLED_BY_USER' in cancelled_status['payload']['feedCount'][-1]

    @pytest.mark.neptune
    def test_iam_load_status(self):
        res = self.client.load_status()  # This should only give a list of load ids
        assert res.status_code == 200

        js = res.json()
        assert 'loadIds' in js['payload']
        assert len(js['payload'].keys()) == 1
