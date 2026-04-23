"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest
from unittest.mock import MagicMock
from graph_notebook.schema_model import GraphSchema
from graph_notebook.magics.schema import (
    _get_labels, _get_triples, _get_node_properties, _get_edge_properties,
    get_schema, _uri_local_name, _is_metadata_uri,
)


class TestGetLabels(unittest.TestCase):
    def test_basic(self):
        summary = {'nodeLabels': ['person', 'software'], 'edgeLabels': ['created', 'knows']}
        n, e = _get_labels(summary)
        self.assertEqual(n, ['person', 'software'])
        self.assertEqual(e, ['created', 'knows'])

    def test_empty(self):
        summary = {'nodeLabels': [], 'edgeLabels': []}
        n, e = _get_labels(summary)
        self.assertEqual(n, [])
        self.assertEqual(e, [])


class TestGetTriples(unittest.TestCase):
    def _mock_client(self, responses):
        client = MagicMock()
        client.opencypher_http.side_effect = [
            MagicMock(json=MagicMock(return_value=r)) for r in responses
        ]
        return client

    def test_single_label_nodes(self):
        client = self._mock_client([
            {'results': [
                {'from': ['person'], 'edge': 'created', 'to': ['software']},
            ]},
        ])
        result = _get_triples(client, ['created'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].left_node, 'person')
        self.assertEqual(result[0].right_node, 'software')
        self.assertEqual(result[0].relation, 'created')

    def test_multi_label_nodes(self):
        client = self._mock_client([
            {'results': [
                {'from': ['Person', 'Employee'], 'edge': 'WORKS_AT', 'to': ['Company']},
            ]},
        ])
        result = _get_triples(client, ['WORKS_AT'])
        self.assertEqual(result[0].left_node, 'Employee:Person')
        self.assertEqual(result[0].right_node, 'Company')

    def test_multiple_edge_labels(self):
        client = self._mock_client([
            {'results': [{'from': ['person'], 'edge': 'created', 'to': ['software']}]},
            {'results': [{'from': ['person'], 'edge': 'knows', 'to': ['person']}]},
        ])
        result = _get_triples(client, ['created', 'knows'])
        self.assertEqual(len(result), 2)

    def test_empty_results(self):
        client = self._mock_client([{'results': []}])
        result = _get_triples(client, ['orphan'])
        self.assertEqual(result, [])


class TestGetNodeProperties(unittest.TestCase):
    def _mock_client(self, responses):
        client = MagicMock()
        client.opencypher_http.side_effect = [
            MagicMock(json=MagicMock(return_value=r)) for r in responses
        ]
        return client

    def test_aggregates_across_nodes(self):
        """Properties from different nodes should be merged."""
        client = self._mock_client([
            {'results': [
                {'props': {'name': 'a', 'color': 'red'}},
                {'props': {'name': 'b', 'size': 5}},
            ]},
        ])
        types = {'str': 'STRING', 'int': 'INTEGER'}
        result = _get_node_properties(client, ['testnode'], types)
        self.assertEqual(len(result), 1)
        prop_names = {p.name for p in result[0].properties}
        self.assertEqual(prop_names, {'name', 'color', 'size'})

    def test_multiple_types_for_same_property(self):
        """A property with different types across nodes should collect all types."""
        client = self._mock_client([
            {'results': [
                {'props': {'value': 'hello'}},
                {'props': {'value': 42}},
            ]},
        ])
        types = {'str': 'STRING', 'int': 'INTEGER'}
        result = _get_node_properties(client, ['mixed'], types)
        value_prop = [p for p in result[0].properties if p.name == 'value'][0]
        self.assertEqual(set(value_prop.type), {'STRING', 'INTEGER'})

    def test_empty_results(self):
        client = self._mock_client([{'results': []}])
        types = {'str': 'STRING'}
        result = _get_node_properties(client, ['empty'], types)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].labels, 'empty')
        self.assertEqual(result[0].properties, [])

    def test_multiple_labels(self):
        client = self._mock_client([
            {'results': [{'props': {'name': 'marko', 'age': 29}}]},
            {'results': [{'props': {'name': 'lop', 'lang': 'java'}}]},
        ])
        types = {'str': 'STRING', 'int': 'INTEGER'}
        result = _get_node_properties(client, ['person', 'software'], types)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].labels, 'person')
        self.assertEqual(result[1].labels, 'software')


