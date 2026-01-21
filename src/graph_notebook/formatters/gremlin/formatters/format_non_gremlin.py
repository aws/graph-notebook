# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Format non-Gremlin code syntax trees."""

from ..types import (
    GremlintInternalConfig,
    UnformattedNonGremlinSyntaxTree,
    FormattedNonGremlinSyntaxTree,
)
from ..utils import last, count


def format_non_gremlin(config: GremlintInternalConfig, tree: UnformattedNonGremlinSyntaxTree) -> FormattedNonGremlinSyntaxTree:
    """Format a non-Gremlin code syntax tree."""
    last_line = last(tree.code.split('\n'))
    return FormattedNonGremlinSyntaxTree(
        code=tree.code,
        width=count(last_line),
    )
