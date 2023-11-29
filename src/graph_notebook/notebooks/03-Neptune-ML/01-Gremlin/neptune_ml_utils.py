import boto3
import pandas as pd
import numpy as np
import pickle
import os
import requests
import json
import zipfile
import logging
import time
from time import strftime, gmtime, sleep
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from datetime import datetime
from urllib.parse import urlparse
from sagemaker.s3 import S3Downloader

# How often to check the status
UPDATE_DELAY_SECONDS = 15
HOME_DIRECTORY = os.path.expanduser("~")


def signed_request(method, url, data=None, params=None, headers=None, service=None):
    request = AWSRequest(method=method, url=url, data=data,
                         params=params, headers=headers)
    session = boto3.Session()
    credentials = session.get_credentials()
    try:
        frozen_creds = credentials.get_frozen_credentials()
    except AttributeError:
        print("Could not find valid IAM credentials in any the following locations:\n")
        print("env, assume-role, assume-role-with-web-identity, sso, shared-credential-file, custom-process, "
              "config-file, ec2-credentials-file, boto-config, container-role, iam-role\n")
        print("Go to https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html for more "
              "details on configuring your IAM credentials.")
        return request
    SigV4Auth(frozen_creds, service, boto3.Session().region_name).add_auth(request)
    return requests.request(method=method, url=url, headers=dict(request.headers), data=data)


def load_configuration():
    with open(f'{HOME_DIRECTORY}/graph_notebook_config.json') as f:
        data = json.load(f)
        host = data['host']
        port = data['port']
        if data.get('auth_mode') == 'IAM':
            iam = True
        else:
            iam = False
    return host, port, iam


def get_host():
    host, port, iam = load_configuration()
    return host


def get_iam():
    host, port, iam = load_configuration()
    return iam


def get_training_job_name(prefix: str):
    return f'{prefix}-{int(time.time())}'


def check_ml_enabled():
    host, port, use_iam = load_configuration()
    response = signed_request(
        "GET", url=f'https://{host}:{port}/ml/modeltraining', service='neptune-db')
    if response.status_code != 200:
        print('''This Neptune cluster \033[1mis not\033[0m configured to use Neptune ML.
Please configure the cluster according to the Amazon Neptune ML documentation before proceeding.''')
    else:
        print("This Neptune cluster is configured to use Neptune ML")


def get_export_service_host():
    with open(f'{HOME_DIRECTORY}/.bashrc') as f:
        data = f.readlines()
    for d in data:
        if str.startswith(d, 'export NEPTUNE_EXPORT_API_URI'):
            parts = d.split('=')
            if len(parts) == 2:
                path = urlparse(parts[1].rstrip())
                return path.hostname + "/v1"
    logging.error(
        "Unable to determine the Neptune Export Service Endpoint. You will need to enter this or assign it manually.")
    return None


def delete_pretrained_data(setup_node_classification: bool,
                           setup_node_regression: bool, setup_link_prediction: bool,
                           setup_edge_regression: bool, setup_edge_classification: bool):
    host, port, use_iam = load_configuration()
    if setup_node_classification:
        response = signed_request("POST", service='neptune-db',
                                  url=f'https://{host}:{port}/gremlin',
                                  headers={'content-type': 'application/json'},
                                  data=json.dumps(
                                      {
                                          'gremlin': "g.V('movie_28', 'movie_69', 'movie_88').properties('genre').drop()"}))

        if response.status_code != 200:
            print(response.content.decode('utf-8'))
    if setup_node_regression:
        response = signed_request("POST", service='neptune-db',
                                  url=f'https://{host}:{port}/gremlin',
                                  headers={'content-type': 'application/json'},
                                  data=json.dumps({'gremlin': "g.V('user_1').out('wrote').properties('score').drop()"}))
        if response.status_code != 200:
            print(response.content.decode('utf-8'))
    if setup_link_prediction:
        response = signed_request("POST", service='neptune-db',
                                  url=f'https://{host}:{port}/gremlin',
                                  headers={'content-type': 'application/json'},
                                  data=json.dumps({'gremlin': "g.V('user_1').outE('rated').drop()"}))
        if response.status_code != 200:
            print(response.content.decode('utf-8'))

    if setup_edge_regression:
        response = signed_request("POST", service='neptune-db',
                                  url=f'https://{host}:{port}/gremlin',
                                  headers={'content-type': 'application/json'},
                                  data=json.dumps(
                                      {'gremlin': "g.V('user_1').outE('rated').properties('score').drop()"}))
        if response.status_code != 200:
            print(response.content.decode('utf-8'))

    if setup_edge_classification:
        response = signed_request("POST", service='neptune-db',
                                  url=f'https://{host}:{port}/gremlin',
                                  headers={'content-type': 'application/json'},
                                  data=json.dumps(
                                      {'gremlin': "g.V('user_1').outE('rated').properties('scale').drop()"}))
        if response.status_code != 200:
            print(response.content.decode('utf-8'))


