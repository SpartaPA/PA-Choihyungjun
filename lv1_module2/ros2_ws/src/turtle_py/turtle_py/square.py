import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math

class Square(Node):
    def __init__(self):
        super().__init__('square')
        self.pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        self.lin_speed = 2.0
        self.ang_speed = math.pi / 2
        self.forward_time = 2.0
        self.turn_time = 1.0

        self.state = 'forward'
        self.phase_start = self.get_clock().now()

        self.timer = self.create_timer(0.05, self.on_timer)
        self.get_logger().info('square driver up')

    def on_timer(self):
        now = self.get_clock().now()
        elapsed = (now - self.phase_start).nanoseconds / 1e9
        twist = Twist()

        if self.state ==  "forward":
            twist.linear.x = self.lin_speed
            if elapsed >= self.forward_time:
                self.state = "turn"
                self.phase_start = now
        else:
            twist.angular.z = self.ang_speed
            if elapsed >= self.turn_time:
                self.state = "forward"
                self.phase_start = now


        self.pub.publish(twist)

def main():
    rclpy.init()
    node = Square()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.pub.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        