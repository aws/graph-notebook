"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging
import os
import threading
import time

import pytest
from botocore.session import get_session

from graph_notebook.configuration.get_config import get_config
from test.integration import GraphNotebookIntegrationTest
from test.integration.iam.ml import setup_iam_client

logger = logging.getLogger()

NEPTUNE_ML_DATAPROCESSING_S3_INPUT = os.getenv('NEPTUNE_ML_DATAPROCESSING_S3_INPUT')
NEPTUNE_ML_DATAPROCESSING_S3_PROCESSED = os.getenv('NEPTUNE_ML_DATAPROCESSING_S3_PROCESSED')
NEPTUNE_ML_TRAINING_OUTPUT = os.getenv('NEPTUNE_ML_TRAINING_OUTPUT')
NEPTUNE_ML_COMPLETED_DATAPROCESSING_JOB_ID = os.getenv('NEPTUNE_ML_COMPLETED_DATAPROCESSING_JOB_ID')
NEPTUNE_ML_IAM_ROLE_ARN = os.getenv('NEPTUNE_ML_IAM_ROLE_ARN')
NEPTUNE_ML_COMPLETED_TRAINING_ID = os.getenv('NEPTUNE_ML_COMPLETED_TRAINING_ID')
NEPTUNE_ML_TRANSFORM_OUTPUT = 's3://akline-misc/transform'
NEPTUNE_ML_MAX_TOTAL_HPO_TRAINING_JOBS = 2
NEPTUNE_ML_MAX_PARALLEL_HPO_TRAINING_JOBS = 2


