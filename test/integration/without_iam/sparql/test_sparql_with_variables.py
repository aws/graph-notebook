"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import pytest

from test.integration import DataDrivenSparqlTest
from graph_notebook.magics.graph_magic import inject_vars_into_query


class TestSparqlQueryWithVariables(DataDrivenSparqlTest):

    @pytest.mark.sparql
    def test_sparql_query_with_variables(self):
        expected_result = {'head': {'vars': ['city']}, 'results': {'bindings': [{'city': {'type': 'literal', 'value': 'Southampton'}}, {'city': {'type': 'literal', 'value': 'Bournemouth'}}]}}

        test_ns = {'city_prefix': 'ou'}
        test_cell = '''
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX so: <https://schema.org/>

                    SELECT ?city
                    WHERE {
                        ?s a so:City .
                        ?s rdfs:label ?city
                        FILTER contains(?city,"${city_prefix}")
                    }
                    '''

        new_cell = inject_vars_into_query(test_cell, test_ns)
        res = self.client.sparql(new_cell)
        results = res.json()

        self.assertEqual(results, expected_result)