class TestGetEdgeProperties(unittest.TestCase):
    def _mock_client(self, responses):
        client = MagicMock()
        client.opencypher_http.side_effect = [
            MagicMock(json=MagicMock(return_value=r)) for r in responses
        ]
        return client

    def test_aggregates_across_edges(self):
        client = self._mock_client([
            {'results': [
                {'props': {'weight': 0.5}},
                {'props': {'weight': 1.0, 'since': 2020}},
            ]},
        ])
        types = {'float': 'DOUBLE', 'int': 'INTEGER'}
        result = _get_edge_properties(client, ['knows'], types)
        self.assertEqual(len(result), 1)
        prop_names = {p.name for p in result[0].properties}
        self.assertEqual(prop_names, {'weight', 'since'})

    def test_empty_results(self):
        client = self._mock_client([{'results': []}])
        types = {'str': 'STRING'}
        result = _get_edge_properties(client, ['empty'], types)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].properties, [])


class TestGetSchemaNeptuneDB(unittest.TestCase):
    def test_neptune_db_path(self):
        client = MagicMock()
        config = MagicMock()
        config.neptune_service = 'neptune-db'

        summary_response = MagicMock()
        summary_response.json.return_value = {
            'payload': {'graphSummary': {
                'nodeLabels': ['person'],
                'edgeLabels': ['knows'],
            }}
        }
        client.statistics.return_value = summary_response

        # triples query
        triples_resp = MagicMock()
        triples_resp.json.return_value = {
            'results': [{'from': ['person'], 'edge': 'knows', 'to': ['person']}]
        }
        # node properties query
        node_props_resp = MagicMock()
        node_props_resp.json.return_value = {
            'results': [{'props': {'name': 'marko', 'age': 29}}]
        }
        # edge properties query
        edge_props_resp = MagicMock()
        edge_props_resp.json.return_value = {
            'results': [{'props': {'weight': 0.5}}]
        }
        client.opencypher_http.side_effect = [triples_resp, node_props_resp, edge_props_resp]

        schema = get_schema(client, config)
        self.assertIsInstance(schema, GraphSchema)
        self.assertEqual(len(schema.nodes), 1)
        self.assertEqual(schema.nodes[0].labels, 'person')
        self.assertEqual(len(schema.relationships), 1)
        self.assertEqual(schema.relationships[0].type, 'knows')
        self.assertEqual(len(schema.relationship_patterns), 1)

    def test_neptune_analytics_path(self):
        client = MagicMock()
        config = MagicMock()
        config.neptune_service = 'neptune-graph'

        resp = MagicMock()
        resp.json.return_value = {
            'results': [{'schema': {
                'labelTriples': [{'~from': 'person', '~type': 'knows', '~to': 'person'}],
                'nodeLabels': ['person'],
                'nodeLabelDetails': {
                    'person': {'properties': {'name': {'datatypes': ['STRING']}, 'age': {'datatypes': ['INTEGER']}}}
                },
                'edgeLabels': ['knows'],
                'edgeLabelDetails': {
                    'knows': {'properties': {'weight': {'datatypes': ['DOUBLE']}}}
                },
            }}]
        }
        client.opencypher_http.return_value = resp

        schema = get_schema(client, config)
        self.assertIsInstance(schema, GraphSchema)
        self.assertEqual(len(schema.nodes), 1)
        self.assertEqual(len(schema.relationship_patterns), 1)

    def test_unsupported_service_raises(self):
        client = MagicMock()
        config = MagicMock()
        config.neptune_service = 'unknown-service'
        with self.assertRaises(NotImplementedError):
            get_schema(client, config)


class TestUriHelpers(unittest.TestCase):
    def test_local_name_hash(self):
        self.assertEqual(_uri_local_name('http://example.org/schema#Person'), 'Person')

    def test_local_name_slash(self):
        self.assertEqual(_uri_local_name('http://example.org/schema/Person'), 'Person')

    def test_local_name_no_separator(self):
        self.assertEqual(_uri_local_name('Person'), 'Person')

    def test_is_metadata_uri(self):
        self.assertTrue(_is_metadata_uri('http://www.w3.org/2000/01/rdf-schema#Class'))
        self.assertTrue(_is_metadata_uri('http://www.w3.org/2002/07/owl#Thing'))
        self.assertFalse(_is_metadata_uri('http://example.org/Person'))


if __name__ == '__main__':
    unittest.main()
