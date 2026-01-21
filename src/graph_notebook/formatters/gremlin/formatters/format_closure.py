# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Format closure syntax trees."""

from typing import Callable, List

from ..types import (
    TokenType,
    GremlintInternalConfig,
    UnformattedSyntaxTree,
    UnformattedClosureSyntaxTree,
    UnformattedClosureLineOfCode,
    FormattedSyntaxTree,
    FormattedClosureSyntaxTree,
    FormattedClosureLineOfCode,
)
from ..recreate_oneliner import recreate_query_oneliner
from .utils import with_no_end_dot_info


def _get_closure_line_indentation(
    relative_indentation: int,
    horizontal_position: int,
    method_width: int,
    line_number: int,
) -> int:
    """Calculate indentation for a closure line."""
    if line_number == 0:
        return max(relative_indentation, 0)
    return max(relative_indentation + horizontal_position + method_width + 1, 0)


def _format_closure_code_block(
    code_block: List[UnformattedClosureLineOfCode],
    horizontal_position: int,
    method_width: int,
) -> List[FormattedClosureLineOfCode]:
    """Format closure code block lines."""
    return [
        FormattedClosureLineOfCode(
            line_of_code=line.line_of_code,
            relative_indentation=line.relative_indentation,
            local_indentation=_get_closure_line_indentation(
                line.relative_indentation,
                horizontal_position,
                method_width,
                i,
            ),
        )
        for i, line in enumerate(code_block)
    ]


def format_closure(
    format_syntax_tree: Callable[[GremlintInternalConfig, UnformattedSyntaxTree], FormattedSyntaxTree],
    config: GremlintInternalConfig,
    tree: UnformattedClosureSyntaxTree,
) -> FormattedClosureSyntaxTree:
    """Format a closure syntax tree."""
    
    recreated = recreate_query_oneliner(tree, config.local_indentation)
    method = format_syntax_tree(with_no_end_dot_info(config), tree.method)
    
    formatted_code_block = _format_closure_code_block(
        tree.closure_code_block,
        config.horizontal_position,
        method.width,
    )
    
    if len(recreated) <= config.max_line_length:
        return FormattedClosureSyntaxTree(
            method=method,
            closure_code_block=formatted_code_block,
            local_indentation=config.local_indentation,
            width=len(recreated.strip()),
            should_start_with_dot=False,
            should_end_with_dot=config.should_end_with_dot,
        )
    
    return FormattedClosureSyntaxTree(
        method=method,
        closure_code_block=formatted_code_block,
        local_indentation=0,
        width=0,
        should_start_with_dot=False,
        should_end_with_dot=config.should_end_with_dot,
    )
