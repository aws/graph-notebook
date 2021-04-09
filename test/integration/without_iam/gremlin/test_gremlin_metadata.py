"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import time
import pytest

from test.integration import DataDrivenGremlinTest
from graph_notebook.magics.metadata import build_gremlin_metadata_from_query


class TestMetadataClassFunctions(DataDrivenGremlinTest):

    @pytest.mark.gremlin
    def test_gremlin_default_query_metadata(self):
        query = "g.V().has('airport','code','CZM').out('route').path().by('code')"
        query_start = time.time() * 1000
        results = self.client.gremlin_query(query)
        query_time = time.time() * 1000 - query_start
        gremlin_metadata = build_gremlin_metadata_from_query(query_type='query', results=results, query_time=query_time)
        meta_dict = gremlin_metadata.to_dict()

        self.assertEqual(meta_dict["Query mode"], "query")
        self.assertIsInstance(meta_dict["Request execution time (ms)"], float)
        self.assertEqual(meta_dict["# of results"], 11)
        self.assertIsInstance(meta_dict["Response size (bytes)"], int)

    @pytest.mark.gremlin
    @pytest.mark.neptune
    def test_gremlin_explain_query_metadata(self):
        query = "g.V().has('airport','code','CZM').out('route').path().by('code')"
        res = self.client.gremlin_explain(query)
        query_res = res.content.decode('utf-8')
        gremlin_metadata = build_gremlin_metadata_from_query(query_type='explain', results=query_res, res=res)
        meta_dict = gremlin_metadata.to_dict()

        self.assertEqual(meta_dict["Query mode"], "explain")
        self.assertIsInstance(meta_dict["Request execution time (ms)"], float)
        self.assertEqual(meta_dict["Status code"], 200)
        self.assertEqual(meta_dict["Status OK?"], True)
        self.assertEqual(meta_dict["# of predicates"], 18)
        self.assertIsInstance(meta_dict["Response size (bytes)"], int)

    @pytest.mark.gremlin
    @pytest.mark.neptune
    def test_gremlin_profile_query_metadata(self):
        query = "g.V().has('airport','code','CZM').out('route').path().by('code')"
        res = self.client.gremlin_profile(query)
        query_res = res.content.decode('utf-8')
        gremlin_metadata = build_gremlin_metadata_from_query(query_type='profile', results=query_res, res=res)
        meta_dict = gremlin_metadata.to_dict()

        self.assertEqual(meta_dict["Query mode"], "profile")
        self.assertIsInstance(meta_dict["Query execution time (ms)"], float)
        self.assertIsInstance(meta_dict["Request execution time (ms)"], float)
        self.assertEqual(meta_dict["Status code"], 200)
        self.assertEqual(meta_dict["Status OK?"], True)
        self.assertEqual(meta_dict["# of predicates"], 18)
        self.assertEqual(meta_dict["# of results"], 11)
        self.assertIsInstance(meta_dict["Response size (bytes)"], int)
