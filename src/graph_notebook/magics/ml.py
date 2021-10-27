import argparse
import json
import datetime
import logging
import time

from IPython.core.display import display
from botocore.session import get_session
from ipywidgets import widgets
from requests import Response

from graph_notebook.neptune.client import Client, ClientBuilder

logger = logging.getLogger("neptune_ml_magic_handler")

DEFAULT_WAIT_INTERVAL = 60
DEFAULT_WAIT_TIMEOUT = 3600


def generate_neptune_ml_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help', dest='which')

    # Begin Export subparsers
    parser_export = subparsers.add_parser('export', help='')
    export_sub_parsers = parser_export.add_subparsers(help='', dest='which_sub')
    export_start_parser = export_sub_parsers.add_parser('start', help='start a new exporter job')
    export_start_parser.add_argument('--export-url', type=str,
                                     help='api gateway endpoint to call the exporter such as '
                                          'foo.execute-api.us-east-1.amazonaws.com/v1')
    export_start_parser.add_argument('--export-iam', action='store_true',
                                     help='flag for whether to sign requests to the export url with SigV4')
    export_start_parser.add_argument('--export-no-ssl', action='store_true',
                                     help='toggle ssl off when connecting to exporter')
    export_start_parser.add_argument('--wait', action='store_true', help='wait for the exporter to finish running')
    export_start_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                     help=f'time in seconds between export status check. '
                                          f'default: {DEFAULT_WAIT_INTERVAL}')
    export_start_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                     help=f'time in seconds to wait for a given export job to complete before '
                                          f'returning most recent status. default: {DEFAULT_WAIT_TIMEOUT}')
    export_start_parser.add_argument('--store-to', default='', dest='store_to',
                                     help='store result to this variable. If --wait is specified, will store the '
                                          'final status.')

    export_status_parser = export_sub_parsers.add_parser('status', help='obtain status of exporter job')
    export_status_parser.add_argument('--job-id', type=str, help='job id to check the status of')
    export_status_parser.add_argument('--export-url', type=str,
                                      help='api gateway endpoint to call the exporter such as '
                                           'foo.execute-api.us-east-1.amazonaws.com/v1')
    export_status_parser.add_argument('--export-iam', action='store_true',
                                      help='flag for whether to sign requests to the export url with SigV4')
    export_status_parser.add_argument('--export-no-ssl', action='store_true',
                                      help='toggle ssl off when connecting to exporter')
    export_status_parser.add_argument('--store-to', default='', dest='store_to',
                                      help='store result to this variable')
    export_status_parser.add_argument('--wait', action='store_true', help='wait for the exporter to finish running')
    export_status_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                      help=f'time in seconds between export status check. '
                                           f'default: {DEFAULT_WAIT_INTERVAL}')
    export_status_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                      help=f'time in seconds to wait for a given export job to complete before '
                                           f'returning most recent status. default: {DEFAULT_WAIT_TIMEOUT}')

    # Begin dataprocessing subparsers
    parser_dataprocessing = subparsers.add_parser('dataprocessing', help='')
    dataprocessing_subparsers = parser_dataprocessing.add_subparsers(help='dataprocessing sub-command',
                                                                     dest='which_sub')
    dataprocessing_start_parser = dataprocessing_subparsers.add_parser('start', help='start a new dataprocessing job')
    dataprocessing_start_parser.add_argument('--job-id', type=str, default='',
                                             help='the unique identifier for for this processing job')
    dataprocessing_start_parser.add_argument('--prev-job-id', type=str, default='',
                                             help='the job ID of a completed data processing job run on an earlier '
                                                  'version of the data.')
    dataprocessing_start_parser.add_argument('--s3-input-uri', type=str, default='',
                                             help='input data location in s3')
    dataprocessing_start_parser.add_argument('--s3-processed-uri', type=str, default='',
                                             help='processed data location in s3')
    dataprocessing_start_parser.add_argument('--sagemaker-iam-role-arn', type=str, default='',
                                             help='The ARN of an IAM role for SageMaker execution. '
                                                  'This must be listed in your DB cluster parameter group or an error '
                                                  'will occur. ')
    dataprocessing_start_parser.add_argument('--neptune-iam-role-arn', type=str, default='',
                                             help='The Amazon Resource Name (ARN) of an IAM role that SageMaker can '
                                                  'assume to perform tasks on your behalf. This must be listed in your '
                                                  'DB cluster parameter group or an error will occur.')
    dataprocessing_start_parser.add_argument('--instance-type', type=str, default='',
                                             help='The type of ML instance used during data processing.')
    dataprocessing_start_parser.add_argument('--instance-volume-size-in-gb', type=int, default=0,
                                             help='The disk volume size of the processing instance.')
    dataprocessing_start_parser.add_argument('--timeout-in-seconds', type=int, default=86400,
                                             help='Timeout in seconds for the data processing job.')
    dataprocessing_start_parser.add_argument('--model-type', type=str, default='',
                                             help='One of the two model types that Neptune ML currently supports: '
                                                  'heterogeneous graph models (heterogeneous), '
                                                  'and knowledge graph (kge).')
    dataprocessing_start_parser.add_argument('--subnets', type=list, default=[],
                                             help='The IDs of the subnets in the Neptune VPC')
    dataprocessing_start_parser.add_argument('--security-group-ids', type=list, default=[],
                                             help='The VPC security group IDs.')
    dataprocessing_start_parser.add_argument('--volume-encryption-kms-key', type=str, default='',
                                             help='The AWS Key Management Service (AWS KMS) key that SageMaker uses to '
                                                  'encrypt data on the storage volume attached to the ML compute '
                                                  'instances that run the processing job.')
    dataprocessing_start_parser.add_argument('--s3-output-encryption-kms-key', type=str, default='',
                                             help='The AWS Key Management Service (AWS KMS) key that SageMaker uses to '
                                                  'encrypt the output of the processing job.')
    dataprocessing_start_parser.add_argument('--config-file-name', type=str, default='')
    dataprocessing_start_parser.add_argument('--store-to', type=str, default='',
                                             help='store result to this variable')
    dataprocessing_start_parser.add_argument('--wait', action='store_true',
                                             help='wait for the exporter to finish running')
    dataprocessing_start_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                             help='wait interval between checks for export status')
    dataprocessing_start_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                             help='timeout while waiting for export job to complete')

    dataprocessing_status_parser = dataprocessing_subparsers.add_parser('status',
                                                                        help='obtain the status of an existing '
                                                                             'dataprocessing job')
    dataprocessing_status_parser.add_argument('--job-id', type=str)
    dataprocessing_status_parser.add_argument('--store-to', type=str, default='',
                                              help='store result to this variable')
    dataprocessing_status_parser.add_argument('--wait', action='store_true',
                                              help='wait for the exporter to finish running')
    dataprocessing_status_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                              help='wait interval between checks for export status')
    dataprocessing_status_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                              help='timeout while waiting for export job to complete')

    # Begin training subparsers
    parser_training = subparsers.add_parser('training', help='training command help')
    training_subparsers = parser_training.add_subparsers(help='training sub-command help',
                                                         dest='which_sub')
    training_start_parser = training_subparsers.add_parser('start', help='start a new training job')
    training_start_parser.add_argument('--job-id', type=str, default='')
    training_start_parser.add_argument('--data-processing-id', type=str, default='')
    training_start_parser.add_argument('--s3-output-uri', type=str, default='')
    training_start_parser.add_argument('--prev-job-id', type=str, default='',
                                       help='The job ID of a completed model-training job that you want to update '
                                            'incrementally based on updated data.')
    training_start_parser.add_argument('--sagemaker-iam-role-arn', type=str, default='',
                                       help='The ARN of an IAM role for SageMaker execution.')
    training_start_parser.add_argument('--neptune-iam-role-arn', type=str, default='',
                                       help='The ARN of an IAM role that provides Neptune access to SageMaker '
                                            'and Amazon S3 resources.')
    training_start_parser.add_argument('--model_name', type=str, default='',
                                       help='The model type for training. By default the ML model is automatically '
                                            'based on the modelType used in data processing, but you can specify a '
                                            'different model type here.')
    training_start_parser.add_argument('--base-processing-instance-type', type=str, default='',
                                       help='The type of ML instance used in preparing and managing training of '
                                            'ML models.')
    training_start_parser.add_argument('--instance-type', type=str, default='')
    training_start_parser.add_argument('--instance-volume-size-in-gb', type=int, default=0,
                                       help='The disk volume size of the training instance.')
    training_start_parser.add_argument('--timeout-in-seconds', type=int, default=86400,
                                       help='Timeout in seconds for the training job.')
    training_start_parser.add_argument('--max-hpo-number', type=int, default=2,
                                       help='Maximum total number of training jobs to start for the hyperparameter '
                                            'tuning job.')
    training_start_parser.add_argument('--max-hpo-parallel', type=int, default=2,
                                       help='Maximum number of parallel training jobs to start for the hyperparameter '
                                            'tuning job.')
    training_start_parser.add_argument('--subnets', type=list, default=[],
                                       help='The IDs of the subnets in the Neptune VPC')
    training_start_parser.add_argument('--security-group-ids', type=list, default=[],
                                       help='The VPC security group IDs.')
    training_start_parser.add_argument('--volume-encryption-kms-key', type=str, default='',
                                       help='The AWS Key Management Service (AWS KMS) key that SageMaker uses to '
                                            'encrypt data on the storage volume attached to the ML compute '
                                            'instances that run the training job.')
    training_start_parser.add_argument('--s3-output-encryption-kms-key', type=str, default='',
                                       help='The AWS Key Management Service (AWS KMS) key that SageMaker uses to '
                                            'encrypt the output of the training job.')
    training_start_parser.add_argument('--store-to', type=str, default='', help='store result to this variable')
    training_start_parser.add_argument('--wait', action='store_true',
                                       help='wait for the exporter to finish running')
    training_start_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                       help='wait interval between checks for export status')
    training_start_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                       help='timeout while waiting for export job to complete')

    training_status_parser = training_subparsers.add_parser('status',
                                                            help='obtain the status of an existing training job')
    training_status_parser.add_argument('--job-id', type=str)
    training_status_parser.add_argument('--store-to', type=str, default='', help='store result to this variable')
    training_status_parser.add_argument('--wait', action='store_true',
                                        help='wait for the exporter to finish running')
    training_status_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                        help='wait interval between checks for export status')
    training_status_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                        help='timeout while waiting for export job to complete')

    # Being modeltransform subparsers
    parser_modeltransform = subparsers.add_parser('modeltransform', help='modeltransform command help')

    # create
    modeltransform_subparsers = parser_modeltransform.add_subparsers(help='modeltransform subcommand help',
                                                                     dest='which_sub')
    modeltransform_start_parser = modeltransform_subparsers.add_parser('start', help='start a new modeltransform job')

    modeltransform_start_parser.add_argument('--job-id', type=str, default='',
                                             help='A unique identifier for the new job.')
    modeltransform_start_parser.add_argument('--s3-output-uri', type=str,
                                             default='The URI of the S3 bucket/location to store your transform '
                                                     'result.')
    modeltransform_start_parser.add_argument('--data-processing-job-id', type=str, default='',
                                             help='The job Id of a completed data-processing job. NOTE: You must '
                                                  'include either both the dataProcessingJobId and the '
                                                  'mlModelTrainingJobId parameters, or the trainingJobName parameter.')
    modeltransform_start_parser.add_argument('--model-training-job-id', type=str, default='',
                                             help='The job Id of a completed model-training job. NOTE: You must include'
                                                  ' either both the dataProcessingJobId and the mlModelTrainingJobId '
                                                  'parameters, or the trainingJobName parameter.')
    modeltransform_start_parser.add_argument('--training-job-name', type=str, default='',
                                             help='The name of a completed SageMaker training job. NOTE: You must '
                                                  'include either both the dataProcessingJobId and the '
                                                  'mlModelTrainingJobId parameters, or the trainingJobName parameter.')
    modeltransform_start_parser.add_argument('--sagemaker-iam-role-arn', type=str, default='',
                                             help='The ARN of an IAM role for SageMaker execution.')
    modeltransform_start_parser.add_argument('--neptune-iam-role-arn', type=str, default='',
                                             help='The ARN of an IAM role that provides Neptune access to SageMaker '
                                                  'and Amazon S3 resources.')
    modeltransform_start_parser.add_argument('--base-processing-instance-type', type=str, default='',
                                             help='The type of ML instance used in preparing and managing training of '
                                                  'ML models.')
    modeltransform_start_parser.add_argument('--base-processing-instance-volume-size-in-gb', type=int, default=0,
                                             help='The disk volume size of the training instance.')
    modeltransform_start_parser.add_argument('--subnets', type=list, default=[],
                                             help='The IDs of the subnets in the Neptune VPC')
    modeltransform_start_parser.add_argument('--security-group-ids', type=list, default=[],
                                             help='The VPC security group IDs.')
    modeltransform_start_parser.add_argument('--volume-encryption-kms-key', type=str, default='',
                                             help='The AWS Key Management Service (AWS KMS) key that SageMaker uses to '
                                                  'encrypt data on the storage volume attached to the ML compute '
                                                  'instances that run the transform job.')
    modeltransform_start_parser.add_argument('--s3-output-encryption-kms-key', type=str, default='',
                                             help='The AWS Key Management Service (AWS KMS) key that SageMaker uses to '
                                                  'encrypt the output of the transform job.')
    modeltransform_start_parser.add_argument('--wait', action='store_true')
    modeltransform_start_parser.add_argument('--store-to', default='', dest='store_to',
                                             help='store result to this variable. '
                                                  'If --wait is specified, will store the final status.')

    # status
    modeltransform_status_subparser = modeltransform_subparsers.add_parser('status',
                                                                           help='get status of a modeltransform job')
    modeltransform_status_subparser.add_argument('--job-id', type=str, required=True,
                                                 help='modeltransform job-id to obtain the status of')
    modeltransform_status_subparser.add_argument('--iam-role-arn', '-i', type=str, default='',
                                                 help='iam role arn to use for modeltransform')
    modeltransform_status_subparser.add_argument('--wait', action='store_true')
    modeltransform_status_subparser.add_argument('--store-to', default='', dest='store_to',
                                                 help='store result to this variable. If --wait is specified, '
                                                      'will store the final status.')

    # list
    modeltransform_list_subparser = modeltransform_subparsers.add_parser('list',
                                                                         help='obtain list of modeltransform jobs')
    modeltransform_list_subparser.add_argument('--max-items', type=int, help='max number of items to obtain',
                                               default=10)
    modeltransform_list_subparser.add_argument('--iam-role-arn', '-i', type=str, default='',
                                               help='iam role arn to use for modeltransform')
    modeltransform_list_subparser.add_argument('--store-to', default='', dest='store_to',
                                               help='store result to this variable.')

    # stop
    modeltransform_stop_subparser = modeltransform_subparsers.add_parser('stop', help='stop a modeltransform job')
    modeltransform_stop_subparser.add_argument('--job-id', type=str, help='modeltransform job id', default='')
    modeltransform_stop_subparser.add_argument('--clean', action='store_true', help='flag ')
    modeltransform_stop_subparser.add_argument('--iam-role-arn', '-i', type=str, default='',
                                               help='iam role arn to use for modeltransform')
    modeltransform_stop_subparser.add_argument('--store-to', default='', dest='store_to',
                                               help='store result to this variable.')

    # Begin endpoint subparsers
    parser_endpoint = subparsers.add_parser('endpoint', help='endpoint command help')
    endpoint_subparsers = parser_endpoint.add_subparsers(help='endpoint sub-command help',
                                                         dest='which_sub')
    endpoint_start_parser = endpoint_subparsers.add_parser('create', help='create a new endpoint')
    endpoint_start_parser.add_argument('--id', type=str, default='A unique identifier for the new inference endpoint.')
    endpoint_start_parser.add_argument('--model-training-job-id', type=str, default='',
                                       help='The job Id of the completed model-training job. '
                                            'You must supply either model-training-job-id or model-transform-job-id.')
    endpoint_start_parser.add_argument('--model-transform-job-id', type=str, default='',
                                       help='The job Id of the completed model-transform job. '
                                            'You must supply either model-training-job-id or model-transform-job-id.')
    endpoint_start_parser.add_argument('--update', action='store_true', default=False,
                                       help='If present, this parameter indicates that this is an update request.')
    endpoint_start_parser.add_argument('--neptune-iam-role-arn', type=str, default='',
                                       help='The ARN of an IAM role providing Neptune access to SageMaker and Amazon '
                                            'S3 resources.')
    endpoint_start_parser.add_argument('--model-name', type=str, default='',
                                       help='Model type for training.')
    endpoint_start_parser.add_argument('--instance-type', type=str, default='ml.r5.xlarge',
                                       help='The type of ML instance used for online servicing.')
    endpoint_start_parser.add_argument('--instance-count', type=int, default=1,
                                       help='The minimum number of Amazon EC2 instances to deploy to an endpoint for '
                                            'prediction.')
    endpoint_start_parser.add_argument('--volume-encryption-kms-key', type=str, default='',
                                       help='The AWS Key Management Service (AWS KMS) key that SageMaker uses to '
                                            'encrypt data on the storage volume attached to the ML compute instance(s) '
                                            'that run the endpoints.')
    endpoint_start_parser.add_argument('--store-to', type=str, default='', help='store result to this variable')
    endpoint_start_parser.add_argument('--wait', action='store_true',
                                       help='wait for the exporter to finish running')
    endpoint_start_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                       help='wait interval between checks for export status')
    endpoint_start_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                       help='timeout while waiting for export job to complete')

    endpoint_status_parser = endpoint_subparsers.add_parser('status',
                                                            help='obtain the status of an existing endpoint '
                                                                 'creation job')
    endpoint_status_parser.add_argument('--id', type=str, default='The ID of an existing inference endpoint.')
    endpoint_status_parser.add_argument('--store-to', type=str, default='', help='store result to this variable')
    endpoint_status_parser.add_argument('--wait', action='store_true',
                                        help='wait for the exporter to finish running')
    endpoint_status_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                        help='wait interval between checks for export status')
    endpoint_status_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                        help='timeout while waiting for export job to complete')

    return parser


