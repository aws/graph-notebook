"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest
from gremlin_python.structure.graph import Path, Edge, Vertex
from gremlin_python.process.traversal import T, Direction
from graph_notebook.network.EventfulNetwork import EVENT_ADD_NODE
from graph_notebook.network.gremlin.GremlinNetwork import GremlinNetwork


class TestGremlinNetwork(unittest.TestCase):
    def test_add_vertex_with_callback(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        reached_callback = {}
        expected_data = {
            'data': {
                'group': 'airport',
                'label': 'airport',
                'properties': {
                    T.id: '1234',
                    T.label: 'airport',
                    'code': 'SEA',
                    'runways': '4',
                    'type': 'Airport'},
                'title': 'airport'},
            'node_id': '1234'}

        def add_node_callback(network, event_name, data):
            self.assertEqual(event_name, EVENT_ADD_NODE)
            self.assertEqual(expected_data, data)
            reached_callback[event_name] = True

        gn = GremlinNetwork(callbacks={EVENT_ADD_NODE: [add_node_callback]})
        gn.add_vertex(vertex)
        self.assertTrue(reached_callback[EVENT_ADD_NODE])
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(expected_data['data']['properties'], node['properties'])

    def test_add_explicit_type_vertex_without_node_property(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork()
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['label'], 'vertex')
        self.assertEqual(node['title'], 'vertex')

    def test_add_explicit_type_vertex_with_invalid_node_property_label(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(display_property='foo')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['label'], 'vertex')
        self.assertEqual(node['title'], 'vertex')

    def test_add_explicit_type_vertex_with_node_property_label(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(display_property='label')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['label'], 'vertex')
        self.assertEqual(node['title'], 'vertex')

    def test_add_explicit_type_vertex_with_node_property_id(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(display_property='id')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['label'], '1')
        self.assertEqual(node['title'], '1')

    def test_add_explicit_type_vertex_with_node_property_json(self):
        vertex1 = Vertex(id='1')

        gn = GremlinNetwork(display_property='{"vertex":"id"}')
        gn.add_vertex(vertex1)
        node1 = gn.graph.nodes.get('1')
        self.assertEqual(node1['label'], '1')
        self.assertEqual(node1['title'], '1')

    def test_add_explicit_type_vertex_with_node_property_json_invalid_json(self):
        vertex1 = Vertex(id='1')

        gn = GremlinNetwork(display_property='{"vertex":id}')
        gn.add_vertex(vertex1)
        node1 = gn.graph.nodes.get('1')
        self.assertEqual(node1['label'], 'vertex')
        self.assertEqual(node1['title'], 'vertex')

    def test_add_explicit_type_vertex_with_node_property_json_invalid_key(self):
        vertex1 = Vertex(id='1')

        gn = GremlinNetwork(display_property='{"foo":"id"}')
        gn.add_vertex(vertex1)
        node1 = gn.graph.nodes.get('1')
        self.assertEqual(node1['label'], 'vertex')
        self.assertEqual(node1['title'], 'vertex')

    def test_add_explicit_type_vertex_with_node_property_json_invalid_value(self):
        vertex1 = Vertex(id='1')

        gn = GremlinNetwork(display_property='{"vertex":"code"}')
        gn.add_vertex(vertex1)
        node1 = gn.graph.nodes.get('1')
        self.assertEqual(node1['label'], 'vertex')
        self.assertEqual(node1['title'], 'vertex')

    def test_add_explicit_type_multiple_vertex_with_node_property_string(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        gn = GremlinNetwork(display_property='id')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get('1')
        node2 = gn.graph.nodes.get('2')
        self.assertEqual(node1['label'], '1')
        self.assertEqual(node1['title'], '1')
        self.assertEqual(node2['label'], '2')
        self.assertEqual(node2['title'], '2')

    def test_add_explicit_type_multiple_vertex_with_node_property_json(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        gn = GremlinNetwork(display_property='{"vertex":"id"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get('1')
        node2 = gn.graph.nodes.get('2')
        self.assertEqual(node1['label'], '1')
        self.assertEqual(node1['title'], '1')
        self.assertEqual(node2['label'], '2')
        self.assertEqual(node2['title'], '2')

    def test_add_vertex_without_node_property(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork()
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'airport')
        self.assertEqual(node['title'], 'airport')

    def test_add_vertex_with_node_property_string(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(display_property='code')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'SEA')
        self.assertEqual(node['title'], 'SEA')

    def test_add_vertex_with_node_property_string_invalid(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(display_property='desc')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'airport')
        self.assertEqual(node['title'], 'airport')

    def test_add_vertex_with_node_property_json(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(display_property='{"airport":"code"}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'SEA')
        self.assertEqual(node['title'], 'SEA')

    def test_add_vertex_with_node_property_json_invalid_json(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(display_property='{"airport":code}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'airport')
        self.assertEqual(node['title'], 'airport')

    def test_add_vertex_with_node_property_json_invalid_key(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(display_property='{"country":"code"}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'airport')
        self.assertEqual(node['title'], 'airport')

    def test_add_vertex_with_node_property_json_invalid_value(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(display_property='{"airport":"desc"}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'airport')
        self.assertEqual(node['title'], 'airport')

    def test_add_vertex_multiple_with_node_property_string(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        vertex2 = {
            T.id: '2345',
            T.label: 'country',
            'type': 'Country',
            'continent': 'NA',
            'code': 'USA'
        }

        gn = GremlinNetwork(display_property='code')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['label'], 'SEA')
        self.assertEqual(node1['title'], 'SEA')
        self.assertEqual(node2['label'], 'USA')
        self.assertEqual(node2['title'], 'USA')

    def test_add_vertex_multiple_with_multiple_node_properties(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        vertex2 = {
            T.id: '2345',
            T.label: 'country',
            'type': 'Country',
            'continent': 'NA',
            'code': 'USA'
        }

        gn = GremlinNetwork(display_property='{"airport":"code","country":"continent"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['label'], 'SEA')
        self.assertEqual(node1['title'], 'SEA')
        self.assertEqual(node2['label'], 'NA')
        self.assertEqual(node2['title'], 'NA')

    def test_add_vertex_with_label_length(self):
        vertex = {
            T.id: '1234',
            T.label: 'Seattle-Tacoma International Airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(label_max_length=15)
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'Seattle-Taco...')
        self.assertEqual(node['title'], 'Seattle-Tacoma International Airport')

    def test_add_vertex_with_bracketed_label_and_label_length(self):
        vertex = {
            T.id: '1234',
            T.label: "['Seattle-Tacoma International Airport']",
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(label_max_length=15)
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'Seattle-Taco...')
        self.assertEqual(node['title'], 'Seattle-Tacoma International Airport')

    def test_add_vertex_with_label_length_less_than_3(self):
        vertex = {
            T.id: '1234',
            T.label: 'Seattle-Tacoma International Airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(label_max_length=-50)
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], '...')
        self.assertEqual(node['title'], 'Seattle-Tacoma International Airport')

    def test_add_vertex_with_node_property_string_and_label_length(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA',
            'desc': 'Seattle-Tacoma International Airport'
        }

        gn = GremlinNetwork(display_property='{"airport":"desc"}', label_max_length=15)
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'Seattle-Taco...')
        self.assertEqual(node['title'], 'Seattle-Tacoma International Airport')

    def test_add_vertex_with_node_property_json_and_label_length(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA',
            'desc': 'Seattle-Tacoma International Airport'
        }

        gn = GremlinNetwork(display_property='desc', label_max_length=15)
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['label'], 'Seattle-Taco...')
        self.assertEqual(node['title'], 'Seattle-Tacoma International Airport')

    def test_add_explicit_type_single_edge_without_edge_property(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='route')

        gn = GremlinNetwork()
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_explicit_type_single_edge_with_invalid_edge_property(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='route')

        gn = GremlinNetwork(edge_display_property='length')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_explicit_type_single_edge_with_edge_property_string_label(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='route')

        gn = GremlinNetwork(edge_display_property='label')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_explicit_type_single_edge_with_edge_property_string_id(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='route')

        gn = GremlinNetwork(edge_display_property='id')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], '1')

    def test_add_explicit_type_single_edge_with_edge_property_json_single_label(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='route')

        gn = GremlinNetwork(edge_display_property='{"route":"inV"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'v[2]')

    def test_add_explicit_type_single_edge_with_edge_property_malformed_json_single_label(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='route')

        gn = GremlinNetwork(edge_display_property='{"route":inV}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_explicit_type_single_edge_with_edge_property_json_invalid_key_single_label(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='route')

        gn = GremlinNetwork(edge_display_property='{"road":"inV"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_explicit_type_single_edge_with_edge_property_json_invalid_value_single_label(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='route')

        gn = GremlinNetwork(edge_display_property='{"route":"distance"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_explicit_type_multiple_edges_with_edge_property_string(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')
        vertex3 = Vertex(id='3')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='airway')
        edge2 = Edge(id='2', outV=vertex2, inV=vertex3, label='road')

        gn = GremlinNetwork(edge_display_property='id')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        gn.add_path_edge(edge2)
        edge_route = gn.graph.get_edge_data('1', '2')
        edge_path = gn.graph.get_edge_data('2', '3')
        self.assertEqual(edge_route['1']['label'], '1')
        self.assertEqual(edge_path['2']['label'], '2')

    def test_add_explicit_type_multiple_edges_with_edge_property_json_single_label(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')
        vertex3 = Vertex(id='3')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='route')
        edge2 = Edge(id='2', outV=vertex2, inV=vertex3, label='route')

        gn = GremlinNetwork(edge_display_property='{"route":"inV"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        gn.add_path_edge(edge2)
        edge_route = gn.graph.get_edge_data('1', '2')
        edge_path = gn.graph.get_edge_data('2', '3')
        self.assertEqual(edge_route['1']['label'], 'v[2]')
        self.assertEqual(edge_path['2']['label'], 'v[3]')

    def test_add_explicit_type_multiple_edges_with_edge_property_json_multiple_labels(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')
        vertex3 = Vertex(id='3')

        edge1 = Edge(id='1', outV=vertex1, inV=vertex2, label='airway')
        edge2 = Edge(id='2', outV=vertex2, inV=vertex3, label='road')

        gn = GremlinNetwork(edge_display_property='{"airway":"inV","road":"id"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1)
        gn.add_path_edge(edge2)
        edge_route = gn.graph.get_edge_data('1', '2')
        edge_path = gn.graph.get_edge_data('2', '3')
        self.assertEqual(edge_route['1']['label'], 'v[2]')
        self.assertEqual(edge_path['2']['label'], '2')

    def test_add_single_edge_without_edge_property(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}

        gn = GremlinNetwork()
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_single_edge_with_invalid_edge_property(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}

        gn = GremlinNetwork(edge_display_property='distance')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_single_edge_with_edge_property_string_label(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}

        gn = GremlinNetwork(edge_display_property='T.label')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_single_edge_with_edge_property_string_id(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}

        gn = GremlinNetwork(edge_display_property='T.id')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], '1')

    def test_add_single_edge_with_edge_property_json(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}

        gn = GremlinNetwork(edge_display_property='{"route":"inV"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'v[2]')

    def test_add_single_edge_with_edge_property_invalid_json(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}

        gn = GremlinNetwork(edge_display_property='{"route":inV}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_single_edge_with_edge_property_json_invalid_key(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}

        gn = GremlinNetwork(edge_display_property='{"distance":"inV"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_single_edge_with_edge_property_json_invalid_value(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}

        gn = GremlinNetwork(edge_display_property='{"route":"foo"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], 'route')

    def test_add_multiple_edges_with_edge_property_string(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}
        edge2 = {T.id: '2', T.label: 'route', 'outV': 'v[2]', 'inV': 'v[3]'}

        gn = GremlinNetwork(edge_display_property='inV')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        gn.add_path_edge(edge2, from_id='2', to_id='3')
        edge1_data = gn.graph.get_edge_data('1', '2')
        edge2_data = gn.graph.get_edge_data('2', '3')
        self.assertEqual(edge1_data['1']['label'], 'v[2]')
        self.assertEqual(edge2_data['2']['label'], 'v[3]')

    def test_add_multiple_edges_with_edge_property_json_single_label(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'route', 'outV': 'v[1]', 'inV': 'v[2]'}
        edge2 = {T.id: '2', T.label: 'route', 'outV': 'v[2]', 'inV': 'v[3]'}

        gn = GremlinNetwork(edge_display_property='{"route":"inV"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        gn.add_path_edge(edge2, from_id='2', to_id='3')
        edge1_data = gn.graph.get_edge_data('1', '2')
        edge2_data = gn.graph.get_edge_data('2', '3')
        self.assertEqual(edge1_data['1']['label'], 'v[2]')
        self.assertEqual(edge2_data['2']['label'], 'v[3]')

    def test_add_multiple_edges_with_edge_property_json_multiple_labels(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')

        edge1 = {T.id: '1', T.label: 'airway', 'outV': 'v[1]', 'inV': 'v[2]'}
        edge2 = {T.id: '2', T.label: 'road', 'outV': 'v[2]', 'inV': 'v[3]'}

        gn = GremlinNetwork(edge_display_property='{"airway":"outV","road":"T.id"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        gn.add_path_edge(edge1, from_id='1', to_id='2')
        gn.add_path_edge(edge2, from_id='2', to_id='3')
        edge1_data = gn.graph.get_edge_data('1', '2')
        edge2_data = gn.graph.get_edge_data('2', '3')
        self.assertEqual(edge1_data['1']['label'], 'v[1]')
        self.assertEqual(edge2_data['2']['label'], '2')

    def test_add_path_with_integer(self):
        path = Path([], ['ANC', 3030, 'DFW'])
        gn = GremlinNetwork()
        gn.add_results([path])
        self.assertEqual(len(path), len(gn.graph.nodes))

    def test_group_with_groupby(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(group_by_property='code')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], 'SEA')

    def test_group_with_groupby_multiple_labels_with_same_property(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'name': 'Seattle-Tacoma International Airport',
            'runways': '4',
            'code': 'SEA'
        }

        vertex2 = {
            T.id: '2345',
            T.label: 'country',
            'type': 'Country',
            'name': 'Austria',
            'continent': 'Europe',
        }

        gn = GremlinNetwork(group_by_property='name')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], 'Seattle-Tacoma International Airport')
        self.assertEqual(node2['group'], 'Austria')

    def test_group_with_groupby_properties_json_single_label(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(group_by_property='{"airport":"code"}')
        gn.add_vertex(vertex1)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        self.assertEqual(node1['group'], 'SEA')

    def test_group_with_groupby_properties_json_multiple_labels(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        vertex2 = {
            T.id: '2345',
            T.label: 'country',
            'type': 'Country',
            'name': 'Austria',
            'continent': 'Europe'
        }

        gn = GremlinNetwork(group_by_property='{"airport":"code","country":"continent"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], 'SEA')
        self.assertEqual(node2['group'], 'Europe')

    def test_group_with_groupby_invalid_json_single_label(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(group_by_property='{"airport":{"code"}}')
        gn.add_vertex(vertex1)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        self.assertEqual(node1['group'], '')

    def test_group_with_groupby_invalid_json_multiple_labels(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        vertex2 = {
            T.id: '2345',
            T.label: 'country',
            'type': 'Country',
            'name': 'Austria',
            'continent': 'Europe'
        }

        gn = GremlinNetwork(group_by_property='{"airport":{"code"},"country":{"groupby":"continent"}}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], '')
        self.assertEqual(node2['group'], '')

    def test_group_nonexistent_groupby(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(group_by_property='foo')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], '')

    def test_group_nonexistent_groupby_properties_json_single_label(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(group_by_property='{"airport":{"groupby":"foo"}}')
        gn.add_vertex(vertex1)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        self.assertEqual(node1['group'], '')

    def test_group_nonexistent_groupby_properties_json_multiple_labels(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        vertex2 = {
            T.id: '2345',
            T.label: 'country',
            'type': 'Country',
            'name': 'Austria',
            'continent': 'Europe'
        }

        gn = GremlinNetwork(group_by_property='{"airport":"foo","country":"continent"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], '')
        self.assertEqual(node2['group'], 'Europe')

    def test_group_nonexistent_label_properties_json_single_label(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(group_by_property='{"air_port":{"groupby":"code"}')
        gn.add_vertex(vertex1)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        self.assertEqual(node1['group'], '')

    def test_group_nonexistent_label_properties_json_multiple_labels(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        vertex2 = {
            T.id: '2345',
            T.label: 'country',
            'type': 'Country',
            'name': 'Austria',
            'continent': 'Europe'
        }

        gn = GremlinNetwork(group_by_property='{"airport":"code","a_country":"continent"}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], 'SEA')
        self.assertEqual(node2['group'], '')

    def test_group_without_groupby(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork()
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], 'airport')

    def test_group_without_groupby_multiple_labels(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        vertex2 = {
            T.id: '2345',
            T.label: 'country',
            'type': 'Country',
            'name': 'Austria',
            'continent': 'Europe'
        }

        gn = GremlinNetwork()
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], 'airport')
        self.assertEqual(node2['group'], 'country')

    def test_group_valueMap_true(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork()
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], 'airport')

    def test_group_without_groupby_list(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'code': ['SEA']
        }

        gn = GremlinNetwork()
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], 'airport')

    def test_group_without_groupby_choose_label(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'code': ['SEA']
        }

        gn = GremlinNetwork(group_by_property='T.label')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], 'airport')

    def test_group_with_groupby_list(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'code': ['SEA']
        }

        gn = GremlinNetwork(group_by_property='code')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], "['SEA']")

    def test_group_with_groupby_list_properties_json(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'code': ['SEA']
        }

        gn = GremlinNetwork(group_by_property='{"airport":"code"}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], "['SEA']")

    def test_group_notokens_groupby(self):
        vertex = {
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(group_by_property='code')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('graph_notebook-ed8fddedf251d3d5745dccfd53edf51d')
        self.assertEqual(node['group'], 'SEA')

    def test_group_notokens_without_groupby(self):
        vertex = {
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork()
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('graph_notebook-ed8fddedf251d3d5745dccfd53edf51d')
        self.assertEqual(node['group'], '')

    def test_add_path_with_edge_property_string(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')
        path = Path([], [vertex1, Edge(id='1', outV=vertex1, inV=vertex2, label='route'), vertex2])
        gn = GremlinNetwork(edge_display_property='id')
        gn.add_results([path])
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], '1')

    def test_add_path_with_edge_property_json(self):
        vertex1 = Vertex(id='1')
        vertex2 = Vertex(id='2')
        path = Path([], [vertex1, Edge(id='1', outV=vertex1, inV=vertex2, label='route'), vertex2])
        gn = GremlinNetwork(edge_display_property='{"route":"id"}')
        gn.add_results([path])
        edge = gn.graph.get_edge_data('1', '2')
        self.assertEqual(edge['1']['label'], '1')

    def test_add_path_without_groupby(self):
        path = Path([], [{'country': ['US'], 'code': ['SEA'], 'longest': [11901], 'city': ['Seattle'],
                          T.label: 'airport', 'lon': [-122.30899810791], 'type': ['airport'], 'elev': [432],
                          T.id: '22', 'icao': ['KSEA'], 'runways': [3], 'region': ['US-WA'],
                          'lat': [47.4490013122559], 'desc': ['Seattle-Tacoma']},
                         {'country': ['US'], 'code': ['ATL'], 'longest': [12390], 'city': ['Atlanta'],
                          T.label: 'airport', 'lon': [-84.4281005859375], 'type': ['airport'], 'elev': [1026],
                          T.id: '1', 'icao': ['KATL'], 'runways': [5], 'region': ['US-GA'],
                          'lat': [33.6366996765137], 'desc': ['Hartsfield - Jackson Atlanta International Airport']}])
        gn = GremlinNetwork()
        gn.add_results([path])
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], "airport")

    def test_add_path_with_groupby(self):
        path = Path([], [{'country': ['US'], 'code': ['SEA'], 'longest': [11901], 'city': ['Seattle'],
                          T.label: 'airport', 'lon': [-122.30899810791], 'type': ['airport'], 'elev': [432],
                          T.id: '22', 'icao': ['KSEA'], 'runways': [3], 'region': ['US-WA'],
                          'lat': [47.4490013122559], 'desc': ['Seattle-Tacoma']},
                         {'country': ['US'], 'code': ['ATL'], 'longest': [12390], 'city': ['Atlanta'],
                          T.label: 'airport', 'lon': [-84.4281005859375], 'type': ['airport'], 'elev': [1026],
                          T.id: '1', 'icao': ['KATL'], 'runways': [5], 'region': ['US-GA'],
                          'lat': [33.6366996765137], 'desc': ['Hartsfield - Jackson Atlanta International Airport']}])
        gn = GremlinNetwork(group_by_property="code")
        gn.add_results([path])
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], "['ATL']")

    def test_add_path_with_groupby_multiple_labels(self):
        path = Path([], [{'country': ['US'], 'code': ['SEA'], 'longest': [11901], 'city': ['Seattle'],
                          T.label: 'airport', 'lon': [-122.30899810791], 'type': ['airport'], 'elev': [432],
                          T.id: '22', 'icao': ['KSEA'], 'runways': [3], 'region': ['US-WA'],
                          'lat': [47.4490013122559], 'desc': ['Seattle-Tacoma']},
                         {'country': ['US'], 'code': ['ATL'], 'longest': [12390], 'city': ['Atlanta'],
                          T.label: 'airport', 'lon': [-84.4281005859375], 'type': ['airport'], 'elev': [1026],
                          T.id: '1', 'icao': ['KATL'], 'runways': [5], 'region': ['US-GA'],
                          'lat': [33.6366996765137], 'desc': ['Hartsfield - Jackson Atlanta International Airport']},
                         {'code': ['AN'], T.label: 'continent', T.id: '3741', 'desc': ['Antarctica']}])
        gn = GremlinNetwork(group_by_property='code')
        gn.add_results([path])
        node1 = gn.graph.nodes.get('1')
        node2 = gn.graph.nodes.get('3741')
        self.assertEqual(node1['group'], "['ATL']")
        self.assertEqual(node2['group'], "['AN']")

    def test_add_path_with_groupby_properties_json(self):
        path = Path([], [{'country': ['US'], 'code': ['SEA'], 'longest': [11901], 'city': ['Seattle'],
                          T.label: 'airport', 'lon': [-122.30899810791], 'type': ['airport'], 'elev': [432],
                          T.id: '22', 'icao': ['KSEA'], 'runways': [3], 'region': ['US-WA'],
                          'lat': [47.4490013122559], 'desc': ['Seattle-Tacoma']},
                         {'country': ['US'], 'code': ['ATL'], 'longest': [12390], 'city': ['Atlanta'],
                          T.label: 'airport', 'lon': [-84.4281005859375], 'type': ['airport'], 'elev': [1026],
                          T.id: '1', 'icao': ['KATL'], 'runways': [5], 'region': ['US-GA'],
                          'lat': [33.6366996765137], 'desc': ['Hartsfield - Jackson Atlanta International Airport']}])
        gn = GremlinNetwork(group_by_property='{"airport":"code"}')
        gn.add_results([path])
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], "['ATL']")

    def test_add_path_with_groupby_properties_json_multiple_labels(self):
        path = Path([], [{'country': ['US'], 'code': ['SEA'], 'longest': [11901], 'city': ['Seattle'],
                          T.label: 'airport', 'lon': [-122.30899810791], 'type': ['airport'], 'elev': [432],
                          T.id: '22', 'icao': ['KSEA'], 'runways': [3], 'region': ['US-WA'],
                          'lat': [47.4490013122559], 'desc': ['Seattle-Tacoma']},
                         {'country': ['US'], 'code': ['ATL'], 'longest': [12390], 'city': ['Atlanta'],
                          T.label: 'airport', 'lon': [-84.4281005859375], 'type': ['airport'], 'elev': [1026],
                          T.id: '1', 'icao': ['KATL'], 'runways': [5], 'region': ['US-GA'],
                          'lat': [33.6366996765137], 'desc': ['Hartsfield - Jackson Atlanta International Airport']},
                         {'code': ['AN'], T.label: 'continent', T.id: '3741', 'desc': ['Antarctica']}])
        gn = GremlinNetwork(group_by_property='{"airport":"region","continent":"code"}')
        gn.add_results([path])
        node1 = gn.graph.nodes.get('1')
        node2 = gn.graph.nodes.get('3741')
        self.assertEqual(node1['group'], "['US-GA']")
        self.assertEqual(node2['group'], "['AN']")

    def test_ignore_group(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        gn = GremlinNetwork(ignore_groups=True)
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], '')

        gn = GremlinNetwork(group_by_property="code", ignore_groups=True)
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], '')

    def test_ignore_group_properties_json(self):
        vertex1 = {
            T.id: '1234',
            T.label: 'airport',
            'type': 'Airport',
            'runways': '4',
            'code': 'SEA'
        }

        vertex2 = {
            T.id: '2345',
            T.label: 'country',
            'type': 'Country',
            'name': 'Austria',
            'continent': 'Europe'
        }

        gn = GremlinNetwork(ignore_groups=True)
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], '')
        self.assertEqual(node2['group'], '')

        gn = GremlinNetwork(group_by_property='{"airport":"code","country":"continent"}',
                            ignore_groups=True)
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], '')
        self.assertEqual(node2['group'], '')

    def test_group_returnvertex_groupby_notspecified(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork()
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], 'vertex')

    def test_group_returnvertex_groupby_label(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(group_by_property="label")
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], 'vertex')

        gn = GremlinNetwork(group_by_property="T.label")
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], 'vertex')

    def test_group_returnvertex_groupby_label_properties_json(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(group_by_property='{"vertex":"label"}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], 'vertex')

        gn = GremlinNetwork(group_by_property='{"vertex":"T.label"}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], 'vertex')

    def test_group_returnvertex_groupby_id(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(group_by_property="id")
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], '1')

        gn = GremlinNetwork(group_by_property="T.id")
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], '1')

    def test_group_returnvertex_groupby_id_properties_json(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(group_by_property='{"vertex":"id"}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], '1')

        gn = GremlinNetwork(group_by_property='{"vertex":"T.id"}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], '1')

    def test_add_elementmap_edge(self):
        edge_map = {
            T.id: '5298',
            T.label: 'route',
            Direction.IN: {T.id: '1112', T.label: 'airport'},
            Direction.OUT: {T.id: '2', T.label: 'airport'},
            'dist': 763
        }

        edge_expected = {
            '5298': {
                'properties': {
                    T.id: '5298',
                    T.label: 'route',
                    Direction.IN: '1112',
                    Direction.OUT: '2',
                    'dist': 763
                },
                'label': 'route'
            }
        }

        gn = GremlinNetwork()
        gn.insert_elementmap(edge_map)
        edge_data = gn.graph.get_edge_data('2', '1112')
        inv_data = gn.graph.nodes.get('1112')
        outv_data = gn.graph.nodes.get('2')
        self.assertEqual(edge_data, edge_expected)
        self.assertEqual(inv_data['properties'], edge_map[Direction.IN])
        self.assertEqual(outv_data['properties'], edge_map[Direction.OUT])

    def test_add_elementmap_vertex(self):
        vertex = {
            T.id: '2',
            T.label: 'airport',
            'code': 'ANC',
            'type': 'airport',
            'desc': 'Anchorage Ted Stevens',
            'country': 'US', 'longest': 12400,
            'city': 'Anchorage',
            'lon': -149.996002197266,
            'elev': 151,
            'icao': 'PANC',
            'region': 'US-AK',
            'runways': 3,
            'lat': 61.1744003295898
        }

        gn = GremlinNetwork()
        gn.insert_elementmap(vertex)
        vertex_data = gn.graph.nodes.get('2')
        self.assertEqual(vertex_data['properties'], vertex)

    def test_add_elementmap_edge_with_existing_full_vertices(self):
        # Test case where a full elementmap vertex has already been inserted into the graph
        # Afterwards, inserting an elementmap edge connected to the same vertex should not overwrite the old vertex
        edge_map = {
            T.id: '5298',
            T.label: 'route',
            Direction.IN: {T.id: '1112', T.label: 'airport'},
            Direction.OUT: {T.id: '2', T.label: 'airport'},
            'dist': 763
        }

        out_vertex = {
            T.id: '2',
            T.label: 'airport',
            'code': 'ANC',
            'type': 'airport',
            'desc': 'Anchorage Ted Stevens',
            'country': 'US', 'longest': 12400,
            'city': 'Anchorage',
            'lon': -149.996002197266,
            'elev': 151,
            'icao': 'PANC',
            'region': 'US-AK',
            'runways': 3,
            'lat': 61.1744003295898
        }

        in_vertex = {
            T.id: '1112',
            T.label: 'airport',
            'code': 'SNP',
            'type': 'airport',
            'desc': 'St Paul Island Airport',
            'country': 'US',
            'longest': 6500,
            'city': 'St Paul Island',
            'lon': -170.220001220703,
            'elev': 63,
            'icao': 'PASN',
            'region': 'US-AK',
            'runways': 1,
            'lat': 57.1673011779785
        }

        gn = GremlinNetwork()
        gn.insert_elementmap(in_vertex)
        gn.insert_elementmap(out_vertex)
        gn.insert_elementmap(edge_map)
        outv_data = gn.graph.nodes.get('2')
        inv_data = gn.graph.nodes.get('1112')
        self.assertEqual(outv_data['properties'], out_vertex)
        self.assertEqual(inv_data['properties'], in_vertex)

    def test_add_elementmap_vertex_with_existing_basic_vertices(self):
        # Test case where an edge elementmap has already inserted a minimal inVertex and outVertex into the graph
        # Inserting the full vertex afterwards should overwrite the old inVertex or outVertex
        edge_map = {
            T.id: '5298',
            T.label: 'route',
            Direction.IN: {T.id: '1112', T.label: 'airport'},
            Direction.OUT: {T.id: '2', T.label: 'airport'},
            'dist': 763
        }

        vertex = {
            T.id: '2',
            T.label: 'airport',
            'code': 'ANC',
            'type': 'airport',
            'desc': 'Anchorage Ted Stevens',
            'country': 'US', 'longest': 12400,
            'city': 'Anchorage',
            'lon': -149.996002197266,
            'elev': 151,
            'icao': 'PANC',
            'region': 'US-AK',
            'runways': 3,
            'lat': 61.1744003295898
        }

        gn = GremlinNetwork()
        gn.insert_elementmap(edge_map)
        outv_data_orig = gn.graph.nodes.get('2')
        self.assertEqual(outv_data_orig['properties'], edge_map[Direction.OUT])

        gn.insert_elementmap(vertex)
        outv_data_final = gn.graph.nodes.get('2')
        self.assertEqual(outv_data_final['properties'], vertex)

    def test_add_results_as_list_of_elementmaps(self):
        edge_map = {
            T.id: '5298',
            T.label: 'route',
            Direction.IN: {T.id: '1112', T.label: 'airport'},
            Direction.OUT: {T.id: '2', T.label: 'airport'},
            'dist': 763
        }

        out_vertex = {
            T.id: '2',
            T.label: 'airport',
            'code': 'ANC',
            'type': 'airport',
            'desc': 'Anchorage Ted Stevens',
            'country': 'US', 'longest': 12400,
            'city': 'Anchorage',
            'lon': -149.996002197266,
            'elev': 151,
            'icao': 'PANC',
            'region': 'US-AK',
            'runways': 3,
            'lat': 61.1744003295898
        }

        in_vertex = {
            T.id: '1112',
            T.label: 'airport',
            'code': 'SNP',
            'type': 'airport',
            'desc': 'St Paul Island Airport',
            'country': 'US',
            'longest': 6500,
            'city': 'St Paul Island',
            'lon': -170.220001220703,
            'elev': 63,
            'icao': 'PASN',
            'region': 'US-AK',
            'runways': 1,
            'lat': 57.1673011779785
        }

        edge_expected = {
            '5298': {
                'properties': {
                    T.id: '5298',
                    T.label: 'route',
                    Direction.IN: '1112',
                    Direction.OUT: '2',
                    'dist': 763
                },
                'label': 'route'
            }
        }

        results = [edge_map, out_vertex, in_vertex]

        gn = GremlinNetwork()
        gn.add_results(results)
        edge_data = gn.graph.get_edge_data('2', '1112')
        outv_data = gn.graph.nodes.get('2')
        inv_data = gn.graph.nodes.get('1112')
        self.assertEqual(outv_data['properties'], out_vertex)
        self.assertEqual(inv_data['properties'], in_vertex)
        self.assertEqual(edge_data, edge_expected)

    def test_add_results_as_list_of_non_elementmap_dicts(self):

        results = [{"vertex1": 1}, {"vertex2": 2}, {"vertex3": 3}]

        gn = GremlinNetwork()
        with self.assertRaises(ValueError):
            gn.add_results(results)

    def test_add_results_as_path_containing_elementmaps(self):
        edge_map = {
            T.id: '5298',
            T.label: 'route',
            Direction.IN: {T.id: '1112', T.label: 'airport'},
            Direction.OUT: {T.id: '2', T.label: 'airport'},
            'dist': 763
        }

        out_vertex = {
            T.id: '2',
            T.label: 'airport',
            'code': 'ANC',
            'type': 'airport',
            'desc': 'Anchorage Ted Stevens',
            'country': 'US', 'longest': 12400,
            'city': 'Anchorage',
            'lon': -149.996002197266,
            'elev': 151,
            'icao': 'PANC',
            'region': 'US-AK',
            'runways': 3,
            'lat': 61.1744003295898
        }

        in_vertex = {
            T.id: '1112',
            T.label: 'airport',
            'code': 'SNP',
            'type': 'airport',
            'desc': 'St Paul Island Airport',
            'country': 'US',
            'longest': 6500,
            'city': 'St Paul Island',
            'lon': -170.220001220703,
            'elev': 63,
            'icao': 'PASN',
            'region': 'US-AK',
            'runways': 1,
            'lat': 57.1673011779785
        }

        edge_expected = {
            '5298': {
                'properties': {
                    T.id: '5298',
                    T.label: 'route',
                    Direction.IN: '1112',
                    Direction.OUT: '2',
                    'dist': 763
                },
                'label': 'route'
            }
        }

        path = Path([], [edge_map, out_vertex, in_vertex])
        gn = GremlinNetwork()
        gn.add_results([path])
        edge_data = gn.graph.get_edge_data('2', '1112')
        outv_data = gn.graph.nodes.get('2')
        inv_data = gn.graph.nodes.get('1112')
        self.assertEqual(outv_data['properties'], out_vertex)
        self.assertEqual(inv_data['properties'], in_vertex)
        self.assertEqual(edge_data, edge_expected)

    def test_add_results_as_path_containing_valuemaps(self):

        out_vertex = {
            'country': ['US'],
            'code': ['SAF'],
            'longest': [8366],
            'city': ['Santa Fe'],
            'lon': [-106.088996887],
            'type': ['airport'],
            T.id: '44', 'elev': [6348],
            T.label: 'airport',
            'icao': ['KSAF'],
            'runways': [3],
            'region': ['US-NM'],
            'lat': [35.617099762],
            'desc': ['Santa Fe']
        }

        in_vertex = {
            'country': ['US'],
            'code': ['DFW'],
            'longest': [13401],
            'city': ['Dallas'],
            'lon': [-97.0380020141602],
            'type': ['airport'],
            T.id: '8',
            'elev': [607],
            T.label: 'airport',
            'icao': ['KDFW'],
            'runways': [7],
            'region': ['US-TX'],
            'lat': [32.896800994873],
            'desc': ['Dallas/Fort Worth International Airport']
        }

        edge_value_expected = {
            'arrows': {
                'to': {
                    'enabled': False
                }
            },
            'label': ''
        }

        path = Path([], [out_vertex, in_vertex])
        gn = GremlinNetwork()
        gn.add_results([path])
        edge_data = gn.graph.get_edge_data('44', '8')
        for prop, value in edge_data.items():
            edge_data_value = value
            break
        outv_data = gn.graph.nodes.get('44')
        inv_data = gn.graph.nodes.get('8')
        self.assertEqual(outv_data['properties'], out_vertex)
        self.assertEqual(inv_data['properties'], in_vertex)
        self.assertEqual(edge_data_value, edge_value_expected)


if __name__ == '__main__':
    unittest.main()