def delete_pretrained_endpoints(endpoints: dict):
    sm = boto3.client("sagemaker")
    try:
        if 'node_classification_endpoint_name' in endpoints and endpoints['node_classification_endpoint_name']:
            sm.delete_endpoint(
                EndpointName=endpoints['node_classification_endpoint_name']["EndpointName"])
        if 'node_regression_endpoint_name' in endpoints and endpoints['node_regression_endpoint_name']:
            sm.delete_endpoint(
                EndpointName=endpoints['node_regression_endpoint_name']["EndpointName"])
        if 'prediction_endpoint_name' in endpoints and endpoints['prediction_endpoint_name']:
            sm.delete_endpoint(
                EndpointName=endpoints['prediction_endpoint_name']["EndpointName"])
        if 'edge_classification_endpoint_name' in endpoints and endpoints['edge_classification_endpoint_name']:
            sm.delete_endpoint(
                EndpointName=endpoints['edge_classification_endpoint_name']["EndpointName"])
        if 'edge_regression_endpoint_name' in endpoints and endpoints['edge_regression_endpoint_name']:
            sm.delete_endpoint(
                EndpointName=endpoints['edge_regression_endpoint_name']["EndpointName"])
        print(f'Endpoint(s) have been deleted')
    except Exception as e:
        logging.error(e)


def delete_endpoint(training_job_name: str, neptune_iam_role_arn=None):
    query_string = ""
    if neptune_iam_role_arn:
        query_string = f'?neptuneIamRoleArn={neptune_iam_role_arn}'
    host, port, use_iam = load_configuration()
    response = signed_request("DELETE", service='neptune-db',
                              url=f'https://{host}:{port}/ml/endpoints/{training_job_name}{query_string}',
                              headers={'content-type': 'application/json'})
    if response.status_code != 200:
        print(response.content.decode('utf-8'))
    else:
        print(response.content.decode('utf-8'))
        print(f'Endpoint {training_job_name} has been deleted')


def prepare_movielens_data(s3_bucket_uri: str):
    try:
        return MovieLensProcessor().prepare_movielens_data(s3_bucket_uri)
    except Exception as e:
        logging.error(e)


def setup_pretrained_endpoints(s3_bucket_uri: str, setup_node_classification: bool,
                               setup_node_regression: bool, setup_link_prediction: bool,
                               setup_edge_classification: bool, setup_edge_regression: bool):
    delete_pretrained_data(setup_node_classification,
                           setup_node_regression, setup_link_prediction,
                           setup_edge_classification, setup_edge_regression)
    try:
        return PretrainedModels().setup_pretrained_endpoints(s3_bucket_uri, setup_node_classification,
                                                             setup_node_regression, setup_link_prediction,
                                                             setup_edge_classification, setup_edge_regression)
    except Exception as e:
        logging.error(e)

def get_neptune_ml_job_output_location(job_name: str, job_type: str):
    assert job_type in ["dataprocessing", "modeltraining", "modeltransform"], "Invalid neptune ml job type"

    host, port, use_iam = load_configuration()

    response = signed_request("GET", service='neptune-db',
                              url=f'https://{host}:{port}/ml/{job_type}/{job_name}',
                              headers={'content-type': 'application/json'})
    result = json.loads(response.content.decode('utf-8'))
    if result["status"] != "Completed":
        logging.error("Neptune ML {} job: {} is not completed".format(job_type, job_name))
        return
    return result["processingJob"]["outputLocation"]


def get_dataprocessing_job_output_location(dataprocessing_job_name: str):
    assert dataprocessing_job_name is not None, \
        "Neptune ML training job name id should be passed, if training job s3 output is missing"
    return get_neptune_ml_job_output_location(dataprocessing_job_name, "dataprocessing")