def neptune_ml_export_start(client: Client, params, export_url: str, export_ssl: bool = True):
    if type(params) is str:
        params = json.loads(params)

    export_res = client.export(export_url, params, export_ssl)
    export_res.raise_for_status()
    job = export_res.json()
    return job


def neptune_ml_export_status(client: Client, export_url: str, job_id: str, export_ssl: bool = True):
    res = client.export_status(export_url, job_id, export_ssl)
    res.raise_for_status()
    job = res.json()
    return job


def wait_for_export(client: Client, export_url: str, job_id: str, output: widgets.Output,
                    export_ssl: bool = True, wait_interval: int = DEFAULT_WAIT_INTERVAL,
                    wait_timeout: int = DEFAULT_WAIT_TIMEOUT):
    job_id_output = widgets.Output()
    update_widget_output = widgets.Output()
    with output:
        display(job_id_output, update_widget_output)

    with job_id_output:
        print(f'Wait called on export job {job_id}')

    with update_widget_output:
        beginning_time = datetime.datetime.utcnow()
        while datetime.datetime.utcnow() - beginning_time < (datetime.timedelta(seconds=wait_timeout)):
            update_widget_output.clear_output()
            print('Checking for latest status...')
            status_res = client.export_status(export_url, job_id, export_ssl)
            status_res.raise_for_status()
            export_status = status_res.json()
            if export_status['status'] in ['succeeded', 'failed']:
                print('Export is finished')
                return export_status
            else:
                print(f'Status is {export_status["status"]}')
                print(f'Waiting for {wait_interval} before checking again...')
                time.sleep(wait_interval)


