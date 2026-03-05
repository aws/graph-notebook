"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import os
import time
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


def validate_and_extract_archive(archive_path, extract_dir):
    """
    Validates all archive member paths before extraction.
    Raises ValueError if any member:
      - contains an absolute or relative path that resolves outside the extraction directory
      - is nested inside a subdirectory
    Extracts to extract_dir if all members are safe.
    """
    abs_extract_dir = os.path.realpath(extract_dir)

    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path) as tar:
            for member in tar.getmembers():
                if member.isdir():
                    continue
                if member.issym() or member.islnk():
                    raise ValueError(
                        f"Archive member '{member.name}' is a symbolic or hard link which is not allowed. "
                        f"Please ensure the archive contains only regular files and try again."
                    )
                if '/' in member.name or '\\' in member.name:
                    raise ValueError(
                        f"Archive member '{member.name}' is nested inside a subdirectory. "
                        f"Please ensure all query files are at the root of the archive and try again."
                    )
                member_path = os.path.realpath(os.path.join(abs_extract_dir, member.name))
                if not member_path.startswith(abs_extract_dir + os.sep):
                    raise ValueError(
                        f"Archive member '{member.name}' contains an absolute or relative path that resolves "
                        f"outside the extraction directory. Please fix the archive and try again."
                    )
            tar.extractall(extract_dir)

    elif zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('/'):
                    continue
                if '/' in name or '\\' in name:
                    raise ValueError(
                        f"Archive member '{name}' is nested inside a subdirectory. "
                        f"Please ensure all query files are at the root of the archive and try again."
                    )
                member_path = os.path.realpath(os.path.join(abs_extract_dir, name))
                if not member_path.startswith(abs_extract_dir + os.sep):
                    raise ValueError(
                        f"Archive member '{name}' contains an absolute or relative path that resolves "
                        f"outside the extraction directory. Please fix the archive and try again."
                    )
            zf.extractall(extract_dir)


def download_and_extract_archive_from_s3(bucket_name, filepath):
    """
    Depending on the S3 path provided, we can handle three possible cases here:
        1. plain S3 directory
        2. zip/tar archive
        3. single data file

    We will first attempt to send a signed AWS request to retrieve the S3 file. If credentials cannot be located, the
    request will be retried once more, unsigned.

    If the S3 request succeeds, this function will create a temporary directory /tmp/seed-{timestamp}/
    to extract archive contents into. After the datafiles are processed in get_queries, the temporary
    directory is deleted in a finally block regardless of success or failure.
    """
    base_file = os.path.basename(filepath)
    if not base_file:
        base_file = filepath
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    extract_dir = f'/tmp/seed-{int(time.time() * 1000)}'
    # retry with a new timestamp if the directory already exists (e.g. two calls in the same millisecond)
    while os.path.exists(extract_dir):
        extract_dir = f'/tmp/seed-{int(time.time() * 1000)}'
    os.makedirs(extract_dir)
    try:
        while True:
            try:
                if base_file.endswith('/'):
                    for obj in bucket.objects.filter(Prefix=filepath):
                        if not obj.key.endswith('/'):
                            new_file = os.path.basename(obj.key)
                            bucket.download_file(obj.key, pjoin(extract_dir, new_file))
                else:
                    bucket.download_file(filepath, pjoin(extract_dir, base_file))
                break
            except ClientError as e:
                if e.response['Error']['Code'] in ["404", "403"]:
                    print("Unable to access the sample dataset specified.")
                raise
            except NoCredentialsError:
                # if no AWS credentials are available, retry with unsigned request.
                s3.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)

        archive_path = pjoin(extract_dir, base_file)
        if not base_file.endswith('/') and (tarfile.is_tarfile(archive_path) or zipfile.is_zipfile(archive_path)):
            nested_dir = pjoin(extract_dir, base_file.split('.')[0])
            os.makedirs(nested_dir, exist_ok=True)
            validate_and_extract_archive(archive_path, nested_dir)
            os.remove(archive_path)
            return nested_dir

        return extract_dir
    except Exception:
        # clean up the temp directory on any failure to avoid leaving partial files on disk
        rmtree(extract_dir, ignore_errors=True)
        raise


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
        try:
            for file in os.listdir(path_to_data_sets):
                new_query = file_to_query(file, path_to_data_sets)
                if new_query:
                    queries.append(new_query)
            queries.sort(key=lambda i: i['name'])  # ensure we get queries back in lexicographical order.
        finally:
            if name.startswith('s3://'):
                rmtree(path_to_data_sets, ignore_errors=True)
    elif os.path.isfile(path_to_data_sets):  # path_to_data_sets is an existing file
        try:
            file = os.path.basename(path_to_data_sets)
            folder = os.path.dirname(path_to_data_sets)
            new_query = file_to_query(file, folder)
            if new_query:
                queries.append(new_query)
        finally:
            if name.startswith('s3://'):
                rmtree(os.path.dirname(path_to_data_sets), ignore_errors=True)
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
