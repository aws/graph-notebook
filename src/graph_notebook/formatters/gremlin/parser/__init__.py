# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Parse Gremlin code into syntax trees."""

from typing import List, Callable

from ..types import (
    TokenType,
    UnformattedSyntaxTree,
    UnformattedNonGremlinSyntaxTree,
    UnformattedTraversalSyntaxTree,
    UnformattedMethodSyntaxTree,
    UnformattedClosureSyntaxTree,
    UnformattedStringSyntaxTree,
    UnformattedWordSyntaxTree,
    UnformattedClosureLineOfCode,
)
from ..utils import last, pipe
from .tokenizer import (
    tokenize_on_top_level_punctuation,
    tokenize_on_top_level_comma,
    tokenize_on_top_level_parentheses,
    tokenize_on_top_level_curly_brackets,
    is_wrapped_in_parentheses,
    is_wrapped_in_curly_brackets,
    is_string,
)
from .extract_queries import extract_gremlin_queries


def _is_method_invocation(token: str) -> bool:
    """Check if token is a method invocation like foo()."""
    tokens = tokenize_on_top_level_parentheses(token)
    last_token = last(tokens)
    return last_token is not None and is_wrapped_in_parentheses(last_token)


def _is_closure_invocation(token: str) -> bool:
    """Check if token is a closure invocation like foo{}."""
    tokens = tokenize_on_top_level_curly_brackets(token)
    last_token = last(tokens)
    return last_token is not None and is_wrapped_in_curly_brackets(last_token)


def _trim_parentheses(expr: str) -> str:
    """Remove outer parentheses."""
    return expr[1:-1]


def _trim_curly_brackets(expr: str) -> str:
    """Remove outer curly brackets."""
    return expr[1:-1]


def _get_indentation(line: str) -> int:
    """Get number of leading spaces."""
    for i, char in enumerate(line):
        if char != ' ':
            return i
    return -1


def _get_method_and_args(token: str):
    """Extract method token and argument tokens from method invocation."""
    tokens = tokenize_on_top_level_parentheses(token)
    method_token = ''.join(tokens[:-1])
    arg_tokens = tokenize_on_top_level_comma(_trim_parentheses(tokens[-1]))
    return method_token, arg_tokens


def _get_method_and_closure(token: str, full_query: str):
    """Extract method token and closure code block from closure invocation."""
    tokens = tokenize_on_top_level_curly_brackets(token)
    method_token = ''.join(tokens[:-1])
    closure_content = _trim_curly_brackets(tokens[-1])
    
    # Calculate initial indentation
    idx = full_query.find(closure_content)
    prefix = full_query[:idx] if idx >= 0 else ''
    initial_indent = len(prefix.split('\n')[-1])
    
    lines = closure_content.split('\n')
    closure_block = []
    for i, line in enumerate(lines):
        indent = _get_indentation(line)
        if i == 0:
            rel_indent = max(indent, 0)
        else:
            rel_indent = indent - initial_indent if indent >= 0 else 0
        closure_block.append(UnformattedClosureLineOfCode(
            line_of_code=line.lstrip(),
            relative_indentation=rel_indent
        ))
    
    return method_token, closure_block


def _parse_code_block(full_code: str, calc_initial_pos: bool = False) -> Callable[[str], UnformattedSyntaxTree]:
    """Return a parser function for code blocks."""
    
    def parser(code_block: str) -> UnformattedSyntaxTree:
        tokens = tokenize_on_top_level_punctuation(code_block)
        
        if len(tokens) == 1:
            token = tokens[0]
            
            if _is_method_invocation(token):
                method_token, arg_tokens = _get_method_and_args(token)
                return UnformattedMethodSyntaxTree(
                    method=_parse_code_block(full_code)(method_token),
                    arguments=[_parse_code_block(full_code)(arg) for arg in arg_tokens]
                )
            
            if _is_closure_invocation(token):
                method_token, closure_block = _get_method_and_closure(token, full_code)
                return UnformattedClosureSyntaxTree(
                    method=_parse_code_block(full_code)(method_token),
                    closure_code_block=closure_block
                )
            
            if is_string(token):
                return UnformattedStringSyntaxTree(string=token)
            
            return UnformattedWordSyntaxTree(word=token)
        
        # Multiple tokens = traversal
        initial_pos = 0
        if calc_initial_pos:
            idx = full_code.find(code_block)
            if idx >= 0:
                initial_pos = len(full_code[:idx].split('\n')[-1])
        
        return UnformattedTraversalSyntaxTree(
            steps=[_parse_code_block(full_code)(t) for t in tokens],
            initial_horizontal_position=initial_pos
        )
    
    return parser


def _parse_non_gremlin(code: str) -> UnformattedNonGremlinSyntaxTree:
    """Create a non-Gremlin syntax tree."""
    return UnformattedNonGremlinSyntaxTree(code=code)


def parse_to_syntax_trees(code: str) -> List[UnformattedSyntaxTree]:
    """Parse code into a list of syntax trees."""
    queries = extract_gremlin_queries(code)
    
    syntax_trees: List[UnformattedSyntaxTree] = []
    remaining = code
    
    for query in queries:
        idx = remaining.find(query)
        if idx > 0:
            syntax_trees.append(_parse_non_gremlin(remaining[:idx]))
        syntax_trees.append(_parse_code_block(code, True)(query))
        remaining = remaining[idx + len(query):]
    
    if remaining:
        syntax_trees.append(_parse_non_gremlin(remaining))
    
    return syntax_trees
