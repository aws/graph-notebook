"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from unittest import TestCase

from graph_notebook.network.EventfulNetwork import EventfulNetwork, EVENT_ADD_NODE, EVENT_ADD_NODE_PROPERTY, \
    EVENT_ADD_EDGE, EVENT_ADD_EDGE_DATA, EVENT_ADD_NODE_DATA


class TestEventfulNetwork(TestCase):
    def test_add_node_callback_dispatch(self):
        node_id = '1'
        node_data = {
            'foo': 'bar'
        }
        callbacks_reached = {}

        def add_node_callback(network, event_name, data):
            self.assertEqual(EVENT_ADD_NODE, event_name)
            self.assertEqual(data['node_id'], node_id)
            self.assertEqual(data['data'], node_data)
            self.assertEqual(type(network), EventfulNetwork)
            callbacks_reached[event_name] = True

        en = EventfulNetwork()
        en.register_callback(EVENT_ADD_NODE, add_node_callback)
        en.add_node(node_id, node_data)
        self.assertIsNotNone(en.graph.nodes.get(node_id))
        self.assertTrue(callbacks_reached[EVENT_ADD_NODE])

    def test_add_node_property_callback_dispatch(self):
        node_id = '1'
        property_key = 'foo'
        property_value = 'bar'
        callback_reached = {}

        def add_node_property_callback(network, event_name, data):
            self.assertEqual(EVENT_ADD_NODE_PROPERTY, event_name)
            expected_payload = {
                'node_id': node_id,
                'key': property_key,
                'value': property_value
            }
            self.assertEqual(data, expected_payload)
            self.assertEqual(type(network), EventfulNetwork)
            callback_reached[event_name] = True

        en = EventfulNetwork(callbacks={EVENT_ADD_NODE_PROPERTY: [add_node_property_callback]})
        en.add_node(node_id)
        en.add_node_property(node_id, property_key, property_value)
        self.assertTrue(callback_reached[EVENT_ADD_NODE_PROPERTY])

    def test_add_edge_callback_dispatched(self):
        from_id = '1'
        to_id = '2'
        edge_id = '1_to_2'
        edge_label = edge_id
        edge_data = dict()
        edge_data['foo'] = 'bar'

        callback_reached = {}

        def add_edge_callback(network, event_name, data):
            self.assertEqual(event_name, EVENT_ADD_EDGE)
            expected_payload = {
                'from_id': from_id,
                'to_id': to_id,
                'edge_id': edge_id,
                'label': edge_label,
                'title': edge_label,
                'data': edge_data
            }
            self.assertEqual(expected_payload, data)
            self.assertEqual(type(network), EventfulNetwork)
            callback_reached[event_name] = True

        en = EventfulNetwork(callbacks={EVENT_ADD_EDGE: [add_edge_callback]})
        en.add_node(from_id)
        en.add_node(to_id)
        en.add_edge(from_id=from_id, to_id=to_id, edge_id=edge_id, label=edge_label, title=edge_label, data=edge_data)
        self.assertTrue(callback_reached[EVENT_ADD_EDGE])

    def test_add_node_data_callback_dispatched(self):
        node_id = '1'
        node_data = {
            'foo': 'bar',
            'lorem': 'ipsum'
        }

        callback_reached = {}

        def add_node_data_callback(network, event_name, data):
            self.assertEqual(EVENT_ADD_NODE_DATA, event_name)
            self.assertEqual(type(network), EventfulNetwork)
            expected_data = {
                'node_id': '1',
                'data': node_data
            }
            self.assertEqual(expected_data, data)
            callback_reached[event_name] = True

        en = EventfulNetwork(callbacks={EVENT_ADD_NODE_DATA: [add_node_data_callback]})
        en.add_node(node_id)
        en.add_node_data(node_id, node_data)
        self.assertTrue(callback_reached[EVENT_ADD_NODE_DATA])

    def test_add_edge_data_callback(self):
        from_id = '1'
        to_id = '2'
        edge_id = '1_to_2'
        attr = dict()
        attr['lorem'] = 'ipsum'

        callback_reached = {}

        def add_edge_data_callback(network, event_name, data):
            self.assertEqual(EVENT_ADD_EDGE_DATA, event_name)
            expected_data = {
                'from_id': from_id,
                'to_id': to_id,
                'edge_id': edge_id,
                'data': attr
            }
            self.assertEqual(expected_data, data)
            self.assertEqual(type(network), EventfulNetwork)
            callback_reached[event_name] = True

        en = EventfulNetwork(callbacks={EVENT_ADD_EDGE_DATA: [add_edge_data_callback]})
        en.add_node(from_id)
        en.add_node(to_id)
        en.add_edge(from_id, to_id, edge_id, edge_id)
        en.add_edge_data(from_id, to_id, edge_id, attr)

        self.assertTrue(callback_reached[EVENT_ADD_EDGE_DATA])
