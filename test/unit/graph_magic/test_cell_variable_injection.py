"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.decorators.decorators import magic_variables


class TestCellVariableInjectionFunction(unittest.TestCase):
    def test_gremlin_variable_injection(self):
        @magic_variables
        def gremlin_mock(self_var, line, cell, local_ns: dict = None):
            return cell

        cell_expected = "g.V().hasLabel('airport').has('code','CZM').out('route').path().by('code')"

        self.assertEqual(gremlin_mock('', '', "g.V().hasLabel('${a}').has('${c}','CZM').out('${r}').path().by('${c}')",
                                      local_ns={'a': 'airport', 'c': 'code', 'r': 'route'}), cell_expected)

    def test_invalid_gremlin_variable_injection(self):
        @magic_variables
        def gremlin_mock(self_var, line, cell, local_ns: dict = None):
            return cell

        cell_expected = None

        self.assertEqual(gremlin_mock('', '', "g.V().hasLabel('${a}').has('${b}','CZM').out('${r}').path().by('${c}')",
                                      local_ns={'a': 'airport', 'c': 'code', 'r': 'route'}), cell_expected)

    def test_sparql_variable_injection(self):
        @magic_variables
        def sparql_mock(self_var, line, cell, local_ns: dict = None):
            return cell

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

        self.assertEqual(sparql_mock('', '',
                        '''
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                        PREFIX so: <https://schema.org/>

                        SELECT ?city
                        WHERE {
                            ?s a so:City .
                            ?s rdfs:label ?city
                            FILTER contains(?city,"${city_prefix}")
                        }
                        ''', local_ns={'city_prefix': 'ou'}), cell_expected)

    def test_invalid_sparql_variable_injection(self):
        @magic_variables
        def sparql_mock(self_var, line, cell, local_ns: dict = None):
            return cell

        cell_expected = None

        self.assertEqual(sparql_mock('', '',
                        '''
                        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                        PREFIX so: <https://schema.org/>

                        SELECT ?city
                        WHERE {
                            ?s a so:City .
                            ?s rdfs:label ?city
                            FILTER contains(?city,"${not_a_city_prefix}")
                        }
                        ''', local_ns={'city_prefix': 'ou'}), cell_expected)
