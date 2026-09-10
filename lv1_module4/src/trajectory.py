"""문제 4 — 궤적 보간. (학생 작성용 템플릿)

경유점(waypoint)을 지나는 궤적을 선형 보간 / 큐빅 스플라인으로 만들고,
시작·끝에서 속도와 가속도가 0 이 되는 5차 다항식 프로파일을 구현한다.

입력 규약
--------
- t_wp : (M,) 경유점 시각, 오름차순
- q_wp : (M,) 스칼라 궤적 또는 (M, D) 다차원 궤적 (예: 3차원 위치는 D = 3)
- t    : (N,) 평가할 시각 (t_wp[0] <= t <= t_wp[-1])
- 반환 : q_wp 가 (M,) 이면 (N,), (M, D) 이면 (N, D)

큐빅 스플라인은 `scipy.interpolate.CubicSpline` 을 써도 된다 (axis=0).
"""

from __future__ import annotations

import numpy as np

__all__ = ["linear_interp", "cubic_spline_interp", "quintic_profile", "finite_diff"]


def linear_interp(t_wp, q_wp, t) -> np.ndarray:
    """경유점 사이를 직선으로 잇는 보간. 각 차원마다 `np.interp` 를 쓰면 된다.

    위치는 이어지지만 경유점에서 속도가 불연속(꺾임)이다.
    """
    # TODO: 문제 4-1
    t_wp = np.asarray(t_wp, dtype=float)
    q_wp = np.asarray(q_wp, dtype=float)
    t = np.atleast_1d(np.asarray(t, dtype=float))

    if q_wp.ndim == 1:
        return np.interp(t, t_wp, q_wp)
    return np.stack([np.interp(t, t_wp, q_wp[:, k]) for k in range(q_wp.shape[1])], axis=1)

from scipy.interpolate import CubicSpline

def cubic_spline_interp(t_wp, q_wp, t, bc_type: str = "natural") -> np.ndarray:
    """경유점을 지나는 큐빅 스플라인 보간 (위치·속도·가속도가 모두 연속, C2).

    bc_type : 양끝 경계 조건. "natural" (양끝 가속도 0) 또는 "clamped" (양끝 속도 0).
    """
    # TODO: 문제 4-1
    t_wp = np.asarray(t_wp, dtype=float)
    q_wp = np.asarray(q_wp, dtype=float)
    cs = CubicSpline(t_wp, q_wp, axis=0, bc_type=bc_type)
    return cs(t)



def quintic_profile(t, t0: float, tf: float, q0, qf,
                    v0=0.0, vf=0.0, a0=0.0, af=0.0):
    """5차 다항식 궤적 q(t) 와 그 도함수 (q, qd, qdd) 를 돌려준다.

    경계 조건 6개 — q(t0)=q0, q(tf)=qf, qd(t0)=v0, qd(tf)=vf, qdd(t0)=a0, qdd(tf)=af —
    로 계수 6개 (c0 ~ c5) 를 정한다. 경계 속도·가속도가 모두 0 인 기본형은

        tau = (t - t0) / (tf - t0)
        s(tau) = 10 tau^3 - 15 tau^4 + 6 tau^5
        q(t) = q0 + (qf - q0) s(tau)

    로 닫힌 꼴이 있고, 일반형은 6x6 선형계를 풀면 된다. 어느 쪽으로 구현해도 된다.
    q0, qf 가 스칼라이면 (N,), (D,) 이면 (N, D) 를 돌려준다.

    Returns
    -------
    q, qd, qdd : 위치, 속도, 가속도 (해석적 미분. 유한차분이 아니다)
    """
    # TODO: 문제 4-4
    t = np.asarray(t, dtype=float)
    q0 = np.asarray(q0, dtype=float)
    qf = np.asarray(qf, dtype=float)
    v0, vf = np.asarray(v0, dtype=float), np.asarray(vf, dtype=float)
    a0, af = np.asarray(a0, dtype=float), np.asarray(af, dtype=float)

    T = tf - t0
    # 경계 조건 6개로 계수 c0..c5 (일반형, 다차원 브로드캐스트)
    c0 = q0
    c1 = v0
    c2 = a0 / 2.0
    c3 = (20 * (qf - q0) - (8 * vf + 12 * v0) * T - (3 * a0 - af) * T**2) / (2 * T**3)
    c4 = (-30 * (qf - q0) + (14 * vf + 16 * v0) * T + (3 * a0 - 2 * af) * T**2) / (2 * T**4)
    c5 = (12 * (qf - q0) - 6 * (vf + v0) * T + (af - a0) * T**2) / (2 * T**5)

    dt = (t - t0)                             # (N,)
    # 스칼라면 (N,), 다차원이면 (N,1) 로 만들어 계수 (D,) 와 브로드캐스트
    if q0.ndim > 0:
        dt = dt[:, None]

    q = c0 + c1*dt + c2*dt**2 + c3*dt**3 + c4*dt**4 + c5*dt**5
    qd = c1 + 2*c2*dt + 3*c3*dt**2 + 4*c4*dt**3 + 5*c5*dt**4
    qdd = 2*c2 + 6*c3*dt + 12*c4*dt**2 + 20*c5*dt**3
    return q, qd, qdd



def finite_diff(y, t) -> np.ndarray:
    """시간축(axis 0)에 대한 수치 미분. `np.gradient(y, t, axis=0)` 를 쓰면 된다.

    y : (N,) 또는 (N, D),  t : (N,)
    속도 = finite_diff(q, t),  가속도 = finite_diff(속도, t)
    """
    # TODO: 문제 4-2
    return np.gradient(np.asarray(y, dtype=float), np.asarray(t, dtype=float), axis=0)
