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
    
    def test_group_with_groupby_property_id(self):
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


    def test_set_vertex_label_property(self):
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

    def test_set_vertex_label_property_invalid(self):
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

    def test_set_vertex_label_property_multiple_types(self):
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
                      "~type": "route",
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

if __name__ == '__main__':
    unittest.main()