def get_modeltraining_job_output_location(training_job_name: str):
    assert training_job_name is not None, \
        "Neptune ML training job name id should be passed, if training job s3 output is missing"
    return get_neptune_ml_job_output_location(training_job_name, "modeltraining")


def get_node_to_idx_mapping(training_job_name: str = None, dataprocessing_job_name: str = None,
                            model_artifacts_location: str = './model-artifacts', vertex_label: str = None):
    assert training_job_name is not None or dataprocessing_job_name is not None, \
        "You must provide either a modeltraining job id or a dataprocessing job id to obtain node to index mappings"

    job_name = training_job_name if training_job_name is not None else dataprocessing_job_name
    job_type = "modeltraining" if training_job_name == job_name else "dataprocessing"
    filename = "mapping.info" if training_job_name == job_name else "info.pkl"
    mapping_key = "node2id" if training_job_name == job_name else "node_id_map"

    # get mappings
    model_artifacts_location = os.path.join(model_artifacts_location, job_name)
    if not os.path.exists(os.path.join(model_artifacts_location, filename)):
        job_s3_output = get_neptune_ml_job_output_location(job_name, job_type)
        print(job_s3_output)
        if not job_s3_output:
            return
        S3Downloader.download(os.path.join(job_s3_output, filename), model_artifacts_location)

    with open(os.path.join(model_artifacts_location, filename), "rb") as f:
        mapping = pickle.load(f)[mapping_key]
        if vertex_label is not None:
            if vertex_label in mapping:
                mapping = mapping[vertex_label]
            else:
                print("Mapping for vertex label: {} not found.".format(vertex_label))
                print("valid vertex labels which have vertices mapped to embeddings: {} ".format(list(mapping.keys())))
                print("Returning mapping for all valid vertex labels")

    return mapping


def get_embeddings(training_job_name: str, download_location: str = './model-artifacts'):
    training_job_s3_output = get_modeltraining_job_output_location(training_job_name)
    if not training_job_s3_output:
        return

    download_location = os.path.join(download_location, training_job_name)
    os.makedirs(download_location, exist_ok=True)
    # download embeddings and mapping info

    S3Downloader.download(os.path.join(training_job_s3_output, "embeddings/"),
                          os.path.join(download_location, "embeddings/"))

    entity_emb = np.load(os.path.join(download_location, "embeddings", "entity.npy"))

    return entity_emb


def get_predictions(training_job_name: str, download_location: str = './model-artifacts', class_preds: bool = False):
    training_job_s3_output = get_modeltraining_job_output_location(training_job_name)
    if not training_job_s3_output:
        return

    download_location = os.path.join(download_location, training_job_name)
    os.makedirs(download_location, exist_ok=True)
    # download embeddings and mapping info

    S3Downloader.download(os.path.join(training_job_s3_output, "predictions/"),
                          os.path.join(download_location, "predictions/"))

    preds = np.load(os.path.join(download_location, "predictions", "result.npz"))['infer_scores']

    if class_preds:
        return preds.argmax(axis=1)

    return preds


def get_performance_metrics(training_job_name: str, download_location: str = './model-artifacts'):
    training_job_s3_output = get_modeltraining_job_output_location(training_job_name)
    if not training_job_s3_output:
        return

    download_location = os.path.join(download_location, training_job_name)
    os.makedirs(download_location, exist_ok=True)
    # download embeddings and mapping info

    S3Downloader.download(os.path.join(training_job_s3_output, "eval_metrics_info.json"),
                          download_location)

    with open(os.path.join(download_location, "eval_metrics_info.json")) as f:
        metrics = json.load(f)

    return metrics


