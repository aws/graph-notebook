"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import pytest

from test.integration import IntegrationTest
from graph_notebook.magics.metadata import build_sparql_metadata_from_query


class TestMetadataClassFunctions(IntegrationTest):

    @pytest.mark.sparql
    def test_sparql_default_query_metadata(self):
        query = "SELECT ?s ?p ?o {?s ?p ?o} LIMIT 100"
        res = self.client.sparql(query)
        results = res.json()
        sparql_metadata = build_sparql_metadata_from_query(query_type='query', res=res, results=results, scd_query=True)
        meta_dict = sparql_metadata.to_dict()

        self.assertEqual(meta_dict["Query mode"], "query")
        self.assertIsInstance(meta_dict["Request execution time (ms)"], float)
        self.assertEqual(meta_dict["Status code"], 200)
        self.assertEqual(meta_dict["Status OK?"], True)
        self.assertEqual(meta_dict["# of results"], 100)
        self.assertEqual(meta_dict["Response content size (bytes)"], 36399)

    @pytest.mark.sparql
    def test_sparql_explain_query_metadata(self):
        query = "SELECT ?s ?p ?o {?s ?p ?o} LIMIT 100"
        res = self.client.sparql_explain(query)
        sparql_metadata = build_sparql_metadata_from_query(query_type='query', res=res)
        meta_dict = sparql_metadata.to_dict()

        self.assertEqual(meta_dict["Query mode"], "explain")
        self.assertIsInstance(meta_dict["Request execution time (ms)"], float)
        self.assertEqual(meta_dict["Status code"], 200)
        self.assertEqual(meta_dict["Status OK?"], True)
        self.assertEqual(meta_dict["Response content size (bytes)"], 1991)
