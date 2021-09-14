"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

# Documentation for these options: https://visjs.github.io/vis-network/docs/network
OPTIONS_DEFAULT_DIRECTED = {
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
        "solver": "barnesHut",
        "enabled": True,
        "adaptiveTimestep": True,
        "stabilization": {
            "enabled": True,
            "iterations": 1
        }
    }
}


def vis_options_merge(original, target):
    """Merge the target dict with the original dict, without modifying the input dicts.

    :param original: the original dict.
    :param target: the target dict that takes precedence when there are type conflicts or value conflicts.
    :return: a new dict containing references to objects in both inputs.
    """
    resultdict = {}
    common_keys = original.keys() & target.keys()

    for key in common_keys:
        obj1 = original[key]
        obj2 = target[key]

        if type(obj1) is dict and type(obj2) is dict:
            resultdict[key] = vis_options_merge(obj1, obj2)
        else:
            resultdict[key] = obj2

    for key in (original.keys() - target.keys()):
        resultdict[key] = original[key]

    for key in (target.keys() - original.keys()):
        resultdict[key] = target[key]

    return resultdict
