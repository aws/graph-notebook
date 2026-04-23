"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest
from graph_notebook.schema_model import Property, Node, Relationship, RelationshipPattern, GraphSchema
from graph_notebook.network.opencypher.OCNetwork import OCNetwork


class TestCreateSchemaNetwork(unittest.TestCase):
    def _make_schema(self, nodes=None, relationships=None, patterns=None):
        return GraphSchema(
            nodes=nodes or [],
            relationships=relationships or [],
            relationship_patterns=patterns or [],
        )

    def test_adds_nodes(self):
        schema = self._make_schema(
            nodes=[
                Node(labels='person', properties=[Property(name='name', type=['STRING'])]),
                Node(labels='software', properties=[Property(name='lang', type=['STRING'])]),
            ]
        )
        gn = OCNetwork(group_by_property='~label')
        gn.create_schema_network(schema)
        self.assertEqual(len(gn.graph.nodes), 2)
        self.assertIn('person', gn.graph.nodes)
        self.assertIn('software', gn.graph.nodes)

    def test_node_properties_in_data(self):
        schema = self._make_schema(
            nodes=[Node(labels='person', properties=[
                Property(name='name', type=['STRING']),
                Property(name='age', type=['INTEGER']),
            ])]
        )
        gn = OCNetwork(group_by_property='~label')
        gn.create_schema_network(schema)
        node = gn.graph.nodes['person']
        self.assertIn('name', node['properties'])
        self.assertIn('age', node['properties'])
        self.assertEqual(node['properties']['~label'], 'person')

    def test_adds_edges(self):
        schema = self._make_schema(
            nodes=[
                Node(labels='person'),
                Node(labels='software'),
            ],
            relationships=[
                Relationship(type='created', properties=[Property(name='weight', type=['DOUBLE'])]),
            ],
            patterns=[
                RelationshipPattern(left_node='person', right_node='software', relation='created'),
            ],
        )
        gn = OCNetwork(group_by_property='~label')
        gn.create_schema_network(schema)
        self.assertEqual(len(gn.graph.edges), 1)
        edges = list(gn.graph.edges(data=True))
        self.assertEqual(edges[0][0], 'person')
        self.assertEqual(edges[0][1], 'software')

    def test_edge_properties_in_data(self):
        schema = self._make_schema(
            nodes=[Node(labels='person')],
            relationships=[
                Relationship(type='knows', properties=[Property(name='since', type=['INTEGER'])]),
            ],
            patterns=[
                RelationshipPattern(left_node='person', right_node='person', relation='knows'),
            ],
        )
        gn = OCNetwork(group_by_property='~label')
        gn.create_schema_network(schema)
        edges = list(gn.graph.edges(data=True))
        self.assertIn('since', edges[0][2]['properties'])
        self.assertEqual(edges[0][2]['properties']['~label'], 'knows')

    def test_missing_relationship_no_crash(self):
        """If a pattern references a relation type not in relationships, should not crash."""
        schema = self._make_schema(
            nodes=[Node(labels='a'), Node(labels='b')],
            relationships=[],
            patterns=[
                RelationshipPattern(left_node='a', right_node='b', relation='missing'),
            ],
        )
        gn = OCNetwork(group_by_property='~label')
        gn.create_schema_network(schema)
        self.assertEqual(len(gn.graph.edges), 1)
        edges = list(gn.graph.edges(data=True))
        self.assertEqual(edges[0][2]['properties']['~label'], 'missing')

    def test_empty_schema(self):
        schema = self._make_schema()
        gn = OCNetwork(group_by_property='~label')
        gn.create_schema_network(schema)
        self.assertEqual(len(gn.graph.nodes), 0)
        self.assertEqual(len(gn.graph.edges), 0)

    def test_self_referencing_edge(self):
        schema = self._make_schema(
            nodes=[Node(labels='person')],
            relationships=[Relationship(type='knows')],
            patterns=[
                RelationshipPattern(left_node='person', right_node='person', relation='knows'),
            ],
        )
        gn = OCNetwork(group_by_property='~label')
        gn.create_schema_network(schema)
        self.assertEqual(len(gn.graph.nodes), 1)
        self.assertEqual(len(gn.graph.edges), 1)

    def test_multiple_patterns_same_nodes(self):
        schema = self._make_schema(
            nodes=[Node(labels='person'), Node(labels='software')],
            relationships=[
                Relationship(type='created'),
                Relationship(type='reviewed'),
            ],
            patterns=[
                RelationshipPattern(left_node='person', right_node='software', relation='created'),
                RelationshipPattern(left_node='person', right_node='software', relation='reviewed'),
            ],
        )
        gn = OCNetwork(group_by_property='~label')
        gn.create_schema_network(schema)
        self.assertEqual(len(gn.graph.edges), 2)


if __name__ == '__main__':
    unittest.main()
