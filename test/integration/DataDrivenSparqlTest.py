"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.seed.load_query import get_queries
from graph_notebook.request_param_generator.factory import create_request_generator
from graph_notebook.sparql.query import do_sparql_query

from test.integration import IntegrationTest

logger = logging.getLogger('DataDrivenSparqlTest')


class DataDrivenSparqlTest(IntegrationTest):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request_generator = create_request_generator(cls.auth_mode, IAMAuthCredentialsProvider.ENV)

        airport_queries = get_queries('sparql', 'epl')
        for q in airport_queries:
            try:  # we are deciding to try except because we do not know if the database we are connecting to has a partially complete set of airports data or not.
                do_sparql_query(q['content'], cls.host, cls.port, cls.ssl, cls.request_generator)
            except Exception as e:
                logger.error(f'query {q["content"]} failed due to {e}')
                continue
