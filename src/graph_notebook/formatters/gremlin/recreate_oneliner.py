# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Recreate query as single line from syntax tree (for width calculations)."""

from .types import (
    TokenType,
    UnformattedSyntaxTree,
    UnformattedTraversalSyntaxTree,
    UnformattedMethodSyntaxTree,
    UnformattedClosureSyntaxTree,
)
from .utils import spaces, last


def recreate_query_oneliner(tree: UnformattedSyntaxTree, local_indentation: int = 0) -> str:
    """Recreate a query as a single line string."""
    
    if tree.type == TokenType.NON_GREMLIN_CODE:
        return tree.code
    
    if tree.type == TokenType.TRAVERSAL:
        steps_str = '.'.join(recreate_query_oneliner(step) for step in tree.steps)
        return spaces(local_indentation) + steps_str
    
    if tree.type == TokenType.METHOD:
        method_str = recreate_query_oneliner(tree.method)
        args_str = ', '.join(recreate_query_oneliner(arg) for arg in tree.arguments)
        return spaces(local_indentation) + f'{method_str}({args_str})'
    
    if tree.type == TokenType.CLOSURE:
        method_str = recreate_query_oneliner(tree.method)
        # Get last line of closure code block
        last_line = last(tree.closure_code_block)
        if last_line:
            closure_content = spaces(max(last_line.relative_indentation, 0)) + last_line.line_of_code
        else:
            closure_content = ''
        return spaces(local_indentation) + f'{method_str}{{{closure_content}}}'
    
    if tree.type == TokenType.STRING:
        return spaces(local_indentation) + tree.string
    
    if tree.type == TokenType.WORD:
        return spaces(local_indentation) + tree.word
    
    return ''
