"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import argparse
import datetime
import logging
import os
import sys
import uuid
import time
import unittest

import boto3 as boto3
import requests

from graph_notebook.configuration.generate_config import AuthModeEnum, Configuration

SUBPARSER_CREATE_CFN = 'create-cfn-stack'
SUBPARSER_DELETE_CFN = 'delete-cfn-stack'
SUBPARSER_RUN_TESTS = 'run-tests'
SUBPARSER_GENERATE_CONFIG = 'generate-config'
SUBPARSER_ENABLE_IAM = 'toggle-cluster-iam'

sys.path.insert(0, os.path.abspath('..'))

TEST_CONFIG_PATH = os.getenv('GRAPH_NOTEBOOK_TEST_CONFIG_PATH', '/tmp/graph_notebook_config_integration_test.json')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def get_cfn_stack_details(cfn_stack_name: str, cfn_client) -> dict:
    stack_instance = cfn_client.describe_stacks(StackName=cfn_stack_name)
    if 'Stacks' not in stack_instance or len(stack_instance['Stacks']) == 0:
        logging.info(f'no stacks found with name {cfn_stack_name}')

    if len(stack_instance['Stacks']) > 1:
        raise ValueError(f'more than one stack found with the name {cfn_stack_name}')

    stack = stack_instance['Stacks'][0]
    return stack


def get_neptune_identifier_from_cfn(cfn_stack_name: str, cfn_client) -> str:
    stack = get_cfn_stack_details(cfn_stack_name, cfn_client)
    for output in stack['Outputs']:
        if output['OutputKey'] == 'DBClusterId':
            return output['OutputValue']
    raise ValueError(f'DBClusterId not found in stack {cfn_stack_name}')


def set_iam_auth_on_neptune_cluster(cluster_identifier: str, iam_value: bool, neptune_client):
    """
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/neptune.html#Neptune.Client.modify_db_cluster
    :return:
    """
    cluster = neptune_client.describe_db_clusters(DBClusterIdentifier=cluster_identifier)['DBClusters'][0]
    if cluster['IAMDatabaseAuthenticationEnabled'] == iam_value:
        return

    response = neptune_client.modify_db_cluster(DBClusterIdentifier=cluster_identifier,
                                                EnableIAMDatabaseAuthentication=iam_value, ApplyImmediately=True)
    logging.info(f'modified neptune cluster {cluster_identifier} to set iam auth to {iam_value}: {response}')

    # wait for authentication setting to show as changed:
    while cluster['IAMDatabaseAuthenticationEnabled'] != iam_value:
        logging.info('waiting for one minute to check authentication setting...')
        time.sleep(60)
        cluster = neptune_client.describe_db_clusters(DBClusterIdentifier=cluster_identifier)['DBClusters'][0]

    logging.info(f'authentication setting for cluster {cluster_identifier} now shows as {iam_value}')
    return


def get_this_machine_ip():
    """
    Get this machine's ip address.
    :return: string representation of tihs machine's ip
    """
    res = requests.get('http://checkip.amazonaws.com')
    res.raise_for_status()
    ip = res.content.decode('utf-8')
    return ip


def run_integration_tests(pattern: str):
    logging.info('starting integration test suite...')
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern)
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)
    exit(0 if test_result.wasSuccessful() else 1)


def loop_until_stack_is_complete(stack_name: str, cfn_client: boto3.session.Session.client,
                                 timeout_minutes: int = 30, loop_wait_seconds: int = 60) -> dict:
    """
    Loops until the given stack name has completed or until the given
    timeout has been exceeded. If the number of stacks returned is not equal
    to 1, the process will end as it is not recoverable.

    :param stack_name: name of the cloud formation stack to check
    :param cfn_client: client to be used for checking stack status
    :param timeout_minutes: number of minutes to wait until the stack is complete
    :param loop_wait_seconds: number of seconds to wait between each attempt
    :return: the stack dict object
    """
    start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).total_seconds() / 60 < timeout_minutes:
        logging.info(f'checking if stack {stack_name} is complete...')
        stack = get_cfn_stack_details(stack_name, cfn_client)

        # make sure that the stack has not failed in any way
        assert 'FAILED' not in stack['StackStatus']
        assert stack['StackStatus'] != 'ROLLBACK_COMPLETE'
        if stack['StackStatus'] == 'CREATE_COMPLETE':
            return stack

        logging.info(f'stack is not complete, waiting for {loop_wait_seconds} seconds and checking again..')
        time.sleep(loop_wait_seconds)
    raise TimeoutError(f'exceeded max number of minutes ({timeout_minutes}) for stack to complete')


