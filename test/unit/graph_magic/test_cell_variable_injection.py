"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.magics.graph_magic import inject_vars_into_query


class TestCellVariableInjectionFunction(unittest.TestCase):

    def test_gremlin_variable_injection(self):
        cell_expected = "g.V().hasLabel('airport').has('code','CZM').out('route').path().by('code')"

        test_ns = {'a': 'airport', 'c': 'code', 'r': 'route'}
        test_cell = "g.V().hasLabel('${a}').has('${c}','CZM').out('${r}').path().by('${c}')"
        new_cell = inject_vars_into_query(test_cell, test_ns)

        self.assertEqual(new_cell, cell_expected)

    def test_invalid_gremlin_variable_injection(self):
        expected = None

        test_ns = {'a': 'airport', 'c': 'code', 'r': 'route'}
        test_cell = "g.V().hasLabel('${a}').has('${b}','CZM').out('${r}').path().by('${c}')"
        new_cell = inject_vars_into_query(test_cell, test_ns)

        self.assertEqual(new_cell, expected)

    def test_sparql_variable_injection(self):
        cell_expected = '''
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX so: <https://schema.org/>

                    SELECT ?city
                    WHERE {
                        ?s a so:City .
                        ?s rdfs:label ?city
                        FILTER contains(?city,"ou")
                    }
                    '''

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

        self.assertEqual(new_cell, cell_expected)

    def test_invalid_sparql_variable_injection(self):
        cell_expected = None

        test_ns = {'city_prefix': 'ou'}
        test_cell = '''
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX so: <https://schema.org/>

                    SELECT ?city
                    WHERE {
                        ?s a so:City .
                        ?s rdfs:label ?city
                        FILTER contains(?city,"${not_a_city_prefix}")
                    }
                    '''
        new_cell = inject_vars_into_query(test_cell, test_ns)

        self.assertEqual(new_cell, cell_expected)
