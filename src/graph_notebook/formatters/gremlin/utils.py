# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar('T')


def last(array: List[T]) -> Optional[T]:
    """Return the last element of a list, or None if empty."""
    return array[-1] if array else None


def pipe(*fns: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Compose functions left-to-right."""
    def piped(value: Any) -> Any:
        for fn in fns:
            value = fn(value)
        return value
    return piped


def spaces(n: int) -> str:
    """Return n spaces."""
    return ' ' * n


def eq(a: Any) -> Callable[[Any], bool]:
    """Return a function that checks equality with a."""
    return lambda b: a == b


def neq(a: Any) -> Callable[[Any], bool]:
    """Return a function that checks inequality with a."""
    return lambda b: a != b


def count(obj: Any) -> int:
    """Return length of object, or 0 if None."""
    if obj is None:
        return 0
    return len(obj) if hasattr(obj, '__len__') else 0


def choose(
    get_condition: Callable[..., Any],
    get_then: Callable[..., Any],
    get_else: Callable[..., Any]
) -> Callable[..., Any]:
    """Conditional function application."""
    def chooser(*params: Any) -> Any:
        if get_condition(*params):
            return get_then(*params)
        return get_else(*params)
    return chooser
