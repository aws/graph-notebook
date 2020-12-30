import argparse
import json
import datetime
import logging
import time
from IPython.core.display import display
from ipywidgets import widgets

from graph_notebook.authentication.iam_credentials_provider.credentials_factory import credentials_provider_factory
from graph_notebook.authentication.iam_credentials_provider.credentials_provider import Credentials
from graph_notebook.configuration.generate_config import Configuration, AuthModeEnum
from graph_notebook.magics.parsing import str_to_namespace_var
from graph_notebook.ml.sagemaker import start_export, get_export_status, start_processing_job, get_processing_status, \
    start_training, get_training_status, start_create_endpoint, get_endpoint_status, EXPORT_SERVICE_NAME

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
                                     help='api gateway endpoint to call the exporter such as foo.execute-api.us-east-1.amazonaws.com/v1')
    export_start_parser.add_argument('--export-iam', action='store_true',
                                     help='flag for whether to sign requests to the export url with SigV4')
    export_start_parser.add_argument('--export-no-ssl', action='store_true',
                                     help='toggle ssl off when connecting to exporter')
    export_start_parser.add_argument('--wait', action='store_true', help='wait for the exporter to finish running')
    export_start_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                     help=f'time in seconds between export status check. default: {DEFAULT_WAIT_INTERVAL}')
    export_start_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                     help=f'time in seconds to wait for a given export job to complete before returning most recent status. default: {DEFAULT_WAIT_TIMEOUT}')
    export_start_parser.add_argument('--store-to', default='', dest='store_to',
                                     help='store result to this variable. If --wait is specified, will store the final status.')

    export_status_parser = export_sub_parsers.add_parser('status', help='obtain status of exporter job')
    export_status_parser.add_argument('--job-id', type=str, help='job id to check the status of')
    export_status_parser.add_argument('--export-url', type=str,
                                      help='api gateway endpoint to call the exporter such as foo.execute-api.us-east-1.amazonaws.com/v1')
    export_status_parser.add_argument('--export-iam', action='store_true',
                                      help='flag for whether to sign requests to the export url with SigV4')
    export_status_parser.add_argument('--export-no-ssl', action='store_true',
                                      help='toggle ssl off when connecting to exporter')
    export_status_parser.add_argument('--store-to', default='', dest='store_to',
                                      help='store result to this variable')
    export_status_parser.add_argument('--wait', action='store_true', help='wait for the exporter to finish running')
    export_status_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                      help=f'time in seconds between export status check. default: {DEFAULT_WAIT_INTERVAL}')
    export_status_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                      help=f'time in seconds to wait for a given export job to complete before returning most recent status. default: {DEFAULT_WAIT_TIMEOUT}')

    # Begin dataprocessing subparsers
    parser_dataprocessing = subparsers.add_parser('dataprocessing', help='')
    dataprocessing_subparsers = parser_dataprocessing.add_subparsers(help='dataprocessing sub-command',
                                                                     dest='which_sub')
    dataprocessing_start_parser = dataprocessing_subparsers.add_parser('start', help='start a new dataprocessing job')
    dataprocessing_start_parser.add_argument('--job-id', type=str,
                                             default='the unique identifier for for this processing job')
    dataprocessing_start_parser.add_argument('--s3-input-uri', type=str, default='input data location in s3')
    dataprocessing_start_parser.add_argument('--s3-processed-uri', type=str, default='processed data location in s3')
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
                                                                        help='obtain the status of an existing dataprocessing job')
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
    training_start_parser.add_argument('--instance-type', type=str, default='')
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

    # Begin endpoint subparsers
    parser_endpoint = subparsers.add_parser('endpoint', help='endpoint command help')
    endpoint_subparsers = parser_endpoint.add_subparsers(help='endpoint sub-command help',
                                                         dest='which_sub')
    endpoint_start_parser = endpoint_subparsers.add_parser('create', help='create a new endpoint')
    endpoint_start_parser.add_argument('--job-id', type=str, default='')
    endpoint_start_parser.add_argument('--model-job-id', type=str, default='')
    endpoint_start_parser.add_argument('--instance-type', type=str, default='ml.r5.xlarge')
    endpoint_start_parser.add_argument('--store-to', type=str, default='', help='store result to this variable')
    endpoint_start_parser.add_argument('--wait', action='store_true',
                                       help='wait for the exporter to finish running')
    endpoint_start_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                       help='wait interval between checks for export status')
    endpoint_start_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                       help='timeout while waiting for export job to complete')

    endpoint_status_parser = endpoint_subparsers.add_parser('status',
                                                            help='obtain the status of an existing endpoint creation job')
    endpoint_status_parser.add_argument('--job-id', type=str, default='')
    endpoint_status_parser.add_argument('--store-to', type=str, default='', help='store result to this variable')
    endpoint_status_parser.add_argument('--wait', action='store_true',
                                        help='wait for the exporter to finish running')
    endpoint_status_parser.add_argument('--wait-interval', default=DEFAULT_WAIT_INTERVAL, type=int,
                                        help='wait interval between checks for export status')
    endpoint_status_parser.add_argument('--wait-timeout', default=DEFAULT_WAIT_TIMEOUT, type=int,
                                        help='timeout while waiting for export job to complete')

    return parser


