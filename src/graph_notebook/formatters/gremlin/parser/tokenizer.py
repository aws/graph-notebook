# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tokenization functions for Gremlin queries."""

from typing import List

SEPARATOR = chr(28)  # File separator character used as internal delimiter


def tokenize_on_top_level_punctuation(query: str) -> List[str]:
    """Split query on top-level dots (outside brackets/strings)."""
    word = ''
    paren_count = 0
    square_count = 0
    curly_count = 0
    in_string = False

    for char in query:
        if char == "'" and not in_string:
            in_string = True
            word += char
        elif char == "'" and in_string:
            in_string = False
            word += char
        elif char == '(' and not in_string:
            paren_count += 1
            word += char
        elif char == ')' and not in_string:
            paren_count -= 1
            word += char
        elif char == '[' and not in_string:
            square_count += 1
            word += char
        elif char == ']' and not in_string:
            square_count -= 1
            word += char
        elif char == '{' and not in_string:
            curly_count += 1
            word += char
        elif char == '}' and not in_string:
            curly_count -= 1
            word += char
        elif char == '.':
            if in_string or paren_count or square_count or curly_count:
                word += '.'
            else:
                word += SEPARATOR
        else:
            word += char

    return [t.strip() for t in word.split(SEPARATOR) if t.strip()]


def tokenize_on_top_level_comma(query: str) -> List[str]:
    """Split query on top-level commas (outside brackets/strings)."""
    word = ''
    paren_count = 0
    square_count = 0
    curly_count = 0
    in_string = False

    for char in query:
        if char == "'" and not in_string:
            in_string = True
            word += char
        elif char == "'" and in_string:
            in_string = False
            word += char
        elif char == '(' and not in_string:
            paren_count += 1
            word += char
        elif char == ')' and not in_string:
            paren_count -= 1
            word += char
        elif char == '[' and not in_string:
            square_count += 1
            word += char
        elif char == ']' and not in_string:
            square_count -= 1
            word += char
        elif char == '{' and not in_string:
            curly_count += 1
            word += char
        elif char == '}' and not in_string:
            curly_count -= 1
            word += char
        elif char == ',':
            if in_string or paren_count or square_count or curly_count:
                word += ','
            else:
                word += SEPARATOR
        else:
            word += char

    return [t.strip() for t in word.split(SEPARATOR) if t.strip()]


def tokenize_on_top_level_parentheses(query: str) -> List[str]:
    """Split query before top-level opening parentheses."""
    word = ''
    paren_count = 0
    square_count = 0
    curly_count = 0
    in_string = False

    for char in query:
        if char == "'" and not in_string:
            in_string = True
            word += char
        elif char == "'" and in_string:
            in_string = False
            word += char
        elif char == '(' and not in_string:
            if paren_count == 0:
                word += SEPARATOR
            paren_count += 1
            word += char
        elif char == ')' and not in_string:
            paren_count -= 1
            word += char
        elif char == '[' and not in_string:
            square_count += 1
            word += char
        elif char == ']' and not in_string:
            square_count -= 1
            word += char
        elif char == '{' and not in_string:
            curly_count += 1
            word += char
        elif char == '}' and not in_string:
            curly_count -= 1
            word += char
        else:
            word += char

    return [t.strip() for t in word.split(SEPARATOR) if t.strip()]


def tokenize_on_top_level_curly_brackets(query: str) -> List[str]:
    """Split query before top-level opening curly brackets."""
    word = ''
    paren_count = 0
    square_count = 0
    curly_count = 0
    in_string = False

    for char in query:
        if char == "'" and not in_string:
            in_string = True
            word += char
        elif char == "'" and in_string:
            in_string = False
            word += char
        elif char == '(' and not in_string:
            paren_count += 1
            word += char
        elif char == ')' and not in_string:
            paren_count -= 1
            word += char
        elif char == '[' and not in_string:
            square_count += 1
            word += char
        elif char == ']' and not in_string:
            square_count -= 1
            word += char
        elif char == '{' and not in_string:
            if curly_count == 0:
                word += SEPARATOR
            curly_count += 1
            word += char
        elif char == '}' and not in_string:
            curly_count -= 1
            word += char
        else:
            word += char

    return [t.strip() for t in word.split(SEPARATOR) if t.strip()]


def is_wrapped_in_parentheses(token: str) -> bool:
    """Check if token is wrapped in parentheses."""
    return len(token) >= 2 and token[0] == '(' and token[-1] == ')'


def is_wrapped_in_curly_brackets(token: str) -> bool:
    """Check if token is wrapped in curly brackets."""
    return len(token) >= 2 and token[0] == '{' and token[-1] == '}'


def is_string(token: str) -> bool:
    """Check if token is a string literal."""
    if len(token) < 2:
        return False
    return token[0] == token[-1] and token[0] in ('"', "'")