def neptune_ml_export(args: argparse.Namespace, client: Client, output: widgets.Output,
                      cell: str):
    # since the exporter is a different host than Neptune, it's IAM auth setting can be different
    # than the client we're using to connect to Neptune. Because of this, need o recreate out client before calling
    # any exporter urls to ensure we're signing any requests that we need to.
    builder = ClientBuilder().with_host(client.host) \
        .with_port(client.port) \
        .with_region(client.region) \
        .with_tls(client.ssl)

    if args.export_iam:
        builder = builder.with_iam(get_session())
    export_client = builder.build()

    export_ssl = not args.export_no_ssl
    if args.which_sub == 'start':
        if cell == '':
            return 'Cell body must have json payload or reference notebook variable using syntax ${payload_var}'
        export_job = neptune_ml_export_start(export_client, cell, args.export_url, export_ssl)
        if args.wait:
            return wait_for_export(export_client, args.export_url, export_job['jobId'],
                                   output, export_ssl, args.wait_interval, args.wait_timeout)
        else:
            return export_job
    elif args.which_sub == 'status':
        if args.wait:
            status = wait_for_export(export_client, args.export_url, args.job_id, output, export_ssl,
                                     args.wait_interval, args.wait_timeout)
        else:
            status_res = export_client.export_status(args.export_url, args.job_id, export_ssl)
            status_res.raise_for_status()
            status = status_res.json()
        return status


