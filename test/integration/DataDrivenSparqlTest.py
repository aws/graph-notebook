"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

from graph_notebook.seed.load_query import get_queries
from test.integration import IntegrationTest

logger = logging.getLogger('DataDrivenSparqlTest')


class DataDrivenSparqlTest(IntegrationTest):

    def setUp(self) -> None:
        super().setUp()

        epl_queries = get_queries('sparql', 'epl')
        for q in epl_queries:
            try:  # we are deciding to try except because we do not know if the database we are connecting to has a partially complete set of airports data or not.
                res = self.client.sparql(q['content'].strip())
                print(res)
            except Exception as e:
                logger.error(f'query {q["content"]} failed due to {e}')
                continue
