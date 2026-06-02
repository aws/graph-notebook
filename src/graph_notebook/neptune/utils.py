"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import ast
import json
from functools import singledispatch


@singledispatch
def serialize_query_params(query_params):
    """Serialize query parameters into a valid JSON string for Neptune.

    Dispatches based on input type:
        - dict: Serializes directly via json.dumps.
        - str: Validates as JSON and passes through, or parses as a Python
          dict literal and converts to JSON.

    Args:
        query_params: Query parameters as a dict, JSON string, or Python
            dict literal string.

    Returns:
        A valid JSON string, or None if the input cannot be parsed.
    """
    return None


@serialize_query_params.register(dict)
def _(query_params):
    """Serialize a dict to a JSON string."""
    return json.dumps(query_params)


@serialize_query_params.register(str)
def _(query_params):
    """Validate a JSON string or parse a Python dict literal string to JSON."""
    try:
        json.loads(query_params)
        return query_params
    except (json.JSONDecodeError, ValueError):
        try:
            return json.dumps(ast.literal_eval(query_params))
        except Exception:
            return None
