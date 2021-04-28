"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import pytest

from test.integration import DataDrivenSparqlTest
from graph_notebook.magics.metadata import build_sparql_metadata_from_query


class TestMetadataClassFunctions(DataDrivenSparqlTest):

    @pytest.mark.sparql
    def test_sparql_default_query_metadata(self):
        query = '''
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX so: <https://schema.org/>
                SELECT ?city
                WHERE {
                    ?s a so:City .
                    ?s rdfs:label ?city
                    FILTER contains(?city,"ou")
                }
                '''
        res = self.client.sparql(query)
        results = res.json()
        sparql_metadata = build_sparql_metadata_from_query(query_type='query', res=res, results=results, scd_query=True)
        meta_dict = sparql_metadata.to_dict()

        self.assertEqual(meta_dict["Query mode"], "query")
        self.assertIsInstance(meta_dict["Request execution time (ms)"], float)
        self.assertEqual(meta_dict["Status code"], 200)
        self.assertEqual(meta_dict["Status OK?"], True)
        self.assertEqual(meta_dict["# of results"], 2)
        self.assertIsInstance(meta_dict["Response content size (bytes)"], int)

    @pytest.mark.sparql
    @pytest.mark.neptune
    def test_sparql_explain_query_metadata(self):
        query = '''
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX so: <https://schema.org/>
                SELECT ?city
                WHERE {
                    ?s a so:City .
                    ?s rdfs:label ?city
                    FILTER contains(?city,"ou")
                }
                '''
        res = self.client.sparql_explain(query)
        sparql_metadata = build_sparql_metadata_from_query(query_type='explain', res=res)
        meta_dict = sparql_metadata.to_dict()

        self.assertEqual(meta_dict["Query mode"], "explain")
        self.assertIsInstance(meta_dict["Request execution time (ms)"], float)
        self.assertEqual(meta_dict["Status code"], 200)
        self.assertEqual(meta_dict["Status OK?"], True)
        self.assertIsInstance(meta_dict["Response content size (bytes)"], int)
