# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Format traversal syntax trees."""

from typing import Callable, List

from ...types import (
    TokenType,
    GremlintInternalConfig,
    UnformattedSyntaxTree,
    UnformattedTraversalSyntaxTree,
    FormattedSyntaxTree,
    FormattedTraversalSyntaxTree,
    GremlinStepGroup,
)
from ...utils import pipe, last
from ...recreate_oneliner import recreate_query_oneliner
from ..utils import with_zero_indentation, with_increased_horizontal_position
from .step_groups import get_step_groups, is_traversal_source


def format_traversal(
    format_syntax_tree: Callable[[GremlintInternalConfig, UnformattedSyntaxTree], FormattedSyntaxTree],
    config: GremlintInternalConfig,
    tree: UnformattedTraversalSyntaxTree,
) -> FormattedTraversalSyntaxTree:
    """Format a traversal syntax tree."""
    
    # Calculate initial position increase for traversal source
    initial_pos_increase = 0
    if tree.steps and is_traversal_source(tree.steps[0]):
        initial_pos_increase = tree.initial_horizontal_position
    
    recreated = recreate_query_oneliner(tree, config.local_indentation + initial_pos_increase)
    
    # Check if traversal fits on one line
    if len(recreated) <= config.max_line_length:
        # All steps on same line
        formatted_steps: List[FormattedSyntaxTree] = []
        for i, step in enumerate(tree.steps):
            if i == 0:
                step_config = config
            else:
                prev_width = sum(s.width for s in formatted_steps) + len(formatted_steps)
                step_config = pipe(
                    with_zero_indentation,
                    with_increased_horizontal_position(tree.initial_horizontal_position + prev_width),
                )(config)
            formatted_steps.append(format_syntax_tree(step_config, step))
        
        return FormattedTraversalSyntaxTree(
            steps=tree.steps,
            step_groups=[GremlinStepGroup(steps=formatted_steps)],
            initial_horizontal_position=tree.initial_horizontal_position,
            local_indentation=0,
            width=len(recreated.strip()),
        )
    
    # Steps need to wrap
    step_groups = get_step_groups(format_syntax_tree, tree.steps, config)
    
    last_group = last(step_groups)
    width = sum(s.width for s in last_group.steps) + len(step_groups) - 1 if last_group else 0
    
    return FormattedTraversalSyntaxTree(
        steps=tree.steps,
        step_groups=step_groups,
        initial_horizontal_position=tree.initial_horizontal_position,
        local_indentation=0,
        width=width,
    )
