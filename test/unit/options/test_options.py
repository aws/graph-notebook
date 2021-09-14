"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.options import OPTIONS_DEFAULT_DIRECTED, vis_options_merge


class TestOptions(unittest.TestCase):
    def test_vis_options_merge_add_primitive(self):
        test_cases = [
            {
                'original': {},
                'target': {"key1": 0},
                'expected': {"key1": 0}
            },
            {
                'original': {},
                'target': {"key1": True},
                'expected': {"key1": True}
            },
            {
                'original': {},
                'target': {"key1": "black"},
                'expected': {"key1": "black"}
            },
            {
                'original': {"key2": 42, "key3": {"key4": 42}},
                'target': {"key3": {"key1": True}},
                'expected': {"key2": 42, "key3": {"key4": 42, "key1": True}}
            }
        ]

        for t in test_cases:
            self.assertDictEqual(t['expected'], vis_options_merge(t['original'], t['target']))

    def test_vis_options_merge_add_mutable(self):
        test_cases = [
            {
                'original': {},
                'target': {"key1": [255, 255, 255]},
                'expected': {"key1": [255, 255, 255]}
            },
            {
                'original': {},
                'target': {"key1": {"red": 255, "green": 255, "blue": 255}},
                'expected': {"key1": {"red": 255, "green": 255, "blue": 255}}
            },
            {
                'original': {"color": {"border": "transparent"}},
                'target': {
                    "color": {
                        "highlight": {
                            "background": "rgba(9, 104, 178, 1)",
                            "border": "rgba(8, 62, 100, 1)"
                        },
                        "background": [255, 255, 255, 1]
                    }
                },
                'expected': {
                    "color": {
                        "border": "transparent",
                        "highlight": {
                            "background": "rgba(9, 104, 178, 1)",
                            "border": "rgba(8, 62, 100, 1)"
                        },
                        "background": [255, 255, 255, 1]
                    }
                }
            },
        ]

        for t in test_cases:
            self.assertDictEqual(t['expected'], vis_options_merge(t['original'], t['target']))

    def test_vis_options_merge_replace(self):
        test_cases = [
            {
                'original': {"key1": 0},
                'target': {"key1": 42},
                'expected': {"key1": 42}
            },
            {
                'original': {"key1": False},
                'target': {"key1": "circle"},
                'expected': {"key1": "circle"}
            },
            {
                'original': {"key1": "transparent"},
                'target': {"key1": True},
                'expected': {"key1": True}
            },
            {
                'original': {"key2": 42, "key3": {"key4": [255, 255, 255], "key5": True}},
                'target': {"key3": {"key4": [], "key5": {"key6": {}}}},
                'expected': {"key2": 42, "key3": {"key4": [], "key5": {"key6": {}}}}
            }
        ]

        for t in test_cases:
            self.assertDictEqual(t['expected'], vis_options_merge(t['original'], t['target']))

    def test_vis_options_merge_complete_config(self):
        test_cases = [
            {
                'original': OPTIONS_DEFAULT_DIRECTED,
                'target': {
                    "physics": {
                        "simulationDuration": 1500,
                        "disablePhysicsAfterInitialSimulation": False,
                        "hierarchicalRepulsion": {
                            "centralGravity": 0
                        },
                        "minVelocity": 0.75,
                        "solver": "hierarchicalRepulsion"
                    },
                    "layout": {
                        "hierarchical": {
                            "enabled": True,
                            "direction": "LR",
                            "sortMethod": "directed",
                            "edgeMinimization": False
                        }
                    }
                },
                'expected': {
                    "nodes": {
                        "borderWidthSelected": 0,
                        "borderWidth": 0,
                        "color": {
                            "background": "rgba(210, 229, 255, 1)",
                            "border": "transparent",
                            "highlight": {
                                "background": "rgba(9, 104, 178, 1)",
                                "border": "rgba(8, 62, 100, 1)"
                            }
                        },
                        "shadow": {
                            "enabled": False
                        },
                        "shape": "circle",
                        "widthConstraint": {
                            "minimum": 70,
                            "maximum": 70
                        },
                        "font": {
                            "face": "courier new",
                            "color": "black",
                            "size": 12
                        }
                    },
                    "edges": {
                        "color": {
                            "inherit": False
                        },
                        "smooth": {
                            "enabled": True,
                            "type": "straightCross"
                        },
                        "arrows": {
                            "to": {
                                "enabled": True,
                                "type": "arrow"
                            }
                        },
                        "font": {
                            "face": "courier new"
                        }
                    },
                    "interaction": {
                        "hover": True,
                        "hoverConnectedEdges": True,
                        "selectConnectedEdges": False
                    },
                    "physics": {
                        "simulationDuration": 1500,
                        "disablePhysicsAfterInitialSimulation": False,
                        "minVelocity": 0.75,
                        "barnesHut": {
                            "centralGravity": 0.1,
                            "gravitationalConstant": -50450,
                            "springLength": 95,
                            "springConstant": 0.04,
                            "damping": 0.09,
                            "avoidOverlap": 0.1
                        },
                        "solver": "hierarchicalRepulsion",
                        "enabled": True,
                        "adaptiveTimestep": True,
                        "stabilization": {
                            "enabled": True,
                            "iterations": 1
                        },
                        "hierarchicalRepulsion": {
                            "centralGravity": 0
                        }
                    },
                    "layout": {
                        "hierarchical": {
                            "enabled": True,
                            "direction": "LR",
                            "sortMethod": "directed",
                            "edgeMinimization": False
                        }
                    }
                }
            },
            {
                'original': OPTIONS_DEFAULT_DIRECTED,
                'target': {
                    "nodes": {
                        "shadow": {
                            "enabled": True
                        },
                        "shape": "hexagon"
                    },
                    "edges": {
                        "dashes": [1, 1, 2, 1, 3, 1, 4, 1, 5, 1, 6, 1]
                    }
                },
                'expected': {
                    "nodes": {
                        "borderWidthSelected": 0,
                        "borderWidth": 0,
                        "color": {
                            "background": "rgba(210, 229, 255, 1)",
                            "border": "transparent",
                            "highlight": {
                                "background": "rgba(9, 104, 178, 1)",
                                "border": "rgba(8, 62, 100, 1)"
                            }
                        },
                        "shadow": {
                            "enabled": True
                        },
                        "shape": "hexagon",
                        "widthConstraint": {
                            "minimum": 70,
                            "maximum": 70
                        },
                        "font": {
                            "face": "courier new",
                            "color": "black",
                            "size": 12
                        },
                    },
                    "edges": {
                        "color": {
                            "inherit": False
                        },
                        "smooth": {
                            "enabled": True,
                            "type": "straightCross"
                        },
                        "arrows": {
                            "to": {
                                "enabled": True,
                                "type": "arrow"
                            }
                        },
                        "font": {
                            "face": "courier new"
                        },
                        "dashes": [1, 1, 2, 1, 3, 1, 4, 1, 5, 1, 6, 1]
                    },
                    "interaction": {
                        "hover": True,
                        "hoverConnectedEdges": True,
                        "selectConnectedEdges": False
                    },
                    "physics": {
                        "simulationDuration": 1500,
                        "disablePhysicsAfterInitialSimulation": False,
                        "minVelocity": 0.75,
                        "barnesHut": {
                            "centralGravity": 0.1,
                            "gravitationalConstant": -50450,
                            "springLength": 95,
                            "springConstant": 0.04,
                            "damping": 0.09,
                            "avoidOverlap": 0.1
                        },
                        "solver": "barnesHut",
                        "enabled": True,
                        "adaptiveTimestep": True,
                        "stabilization": {
                            "enabled": True,
                            "iterations": 1
                        }
                    }
                }
            }
        ]

        for t in test_cases:
            self.assertDictEqual(t['expected'], vis_options_merge(t['original'], t['target']))
