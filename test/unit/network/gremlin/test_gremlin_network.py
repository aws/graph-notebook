"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest
from gremlin_python.structure.graph import Path
from gremlin_python.process.traversal import T
from graph_notebook.network.EventfulNetwork import EVENT_ADD_NODE
from graph_notebook.network.gremlin.GremlinNetwork import GremlinNetwork
from gremlin_python.structure.graph import Vertex


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

<<<<<<< HEAD
=======
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

        gn = GremlinNetwork(group_by_property='{"airport":{"groupby":"code"}}')
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

        gn = GremlinNetwork(group_by_property='{"airport":{"groupby":"code"},"country":{"groupby":"continent"}}')
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

>>>>>>> rebase from 2.1.2
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

<<<<<<< HEAD
=======
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

        gn = GremlinNetwork(group_by_property='{"airport":{"groupby":"foo"},"country":{"groupby":"continent"}}')
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

        gn = GremlinNetwork(group_by_property='{"airport":{"groupby":"code"},"a_country":{"groupby":"continent"}}')
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], 'SEA')
        self.assertEqual(node2['group'], '')

>>>>>>> rebase from 2.1.2
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

<<<<<<< HEAD
=======
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

>>>>>>> rebase from 2.1.2
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

<<<<<<< HEAD
=======
    def test_group_with_groupby_list_properties_json(self):
        vertex = {
            T.id: '1234',
            T.label: 'airport',
            'code': ['SEA']
        }

        gn = GremlinNetwork(group_by_property='{"airport":{"groupby":"code"}}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get(vertex[T.id])
        self.assertEqual(node['group'], "['SEA']")

>>>>>>> rebase from 2.1.2
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

<<<<<<< HEAD
=======
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
        gn = GremlinNetwork(group_by_property='{"airport":{"groupby":"code"}}')
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
        gn = GremlinNetwork(group_by_property='{"airport":{"groupby":"region"}, "continent":{"groupby":"code"}}')
        gn.add_results([path])
        node1 = gn.graph.nodes.get('1')
        node2 = gn.graph.nodes.get('3741')
        self.assertEqual(node1['group'], "['US-GA']")
        self.assertEqual(node2['group'], "['AN']")

>>>>>>> rebase from 2.1.2
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

<<<<<<< HEAD
=======
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

        gn = GremlinNetwork(group_by_property='{"airport":{"groupby":"code"},"country":{"groupby":"continent"}}',
                            ignore_groups=True)
        gn.add_vertex(vertex1)
        gn.add_vertex(vertex2)
        node1 = gn.graph.nodes.get(vertex1[T.id])
        node2 = gn.graph.nodes.get(vertex2[T.id])
        self.assertEqual(node1['group'], '')
        self.assertEqual(node2['group'], '')

>>>>>>> rebase from 2.1.2
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

<<<<<<< HEAD
=======
    def test_group_returnvertex_groupby_label_properties_json(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(group_by_property='{"vertex":{"groupby":"label"}}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], 'vertex')

        gn = GremlinNetwork(group_by_property='{"vertex":{"groupby":"T.label"}}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], 'vertex')

>>>>>>> rebase from 2.1.2
    def test_group_returnvertex_groupby_id(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(group_by_property="id")
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], '1')

        gn = GremlinNetwork(group_by_property="T.id")
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], '')

<<<<<<< HEAD
=======
    def test_group_returnvertex_groupby_id_properties_json(self):
        vertex = Vertex(id='1')

        gn = GremlinNetwork(group_by_property='{"vertex":{"groupby":"id"}}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], '1')

        gn = GremlinNetwork(group_by_property='{"vertex":{"groupby":"T.id"}}')
        gn.add_vertex(vertex)
        node = gn.graph.nodes.get('1')
        self.assertEqual(node['group'], '')

>>>>>>> rebase from 2.1.2

if __name__ == '__main__':
    unittest.main()
