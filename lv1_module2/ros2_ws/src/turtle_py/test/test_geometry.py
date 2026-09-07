import math

import pytest

from turtle_py.geometry import distance, normalize_angle, reached


def test_distance():
    # 정상: 3-4-5 직각삼각형
    assert distance(3.0, 4.0) == pytest.approx(5.0)
    # 경계: 목표와 같은 점 → 0
    assert distance(2.0, 2.0, 2.0, 2.0) == pytest.approx(0.0)


def test_normalize_angle():
    # 정상: 범위 안 값은 그대로
    assert normalize_angle(math.pi / 2) == pytest.approx(math.pi / 2)
    # 경계: 2pi 는 0 으로 래핑
    assert normalize_angle(2 * math.pi) == pytest.approx(0.0, abs=1e-9)
    # 예외적 큰 각: pi 를 넘으면 음수로 래핑
    assert normalize_angle(3 * math.pi / 2) == pytest.approx(-math.pi / 2)


def test_reached_boundary():
    # 경계값: 정확히 tolerance 면 도달로 인정
    assert reached(0.0, 0.35, 0.0, 0.0, 0.35) is True
    # 경계 바로 밖: 미도달
    assert reached(0.0, 0.36, 0.0, 0.0, 0.35) is False
