"""大小 yaw 水平转向示例。安装尺寸为练习参数，距离 m，内部角度 rad。"""
import argparse
import math
from robotics_demo import rotate2d


def yaw_transform(point, yaw, offset):
    """目标点从子系换到父系：水平旋转，再加父系表达的安装偏移。"""
    x, y = rotate2d(point[0], point[1], yaw)
    return x + offset[0], y + offset[1], point[2] + offset[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--big-yaw-deg", type=float, default=90.0, help="大 yaw 相对底盘的角度，单位度")
    parser.add_argument("--small-yaw-deg", type=float, default=-90.0, help="小 yaw 相对大 yaw 的角度，单位度")
    args = parser.parse_args()
    if not all(math.isfinite(v) for v in (args.big_yaw_deg, args.small_yaw_deg)):
        parser.error("两段 yaw 必须是有限数值")

    point_small = (2.0, 0.0, 0.5)
    small_offset = (0.3, 0.2, 0.0)  # 用大 yaw 的轴表达小 yaw 原点位置。
    big_offset = (0.0, 0.0, 0.2)    # 用底盘的轴表达大 yaw 原点位置。
    point_large = yaw_transform(point_small, math.radians(args.small_yaw_deg), small_offset)
    point_base = yaw_transform(point_large, math.radians(args.big_yaw_deg), big_offset)
    print("进阶示例：小 yaw → 大 yaw 平台 → 底盘")
    print(f"  大 yaw 相对底盘：{args.big_yaw_deg:.3f}°；小 yaw 相对大 yaw：{args.small_yaw_deg:.3f}°。")
    print(f"  小 yaw 中的输入点：{point_small} m。")
    print(f"  小 yaw 原点在大 yaw 中的位置：{small_offset} m。")
    print(f"  大 yaw 原点在底盘中的位置：{big_offset} m。")
    print("  第一步：按小 yaw 角旋转，再加小 yaw 安装偏移。")
    print("          大 yaw 平台中的点 = ({:.6f}, {:.6f}, {:.6f}) m。".format(*point_large))
    print("  第二步：按大 yaw 角旋转，再加大 yaw 安装偏移。")
    print("          底盘中的点 = ({:.6f}, {:.6f}, {:.6f}) m。".format(*point_base))


if __name__ == "__main__":
    main()
