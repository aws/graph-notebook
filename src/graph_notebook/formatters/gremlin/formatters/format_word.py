# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Format word syntax trees."""

from ..types import (
    TokenType,
    GremlintInternalConfig,
    UnformattedWordSyntaxTree,
    FormattedWordSyntaxTree,
)


def format_word(config: GremlintInternalConfig, tree: UnformattedWordSyntaxTree) -> FormattedWordSyntaxTree:
    """Format a word syntax tree."""
    return FormattedWordSyntaxTree(
        word=tree.word,
        local_indentation=config.local_indentation,
        should_start_with_dot=config.should_start_with_dot,
        should_end_with_dot=config.should_end_with_dot,
        width=len(tree.word),
    )
