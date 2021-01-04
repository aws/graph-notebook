"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from .completers.graph_completer import get_completion_options
from .graph_magic import Graph


def load_ipython_extension(ipython):
    ipython.set_hook('complete_command', get_completion_options, re_key=".*")
    ipython.register_magics(Graph)
