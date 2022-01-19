"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

from graph_notebook.seed.load_query import get_queries

from test.integration import IntegrationTest


class DataDrivenGremlinTest(IntegrationTest):
    def setUp(self):
        super().setUp()

        self.client = self.client_builder.build()
        query_check_for_airports = "g.V('3745').outE().inV().has(id, '3195')"
        res = self.client.gremlin_query(query_check_for_airports)
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
                        self.client.gremlin_query(line)
                    except Exception as e:
                        logging.error(f'query {q} failed due to {e}')
                        continue
