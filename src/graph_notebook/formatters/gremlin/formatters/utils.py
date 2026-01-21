# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Config modifier utilities for formatters."""

from dataclasses import replace
from ..types import GremlintInternalConfig


def with_indentation(local_indentation: int):
    """Set local indentation."""
    def modifier(config: GremlintInternalConfig) -> GremlintInternalConfig:
        return replace(config, local_indentation=local_indentation)
    return modifier


def with_zero_indentation(config: GremlintInternalConfig) -> GremlintInternalConfig:
    """Set local indentation to 0."""
    return replace(config, local_indentation=0)


def with_increased_indentation(increase: int):
    """Increase local indentation."""
    def modifier(config: GremlintInternalConfig) -> GremlintInternalConfig:
        return replace(config, local_indentation=config.local_indentation + increase)
    return modifier


def with_dot_info(should_start_with_dot: bool, should_end_with_dot: bool):
    """Set dot placement info."""
    def modifier(config: GremlintInternalConfig) -> GremlintInternalConfig:
        return replace(config, 
                      should_start_with_dot=should_start_with_dot,
                      should_end_with_dot=should_end_with_dot)
    return modifier


def with_zero_dot_info(config: GremlintInternalConfig) -> GremlintInternalConfig:
    """Clear dot placement info."""
    return replace(config, should_start_with_dot=False, should_end_with_dot=False)


def with_no_end_dot_info(config: GremlintInternalConfig) -> GremlintInternalConfig:
    """Clear end dot info only."""
    return replace(config, should_end_with_dot=False)


def with_horizontal_position(position: int):
    """Set horizontal position."""
    def modifier(config: GremlintInternalConfig) -> GremlintInternalConfig:
        return replace(config, horizontal_position=position)
    return modifier


def with_increased_horizontal_position(increase: int):
    """Increase horizontal position."""
    def modifier(config: GremlintInternalConfig) -> GremlintInternalConfig:
        return replace(config, horizontal_position=config.horizontal_position + increase)
    return modifier