def get_stack_details_to_run(stack: dict, region: str = 'us-east-1', timeout_minutes: int = 20,
                             loop_wait_seconds: int = 10) -> dict:
    """
    Get the stack details needed to run this integration test. This includes the ip address
    for a loadbalancer which is working, the cluster writer endpoint, and the s3 loader arn which is attached
    to the cluster. When ip addresses for each load balancer are found, check if any of them work.
    Once one does, return details.

    :param stack: the name of the stack to gather details for
    :param timeout_minutes: the amount of time to to attempt to gather these details
    :param loop_wait_seconds:
    :return: dict
    """

    logging.info(f'looking for details from stack {stack}')
    start_time = datetime.datetime.now()
    while (datetime.datetime.now() - start_time).total_seconds() / 60 < timeout_minutes:
        stack_output = {}
        for output in stack['Outputs']:
            stack_output[output['OutputKey']] = output['OutputValue']

        lb_client = boto3.client('elbv2', region_name=region)
        stack_arn = stack_output['LoadBalancer']
        load_balancers = lb_client.describe_load_balancers(LoadBalancerArns=[stack_arn])

        if 'LoadBalancers' not in load_balancers or len(load_balancers['LoadBalancers']) == 0:
            logging.info(f'load balancer with arn {stack_arn} was not found, waiting {loop_wait_seconds} seconds..')
            time.sleep(loop_wait_seconds)
            continue

        load_balancer = load_balancers['LoadBalancers'][0]
        ec2_client = boto3.client('ec2', region_name=region)
        network_interfaces = ec2_client.describe_network_interfaces(Filters=[
            {
                'Name': 'description',
                'Values': [f'ELB *{load_balancer["LoadBalancerName"]}*']
            }
        ])

        if 'NetworkInterfaces' not in network_interfaces or len(network_interfaces['NetworkInterfaces']) < 1:
            logging.info(
                f'no network interfaces matching the description pattern "ELB *{load_balancer["LoadBalancerName"]}*')
            time.sleep(loop_wait_seconds)
            continue

        # check which IP address is working
        success = False
        ip = ''
        for network_interface in network_interfaces['NetworkInterfaces']:
            logging.info('checking if one ip address is working...')
            ip = network_interface['PrivateIpAddresses'][0]['Association']['PublicIp']
            logging.info(f'checking if ip {ip} can be used ')

            url = f'https://{ip}:80/status'
            try:
                logging.info(f'checking ip address {ip}, url={url}')
                # hard-coded to port 80 since that's what this CFN stack uses for its load balancer
                requests.get(url, verify=False, timeout=5)  # an exception is thrown if the host cannot be reached.
                success = True
                break
            except Exception:
                logging.info(f'{url} could not be reached')

        if not success:
            logging.info(f'no ip addresses working yet, waiting for {loop_wait_seconds} seconds and trying again..')
            time.sleep(loop_wait_seconds)
            continue

        connection_data = {
            'ip': ip,
            'endpoint': stack_output['DBClusterEndpoint'],
            'loader_arn': stack_output['NeptuneLoadFromS3IAMRoleArn']
        }

        return connection_data
    raise TimeoutError(f'time limit of {timeout_minutes} exceeded')


def create_cfn_stack(stack_name: str, stack_url: str, s3_bucket: str, runner_role: str, cfn_client) -> dict:
    """
    Create the cfn stack and wait for it to complete.


    :param stack_name: the name of the stack
    :param stack_url: the cfn template url
    :param s3_bucket: the bucket to store ip addresses to
    :param runner_role: the role to pass to cfn for resource provisioning

    :return: the stack dict object
    """
    logging.info(
        f'creating cfn stack using url={stack_url}, name={stack_name}, s3_bucket={s3_bucket}')
    params = [
        {
            'ParameterKey': 'ClientIPRange',
            'ParameterValue': get_this_machine_ip(),
        },
        {
            'ParameterKey': 'IamAuthEnabled',
            'ParameterValue': 'false'  # must be lowercase, otherwise we would use str(iam)
        },
        {
            'ParameterKey': 'S3BucketName',
            'ParameterValue': s3_bucket
        }
    ]

    if runner_role != '':
        res = cfn_client.create_stack(StackName=stack_name, DisableRollback=True, TemplateURL=stack_url,
                                      Parameters=params,
                                      Capabilities=['CAPABILITY_IAM'], RoleARN=runner_role)
    else:
        res = cfn_client.create_stack(StackName=stack_name, DisableRollback=True, TemplateURL=stack_url,
                                      Parameters=params,
                                      Capabilities=['CAPABILITY_IAM'])

    logging.info(f'create stack response: {res}')
    logging.info('waiting for stack to complete (this will take a few minutes)...')
    stack = loop_until_stack_is_complete(stack_name, cfn_client)
    return stack


