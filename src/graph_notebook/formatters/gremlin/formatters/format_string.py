# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Format string syntax trees."""

from ..types import (
    GremlintInternalConfig,
    UnformattedStringSyntaxTree,
    FormattedStringSyntaxTree,
)


def format_string(config: GremlintInternalConfig, tree: UnformattedStringSyntaxTree) -> FormattedStringSyntaxTree:
    """Format a string syntax tree."""
    return FormattedStringSyntaxTree(
        string=tree.string,
        local_indentation=config.local_indentation,
        width=len(tree.string),
    )
