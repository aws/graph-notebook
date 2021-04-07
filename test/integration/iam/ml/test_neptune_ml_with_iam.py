"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging
import os
import threading
import time
import unittest

import pytest
from botocore.session import get_session

from graph_notebook.configuration.get_config import get_config
from test.integration import IntegrationTest
from test.integration.iam.ml import setup_iam_client

logger = logging.getLogger()


@unittest.skip
class TestNeptuneMLWithIAM(IntegrationTest):
    def setUp(self) -> None:
        self.client = self.client_builder.with_iam(get_session()).build()

    def tearDown(self) -> None:
        endpoint_ids = client.endpoints().json()['ids']
        for endpoint_id in endpoint_ids:
            self.client.endpoints_delete(endpoint_id)

        client.close()

    @pytest.mark.neptuneml
    @pytest.mark.iam
    def test_neptune_ml_e2e(self):
        s3_input_uri = os.getenv('NEPTUNE_ML_DATAPROCESSING_S3_INPUT', '')
        s3_processed_uri = os.getenv('NEPTUNE_ML_DATAPROCESSING_S3_PROCESSED', '')
        train_model_s3_location = os.getenv('NEPTUNE_ML_TRAINING_S3_LOCATION', '')

        assert s3_input_uri != ''
        assert s3_processed_uri != ''
        assert train_model_s3_location != ''

        logger.info("dataprocessing...")
        dataprocessing_job = do_dataprocessing(s3_input_uri, s3_processed_uri)
        dataprocessing_id = dataprocessing_job['id']

        p = threading.Thread(target=wait_for_dataprocessing_complete, args=(dataprocessing_id,))
        p.start()
        p.join(3600)

        logger.info("model training...")
        training_job = do_modeltraining(dataprocessing_id, train_model_s3_location)
        training_job_id = training_job['id']

        p = threading.Thread(target=wait_for_modeltraining_complete, args=(training_job_id,))
        p.start()
        p.join(3600)

        logger.info("endpoint...")
        endpoint_job = do_create_endpoint(training_job_id)
        endpoint_job_id = endpoint_job['id']
        p = threading.Thread(target=wait_for_endpoint_complete, args=(endpoint_job_id,))
        p.start()
        p.join(3600)

    @pytest.mark.neptuneml
    @pytest.mark.iam
    def test_neptune_ml_dataprocessing_status(self):
        status = client.dataprocessing_status()

        assert status.status_code == 200
        assert 'ids' in status.json()

    @pytest.mark.neptuneml
    @pytest.mark.iam
    def test_neptune_ml_modeltraining_status(self):
        status = client.modeltraining_status()
        assert status.status_code == 200
        assert 'ids' in status.json()

    @pytest.mark.neptuneml
    @pytest.mark.iam
    def test_neptune_ml_training(self):
        dataprocessing_id = os.getenv('NEPTUNE_ML_DATAPROCESSING_ID', '')
        train_model_s3_location = os.getenv('NEPTUNE_ML_TRAINING_S3_LOCATION', '')

        assert dataprocessing_id != ''
        assert train_model_s3_location != ''

        dataprocessing_status = client.dataprocessing_job_status(dataprocessing_id)
        assert dataprocessing_status.status_code == 200

        job_start_res = client.modeltraining_start(dataprocessing_id, train_model_s3_location)
        assert job_start_res.status_code == 200

        job_id = job_start_res.json()['id']
        training_status_res = client.modeltraining_job_status(job_id)
        assert training_status_res.status_code == 200

        job_stop_res = client.modeltraining_stop(job_id, clean=True)
        assert job_stop_res.status_code == 200


def setup_module():
    global client
    client = setup_iam_client(get_config())


def teardown_module():
    endpoint_ids = client.endpoints().json()['ids']
    for endpoint_id in endpoint_ids:
        client.endpoints_delete(endpoint_id)

    client.close()


def do_dataprocessing(s3_input, s3_processed) -> dict:
    logger.info(f"starting dataprocessing job with input={s3_input} and processed={s3_processed}")
    dataprocessing_res = client.dataprocessing_start(s3_input, s3_processed)
    assert dataprocessing_res.status_code == 200
    return dataprocessing_res.json()


def wait_for_dataprocessing_complete(dataprocessing_id: str):
    logger.info(f"waiting for dataprocessing job {dataprocessing_id} to complete")
    while True:
        status = client.dataprocessing_job_status(dataprocessing_id)
        assert status.status_code == 200
        raw = status.json()
        logger.info(f"status is {raw['status']}")
        if raw['status'] != 'InProgress':
            assert raw['status'] == 'Completed'
            return raw
        logger.info("waiting for 10 seconds then checking again")
        time.sleep(10)


def do_modeltraining(dataprocessing_id, train_model_s3_location):
    logger.info(
        f"starting training job from dataprocessing_job_id={dataprocessing_id} and training_model_s3_location={train_model_s3_location}")
    training_start = client.modeltraining_start(dataprocessing_id, train_model_s3_location)
    assert training_start.status_code == 200
    return training_start.json()


def wait_for_modeltraining_complete(training_job: str) -> dict:
    logger.info(f"waiting for modeltraining job {training_job} to complete")
    while True:
        status = client.modeltraining_job_status(training_job)
        assert status.status_code == 200
        raw = status.json()
        logger.info(f"status is {raw['status']}")
        if raw['status'] != 'InProgress':
            assert raw['status'] == 'Completed'
            return raw
        logger.info("waiting for 10 seconds then checking again")
        time.sleep(10)


def do_create_endpoint(training_job_id: str) -> dict:
    endpoint_res = client.endpoints_create(training_job_id)
    assert endpoint_res.status_code == 200
    return endpoint_res.json()


def wait_for_endpoint_complete(endpoint_job_id):
    logger.info(f"waiting for endpoint creation job {endpoint_job_id} to complete")
    while True:
        endpoint_status = client.endpoints_status(endpoint_job_id)
        assert endpoint_status.status_code == 200
        raw = endpoint_status.json()
        logger.info(f"status is {raw['status']}")
        if raw['status'] != 'Creating':
            assert raw['status'] == 'InService'
            return raw
        logger.info("waiting for 10 seconds then checking again")
        time.sleep(10)
