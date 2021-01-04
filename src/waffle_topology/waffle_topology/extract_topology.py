#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA
from visualization_msgs.msg import Marker

import math

from waffle_topology.graph import Graph

class Extract_topology(Node):
    def __init__(self):
        # Set parameters
        self.scan_angle_min = -2.35
        self.scan_angle_max = 2.35
        self.scan_radius = 5.0
        self.scan_map_resolution = 0.05
        self.occupancy_img_threshold = 127

        self.scan = LaserScan()
        self.scan_map_shape = (
            int((2*self.scan_radius) // self.scan_map_resolution),
            int((2*self.scan_radius) // self.scan_map_resolution), 1)
        self.scan_map_center = (
            int(self.scan_map_shape[0] // 2),
            int(self.scan_map_shape[1] // 2))

        # Initialize ROS node
        super().__init__('waffle_topology_extract_topology')
        self.area_subscription = self.create_subscription(OccupancyGrid, '/topology/area', self.area_callback, 1)
        self.odom_subscription = self.create_subscription(Odometry, '/odom', self.odom_callback, 1)
        self.nodes_publisher = self.create_publisher(Marker, '/topology/nodes', 10)
        self.edges_publisher = self.create_publisher(Marker, '/topology/edges', 10)

        # # Initialize history
        # self.history = Marker()
        # self.history.header.frame_id = 'odom'
        # self.history.ns = 'intersection'
        # self.history.id = 0
        # self.history.type = Marker.POINTS
        # self.history.action = Marker.ADD
        # self.history.scale.x = 0.1      # Point width
        # self.history.scale.y = 0.1      # Point height

        # p = Point(x=0., y=0., z=1.)
        # self.history.points.append(p)
        # color = ColorRGBA(r=1., g=1., b=1., a=0.5)
        # self.history.colors.append(color)
        self.history_publisher = self.create_publisher(Marker, '/topology/history', 10)
    
    def init_colors(self):
        self.COLOR_NODE = ColorRGBA(r=0.53, g=0.9, b=0.5, a=0.2)        # Green
        self.COLOR_EDGE = ColorRGBA(r=0.53, g=0.9, b=0.5, a=0.2)        # Green
        self.COLOR_INTERSECTION = ColorRGBA(r=1., g=0.73, b=0., a=0.2)  # Yellow
        self.COLOR_LEAF = ColorRGBA(r=0.95, g=0.37, b=0.37, a=0.2)      # Red

    def area_callback(self, msg):
        # Generate graph from gridmap message
        try:
            topology = Graph(msg, self.robot_pose)
        except:
            print("Graph generation failed", msg.header.stamp.sec)
            return

        # Search next goal

        # Color important elements
        # topology.update_node_color_alpha(topology.root[1], 1.)
        # topology.update_edge_color_alpha(topology.root, 1.)

        # Publish results
        # self.nodes_publisher.publish(topology.nodes_marker)
        # self.edges_publisher.publish(topology.edges_marker)

        # Log
        # self.draw_history(topology)

        # Visualize graph
        # self.init_colors()
        # self.nodes_marker, self.edges_marker = self.generate_markers(
        #     self.nodes_point, self.num_nodes_neighbor, self.edges, msg)

    def draw_history(self, topology):
        """Draw intersection point on odometry frame"""

        # Transform intersection point into odometry
        try:
            self.robot_pose
        except:
            return
        target = topology.nodes_point[topology.root[1]]

        # target = [0, 0]

        x = target[0]*math.cos(self.robot_pose[2]) - target[1]*math.sin(self.robot_pose[2]) + self.robot_pose[0]
        y = target[0]*math.sin(self.robot_pose[2]) + target[1]*math.cos(self.robot_pose[2]) + self.robot_pose[1]

        # Append a marker point
        # p = Point()
        # p.x = -x
        # p.y = -y
        # p.z = 1.
        # self.history.points.append(p)
        # color = ColorRGBA()
        # color.r = 1.
        # color.g = 1.
        # color.b = 1.
        # color.a = 0.1
        # self.history.colors.append(color)
        self.history.points[0].x = -x
        self.history.points[0].y = -y
        self.history_publisher.publish(self.history)

    def odom_callback(self, msg):
        theta = self.quaternion_to_euler(
            msg.pose.pose.orientation.x,
            msg.pose.pose.orientation.y,
            msg.pose.pose.orientation.z,
            msg.pose.pose.orientation.w)
        self.robot_pose = [msg.pose.pose.position.x, msg.pose.pose.position.y, theta]
    
    def quaternion_to_euler(self, x, y, z, w):
        # t0 = +2.0 * (w * x + y * z)
        # t1 = +1.0 - 2.0 * (x * x + y * y)
        # X = math.atan2(t0, t1)
        # t2 = +2.0 * (w * y - z * x)
        # t2 = +1.0 if t2 > +1.0 else t2
        # t2 = -1.0 if t2 < -1.0 else t2
        # Y = math.asin(t2)
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        Z = math.atan2(t3, t4)
        return Z

    def generate_markers(self, nodes_point, num_nodes_neighbor, edges, msg):
        # Add node marker
        nodes_marker = Marker()
        nodes_marker.header = copy.deepcopy(msg.header)
        nodes_marker.header.frame_id = 'odom'
        nodes_marker.ns = 'node'
        nodes_marker.id = 0
        nodes_marker.type = Marker.POINTS
        nodes_marker.action = Marker.ADD
        nodes_marker.scale.x = 0.1      # Point width
        nodes_marker.scale.y = 0.1      # Point height
        for i, node_point in enumerate(nodes_point):
            p = Point(
                x = -node_point[0],
                y = -node_point[1],
                z = 0.1)
            nodes_marker.points.append(p)
            if(num_nodes_neighbor[i] == 1):
                nodes_marker.colors.append(copy.deepcopy(self.COLOR_LEAF))
            elif(num_nodes_neighbor[i] > 2):
                nodes_marker.colors.append(copy.deepcopy(self.COLOR_INTERSECTION))
            else:
                nodes_marker.colors.append(copy.deepcopy(self.COLOR_NODE))                

        # Add edge marker
        edges_marker = Marker()
        edges_marker.header = copy.deepcopy(msg.header)
        edges_marker.header.frame_id = 'odom'
        edges_marker.ns = 'edge'
        edges_marker.id = 0
        edges_marker.type = Marker.LINE_LIST
        edges_marker.action = Marker.ADD
        edges_marker.scale.x = 0.03     # Line width
        for edge in edges:
            edges_marker.points.append(nodes_marker.points[edge[0]])
            edges_marker.points.append(nodes_marker.points[edge[1]])
            edges_marker.colors.append(copy.deepcopy(self.COLOR_EDGE))
            edges_marker.colors.append(copy.deepcopy(self.COLOR_EDGE))
        
        return nodes_marker, edges_marker

    def update_node_color_alpha(self, node, alpha):
        self.nodes_marker.colors[node].a = alpha

    def update_edge_color_alpha(self, edge, alpha):
        for i, e in enumerate(self.edges):
            if(e == edge or e[::-1] == edge):
                self.edges_marker.colors[2*i].a = alpha
                self.edges_marker.colors[2*i+1].a = alpha

def main(args=None):
    rclpy.init(args=args)
    node = Extract_topology()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()