class TestNeptuneMLWithIAM(GraphNotebookIntegrationTest):
    def setUp(self) -> None:
        super(TestNeptuneMLWithIAM, self).setUp()
        assert NEPTUNE_ML_DATAPROCESSING_S3_INPUT is not None
        assert NEPTUNE_ML_DATAPROCESSING_S3_PROCESSED is not None
        assert NEPTUNE_ML_IAM_ROLE_ARN is not None
        assert NEPTUNE_ML_TRAINING_OUTPUT is not None

        self.client = self.client_builder.with_iam(get_session()).build()

    def tearDown(self) -> None:
        res = client.endpoints()
        res.raise_for_status()
        endpoint_res = res.json()
        endpoint_ids = endpoint_res['ids']
        for endpoint_id in endpoint_ids:
            self.client.endpoints_delete(endpoint_id)

        client.close()

    def test_neptuneml_magic(self):
        data = {
            'output_s3_location': 's3://akline-misc/transform',
            'dataprocessing_job_id': NEPTUNE_ML_COMPLETED_DATAPROCESSING_JOB_ID,
            'modeltraining_job_id': NEPTUNE_ML_COMPLETED_TRAINING_ID
        }

        cell = '''{
    "output_s3_location": "s3://akline-misc/transform",
    "dataprocessing_job_id": "node-classification-1621962877",
    "modeltraining_job_id": "node-classification-1621962877"
}'''
        self.ip.user_ns['create_input'] = data
        self.ip.run_cell_magic('neptune_ml', 'modeltransform create --wait', cell)
        # create_res = self.ip.run_cell_magic('neptune_ml', 'modeltransform create --wait', cell)
        # assert create_res.status_code == 200
        pass

    def test_neptune_ml_dataprocessing(self):
        params = {
            'neptuneIamRoleArn': NEPTUNE_ML_IAM_ROLE_ARN,
            'configFileName': 'training-job-configuration.json'
        }
        res = self.client.dataprocessing_start(NEPTUNE_ML_DATAPROCESSING_S3_INPUT,
                                               NEPTUNE_ML_DATAPROCESSING_S3_PROCESSED, **params)
        assert res.status_code == 200
        response = res.json()
        dataprocessing_id = response['id']

        time.sleep(30)
        status_res = self.client.dataprocessing_job_status(dataprocessing_id)
        assert status_res.status_code == 200

        list_res = self.client.dataprocessing_list()
        assert list_res.status_code == 200
        ids = list_res.json()['ids']
        assert dataprocessing_id in ids

        delete_res = self.client.dataprocessing_stop(dataprocessing_id, True)
        assert delete_res.status_code == 200

    def test_neptune_ml_modeltraining(self):
        training_res = self.client.modeltraining_start(NEPTUNE_ML_COMPLETED_DATAPROCESSING_JOB_ID,
                                                       NEPTUNE_ML_TRAINING_OUTPUT,
                                                       NEPTUNE_ML_MAX_TOTAL_HPO_TRAINING_JOBS,
                                                       NEPTUNE_ML_MAX_PARALLEL_HPO_TRAINING_JOBS)
        assert training_res.status_code == 200
        training = training_res.json()

        modeltraining_id = training['id']

        time.sleep(30)

        list_res = self.client.modeltraining_list()
        assert list_res.status_code == 200
        ids = list_res.json()['ids']
        assert modeltraining_id in ids

        status_res = self.client.modeltraining_job_status(modeltraining_id)
        assert status_res.status_code == 200

        delete_res = self.client.modeltraining_stop(modeltraining_id)
        assert delete_res.status_code == 200

    def test_neptune_ml_modeltransform(self):
        create_res = self.client.modeltransform_create(output_s3_location=NEPTUNE_ML_TRANSFORM_OUTPUT,
                                                       dataprocessing_job_id=NEPTUNE_ML_COMPLETED_DATAPROCESSING_JOB_ID,
                                                       modeltraining_job_id=NEPTUNE_ML_COMPLETED_TRAINING_ID)
        assert create_res.status_code == 200

        create = create_res.json()
        transform_id = create['id']

        time.sleep(30)

        status_res = self.client.modeltransform_status(transform_id)
        assert status_res.status_code == 200

        list_res = self.client.modeltraining_list()
        assert list_res.status_code == 200
        assert transform_id in list_res.json()['ids']

        stop_res = self.client.modeltransform_stop(transform_id)
        assert stop_res.status_code == 200

    def test_neptune_ml_endpoint(self):
        pass

    @pytest.mark.neptuneml
    @pytest.mark.iam
    def test_neptune_ml_e2e(self):
        s3_input_uri = os.getenv('NEPTUNE_ML_DATAPROCESSING_S3_INPUT', '')
        s3_processed_uri = os.getenv('NEPTUNE_ML_DATAPROCESSING_S3_PROCESSED', '')
        train_model_s3_location = os.getenv('NEPTUNE_ML_TRAINING_S3_LOCATION', '')
        hpo_number = NEPTUNE_ML_MAX_TOTAL_HPO_TRAINING_JOBS
        hpo_parallel = NEPTUNE_ML_MAX_PARALLEL_HPO_TRAINING_JOBS

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
        training_job = do_modeltraining(dataprocessing_id, train_model_s3_location, hpo_number, hpo_parallel)
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
        status = client.dataprocessing_list()

        assert status.status_code == 200
        assert 'ids' in status.json()

    @pytest.mark.neptuneml
    @pytest.mark.iam
    def test_neptune_ml_modeltraining_status(self):
        status = client.modeltraining_list()
        assert status.status_code == 200
        assert 'ids' in status.json()

    @pytest.mark.neptuneml
    @pytest.mark.iam
    def test_neptune_ml_training(self):
        dataprocessing_id = os.getenv('NEPTUNE_ML_DATAPROCESSING_ID', '')
        train_model_s3_location = os.getenv('NEPTUNE_ML_TRAINING_S3_LOCATION', '')
        hpo_number = NEPTUNE_ML_MAX_TOTAL_HPO_TRAINING_JOBS
        hpo_parallel = NEPTUNE_ML_MAX_PARALLEL_HPO_TRAINING_JOBS

        assert dataprocessing_id != ''
        assert train_model_s3_location != ''

        dataprocessing_status = client.dataprocessing_job_status(dataprocessing_id)
        assert dataprocessing_status.status_code == 200

        job_start_res = client.modeltraining_start(dataprocessing_id, train_model_s3_location, hpo_number, hpo_parallel)
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


def do_modeltraining(dataprocessing_id, train_model_s3_location, hpo_number, hpo_parallel):
    logger.info(
        f"starting training job from dataprocessing_job_id={dataprocessing_id} "
        f"and training_model_s3_location={train_model_s3_location}")
    training_start = client.modeltraining_start(dataprocessing_id, train_model_s3_location, hpo_number, hpo_parallel)
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
    endpoint_res = client.endpoints_create(model_training_job_id=training_job_id)
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
