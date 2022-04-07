"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import zipfile
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError
from botocore.handlers import disable_signing
from os.path import join as pjoin
from shutil import rmtree


def normalize_model_name(name):
    name = name.lower().replace('_', '')
    # handles legacy scenarios
    if name in ('gremlin', 'opencypher', 'property_graph', 'propertygraph'):
        name = 'propertygraph'
    elif name in ('sparql', 'rdf'):
        name = 'rdf'
    return name


def file_to_query(file, path_to_data_sets):
    if file == '__init__.py' or file == '__pycache__':
        return None
    full_path = pjoin(path_to_data_sets, file)
    with open(full_path, mode='r', encoding="utf-8") as f:
        query = {
            'name': file,
            'content': f.read()
        }
        return query


# returns a list of queries which correspond to a given query language and name
def get_queries(model, name, location):
    if location == 'samples':
        bucketname = 'aws-neptune-notebook'
        filename_parent = 'queries/' + normalize_model_name(model)
        filename_base = name + '.zip'
        filename = filename_parent + '/' + filename_base
        s3 = boto3.resource('s3')
        s3.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)
        try:
            s3.Bucket(bucketname).download_file(filename, os.path.basename(filename))
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("Unable to access the sample dataset specified.")
            raise
        with zipfile.ZipFile(filename_base, 'r') as zf:
            zf.extractall()
        os.remove(filename_base)
        path_to_data_sets = pjoin(os.getcwd(), name)
    else:
        path_to_data_sets = name
    queries = []

    if os.path.isdir(path_to_data_sets):  # path_to_data_sets is a directory
        for file in os.listdir(path_to_data_sets):
            new_query = file_to_query(file, path_to_data_sets)
            if new_query:
                queries.append(new_query)
        queries.sort(key=lambda i: i['name'])  # ensure we get queries back in lexicographical order.
        if location == 'samples':  # if sample data was downloaded, delete the temp folder.
            rmtree(path_to_data_sets, ignore_errors=True)
    else:  # path_to_data_sets is a file
        file = os.path.basename(path_to_data_sets)
        folder = os.path.dirname(path_to_data_sets)
        new_query = file_to_query(file, folder)
        if new_query:
            queries.append(new_query)

    return queries


def get_data_sets(model):
    if model == '':
        return []
    bucketname = 'aws-neptune-notebook'
    model_folder = normalize_model_name(model) + '/'
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    data_sets = []
    try:
        objects = s3.list_objects_v2(Bucket=bucketname)
        for obj in objects['Contents']:
            if model_folder in obj['Key']:
                filename = os.path.basename(obj['Key'])
                if filename != '__init__.py':
                    data_sets.append(filename[:-len('.zip')])
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("Unable to access samples bucket, please check your network connection.")
        raise
    return data_sets
