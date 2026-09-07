import math

import rclpy
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy, qos_profile_sensor_data)
from std_msgs.msg import Float32
from turtlesim.msg import Pose

class DistancePublisher(Node):
    def __init__(self):
        super().__init__('turtle_distance_publisher')
        # 파라미터 : 발행 주기
        self.declare_parameter('publish_rate', 10.0,
                               ParameterDescriptor(description='/turtle_distance 발행 주기 [Hz], 0 보다 커야 함'))
        rate = self.get_parameter('publish_rate').value

        # ---------- 상태 -------------
        self.start = None   # 시작점
        self.latest = None  # 최신 pose

        # ---------- 구독 -------------
        pose_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        _ = qos_profile_sensor_data  

        self._pose_sub = self.create_subscription(
            Pose, 'turtle1/pose', self.on_pose, pose_qos)

        # ---------- 발행 -----------------
        self.pub = self.create_publisher(Float32, '/turtle_distance', 10)

        # ---------- 타이머 -----------------
        self.timer = self.create_timer(1.0 / rate, self.on_timer)

        # ---------- 파라미터 변경 콜백 -----------------
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self.get_logger().info(f'turtle_distance_publisher 시작: publish_rate={rate} Hz')

    def on_pose(self, msg):     # 구독 콜백 : 저장만
        if self.start is None:
            self.start = (msg.x, msg.y)
        self.latest = msg

    def on_timer(self):         # 타이머 콜백 : 계산 + 발행
        if self.latest is None:
            self.get_logger().warn('아직 /turtle1/pose 를 받지 못했습니다',
                                   throttle_duration_sec=1.0)
            return
        d = math.hypot(self.latest.x - self.start[0],
                       self.latest.y - self.start[1])
        self.pub.publish(Float32(data=float(d)))

    def _on_set_parameters(self, params):
        """파라미터 변경 검증 + 타이머 재생성.

        주의: 이 콜백 안에서 self.get_parameter('publish_rate') 를 읽으면 "옛 값" 이 나옵니다.
        새 값은 인자로 들어온 params[i].value 에서 읽어야 합니다.
        """
        for p in params:
            if p.name != 'publish_rate':
                continue
            if p.type_ != Parameter.Type.DOUBLE:
                return SetParametersResult(
                    successful=False, reason='publish_rate 는 double 이어야 합니다 (예: 5.0)')
            if p.value <= 0.0:
                return SetParametersResult(
                    successful=False, reason='publish_rate 는 0 보다 커야 합니다')
            # 타이머는 주기를 바꾸는 API 가 없으므로 "파괴 후 재생성" 합니다.
            self.destroy_timer(self.timer)
            self.timer = self.create_timer(1.0 / p.value, self.on_timer)
            self.get_logger().info(f'publish_rate 변경 → {p.value} Hz (타이머 재생성)')
        return SetParametersResult(successful=True)


def main():
    rclpy.init()
    node = DistancePublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Ctrl+c - 정상 정료')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()

