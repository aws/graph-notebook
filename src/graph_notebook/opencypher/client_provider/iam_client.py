import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import datetime
import json

from neo4j import GraphDatabase

from graph_notebook.authentication.iam_credentials_provider.credentials_provider import CredentialsProviderBase
from graph_notebook.opencypher.client_provider.default_client import AbstractCypherClientProvider


class IAMCypherClientProvider(AbstractCypherClientProvider):
    """
    CypherClientProvider is a client which will attempt to obtain a bolt
    connection to the configured endpoint without any authentication settings
    """

    def __init__(self, credentials_provider: CredentialsProviderBase):
        self.credentials_provider = credentials_provider

    def get_driver(self, host: str, port: str, ssl: bool, user: str = 'neo4j', password: str = 'neo4j') -> GraphDatabase.driver:
        creds = self.credentials_provider.get_iam_credentials()
        uri = f'bolt://{host}:{port}'

        method = 'POST'
        headers = {
            'HttpVersion': 'HTTP/1.1',
            'HttpMethod': method,
            'Host': f'bolt://{host}:{port}'
        }

        session = boto3.Session(aws_access_key_id=creds.key, aws_secret_access_key=creds.secret,
                                aws_session_token=creds.token, region_name=creds.region)
        credentials = session.get_credentials()
        frozen_creds = credentials.get_frozen_credentials()

        req = AWSRequest(method=method, url=uri)
        SigV4Auth(frozen_creds, "neptune-db", creds.region).add_auth(req)
        prepared = req.prepare()

        for item in prepared.headers.items():
            headers[item[0]] = item[1]

        auth_str = json.dumps(headers)
        driver = GraphDatabase.driver(uri, auth=('neo4j', auth_str), encrypted=ssl)
        return driver