def neptune_ml_export_start(params, export_url: str, export_ssl: bool = True, creds: Credentials = None):
    if type(params) is str:
        params = json.loads(params)

    job = start_export(export_url, params, export_ssl, creds)
    return job


def wait_for_export(export_url: str, job_id: str, output: widgets.Output,
                    export_ssl: bool = True, wait_interval: int = DEFAULT_WAIT_INTERVAL,
                    wait_timeout: int = DEFAULT_WAIT_TIMEOUT, creds: Credentials = None):
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
            export_status = get_export_status(export_url, export_ssl, job_id, creds)
            if export_status['status'] in ['succeeded', 'failed']:
                print('Export is finished')
                return export_status
            else:
                print(f'Status is {export_status["status"]}')
                print(f'Waiting for {wait_interval} before checking again...')
                time.sleep(wait_interval)


def neptune_ml_export(args: argparse.Namespace, config: Configuration, output: widgets.Output, cell: str):
    auth_mode = AuthModeEnum.IAM if args.export_iam else AuthModeEnum.DEFAULT
    creds = None
    if auth_mode == AuthModeEnum.IAM:
        creds = credentials_provider_factory(config.iam_credentials_provider_type).get_iam_credentials()

    export_ssl = not args.export_no_ssl
    if args.which_sub == 'start':
        if cell == '':
            return 'Cell body must have json payload or reference notebook variable using syntax ${payload_var}'
        export_job = neptune_ml_export_start(cell, args.export_url, export_ssl, creds)
        if args.wait:
            return wait_for_export(args.export_url, export_job['jobId'],
                                   output, export_ssl, args.wait_interval, args.wait_timeout, creds)
        else:
            return export_job
    elif args.which_sub == 'status':
        if args.wait:
            status = wait_for_export(args.export_url, args.job_id, output, export_ssl, args.wait_interval,
                                     args.wait_timeout, creds)
        else:
            status = get_export_status(args.export_url, export_ssl, args.job_id, creds)
        return status


