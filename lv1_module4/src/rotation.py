from __future__ import annotations

import numpy as np

from .vectors import as_vector ,det, normalize, skew

__all__ = [
    "rot_x",
    "rot_y",
    "rot_z",
    "rodrigues",
    "gram_schmidt",
    "orthogonality_error",
    "is_rotation",
    "axis_angle_from_matrix",
    "quaternion_from_axis_angle",
]


# ------------------------------------------------------------ 축별 회전 행렬

def rot_x(theta, d : bool=False) -> np.ndarray:
    """x축 기준 회전 행렬 (theta 는 **라디안**). x 성분은 보존된다."""
    if d:
        theta = np.radians(theta)

    c = np.cos(theta)
    s = np.sin(theta)

    R = np.array(
        [[1, 0, 0],
         [0, c, -s],
         [0, s, c]],dtype=float)
    return R


def rot_y(theta, d : bool=False) -> np.ndarray:
    """y축 기준 회전 행렬 (theta 는 라디안). y 성분은 보존된다.

    부호 배치가 x·z 와 반대로 보이는 이유는 노트북 2-1 에서 설명한다.
    """
    if d:
        theta = np.radians(theta)
    

    c = np.cos(theta)
    s = np.sin(theta)

    R = np.array(
        [[c, 0, s],
         [0, 1, 0],
         [-s, 0 ,c ]], dtype=float)
    return R

def rot_z(theta, d : bool=False) -> np.ndarray:
    """z축 기준 회전 행렬 (theta 는 라디안). z 성분은 보존된다."""
    if d:
        theta = np.radians(theta)

    c = np.cos(theta)
    s = np.sin(theta)

    R = np.array(
        [[c, -s, 0],
         [s, c, 0],
         [0, 0 ,1]], dtype=float)

    return R 


def rodrigues(axis, theta : float, d : bool = False) -> np.ndarray:
    """로드리게스 공식으로 임의 축 회전 행렬을 만든다.

        R = I + sin(theta) * K + (1 - cos(theta)) * K @ K,   K = [k]_x

    - 축은 함수 안에서 단위벡터로 정규화한다
      (정규화되지 않은 축을 넣어도 같은 결과가 나와야 한다).
    - 문제 1 의 `skew` 를 반드시 사용한다.
    """
    u = as_vector(axis)
    if u.shape[0] != 3:
        raise ValueError("3차원 행렬이 아님")

    u = normalize(u)
    I = np.eye(3)
    K = skew(u)

    if d:
        theta = np.radians(theta)
    rodrigues = I + np.sin(theta) * K + (1.0 - np.cos(theta)) * (K @ K)

    return rodrigues


# ------------------------------------------------------------- 재직교화 관련
def gram_schmidt(A, eps : float = 1e-14) -> np.ndarray:
    """**열벡터**에 대해 Gram-Schmidt 직교정규화를 수행한다.

        q1 = a1 / |a1|
        vj = aj - sum_{i<j} (qi · aj) qi
        qj = vj / |vj|

    각 열에서 앞선 열 방향 성분(정사영)을 빼고 정규화하는 것이며,
    문제 1 의 project / reject 와 같은 연산의 반복이다.

    수치적으로는 성분을 빼자마자 갱신하는 modified Gram-Schmidt 가 더 안정적이다.
    앞선 열들에 종속인 열이 있으면 ValueError.
    """
    A = np.asarray(A, dtype=float).copy()
    m, n = A.shape

    for i in range(n):
        norm = np.linalg.norm(A[:, i])
        if norm < eps:
            raise ValueError(f"{i}번째 열벡터가 선형 종속 또는 크기가 0")
        A[:, i] /= norm

        for j in range(i+1, n):
            proj = np.dot(A[:, i], A[:,  j])
            A[:, j] -= proj * A[:, i]
    return A


def orthogonality_error(R : np.ndarray) -> float:
    """직교성 이탈 지표: || R^T R - I ||_F  (프로베니우스 노름).

    완전한 직교행렬이면 0 이고, 클수록 직교성이 무너진 것이다.
    """
    R = np.asarray(R, dtype=float)
    I = np.eye(R.shape[0], dtype=float)

    # 프로베니우스 norm : R^T * R - I 
    return float(np.linalg.norm(R.T @ R - I))




