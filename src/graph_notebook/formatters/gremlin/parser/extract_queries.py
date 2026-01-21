# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Extract Gremlin queries from mixed code."""

import re
from typing import List

# Unicode replacements for nested brackets/dots
LEFT_WHITE_PAREN = '⦅'
RIGHT_WHITE_PAREN = '⦆'
LEFT_WHITE_SQUARE = '⟦'
RIGHT_WHITE_SQUARE = '⟧'
LEFT_WHITE_CURLY = '⦃'
RIGHT_WHITE_CURLY = '⦄'
WHITE_DOT = '。'


def _encode_nested_brackets_and_dots(code: str) -> str:
    """Encode nested brackets and dots with unicode placeholders."""
    word = ''
    paren_count = 0
    square_count = 0
    curly_count = 0
    in_string = False

    for char in code:
        is_top_level = not in_string and not paren_count and not square_count and not curly_count

        if char == "'":
            in_string = not in_string
            word += char
        elif char == '.':
            word += '.' if is_top_level else WHITE_DOT
        elif char == '(':
            if not in_string:
                paren_count += 1
            word += '(' if is_top_level else LEFT_WHITE_PAREN
        elif char == ')':
            if not in_string:
                paren_count -= 1
            word += ')' if (not in_string and paren_count == 0 and not square_count and not curly_count) else RIGHT_WHITE_PAREN
        elif char == '[':
            if not in_string:
                square_count += 1
            word += '[' if is_top_level else LEFT_WHITE_SQUARE
        elif char == ']':
            if not in_string:
                square_count -= 1
            word += ']' if (not in_string and not paren_count and square_count == 0 and not curly_count) else RIGHT_WHITE_SQUARE
        elif char == '{':
            if not in_string:
                curly_count += 1
            word += '{' if is_top_level else LEFT_WHITE_CURLY
        elif char == '}':
            if not in_string:
                curly_count -= 1
            word += '}' if (not in_string and not paren_count and not square_count and curly_count == 0) else RIGHT_WHITE_CURLY
        else:
            word += char

    return word


def _decode_brackets_and_dots(code: str) -> str:
    """Decode unicode placeholders back to original characters."""
    return (code
            .replace(WHITE_DOT, '.')
            .replace(LEFT_WHITE_PAREN, '(')
            .replace(RIGHT_WHITE_PAREN, ')')
            .replace(LEFT_WHITE_SQUARE, '[')
            .replace(RIGHT_WHITE_SQUARE, ']')
            .replace(LEFT_WHITE_CURLY, '{')
            .replace(RIGHT_WHITE_CURLY, '}'))


# Regex components for Gremlin query matching
_SPACE = r'\s'
_HORIZONTAL_SPACE = r'[^\S\r\n]'
_DOT = r'\.'
_METHOD_STEP = rf'\w+{_HORIZONTAL_SPACE}*\([^\)]*\)'
_CLOSURE_STEP = rf'\w+{_HORIZONTAL_SPACE}*\{{[^\}}]*\}}'
_WORD_STEP = r'\w+'
_GREMLIN_STEP = rf'({_METHOD_STEP}|{_CLOSURE_STEP}|{_WORD_STEP})'
_STEP_CONNECTOR = rf'({_SPACE}*{_DOT}{_SPACE}*)'
_GREMLIN_QUERY = rf'g({_STEP_CONNECTOR}{_GREMLIN_STEP})+'

_GREMLIN_QUERY_PATTERN = re.compile(_GREMLIN_QUERY)


def extract_gremlin_queries(code: str) -> List[str]:
    """Extract Gremlin queries from mixed code."""
    encoded = _encode_nested_brackets_and_dots(code)
    matches = _GREMLIN_QUERY_PATTERN.findall(encoded)
    
    # findall returns tuples when there are groups, we need full matches
    full_matches = _GREMLIN_QUERY_PATTERN.finditer(encoded)
    queries = [match.group(0) for match in full_matches]
    
    return [_decode_brackets_and_dots(q) for q in queries]
