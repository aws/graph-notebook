"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import zipfile
import tarfile
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.handlers import disable_signing
from os.path import join as pjoin
from shutil import rmtree


def normalize_model_name(name):
    name = name.lower().replace('_', '')
    # handles legacy scenarios
    if name in ('gremlin', 'opencypher', 'property_graph', 'propertygraph', 'pg'):
        name = 'propertygraph'
    elif name in ('sparql', 'rdf'):
        name = 'rdf'
    return name


def normalize_language_name(lang):
    lang = lang.lower().replace('_', '')
    if lang in ['opencypher', 'oc', 'cypher']:
        lang = 'opencypher'
    return lang


def file_to_query(file, path_to_data_sets):
    if file == '__init__.py' or file == '__pycache__':
        return None
    full_path = pjoin(path_to_data_sets, file)
    try:
        with open(full_path, mode='r', encoding="utf-8") as file_content:
            query_dict = {
                'name': file,
                'content': file_content.read()
            }
            return query_dict
    except Exception:
        print(f"Unable to read queries from file [{file}] under local directory [{path_to_data_sets}]")
        return None


def download_and_extract_archive_from_s3(bucket_name, filepath):
    """
    Depending on the S3 path provided, we can handle three possible cases here:
        1. plain S3 directory
        2. zip/tar archive
        3. single data file

    We will first attempt to send a signed AWS request to retrieve the S3 file. If credentials cannot be located, the
    request will be retried once more, unsigned.

    If the S3 request succeeds, this function will create a temporary file(or folder containing data files, in the case
    of a directory/archive URI) in the immediate Jupyter directory. After the datafiles are processed in get_queries,
    the temporary file is deleted.
    """
    base_file = os.path.basename(filepath)
    if not base_file:
        base_file = filepath
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    while True:
        try:
            if base_file.endswith('/'):
                if not os.path.exists(base_file):
                    os.makedirs(base_file)
                for obj in bucket.objects.filter(Prefix=filepath):
                    if not obj.key.endswith('/'):
                        new_file = os.path.basename(obj.key)
                        target_file = base_file + new_file
                        bucket.download_file(obj.key, target_file)
            else:
                bucket.download_file(filepath, base_file)
            break
        except ClientError as e:
            if e.response['Error']['Code'] in ["404", "403"]:
                print("Unable to access the sample dataset specified.")
            raise
        except NoCredentialsError:
            # if no AWS credentials are available, retry with unsigned request.
            s3.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)
    is_archive = True
    if os.path.isdir(base_file):  # check this first so we don't get an IsADirectoryError in below conditionals
        is_archive = False
    elif tarfile.is_tarfile(base_file):
        tar_file = tarfile.open(base_file)
        tar_file.extractall()
        tar_file.close()
    elif zipfile.is_zipfile(base_file):
        with zipfile.ZipFile(base_file, 'r') as zf:
            zf.extractall()
    else:
        is_archive = False
    if is_archive:
        # we have the extracted contents elsewhere now, so delete the downloaded archive.
        os.remove(base_file)
        path_to_data_sets = pjoin(os.getcwd(), os.path.splitext(base_file)[0])
    else:
        # Any other filetype. If unreadable, we'll handle it in the file_to_query function.
        path_to_data_sets = pjoin(os.getcwd(), base_file)
    return path_to_data_sets


# returns a list of queries which correspond to a given query language and name
def get_queries(query_language, name, location):
    if location == 'samples':
        d = os.path.dirname(os.path.realpath(__file__))
        path_to_data_sets = pjoin(d, 'queries', normalize_model_name(query_language),
                                  normalize_language_name(query_language), name)
    else:
        # handle custom files here
        if name.startswith('s3://'):
            bucketname, filename = name.replace("s3://", "").split("/", 1)
            path_to_data_sets = download_and_extract_archive_from_s3(bucketname, filename)
        else:
            path_to_data_sets = name
    queries = []

    if os.path.isdir(path_to_data_sets):  # path_to_data_sets is an existing directory
        for file in os.listdir(path_to_data_sets):
            new_query = file_to_query(file, path_to_data_sets)
            if new_query:
                queries.append(new_query)
        queries.sort(key=lambda i: i['name'])  # ensure we get queries back in lexicographical order.
        if name.startswith('s3://'):
            # if S3 data was downloaded, delete the temp folder.
            rmtree(path_to_data_sets, ignore_errors=True)
    elif os.path.isfile(path_to_data_sets):  # path_to_data_sets is an existing file
        file = os.path.basename(path_to_data_sets)
        folder = os.path.dirname(path_to_data_sets)
        new_query = file_to_query(file, folder)
        if new_query:
            queries.append(new_query)
        if name.startswith('s3://'):
            os.unlink(path_to_data_sets)
    else:
        return None

    return queries


def get_data_sets(query_language):
    if query_language == '':
        return []
    d = os.path.dirname(os.path.realpath(__file__))
    path_to_data_sets = pjoin(d, 'queries', normalize_model_name(query_language),
                              normalize_language_name(query_language))
    data_sets = []
    for data_set in os.listdir(path_to_data_sets):
        if data_set != '__pycache__' and os.path.isdir(pjoin(path_to_data_sets, data_set)):
            data_sets.append(data_set)
    return data_sets
