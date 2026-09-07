import math


def distance(x, y, gx=0.0, gy=0.0):
    """두 점 사이 유클리드 거리. 기본 목표는 원점(0,0)."""
    return math.hypot(gx - x, gy - y)


def normalize_angle(theta):
    """각도를 -pi ~ pi 범위로 정규화."""
    return math.atan2(math.sin(theta), math.cos(theta))


def reached(x, y, gx, gy, tolerance):
    """(x, y) 가 목표(gx, gy)의 허용 오차 안에 들어왔는지 판정."""
    return distance(x, y, gx, gy) <= tolerance
