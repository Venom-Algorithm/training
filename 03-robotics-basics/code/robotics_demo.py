"""机器人学数学演示：使用标准库，长度 m，内部角度 rad。"""
import argparse
import math
from typing import Tuple

Vec3 = Tuple[float, float, float]
Mat3 = Tuple[Vec3, Vec3, Vec3]


def rotate2d(x: float, y: float, yaw: float):
    """将二维位移沿 yaw 旋转；yaw 使用 rad。"""
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    rotated_x = cos_yaw * x - sin_yaw * y
    rotated_y = sin_yaw * x + cos_yaw * y
    return rotated_x, rotated_y


def world_to_body(point_world, translation_world_body, yaw_world_body):
    """先减去底盘位置，再用负 yaw 将位移转回底盘方向。"""
    dx = point_world[0] - translation_world_body[0]
    dy = point_world[1] - translation_world_body[1]
    return rotate2d(dx, dy, -yaw_world_body)


def rot_y(pitch: float) -> Mat3:
    """右手绕 +Y 旋转；机体采用 X 前、Y 左、Z 上。"""
    cos_pitch = math.cos(pitch)
    sin_pitch = math.sin(pitch)
    return (
        (cos_pitch, 0.0, sin_pitch),
        (0.0, 1.0, 0.0),
        (-sin_pitch, 0.0, cos_pitch),
    )


def transform_point(point: Vec3, rotation: Mat3, translation: Vec3) -> Vec3:
    """将同一个点的 source 坐标换成 target 坐标。"""
    source_x, source_y, source_z = point
    # 矩阵每一行分别算出目标坐标系中的一个分量，再加该分量的平移。
    target_x = (
        rotation[0][0] * source_x
        + rotation[0][1] * source_y
        + rotation[0][2] * source_z
        + translation[0]
    )
    target_y = (
        rotation[1][0] * source_x
        + rotation[1][1] * source_y
        + rotation[1][2] * source_z
        + translation[1]
    )
    target_z = (
        rotation[2][0] * source_x
        + rotation[2][1] * source_y
        + rotation[2][2] * source_z
        + translation[2]
    )
    return target_x, target_y, target_z


def optical_to_link(point: Vec3) -> Vec3:
    """共原点、光轴沿 link 前方的安装关系。"""
    optical_x, optical_y, optical_z = point
    link_x = optical_z      # 光学前方，放到机体式的 X。
    link_y = -optical_x     # 光学右方，对应机体式的负 Y。
    link_z = -optical_y     # 光学下方，对应机体式的负 Z。
    return link_x, link_y, link_z


def quaternion_rotate(point: Vec3, quaternion: Tuple[float, float, float, float]) -> Vec3:
    """四元数顺序 x,y,z,w；先归一化，再用 q 对点向量作旋转。"""
    if not all(math.isfinite(v) for v in point + quaternion):
        raise ValueError("point and quaternion must be finite")
    norm = math.sqrt(sum(v * v for v in quaternion))
    if norm < 1e-12:
        raise ValueError("zero quaternion has no rotation")
    qx, qy, qz, qw = (v / norm for v in quaternion)
    x, y, z = point
    # t = 2 * cross(q_xyz, point); result = point + qw*t + cross(q_xyz, t)
    tx, ty, tz = 2 * (qy * z - qz * y), 2 * (qz * x - qx * z), 2 * (qx * y - qy * x)
    return (
        x + qw * tx + qy * tz - qz * ty,
        y + qw * ty + qz * tx - qx * tz,
        z + qw * tz + qx * ty - qy * tx,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pitch-deg", type=float, default=0.0,
                        help="旧 TF 教学模型中的绕 +Y 角度，单位度")
    args = parser.parse_args()
    if not math.isfinite(args.pitch_deg):
        parser.error("pitch 必须是有限数值")

    yaw_rad = math.radians(90.0)
    displacement_world = rotate2d(3.0, -1.0, yaw_rad)
    world_x = displacement_world[0] + 2.0
    world_y = displacement_world[1] + 1.0
    print("例题一：从底盘坐标换到场地坐标")
    print("  输入：底盘原点在场地 (2, 1) m，yaw 为 90°。")
    print("  目标在底盘前方 3 m、右侧 1 m，即 (3, -1) m。")
    print(f"  第一步：90° 转成弧度，得到 {yaw_rad:.6f} rad。")
    print("  第二步：把前方和右方的位移旋转成场地方向。")
    print("          得到相对底盘原点的场地位移 ({:.6f}, {:.6f}) m。".format(*displacement_world))
    print("  第三步：加底盘原点的场地位置 (2, 1) m。")
    print(f"          目标场地坐标 = ({world_x:.6f}, {world_y:.6f}) m。")
    print("  两组坐标描述同一个目标，分别从底盘原点和场地原点量起。")
    point_body = world_to_body((world_x, world_y), (2.0, 1.0), yaw_rad)
    print("  逆变换：先减 (2, 1)，再转回底盘方向，得到 ({:.6f}, {:.6f}) m。".format(*point_body))

    point_optical = (1.0, 0.0, 3.0)
    point_link = optical_to_link(point_optical)
    pitch_rad = math.radians(args.pitch_deg)
    rotation = rot_y(pitch_rad)
    rotated_displacement = transform_point(point_link, rotation, (0.0, 0.0, 0.0))
    point_gimbal = transform_point(point_link, rotation, (0.1, 0.0, 0.0))
    point_base = (point_gimbal[0], point_gimbal[1], point_gimbal[2] + 0.2)
    print("\n例题二：光学目标经过相机和云台，换到底盘坐标")
    print(f"  输入：光学坐标 {point_optical} m，pitch 为 {args.pitch_deg:.3f}°。")
    print("        光学 X 向右、Y 向下、Z 向前。")
    print("  第一步：按前、左、上换轴，camera_link 中的点 = ({:.6f}, {:.6f}, {:.6f}) m。".format(*point_link))
    print("  第二步：按 pitch 旋转位移，得到 ({:.6f}, {:.6f}, {:.6f}) m。".format(*rotated_displacement))
    print("  第三步：加相机在云台前方的 0.1 m。")
    print("          gimbal 中的点 = ({:.6f}, {:.6f}, {:.6f}) m。".format(*point_gimbal))
    print("  第四步：加云台在底盘上方的 0.2 m。")
    print("          base 中的点 = ({:.6f}, {:.6f}, {:.6f}) m。".format(*point_base))
    print("  相机原点在 base 中 = (0.100000, 0.000000, 0.200000) m。")

    aim_point = (3.0, -1.0, 1.0)
    geometric_yaw = math.atan2(aim_point[1], aim_point[0])
    horizontal_distance = math.hypot(aim_point[0], aim_point[1])
    elevation = math.atan2(aim_point[2], horizontal_distance)
    print("\n例题三：在固定瞄准参考系中求角度")
    print("  输入：目标在前方 3 m、右侧 1 m、上方 1 m，即 (3, -1, 1) m。")
    print("  第一步：俯视图中，用 atan2(-1, 3) 求水平角。")
    print(f"          yaw = {geometric_yaw:.6f} rad = {math.degrees(geometric_yaw):.6f}°。")
    print(f"  第二步：水平距离 sqrt(3² + (-1)²) = {horizontal_distance:.6f} m。")
    print("  第三步：侧视图中，用 atan2(高度, 水平距离) 求仰角。")
    print(f"          elevation = {elevation:.6f} rad = {math.degrees(elevation):.6f}°。")
    print("  方向判断：向右转，所以 yaw 为负；向上抬，所以仰角为正。")


if __name__ == "__main__":
    main()
