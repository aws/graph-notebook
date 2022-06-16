import shutil
import urllib

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

from rdflib import Namespace, ConjunctiveGraph, RDF, Literal, XSD, RDFS
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


def get_neptune_ml_role():
    with open(f'{HOME_DIRECTORY}/.bashrc') as f:
        data = f.readlines()

    for d in data:
        if str.startswith(d, 'export NEPTUNE_ML_ROLE_ARN'):
            parts = d.split('=')
            if len(parts) == 2:
                print('ml role: ' + parts[1].rstrip())
                return parts[1].rstrip()
    logging.error("Unable to determine the Neptune ML IAM Role.")
    return None


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


def delete_pretrained_endpoints(endpoints: dict):
    sm = boto3.client("sagemaker")
    try:
        if 'object_classification_endpoint_name' in endpoints and endpoints['object_classification_endpoint_name']:
            sm.delete_endpoint(
                EndpointName=endpoints['object_classification_endpoint_name']["EndpointName"])
        if 'object_regression_endpoint_name' in endpoints and endpoints['object_regression_endpoint_name']:
            sm.delete_endpoint(
                EndpointName=endpoints['object_regression_endpoint_name']["EndpointName"])
        if 'link_prediction_endpoint_name' in endpoints and endpoints['link_prediction_endpoint_name']:
            sm.delete_endpoint(
                EndpointName=endpoints['link_prediction_endpoint_name']["EndpointName"])
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


def prepare_movielens_data_rdf(s3_bucket_uri: str, clear_staging_area: bool = True):
    try:
        return MovieLensProcessor().prepare_movielens_data_rdf(s3_bucket_uri, clear_staging_area)
    except Exception as e:
        logging.error(e)


