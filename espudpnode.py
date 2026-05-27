import rclpy 
from rclpy.node import Node
from std_msgs.msg import Float32, String, Int32
import socket, json
import threading
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5005))
sock.setblocking(False)  # Nieblokujący socket
print("Nasłuchuje na porcie 5005...")

class WebPublisher(Node):
    def __init__(self):
        super().__init__('webPublisher')

        qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
        )

        self.temp_pub = self.create_publisher(Float32, 'water_temp', qos)
        self.ph_pub = self.create_publisher(Float32, 'water_ph', qos)
        self.cond_pub = self.create_publisher(Float32, 'water_cond', qos)
        self.timer = self.create_timer(0.1, self.publish_data)  # Szybszy timer, tylko do publikowania
                
        self.temp = 0.0
        self.ph = 0.0
        self.cond = 0.0
        
        # Wątek do nasłuchiwania UDP
        self.listen_thread = threading.Thread(target=self.listen_udp, daemon=True)
        self.listen_thread.start()
    
    def listen_udp(self):
        """Wątek nasłuchujący UDP - działa niezależnie od timera"""
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                parsed = json.loads(data.decode())
                
                self.temp = float(parsed["temperatura"])
                self.ph = float(parsed["ph"])
                self.cond = float(parsed["cond"])
                self.time = float(parsed["timestamp"])
                
                self.get_logger().info(f"Od {addr}: {parsed}")
            except BlockingIOError:
                pass
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.get_logger().warn(f"Data error: {e}")
            except Exception as e:
                self.get_logger().error(f"UDP error: {e}")
    
    def publish_data(self):
        """Publikuj aktualne dane na topicach"""
        self.temp_pub.publish(Float32(data=self.temp))
        self.ph_pub.publish(Float32(data=self.ph))
        self.cond_pub.publish(Float32(data=self.cond))

def main(args=None):
    rclpy.init(args=args)
    node = WebPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()