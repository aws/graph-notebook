# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Gremlin query formatter - Python port of gremlint."""

from typing import Optional

from .types import GremlintConfig, GremlintInternalConfig
from .parser import parse_to_syntax_trees
from .formatters import format_syntax_trees
from .recreate_formatted import recreate_query_string

__all__ = ['format_query', 'GremlintConfig']


def format_query(query: str, config: Optional[GremlintConfig] = None) -> str:
    """
    Format a Gremlin query string.
    
    Args:
        query: The Gremlin query to format
        config: Optional configuration options
        
    Returns:
        The formatted query string
        
    Example:
        >>> from graph_notebook.formatters.gremlin import format_query
        >>> query = "g.V().hasLabel('person').out('knows').values('name')"
        >>> print(format_query(query))
        g.V().
          hasLabel('person').
          out('knows').
          values('name')
    """
    if config is None:
        config = GremlintConfig()
    
    internal_config = GremlintInternalConfig(
        global_indentation=config.indentation,
        local_indentation=0,
        max_line_length=config.max_line_length - config.indentation,
        should_place_dots_after_line_breaks=config.should_place_dots_after_line_breaks,
        should_start_with_dot=False,
        should_end_with_dot=False,
        horizontal_position=0,
    )
    
    trees = parse_to_syntax_trees(query)
    formatted = format_syntax_trees(internal_config, trees)
    return recreate_query_string(internal_config, formatted)
