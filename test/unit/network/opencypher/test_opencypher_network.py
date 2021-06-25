"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest
from graph_notebook.network.EventfulNetwork import EVENT_ADD_EDGE, EVENT_ADD_NODE
from graph_notebook.network.opencypher.OCNetwork import OCNetwork


class TestOpenCypherNetwork(unittest.TestCase):
    def test_add_node_with_callback(self):
        res = {
        "results": [
            {
            "a": {
                "~id": "22",
                "~entityType": "node",
                "~labels": [
                "airport"
                ],
                "~properties": {
                "runways": 3,
                "code": "SEA"
                }
            }
            }
        ]
        }

        reached_callback = {}
        expected_data = {
            'data': {
                'group': 'airport',
                'label': 'airport',
                'properties': {
                    "~id": '22',
                    "~entityType": "node",
                    "~labels": ['airport'],
                    'code': 'SEA',
                    'runways': 3},
                'title': 'airport'},
            'node_id': '22'}

        def add_node_callback(network, event_name, data):
            self.assertEqual(event_name, EVENT_ADD_NODE)
            self.assertEqual(expected_data, data)
            reached_callback[event_name] = True

        gn = OCNetwork(callbacks={EVENT_ADD_NODE: [add_node_callback]})
        gn.add_results(res)
        self.assertTrue(reached_callback[EVENT_ADD_NODE])
        node = gn.graph.nodes.get("22")
        self.assertEqual(expected_data['data']['properties'], node['properties'])

    def test_add_edge_with_callback(self):
        res = {
        "results": [
            {
            "r": {
                "~id": "7389",
                "~entityType": "relationship",
                "~start": "22",
                "~end": "151",
                "~type": "route",
                "~properties": {
                "dist": 956
                }
            }
            }
        ]
        }

        reached_callback = {}
        expected_data = {
            'data': {
                "label": 'route',
                "properties": {
                "~id": "7389",
                "~entityType": "relationship",
                "~start": "22",
                "~end": "151",
                "~type": "route",
                'dist': 956}
                },
            'label': 'route',
            'from_id':"22",
            'to_id': '151',
            'edge_id': '7389'}

        def add_edge_callback(network, event_name, data):
            self.assertEqual(event_name, EVENT_ADD_EDGE)
            self.assertEqual(expected_data, data)
            reached_callback[event_name] = True

        gn = OCNetwork(callbacks={EVENT_ADD_EDGE: [add_edge_callback]})
        gn.add_results(res)
        self.assertTrue(reached_callback[EVENT_ADD_EDGE])

    def test_path(self):
        path = {
        "results": [
            {
            "p": [
                {
                "~id": "22",
                "~entityType": "node",
                "~labels": [
                    "airport"
                ],
                "~properties": {
                    "runways": 3,
                    "code": "SEA"
                }
                },
                {
                "~id": "7389",
                "~entityType": "relationship",
                "~start": "22",
                "~end": "151",
                "~type": "route",
                "~properties": {
                    "dist": 956
                }
                },
                {
                "~id": "151",
                "~entityType": "node",
                "~labels": [
                    "airport"
                ],
                "~properties": {
                    "runways": 2,
                    "code": "ONT"
                }
                }
            ]
            }
        ]
        }
        gn = OCNetwork()
        gn.add_results(path)
        self.assertEqual(2, len(gn.graph.nodes))
        self.assertEqual(1, len(gn.graph.edges))
    
    def test_group_with_groupby(self):
        path={
        "results": [
            {
            "p": [
                {
                "~id": "2",
                "~entityType": "node",
                "~labels": [
                    "airport"
                ],
                "~properties": {
                    "desc": "Anchorage Ted Stevens",
                    "lon": -149.996002197266,
                    "runways": 3,
                    "type": "airport",
                    "country": "US",
                    "region": "US-AK",
                    "lat": 61.1744003295898,
                    "elev": 151,
                    "city": "Anchorage",
                    "icao": "PANC",
                    "code": "ANC",
                    "longest": 12400
                }
                },
                {
                "~id": "57061",
                "~entityType": "relationship",
                "~start": "3684",
                "~end": "2",
                "~type": "contains"
                },
                {
                "~id": "3684",
                "~entityType": "node",
                "~labels": [
                    "continent"
                ],
                "~properties": {
                    "desc": "North America",
                    "code": "NA"
                }
                }
            ]
            },
            {
            "p": [
                {
                "~id": "2",
                "~entityType": "node",
                "~labels": [
                    "airport"
                ],
                "~properties": {
                    "desc": "Anchorage Ted Stevens",
                    "lon": -149.996002197266,
                    "runways": 3,
                    "type": "airport",
                    "country": "US",
                    "region": "US-AK",
                    "lat": 61.1744003295898,
                    "elev": 151,
                    "city": "Anchorage",
                    "icao": "PANC",
                    "code": "ANC",
                    "longest": 12400
                }
                },
                {
                "~id": "53617",
                "~entityType": "relationship",
                "~start": "3670",
                "~end": "2",
                "~type": "contains"
                },
                {
                "~id": "3670",
                "~entityType": "node",
                "~labels": [
                    "country"
                ],
                "~properties": {
                    "desc": "United States",
                    "code": "US"
                }
                }
            ]
            }
        ]
        }

        gn = OCNetwork()
        gn.add_results(path)
        node = gn.graph.nodes.get('2')
        self.assertEqual(node['group'], 'airport')
        node = gn.graph.nodes.get('3670')
        self.assertEqual(node['group'], 'country')
        node = gn.graph.nodes.get('3684')
        self.assertEqual(node['group'], 'continent')

    def test_group_with_groupby_property(self):
        res = {
            "results": [
                {
                "d": {
                    "~id": "159",
                    "~entityType": "node",
                    "~labels": [
                    "airport"
                    ],
                    "~properties": {
                    "desc": "Fairbanks International Airport",
                    "lon": -147.8560028,
                    "runways": 4,
                    "type": "airport",
                    "country": "US",
                    "region": "US-AK",
                    "lat": 64.81510162,
                    "elev": 439,
                    "city": "Fairbanks",
                    "icao": "PAFA",
                    "code": "FAI",
                    "longest": 11800
                    }
                }
                },
                {
                "d": {
                    "~id": "8",
                    "~entityType": "node",
                    "~labels": [
                    "airport"
                    ],
                    "~properties": {
                    "desc": "Dallas/Fort Worth International Airport",
                    "lon": -97.0380020141602,
                    "runways": 7,
                    "type": "airport",
                    "country": "US",
                    "region": "US-TX",
                    "lat": 32.896800994873,
                    "elev": 607,
                    "city": "Dallas",
                    "icao": "KDFW",
                    "code": "DFW",
                    "longest": 13401
                    }
                }
                }
            ]
            }

        gn = OCNetwork(group_by_property='region')
        gn.add_results(res)        
        node1 = gn.graph.nodes.get('159')
        node2 = gn.graph.nodes.get('8')
        self.assertEqual(node1['group'], 'US-AK')
        self.assertEqual(node2['group'], 'US-TX')
    
    def test_group_with_groupby_property(self):
        res = {
            "results": [
                {
                "d": {
                    "~id": "159",
                    "~entityType": "node",
                    "~labels": [
                    "airport"
                    ],
                    "~properties": {
                    "desc": "Fairbanks International Airport",
                    "lon": -147.8560028,
                    "runways": 4,
                    "type": "airport",
                    "country": "US",
                    "region": "US-AK",
                    "lat": 64.81510162,
                    "elev": 439,
                    "city": "Fairbanks",
                    "icao": "PAFA",
                    "code": "FAI",
                    "longest": 11800
                    }
                }
                },
                {
                "d": {
                    "~id": "8",
                    "~entityType": "node",
                    "~labels": [
                    "airport"
                    ],
                    "~properties": {
                    "desc": "Dallas/Fort Worth International Airport",
                    "lon": -97.0380020141602,
                    "runways": 7,
                    "type": "airport",
                    "country": "US",
                    "region": "US-TX",
                    "lat": 32.896800994873,
                    "elev": 607,
                    "city": "Dallas",
                    "icao": "KDFW",
                    "code": "DFW",
                    "longest": 13401
                    }
                }
                }
            ]
            }

        gn = OCNetwork(group_by_property='~id')
        gn.add_results(res)        
        node1 = gn.graph.nodes.get('159')
        node2 = gn.graph.nodes.get('8')
        self.assertEqual(node1['group'], '159')
        self.assertEqual(node2['group'], '8')

    def test_group_with_groupby_label(self):
        res = {
            "results": [
                {
                "d": {
                    "~id": "159",
                    "~entityType": "node",
                    "~labels": [
                    "airport"
                    ],
                    "~properties": {
                    "desc": "Fairbanks International Airport",
                    "lon": -147.8560028,
                    "runways": 4,
                    "type": "airport",
                    "country": "US",
                    "region": "US-AK",
                    "lat": 64.81510162,
                    "elev": 439,
                    "city": "Fairbanks",
                    "icao": "PAFA",
                    "code": "FAI",
                    "longest": 11800
                    }
                }
                },
                {
                "d": {
                    "~id": "8",
                    "~entityType": "node",
                    "~labels": [
                    "airport"
                    ],
                    "~properties": {
                    "desc": "Dallas/Fort Worth International Airport",
                    "lon": -97.0380020141602,
                    "runways": 7,
                    "type": "airport",
                    "country": "US",
                    "region": "US-TX",
                    "lat": 32.896800994873,
                    "elev": 607,
                    "city": "Dallas",
                    "icao": "KDFW",
                    "code": "DFW",
                    "longest": 13401
                    }
                }
                }
            ]
            }

        gn = OCNetwork(group_by_property='region')
        gn.add_results(res)        
        node1 = gn.graph.nodes.get('159')
        node2 = gn.graph.nodes.get('8')
        self.assertEqual(node1['group'], 'US-AK')
        self.assertEqual(node2['group'], 'US-TX')

    def test_group_with_groupby_properties_json_single_label(self):
        res = {
        "results": [
            {
            "a": {
                "~id": "22",
                "~entityType": "node",
                "~labels": [
                "airport"
                ],
                "~properties": {
                "runways": 3,
                "code": "SEA"
                }
            }
            }
        ]
        }

        gn = OCNetwork(group_by_property='{"airport":{"groupby":"code"}}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['group'], 'SEA')

    def test_group_with_groupby_properties_json_multiple_labels(self):
        path={
            "results": [
                {
                "p": [
                    {
                    "~id": "2",
                    "~entityType": "node",
                    "~labels": [
                        "airport"
                    ],
                    "~properties": {
                        "desc": "Anchorage Ted Stevens",
                        "lon": -149.996002197266,
                        "runways": 3,
                        "type": "airport",
                        "country": "US",
                        "region": "US-AK",
                        "lat": 61.1744003295898,
                        "elev": 151,
                        "city": "Anchorage",
                        "icao": "PANC",
                        "code": "ANC",
                        "longest": 12400
                    }
                    },
                    {
                    "~id": "53617",
                    "~entityType": "relationship",
                    "~start": "3670",
                    "~end": "2",
                    "~type": "contains"
                    },
                    {
                    "~id": "3670",
                    "~entityType": "node",
                    "~labels": [
                        "country"
                    ],
                    "~properties": {
                        "desc": "United States",
                        "code": "US"
                    }
                    }
                ]
                }
            ]
            }

        gn = OCNetwork(group_by_property='{"airport":{"groupby":"code"},"country":{"groupby":"desc"}}')
        gn.add_results(path)
        node1 = gn.graph.nodes.get('2')
        node2 = gn.graph.nodes.get('3670')
        self.assertEqual(node1['group'], 'ANC')
        self.assertEqual(node2['group'], 'United States')


    def test_set_label_property(self):
        res = {
        "results": [
            {
            "a": {
                "~id": "22",
                "~entityType": "node",
                "~labels": [
                "airport"
                ],
                "~properties": {
                "runways": 3,
                "code": "SEA"
                }
            }
            }
        ]
        }
        gn = OCNetwork(display_property='{"airport":"code"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'SEA')

    def test_set_label_length(self):
        res = {
        "results": [
            {
            "a": {
                "~id": "22",
                "~entityType": "node",
                "~labels": [
                "airport"
                ],
                "~properties": {
                "runways": 3,
                "code": "SEA"
                }
            }
            }
        ]
        }
        gn = OCNetwork(label_max_length=5)
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'ai...')

    def test_set_label_property_invalid(self):
        res = {
        "results": [
            {
            "a": {
                "~id": "22",
                "~entityType": "node",
                "~labels": [
                "airport"
                ],
                "~properties": {
                "runways": 3,
                "code": "SEA"
                }
            }
            }
        ]
        }
        gn = OCNetwork(display_property='{"airport":"foo"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')

    def test_set_label_property_multiple_types(self):
        path={
            "results": [
                {
                "p": [
                    {
                    "~id": "2",
                    "~entityType": "node",
                    "~labels": [
                        "airport"
                    ],
                    "~properties": {
                        "desc": "Anchorage Ted Stevens",
                        "lon": -149.996002197266,
                        "runways": 3,
                        "type": "airport",
                        "country": "US",
                        "region": "US-AK",
                        "lat": 61.1744003295898,
                        "elev": 151,
                        "city": "Anchorage",
                        "icao": "PANC",
                        "code": "ANC",
                        "longest": 12400
                    }
                    },
                    {
                    "~id": "53617",
                    "~entityType": "relationship",
                    "~start": "3670",
                    "~end": "2",
                    "~type": "contains"
                    },
                    {
                    "~id": "3670",
                    "~entityType": "node",
                    "~labels": [
                        "country"
                    ],
                    "~properties": {
                        "desc": "United States",
                        "code": "US"
                    }
                    }
                ]
                }
            ]
            }
        gn = OCNetwork(display_property='{"airport":"code","country":"desc"}')
        gn.add_results(path)
        node1 = gn.graph.nodes.get('2')
        node2 = gn.graph.nodes.get('3670')
        self.assertEqual(node1['label'], 'ANC')
        self.assertEqual(node2['label'], 'United ...')

if __name__ == '__main__':
    unittest.main()
