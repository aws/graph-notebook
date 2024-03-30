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
                'title': "airport"},
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
                "title": 'route',
                "properties": {
                    "~id": "7389",
                    "~entityType": "relationship",
                    "~start": "22",
                    "~end": "151",
                    "~type": "route",
                    'dist': 956
                }
            },
            'label': 'route',
            'title': 'route',
            'from_id': "22",
            'to_id': '151',
            'edge_id': '7389'
        }

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

    def test_ignore_group(self):
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

        gn = OCNetwork(ignore_groups=True)
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], 'DEFAULT_GROUP')

        gn = OCNetwork(group_by_property="code", ignore_groups=True)
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], 'DEFAULT_GROUP')

    def test_default_groups_no_label(self):
        res = {
            "results": [
                {
                    "a": {
                        "~id": "22",
                        "~entityType": "node",
                        "~properties": {
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }

        gn = OCNetwork(ignore_groups=True)
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], 'DEFAULT_GROUP')

        gn = OCNetwork(group_by_property="code", ignore_groups=True)
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], 'DEFAULT_GROUP')

    def test_default_groups_empty_label(self):
        res = {
            "results": [
                {
                    "a": {
                        "~id": "22",
                        "~entityType": "node",
                        "~labels": [],
                        "~properties": {
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }

        gn = OCNetwork(ignore_groups=True)
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], 'DEFAULT_GROUP')

        gn = OCNetwork(group_by_property="code", ignore_groups=True)
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], 'DEFAULT_GROUP')

    def test_group_with_groupby(self):
        path = {
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

    def test_group_with_groupby_property_id_custom(self):
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
                            "id": "custom_id_159",
                            "desc": "Fairbanks International Airport",
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
                            "id": "custom_id_8",
                            "desc": "Dallas/Fort Worth International Airport",
                        }
                    }
                }
            ]
        }

        gn = OCNetwork(group_by_property='id')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('159')
        node2 = gn.graph.nodes.get('8')
        self.assertEqual(node1['group'], 'custom_id_159')
        self.assertEqual(node2['group'], 'custom_id_8')

    def test_group_with_groupby_property_id_actual(self):
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
                            "id": "test_id",
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
                            "id": "test_id",
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

    def test_group_with_groupby_label_custom(self):
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
                            "labels": "custom_label_159",
                            "desc": "Fairbanks International Airport",
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
                            "labels": "custom_label_8",
                            "desc": "Dallas/Fort Worth International Airport",
                        }
                    }
                }
            ]
        }

        gn = OCNetwork(group_by_property='labels')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('159')
        node2 = gn.graph.nodes.get('8')
        self.assertEqual(node1['group'], 'custom_label_159')
        self.assertEqual(node2['group'], 'custom_label_8')

    def test_group_with_groupby_label_actual(self):
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
                            "labels": "custom_label_159",
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
                            "labels": "custom_label_8",
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

        gn = OCNetwork(group_by_property='~labels')
        gn.add_results(res)        
        node1 = gn.graph.nodes.get('159')
        node2 = gn.graph.nodes.get('8')
        self.assertEqual(node1['group'], 'airport')
        self.assertEqual(node2['group'], 'airport')

    def test_group_with_groupby_depth_default(self):
        node = {
            "~id": "3",
            "~entityType": "node",
            "~labels": [
                "airport"
            ],
            "~properties": {
                "desc": "Austin Bergstrom International Airport",
            }
        }

        gn = OCNetwork(group_by_property='TRAVERSAL_DEPTH')
        gn.parse_node(node)
        node1 = gn.graph.nodes.get('3')
        self.assertEqual(node1['group'], '__DEPTH--1__')

    def test_group_with_groupby_depth_string(self):
        node = {
            "~id": "3",
            "~entityType": "node",
            "~labels": [
                "airport"
            ],
            "~properties": {
                "desc": "Austin Bergstrom International Airport",
            }
        }

        gn = OCNetwork(group_by_property='TRAVERSAL_DEPTH')
        gn.parse_node(node, path_index=2)
        node1 = gn.graph.nodes.get('3')
        self.assertEqual(node1['group'], '__DEPTH-1__')

    def test_group_with_groupby_depth_json(self):
        node = {
            "~id": "3",
            "~entityType": "node",
            "~labels": [
                "airport"
            ],
            "~properties": {
                "desc": "Austin Bergstrom International Airport",
            }
        }

        gn = OCNetwork(group_by_property='{"airport":"TRAVERSAL_DEPTH"}')
        gn.parse_node(node, path_index=2)
        node1 = gn.graph.nodes.get('3')
        self.assertEqual(node1['group'], '__DEPTH-1__')

    def test_group_with_groupby_depth_explicit_command(self):
        node = {
            "~id": "3",
            "~entityType": "node",
            "~labels": [
                "airport"
            ],
            "~properties": {
                "desc": "Austin Bergstrom International Airport",
            }
        }

        gn = OCNetwork(group_by_depth=True)
        gn.parse_node(node, path_index=2)
        node1 = gn.graph.nodes.get('3')
        self.assertEqual(node1['group'], '__DEPTH-1__')

    def test_group_with_groupby_depth_explicit_command_overwrite_gbp(self):
        node = {
            "~id": "3",
            "~entityType": "node",
            "~labels": [
                "airport"
            ],
            "~properties": {
                "desc": "Austin Bergstrom International Airport",
            }
        }

        gn = OCNetwork(group_by_depth=True, group_by_property='{"airport":"desc"}')
        gn.parse_node(node, path_index=2)
        node1 = gn.graph.nodes.get('3')
        self.assertEqual(node1['group'], '__DEPTH-1__')

    def test_group_by_raw_string(self):
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

        expected = "{'~id': '22', '~entityType': 'node', '~labels': ['airport'], " \
                   "'~properties': {'runways': 3, 'code': 'SEA'}}"

        gn = OCNetwork(group_by_property='__RAW_RESULT__')
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], expected)

    def test_group_by_raw_json(self):
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

        expected = "{'~id': '22', '~entityType': 'node', '~labels': ['airport'], " \
                   "'~properties': {'runways': 3, 'code': 'SEA'}}"

        gn = OCNetwork(group_by_property='{"airport":"__RAW_RESULT__"}')
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], expected)

    def test_group_by_raw_explicit(self):
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

        expected = "{'~id': '22', '~entityType': 'node', '~labels': ['airport'], " \
                   "'~properties': {'runways': 3, 'code': 'SEA'}}"

        gn = OCNetwork(group_by_raw=True)
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], expected)

    def test_group_by_raw_explicit_overrule_gbp(self):
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

        expected = "{'~id': '22', '~entityType': 'node', '~labels': ['airport'], " \
                   "'~properties': {'runways': 3, 'code': 'SEA'}}"

        gn = OCNetwork(group_by_raw=True, group_by_property='{"airport":"code"}')
        gn.add_results(res)
        node = gn.graph.nodes.get('22')
        self.assertEqual(node['group'], expected)

    def test_group_with_groupby_depth(self):
        res = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "3",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Austin Bergstrom International Airport",
                            }
                        },
                        {
                            "~id": "3820",
                            "~entityType": "relationship",
                            "~start": "3",
                            "~end": "23",
                            "~type": "route",
                            "~properties": {
                                "dist": 1500
                            }
                        },
                        {
                            "~id": "23",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "San Francisco International Airport",
                            }
                        },
                        {
                            "~id": "7541",
                            "~entityType": "relationship",
                            "~start": "23",
                            "~end": "55",
                            "~type": "route",
                            "~properties": {
                                "dist": 7420
                            }
                        },
                        {
                            "~id": "55",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Sydney Kingsford Smith",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(group_by_property='TRAVERSAL_DEPTH')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('3')
        node2 = gn.graph.nodes.get('23')
        node3 = gn.graph.nodes.get('55')
        self.assertEqual(node1['group'], '__DEPTH-0__')
        self.assertEqual(node2['group'], '__DEPTH-1__')
        self.assertEqual(node3['group'], '__DEPTH-2__')

    def test_path_with_default_groupby(self):
        res = {
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
                                "desc": "Seattle-Tacoma",
                                "lon": -122.30899810791,
                                "runways": 3,
                                "type": "airport",
                                "country": "US",
                                "region": "US-WA",
                                "lat": 47.4490013122559,
                                "elev": 432,
                                "city": "Seattle",
                                "icao": "KSEA",
                                "code": "SEA",
                                "longest": 11901
                            }
                        },
                        {
                            "~id": "57081",
                            "~entityType": "relationship",
                            "~start": "3684",
                            "~end": "22",
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
                            "~id": "22",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Seattle-Tacoma",
                                "lon": -122.30899810791,
                                "runways": 3,
                                "type": "airport",
                                "country": "US",
                                "region": "US-WA",
                                "lat": 47.4490013122559,
                                "elev": 432,
                                "city": "Seattle",
                                "icao": "KSEA",
                                "code": "SEA",
                                "longest": 11901
                            }
                        },
                        {
                            "~id": "53637",
                            "~entityType": "relationship",
                            "~start": "3670",
                            "~end": "22",
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
        gn.add_results(res)        
        seattle = gn.graph.nodes.get('22')
        north_america = gn.graph.nodes.get('3684')
        united_states = gn.graph.nodes.get('3670')
        self.assertEqual(seattle['group'], 'airport')
        self.assertEqual(north_america['group'], 'continent')
        self.assertEqual(united_states['group'], 'country')

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

        gn = OCNetwork(group_by_property='{"airport":"code"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['group'], 'SEA')

    def test_group_with_groupby_properties_json_label_value_custom(self):
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
                            "labels": "custom_label_22",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }

        gn = OCNetwork(group_by_property='{"airport":"labels"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['group'], 'custom_label_22')

    def test_group_with_groupby_properties_json_label_value_actual(self):
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
                            "labels": "custom_label_22",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }

        gn = OCNetwork(group_by_property='{"airport":"~labels"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['group'], 'airport')

    def test_group_with_groupby_properties_json_ID_value_custom(self):
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
                            "id": "custom_id_22",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }

        gn = OCNetwork(group_by_property='{"airport":"id"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['group'], 'custom_id_22')

    def test_group_with_groupby_properties_json_ID_value_actual(self):
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
                            "id": "custom_id_22",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }

        gn = OCNetwork(group_by_property='{"airport":"~id"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['group'], '22')

    def test_group_with_groupby_properties_json_depth(self):
        res = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "3",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Austin Bergstrom International Airport",
                            }
                        },
                        {
                            "~id": "3820",
                            "~entityType": "relationship",
                            "~start": "3",
                            "~end": "23",
                            "~type": "route",
                            "~properties": {
                                "dist": 1500
                            }
                        },
                        {
                            "~id": "23",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "San Francisco International Airport",
                            }
                        },
                        {
                            "~id": "7541",
                            "~entityType": "relationship",
                            "~start": "23",
                            "~end": "55",
                            "~type": "route",
                            "~properties": {
                                "dist": 7420
                            }
                        },
                        {
                            "~id": "55",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Sydney Kingsford Smith",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(group_by_property='{"airport":"TRAVERSAL_DEPTH"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('3')
        node2 = gn.graph.nodes.get('23')
        node3 = gn.graph.nodes.get('55')
        self.assertEqual(node1['group'], '__DEPTH-0__')
        self.assertEqual(node2['group'], '__DEPTH-1__')
        self.assertEqual(node3['group'], '__DEPTH-2__')

    def test_group_with_groupby_properties_json_invalid(self):
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

        gn = OCNetwork(group_by_property='{"airport":"elevation"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['group'], 'DEFAULT_GROUP')

    def test_group_with_groupby_properties_json_multiple_labels(self):
        path = {
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

        gn = OCNetwork(group_by_property='{"airport":"code","country":"desc"}')
        gn.add_results(path)
        node1 = gn.graph.nodes.get('2')
        node2 = gn.graph.nodes.get('3670')
        self.assertEqual(node1['group'], 'ANC')
        self.assertEqual(node2['group'], 'United States')

    def test_add_non_graphable_results_list(self):
        res = {
            'results': [
                {
                    'a': [1, 2, 3, 4, 5, 6, 7]
                }
            ]
        }

        gn = OCNetwork()
        try:
            gn.add_results(res)
        except TypeError:
            self.fail()
        nodes_list = list(gn.graph.nodes)
        edges_list = list(gn.graph.edges)
        self.assertEqual(nodes_list, [])
        self.assertEqual(edges_list, [])

    def test_add_empty_node_in_dict(self):
        res = {
            "results": [
                {
                    "d": {
                        "~id": "6a6e5a7c-41ab-46e1-a8d1-397cc3e55294",
                        "~entityType": "node",
                        "~labels": [],
                        "~properties": {}
                    }
                }
            ]
        }

        gn = OCNetwork()
        try:
            gn.add_results(res)
        except IndexError:
            self.fail()
        nodes_list = list(gn.graph.nodes)
        self.assertEqual(nodes_list, ["6a6e5a7c-41ab-46e1-a8d1-397cc3e55294"])

        node = gn.graph.nodes.get("6a6e5a7c-41ab-46e1-a8d1-397cc3e55294")
        self.assertEqual(node['label'], "6a6e5a7...")
        self.assertEqual(node['title'], "6a6e5a7c-41ab-46e1-a8d1-397cc3e55294")

    def test_add_empty_node_in_list(self):
        res = {
            "results": [
                {
                    "p": [
                        {
                            '~id': "6a6e5a7c-41ab-46e1-a8d1-397cc3e55294",
                            '~entityType': "node",
                            "~labels": [],
                            "~properties": {}
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork()
        try:
            gn.add_results(res)
        except IndexError:
            self.fail()
        nodes_list = list(gn.graph.nodes)
        self.assertEqual(nodes_list, ["6a6e5a7c-41ab-46e1-a8d1-397cc3e55294"])

        node = gn.graph.nodes.get("6a6e5a7c-41ab-46e1-a8d1-397cc3e55294")
        self.assertEqual(node['label'], "6a6e5a7...")
        self.assertEqual(node['title'], "6a6e5a7c-41ab-46e1-a8d1-397cc3e55294")

    def test_do_not_set_vertex_label_or_vertex_tooltip(self):
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
        gn = OCNetwork()
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_property_string(self):
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
        gn = OCNetwork(display_property='code')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'SEA')
        self.assertEqual(node1['title'], 'SEA')

    def test_set_vertex_label_property_string_apostrophe_value(self):
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
                            "code": "S'E'A"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='code')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], "S'E'A")
        self.assertEqual(node1['title'], "S'E'A")

    def test_set_vertex_label_property_string_id_custom(self):
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
                            "id": "node_22",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='id')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'node_22')
        self.assertEqual(node1['title'], 'node_22')

    def test_set_vertex_label_property_string_label_custom(self):
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
                            "label": "airport_22",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='label')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport_22')
        self.assertEqual(node1['title'], 'airport_22')

    def test_set_vertex_label_property_string_type_custom(self):
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
                            "type": "test_type",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='type')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'test_type')
        self.assertEqual(node1['title'], 'test_type')

    def test_set_vertex_label_property_string_id_actual(self):
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
                            "id": "node_22",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='~id')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], '22')
        self.assertEqual(node1['title'], '22')

    def test_set_vertex_label_property_string_actual(self):
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
                            "label": "airport_22",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='~labels')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_property_string_type_actual(self):
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
                            "type": "test_type",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='~entityType')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'node')
        self.assertEqual(node1['title'], 'node')

    def test_set_vertex_label_property_json(self):
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
        self.assertEqual(node1['title'], 'SEA')

    def test_set_vertex_label_property_json_apostrophe_value(self):
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
                            "code": "S'E'A"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='{"airport":"code"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], "S'E'A")
        self.assertEqual(node1['title'], "S'E'A")

    def test_set_vertex_label_property_invalid_json(self):
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
        gn = OCNetwork(display_property='{"airport":code}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_property_invalid_key(self):
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
        gn = OCNetwork(display_property='{"location":"code"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_length(self):
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
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_property_invalid_value(self):
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
        self.assertEqual(node1['title'], 'airport')

    def test_set_label_property_multiple_vertices_property_string(self):
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
                    },
                    "b": {
                        "~id": "11",
                        "~entityType": "node",
                        "~labels": [
                            "airport"
                        ],
                        "~properties": {
                            "runways": 5,
                            "code": "JFK"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='code')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('11')
        node2 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'JFK')
        self.assertEqual(node1['title'], 'JFK')
        self.assertEqual(node2['label'], 'SEA')
        self.assertEqual(node2['title'], 'SEA')

    def test_set_label_property_multiple_types(self):
        path = {
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
        self.assertEqual(node1['title'], 'ANC')
        self.assertEqual(node2['label'], 'United ...')
        self.assertEqual(node2['title'], 'United States')

    def test_set_vertex_label_property_string_and_multiproperty_access(self):
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
                            "code": ["SEA", "SJC"]
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='code[1]')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'SJC')
        self.assertEqual(node1['title'], 'SJC')

    def test_set_vertex_label_property_string_and_multiproperty_access_no_property_match(self):
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
                            "code": ["SEA", "SJC"]
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='distance[1]')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_property_string_and_multiproperty_access_non_multiproperty(self):
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
        gn = OCNetwork(display_property='code[1]')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_property_string_and_multiproperty_access_with_bad_index(self):
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
                            "code": ["SEA", "SJC"]
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='code[2]')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_property_string_and_non_multiproperty_access_on_multiproperty_value(self):
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
                            "code": ["SEA", "SJC"]
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='code', label_max_length=50)
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], "['SEA', 'SJC']")
        self.assertEqual(node1['title'], "['SEA', 'SJC']")

    def test_set_vertex_label_property_json_and_multiproperty_access(self):
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
                            "code": ["SEA", "SJC"]
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='{"airport":"code[1]"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'SJC')
        self.assertEqual(node1['title'], 'SJC')

    def test_set_vertex_label_property_json_and_non_multiproperty_access_on_multiproperty_value(self):
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
                            "code": ["SEA", "SJC"]
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='{"airport":"code"}', label_max_length=50)
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], "['SEA', 'SJC']")
        self.assertEqual(node1['title'], "['SEA', 'SJC']")

    def test_set_vertex_label_property_json_and_multiproperty_access_on_non_multiproperty(self):
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
        gn = OCNetwork(display_property='{"airport":"code[1]"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_property_json_and_multiproperty_access_no_match(self):
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
                            "code": ["SEA", "SJC"]
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='{"airport":"distance[1]"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_vertex_label_property_json_and_multiproperty_access_with_bad_index(self):
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
                            "code": ["SEA", "SJC"]
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(display_property='{"airport":"code[2]"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_multiple_vertex_label_multiproperty(self):
        path = {
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
                                "longest": 12400,
                                'regionality': ['domestic', 'international']
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
                                "code": "US",
                                "alliances": ['NATO', 'UN']
                            }
                        }
                    ]
                }
            ]
        }
        gn = OCNetwork(display_property='{"airport":"regionality[0]","country":"alliances[0]"}')
        gn.add_results(path)
        node1 = gn.graph.nodes.get('2')
        node2 = gn.graph.nodes.get('3670')
        self.assertEqual(node1['label'], 'domestic')
        self.assertEqual(node1['title'], 'domestic')
        self.assertEqual(node2['label'], 'NATO')
        self.assertEqual(node2['title'], 'NATO')

    def test_set_vertex_tooltip_property_string_custom(self):
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
                            "type": "test_type",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(tooltip_property='type')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'test_type')

    def test_set_vertex_tooltip_property_string_custom_actual(self):
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
                            "type": "test_type",
                            "runways": 3,
                            "code": "SEA"
                        }
                    }
                }
            ]
        }
        gn = OCNetwork(tooltip_property='~entityType')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'node')

    def test_set_vertex_tooltip_property_json(self):
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
        gn = OCNetwork(tooltip_property='{"airport":"code"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'SEA')

    def test_set_vertex_tooltip_property_invalid_value(self):
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
        gn = OCNetwork(tooltip_property='{"airport":"foo"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], 'airport')
        self.assertEqual(node1['title'], 'airport')

    def test_set_different_vertex_tooltip_property_and_label_property(self):
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
        gn = OCNetwork(display_property='{"airport":"runways"}', tooltip_property='{"airport":"code"}')
        gn.add_results(res)
        node1 = gn.graph.nodes.get('22')
        self.assertEqual(node1['label'], '3')
        self.assertEqual(node1['title'], 'SEA')

    def test_add_edge_without_property(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork()
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_string(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='dist')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], '792')

    def test_add_edge_with_property_string_apostrophe_value(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": "7'9'2"
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='dist')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], "7'9'2")

    def test_add_edge_with_property_string_and_multiproperty_access(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='endpoints[0]')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], '365')

    def test_add_edge_with_property_string_and_multiproperty_access_no_property_match(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='callsigns[0]')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_string_and_multiproperty_access_with_non_multiproperty(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='dist[0]')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_string_and_multiproperty_access_with_bad_index(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='endpoints[2]')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_string_invalid(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='desc')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_json(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"dist"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], '792')

    def test_add_edge_with_property_json_apostrophe_value(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": "7'9'2"
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"dist"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], "7'9'2")

    def test_add_edge_with_property_invalid_json(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":dist}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_json_invalid_key(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"road":"dist"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_invalid_json_value(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"trips"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_json_and_multiproperty_access(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"endpoints[0]"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], '365')

    def test_add_edge_with_property_json_and_multiproperty_access_display_param_has_no_index(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"endpoints"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], "['365',...")

    def test_add_edge_with_property_json_and_multiproperty_access_with_non_multiproperty(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"dist[0]"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_json_and_multiproperty_access_no_matching_property(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"callsigns[0]"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_add_edge_with_property_json_and_multiproperty_access_with_bad_index(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"endpoints[2]"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')

    def test_set_relation_label_length_full(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_label_max_length=5)
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')
        self.assertEqual(edge_route['title'], 'route')

    def test_set_relation_label_length_truncated(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_label_max_length=4)
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'r...')
        self.assertEqual(edge_route['title'], 'route')

    def test_set_relation_label_length_less_than_3(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "CZM",
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "endpoints": ['365', '136']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "runways": 2,
                                "code": "MEX",
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_label_max_length=-100)
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], '...')
        self.assertEqual(edge_route['title'], 'route')

    def test_add_multiple_edge_with_property_string(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                },
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30604",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "367",
                            "~type": "path",
                            "~properties": {
                                "dist": 911
                            }
                        },
                        {
                            "~id": "367",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "General Mariano Escobedo International Airport",
                                "lon": -100.107002258,
                                "runways": 1,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-NLE",
                                "lat": 25.7784996033,
                                "elev": 1278,
                                "city": "Monterrey",
                                "icao": "MMMY",
                                "code": "MTY",
                                "longest": 5909
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='dist')
        gn.add_results(path)
        edge_1 = gn.graph.get_edge_data('365', '136', '30601')
        edge_2 = gn.graph.get_edge_data('365', '367', '30604')
        self.assertEqual(edge_1['label'], '792')
        self.assertEqual(edge_2['label'], '911')

    def test_add_multiple_edge_with_property_json(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                },
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30604",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "367",
                            "~type": "path",
                            "~properties": {
                                "dist": 911
                            }
                        },
                        {
                            "~id": "367",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "General Mariano Escobedo International Airport",
                                "lon": -100.107002258,
                                "runways": 1,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-NLE",
                                "lat": 25.7784996033,
                                "elev": 1278,
                                "city": "Monterrey",
                                "icao": "MMMY",
                                "code": "MTY",
                                "longest": 5909
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"dist","path":"~id"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        edge_path = gn.graph.get_edge_data('365', '367', '30604')
        self.assertEqual(edge_route['label'], '792')
        self.assertEqual(edge_path['label'], '30604')

    def test_add_multiple_edge_with_property_json_and_multiproperties(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "foobar": ['foo', 'bar']
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                },
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30604",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "367",
                            "~type": "path",
                            "~properties": {
                                "dist": 911,
                                "barfoo": ["bar", "foo"]
                            },
                        },
                        {
                            "~id": "367",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "General Mariano Escobedo International Airport",
                                "lon": -100.107002258,
                                "runways": 1,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-NLE",
                                "lat": 25.7784996033,
                                "elev": 1278,
                                "city": "Monterrey",
                                "icao": "MMMY",
                                "code": "MTY",
                                "longest": 5909
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"foobar[0]","path":"barfoo[0]"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        edge_path = gn.graph.get_edge_data('365', '367', '30604')
        self.assertEqual(edge_route['label'], 'foo')
        self.assertEqual(edge_path['label'], 'bar')

    def test_add_edge_with_tooltip_property_string(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_tooltip_property='dist')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')
        self.assertEqual(edge_route['title'], 792)

    def test_add_edge_with_tooltip_property_json(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_tooltip_property='{"route":"dist"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')
        self.assertEqual(edge_route['title'], 792)

    def test_add_edge_with_tooltip_property_json_invalid_value(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_tooltip_property='{"route":"foo"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'route')
        self.assertEqual(edge_route['title'], 'route')

    def test_add_edge_with_display_property_and_tooltip_property(self):
        path = {
            "results": [
                {
                    "p": [
                        {
                            "~id": "365",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Cozumel International Airport",
                                "lon": -86.9255981445312,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-ROO",
                                "lat": 20.5223999023438,
                                "elev": 15,
                                "city": "Cozumel",
                                "icao": "MMCZ",
                                "code": "CZM",
                                "longest": 10165
                            }
                        },
                        {
                            "~id": "30601",
                            "~entityType": "relationship",
                            "~start": "365",
                            "~end": "136",
                            "~type": "route",
                            "~properties": {
                                "dist": 792,
                                "lane": 'commercial'
                            }
                        },
                        {
                            "~id": "136",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Mexico City, Licenciado Benito Juarez International Airport",
                                "lon": -99.0720977783203,
                                "runways": 2,
                                "type": "airport",
                                "country": "MX",
                                "region": "MX-DIF",
                                "lat": 19.43630027771,
                                "elev": 7316,
                                "city": "Mexico City",
                                "icao": "MMMX",
                                "code": "MEX",
                                "longest": 12966
                            }
                        }
                    ]
                }
            ]
        }

        gn = OCNetwork(edge_display_property='{"route":"lane"}', edge_tooltip_property='{"route":"dist"}')
        gn.add_results(path)
        edge_route = gn.graph.get_edge_data('365', '136', '30601')
        self.assertEqual(edge_route['label'], 'commercial')
        self.assertEqual(edge_route['title'], 792)


if __name__ == '__main__':
    unittest.main()