def wait_for_dataprocessing(job_id: str, client: Client, output: widgets.Output,
                            wait_interval: int = DEFAULT_WAIT_INTERVAL, wait_timeout: int = DEFAULT_WAIT_TIMEOUT):
    job_id_output = widgets.Output()
    update_status_output = widgets.Output()
    with output:
        display(job_id_output, update_status_output)

    with job_id_output:
        print(f'Wait called on dataprocessing job {job_id}')

    with update_status_output:
        beginning_time = datetime.datetime.utcnow()
        while datetime.datetime.utcnow() - beginning_time < (datetime.timedelta(seconds=wait_timeout)):
            update_status_output.clear_output()
            status_res = client.dataprocessing_job_status(job_id)
            status_res.raise_for_status()
            status = status_res.json()
            if status['status'] in ['Completed', 'Failed']:
                print('Data processing is finished')
                return status
            else:
                print(f'Status is {status["status"]}')
                print(f'Waiting for {wait_interval} before checking again...')
                time.sleep(wait_interval)


def neptune_ml_dataprocessing(args: argparse.Namespace, client, output: widgets.Output, params):
    if args.which_sub == 'start':
        if params is None or params == '' or params == {}:
            params = {
                'id': args.job_id,
                'configFileName': args.config_file_name
            }
            if args.prev_job_id:
                params['previousDataProcessingJobId'] = args.prev_job_id
            if args.instance_type:
                params['processingInstanceType'] = args.instance_type
            if args.instance_volume_size_in_gb:
                params['processingInstanceVolumeSizeInGB'] = args.instance_volume_size_in_gb
            if args.timeout_in_seconds:
                params['processingTimeOutInSeconds'] = args.timeout_in_seconds
            if args.model_type:
                params['modelType'] = args.model_type
            params = add_security_params(args, params)
            s3_input = args.s3_input_uri
            s3_output = args.s3_processed_uri
        else:
            try:
                if not isinstance(params, dict):
                    params = json.loads(params)
                if 'dataprocessing' in params:
                    params = params['dataprocessing']
                try:
                    if 'inputDataS3Location' in params:
                        s3_input = params['inputDataS3Location']
                    else:
                        s3_input = args.s3_input_uri
                    if 'processedDataS3Location' in params:
                        s3_output = params['processedDataS3Location']
                    else:
                        s3_output = args.s3_output_uri
                except AttributeError as e:
                    print(f"A required parameter has not been defined in params or args. Traceback: {e}")
            except (ValueError, AttributeError) as e:
                print("Error occurred while processing parameters. Please ensure your parameters are in JSON "
                      "format, and that you have defined both 'inputDataS3Location' and 'processedDataS3Location'.")

        processing_job_res = client.dataprocessing_start(s3_input, s3_output, **params)
        processing_job_res.raise_for_status()
        processing_job = processing_job_res.json()
        job_id = params['id'] if 'dataprocessing' not in params else params['dataprocessing']['id']
        if args.wait:
            try:
                wait_interval = params['wait_interval']
            except KeyError:
                wait_interval = args.wait_interval
            try:
                wait_timeout = params['wait_timeout']
            except KeyError:
                wait_timeout = args.wait_timeout
            return wait_for_dataprocessing(job_id, client, output, wait_interval, wait_timeout)
        else:
            return processing_job
    elif args.which_sub == 'status':
        if args.wait:
            return wait_for_dataprocessing(args.job_id, client, output, args.wait_interval, args.wait_timeout)
        else:
            processing_status = client.dataprocessing_job_status(args.job_id)
            processing_status.raise_for_status()
            return processing_status.json()
    else:
        return f'Sub parser "{args.which} {args.which_sub}" was not recognized'