class MovieLensProcessor:
    raw_directory = fr'{HOME_DIRECTORY}/data/raw'
    formatted_directory = fr'{HOME_DIRECTORY}/data/formatted'

    def __download_and_unzip(self):
        if not os.path.exists(f'{HOME_DIRECTORY}/data'):
            os.makedirs(f'{HOME_DIRECTORY}/data')
        if not os.path.exists(f'{HOME_DIRECTORY}/data/raw'):
            os.makedirs(f'{HOME_DIRECTORY}/data/raw')
        if not os.path.exists(f'{HOME_DIRECTORY}/data/formatted'):
            os.makedirs(f'{HOME_DIRECTORY}/data/formatted')
        # Download the MovieLens dataset
        url = 'https://files.grouplens.org/datasets/movielens/ml-100k.zip'
        r = requests.get(url, allow_redirects=True)
        open(os.path.join(self.raw_directory, 'ml-100k.zip'), 'wb').write(r.content)

        with zipfile.ZipFile(os.path.join(self.raw_directory, 'ml-100k.zip'), 'r') as zip_ref:
            zip_ref.extractall(self.raw_directory)

    def __process_movies_genres(self):
        # process the movies_vertex.csv
        print('Processing Movies', end='\r')
        movies_df = pd.read_csv(os.path.join(
            self.raw_directory, 'ml-100k/u.item'), sep='|', encoding='ISO-8859-1',
            names=['~id', 'title', 'release_date', 'video_release_date', 'imdb_url',
                   'unknown', 'Action', 'Adventure', 'Animation', 'Childrens', 'Comedy',
                   'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical',
                   'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western'])
        # Parse date and convert to ISO format
        movies_df['release_date'] = movies_df['release_date'].apply(
            lambda x: str(
                datetime.strptime(x, '%d-%b-%Y').isoformat()) if not pd.isna(x) else x)
        movies_df['~label'] = 'movie'
        movies_df['~id'] = movies_df['~id'].apply(
            lambda x: f'movie_{x}')
        movie_genre_df = movies_df[[
            '~id', 'unknown', 'Action', 'Adventure', 'Animation', 'Childrens', 'Comedy',
            'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical',
            'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']]
        genres_edges_df = pd.DataFrame(
            columns=['~id', '~from', '~to', '~label'])

        genres = ['unknown', 'Action', 'Adventure', 'Animation', 'Childrens', 'Comedy',
                  'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical',
                  'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']

        genre_df = pd.DataFrame(genres, columns=['~id'])
        genre_df['~label'] = 'genre'
        genre_df['name'] = genre_df['~id']
        genre_df.to_csv(os.path.join(self.formatted_directory,
                                     'genre_vertex.csv'), index=False)
        genres_edge_df_rows_list = [genres_edges_df]

        # Loop through all the movies and pull out the genres
        for index, row in movie_genre_df.iterrows():
            genre_lst = []
            for g in genres:
                if row[g] == 1:
                    row_as_df = pd.DataFrame.from_dict({'~id': f"{row['~id']}-included_in-{g}",
                                                        '~label': 'included_in',
                                                        '~from': row['~id'],
                                                        '~to': g},
                                                       orient='index').T
                    genres_edge_df_rows_list.append(row_as_df)
                    genre_lst.append(g)
            movies_df.loc[index, 'genre:String[]'] = ';'.join(genre_lst)

        genres_edges_df = pd.concat(genres_edge_df_rows_list, ignore_index=True)
        # rename the release data column to specify the data type
        movies_df['release_date:Date'] = movies_df['release_date']
        # Drop the genre columns as well as the uneeded release date columns
        genres.append('video_release_date')
        genres.append('release_date')
        movies_df = movies_df.drop(columns=genres)

        movies_df.to_csv(os.path.join(self.formatted_directory,
                                      'movie_vertex.csv'), index=False)
        genres_edges_df.to_csv(os.path.join(self.formatted_directory,
                                            'genre_edges.csv'), index=False)

    def __process_ratings_users(self):
        # Create ratings vertices and add edges on both sides
        print('Processing Ratings', end='\r')
        ratings_vertices = pd.read_csv(os.path.join(
            self.raw_directory, 'ml-100k/u.data'), sep='\t', encoding='ISO-8859-1',
            names=['~from', '~to', 'score:Int', 'timestamp'])
        ratings_vertices['~from'] = ratings_vertices['~from'].apply(
            lambda x: f'user_{x}')
        ratings_vertices['~to'] = ratings_vertices['~to'].apply(
            lambda x: f'movie_{x}')
        rated_edges = ratings_vertices.copy(deep=True)

        ratings_vertices['~id'] = ratings_vertices['~from'].str.cat(
            ratings_vertices['~to'], sep=":")
        ratings_vertices['~label'] = "rating"
        dict = {}
        edges = {}
        for index, row in ratings_vertices.iterrows():
            id_from = row['~from']
            id_to = row['~to']
            id_id = row['~id']
            dict[index * 2] = {'~id': f"{id_from}-wrote-{id_id}", '~label': 'wrote',
                               '~from': id_from, '~to': id_id}
            dict[index * 2 + 1] = {'~id': f"{id_id}-about-{id_to}", '~label': 'about',
                                   '~from': id_id, '~to': id_to}
            score = row['score:Int']
            scale = ''
            if score == 1:
                scale = 'Hate'
            elif score == 2:
                scale = 'Dislike'
            elif score == 3:
                scale = 'Neutral'
            elif score == 4:
                scale = 'Like'
            elif score == 5:
                scale = 'Love'
            edges[index] = {'~id': f"{id_from}-rated-{id_to}", '~label': 'rated',
                            '~from': id_from, '~to': id_to, 'score:Int': score, 'scale': scale}
        rating_edges_df = pd.DataFrame.from_dict(dict, "index")

        # Remove the from and to columns and write this out as a vertex now
        ratings_vertices = ratings_vertices.drop(columns=['~from', '~to'])
        ratings_vertices.to_csv(os.path.join(self.formatted_directory,
                                             'ratings_vertices.csv'), index=False)
        # Write out the rating vertex edges for wrote and about
        rating_edges_df.to_csv(os.path.join(self.formatted_directory,
                                            'ratings_vertex_edges.csv'), index=False)
        # Write out the rated edges
        rated_edges_df = pd.DataFrame.from_dict(edges, "index")
        rated_edges_df.to_csv(os.path.join(self.formatted_directory,
                                           'rated_edges.csv'), index=False)

    def __process_users(self):
        print("Processing Users", end='\r')
        # User Vertices - Load, rename column with type, and save

        user_df = pd.read_csv(os.path.join(
            self.raw_directory, 'ml-100k/u.user'), sep='|', encoding='ISO-8859-1',
            names=['~id', 'age:Int', 'gender', 'occupation', 'zip_code'])
        user_df['~id'] = user_df['~id'].apply(
            lambda x: f'user_{x}')
        user_df['~label'] = 'user'
        user_df.to_csv(os.path.join(self.formatted_directory,
                                    'user_vertex.csv'), index=False)

    def __upload_to_s3(self, bucketname: str):
        path = urlparse(bucketname, allow_fragments=False)
        bucket = path.netloc
        file_path = path.path.lstrip('/').rstrip('/')

        s3_client = boto3.client('s3')
        for root, dirs, files in os.walk(self.formatted_directory):
            for file in files:
                s3_client.upload_file(os.path.join(
                    self.formatted_directory, file), bucket, f'{file_path}/{file}')

    def prepare_movielens_data(self, s3_bucket: str):
        bucket_name = f'{s3_bucket}/neptune-formatted/movielens-100k'
        self.__download_and_unzip()
        self.__process_movies_genres()
        self.__process_users()
        self.__process_ratings_users()
        self.__upload_to_s3(bucket_name)
        print('Completed Processing, data is ready for loading using the s3 url below:')
        print(bucket_name)
        return bucket_name


