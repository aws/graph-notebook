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

    # Being modeltransform subparsers
    parser_modeltransform = subparsers.add_parser('modeltransform', help='modeltransform command help')

    # create
    modeltransform_subparsers = parser_modeltransform.add_subparsers(help='modeltransform subcommand help',
                                                                     dest='which_sub')
    modeltransform_create_parser = modeltransform_subparsers.add_parser('create', help='start a new modeltransform job')
    modeltransform_create_parser.add_argument('--wait', action='store_true')
    modeltransform_create_parser.add_argument('--store-to', default='', dest='store_to',
                                              help='store result to this variable. If --wait is specified, will store the final status.')

    # status
    modeltransform_status_subparser = modeltransform_subparsers.add_parser('status',
                                                                           help='get status of a modeltransform job')
    modeltransform_status_subparser.add_argument('--job-id', type=str, required=True,
                                                 help='modeltransform job-id to obtain the status of')
    modeltransform_status_subparser.add_argument('--iam-role-arn', '-i', type=str, default='',
                                                 help='iam role arn to use for modeltransform')
    modeltransform_status_subparser.add_argument('--wait', action='store_true')
    modeltransform_status_subparser.add_argument('--store-to', default='', dest='store_to',
                                                 help='store result to this variable. If --wait is specified, will store the final status.')

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

        processing_job_res = client.dataprocessing_start(args.s3_input_uri, args.s3_processed_uri, **params)
        processing_job_res.raise_for_status()
        processing_job = processing_job_res.json()
        job_id = params['id']
        if args.wait:
            return wait_for_dataprocessing(job_id, client, output, args.wait_interval, args.wait_timeout)
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
                "trainingInstanceType": args.instance_type,
            }

        start_training_res = client.modeltraining_start(args.job_id, args.s3_output_uri, **params)
        start_training_res.raise_for_status()
        training_job = start_training_res.json()
        if args.wait:
            return wait_for_training(training_job['id'], client, output, args.wait_interval, args.wait_timeout)
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
                "id": args.job_id,
                'instanceType': args.instance_type
            }

        create_endpoint_res = client.endpoints_create(args.model_job_id, **params)
        create_endpoint_res.raise_for_status()
        create_endpoint_job = create_endpoint_res.json()
        if args.wait:
            return wait_for_endpoint(create_endpoint_job['id'], client, output, args.wait_interval, args.wait_timeout)
        else:
            return create_endpoint_job
    elif args.which_sub == 'status':
        if args.wait:
            return wait_for_endpoint(args.job_id, client, output, args.wait_interval, args.wait_timeout)
        else:
            endpoint_status = client.endpoints_status(args.job_id)
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
        print(f'Wait called on endpoint creation job {job_id}')

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


def modeltransform_start(client: Client, params):
    """
    Starts a new modeltransform job. If Params is not empty, we will attempt to parse it into JSON
    and use it as the command payload. Otherwise we will check args for the required parameters:
    """

    data = params if type(params) is dict else json.loads(params)
    res: Response = client.modeltransform_create(**data)
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
    return f'Job cancelled, you can check its status by running the command "%neptune_ml modeltransform status {args.job_id}"'


def neptune_ml_modeltransform(args: argparse.Namespace, client: Client, output: widgets.Output, params):
    """
    We have three possible variants when invoking the `%neptune_ml modeltransform` command:
        - create
        - status
        - list
        - stop

    NOTE: If params is a non-empty string, we will attempt to use it as the payload for the query.
    """
    if args.which_sub == 'create':
        create_res = modeltransform_start(client, params)
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