def wait_for_training(job_id: str, client: Client, output: widgets.Output,
                      wait_interval: int = DEFAULT_WAIT_INTERVAL, wait_timeout: int = DEFAULT_WAIT_TIMEOUT):
    job_id_output = widgets.Output()
    update_status_output = widgets.Output()
    with output:
        display(job_id_output, update_status_output)

    with job_id_output:
        print(f'Wait called on training job {job_id}')

    with update_status_output:
        beginning_time = datetime.datetime.utcnow()
        while datetime.datetime.utcnow() - beginning_time < (datetime.timedelta(seconds=wait_timeout)):
            update_status_output.clear_output()
            training_status_res = client.modeltraining_job_status(job_id)
            training_status_res.raise_for_status()
            status = training_status_res.json()
            if status['status'] in ['Completed', 'Failed']:
                print('Training is finished')
                return status
            else:
                print(f'Status is {status["status"]}')
                print(f'Waiting for {wait_interval} before checking again...')
                time.sleep(wait_interval)


def neptune_ml_training(args: argparse.Namespace, client: Client, output: widgets.Output, params):
    if args.which_sub == 'start':
        if params is None or params == '' or params == {}:
            params = {
                "id": args.job_id,
                "dataProcessingJobId": args.data_processing_id,
                "trainingInstanceType": args.instance_type
            }
            if args.prev_job_id:
                params['previousModelTrainingJobId'] = args.prev_job_id
            if args.model_name:
                params['modelName'] = args.model_name
            if args.base_processing_instance_type:
                params['baseProcessingInstanceType'] = args.base_processing_instance_type
            if args.instance_volume_size_in_gb:
                params['trainingInstanceVolumeSizeInGB'] = args.instance_volume_size_in_gb
            if args.timeout_in_seconds:
                params['trainingTimeOutInSeconds'] = args.timeout_in_seconds
            params = add_security_params(args, params)
            data_processing_id = args.data_processing_id
            s3_output_uri = args.s3_output_uri
            max_hpo_number = args.max_hpo_number
            max_hpo_parallel = args.max_hpo_parallel
        else:
            try:
                if not isinstance(params, dict):
                    params = json.loads(params)
                if 'training' in params:
                    params = params['training']
                try:
                    if 'dataProcessingJobId' in params:
                        data_processing_id = params['dataProcessingJobId']
                    else:
                        data_processing_id = args.data_processing_id
                    if 'trainModelS3Location' in params:
                        s3_output_uri = params['trainModelS3Location']
                    else:
                        s3_output_uri = args.s3_output_uri
                    if 'maxHPONumberOfTrainingJobs' in params:
                        max_hpo_number = params['maxHPONumberOfTrainingJobs']
                    else:
                        max_hpo_number = args.max_hpo_number
                    if 'maxHPOParallelTrainingJobs' in params:
                        max_hpo_parallel = params['maxHPOParallelTrainingJobs']
                    else:
                        max_hpo_parallel = args.max_hpo_parallel
                except AttributeError as e:
                    print(f"A required parameter has not been defined in params or args. Traceback: {e}")
            except (ValueError, AttributeError) as e:
                print("Error occurred while processing parameters. Please ensure your parameters are in JSON "
                      "format, and that you have defined both all of the following options: dataProcessingJobId, "
                      "trainModelS3Location, maxHPONumberOfTrainingJobs, maxHPOParallelTrainingJobs.")

        start_training_res = client.modeltraining_start(data_processing_id, s3_output_uri,
                                                        max_hpo_number, max_hpo_parallel, **params)
        start_training_res.raise_for_status()
        training_job = start_training_res.json()
        if args.wait:
            try:
                wait_interval = params['wait_interval']
            except KeyError:
                wait_interval = args.wait_interval
            try:
                wait_timeout = params['wait_timeout']
            except KeyError:
                wait_timeout = args.wait_timeout
            return wait_for_training(training_job['id'], client, output, wait_interval, wait_timeout)
        else:
            return training_job
    elif args.which_sub == 'status':
        if args.wait:
            return wait_for_training(args.job_id, client, output, args.wait_interval, args.wait_timeout)
        else:
            training_status_res = client.modeltraining_job_status(args.job_id)
            training_status_res.raise_for_status()
            return training_status_res.json()
    else:
        return f'Sub parser "{args.which} {args.which_sub}" was not recognized'