def is_rotation(A, eps : float = 1e-14) -> bool:
    """회전행렬 판정: 직교(R^T R = I) **그리고** det(R) = +1 이면 True.

    det = -1 이면 직교이긴 하지만 반사가 섞여 있어 회전이 아니다.
    3x3 이 아니면 False.
    """
    A = np.asarray(A, dtype=float).copy()
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        return False

    n = A.shape[1]
    I = np.eye(n)
    # 직교성 확인
    if np.allclose(I, A.T @ A, atol=eps) != True:
        return False

    # 고유 회전 검사(det(A) = 1)
    proper_rotation = np.allclose(np.linalg.det(A), 1.0, atol=eps)

    return bool(proper_rotation)


    # --------------------------------------------------- 회전축·회전각·쿼터니언

def axis_angle_from_matrix(R, atol: float = 1e-8):
    """고유값 분해로 회전축을, 대각합으로 회전각을 복원한다.

    - 회전축은 고유값 1 에 대응하는 실수 고유벡터다 (R k = k).
      -> 여기서는 `np.linalg.eig` 를 써도 된다 (검산이 아니라 축 복원이 목적).
    - 회전각은 trace(R) = 1 + 2 cos(theta) 에서 구한다.
    - arccos 의 치역이 [0, pi] 라 '어느 쪽으로 도는지'는 알 수 없고,
      고유벡터도 부호가 정해지지 않는다. 반대칭 성분
      R - R^T = 2 sin(theta) [k]_x 를 이용해 부호를 맞춘다.
    - theta = 0 (회전 없음) 과 theta = pi (sin = 0) 는 따로 처리해야 한다.
      두 경우에 어떤 규약을 쓸지 정하고 주석으로 남긴다.

    Returns
    -------
    axis : 단위 회전축 (3,)
    angle : 회전각 [rad], 0 <= angle <= pi
    """
    R = np.asarray(R, dtype=float)
    if R.shape != (3, 3):
        raise ValueError(f"3x3 이 아님: {R.shape}")

    cos_t = np.clip((np.trace(R) - 1.0) / 2.0, -1.0, 1.0)   # tr(R) = 1 + 2 cos(theta)
    theta = float(np.arccos(cos_t))

    # theta = 0 : 회전이 없어 축이 정의되지 않는다. 규약상 +x 를 돌려준다.
    if theta < atol:
        return np.array([1.0, 0.0, 0.0]), 0.0

    # theta = pi : sin(theta)=0 이라 R - R^T = 0. 대신 R + I = 2 k k^T 를 쓴다.
    if np.pi - theta < atol:
        M = (R + np.eye(3)) / 2.0
        i = int(np.argmax(np.diag(M)))          # 가장 큰 대각 성분 기준으로 부호 고정
        k = normalize(M[:, i])
        for c in k:                             # 규약: 첫 비영 성분이 양수
            if abs(c) > atol:
                if c < 0:
                    k = -k
                break
        return k, np.pi

    # 일반: R - R^T = 2 sin(theta) [k]_x  -> 부호까지 결정된다
    k = np.array([R[2, 1] - R[1, 2],
                  R[0, 2] - R[2, 0],
                  R[1, 0] - R[0, 1]]) / (2.0 * np.sin(theta))
    return normalize(k), theta


def quaternion_from_axis_angle(axis, angle: float) -> np.ndarray:
    """축-각에서 단위 쿼터니언을 만든다.

        q = (k * sin(theta/2), cos(theta/2))

    반환 순서는 SciPy `Rotation.as_quat()` 와 같은 **(x, y, z, w)** 로 맞춘다
    (그래야 문제 6-5 에서 바로 비교할 수 있다).
    """
    k = normalize(as_vector(axis))
    h = angle / 2.0
    v = k * np.sin(h)
    return np.array([v[0], v[1], v[2], np.cos(h)])  