"""Tests for finscrape.market_data.calculate_market_boost."""

import pytest

from finscrape.market_data import calculate_market_boost


@pytest.mark.parametrize(
    "change_percent, expected",
    [
        (-12, -2),
        (12, 2),
        (6, 1),
        (-6, -1),
        (2, 0),
    ],
)
def test_single_move(change_percent, expected):
    assert calculate_market_boost([{"change_percent": change_percent}]) == expected


def test_empty_list():
    assert calculate_market_boost([]) == 0


def test_mixed_moves_biggest_mover_wins_with_its_own_sign():
    market_data = [{"change_percent": 11}, {"change_percent": -13}]
    assert calculate_market_boost(market_data) == -2