def setup_pretrained_endpoints_rdf(s3_bucket_uri: str, setup_object_classification: bool, setup_object_regression: bool,
                                   setup_link_prediction: bool):
    try:
        return PretrainedModels().setup_pretrained_endpoints_rdf(s3_bucket_uri, setup_object_classification,
                                                                 setup_object_regression, setup_link_prediction)
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

    ns_resource = Namespace("http://aws.amazon.com/neptune/resource#")
    ns_ontology = Namespace("http://aws.amazon.com/neptune/ontology/")

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

    def __upload_to_s3(self, bucketname: str):
        path = urlparse(bucketname, allow_fragments=False)
        bucket = path.netloc
        file_path = path.path.lstrip('/').rstrip('/')

        s3_client = boto3.client('s3')
        for root, dirs, files in os.walk(self.formatted_directory):
            for file in files:
                s3_client.upload_file(os.path.join(
                    self.formatted_directory, file), bucket, f'{file_path}/{file}')

    def prepare_movielens_data_rdf(self, s3_bucket: str, clear_staging_area: bool):
        self.formatted_directory = f'{self.formatted_directory}/rdf'
        if clear_staging_area:
            print('Clearing staging area by default, use "clear_staging_area=False" to retain')
            shutil.rmtree(self.formatted_directory, ignore_errors=True)
            os.makedirs(self.formatted_directory, exist_ok=True)
        bucket_name = f'{s3_bucket}/neptune-formatted/movielens-100k/rdf/'
        self.__download_and_unzip()
        self.__process_movies_genres_rdf()
        self.__process_users_rdf()
        self.__process_ratings_users_rdf()
        self.__upload_to_s3(bucket_name)
        if clear_staging_area:
            shutil.rmtree(self.formatted_directory, ignore_errors=True)
        print('Completed Processing, data is ready for loading using the s3 url below:')
        print(bucket_name)
        return bucket_name

    def __process_movies_genres_rdf(self):
        # process the movies_vertex.csv
        print('Processing Movies to RDF')
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

        genres = ['unknown', 'Action', 'Adventure', 'Animation', 'Childrens', 'Comedy',
                  'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical',
                  'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']

        genre_df = pd.DataFrame(genres, columns=['~id'])
        genre_df['~label'] = 'genre'
        genre_df['name'] = genre_df['~id']

        movie_rdf_filename = os.path.join(self.formatted_directory, 'movies.nq')
        movie_genre_rdf_filename = os.path.join(self.formatted_directory, 'movie_genres.nq')
        movie_graph = ConjunctiveGraph()
        movie_genre_graph = ConjunctiveGraph()

        # movie vertex file creation
        for index, row in movies_df.iterrows():
            id = row['~id']
            title = row['title']
            imdb_url = row['imdb_url']
            release_date = row['release_date']

            movie_graph.add((
                self.ns_resource[id], RDF.type, self.ns_ontology.Movie, self.ns_ontology.Movies
            ))
            movie_graph.add((
                self.ns_resource[id], self.ns_ontology.title, Literal(title, datatype=XSD.string),
                self.ns_ontology.Movies
            ))
            movie_graph.add((
                self.ns_resource[id], RDFS.label, Literal(title, datatype=XSD.string), self.ns_ontology.Movies
            ))
            movie_graph.add((
                self.ns_resource[id], self.ns_ontology.imdbURL, Literal(imdb_url, datatype=XSD.anyURI),
                self.ns_ontology.Movies
            ))
            movie_graph.add((
                self.ns_resource[id], self.ns_ontology.releaseDate,
                Literal(release_date, datatype=XSD.dateTime), self.ns_ontology.Movies
            ))
            # add genre labels
            for genre_value in genres:
                if row[genre_value]:
                    movie_genre_graph.add((
                        self.ns_resource[id], self.ns_ontology.hasGenre,
                        Literal(genre_value, datatype=XSD.string), self.ns_ontology.Movie
                    ))
                    movie_genre_graph.add((
                        self.ns_resource[id], self.ns_ontology.hasOriginalGenre,
                        Literal(genre_value, datatype=XSD.string), self.ns_ontology.Movie
                    ))

        movie_graph.serialize(format='nquads', destination=movie_rdf_filename)
        movie_genre_graph.serialize(format='nquads', destination=movie_genre_rdf_filename)

    def __process_users_rdf(self):
        print("Processing Users to RDF")
        # User Vertices - Load, rename column with type, and save

        user_df = pd.read_csv(os.path.join(
            self.raw_directory, 'ml-100k/u.user'), sep='|', encoding='ISO-8859-1',
            names=['~id', 'age:Int', 'gender', 'occupation', 'zip_code'])
        user_df['~id'] = user_df['~id'].apply(
            lambda x: f'user_{x}'
        )

        users_graph = ConjunctiveGraph()

        for index, row in user_df.iterrows():
            users_graph.add((
                self.ns_resource[row['~id']], RDF.type, self.ns_ontology.User, self.ns_ontology.DefaultNamedGraph
            ))
            users_graph.add((
                self.ns_resource[row['~id']], self.ns_ontology.age,
                Literal(row['age:Int'], datatype=XSD.integer), self.ns_ontology.Users
            ))
            users_graph.add((
                self.ns_resource[row['~id']], self.ns_ontology.occupation,
                Literal(row['occupation'], datatype=XSD.string),
                self.ns_ontology.Users
            ))
            users_graph.add((
                self.ns_resource[row['~id']], self.ns_ontology.gender, Literal(row['gender'], datatype=XSD.string),
                self.ns_ontology.Users
            ))
            users_graph.add((
                self.ns_resource[row['~id']], self.ns_ontology.zipCode,
                Literal(row['zip_code'], datatype=XSD.string),
                self.ns_ontology.Users
            ))

        users_rdf_file = os.path.join(self.formatted_directory, 'users.nq')
        users_graph.serialize(format='nquads', destination=users_rdf_file)

    def __process_ratings_users_rdf(self):
        # Create ratings vertices and add edges on both sides
        print('Processing Ratings to RDF')
        ratings_vertices = pd.read_csv(
            os.path.join(self.raw_directory, 'ml-100k/u.data'),
            sep='\t',
            encoding='ISO-8859-1',
            names=['~from', '~to', 'score:Int', 'timestamp']
        )
        ratings_vertices['~from'] = ratings_vertices['~from'].apply(lambda x: f'user_{x}')
        ratings_vertices['~to'] = ratings_vertices['~to'].apply(lambda x: f'movie_{x}')
        ratings_vertices['~id'] = ratings_vertices['~from'].str.cat(ratings_vertices['~to'], sep="_")
        ratings_vertices['~label'] = "rating"

        ratings_graph = ConjunctiveGraph()

        averages_graph = ConjunctiveGraph()

        for index, row in ratings_vertices.groupby('~to').mean().iterrows():
            score = int(round(row['score:Int']))
            averages_graph.add((
                self.ns_resource[index], self.ns_ontology.criticScore, Literal(score, datatype=XSD.integer),
                self.ns_ontology.Rating
            ))

        for index, row in ratings_vertices.iterrows():
            uri = urllib.parse.quote_plus(row['~id'])
            ratings_graph.add((
                self.ns_resource[uri], RDF.type, self.ns_ontology.Rating, self.ns_ontology.Rating
            ))
            ratings_graph.add((
                self.ns_resource[uri], self.ns_ontology.score,
                Literal(row['score:Int'], datatype=XSD.integer),
                self.ns_ontology.Rating
            ))
            ratings_graph.add((
                self.ns_resource[uri], self.ns_ontology.timestamp, Literal(row['timestamp']),
                self.ns_ontology.Rating
            ))
            ratings_graph.add((
                self.ns_resource[uri], self.ns_ontology.forMovie, self.ns_resource[row['~to']],
                self.ns_ontology.Rating
            ))
            ratings_graph.add((
                self.ns_resource[uri], self.ns_ontology.byUser, self.ns_resource[row['~from']],
                self.ns_ontology.Rating
            ))
            if row['score:Int'] > 3:
                ratings_graph.add((
                    self.ns_resource[row['~from']], self.ns_ontology.recommended, self.ns_resource[row['~to']],
                    self.ns_ontology.Rating
                ))
                ratings_graph.add((
                    self.ns_resource[row['~to']], self.ns_ontology.wasRecommendedBy, self.ns_resource[row['~from']],
                    self.ns_ontology.Rating
                ))

        ratings_rdf_file = os.path.join(self.formatted_directory, 'user_movie_ratings.nq')
        averages_graph_file = os.path.join(self.formatted_directory, 'critic_movie_scores.nq')

        ratings_graph.serialize(format='nquads', destination=ratings_rdf_file)
        averages_graph.serialize(format='nquads', destination=averages_graph_file)


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
        with open('./neptune-ml-pretrained-rdf-model-config.json') as f:
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

    def get_neptune_role(self):
        role = self.__get_neptune_ml_role()
        return role

    def setup_pretrained_endpoints_rdf(self, s3_bucket_uri: str, setup_object_classification: bool,
                                       setup_object_regression: bool, setup_link_prediction: bool):
        print('Beginning endpoint creation', end='\r')
        if setup_object_classification:
            # copy model
            self.__copy_s3(f'{s3_bucket_uri}/rdf/pretrained-models/object-classification/model.tar.gz',
                           self.PRETRAINED_MODEL['object_classification'])
            # create model
            classification_output = self.__create_model(
                'classifi', f'{s3_bucket_uri}/rdf/pretrained-models/object-classification/model.tar.gz')
        if setup_object_regression:
            # copy model
            self.__copy_s3(f'{s3_bucket_uri}/rdf/pretrained-models/object-regression/model.tar.gz',
                           self.PRETRAINED_MODEL['object_regression'])
            # create model
            regression_output = self.__create_model(
                'regressi', f'{s3_bucket_uri}/rdf/pretrained-models/object-regression/model.tar.gz')
        if setup_link_prediction:
            # copy model
            self.__copy_s3(f'{s3_bucket_uri}/rdf/pretrained-models/link-prediction/model.tar.gz',
                           self.PRETRAINED_MODEL['link_prediction'])
            # create model
            prediction_output = self.__create_model(
                'linkpred', f'{s3_bucket_uri}/rdf/pretrained-models/link-prediction/model.tar.gz')

        sleep(UPDATE_DELAY_SECONDS)
        classification_running = setup_object_classification
        regression_running = setup_object_regression
        prediction_running = setup_link_prediction
        classification_endpoint_name = ""
        regression_endpoint_name = ""
        prediction_endpoint_name = ""
        sm = boto3.client("sagemaker")

        while classification_running or regression_running or prediction_running:
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

        print('Endpoint creation complete', end='\r')
        return {
            'object_classification_endpoint_name': classification_endpoint_name,
            'object_regression_endpoint_name': regression_endpoint_name,
            'link_prediction_endpoint_name': prediction_endpoint_name
        }
