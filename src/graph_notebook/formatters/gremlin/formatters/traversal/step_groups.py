# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Step grouping logic for traversal formatting."""

from typing import Callable, List, Dict, Any

from ...types import (
    TokenType,
    GremlintInternalConfig,
    UnformattedSyntaxTree,
    FormattedSyntaxTree,
    GremlinStepGroup,
)
from ...consts import STEP_MODULATORS
from ...utils import pipe
from ...recreate_oneliner import recreate_query_oneliner
from ..utils import (
    with_indentation,
    with_zero_indentation,
    with_dot_info,
    with_horizontal_position,
    with_increased_horizontal_position,
)


def is_traversal_source(step: UnformattedSyntaxTree) -> bool:
    """Check if step is 'g' (traversal source)."""
    return step.type == TokenType.WORD and step.word == 'g'


def is_modulator(step: UnformattedSyntaxTree) -> bool:
    """Check if step is a modulator (by, as, from, etc.)."""
    if step.type not in (TokenType.METHOD, TokenType.CLOSURE):
        return False
    if step.method.type != TokenType.WORD:
        return False
    return step.method.word in STEP_MODULATORS


def _is_line_too_long_with_modulators(
    config: GremlintInternalConfig,
    steps_in_group: List[FormattedSyntaxTree],
    step_groups: List[GremlinStepGroup],
    step: UnformattedSyntaxTree,
    index: int,
    steps: List[UnformattedSyntaxTree],
) -> bool:
    """Check if line would be too long including subsequent modulators."""
    # Collect subsequent modulators
    subsequent_steps = [step]
    for s in steps[index + 1:]:
        if is_modulator(s):
            subsequent_steps.append(s)
        else:
            break
    
    # Calculate indentation
    traversal_indent = 2 if (step_groups and is_traversal_source(step_groups[0].steps[0])) else 0
    modulator_indent = 2 if (steps_in_group or is_modulator(step)) and is_modulator(subsequent_steps[0]) else 0
    total_indent = config.local_indentation + traversal_indent + modulator_indent
    
    # Create temporary traversal to measure
    from ...types import UnformattedTraversalSyntaxTree
    temp_traversal = UnformattedTraversalSyntaxTree(steps=subsequent_steps)
    recreated = recreate_query_oneliner(temp_traversal, total_indent)
    
    return len(recreated) > config.max_line_length


def _should_be_last_in_group(
    config: GremlintInternalConfig,
    steps_in_group: List[FormattedSyntaxTree],
    step_groups: List[GremlinStepGroup],
    step: UnformattedSyntaxTree,
    index: int,
    steps: List[UnformattedSyntaxTree],
) -> bool:
    """Determine if step should be the last in its group."""
    is_first_in_group = len(steps_in_group) == 0
    is_last_step = index == len(steps) - 1
    next_is_modulator = not is_last_step and is_modulator(steps[index + 1])
    
    line_too_long = _is_line_too_long_with_modulators(
        config, steps_in_group, step_groups, step, index, steps
    )
    
    # If first step in group is modulator, it must also be last
    if is_last_step:
        return True
    if is_first_in_group and is_modulator(step):
        return True
    if step.type in (TokenType.METHOD, TokenType.CLOSURE):
        if not (next_is_modulator and not line_too_long):
            return True
    
    return False


def get_step_groups(
    format_syntax_tree: Callable[[GremlintInternalConfig, UnformattedSyntaxTree], FormattedSyntaxTree],
    steps: List[UnformattedSyntaxTree],
    config: GremlintInternalConfig,
) -> List[GremlinStepGroup]:
    """Group steps into step groups for line wrapping."""
    
    steps_in_group: List[FormattedSyntaxTree] = []
    step_groups: List[GremlinStepGroup] = []
    
    for index, step in enumerate(steps):
        is_first_in_group = len(steps_in_group) == 0
        should_be_last = _should_be_last_in_group(
            config, steps_in_group, step_groups, step, index, steps
        )
        
        # Calculate indentation
        traversal_indent = 2 if (step_groups and is_traversal_source(step_groups[0].steps[0])) else 0
        modulator_indent = 2 if is_modulator(step) else 0
        local_indent = config.local_indentation + traversal_indent + modulator_indent
        
        is_first_group = len(step_groups) == 0
        is_last_step = index == len(steps) - 1
        
        if is_first_in_group and should_be_last:
            # Single step in group
            should_start = not is_first_group and config.should_place_dots_after_line_breaks
            should_end = not is_last_step and not config.should_place_dots_after_line_breaks
            
            step_config = pipe(
                with_indentation(local_indent),
                with_dot_info(should_start, should_end),
                with_horizontal_position(local_indent + int(config.should_place_dots_after_line_breaks)),
            )(config)
            
            step_groups.append(GremlinStepGroup(
                steps=[format_syntax_tree(step_config, step)]
            ))
            steps_in_group = []
            
        elif is_first_in_group:
            # First step in group (not last)
            should_start = not is_first_group and config.should_place_dots_after_line_breaks
            
            step_config = pipe(
                with_indentation(local_indent),
                with_dot_info(should_start, False),
                with_horizontal_position(local_indent),
            )(config)
            
            steps_in_group = [format_syntax_tree(step_config, step)]
            
        elif should_be_last:
            # Last step in group (not first)
            should_end = not is_last_step and not config.should_place_dots_after_line_breaks
            
            h_pos = config.local_indentation + sum(s.width for s in steps_in_group) + len(steps_in_group)
            step_config = pipe(
                with_zero_indentation,
                with_dot_info(False, should_end),
                with_increased_horizontal_position(sum(s.width for s in steps_in_group) + len(steps_in_group)),
            )(config)
            
            step_groups.append(GremlinStepGroup(
                steps=steps_in_group + [format_syntax_tree(step_config, step)]
            ))
            steps_in_group = []
            
        else:
            # Middle step in group
            h_pos = config.local_indentation + sum(s.width for s in steps_in_group) + len(steps_in_group)
            step_config = pipe(
                with_zero_indentation,
                with_dot_info(False, False),
                with_horizontal_position(h_pos),
            )(config)
            
            steps_in_group.append(format_syntax_tree(step_config, step))
    
    return step_groups
