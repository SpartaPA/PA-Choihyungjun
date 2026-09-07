
from __future__ import annotations

import numpy as np

__all__ = [
    "as_vector",
    "dot",
    "norm",
    "angle_between",
    "normalize",
    "project",
    "reject",
    "skew",
    "cross",
    "plane_normal",
    "row_echelon",
    "rank",
    "det",
    "gauss_eliminate",
    "inverse_gauss_jordan",
]


# ---------------------------------------------------------------- 기본 연산

def as_vector(v) -> np.ndarray:
    """입력(리스트/튜플/배열)을 1차원 float 배열로 변환한다.

    1차원이 아니면 ValueError 를 던진다.
    """
    arr = np.asarray(v, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"1차원 벡터 필요. 입력 shape = {arr.shape}")
    return arr


def dot(x, y) -> float:
    """내적. sum(a_i * b_i) 를 직접 계산한다 (`np.dot` 사용 금지).

    두 벡터의 차원이 다르면 ValueError.
    """    
    x, y = as_vector(x), as_vector(y)
    if x.shape != y.shape:
        raise ValueError("x,y 차원 다름.")
    return float(np.sum(x * y))

def norm(v) -> float:
    """유클리드 노름. sqrt(v·v) — 위에서 만든 dot 을 재사용한다."""
    return float(np.sqrt(dot(v,v)))

