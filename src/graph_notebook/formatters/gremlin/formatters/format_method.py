# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Format method syntax trees."""

from typing import Callable

from ..types import (
    TokenType,
    GremlintInternalConfig,
    UnformattedSyntaxTree,
    UnformattedMethodSyntaxTree,
    FormattedSyntaxTree,
    FormattedMethodSyntaxTree,
)
from ..utils import pipe, last
from ..recreate_oneliner import recreate_query_oneliner
from .utils import (
    with_zero_indentation,
    with_zero_dot_info,
    with_no_end_dot_info,
    with_increased_indentation,
    with_horizontal_position,
    with_increased_horizontal_position,
)


def format_method(
    format_syntax_tree: Callable[[GremlintInternalConfig, UnformattedSyntaxTree], FormattedSyntaxTree],
    config: GremlintInternalConfig,
    tree: UnformattedMethodSyntaxTree,
) -> FormattedMethodSyntaxTree:
    """Format a method syntax tree."""
    
    recreated = recreate_query_oneliner(tree, config.local_indentation)
    method = format_syntax_tree(with_no_end_dot_info(config), tree.method)
    
    # Check if arguments will fit on one line
    if len(recreated) <= config.max_line_length:
        # Arguments on same line
        argument_group = []
        for i, arg in enumerate(tree.arguments):
            # Calculate horizontal position for each argument
            prev_width = sum(a.width for a in argument_group) + len(argument_group)
            arg_config = pipe(
                with_zero_indentation,
                with_zero_dot_info,
                with_increased_horizontal_position(method.width + 1 + prev_width),
            )(config)
            argument_group.append(format_syntax_tree(arg_config, arg))
        
        return FormattedMethodSyntaxTree(
            method=method,
            arguments=tree.arguments,
            argument_groups=[argument_group] if argument_group else [],
            arguments_should_start_on_new_line=False,
            local_indentation=config.local_indentation,
            should_start_with_dot=False,
            should_end_with_dot=config.should_end_with_dot,
            width=len(recreated.strip()),
        )
    
    # Arguments need to wrap - each on its own line
    argument_groups = []
    for arg in tree.arguments:
        arg_config = pipe(
            with_increased_indentation(2),
            with_zero_dot_info,
            with_horizontal_position(config.local_indentation + 2),
        )(config)
        argument_groups.append([format_syntax_tree(arg_config, arg)])
    
    # Calculate width from last argument group
    last_group = last(argument_groups)
    width = sum(a.width for a in last_group) + len(last_group) - 1 if last_group else 0
    
    return FormattedMethodSyntaxTree(
        method=method,
        arguments=tree.arguments,
        argument_groups=argument_groups,
        arguments_should_start_on_new_line=True,
        local_indentation=0,
        should_start_with_dot=False,
        should_end_with_dot=config.should_end_with_dot,
        width=width,
    )