def wait_for_endpoint(job_id: str, client: Client, output: widgets.Output,
                      wait_interval: int = DEFAULT_WAIT_INTERVAL, wait_timeout: int = DEFAULT_WAIT_TIMEOUT):
    job_id_output = widgets.Output()
    update_status_output = widgets.Output()
    with output:
        display(job_id_output, update_status_output)

    with job_id_output:
        print(f'Wait called on endpoint creation job {job_id}')

    with update_status_output:
        beginning_time = datetime.datetime.utcnow()
        while datetime.datetime.utcnow() - beginning_time < (datetime.timedelta(seconds=wait_timeout)):
            update_status_output.clear_output()
            endpoint_status_res = client.endpoints_status(job_id)
            endpoint_status_res.raise_for_status()
            status = endpoint_status_res.json()
            if status['status'] in ['InService', 'Failed']:
                print('Endpoint creation is finished')
                return status
            else:
                print(f'Status is {status["status"]}')
                print(f'Waiting for {wait_interval} before checking again...')
                time.sleep(wait_interval)


def neptune_ml_endpoint(args: argparse.Namespace, client: Client, output: widgets.Output, params):
    if args.which_sub == 'create':
        if params is None or params == '' or params == {}:
            params = {
                "id": args.id,
                'instanceType': args.instance_type
            }
            if args.update:
                params['update'] = args.update
            if args.neptune_iam_role_arn:
                params['neptuneIamRoleArn'] = args.neptune_iam_role_arn
            if args.model_name:
                params['modelName'] = args.model_name
            if args.instance_count:
                params['instanceCount'] = args.instance_count
            if args.volume_encryption_kms_key:
                params['volumeEncryptionKMSKey'] = args.volume_encryption_kms_key
            model_training_job_id = args.model_training_job_id
            model_transform_job_id = args.model_transform_job_id
        else:
            try:
                if not isinstance(params, dict):
                    params = json.loads(params)
                if 'endpoint' in params:
                    params = params['endpoint']

                has_training_id = False
                has_transform_id = False
                try:
                    if 'mlModelTrainingJobId' in params:
                        model_training_job_id = params['mlModelTrainingJobId']
                    else:
                        model_training_job_id = args.model_training_job_id
                    has_training_id = True
                except AttributeError:
                    pass
                try:
                    if 'mlModelTransformJobId' in params:
                        model_transform_job_id = params['mlModelTransformJobId']
                    else:
                        model_transform_job_id = args.model_transform_job_id
                    has_transform_id = True
                except AttributeError:
                    pass
                if not has_training_id and not has_transform_id:
                    print("You are required to define either mlModelTrainingJobId or mlModelTransformJobId as"
                          "an argument when creating an inference endpoint.")
            except (ValueError, AttributeError) as e:
                print("Error occurred while processing parameters. Please ensure your parameters are in JSON "
                      "format.")

        create_endpoint_res = client.endpoints_create(model_training_job_id, model_transform_job_id, **params)
        create_endpoint_res.raise_for_status()
        create_endpoint_job = create_endpoint_res.json()
        if args.wait:
            try:
                wait_interval = params['wait_interval']
            except KeyError:
                wait_interval = args.wait_interval
            try:
                wait_timeout = params['wait_timeout']
            except KeyError:
                wait_timeout = args.wait_timeout
            return wait_for_endpoint(create_endpoint_job['id'], client, output, wait_interval, wait_timeout)
        else:
            return create_endpoint_job
    elif args.which_sub == 'status':
        if args.wait:
            return wait_for_endpoint(args.id, client, output, args.wait_interval, args.wait_timeout)
        else:
            endpoint_status = client.endpoints_status(args.id)
            endpoint_status.raise_for_status()
            return endpoint_status.json()
    else:
        return f'Sub parser "{args.which} {args.which_sub}" was not recognized'


