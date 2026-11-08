# 机器人学基础：阅读与练习

机器人学研究机器人怎样表示位置和朝向，以及怎样产生需要的运动。这份材料先介绍这些问题，再学习旋转、平移和坐标变换，最后用云台和底盘举例。正文会说明每一步在算什么，再给出公式和例题。

## 从哪里开始

先读[正文](培训讲义.md)第 1～3 节，理解机器人学的基本问题，以及同一个点怎样用不同坐标系表示。第 4～6 节将这些计算用到相机和云台，第 7 节简要说明时间对应。第 8 节带你运行示例，第 9 节提供代码作业，其中第 9.2 节介绍大小 yaw 的进阶内容。文末另有旋转矩阵检查的补充阅读和参考资料。

同步培训仓库后，进入 `03-robotics-basics` 目录阅读和运行。下方命令沿用克隆位置 `~/venom_cpp_basics/training`；下载材料包的同学可将解压后的 `venom_robotics_next` 放在主目录，代码目录对应为 `~/venom_robotics_next/code`。数学示例和作业用 Python 3.10+ 标准库。运行可选的 ROS2 示例时，沿用前面准备的 Ubuntu 22.04 + ROS 2 Humble 环境。

| 文件 | 用途 |
| --- | --- |
| [培训讲义.md](培训讲义.md) | 正文、坐标换算示意图、两张应用图和计算例题。 |
| [作业说明.md](作业说明.md) | 基础作业、进阶作业的接口和检查方法。 |
| [code/robotics_demo.py](code/robotics_demo.py) | 逐步输出坐标变换和瞄准角的计算结果，提供变换工具。 |
| [code/big_small_yaw_demo.py](code/big_small_yaw_demo.py) | 逐步输出小 yaw、大 yaw 平台与底盘之间的位置换算。 |
| [code/exercise.py](code/exercise.py) | 基础作业的两个函数和进阶作业的一个函数。 |
| [code/test_exercise.py](code/test_exercise.py) | 按基础、进阶两档自动检查。 |
| [code/tf_target_demo.py](code/tf_target_demo.py) | 使用已有 TF 广播器，将合成目标转换到底盘坐标系。 |

## 运行与自检

在 `code` 目录运行数学示例，对照正文中的中间结果：

```bash
cd ~/venom_cpp_basics/training/03-robotics-basics/code
python3 robotics_demo.py --pitch-deg 30
```

接着按[作业说明](作业说明.md)完成 `exercise.py`。基础为必做，进阶为选做；两档都由程序检查，提交完成的 `exercise.py` 即可。

```bash
python3 test_exercise.py --level basic
python3 test_exercise.py --level advanced
```

进阶作业的结构与安装偏移可先运行 `python3 big_small_yaw_demo.py` 对照，再完成第三个函数。
