"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

from graph_notebook.gremlin.client_provider.default_client import ClientProvider
from graph_notebook.gremlin.query import do_gremlin_query

from test.integration import IntegrationTest

logger = logging.getLogger('TestUnhashableTypeDict')


class TestBugFixes(IntegrationTest):
    """Because under the covers we use Gremlin Python there is a chance we can hit a limitation in the Gremlin Python
    driver that exposes a Python constraint. The key for a dict (map) type in Python must be hashable
    (which means it must be essentially immutable). A tuple like (1,2,3) is fine but a list [1,2,3] or map {'a':5}
    is not. We ran into this in a Data Lab a while back but we worked around it there by monkey patching the Gremlin
    Python client. We may want to do the same for the version of Gremlin Python used by the workbench."""

    @classmethod
    def setUpClass(cls):
        super(TestBugFixes, cls).setUpClass()

        cls.client_provider = ClientProvider()

        queries = [
            "g.addV('Interest').property(id,'i1').property('value', 4)",
            "g.addV('Priority').property(id, 'p1').property('name', 'P1')",
            "g.addV('Member').property(id, 'm1')",
            "g.V('m1').addE('interested').to(g.V('i1'))",
            "g.V('m1').addE('prioritized').to(g.V('p1'))"
        ]
        cls.runQueries(queries)

    @classmethod
    def tearDownClass(cls):
        queries = [
            "g.V('i1').drop()",
            "g.V('p1').drop()",
            "g.V('m1').drop()"
        ]
        cls.runQueries(queries)

    @classmethod
    def runQueries(cls, queries):
        for query in queries:
            try:
                do_gremlin_query(query, cls.host, cls.port, cls.ssl, cls.client_provider)
            except Exception as e:
                logger.error(f'query {query} failed due to {e}')

    def test_do_gremlin_query(self):
        query = """
        g.V().hasLabel("Interest").as("int")
            .in("interested")
            .out("prioritized").as("exp")
            .select("int","exp")
                .by("value")
                .by("name")
            .groupCount().unfold()
        """
        results = do_gremlin_query(query, self.host, self.port, self.ssl, self.client_provider)

        self.assertEqual(results, [{(('int', 4), ('exp', 'P1')): 1}])
