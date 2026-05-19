import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String, Int32
import random

class TestPublisher(Node):
    def __init__(self):
        super().__init__('test_publisher')
        self.altitude_pub = self.create_publisher(Float32, 'altitude', 10)
        self.speed_pub = self.create_publisher(Float32, 'speed', 10)
        self.battery_percent_pub = self.create_publisher(Int32, 'battery_percent', 10)
        self.battery_voltage_pub = self.create_publisher(Float32, 'battery_voltage', 10)
        self.gps_global_pub = self.create_publisher(String, 'gps_global', 10)
        self.gps_relative_pub = self.create_publisher(String, 'gps_relative', 10)
        self.mission_time_pub = self.create_publisher(String, 'mission_time', 10)
        self.flight_mode_pub = self.create_publisher(String, 'flight_mode', 10)
        self.water_temp_pub = self.create_publisher(Float32, 'water_temp', 10)
        self.timer = self.create_timer(1.0, self.publish_all)

    def publish_all(self):
        self.altitude_pub.publish(Float32(data=random.uniform(0, 120)))
        self.speed_pub.publish(Float32(data=random.uniform(0, 20)))
        self.battery_percent_pub.publish(Int32(data=random.randint(0, 100)))
        self.battery_voltage_pub.publish(Float32(data=random.uniform(10, 16)))
        self.gps_global_pub.publish(String(data="52.{:06f},20.{:06f}".format(random.random(), random.random())))
        self.gps_relative_pub.publish(String(data="0.{:06f},0.{:06f}".format(random.random(), random.random())))
        self.mission_time_pub.publish(String(data="00:{:02}:{:02}".format(random.randint(0,59), random.randint(0,59))))
        self.flight_mode_pub.publish(String(data=random.choice(["INIT", "AUTO", "MANUAL", "RTL", "LAND"])))
        self.water_temp_pub.publish(Float32(data=random.uniform(15, 25)))

def main(args=None):
    rclpy.init(args=args)
    node = TestPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()