def generate_config_from_stack(stack: dict, region: str, iam: bool) -> Configuration:
    logging.info('stack finished, retrieving stack details')
    details = get_stack_details_to_run(stack, region)
    logging.info(f'obtained stack details: {details}')

    # because this stack puts Neptune behind a load balancer, we need to alias the ip address of the load
    # balancer to the Neptune cluster endpoint to ensure that SSL certificates match the host that we are calling.
    # To do this will we need to alter /etc/hosts
    host_alias = f'{details["ip"]} {details["endpoint"]}'
    logging.info(
        f'adding {host_alias} to /etc/hosts and removing other aliased lines to cluster endpoint {details["endpoint"]}')

    new_lines = []
    with open('/etc/hosts', 'w+') as file:
        lines = file.read().split('\n')
        for line in lines:
            if details['endpoint'] not in line:
                new_lines.append(line)
        new_lines.append(host_alias + '\n')
        file.writelines(new_lines)

    auth = AuthModeEnum.IAM if iam else AuthModeEnum.DEFAULT
    conf = Configuration(details['endpoint'], 80, auth, details['loader_arn'], ssl=True, aws_region=region)
    logging.info(f'generated configuration for test run: {conf.to_dict()}')
    return conf


def delete_stack(stack_name, cfn_client):
    res = cfn_client.delete_stack(StackName=stack_name)
    logging.info(f'deleted cfn stack {stack_name}. res={res}')


def generate_stack_name() -> str:
    return f'graph-notebook-test-{str(uuid.uuid4())[:8]}'


def handle_create_cfn_stack(stack_name: str, url: str, s3_bucket: str, cfn_client,
                            runner_role: str = ''):
    """
    Creates a cfn stack for use in testing. Will wait until stack is finished being created to exit.

    :param stack_name: Name of the stack
    :param url: CFN Template URL
    :param s3_bucket: cfn param used to store ip addresses for load balancer -> Neptune connection
    :param runner_role: The iam role for cfn to use for resource creation (OPTIONAL)
    """

    logging.info(f'''creating cfn stack with params:
    name={stack_name}
    url={url}
    s3_bucket={s3_bucket}
    runner_role={runner_role}''')

    create_cfn_stack(stack_name, url, s3_bucket, runner_role, cfn_client)
    stack = loop_until_stack_is_complete(stack_name, cfn_client)
    logging.info(f'stack creation finished. Name={stack_name}, stack={stack}')


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(help='sub-command help', dest='which')
    # sub parser for creating the cfn stack
    parser_create_stack = subparsers.add_parser(SUBPARSER_CREATE_CFN, help='create cfn stack for use in testing')
    parser_create_stack.add_argument('--cfn-stack-name', type=str, default='')
    parser_create_stack.add_argument('--cfn-template-url', type=str, required=True)
    parser_create_stack.add_argument('--cfn-s3-bucket', type=str, default='')
    parser_create_stack.add_argument('--aws-region', default='us-east-1', type=str)
    parser_create_stack.add_argument('--cfn-runner-role', type=str, required=False, default='',
                                     help='OPTIONAL: iam role for cloud formation to use')

    # sub parser for deleting cfn stack
    delete_parser = subparsers.add_parser(SUBPARSER_DELETE_CFN, help='delete cfn stack used for testing')
    delete_parser.add_argument('--cfn-stack-name', type=str, default='')
    delete_parser.add_argument('--aws-region', type=str, default='us-east-1')

    # sub parser generate config
    config_parser = subparsers.add_parser(SUBPARSER_GENERATE_CONFIG,
                                          help='generate test configuration from supplied cfn stack')
    config_parser.add_argument('--cfn-stack-name', type=str, default='')
    config_parser.add_argument('--aws-region', type=str, default='us-east-1')
    config_parser.add_argument('--iam', action='store_true')

    args = parser.parse_args()

    cfn_client = boto3.client('cloudformation', region_name=args.aws_region)
    neptune_client = boto3.client('neptune', region_name=args.aws_region)
    if args.which == SUBPARSER_CREATE_CFN:
        stack_name = args.cfn_stack_name if args.cfn_stack_name != '' else generate_stack_name()
        handle_create_cfn_stack(stack_name, args.cfn_template_url, args.cfn_s3_bucket, cfn_client, args.cfn_runner_role)
    elif args.which == SUBPARSER_DELETE_CFN:
        delete_stack(args.cfn_stack_name, cfn_client)
    elif args.which == SUBPARSER_ENABLE_IAM:
        cluster_identifier = get_neptune_identifier_from_cfn(args.cfn_stack_name, cfn_client)
        set_iam_auth_on_neptune_cluster(cluster_identifier, True, neptune_client)
        logging.info('waiting for one minute while change is applied...')
        time.sleep(60)
    elif args.which == SUBPARSER_GENERATE_CONFIG:
        stack = get_cfn_stack_details(args.cfn_stack_name, cfn_client)
        cluster_identifier = get_neptune_identifier_from_cfn(args.cfn_stack_name, cfn_client)
        set_iam_auth_on_neptune_cluster(cluster_identifier, args.iam, neptune_client)
        config = generate_config_from_stack(stack, args.aws_region, args.iam)
        config.write_to_file(TEST_CONFIG_PATH)


if __name__ == '__main__':
    main()
