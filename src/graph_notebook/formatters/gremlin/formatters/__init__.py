# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Format syntax trees."""

from typing import List

from ..types import (
    TokenType,
    GremlintInternalConfig,
    UnformattedSyntaxTree,
    FormattedSyntaxTree,
)
from .format_word import format_word
from .format_string import format_string
from .format_non_gremlin import format_non_gremlin
from .format_method import format_method
from .format_closure import format_closure
from .traversal import format_traversal


def format_syntax_tree(config: GremlintInternalConfig, tree: UnformattedSyntaxTree) -> FormattedSyntaxTree:
    """Format a single syntax tree."""
    
    if tree.type == TokenType.NON_GREMLIN_CODE:
        return format_non_gremlin(config, tree)
    
    if tree.type == TokenType.TRAVERSAL:
        return format_traversal(format_syntax_tree, config, tree)
    
    if tree.type == TokenType.METHOD:
        return format_method(format_syntax_tree, config, tree)
    
    if tree.type == TokenType.CLOSURE:
        return format_closure(format_syntax_tree, config, tree)
    
    if tree.type == TokenType.STRING:
        return format_string(config, tree)
    
    if tree.type == TokenType.WORD:
        return format_word(config, tree)
    
    raise ValueError(f"Unknown token type: {tree.type}")


def format_syntax_trees(config: GremlintInternalConfig, trees: List[UnformattedSyntaxTree]) -> List[FormattedSyntaxTree]:
    """Format a list of syntax trees."""
    return [format_syntax_tree(config, tree) for tree in trees]