def modeltransform_wait(job_id: str, client: Client, output: widgets.Output,
                        wait_interval: int = DEFAULT_WAIT_INTERVAL, wait_timeout: int = DEFAULT_WAIT_TIMEOUT):
    job_id_output = widgets.Output()
    update_status_output = widgets.Output()
    with output:
        display(job_id_output, update_status_output)

    with job_id_output:
        print(f'Wait called on modeltransform job {job_id}')

    with update_status_output:
        beginning_time = datetime.datetime.utcnow()
        while datetime.datetime.utcnow() - beginning_time < (datetime.timedelta(seconds=wait_timeout)):
            update_status_output.clear_output()
            status_res = client.modeltransform_status(job_id)
            status_res.raise_for_status()
            status = status_res.json()
            if status['status'] in ['Completed', 'Failed', 'Stopped']:
                print('modeltransform is finished')
                return status
            else:
                print(f'Status is {status["status"]}')
                print(f'Waiting for {wait_interval} before checking again...')
                time.sleep(wait_interval)


def modeltransform_start(args: argparse.Namespace, client: Client, params):
    """
    Starts a new modeltransform job. If Params is not empty, we will attempt to parse it into JSON
    and use it as the command payload. Otherwise we will check args for the required parameters:
    """

    if params is None or params == '' or params == {}:
        data = {
            'id': args.job_id
        }
        if args.base_processing_instance_type:
            data['baseProcessingInstanceType'] = args.base_processing_instance_type
        if args.base_processing_instance_volume_size_in_gb:
            data['baseProcessingInstanceVolumeSizeInGB'] = args.base_processing_instance_volume_size_in_gb
        data = add_security_params(args, data)
        s3_output_uri = args.s3_output_uri
        data_processing_job_id = args.data_processing_job_id
        model_training_job_id = args.model_training_job_id
        training_job_name = args.training_job_name
    else:
        if type(params) is dict:
            data = params
        else:
            try:
                data = json.loads(params)
            except ValueError:
                print("Error: Unable to load modeltransform parameters. Please check that they are defined in JSON "
                      "format.")
        if 'modeltransform' in data:
            data = data['modeltransform']
        if 'modelTransformOutputS3Location' in data:
            s3_output_uri = data['modelTransformOutputS3Location']
        else:
            s3_output_uri = args.s3_output_uri
        has_dataprocessing_id = False
        has_training_id = False
        has_training_name = False
        try:
            if 'dataProcessingJobId' in data:
                data_processing_job_id = data['dataProcessingJobId']
            else:
                data_processing_job_id = args.data_processing_job_id
            has_dataprocessing_id = True
        except AttributeError:
            pass
        try:
            if 'mlModelTrainingJobId' in data:
                model_training_job_id = data['mlModelTrainingJobId']
            else:
                model_training_job_id = args.model_training_job_id
            has_training_id = True
        except AttributeError:
            pass
        try:
            if 'trainingJobName' in data:
                training_job_name = data['trainingJobName']
            else:
                training_job_name = args.training_job_name
            has_training_name = True
        except AttributeError:
            pass
        if not (has_dataprocessing_id and has_training_id) and not has_training_name:
            print("You are required to define either a) dataProcessingJobId AND mlModelTrainingJobId or "
                  "b) trainingJobName as arguments when creating a transform job.")

    res: Response = client.modeltransform_create(s3_output_uri, data_processing_job_id,
                                                 model_training_job_id, training_job_name, **data)
    res.raise_for_status()
    return res.json()


