import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
import cv2
import numpy as np

class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')
        self.publisher_ = self.create_publisher(CompressedImage, 'drone_image', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 FPS
        self.cap = cv2.VideoCapture(0)  # domyślna kamera

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warning('Nie udało się pobrać obrazu z kamery!')
            return
        # Kodowanie do JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            self.get_logger().warning('Nie udało się zakodować obrazu!')
            return
        msg = CompressedImage()
        msg.format = 'jpeg'
        msg.data = np.array(buffer).tobytes()
        self.publisher_.publish(msg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
