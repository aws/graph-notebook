import json

from neo4j import Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from botocore.compat import urlsplit
from botocore.auth import SigV4Auth

SCHEME = "basic"
REALM = "realm"
SERVICE_NAME = "neptune-db"
DUMMY_USERNAME = "username"
HTTP_METHOD_HDR = "HttpMethod"
HTTP_METHOD = "GET"
AUTHORIZATION = "Authorization"
X_AMZ_DATE = "X-Amz-Date"
X_AMZ_SECURITY_TOKEN = "X-Amz-Security-Token"
HOST = "Host"


class NeptuneBoltAuthToken(Auth):
    def __init__(
        self,
        credentials: Credentials,
        region: str,
        url: str,
        **parameters
    ):
        request = AWSRequest(method=HTTP_METHOD, url=url)

        url_parts = urlsplit(request.url)
        host_part = url_parts.hostname
        request.headers.add_header("Host", host_part)
        sigv4 = SigV4Auth(credentials, SERVICE_NAME, region)
        sigv4.add_auth(request)

        auth_obj = {
          hdr: request.headers[hdr]
          for hdr in [AUTHORIZATION, X_AMZ_DATE, X_AMZ_SECURITY_TOKEN, HOST]
        }
        auth_obj[HTTP_METHOD_HDR] = request.method
        creds: str = json.dumps(auth_obj)
        super().__init__(SCHEME, DUMMY_USERNAME, creds, REALM, **parameters)
