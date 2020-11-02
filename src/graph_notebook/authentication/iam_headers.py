"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import datetime
import hashlib
import hmac
import logging
import urllib


logging.basicConfig()
logger = logging.getLogger("graph_magic")


# Key derivation functions. See:
# https://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature_key(key, dateStamp, regionName, serviceName):
    k_date = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    k_region = sign(k_date, regionName)
    k_service = sign(k_region, serviceName)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing


def get_canonical_uri_and_payload(query_type, query):
    # Set the stack and payload depending on query_type.
    if query_type == 'sparql':
        canonical_uri = '/sparql/'
        payload = query

    elif query_type == 'sparqlupdate':
        canonical_uri = '/sparql/'
        payload = query

    elif query_type == 'sparql/status':
        canonical_uri = '/sparql/status/'
        payload = query

    elif query_type == 'gremlin':
        canonical_uri = '/gremlin'
        payload = {}

    elif query_type == 'gremlin/status':
        canonical_uri = '/gremlin/status/'
        payload = query

    elif query_type == "loader":
        canonical_uri = "/loader/"
        payload = query

    elif query_type == "status":
        canonical_uri = "/status/"
        payload = {}

    elif query_type == "gremlin/explain":
        canonical_uri = "/gremlin/explain/"
        payload = query

    elif query_type == "gremlin/profile":
        canonical_uri = "/gremlin/profile/"
        payload = query

    elif query_type == "system":
        canonical_uri = "/system/"
        payload = query
    else:
        raise ValueError('query_type %s is not valid' % query_type)

    return canonical_uri, payload


def normalize_query_string(query):
    kv = (list(map(str.strip, s.split("=")))
          for s in query.split('&')
          if len(s) > 0)

    normalized = '&'.join('%s=%s' % (p[0], p[1] if len(p) > 1 else '')
                          for p in sorted(kv))
    return normalized


def make_signed_request(method, query_type, query, host, port, signing_access_key, signing_secret, signing_region, use_ssl=False, signing_token='', additional_headers=None):
    if additional_headers is None:
        additional_headers = []

    signing_region = signing_region.lower()
    service = 'neptune-db'

    if use_ssl:
        protocol = 'https'
    else:
        protocol = 'http'

    # this is always http right now
    endpoint = f'{protocol}://{host}:{port}'

    # get canonical_uri and payload
    canonical_uri, payload = get_canonical_uri_and_payload(query_type, query)

    request_parameters = urllib.parse.urlencode(payload, quote_via=urllib.parse.quote)
    request_parameters = request_parameters.replace('%27', '%22')
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')  # Date w/o time, used in credential scope

    method = method.upper()
    if method == 'GET' or method == 'DELETE':
        canonical_querystring = normalize_query_string(request_parameters)
    elif method == 'POST':
        canonical_querystring = ''
    else:
        raise ValueError('method %s is not valid when creating canonical request' % method)

    # Step 4: Create the canonical headers and signed headers. Header names
    # must be trimmed and lowercase, and sorted in code point order from
    # low to high. Note that there is a trailing \n.
    canonical_headers = f'host:{host}:{port}\nx-amz-date:{amz_date}\n'

    # Step 5: Create the list of signed headers. This lists the headers
    # in the canonical_headers list, delimited with ";" and in alpha order.
    # Note: The request can include any headers; canonical_headers and
    # signed_headers lists those that you want to be included in the
    # hash of the request. "Host" and "x-amz-date" are always required.
    signed_headers = 'host;x-amz-date'

    # Step 6: Create payload hash (hash of the request body content). For GET and DELETE
    # requests, the payload is an empty string ("").
    if method == 'GET' or method == 'DELETE':
        post_payload = ''
    elif method == 'POST':
        post_payload = request_parameters
    else:
        raise ValueError('method %s is not supported' % method)

    payload_hash = hashlib.sha256(post_payload.encode('utf-8')).hexdigest()

    # Step 7: Combine elements to create canonical request.
    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    # ************* TASK 2: CREATE THE STRING TO SIGN*************
    # Match the algorithm to the hashing algorithm you use, either SHA-1 or
    # SHA-256 (recommended)
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + signing_region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' + amz_date + '\n' + credential_scope + '\n' + hashlib.sha256(
        canonical_request.encode('utf-8')).hexdigest()

    # ************* TASK 3: CALCULATE THE SIGNATURE *************
    # Create the signing key using the function defined above.
    signing_key = get_signature_key(signing_secret, date_stamp, signing_region, service)

    # Sign the string_to_sign using the signing_key
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
    # The signing information can be either in a query string value or in
    # a header named Authorization. This code shows how to use a header.
    # Create authorization header and add to request headers
    authorization_header = algorithm + ' ' + 'Credential=' + signing_access_key + '/' + credential_scope + ', ' + 'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    # The request can include any headers, but MUST include "host", "x-amz-date",
    # and (for this scenario) "Authorization". "host" and "x-amz-date" must
    # be included in the canonical_headers and signed_headers, as noted
    # earlier. Order here is not significant.
    # Python note: The 'host' header is added automatically by the Python 'requests' library.
    if method == 'GET' or method == 'DELETE':
        headers = {
            'x-amz-date': amz_date,
            'Authorization': authorization_header
        }
    elif method == 'POST':
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'x-amz-date': amz_date,
            'Authorization': authorization_header,
        }
    else:
        raise ValueError('method %s is not valid while creating request headers' % method)

    if additional_headers is not None:
        for key in additional_headers:
            headers[key] = additional_headers[key]

    if signing_token != '':
        headers['X-Amz-Security-Token'] = signing_token

    # ************* SEND THE REQUEST *************
    request_url = endpoint + canonical_uri

    return {
        'url': request_url,
        'headers': headers,
        'params': request_parameters
    }
