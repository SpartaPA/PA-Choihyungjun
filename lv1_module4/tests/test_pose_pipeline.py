"""문제 2 — PosePipeline 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 "2개 이상" 을 아래 두 테스트로 채운다.

  1. camera_to_base 가 모듈 ③ 체인(행렬 곱)과 같은 결과를 주는가  -> test_camera_to_base_matches_chain
  2. base 로 갔다가 camera 로 되돌리면 원래 점군이 나오는가       -> test_roundtrip_restores_points

작성 요령
--------
- 비교는 `np.allclose` (기본 허용오차) 로 한다.
- 난수는 반드시 시드를 고정한다 (fixture `rng`).
- 관절 각도 0 에서 파이프라인이 default_chain 과 같은지, 각도를 바꾸면 결과가 달라지는지 등
  테스트를 더 붙이면 좋다 (아래 권장 예시).

실행: 프로젝트 루트에서  pytest tests/test_pose_pipeline.py -v
"""

import numpy as np
import pytest

from src.coordinate_chain import default_chain
from src.pose_pipeline import PosePipeline
from src.transform import make_T, transform_points
from src.rotation import rot_x, rot_y, rot_z


@pytest.fixture
def rng():
    """난수는 반드시 시드를 고정한다."""
    return np.random.default_rng(42)


@pytest.fixture
def pipeline():
    """모듈 ③ default_chain 과 같은 값으로 만든 파이프라인."""
    chain = default_chain()
    return PosePipeline(chain.get("base", "link"), chain.get("link", "camera"))


# --- 1. camera_to_base == 체인/행렬 곱 --------------------------------------

def test_camera_to_base_matches_chain(pipeline, rng):
    # TODO: (N,3) 점군을 만들어 pipeline.camera_to_base 결과가
    #       default_chain().transform("base", "camera", P) 및
    #       transform_points(T_base_link @ T_link_camera, P) 와 같은지 검사
    P = rng.normal(0.0, 0.1, size=(50, 3))          # (N,3) 점군
    pipe = pipeline.camera_to_base(P)

    chain = default_chain()
    expected_chain = chain.transform("base", "camera", P)
    T_base_camera = chain.get("base", "link") @ chain.get("link", "camera")
    expected_mat = transform_points(T_base_camera, P)

    assert pipe.shape == P.shape
    assert np.allclose(pipe, expected_chain)
    assert np.allclose(pipe, expected_mat)


# --- 2. 왕복 검증 -------------------------------------------------------------

def test_roundtrip_restores_points(pipeline, rng):
    # TODO: P_cam -> camera_to_base -> base_to_camera 가 P_cam 과 같은지 (allclose) 검사
    #       (3,) 단일 점과 (N,3) 점군 둘 다 확인
    # (3,) 단일 점
    P_s = rng.normal(0, 0.1, size=3)
    back1 = pipeline.camera_to_base(pipeline.base_to_camera(P_s))
    assert np.allclose(P_s, back1)

    # (N,3) 점군
    P_g = rng.normal(0, 0.1 , size=(50,3))
    back2 = pipeline.camera_to_base(pipeline.base_to_camera(P_g))
    assert np.allclose(P_g, back2)


# --- 여기부터는 추가 테스트 (권장) -------------------------------------------
#
# 예) def test_joint_angle_zero_is_nominal(pipeline):
#         """set_joint_angle(0) 이면 T_base_link 가 생성자에 준 값 그대로."""
#
# 예) def test_joint_angle_changes_result(pipeline, rng):
#         """관절 각도를 바꾸면 같은 관측이 base 에서 다른 위치로 간다."""
#
# 예) def test_distance_is_preserved(pipeline, rng):
#         """강체 변환은 두 점 사이 거리를 보존한다."""
#
# 예) def test_rejects_wrong_shape():
#         """(3,3) 을 넣으면 ValueError."""
