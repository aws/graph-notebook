"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""


def _jupyter_nbextension_paths():
    return [
        dict(
            section="notebook",
            src="gremlin_syntax/static",
            dest="gremlin_syntax",
            require="gremlin_syntax/main"),
        dict(
            section="notebook",
            src="sparql_syntax/static",
            dest="sparql_syntax",
            require="sparql_syntax/main"),
        dict(
            section="notebook",
            src="opencypher_syntax/static",
            dest="opencypher_syntax",
            require="opencypher_syntax/main"),
        dict(
            section="notebook",
            src="neptune_menu/static",
            dest="neptune_menu",
            require="neptune_menu/main"),
        dict(
            section="notebook",
            src="playable_cells/static",
            dest="playable_cells",
            require="playable_cells/main"),
    ]
