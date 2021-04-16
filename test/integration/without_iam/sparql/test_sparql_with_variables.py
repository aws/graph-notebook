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
        expected_result = {'head': {'vars': ['team', 'city']}, 'results': {'bindings': [{'team': {'type': 'literal', 'value': 'Manchester United'}, 'city': {'type': 'literal', 'value': 'Manchester'}}]}}

        test_ns = {'h': 'homeStadium', 'l': 'location', 'mann_u': 'Manchester United'}
        test_cell = '''
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX soco: <http://www.example.com/soccer/ontology/>
                    PREFIX socr: <http://www.example.com/soccer/resource#>
                    PREFIX so: <https://schema.org/>

                    SELECT ?team ?city
                    WHERE {
                        VALUES ?team {"${mann_u}"}
                        ?s soco:${h}/so:${l} ?o .
                        ?s rdfs:label ?team .
                        ?o rdfs:label ?city
                    }
                    '''
        new_cell = inject_vars_into_query(test_cell, test_ns)
        res = self.client.sparql(new_cell)
        results = res.json()

        self.assertEqual(results, expected_result)
