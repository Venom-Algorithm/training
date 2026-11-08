"""ROS2 演示：复用 rm_tf_demo，将合成目标变换到 base_link。"""
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener, TransformException

from robotics_demo import optical_to_link, quaternion_rotate


class TargetTransformDemo(Node):
    def __init__(self):
        super().__init__("robotics_target_transform_demo")
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.timer = self.create_timer(0.5, self.show_target)

    def show_target(self):
        try:
            # 合成点与本次查询的 TF 对齐；接入图像时使用采集时刻：
            # Time.from_msg(point_msg.header.stamp)。
            transform = self.buffer.lookup_transform("base_link", "camera_link", Time())
        except TransformException as exc:
            self.get_logger().warn(f"等待 base_link ← camera_link：{exc}")
            return

        q = transform.transform.rotation
        t = transform.transform.translation
        point_link = optical_to_link((1.0, 0.0, 3.0))
        rotated = quaternion_rotate(point_link, (q.x, q.y, q.z, q.w))
        point_base = rotated[0] + t.x, rotated[1] + t.y, rotated[2] + t.z
        stamp = transform.header.stamp
        self.get_logger().info(
            f"TF时刻={stamp.sec}.{stamp.nanosec:09d}；"
            f"camera原点=({t.x:.3f}, {t.y:.3f}, {t.z:.3f}) m；"
            f"合成目标base=({point_base[0]:.3f}, {point_base[1]:.3f}, {point_base[2]:.3f}) m"
        )


def main(args=None):
    rclpy.init(args=args)
    node = TargetTransformDemo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