def wait_for_dataprocessing(job_id: str, config: Configuration, request_param_generator, output: widgets.Output,
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
            status = get_processing_status(config.host, str(config.port), config.ssl, request_param_generator, job_id)
            if status['status'] in ['Completed', 'Failed']:
                print('Data processing is finished')
                return status
            else:
                print(f'Status is {status["status"]}')
                print(f'Waiting for {wait_interval} before checking again...')
                time.sleep(wait_interval)


def neptune_ml_dataprocessing(args: argparse.Namespace, request_param_generator, output: widgets.Output,
                              config: Configuration, params: dict = None):
    if args.which_sub == 'start':
        if params is None or params == '' or params == {}:
            params = {
                'inputDataS3Location': args.s3_input_uri,
                'processedDataS3Location': args.s3_processed_uri,
                'id': args.job_id,
                'configFileName': args.config_file_name
            }

        processing_job = start_processing_job(config.host, str(config.port), config.ssl,
                                              request_param_generator, params)
        job_id = params['id']
        if args.wait:
            return wait_for_dataprocessing(job_id, config, request_param_generator,
                                           output, args.wait_interval, args.wait_timeout)
        else:
            return processing_job
    elif args.which_sub == 'status':
        if args.wait:
            return wait_for_dataprocessing(args.job_id, config, request_param_generator, output, args.wait_interval,
                                           args.wait_timeout)
        else:
            return get_processing_status(config.host, str(config.port), config.ssl, request_param_generator,
                                         args.job_id)
    else:
        return f'Sub parser "{args.which} {args.which_sub}" was not recognized'


def wait_for_training(job_id: str, config: Configuration, request_param_generator, output: widgets.Output,
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
            status = get_training_status(config.host, str(config.port), config.ssl, request_param_generator, job_id)
            if status['status'] in ['Completed', 'Failed']:
                print('Training is finished')
                return status
            else:
                print(f'Status is {status["status"]}')
                print(f'Waiting for {wait_interval} before checking again...')
                time.sleep(wait_interval)


def neptune_ml_training(args: argparse.Namespace, request_param_generator, config: Configuration,
                        output: widgets.Output, params):
    if args.which_sub == 'start':
        if params is None or params == '' or params == {}:
            params = {
                "id": args.job_id,
                "dataProcessingJobId": args.data_processing_id,
                "trainingInstanceType": args.instance_type,
                "trainModelS3Location": args.s3_output_uri
            }

        training_job = start_training(config.host, str(config.port), config.ssl, request_param_generator, params)
        if args.wait:
            return wait_for_training(training_job['id'], config, request_param_generator, output, args.wait_interval,
                                     args.wait_timeout)
        else:
            return training_job
    elif args.which_sub == 'status':
        if args.wait:
            return wait_for_training(args.job_id, config, request_param_generator, output, args.wait_interval,
                                     args.wait_timeout)
        else:
            return get_training_status(config.host, str(config.port), config.ssl, request_param_generator,
                                       args.job_id)
    else:
        return f'Sub parser "{args.which} {args.which_sub}" was not recognized'


def wait_for_endpoint(job_id: str, config: Configuration, request_param_generator, output: widgets.Output,
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
            status = get_endpoint_status(config.host, str(config.port), config.ssl, request_param_generator, job_id)
            if status['status'] in ['InService', 'Failed']:
                print('Endpoint creation is finished')
                return status
            else:
                print(f'Status is {status["status"]}')
                print(f'Waiting for {wait_interval} before checking again...')
                time.sleep(wait_interval)


def neptune_ml_endpoint(args: argparse.Namespace, request_param_generator,
                        config: Configuration, output: widgets.Output, params):
    if args.which_sub == 'create':
        if params is None or params == '' or params == {}:
            params = {
                "id": args.job_id,
                "mlModelTrainingJobId": args.model_job_id,
                'instanceType': args.instance_type
            }

        create_endpoint_job = start_create_endpoint(config.host, str(config.port), config.ssl,
                                                    request_param_generator, params)

        if args.wait:
            return wait_for_endpoint(create_endpoint_job['id'], config, request_param_generator, output,
                                     args.wait_interval, args.wait_timeout)
        else:
            return create_endpoint_job
    elif args.which_sub == 'status':
        if args.wait:
            return wait_for_endpoint(args.job_id, config, request_param_generator, output,
                                     args.wait_interval, args.wait_timeout)
        else:
            return get_endpoint_status(config.host, str(config.port), config.ssl, request_param_generator, args.job_id)
    else:
        return f'Sub parser "{args.which} {args.which_sub}" was not recognized'


def neptune_ml_magic_handler(args, request_param_generator, config: Configuration, output: widgets.Output,
                             cell: str = '', local_ns: dict = None) -> any:
    if local_ns is None:
        local_ns = {}
    cell = str_to_namespace_var(cell, local_ns)

    if args.which == 'export':
        return neptune_ml_export(args, config, output, cell)
    elif args.which == 'dataprocessing':
        return neptune_ml_dataprocessing(args, request_param_generator, output, config, cell)
    elif args.which == 'training':
        return neptune_ml_training(args, request_param_generator, config, output, cell)
    elif args.which == 'endpoint':
        return neptune_ml_endpoint(args, request_param_generator, config, output, cell)
    else:
        return f'sub parser {args.which} was not recognized'
