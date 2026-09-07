import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from turtlesim.msg import Pose

class TurtleTF(Node):
    def __init__(self):
        super().__init__('turtle_tf_broadcaster')
        self.br = TransformBroadcaster(self)
        self.create_subscription(Pose, '/turtle1/pose', self.on_pose, 10)

    def on_pose(self, msg):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'world'          # Fixed Frame
        t.child_frame_id = 'turtle1'
        t.transform.translation.x = msg.x
        t.transform.translation.y = msg.y
        t.transform.rotation.z = math.sin(msg.theta / 2.0)  # z축 회전 쿼터니언
        t.transform.rotation.w = math.cos(msg.theta / 2.0)
        self.br.sendTransform(t)

def main():
    rclpy.init()
    node = TurtleTF()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