def angle_between(x, y, degrees: bool = True, eps: float = 1e-14) -> float:
    """두 벡터 사이각. degrees=True 면 도(°), False 면 라디안.

    cos(theta) = (a·b) / (|a||b|)

    주의 1. 영벡터가 들어오면 사이각이 정의되지 않는다 -> ValueError.
    주의 2. 부동소수점 오차로 |cos| 가 1 을 아주 조금 넘으면 arccos 가 nan 을 낸다.
            [-1, 1] 로 clip 해야 무작위 입력에서도 안전하다.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    nx = np.linalg.norm(x)
    ny = np.linalg.norm(y)

    # 주의 1.
    if nx < eps or ny < eps:
        raise ValueError("영벡터 사이의 각은 정의 불가")
    # 주의 2.
    cos_theta = np.dot(x, y) / (nx * ny)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)

    theta = np.arccos(cos_theta)

    if degrees:
        return float(np.degrees(theta))
    return float(theta)

def normalize(x, eps : float = 1e-14) -> np.ndarray:
    """단위벡터로 정규화한다. v / |v|

    영벡터를 어떻게 처리할지는 **문제 1-2 에서 직접 정한다.**
    노트북 1-2 에서 (1) 아무 처리 없이 나눴을 때 무슨 일이 나는지 관찰하고,
    (2) 선택한 처리 방식과 근거를 마크다운에 적은 뒤, 그 방식대로 여기에 구현한다.
    선택에 따라 노트북/테스트의 검증 코드도 그 방식에 맞춰 작성한다.
    """
    x = as_vector(x)
    n = norm(x)

    if n < eps:
        raise ValueError("영벡터거나 norm 값이 너무 작음")

    return x / n


def project(x, y, esp : float = 1e-14) -> np.ndarray:
    """a 를 b 방향으로 정사영한 성분.

        proj_b(a) = (a·b / b·b) * b

    분모가 |b|^2 이므로 b 를 미리 정규화할 필요는 없다.
    b 가 영벡터면 ValueError.
    """    
    x, y = as_vector(x), as_vector(y)

    denom = dot(y, y)
    if denom < esp:
        raise ValueError("영벡터는 사영 불가")
    
    proj = (dot(x,y) / denom) * y
    return proj

def reject(x, y, eps : float = 1e-14) -> np.ndarray:
    """a 에서 b 방향 성분을 뺀 나머지(수직 성분). a = project + reject 가 성립해야 한다."""
    x, y = as_vector(x), as_vector(y)
    rej = x - project(x, y, eps)
    return rej

def skew(v) -> np.ndarray:
    """3차원 벡터 a 에 대응하는 반대칭행렬 [a]_x 를 만든다.

        [a]_x = [[  0, -a3,  a2],
                 [ a3,   0, -a1],
                 [-a2,  a1,   0]]

    만족해야 하는 성질: [a]_x @ b == a x b,  [a]_x.T == -[a]_x
    3차원이 아니면 ValueError.
    """    
    v = as_vector(v)
    if v.shape[0] != 3:
        raise ValueError("3차원 아님")

    v_skew = np.array([[0, -v[2], v[1]],
              [v[2], 0, -v[0]],
              [-v[1], v[0], 0]], dtype = float)
    return v_skew

def cross(x, y) -> np.ndarray:
    """외적을 **반대칭행렬 곱으로** 계산한다 (`np.cross` 사용 금지)."""
    x, y = as_vector(x), as_vector(y)
    cross = skew(x) @ y
    return cross

def plane_normal(x, y, z) -> np.ndarray:
    """세 점이 이루는 평면의 **단위** 법선 벡터.

    두 모서리 벡터(P2-P1, P3-P1)의 외적이 평면에 수직이다.
    세 점이 일직선이면 외적이 영벡터가 되어 평면이 하나로 정해지지 않는다 -> ValueError.
    """      
    x, y, z = as_vector(x), as_vector(y), as_vector(z)
    u = x - y
    v = x - z

    plane_normal = cross(u, v)
    return normalize(plane_normal)

# --------------------------- 가우스 소거 활용

def row_echelon(x, eps : float = 1e-14, pivoting : bool = True) -> tuple[np.ndarray, list[int], int]:
    """행 사다리꼴(row echelon form) 로 만든다.

    Parameters
    ----------
    pivoting : True 면 부분 피벗팅(각 열에서 절댓값이 가장 큰 행을 피벗으로 올림)

    Returns
    -------
    U : (m, n) 상삼각 형태 행렬
    pivot_cols : 피벗이 선 열 인덱스 리스트
    n_swaps : 행 교환 횟수 (행렬식 부호 계산에 필요)

    힌트: 0 인지 판정할 때는 `== 0` 대신 허용오차(tol)를 쓴다.
          예) tol = max(m, n) * np.finfo(float).eps * max(1.0, np.max(np.abs(U)))
    """    
    M = np.asarray(x, dtype=float).copy()
    if M.ndim != 2:
        raise ValueError("2차원 행렬 아님")

    m, n = M.shape
    pivot_row = 0
    pivot_cols = []
    n_swaps = 0

    for col in range(n):
        if pivot_row >= m:
            break

        if pivoting:
            max_row = pivot_row + np.argmax(np.abs(M[pivot_row:m, col]))
            if np.abs(M[max_row, col]) < eps:
                continue

            if max_row != pivot_row:
                M[[pivot_row, max_row]] = M[[max_row, pivot_row]]
                n_swaps += 1
        else:
            if np.abs(M[pivot_row, col]) < eps:
                continue

        for r in range(pivot_row + 1, m):
            factor = M[r, col] / M[pivot_row, col]
            M[r, col:] -= factor * M[pivot_row, col:]
            M[r, col] = 0.0

        pivot_cols.append(col) 
        pivot_row += 1

    return M, pivot_cols, n_swaps

def rank(x, eps : float = 1e-14) -> int:
    """행 사다리꼴의 피벗 개수 = rank."""
    ref, pivot_col, swaps = row_echelon(x, eps=eps)
    return len(pivot_col)

def det(x, eps : float = 1e-14) -> float:
    """행렬식 = 행 사다리꼴 대각성분의 곱 x (-1)^(행 교환 횟수).

    피벗이 n 개보다 적으면(특이행렬) 0.0 을 돌려준다.
    정사각 행렬이 아니면 ValueError.
    """
    M = np.asarray(x, dtype=float).copy()
    if M.ndim != 2 or M.shape[0] != M.shape[1]:
        raise ValueError("정사각행렬 아님")

    n = M.shape[0]
    U, pivot_col, n_swaps = row_echelon(M, pivoting=True)

    if len(pivot_col) < n:
        return 0.0

    sign = -1.0 if (n_swaps % 2== 1) else 1.0
    return float(sign * np.prod(np.diag(U)))


def gauss_eliminate(A, b , pivoting : bool = True, eps : float = 1e-14, verbose : bool = False):
    """가우스 소거법 + 후진대입으로 Ax = b 를 푼다.

    Parameters
    ----------
    pivoting : True 면 부분 피벗팅을 적용한다. False 면 피벗을 그대로 쓴다
               (문제 4-4 에서 두 경우의 오차를 비교하므로 **둘 다 동작해야 한다**).
    verbose  : True 면 각 소거 단계의 첨가행렬 [A|b] 를 출력한다
               (문제 4-1 이 요구하는 '단계별 출력').

    Returns
    -------
    x : 해 벡터
    steps : 단계별 첨가행렬 [A|b] 스냅샷 리스트 (초기 상태 포함)

    피벗이 0 이면 해가 유일하지 않다 -> ZeroDivisionError.
    """    
    A = np.asarray(A,dtype=float)
    b = np.asarray(b,dtype=float).reshape(-1, 1)

    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("정사각행렬 아님")
    if A.shape[0] != b.shape[0]:
        raise ValueError("A와 b 차원 불일치")

    n = A.shape[1]
    Ab = np.hstack([A,b])
    steps = []
    pivot_row = 0

    steps.append(Ab.copy())

    if verbose:
        print(steps)

    for col in range(n):
        if col >= n:
            break

        if pivoting:
            max_row = pivot_row + np.argmax(np.abs(Ab[pivot_row:n, col]))

            if np.abs(Ab[max_row, col]) < eps:
                raise ZeroDivisionError
            if pivot_row != max_row:
                Ab[[pivot_row, max_row]] = Ab[[max_row, pivot_row]]
        else:
            if np.abs(Ab[pivot_row, col]) < eps:
                raise ZeroDivisionError
    
        for r in range(col + 1, n):
            factor = Ab[r, col] / Ab[pivot_row, col]
            Ab[r, col:] -= factor * Ab[pivot_row, col:]
            Ab[r, col] = 0.0
        pivot_row += 1 

        steps.append(Ab.copy())
        if verbose:
            print(f"\n[{col}] {col}열 소거 후")
            print(Ab)

    x = np.zeros(n)
    for i in range(n - 1, -1, -1):
        x[i] = (Ab[i, n] - Ab[i, i + 1:n] @ x[i + 1:]) / Ab[i, i]
 
    if verbose:
        print("\n해 x =", x)
 
    return x, steps
    
            

    
def inverse_gauss_jordan(A, eps : float = 1e-14) -> np.ndarray:
    """가우스-조던 소거로 역행렬을 구한다. [A|I] -> [I|A^-1].

    정사각이 아니면 ValueError, 특이행렬이면 np.linalg.LinAlgError.
    (`np.linalg.inv` 를 부르지 말고 소거로 직접 구한다)
    """
    A = np.asarray(A, dtype=float)
    if A.ndim != 2:
        raise ValueError("정사각행렬 아님")

    m, n = A.shape
    if m != n:
        raise ValueError("정사각행렬 아님")

    I = np.eye(n)
    AI = np.hstack([A, I])

    for col in range(n):
        max_row = col + np.argmax(np.abs(AI[col:n, col]))

        if np.abs(AI[max_row, col]) < eps:
            raise np.linalg.LinAlgError("특이행렬 (역행렬 존재하지 않음).")

        if col != max_row:
            AI[[col, max_row]] = AI[[max_row, col]]

        AI[col] = AI[col] / AI[col, col]

        for r in range(n):
            if r != col:
                AI[r] -= AI[r, col] * AI[col]

    return AI[:, n:]





    
