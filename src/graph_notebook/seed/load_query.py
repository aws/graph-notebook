"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import io
import zipfile
import tarfile
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.handlers import disable_signing
from os.path import join as pjoin


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


def content_to_query(name, content):
    if name == '__init__.py' or name == '__pycache__':
        return None
    return {'name': name, 'content': content}


def file_to_query(file, path_to_data_sets):
    full_path = pjoin(path_to_data_sets, file)
    try:
        with open(full_path, mode='r', encoding="utf-8") as file_content:
            return content_to_query(file, file_content.read())
    except Exception:
        print(f"Unable to read queries from file [{file}] under local directory [{path_to_data_sets}]")
        return None


def download_and_read_archive_from_s3(bucket_name, filepath):
    """
    Depending on the S3 path provided, we can handle three possible cases here:
        1. plain S3 directory
        2. zip/tar archive — read in-memory without extracting to disk
        3. single data file

    We will first attempt to send a signed AWS request to retrieve the S3 file. If credentials cannot be located, the
    request will be retried once more, unsigned.
    """
    base_file = os.path.basename(filepath)
    if not base_file:
        base_file = filepath
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    while True:
        try:
            if base_file.endswith('/'):
                queries = []
                for obj in bucket.objects.filter(Prefix=filepath):
                    if not obj.key.endswith('/'):
                        new_query = content_to_query(os.path.basename(obj.key), obj.get()['Body'].read().decode('utf-8'))
                        if new_query:
                            queries.append(new_query)
                return queries
            else:
                buf = io.BytesIO()
                bucket.download_fileobj(filepath, buf)
            break
        except ClientError as e:
            if e.response['Error']['Code'] in ["404", "403"]:
                print("Unable to access the sample dataset specified.")
            raise
        except NoCredentialsError:
            # if no AWS credentials are available, retry with unsigned request.
            s3.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)

    # Read archive contents in-memory — never extract to disk
    buf.seek(0)
    if tarfile.is_tarfile(buf):
        buf.seek(0)
        queries = []
        with tarfile.open(fileobj=buf) as tar:
            for member in tar.getmembers():
                f = tar.extractfile(member)
                if f:
                    try:
                        new_query = content_to_query(os.path.basename(member.name), f.read().decode('utf-8'))
                        if new_query:
                            queries.append(new_query)
                    except Exception:
                        print(f"Unable to read archive member [{member.name}]")
        return queries

    buf.seek(0)
    if zipfile.is_zipfile(buf):
        buf.seek(0)
        queries = []
        with zipfile.ZipFile(buf, 'r') as zf:
            for name in zf.namelist():
                try:
                    new_query = content_to_query(os.path.basename(name), zf.read(name).decode('utf-8'))
                    if new_query:
                        queries.append(new_query)
                except Exception:
                    print(f"Unable to read zip member [{name}]")
        return queries

    # Single file
    buf.seek(0)
    try:
        return [content_to_query(base_file, buf.read().decode('utf-8'))]
    except Exception:
        print(f"Unable to read file [{base_file}] from S3.")
        return []


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
            queries = download_and_read_archive_from_s3(bucketname, filename)
            queries.sort(key=lambda i: i['name'])
            return queries
        else:
            path_to_data_sets = name
    queries = []

    if os.path.isdir(path_to_data_sets):  # path_to_data_sets is an existing directory
        for file in os.listdir(path_to_data_sets):
            new_query = file_to_query(file, path_to_data_sets)
            if new_query:
                queries.append(new_query)
        queries.sort(key=lambda i: i['name'])  # ensure we get queries back in lexicographical order.
    elif os.path.isfile(path_to_data_sets):  # path_to_data_sets is an existing file
        file = os.path.basename(path_to_data_sets)
        folder = os.path.dirname(path_to_data_sets)
        new_query = file_to_query(file, folder)
        if new_query:
            queries.append(new_query)
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
