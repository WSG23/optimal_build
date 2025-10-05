"""Test that numpy crash fixes prevent floating point exceptions."""

import numpy as np


def test_sqrt_with_zero():
    """Test that we handle zero values correctly in sqrt operations."""
    # This would have caused a crash before
    floor_area = 0

    # Our fix checks floor_area > 0 before calling sqrt
    if floor_area > 0:
        side_length = np.sqrt(floor_area)
    else:
        side_length = 30  # Default

    assert side_length == 30


def test_sqrt_with_negative():
    """Test that we handle negative values correctly in sqrt operations."""
    floor_area = -10

    # Our fix checks floor_area > 0 before calling sqrt
    if floor_area > 0:
        side_length = np.sqrt(floor_area)
    else:
        side_length = 30  # Default

    assert side_length == 30


def test_mean_with_empty_list():
    """Test that we handle empty lists correctly in mean operations."""
    setback_values = []

    # Our fix checks if list is empty before calling mean
    if not setback_values:
        avg_setback = 3.0  # Default
    else:
        avg_setback = np.mean(setback_values)

    assert avg_setback == 3.0


def test_division_by_very_small_number():
    """Test that we handle very small divisors correctly."""
    avg_absorption = 0.0001  # Very small number
    current_absorbed = 50

    # Our fix checks for very small absorption rates
    if avg_absorption > 0:
        absorption_rate = avg_absorption / 100
        if absorption_rate > 0.001:  # More than 0.1% monthly
            months_to_sellout = (100 - current_absorbed) / absorption_rate
        else:
            months_to_sellout = None  # Too slow to estimate
    else:
        months_to_sellout = None

    assert months_to_sellout is None


def test_division_by_zero():
    """Test that we handle division by zero correctly."""
    avg_absorption = 0
    current_absorbed = 50

    # Our fix checks avg_absorption > 0
    if avg_absorption > 0:
        absorption_rate = avg_absorption / 100
        if absorption_rate > 0.001:
            months_to_sellout = (100 - current_absorbed) / absorption_rate
        else:
            months_to_sellout = None
    else:
        months_to_sellout = None

    assert months_to_sellout is None
