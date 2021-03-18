"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

import pytest

from test.integration import IntegrationTest

logger = logging.getLogger('test_bug_fixes')


class TestBugFixes(IntegrationTest):
    """Because under the covers we use Gremlin Python there is a chance we can hit a limitation in the Gremlin Python
    driver that exposes a Python constraint. The key for a dict (map) type in Python must be hashable
    (which means it must be essentially immutable). A tuple like (1,2,3) is fine but a list [1,2,3] or map {'a':5}
    is not. We ran into this in a Data Lab a while back but we worked around it there by monkey patching the Gremlin
    Python client. We may want to do the same for the version of Gremlin Python used by the workbench."""

    def setUp(self) -> None:
        self.client = self.client_builder.build()
        queries = [
            "g.addV('Interest').property(id,'i1').property('value', 4)",
            "g.addV('Priority').property(id, 'p1').property('name', 'P1')",
            "g.addV('Member').property(id, 'm1')",
            "g.V('m1').addE('interested').to(g.V('i1'))",
            "g.V('m1').addE('prioritized').to(g.V('p1'))"
        ]
        for q in queries:
            self.client.gremlin_query(q)

    def tearDown(self) -> None:
        queries = [
            "g.V('i1').drop()",
            "g.V('p1').drop()",
            "g.V('m1').drop()"
        ]
        for q in queries:
            self.client.gremlin_query(q)

    @pytest.mark.gremlin
    def test_do_gremlin_query_with_map_as_key(self):
        query = """
        g.V().hasLabel("Interest").as("int")
            .in("interested")
            .out("prioritized").as("exp")
            .select("int","exp")
                .by("value")
                .by("name")
            .groupCount().unfold()
        """
        results = self.client.gremlin_query(query)
        keys_are_hashable = True
        for key in results[0].keys():
            try:
                hash(key)
            except TypeError:
                keys_are_hashable = False
                break
        self.assertEqual(keys_are_hashable, True)

    @pytest.mark.gremlin
    def test_do_gremlin_query_with_list_as_key(self):
        query = """
        g.V('m1').group()
            .by(out().fold())
            .by(out().count())
        """
        results = self.client.gremlin_query(query)
        keys_are_hashable = True
        for key in results[0].keys():
            try:
                hash(key)
            except TypeError:
                keys_are_hashable = False
                break
        self.assertEqual(keys_are_hashable, True)