class PretrainedModels:
    SCRIPT_PARAM_NAME = "sagemaker_program"
    DIR_PARAM_NAME = "sagemaker_submit_directory"
    CONTAINER_LOG_LEVEL_PARAM_NAME = "sagemaker_container_log_level"
    ENABLE_CLOUDWATCH_METRICS_PARAM = "sagemaker_enable_cloudwatch_metrics"
    MODEL_SERVER_TIMEOUT_PARAM_NAME = "sagemaker_model_server_timeout"
    MODEL_SERVER_WORKERS_PARAM_NAME = "sagemaker_model_server_workers"
    SAGEMAKER_REGION_PARAM_NAME = "sagemaker_region"
    INSTANCE_TYPE = 'ml.m5.2xlarge'
    PYTORCH_CPU_CONTAINER_IMAGE = ""
    PRETRAINED_MODEL = {}

    def __init__(self):
        with open('./neptune-ml-pretrained-model-config.json') as f:
            config = json.load(f)
            region_name = boto3.session.Session().region_name
            if region_name in ['cn-north-1', 'cn-northwest-1']:
                self.PRETRAINED_MODEL = config['models_cn']
            else:
                self.PRETRAINED_MODEL = config['models']
            self.PYTORCH_CPU_CONTAINER_IMAGE = config['container_images'][region_name]

    def __run_create_model(self, sm_client,
                           name,
                           role,
                           image_uri,
                           model_s3_location,
                           container_mode='SingleModel',
                           script_name='infer_entry_point.py',
                           ):
        model_environment_vars = {self.SCRIPT_PARAM_NAME.upper(): script_name,
                                  self.DIR_PARAM_NAME.upper(): model_s3_location,
                                  self.CONTAINER_LOG_LEVEL_PARAM_NAME.upper(): str(20),
                                  self.MODEL_SERVER_TIMEOUT_PARAM_NAME.upper(): str(1200),
                                  self.MODEL_SERVER_WORKERS_PARAM_NAME.upper(): str(1),
                                  self.SAGEMAKER_REGION_PARAM_NAME.upper(): boto3.session.Session().region_name,
                                  self.ENABLE_CLOUDWATCH_METRICS_PARAM.upper(): "false"
                                  }

        container_def = [{"Image": self.PYTORCH_CPU_CONTAINER_IMAGE,
                          "Environment": model_environment_vars,
                          "ModelDataUrl": model_s3_location,
                          "Mode": container_mode
                          }]
        request = {"ModelName": name,
                   "ExecutionRoleArn": role,
                   "Containers": container_def
                   }
        return sm_client.create_model(**request)

    def __run_create_endpoint_config(self, sm_client,
                                     model_name,
                                     instance_type='ml.m5.2xlarge',
                                     initial_instance_count=1,
                                     initial_weight=1,
                                     variant_name='AllTraffic'
                                     ):
        production_variant_configuration = [{
            "ModelName": model_name,
            "InstanceType": instance_type,
            "InitialInstanceCount": initial_instance_count,
            "VariantName": variant_name,
            "InitialVariantWeight": initial_weight,
        }]
        request = {"EndpointConfigName": model_name,
                   "ProductionVariants": production_variant_configuration
                   }

        return sm_client.create_endpoint_config(**request)

    def __create_model(self, name: str, model_s3_location: str):
        image_uri = self.PYTORCH_CPU_CONTAINER_IMAGE
        instance_type = self.INSTANCE_TYPE
        role = self.__get_neptune_ml_role()
        sm = boto3.client("sagemaker")
        name = "{}-{}".format(name, strftime("%Y-%m-%d-%H-%M-%S", gmtime()))
        create_model_result = self.__run_create_model(
            sm, name, role, image_uri, model_s3_location)
        create_endpoint_config_result = self.__run_create_endpoint_config(
            sm, name, instance_type=instance_type)
        create_endpoint_result = sm.create_endpoint(
            EndpointName=name, EndpointConfigName=name)
        return name

    def __get_neptune_ml_role(self):
        with open(f'{HOME_DIRECTORY}/.bashrc') as f:
            data = f.readlines()
        for d in data:
            if str.startswith(d, 'export NEPTUNE_ML_ROLE_ARN'):
                parts = d.split('=')
                if len(parts) == 2:
                    return parts[1].rstrip()
        logging.error("Unable to determine the Neptune ML IAM Role.")
        return None

    def __copy_s3(self, s3_bucket_uri: str, source_s3_uri: str):
        path = urlparse(s3_bucket_uri, allow_fragments=False)
        bucket = path.netloc
        file_path = path.path.lstrip('/').rstrip('/')
        source_path = urlparse(source_s3_uri, allow_fragments=False)
        source_bucket = source_path.netloc
        source_file_path = source_path.path.lstrip('/').rstrip('/')
        s3 = boto3.resource('s3')
        s3.meta.client.copy(
            {"Bucket": source_bucket, "Key": source_file_path}, bucket, file_path)

    def setup_pretrained_endpoints(self, s3_bucket_uri: str,
                                   setup_node_classification: bool, setup_node_regression: bool,
                                   setup_link_prediction: bool, setup_edge_classification: bool,
                                   setup_edge_regression: bool):
        print('Beginning endpoint creation', end='\r')
        if setup_node_classification:
            # copy model
            self.__copy_s3(f'{s3_bucket_uri}/pretrained-models/node-classification/model.tar.gz',
                           self.PRETRAINED_MODEL['node_classification'])
            # create model
            classification_output = self.__create_model(
                'classifi', f'{s3_bucket_uri}/pretrained-models/node-classification/model.tar.gz')
        if setup_node_regression:
            # copy model
            self.__copy_s3(f'{s3_bucket_uri}/pretrained-models/node-regression/model.tar.gz',
                           self.PRETRAINED_MODEL['node_regression'])
            # create model
            regression_output = self.__create_model(
                'regressi', f'{s3_bucket_uri}/pretrained-models/node-regression/model.tar.gz')
        if setup_link_prediction:
            # copy model
            self.__copy_s3(f'{s3_bucket_uri}/pretrained-models/link-prediction/model.tar.gz',
                           self.PRETRAINED_MODEL['link_prediction'])
            # create model
            prediction_output = self.__create_model(
                'linkpred', f'{s3_bucket_uri}/pretrained-models/link-prediction/model.tar.gz')
        if setup_edge_classification:
            # copy model
            self.__copy_s3(f'{s3_bucket_uri}/pretrained-models/edge-classification/model.tar.gz',
                           self.PRETRAINED_MODEL['edge_classification'])
            # create model
            edgeclass_output = self.__create_model(
                'edgeclass', f'{s3_bucket_uri}/pretrained-models/edge-classification/model.tar.gz')
        if setup_edge_regression:
            # copy model
            self.__copy_s3(f'{s3_bucket_uri}/pretrained-models/edge-regression/model.tar.gz',
                           self.PRETRAINED_MODEL['edge_regression'])
            # create model
            edgereg_output = self.__create_model(
                'edgereg', f'{s3_bucket_uri}/pretrained-models/edge-regression/model.tar.gz')

        sleep(UPDATE_DELAY_SECONDS)
        classification_running = setup_node_classification
        regression_running = setup_node_regression
        prediction_running = setup_link_prediction
        edgeclass_running = setup_edge_classification
        edgereg_running = setup_edge_regression
        classification_endpoint_name = ""
        regression_endpoint_name = ""
        prediction_endpoint_name = ""
        edge_classification_endpoint_name = ""
        edge_regression_endpoint_name = ""
        sucessful = False
        sm = boto3.client("sagemaker")
        while classification_running or regression_running or prediction_running or edgeclass_running or edgereg_running:
            if classification_running:
                response = sm.describe_endpoint(
                    EndpointName=classification_output
                )
                if response['EndpointStatus'] in ['InService', 'Failed']:
                    if response['EndpointStatus'] == 'InService':
                        classification_endpoint_name = response
                    classification_running = False
            if regression_running:
                response = sm.describe_endpoint(
                    EndpointName=regression_output
                )
                if response['EndpointStatus'] in ['InService', 'Failed']:
                    if response['EndpointStatus'] == 'InService':
                        regression_endpoint_name = response
                    regression_running = False
            if prediction_running:
                response = sm.describe_endpoint(
                    EndpointName=prediction_output
                )
                if response['EndpointStatus'] in ['InService', 'Failed']:
                    if response['EndpointStatus'] == 'InService':
                        prediction_endpoint_name = response
                    prediction_running = False
            if edgeclass_running:
                response = sm.describe_endpoint(
                    EndpointName=edgeclass_output
                )
                if response['EndpointStatus'] in ['InService', 'Failed']:
                    if response['EndpointStatus'] == 'InService':
                        edge_classification_endpoint_name = response
                    edgeclass_running = False
            if edgereg_running:
                response = sm.describe_endpoint(
                    EndpointName=edgereg_output
                )
                if response['EndpointStatus'] in ['InService', 'Failed']:
                    if response['EndpointStatus'] == 'InService':
                        edge_regression_endpoint_name = response
                    edgereg_running = False

            print(
                f'Checking Endpoint Creation Statuses at {datetime.now().strftime("%H:%M:%S")}', end='\r')
            sleep(UPDATE_DELAY_SECONDS)

        print("")
        if classification_endpoint_name:
            print(
                f"Node Classification Endpoint Name: {classification_endpoint_name['EndpointName']}")
        if regression_endpoint_name:
            print(
                f"Node Regression Endpoint Name: {regression_endpoint_name['EndpointName']}")
        if prediction_endpoint_name:
            print(
                f"Link Prediction Endpoint Name: {prediction_endpoint_name['EndpointName']}")
        if edge_classification_endpoint_name:
            print(
                f"Edge Classification Endpoint Name: {edge_classification_endpoint_name['EndpointName']}")
        if edge_regression_endpoint_name:
            print(
                f"Edge Regression Endpoint Name: {edge_regression_endpoint_name['EndpointName']}")
        print('Endpoint creation complete', end='\r')
        return {
            'node_classification_endpoint_name': classification_endpoint_name,
            'node_regression_endpoint_name': regression_endpoint_name,
            'prediction_endpoint_name': prediction_endpoint_name,
            'edge_classification_endpoint_name': edge_classification_endpoint_name,
            'edge_regression_endpoint_name': edge_regression_endpoint_name
        }