def modeltransform_status(args: argparse.Namespace, client: Client, output: widgets.Output):
    if args.wait:
        return modeltransform_wait(args.job_id, client, output)
    else:
        status_res = client.modeltransform_status(args.job_id)
        status_res.raise_for_status()
        return status_res.json()


def modeltransform_list(client: Client):
    list_res = client.modeltransform_list()
    list_res.raise_for_status()
    return list_res.json()


def modeltransform_stop(args: argparse.Namespace, client: Client):
    stop_res = client.modeltransform_stop(args.job_id)
    stop_res.raise_for_status()
    return f'Job cancelled, you can check its status by running the command "%neptune_ml modeltransform status ' \
           f'{args.job_id}"'


def neptune_ml_modeltransform(args: argparse.Namespace, client: Client, output: widgets.Output, params):
    """
    We have three possible variants when invoking the `%neptune_ml modeltransform` command:
        - start
        - status
        - list
        - stop

    NOTE: If params is a non-empty string, we will attempt to use it as the payload for the query.
    """
    if args.which_sub == 'start':
        create_res = modeltransform_start(args, client, params)
        if args.wait:
            return modeltransform_wait(create_res['id'], client, output)
        else:
            return create_res
    elif args.which_sub == 'status':
        return modeltransform_status(args, client, output)
    elif args.which_sub == 'list':
        return modeltransform_list(client)
    elif args.which_sub == 'stop':
        return modeltransform_stop(args, client)


def neptune_ml_magic_handler(args, client: Client, output: widgets.Output, cell: str = ''):
    logger.debug(f'neptune_ml_magic_handler called with cell: {cell}')
    if args.which == 'export':
        return neptune_ml_export(args, client, output, cell)
    elif args.which == 'dataprocessing':
        return neptune_ml_dataprocessing(args, client, output, cell)
    elif args.which == 'training':
        return neptune_ml_training(args, client, output, cell)
    elif args.which == 'endpoint':
        return neptune_ml_endpoint(args, client, output, cell)
    elif args.which == 'modeltransform':
        return neptune_ml_modeltransform(args, client, output, cell)
    else:
        return f'sub parser {args.which} was not recognized'


def add_security_params(args, params: dict):
    if args.sagemaker_iam_role_arn:
        params['sagemakerIamRoleArn'] = args.sagemaker_iam_role_arn
    if args.neptune_iam_role_arn:
        params['neptuneIamRoleArn'] = args.neptune_iam_role_arn
    if args.subnets:
        if all(isinstance(subnet, str) for subnet in []):
            params['subnets'] = args.subnets
        else:
            print('Ignoring subnets, list does not contain all strings.')
    if args.security_group_ids:
        if all(isinstance(security_group_id, str) for security_group_id in []):
            params['securityGroupIds'] = args.security_group_ids
        else:
            print('Ignoring security group IDs, list does not contain all strings.')
    if args.volume_encryption_kms_key:
        params['volumeEncryptionKMSKey'] = args.volume_encryption_kms_key
    if args.s3_output_encryption_kms_key:
        params['s3OutputEncryptionKMSKey'] = args.s3_output_encryption_kms_key

    return params
