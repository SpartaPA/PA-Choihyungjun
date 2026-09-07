import numpy as np
import pytest

from src.rotation import (
    rot_x, 
    rot_y, 
    rot_z, 
    gram_schmidt, 
    is_rotation,
    orthogonality_error,
    rodrigues
) 

ANGLES = [0.0, np.pi / 6, np.pi / 4, np.pi / 2, 2.0, np.pi, -1.234]
MAKERS = [rot_x, rot_y, rot_z]
EPS = 1e-14

@pytest.fixture
def rng():
    """난수는 반드시 시드를 고정한다."""
    return np.random.default_rng(42)

# --- 1. 열이 서로 직교하는 단위벡터인가 -------------------------------------

@pytest.mark.parametrize("maker", MAKERS)
@pytest.mark.parametrize("theta", ANGLES)
def test_columns_are_orthonormal(maker, theta):
    R = maker(theta)
    n = R.shape[0]
    I = np.eye(n)

    # 각 열의 길이가 1인지
    col_norm = np.linalg.norm(R, axis=0)
    assert np.allclose(col_norm, 1.0, atol=1e-12)

    # 각 열이 서로 직교하는지
    assert np.allclose(R.T @ R, I, atol=1e-12)


# --- 2. 행렬식이 1인가 --------------------------------------------------------

@pytest.mark.parametrize("maker", MAKERS)
@pytest.mark.parametrize("theta", ANGLES)
def test_determinant_is_one(maker, theta):
    R = maker(theta)
    det = np.linalg.det(R)
    assert np.isclose(det, 1.0, atol=1e-12)


# --- 3. 역행렬 == 전치 --------------------------------------------------------

@pytest.mark.parametrize("maker", MAKERS)
@pytest.mark.parametrize("theta", ANGLES)
def test_inverse_equals_transpose(maker, theta):
    R = maker(theta)
    R_inv = np.linalg.inv(R)
    R_T = R.T  # [수정] R_inv 가 아닌 실제 전치 행렬 R.T 취득

    # inv(R) == R.T 검증
    assert np.allclose(R_inv, R_T, atol=1e-12)
    # R.T @ R == I 검증
    assert np.allclose(R_T @ R, np.eye(3), atol=1e-12)


# --- 4. 재직교화 결과가 직교행렬인가 -----------------------------------------

def test_gram_schmidt_restores_orthogonality(rng):
    theta = rng.uniform(-np.pi, np.pi)
    R_clean = rot_z(theta)

    noise = rng.normal(0.0, 1e-3, size=R_clean.shape)
    R_noisy = R_clean + noise
    
    assert orthogonality_error(R_noisy) > 1e-4
    
    R_restored = gram_schmidt(R_noisy)
    
    assert orthogonality_error(R_restored) < 1e-12
    assert np.isclose(np.linalg.det(R_restored), 1.0, atol=1e-12)  
    assert is_rotation(R_restored)