"""Numeric validation shared by source edits and geometry."""

import math


def finite(value, name):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(name + " must be a finite number")
    return value


def positive(value, name):
    if finite(value, name) <= 0:
        raise ValueError(name + " must be positive")
    return value
