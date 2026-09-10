from __future__ import annotations

import numpy as np

from .vectors import inverse_gauss_jordan

__all__ = [
    "make_T",
    "inv_T",
    "inv_T_batch",
    "to_homogeneous",
    "transform_point",
    "transform_direction",
    "transform_points",
    "least_squares_normal_equation",
    "rmse",
]


def make_T(R, t) -> np.ndarray:
    """회전 R(3x3)과 병진 t(3,)로 4x4 동차변환을 만든다.

        T = [[R, t],
             [0, 1]]

    R 이 3x3 이 아니면 ValueError.
    """
    R = np.asarray(R)
    t = np.asarray(t)

    if R.shape != (3,3):
        raise ValueError("R이 3x3이 아님")
    if t.size != 3:
        raise ValueError("t 원소가 3개가 아님")

    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t.ravel()

    return T


def inv_T(T) -> np.ndarray:
    """동차변환의 역변환. **일반 역행렬 함수를 쓰지 않고** 공식으로 구한다.

        T^-1 = [[R^T, -R^T t],
                [  0,      1]]

    유도: T^-1 을 [[S, u], [0, 1]] 로 두고 T T^-1 = I 를 풀면
          R S = I -> S = R^T (R 이 직교),  R u + t = 0 -> u = -R^T t.

    4x4 가 아니면 ValueError.
    """
    T = np.asarray(T)

    if T.shape != (4, 4):
        raise ValueError("4x4 행렬 아님")

    R = T[:3, :3]
    t = T[:3, 3]

    R_T = R.T
    u = - R_T @ t 

    T_inv = np.eye(4)
    T_inv[:3, :3] = R.T
    T_inv[:3, 3] = u

    return T_inv

def inv_T_batch(Ts) -> np.ndarray:
    """(N, 4, 4) 동차변환 묶음을 **반복문 없이** 한 번에 역변환한다.

    `inv_T` 와 같은 공식을 배치 축으로 확장한 것이다.
    문제 5-4 의 속도 비교에서 쓴다 — 단건 호출은 파이썬/NumPy 호출 오버헤드가
    지배해서 연산량 차이가 드러나지 않기 때문이다.

    힌트: 전치는 `np.swapaxes(..., 1, 2)`, 배치 행렬-벡터 곱은
          `np.einsum("nij,nj->ni", ...)` 로 쓸 수 있다.
    """
    Ts = np.asarray(Ts, dtype=float)
    if Ts.ndim != 3 or Ts.shape[1:] != (4, 4):
        raise ValueError("(N, 4, 4) 형태의 배열이 아닙니다.")

    R = Ts[:, :3, :3]
    t = Ts[:, :3, 3]

    R_T = np.swapaxes(R, 1, 2)
    u = -np.einsum("nij,nj->ni", R_T, t)

    T_inv = np.zeros_like(Ts)
    T_inv[:, :3, :3] = R_T
    T_inv[:, :3, 3] = u
    T_inv[:, 3, 3] = 1.0

    return T_inv


def to_homogeneous(P, w: float = 1.0) -> np.ndarray:
    """(3,) 또는 (N,3) 좌표에 마지막 성분 w 를 붙인다.

    w = 1 이면 점(위치), w = 0 이면 방향(벡터).
    """
    P = np.asarray(P, dtype=float)
    if P.ndim == 1:
        return np.append(P, w)
    elif P.ndim == 2:
        N = P.shape[0]
        col = np.full((N, 1), w, dtype=float)
        return np.hstack([P, col])
    else:
        raise ValueError("1차원 또는 2차원 배열만 지원합니다.")

def transform_point(T, p) -> np.ndarray:
    """점 변환 (w = 1): 회전과 병진이 모두 적용된다. 반환은 (3,)."""
    T = np.asarray(T, dtype=float)
    p = np.asarray(p, dtype=float)

    p_hom = to_homogeneous(p)
    res = (T @ p_hom.T).T

    return res[..., :3] / res[..., 3:]

def transform_direction(T, v) -> np.ndarray:
    """방향 변환 (w = 0): 회전만 적용되고 병진은 무시된다. 반환은 (3,)."""
    T = np.asarray(T, dtype=float)
    v = np.asarray(v, dtype=float)

    v_hom = to_homogeneous(v, 0.0)
    res = T @ v_hom

    return res[:3]
    

def transform_points(T, P, w: float = 1.0) -> np.ndarray:
    """(N,3) 점군을 **반복문 없이** 한 번에 변환한다. (3,) 입력도 받아야 한다.

    힌트: (T @ P_h.T).T 대신 P_h @ T.T 를 쓰면 전치가 한 번으로 끝나고
          메모리 접근도 행 방향이라 캐시에 유리하다.
    """
    T = np.asarray(T, dtype=float)
    P = np.asarray(P, dtype=float)
    P_h = to_homogeneous(P, w)        
    res = P_h @ T.T                    

    return res[..., :3] / res[..., 3:]


def least_squares_normal_equation(A, b):
    """정규방정식 (A^T A) x = A^T b 를 직접 세워 최소자승해를 구한다.

    - (A^T A) 의 역행렬은 문제 4 에서 만든 `inverse_gauss_jordan` 으로 구한다
      (`np.linalg.lstsq` 는 노트북에서 **비교 대상**으로만 쓴다).
    - 근거: 잔차 r = b - A x 가 최소일 때 r 은 A 의 열공간에 수직이므로 A^T r = 0.

    Returns
    -------
    x : 최소자승해
    residual : b - A x
    """
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)

    ATA = A.T @ A
    ATb = A.T @ b

    inv_ATA = inverse_gauss_jordan(ATA)

    x = inv_ATA @ ATb
    residual = b - A @ x

    return x, residual


def rmse(residual) -> float:
    """잔차의 RMSE = sqrt(mean(r^2))."""
    residual = np.asarray(residual, dtype=float)
    RMSE = np.sqrt(np.mean(np.square(residual)))

    return RMSE