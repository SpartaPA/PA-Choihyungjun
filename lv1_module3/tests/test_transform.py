"""문제 5 — 동차변환 inv_T 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 것은 `inv_T` 검증이지만,
점/방향 구분과 벡터화, 최소자승까지 함께 검증해 두면 이후 문제에서 안전하다.

실행: 프로젝트 루트에서  pytest -v
"""

import numpy as np
import pytest

from src.rotation import rot_x, rot_y, rot_z
from src.transform import (
    inv_T,
    least_squares_normal_equation,
    make_T,
    transform_direction,
    transform_point,
    transform_points,
)


@pytest.fixture
def T():
    """테스트에 쓸 대표 동차변환 하나."""
    R = rot_z(0.9) @ rot_y(-0.35) @ rot_x(1.3)
    return make_T(R, [0.35, -0.15, 0.55])


def test_inv_T_gives_identity(T):
    # TODO: inv_T(T) @ T 와 T @ inv_T(T) 가 모두 4x4 단위행렬인지 검사
    T_inv = inv_T(T)
    I = np.eye(4)

    assert np.allclose(T_inv @ T, I, atol=1e-12)
    assert np.allclose(T @ T_inv, I, atol=1e-12)
        

def test_inv_T_matches_generic_inverse(T):
    # TODO: inv_T(T) 가 np.linalg.inv(T) 와 일치하는지 검사 (np.linalg 는 검산용)
    assert np.allclose(inv_T(T), np.linalg.inv(T), atol=1e-12)

def test_point_and_direction_differ(T):
    # TODO: 같은 벡터를 점(w=1)/방향(w=0)으로 변환하면 결과가 다르고,
    #       그 차이가 정확히 병진 벡터 T[:3, 3] 이며,
    #       방향 변환은 길이를 보존하는지 검사
    rng = np.random.default_rng(42)
    for v in rng.standard_normal((20, 3)):    
        p_out = transform_point(T, v)       # w=1: 회전+병진
        d_out = transform_direction(T, v)   # w=0: 회전만
        assert not np.allclose(p_out, d_out)                         
        assert np.allclose(p_out - d_out, T[:3, 3], atol=1e-12)      
        assert np.isclose(np.linalg.norm(d_out), np.linalg.norm(v))  



def test_transform_points_is_vectorized(T):
    # TODO: (N,3) 점군을 한 번에 변환한 결과가
    #       transform_point 를 반복문으로 돌린 결과와 같은지 검사
    rng = np.random.default_rng(42)
    P = rng.standard_normal((10, 3))
    out = transform_points(T, P)
    expected = np.array([transform_point(T, p) for p in P])
    assert out.shape == (10, 3)
    assert np.allclose(out, expected, atol=1e-12)

def test_roundtrip_through_inverse(T):
    # TODO: T 로 보냈다가 inv_T(T) 로 되돌리면 원래 점군이 나오는지 검사
    rng = np.random.default_rng(42)
    P = rng.standard_normal((10, 3))
    back = transform_points(inv_T(T), transform_points(T, P))
    assert np.allclose(back, P, atol=1e-10)


def test_least_squares_matches_lstsq():
    # TODO: 노이즈를 섞은 과결정 문제를 만들어
    #       least_squares_normal_equation 의 해가 np.linalg.lstsq 와 일치하고
    #       잔차가 A 의 열공간에 수직(A^T r = 0)인지 검사
    rng = np.random.default_rng(42)
    A = rng.standard_normal((50, 3))
    x_true = np.array([1.0, -2.0, 0.5])
    b = A @ x_true + 0.01 * rng.standard_normal(50)     # 과결정 + 노이즈
    x, residual = least_squares_normal_equation(A, b)
    x_ref, *_ = np.linalg.lstsq(A, b, rcond=None)       
    assert np.allclose(x, x_ref, atol=1e-8)             
    assert np.allclose(A.T @ residual, 0.0, atol=1e-8)  