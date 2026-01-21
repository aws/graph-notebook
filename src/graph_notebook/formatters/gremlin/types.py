# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union, Callable


class TokenType(Enum):
    NON_GREMLIN_CODE = "NON_GREMLIN_CODE"
    TRAVERSAL = "TRAVERSAL"
    METHOD = "METHOD"
    CLOSURE = "CLOSURE"
    STRING = "STRING"
    WORD = "WORD"


# User-facing config
@dataclass
class GremlintConfig:
    indentation: int = 0
    max_line_length: int = 80
    should_place_dots_after_line_breaks: bool = True


# Internal config used during formatting
@dataclass
class GremlintInternalConfig:
    global_indentation: int
    local_indentation: int
    max_line_length: int
    should_place_dots_after_line_breaks: bool
    should_start_with_dot: bool
    should_end_with_dot: bool
    horizontal_position: int


# Unformatted syntax trees (output of parser)
@dataclass
class UnformattedClosureLineOfCode:
    line_of_code: str
    relative_indentation: int


@dataclass
class UnformattedNonGremlinSyntaxTree:
    type: TokenType = field(default=TokenType.NON_GREMLIN_CODE, init=False)
    code: str = ""


@dataclass
class UnformattedStringSyntaxTree:
    type: TokenType = field(default=TokenType.STRING, init=False)
    string: str = ""


@dataclass
class UnformattedWordSyntaxTree:
    type: TokenType = field(default=TokenType.WORD, init=False)
    word: str = ""


@dataclass
class UnformattedMethodSyntaxTree:
    type: TokenType = field(default=TokenType.METHOD, init=False)
    method: "UnformattedSyntaxTree" = None
    arguments: List["UnformattedSyntaxTree"] = field(default_factory=list)


@dataclass
class UnformattedClosureSyntaxTree:
    type: TokenType = field(default=TokenType.CLOSURE, init=False)
    method: "UnformattedSyntaxTree" = None
    closure_code_block: List[UnformattedClosureLineOfCode] = field(default_factory=list)


@dataclass
class UnformattedTraversalSyntaxTree:
    type: TokenType = field(default=TokenType.TRAVERSAL, init=False)
    steps: List["UnformattedSyntaxTree"] = field(default_factory=list)
    initial_horizontal_position: int = 0


UnformattedSyntaxTree = Union[
    UnformattedNonGremlinSyntaxTree,
    UnformattedTraversalSyntaxTree,
    UnformattedMethodSyntaxTree,
    UnformattedClosureSyntaxTree,
    UnformattedStringSyntaxTree,
    UnformattedWordSyntaxTree,
]


# Formatted syntax trees (output of formatters)
@dataclass
class FormattedClosureLineOfCode:
    line_of_code: str
    relative_indentation: int
    local_indentation: int


@dataclass
class FormattedNonGremlinSyntaxTree:
    type: TokenType = field(default=TokenType.NON_GREMLIN_CODE, init=False)
    code: str = ""
    width: int = 0


@dataclass
class FormattedStringSyntaxTree:
    type: TokenType = field(default=TokenType.STRING, init=False)
    string: str = ""
    width: int = 0
    local_indentation: int = 0


@dataclass
class FormattedWordSyntaxTree:
    type: TokenType = field(default=TokenType.WORD, init=False)
    word: str = ""
    local_indentation: int = 0
    width: int = 0
    should_start_with_dot: bool = False
    should_end_with_dot: bool = False


@dataclass
class FormattedMethodSyntaxTree:
    type: TokenType = field(default=TokenType.METHOD, init=False)
    method: "FormattedSyntaxTree" = None
    arguments: List[UnformattedSyntaxTree] = field(default_factory=list)
    argument_groups: List[List["FormattedSyntaxTree"]] = field(default_factory=list)
    arguments_should_start_on_new_line: bool = False
    local_indentation: int = 0
    width: int = 0
    should_start_with_dot: bool = False
    should_end_with_dot: bool = False


@dataclass
class FormattedClosureSyntaxTree:
    type: TokenType = field(default=TokenType.CLOSURE, init=False)
    method: "FormattedSyntaxTree" = None
    closure_code_block: List[FormattedClosureLineOfCode] = field(default_factory=list)
    local_indentation: int = 0
    width: int = 0
    should_start_with_dot: bool = False
    should_end_with_dot: bool = False


@dataclass
class GremlinStepGroup:
    steps: List["FormattedSyntaxTree"] = field(default_factory=list)


@dataclass
class FormattedTraversalSyntaxTree:
    type: TokenType = field(default=TokenType.TRAVERSAL, init=False)
    steps: List[UnformattedSyntaxTree] = field(default_factory=list)
    step_groups: List[GremlinStepGroup] = field(default_factory=list)
    initial_horizontal_position: int = 0
    local_indentation: int = 0
    width: int = 0


FormattedSyntaxTree = Union[
    FormattedNonGremlinSyntaxTree,
    FormattedTraversalSyntaxTree,
    FormattedMethodSyntaxTree,
    FormattedClosureSyntaxTree,
    FormattedStringSyntaxTree,
    FormattedWordSyntaxTree,
]

# Type alias for formatter functions
GremlinSyntaxTreeFormatter = Callable[[GremlintInternalConfig], Callable[[UnformattedSyntaxTree], FormattedSyntaxTree]]
