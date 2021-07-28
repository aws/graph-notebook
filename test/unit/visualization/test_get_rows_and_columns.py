"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

import graph_notebook.visualization.rows_and_columns as rc


class TestGetRowsAndColumns(unittest.TestCase):

    def test_opencypher_parse_node_http(self):
        res = {
            "results": [
                {
                    "n": {
                        "~id": "22",
                        "~entityType": "node",
                        "~labels": [
                            "airport"
                        ],
                        "~properties": {
                            "desc": "Seattle-Tacoma",
                            "runways": 3,
                        }
                    }
                }
            ]
        }
        data = rc.opencypher_get_rows_and_columns(res, False)
        self.assertEqual(len(data['columns']), 1)
        self.assertEqual(len(data['rows']), 1)

    def test_opencypher_parse_path_http(self):
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
                            "~id": "4404",
                            "~entityType": "relationship",
                            "~start": "22",
                            "~end": "1",
                            "~type": "route",
                            "~properties": {
                                "dist": 2180
                            }
                        },
                        {
                            "~id": "1",
                            "~entityType": "node",
                            "~labels": [
                                "airport"
                            ],
                            "~properties": {
                                "desc": "Hartsfield - Jackson Atlanta International Airport",
                                "lon": -84.4281005859375,
                                "runways": 5,
                                "type": "airport",
                                "country": "US",
                                "region": "US-GA",
                                "lat": 33.6366996765137,
                                "elev": 1026,
                                "city": "Atlanta",
                                "icao": "KATL",
                                "code": "ATL",
                                "longest": 12390
                            }
                        }
                    ]
                }
            ]
        }
        data = rc.opencypher_get_rows_and_columns(res, False)
        self.assertEqual(len(data['columns']), 1)
        self.assertEqual(len(data['rows']), 1)

    def test_opencypher_parse_values_http(self):
        res = {
            "results": [
                {
                    "n.city": "Cozumel",
                    "n.elev": 15,
                    "r.dist": 918,
                    "d.city": "Atlanta"
                },
                {
                    "n.city": "Cozumel",
                    "n.elev": 15,
                    "r.dist": 1056,
                    "d.city": "Dallas"
                }
            ]
        }
        data = rc.opencypher_get_rows_and_columns(res, False)
        self.assertEqual(len(data['columns']), 4)
        self.assertEqual(len(data['rows']), 2)

    def test_opencypher_parse_node_bolt(self):
        res = [
            {
                "n": {
                    "~id": "22",
                    "~entityType": "node",
                    "~labels": [
                        "airport"
                    ],
                    "~properties": {
                        "desc": "Seattle-Tacoma",
                        "runways": 3,
                    }
                }
            }
        ]
        data = rc.opencypher_get_rows_and_columns(res, True)
        self.assertEqual(len(data['columns']), 1)
        self.assertEqual(len(data['rows']), 1)

    def test_opencypher_parse_path_bolt(self):
        res = [
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
                        "~id": "4404",
                        "~entityType": "relationship",
                        "~start": "22",
                        "~end": "1",
                        "~type": "route",
                        "~properties": {
                            "dist": 2180
                        }
                    },
                    {
                        "~id": "1",
                        "~entityType": "node",
                        "~labels": [
                            "airport"
                        ],
                        "~properties": {
                            "desc": "Hartsfield - Jackson Atlanta International Airport",
                            "lon": -84.4281005859375,
                            "runways": 5,
                            "type": "airport",
                            "country": "US",
                            "region": "US-GA",
                            "lat": 33.6366996765137,
                            "elev": 1026,
                            "city": "Atlanta",
                            "icao": "KATL",
                            "code": "ATL",
                            "longest": 12390
                        }
                    }
                ]
            }
        ]
        data = rc.opencypher_get_rows_and_columns(res, True)
        self.assertEqual(len(data['columns']), 1)
        self.assertEqual(len(data['rows']), 1)

    def test_opencypher_parse_values_bolt(self):
        res = [
            {
                "n.city": "Cozumel",
                "n.elev": 15,
                "r.dist": 918,
                "d.city": "Atlanta"
            },
            {
                "n.city": "Cozumel",
                "n.elev": 15,
                "r.dist": 1056,
                "d.city": "Dallas"
            }
        ]
        data = rc.opencypher_get_rows_and_columns(res, True)
        self.assertEqual(len(data['columns']), 4)
        self.assertEqual(len(data['rows']), 2)
