"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import graph_notebook.gremlin.client_provider.graphsonV3d0_MapType_objectify_patch  # noqa F401
import logging

from gremlin_python.driver import client

logging.basicConfig()
logger = logging.getLogger("default_client")


class ClientProvider(object):
    @staticmethod
    def get_client(host, port, use_ssl):
        protocol = 'wss' if use_ssl else 'ws'
        url = f'{protocol}://{host}:{port}/gremlin'
        c = client.Client(url, 'g')
        return c
