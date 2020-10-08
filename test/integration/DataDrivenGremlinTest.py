"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

from graph_notebook.gremlin.client_provider.factory import create_client_provider
from graph_notebook.seed.load_query import get_queries
from graph_notebook.gremlin.query import do_gremlin_query

from test.integration import IntegrationTest


class DataDrivenGremlinTest(IntegrationTest):
    def setUp(self):
        super().setUp()

        self.client_provider = create_client_provider(self.auth_mode, self.iam_credentials_provider_type)
        query_check_for_airports = "g.V('3684').outE().inV().has(id, '3444')"
        res = do_gremlin_query(query_check_for_airports, self.host, self.port, self.ssl, self.client_provider)
        if len(res) < 1:
            logging.info('did not find final airports edge, seeding database now...')
            airport_queries = get_queries('gremlin', 'airports')
            for q in airport_queries:
                lines = q['content'].splitlines()
                for i in range(len(lines)):
                    line = lines[i]
                    logging.debug(f'executing line {i} of {len(lines)} for seeding DataDrivenGremlinTest')
                    # we are deciding to try except because we do not know if the database
                    # we are connecting to has a partially complete set of airports data or not.
                    try:
                        do_gremlin_query(line, self.host, self.port, self.ssl, self.client_provider)
                    except Exception as e:
                        logging.error(f'query {q} failed due to {e}')
                        continue
