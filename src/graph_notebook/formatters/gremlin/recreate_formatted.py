# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Recreate formatted query string from formatted syntax trees."""

from typing import List

from .types import (
    TokenType,
    GremlintInternalConfig,
    FormattedSyntaxTree,
)
from .utils import spaces


def _recreate_from_tree(tree: FormattedSyntaxTree) -> str:
    """Recreate query string from a single formatted syntax tree."""
    
    if tree.type == TokenType.NON_GREMLIN_CODE:
        return tree.code
    
    if tree.type == TokenType.TRAVERSAL:
        lines = []
        for group in tree.step_groups:
            line = '.'.join(_recreate_from_tree(step) for step in group.steps)
            lines.append(line)
        return '\n'.join(lines)
    
    if tree.type == TokenType.METHOD:
        start_dot = '.' if tree.should_start_with_dot else ''
        end_dot = '.' if tree.should_end_with_dot else ''
        
        method_str = _recreate_from_tree(tree.method)
        
        # Format argument groups
        arg_lines = []
        for arg_group in tree.argument_groups:
            arg_line = ', '.join(_recreate_from_tree(arg) for arg in arg_group)
            arg_lines.append(arg_line)
        
        args_str = ',\n'.join(arg_lines)
        
        if tree.arguments_should_start_on_new_line:
            return f'{start_dot}{method_str}(\n{args_str}){end_dot}'
        else:
            return f'{start_dot}{method_str}({args_str}){end_dot}'
    
    if tree.type == TokenType.CLOSURE:
        start_dot = '.' if tree.should_start_with_dot else ''
        end_dot = '.' if tree.should_end_with_dot else ''
        
        method_str = _recreate_from_tree(tree.method)
        
        closure_lines = []
        for line in tree.closure_code_block:
            closure_lines.append(f'{spaces(line.local_indentation)}{line.line_of_code}')
        closure_str = '\n'.join(closure_lines)
        
        return f'{start_dot}{method_str}{{{closure_str}}}{end_dot}'
    
    if tree.type == TokenType.STRING:
        return spaces(tree.local_indentation) + tree.string
    
    if tree.type == TokenType.WORD:
        start_dot = '.' if tree.should_start_with_dot else ''
        end_dot = '.' if tree.should_end_with_dot else ''
        return f'{spaces(tree.local_indentation)}{start_dot}{tree.word}{end_dot}'
    
    return ''


def _is_empty_line(line: str) -> bool:
    """Check if line contains only whitespace."""
    return all(c == ' ' for c in line)


def recreate_query_string(config: GremlintInternalConfig, trees: List[FormattedSyntaxTree]) -> str:
    """Recreate the final formatted query string."""
    # Join all trees
    result = ''.join(_recreate_from_tree(tree) for tree in trees)
    
    # Apply global indentation and clean up empty lines
    lines = []
    for line in result.split('\n'):
        if _is_empty_line(line):
            lines.append('')
        elif line:
            lines.append(spaces(config.global_indentation) + line)
        else:
            lines.append(line)
    
    return '\n'.join(lines)
