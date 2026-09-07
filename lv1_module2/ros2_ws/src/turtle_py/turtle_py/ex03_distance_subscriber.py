import rclpy
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from std_msgs.msg import Float32



class DistanceSubscriber(Node):
    def __init__(self):
        super().__init__('turtle_distance_subscriber')
        self.declare_parameter('warn_distance', 2.5,
                               ParameterDescriptor(description='이 거리[m]를 넘으면 경고 로그'))
        self.warn = self.get_parameter('warn_distance').value
        qos = QoSProfile(
            history = HistoryPolicy.KEEP_LAST,
            depth = 10,
            reliability = ReliabilityPolicy.RELIABLE,
            durability = DurabilityPolicy.VOLATILE,
        )

        self.create_subscription(Float32, '/turtle_distance', self.on_dist, qos)
        self.add_on_set_parameters_callback(self._on_set_parameters)

        self.get_logger().info('distance_watcher up')

    def on_dist(self, msg):
        if msg.data > self.warn:
            self.get_logger().warn(f"경고: 원점거리 {msg.data:.2f} m > 임계 {self.warn:.2f} m")
        else:
            self.get_logger().debug(f"거리 {msg.data:.2f}m")

    def _on_set_parameters(self, params):
        for p in params:
            if p.name == 'warn_distance':
                if p.type_ != Parameter.Type.DOUBLE:
                    return SetParametersResult(successful=False,
                                               reason='warn_distance 는 double 이어야 합니다')
                if p.value < 0.0:
                    return SetParametersResult(successful=False,
                                               reason='warn_distance 는 음수일 수 없습니다')
                self._warn_distance = p.value
                self.get_logger().info(f'warn_distance 변경 → {p.value}')
        return SetParametersResult(successful=True)

def main():
    rclpy.init()
    node = DistanceSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

