import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
from turtle_interfaces.msg import WaypointList

class WaypointMarkers(Node):
    def __init__(self):
        super().__init__('waypoint_markers')
        self.pub = self.create_publisher(Marker, '/waypoint_markers', 10)
        self.create_subscription(WaypointList, '/waypoints', self.on_waypoints, 10)
        self.get_logger().info('waypoint_markers up (/waypoints 구독)')

    def on_waypoints(self, msg):
        m = Marker()
        m.header.frame_id = 'world'
        m.header.stamp = self.get_clock().now().to_msg()
        m.pose.orientation.w = 1.0
        m.ns = 'waypoints'
        m.id = 0
        m.type = Marker.SPHERE_LIST
        m.action = Marker.ADD
        m.scale.x = m.scale.y = m.scale.z = 0.4
        m.color.r = 1.0
        m.color.a = 1.0
        m.points = [Point(x=w.x, y=w.y, z=0.0) for w in msg.waypoints]
        self.pub.publish(m)

def main():
    rclpy.init()
    node = WaypointMarkers()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()