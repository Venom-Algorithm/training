# 4. 机器人自主导航与 Nav2 入门

> 从 ROS2 到 RoboMaster 自主导航系统  
> 适用对象：完成上一课《3. ROS2基础》的算法组新同学  
> 建议环境：Ubuntu 22.04 + ROS2 Humble + Gazebo Classic + RViz2  
> 建议用时：正文学习与操作约 4～6 小时，作业约 3～5 小时；环境问题另计

## 开始之前

如果你以前打开过一个导航仓库，大概会有这种体验：`planner_server`、`controller_server`、`amcl`、`costmap`、`bt_navigator` 全都摆在面前，配置文件有几百行，终端同时跑着十几个节点。每个名字查一查似乎都懂，但机器人到底为什么会动、走不过去时应该看哪里，还是说不清楚。

这次我们换个顺序。**先让机器人走起来，再去追它用到了哪些数据，最后才打开配置文件和框架。** 这一课只关注整个导航系统是怎么跑起来的，把规划算法推导和源码实现留到后续专题。

学完以后，希望你能把一次导航大致讲清楚：目标点是怎么发过去的；机器人靠什么知道自己在哪里；障碍物信息从哪里来；谁负责生成路径；谁把路径变成速度指令；如果导航失败，应该先检查哪一块。

这里使用 TurtleBot3 做入门，是因为它的仿真和 Nav2 已经接好。我们重点借它认识导航系统的数据流，最后一章再专门讨论它与 RM 全向底盘的区别。

### 本课边界

本课不需要手写 A*、DWA 或 MPC，也不用读懂 Nav2 源码、从零建图或部署整套 RM 哨兵工程。遇到 YAML 里的诸多参数和专业名词，先搞清楚它们各自解决什么问题即可。

### 阅读方法

文中用三种标记：

- **动手**：请跟着运行命令，亲眼看结果。
- **想一想**：先自己猜，再看后面的解释；不要求一次猜对。
- **作业打卡**：正文中标有【对应作业 A～D】的位置，做完实验顺手截图并记下两三句话即可，最后直接汇总成报告，无需重复劳动。

> 文中截图来自培训机的 Humble 环境实测，按对应操作展示；

---

# 0. 环境准备：先确保可以打开仿真

上一课已经安装过 ROS2，这次尽量沿用同一台 Ubuntu 22.04 + Humble 环境。Nav2 官方快速入门使用 TurtleBot3 的 Gazebo 仿真作为示例，我们也从这里开始。

> **版本提醒**：以下命令针对 Humble 的 Gazebo Classic 示例。网上 Nav2 文档默认展示 Rolling、Jazzy 的配置和新版 Gazebo 仿真，注意区分启动文件、插件名和参数版本。为了与上一课 Humble 环境保持一致，本次沿用 Gazebo Classic 入门示例。

## 0.1 安装依赖

打开终端，先确认版本：

```bash
source /opt/ros/humble/setup.bash
printenv ROS_DISTRO
# 预期输出：humble
```

安装本课使用的包（已经装过的会跳过）：

```bash
sudo apt update
sudo apt install -y \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-turtlebot3-gazebo \
  ros-humble-gazebo-ros-pkgs
```

如果上一课使用了 `conda activate rm_ros2`，本课建议先开一个**未激活 conda 的新终端**运行系统 ROS2；不要把另一套 Python 环境与 ROS2 系统包混起来。确实需要继续用上一课环境的同学，先确认 `ros2`、RViz、Gazebo 都能正常启动，再往下做。

验证启动文件存在：

```bash
ros2 pkg prefix --share nav2_bringup
ros2 launch nav2_bringup tb3_simulation_launch.py --show-args
```

后一个命令会列出可传入的启动参数。我们后面会用到 `headless` 和 `params_file`。

## 0.2 启动一次完整导航环境

启动前先设置 TurtleBot3 型号与 Gazebo 模型路径：

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle
export GAZEBO_MODEL_PATH=/usr/share/gazebo-11/models:/opt/ros/humble/share/turtlebot3_gazebo/models${GAZEBO_MODEL_PATH:+:$GAZEBO_MODEL_PATH}
export GAZEBO_MODEL_DATABASE_URI=""
ros2 launch nav2_bringup tb3_simulation_launch.py headless:=False
```

正常情况下会弹出 Gazebo 和 RViz 两个窗口，第一次加载模型和地图稍慢。Gazebo 模拟物理世界，RViz 则相当于机器人系统的“仪表盘”：地图、位置、激光、路径、代价地图都能放在里面观察。**后面大部分实验主要观察 RViz，必要时再对照 Gazebo。**

![图 0-1：Gazebo 仿真场景与 RViz 地图](<截图/截图 2026-11-07 21-04-37.png>)

图 0-1：左侧为 Gazebo 仿真场景，右侧为 RViz 地图。

上面的模型路径和禁用在线模型库设置用于避免 Gazebo 联网加载模型时卡住。若仍遇到未响应、场景空白等问题，可将启动命令和终端报错提供给 AI 工具，辅助排查网络、模型路径或图形环境问题。

## 0.3 操作约定

本课默认使用两个终端：终端 A 持续运行仿真，终端 B 用来查看 ROS2 数据。**每个新终端都需要先执行 `source /opt/ros/humble/setup.bash`**（若需要启动仿真，还要带上 `TURTLEBOT3_MODEL` 和 `GAZEBO_MODEL_PATH`；也可以写进 `~/.bashrc`）。修改 YAML 后，先停止仿真再重新启动，确保对照实验加载了新参数。

若 Ctrl+C 后一直无法退出，可在终端 B 执行：

```bash
pkill -9 -u "$USER" -f '(^|/)(gzserver|gzclient|rviz2|robot_state_publisher|component_container_isolated)( |$)|(^|/)ros2 launch nav2_bringup tb3_simulation_launch[.]py( |$)'
```

这会强制结束当前用户的仿真、RViz、Nav2 容器及本课启动器；仅在没有其他 ROS 任务运行的培训机上使用，清理后再启动下一组配置。

---

# 1. 先让机器人走起来

本章目标很简单：**给机器人一个目标点，看它从当前位置走过去。** 此时先不研究有哪些 Server，也不要急着打开配置文件。

## 1.1 两次点击

在 RViz 中先用 **2D Pose Estimate** 设置机器人初始位姿：在地图上点选机器人当前大致位置，拖动箭头让朝向与 Gazebo 中接近。这一步用于帮定位模块初始化“我大概在地图哪个位置”。

接着选择 **Nav2 Goal**（个别界面显示为 2D Nav Goal），在地图上找一块无障碍区域，点击并拖出目标朝向，观察机器人开始运动。

![图 1-1：初始位姿与导航目标工具，以及导航中的机器人和路径](<截图/截图 2026-11-07 21-06-02.png>)

图 1-1：RViz 顶部的 **2D Pose Estimate** 和 **Nav2 Goal** 分别用于设置初始位姿和发送目标；右侧地图中可见机器人及规划路径，导航面板的 Feedback 为 active，表示任务仍在执行。

**【对应作业 A-1】** 机器人成功到达目标了吗？截一张能够同时看到机器人、目标点和全局路径的 RViz 图。

## 1.2 只看三个东西

先不必认全 RViz 上的颜色和箭头，只观察三个东西：

| 看到的东西 | 先把它理解成 | 后面对应的内容 |
|---|---|---|
| 地图上的目标箭头 | 我希望机器人到哪里 | 导航 Action |
| 从机器人延伸出去的路线 | 导航系统建议走哪条路 | Planner、`nav_msgs/Path` |
| 机器人实际运动 | 机器人每一刻应该怎样动 | Controller、速度指令 |

**想一想：** 画出来的路径和机器人实际走过的轨迹一定重合吗？为什么？

不一定。全局路径给出的是参考路线，真实运动还会受到底盘运动学约束、控制器采样、定位误差和局部障碍变化的影响，机器人会边走边调整。

## 1.3 用上一课的 ROS2 知识看一下

另开终端 B：

```bash
source /opt/ros/humble/setup.bash
ros2 action list -t
ros2 action info /navigate_to_pose
ros2 topic list -t
```

你应该能找到导航相关的 Action。**Action 很适合导航这种需要一段时间才能完成、过程中有反馈、还可能被取消的任务。**

可以把它和上一课的 Topic、Service 对比着记：

- Topic：持续发布数据，例如里程计、雷达和速度指令。
- Service：发出一次请求，得到一次响应，例如请求清理 Costmap。
- Action：提交一个需要持续执行的任务，例如“导航到这个目标点”。

一次 `NavigateToPose` 大致包含三个部分：

- **Goal**：目标位姿，通常是 `geometry_msgs/PoseStamped`，还可以指定要使用的行为树文件。
- **Feedback**：执行过程中的反馈，例如当前位姿、剩余距离、预计剩余时间和恢复次数。
- **Result**：任务结束后的结果。客户端还可以取消正在执行的 Goal。

因此，在 RViz 里点击 Nav2 Goal，本质上是向 Nav2 的 Action Server 提交了一项导航任务。后面如果 RM 决策节点要调用 Nav2，通常也会采用同样的 Action Client 方式。

现在不用自己写 Action 客户端。先记住：**Goal 是任务要求，Feedback 是过程反馈，Result 是最终结果；取消也是 Action 的一部分。**

---

# 2. 导航到底依赖哪些数据？

看过机器人走路之后，反过来想：它能走，是因为它“知道”三件事：**现在在哪、哪里有障碍、要去哪里。** 第三件事我们已经通过 Nav2 Goal 给过了，接下来追前两件。

## 2.1 它怎么知道自己在哪：`map`、`odom`、`base_link`

上一课讲过 TF2。放到移动机器人上，核心坐标系链条是：

```text
map ──> odom ──> (base_footprint) ──> base_link ──> [lidar / 其他传感器坐标系]
```

- `base_link`：机器人自身坐标系。往前走时，机器人在这个坐标系里“前方”方向不变。（在 TurtleBot3 默认仿真及很多标准配置中，`odom` 与 `base_link` 之间还会有一层贴合地面的投影坐标系 `base_footprint`。）
- `odom`：局部、连续的里程计参考系，适合表示机器人短时间内的连续运动，但长时间运行会积累漂移。
- `map`：全局参考系，定位模块负责把机器人对齐到这张全局地图上。

通常由里程计模块提供 `odom → base_footprint → base_link`，由定位模块（例如本例中的 AMCL，或实车常用的 LIO 等方案）提供 `map → odom`。

**动手：**

```bash
ros2 topic echo /odom --once
ros2 topic hz /odom
ros2 run tf2_ros tf2_echo map base_link
# 可选：生成整棵 TF 树的 PDF 图（保存在当前目录）
ros2 run tf2_tools view_frames
```

然后让机器人再去一个目标点，观察位置数值的变化。`/odom` 话题提供机器人的运动状态（位姿与速度）；TF 则维护各个坐标系之间的实时转换关系。

![图 2-1：RViz 中的 TF 坐标系树](<截图/截图 2026-11-07 21-11-09.png>)

图 2-1：展开 TF 的 Tree，可看到 `map → odom → base_footprint → base_link → base_scan`，把地图、里程计、底盘与雷达串在同一棵坐标系树上。

**想一想：** 为什么已经有 `/odom`，还需要在 RViz 中用 2D Pose Estimate 设置初始位姿？

因为局部里程计只记录相对于起点的运动，并不知道自己处在整张地图的哪个位置。给定初始位姿后，AMCL 才能把激光观测与地图匹配起来，算出稳定的 `map → odom` 变换，把“地图上的目标点”和“机器人当前位置”联系起来。

## 2.2 它怎么知道哪里有障碍：从传感器到 Costmap
**动手：在 RViz 中看雷达实际看到了什么。**

1. 在左侧 Displays 中找到并勾选 `LaserScan`；如果没有，点击 **Add → By display type → LaserScan**，将 Topic 设为 `/scan`。
2. 放大机器人附近的画面，对照 Gazebo 中的墙壁和柱子，观察激光点是否落在这些障碍物的表面。激光点表示雷达测到的物体表面，不是机器人规划的路线。

**想一想：** 墙后面的物体为什么不一定有激光点？雷达只能测到当前视野内、未被遮挡且有有效回波的表面，并不是直接读取整张地图。

终端只用于辅助检查，不需要逐项阅读整屏距离数字：

```bash
ros2 topic echo /scan --once --field header
ros2 topic hz /scan
# 看 frame_id 确认数据所属坐标系，看频率确认雷达是否持续发布；Ctrl+C 停止查看频率
```

`/scan` 一般是 `sensor_msgs/msg/LaserScan`，表示一圈方向上的距离观测。真实 RM 机器人常使用 3D 激光雷达输出 `PointCloud2`，相机也可以通过检测或深度估计提取障碍物。**这些原始传感器观测需要先填入代价地图（Costmap），才能供规划器和控制器判断哪里可通行。**

可以先记住一条最简单的数据链：

```text
激光雷达观测（/scan）
          ↓
Costmap 的障碍物层
          ↓
哪些位置不可通行、哪些地方代价高
          ↓
规划 / 控制
```

这里要注意区分雷达的两条数据去向：**同一台雷达既可以拿去辅助定位，也可以直接用来更新障碍物。** 在官方示例里，AMCL 读取雷达和地图来纠正位姿；Costmap 同时也会直接订阅 `/scan` 来标记实时障碍物。即使实车用上了 LIO 定位，点云依然会进入 Costmap 用于避障。

## 2.3 地图和 Costmap 有什么区别？

“静态地图”描述的是场地固有结构：墙在哪、哪些地方被占据、哪些区域未知。Costmap 则在此基础上，结合机器人尺寸和实时传感器观测，给不同位置赋上通行代价。

除了标记“绝对不能碰”的障碍物，障碍物周边区域往往也不适合贴着走，因此 Costmap 会引入 **Inflation Layer（膨胀层）**，让障碍物周围的代价值由高到低平滑衰减。

在本课 Humble 默认示例里，同时运行着两套代价地图：

| | Global Costmap | Local Costmap |
|---|---|---|
| 作用范围 | 覆盖全局地图，辅助选择整体路线 | 跟随机器人周边滚动窗口，辅助实时控制与避障 |
| 常见参考系 | `map` | `odom` |
| 服务对象 | 全局规划器（Planner） | 局部控制器（Controller） |
| 本课主要观察 | 规划路线与障碍物保持多大安全距离 | 机器人附近的实时障碍代价分布 |

两张代价地图具体融合哪些障碍信息完全取决于 YAML 配置。比如在本课 Humble 默认参数中，**Global Costmap 除静态地图外同样订阅了 `/scan` 的障碍物层**；Local Costmap 则使用 Voxel Layer 处理实时观测。

**动手（含动态放障实验）：**
1. 在 RViz 左侧 Displays 面板中查看 Global Costmap 和 Local Costmap。在本课实测 RViz 界面里，它们分别位于 **`Global Planner → Global Costmap`** 和 **`Controller → Local Costmap`** 展开项下；如果某一项未勾选，可以展开后勾选查看。
2. 给机器人发送一个较远的目标点；趁机器人正在行进时，切到 **Gazebo** 窗口，从顶部工具栏点选一个圆柱（Cylinder）或方块（Box），**直接拖到机器人正前方的路径上**。切回 RViz 观察代价地图和路径的变化。

![图 2-2a：叠加在静态地图上的 Global Costmap](<截图/截图 2026-11-07 21-17-52.png>)

图 2-2a：开启 Global Costmap、关闭 Local Costmap，彩色代价区域覆盖全局场地，墙壁和柱子周围有膨胀区域。

![图 2-2b：叠加在静态地图上的 Local Costmap](<截图/截图 2026-11-07 21-17-58.png>)

图 2-2b：在相近机器人位置关闭 Global Costmap、开启 Local Costmap，彩色代价区域只覆盖机器人周围的局部窗口，窗口外仍可看到静态地图。

**【对应作业 A-2】** 往 Gazebo 路径上突然放一个新障碍物后，RViz 里的 Costmap 和机器人的路线发生了什么变化？截一张图并简短说明原因。

## 2.4 把“机器人认识环境”串起来

到这里，可以稍微展开第一章的黑盒：

```text
        已知地图 ───────────────┐
                              ├──> Global Costmap ──> 规划
雷达观测 ──> 障碍物数据 ───────┤
                              └──> Local Costmap ──> 控制

里程计 / 定位 ──> TF 与机器人状态 ─────────> 规划、控制
```
在实际 Nav2 工程中，Global 和 Local Costmap 可以按需配置各自的 Layer，分别订阅所需的传感器话题和 TF。
如果有一天你看到一份 RM 工程同时启动了 MID-360、Point-LIO、点云预处理、Costmap、Nav2，先不要急着读每个源码。先问：**它最终向 Nav2 提供的是位姿、环境障碍，还是底盘运动能力？** 通常把这个问题分清楚，仓库结构就会好懂不少。

---

# 3. 导航系统为什么会这样走？

现在机器人知道自己在哪，也知道地图和障碍物是什么样的。剩下的问题是：**谁来选路线，谁来让机器人沿路线运动？**

## 3.1 规划与控制的分工

先看这个简图：

```text
当前位置 + 目标点 + Global Costmap
                ↓
           Planner Server
                ↓
         全局路径（Path）
                ↓
           Controller Server  ← 机器人当前状态 / Local Costmap
                ↓
       速度指令（cmd_vel_nav）
                ↓
         Velocity Smoother
                ↓
          速度指令（cmd_vel）
                ↓
               底盘
```

Planner 回答“**大体应该走哪条路**”，Controller 回答“**眼下这一小段应该怎么动**”。

就像步行去食堂：先在地图上看好走哪条路是全局规划；走在路上时实时迈步、避开迎面走来的人则是局部控制。

常见全局规划算法有 Dijkstra、A* 等。**在 Humble 默认示例的 `nav2_params.yaml` 里，Planner 插件采用 `NavfnPlanner`，且默认 `use_astar: false`（即采用 Dijkstra 方式展开搜索）。**

Controller 本课默认使用 DWB 插件。它会综合参考路径、机器人加减速能力以及 Local Costmap 代价，在当前时刻采样并评估出最合适的运动速度指令（`Twist`）。

此外，默认启动链路中还串联了 **Velocity Smoother（速度平滑器）**。Controller 算出的期望速度会先发给 Velocity Smoother，按速度和加速度上限平滑后再发往底盘。

注意区分两个名字相近的模块：**Velocity Smoother 平滑的是速度指令（`Twist`），而 `smoother_server` 平滑的是几何路径（`Path`）**。本课主要观察 Velocity Smoother 在速度链路中的表现。

## 3.2 Action、Path 和 Topic：一次导航内部怎样配合？

前面已经知道，RViz 会向 Nav2 发送 `NavigateToPose`。但 Nav2 收到目标之后，Planner 和 Controller 是怎么配合的？这里值得多看一眼，因为它能把前面学过的 Action、Topic 和 Path 真正串起来。

在默认的导航行为树中，可以先把过程理解成这样：

```text
RViz / RM 决策节点
       │
       │ Action：NavigateToPose（目标位姿）
       ▼
  BT Navigator（执行行为树）
       │
       │ ① 行为树节点调用 Action：ComputePathToPose
       ▼
  Planner Server
       │
       └── Result：nav_msgs/Path
                    │
                    ▼
             行为树保存路径
                    │
                    │ ② 行为树节点调用 Action：FollowPath
                    │    Goal 中携带刚得到的 Path
                    ▼
             Controller Server
                    │
                    └── Topic：cmd_vel_nav
                                ▼
                          Velocity Smoother
                                │
                                └── Topic：cmd_vel
                                            ▼
                                           底盘
```

实际运行时，默认行为树会以一定频率周期性地调用 Planner 重新规划，并持续将最新路径交给 Controller 跟踪；遇到突发阻碍时还会触发恢复行为。

结合这张图，可以理清两个核心机制：

**第一，Planner 和 Controller 之间通过行为树和 Action 传递路径。** BT Navigator 调用 Planner Server 的 `ComputePathToPose` Action，拿到返回的 `nav_msgs/Path` 后，再把这条路径放进 `FollowPath` Action 的 Goal 里发给 Controller Server。

**第二，`/plan` 话题主要用于可视化和调试。** Planner Server 每次算出路径后都会顺带往 `/plan` 发布一份，方便 RViz 显示。因此只看 `ros2 topic list` 只能看到可视化话题，结合 Action 才能看清模块间的调用链。

在 Humble 默认启动配置中，Controller Server 的速度输出被重映射到 `/cmd_vel_nav`；Velocity Smoother 订阅该话题，平滑后再发布到 `/cmd_vel`：

```text
Controller Server → /cmd_vel_nav → Velocity Smoother → /cmd_vel → 底盘
```

不同机器人或 Launch 文件可能会修改命名空间与重映射（remapping），看陌生工程时以实际运行的话题连接为准。另外，上面这条是 **Controller 正常跟踪路径时的速度链路**；当 `Behavior Server` 执行 `Spin`（原地旋转）、`BackUp`（后退）等恢复动作时，Humble 默认 Launch 会让它直接往 `cmd_vel` 发布指令。
## 3.3 先看到输出，再看配置

导航到一个稍远的目标点时，打开终端 B。先查看 Action 和 Topic 的名字：

```bash
# 看导航相关 Action
ros2 action list -t
ros2 action info /navigate_to_pose
ros2 action info /compute_path_to_pose
ros2 action info /follow_path

# 看路径与速度相关 Topic
ros2 topic list -t | grep -E 'plan|cmd_vel'
ros2 topic info /plan -v
ros2 topic info /cmd_vel_nav -v
ros2 topic info /cmd_vel -v
```

在本课默认示例中，可以看到 `/plan`（`nav_msgs/msg/Path`）、`/cmd_vel_nav` 和 `/cmd_vel`（`geometry_msgs/msg/Twist`）。

输出较多时，只看 Action 的服务端是谁，以及 Topic 的发布者和订阅者分别是谁，把它们与上一节的数据流对上即可；GID、QoS 等细节暂时跳过。

在默认行为树配置下，导航过程中 Planner 会以 1 Hz 左右的频率周期性重规划。由于一条 `Path` 消息包含几十上百个路径点，直接打印完整消息会瞬间刷屏，可以只查看消息头（包含时间戳和 `map` 坐标系）来确认规划输出：

```bash
ros2 topic echo /plan --field header --once
```

（提示：需要先运行监听命令，再去 RViz 发送导航目标。）

在机器人导航时，任选下面一个命令查看速度话题，重点看 `linear.x`（前进速度）和 `angular.z`（转弯角速度），观察直行、转弯和停车时数值的变化；按 Ctrl+C 结束。

```bash
ros2 topic echo /cmd_vel_nav
# 或
ros2 topic echo /cmd_vel
```

`/cmd_vel_nav` 是控制器输出，`/cmd_vel` 是经过速度平滑后发给底盘的指令。如果话题暂时没有输出，先确认机器人是否正在执行导航任务。
> 观察完后，可以顺手记住这几个核心接口的名字：提交任务用的是 `NavigateToPose`、`ComputePathToPose`、`FollowPath`（Action）；持续发布数据用的是 `/plan`、`/cmd_vel_nav`、`/cmd_vel`（Topic）。
## 3.4 实验一：调整膨胀半径对全局路径的影响

确认基础导航正常后，我们来动手修改第一处配置。

### 准备两份对照配置

新开终端，将 Humble 默认配置文件复制到自己的工作目录下修改，保持 `/opt/ros/humble` 下的原文件不动：

```bash
mkdir -p ~/rm_nav2_training/config
cp "$(ros2 pkg prefix --share nav2_bringup)/params/nav2_params.yaml" \
   ~/rm_nav2_training/config/nav2_base.yaml
cp ~/rm_nav2_training/config/nav2_base.yaml \
   ~/rm_nav2_training/config/nav2_inflation_small.yaml
cp ~/rm_nav2_training/config/nav2_base.yaml \
   ~/rm_nav2_training/config/nav2_inflation_large.yaml
```

打开这两份 YAML，定位到 **`global_costmap → global_costmap → ros__parameters → inflation_layer`**（注意修改的是 `global_costmap` 段落下的膨胀层，保持 `local_costmap` 下的同名段落不变）。

Humble 默认配置中，`robot_radius` 为 `0.22`，`inflation_radius` 默认值为 `0.55`。我们在两份配置中分别将它改为 `0.35`（缩小膨胀区）和 `0.85`（扩大膨胀区）：

```yaml
# nav2_inflation_small.yaml 中，位于 global_costmap 的 inflation_layer 下
inflation_layer:
  plugin: "nav2_costmap_2d::InflationLayer"
  cost_scaling_factor: 3.0
  inflation_radius: 0.35
```

```yaml
# nav2_inflation_large.yaml 中，位于 global_costmap 的 inflation_layer 下
inflation_layer:
  plugin: "nav2_costmap_2d::InflationLayer"
  cost_scaling_factor: 3.0
  inflation_radius: 0.85
```

保留原文件其余部分，只替换 `inflation_radius` 数值。机器人的物理半径 `robot_radius` 代表真实车体尺寸，保持 `0.22` 不动。

### A/B 对照

先停止已有仿真，带参数启动小膨胀半径配置：

```bash
export TURTLEBOT3_MODEL=waffle
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models
ros2 launch nav2_bringup tb3_simulation_launch.py headless:=False \
  params_file:=$HOME/rm_nav2_training/config/nav2_inflation_small.yaml
```

设置初始位姿后，选一个需要绕过圆柱或墙角的导航目标，截图保存 Global Costmap 和全局路径。随后停止仿真，换用 `nav2_inflation_large.yaml` 启动，**使用尽量一致的起点、朝向和目标点**，再次观察并截图。

> **实验小提示**：在 `0.35` 的小膨胀半径下，全局规划器可能会画出一条非常贴近障碍物的路径；而由于我们没有改 `local_costmap`（膨胀半径仍为默认的 `0.55`），机器人走到窄处时，局部控制器可能会因为觉得离障碍太近而减速甚至停滞。这个现象刚好直观展示了 Global Costmap 和 Local Costmap 各司其职。

![图 3-1：小膨胀半径下的 Costmap 与路径](<截图/截图 2026-11-07 21-36-08.png>)

图 3-1：小膨胀半径（`0.35`）下，柱子周围的全局代价区域较窄，柱间可见较多白色低代价区域。

![图 3-2：大膨胀半径下的 Costmap 与路径](<截图/截图 2026-11-07 21-41-12.png>)

图 3-2：大膨胀半径（`0.85`）下，全局代价区域扩大并相互连接，但路径仍经过相近的通道。机器人附近颜色较浓的矩形区域还叠加了 Local Costmap，比较全局膨胀效果时优先看其外侧的柱子和墙边。

**想一想：** 障碍物周围的高代价区域扩大后，全局路径在任何起终点下都会发生明显改变吗？

这取决于起终点与障碍物的相对位置。如果起终点之间本来就在开阔地带，远离障碍物膨胀区，两条路径看起来就会差不多；而在需要穿过圆柱阵列或贴近拐角时，大膨胀半径下的路径会明显向外绕开。**如实记录你所选点位下的真实表现即可。**

**【对应作业 B】** 分别截下小膨胀半径（`0.35`）和大膨胀半径（`0.85`）下的 Global Costmap 与全局路径图，用两三句话说明现象与原因。
## 3.5 观察体验：路径没变，为什么车走得慢了？

这次不改 Planner、Costmap，只改 Controller 的速度限制。仍然从 `nav2_base.yaml` 复制出两份配置，避免把上一实验的变化带进来。

```bash
cp ~/rm_nav2_training/config/nav2_base.yaml \
   ~/rm_nav2_training/config/nav2_speed_slow.yaml
cp ~/rm_nav2_training/config/nav2_base.yaml \
   ~/rm_nav2_training/config/nav2_speed_default.yaml
```

在 `controller_server → ros__parameters → FollowPath` 下，Humble 默认的 DWB 配置有：

```yaml
max_vel_x: 0.26
max_speed_xy: 0.26
```

`nav2_speed_default.yaml` 保持默认 `0.26`；`nav2_speed_slow.yaml` 把**这两项**都改为 `0.12`，让最大前向速度与最大平面速度约束同步降低。（之所以往小改，是因为下游的 `velocity_smoother` 默认也有 `0.26` 的速度上限把关；如果只把 DWB 往大改，最终输出依然会被平滑器限幅在 `0.26`。）

分别启动两份配置，设置尽量相同的起终点，选一段较直、无遮挡的路线，在 Gazebo 或 RViz 中肉眼观察机器人行进快慢，并比较全局路径是否有明显变化。

**想一想：** 为什么调低控制器的速度上限，全局规划路径依然保持原样？

因为全局路径由 Planner 根据地图与 Global Costmap 算出，只管几何路线与通行代价；而 `max_vel_x` 约束的是 DWB 控制器在跟踪这条路径时的采样速度范围。至于总耗时，除了最高巡航速度外，还会包含起步加速、转弯减速和到达微调的时间。

> **本章小结**：路线绕路或穿墙，优先排查 Global Costmap 和 Planner；路径合理但车走得慢、抖动、贴墙卡住或原地打转，重点关注 Controller、Local Costmap、定位状态与底盘速度链路。

---

# 4. 到这里，再打开 Nav2 这个黑盒

前面我们已经见过路径、速度、定位、地图和 Costmap。现在介绍模块名字，就不再只是背概念了。

## 4.1 一次完整导航是如何组织的

先把上面学到的东西放进一张图里：

```text
                    RViz / RM 上层决策
                            │
              Action：NavigateToPose（Goal）
                            │
                            ▼
                       BT Navigator
                    （协调导航任务流程）
                            │
             ① Action：ComputePathToPose
                            │
                            ▼
                     Planner Server
                            │
                    Result：nav_msgs/Path
                            │
                            ▼
                   行为树保存并使用 Path
                            │
             ② Action：FollowPath（Goal 携带 Path）
                            │
                            ▼
                   Controller Server
                            │
                   Topic：/cmd_vel_nav
                            │
                            ▼
                    Velocity Smoother
                            │
                    Topic：/cmd_vel
                            │
                            ▼
                           底盘

     地图 / TF / 定位 / 传感器 ──> Global / Local Costmap
                                      │
                          供 Planner 和 Controller 使用
```

实际运行中，定位、TF、里程计和传感器持续刷新环境状态；Costmap 实时融合障碍信息；BT Navigator 则根据 Action 反馈决定继续跟踪、周期重规划或是触发恢复行为。

总结一下核心机制：**BT Navigator 通过 `ComputePathToPose` 和 `FollowPath` 两个 Action 把 Planner 与 Controller 串联起来；`/plan` 话题则专门提供给 RViz 等工具做可视化观察。**
## 4.2 Topic、Service、Action：模块之间怎么说话？

上一课已经讲过三种 ROS2 通信方式，这里不重新讲定义，只把它们放回 Nav2 中。

| 通信方式 | 什么时候用 | Nav2 中可以观察的例子 |
|---|---|---|
| Topic | 持续传递状态或指令 | `/scan`、`/odom`、`/tf`、`/plan`、`/cmd_vel_nav`、`/cmd_vel` |
| Service | 一次请求、一次响应 | Lifecycle 状态切换、清理 Costmap、加载地图等服务 |
| Action | 执行一段时间的任务，需要反馈或取消 | `NavigateToPose`、`ComputePathToPose`、`FollowPath`、`Spin`、`BackUp` |

不用背所有接口名称，先记住它们的分工：

- **Topic 像持续播报。** 机器人不断发布里程计，雷达不断发布扫描，控制链路不断发布速度指令。
- **Service 像办一次手续。** 例如请求清理某张 Costmap，服务端完成后返回响应。
- **Action 像派发一项任务。** 例如导航到某个位置，过程中可以查看 Feedback，必要时还可以取消。

可以用下面的命令自己确认，不要只看文档里的示意图：

```bash
ros2 action list -t
ros2 service list -t
ros2 topic list -t

ros2 action info /navigate_to_pose
ros2 action info /compute_path_to_pose
ros2 action info /follow_path
```

如果你的工程使用命名空间，接口名前面可能带有命名空间；请以实际列表为准。

**想一想：** 为什么导航目标更适合用 Action，而不是用 Topic 发布一个目标点就不管了？因为导航是持续任务，调用方通常需要知道任务是否接受、执行到哪里、最终成功还是失败，也可能中途取消。

## 4.3 为什么需要行为树？

想象机器人已经开始去 A 点，但前方突然过不去了。导航不可能永远只执行一次规划，然后死盯着原路线走。它可能需要重新规划，或者调用恢复行为；再不行还得告诉上层“这次任务失败了”。

行为树的作用，就是组织这些**什么时候做什么、失败时怎么处理**的流程。Humble 默认的导航行为树已经包含重新规划和恢复相关逻辑，不需要我们第一节课就学习每种 BT 节点的源码。

可以先记成：

```text
收到导航任务
  ├─ 调用规划 Action，计算路径
  ├─ 调用跟踪 Action，让控制器执行路径
  ├─ 根据条件继续跟踪或重新规划
  ├─ 失败时尝试配置好的恢复行为
  └─ 返回成功、失败或取消
```

**想一想：** 看到机器人绕开了前方新出现的障碍，有哪些可能的原因？

既可能是 Controller 根据 Local Costmap 实时采样出了绕行速度，也可能是 Planner 在周期重规划中更新了全局路线，或者是受阻后触发了 BT 恢复行为。**遇到现象时先提出假设，再去对应的 Action 状态、Costmap 显示或终端日志里找证据验证。**

## 4.4 Lifecycle：为什么节点启动了还不能马上干活？

有时用 `ros2 node list` 已经能看到 `/planner_server`，但导航依然无法工作。这通常与节点的生命周期（Lifecycle）状态有关：**节点进程启动后，还需要完成参数加载（Configure）和激活（Activate），才会真正开始处理导航任务。**
Nav2 中很多核心节点采用 ROS2 Lifecycle（生命周期）机制。入门阶段先认识四个主要状态：

| 状态 | 可以怎么理解 |
|---|---|
| `Unconfigured` | 节点已经创建，但还没有完成配置 |
| `Inactive` | 已经配置好，但还没有激活执行正常工作 |
| `Active` | 已激活，可以正常处理相应任务 |
| `Finalized` | 生命周期已经结束 |

常见启动过程可以简化为：

```text
Unconfigured
     │ configure
     ▼
  Inactive
     │ activate
     ▼
   Active
```

实际还有 deactivate、cleanup、shutdown 和 error 等状态转换，这次不要求掌握完整状态机。

### Lifecycle Manager 做什么？

Nav2 使用 Lifecycle Manager 按照配置顺序管理一组 Lifecycle Node：启动时依次配置、激活；关闭时再按相应流程关闭。它还会通过 Bond 机制监测受管理服务器的连接状态。

在本课 Humble bringup 中，定位相关节点和导航相关节点由不同的 Lifecycle Manager 管理：

- `lifecycle_manager_localization`：管理 `map_server`、`amcl`。
- `lifecycle_manager_navigation`：管理 `controller_server`、`smoother_server`、`planner_server`、`behavior_server`、`bt_navigator`、`waypoint_follower`、`velocity_smoother`。

这里的 `smoother_server` 是路径平滑服务器；`velocity_smoother` 是速度平滑器。它们是两个不同节点。

常见配置里，`autostart: true` 表示启动后自动将受管理节点配置并激活；`node_names` 则列出需要管理的节点及其顺序。知道这两个参数的作用就够了，不需要自己写 Lifecycle Manager。

### 动手：查看节点当前状态

在仿真正常运行时，打开新终端：

```bash
ros2 lifecycle nodes
ros2 lifecycle get /planner_server
ros2 lifecycle get /controller_server
ros2 lifecycle get /velocity_smoother
ros2 lifecycle get /amcl
```

正常运行时，这些受管理节点通常应处于 `active` 状态。具体节点名可能受命名空间影响；如果命令提示找不到节点，先用 `ros2 lifecycle nodes` 查看实际名称。

> 小思考：看到这里你就明白，为什么 `ros2 node list` 能看到节点，还得配合 `ros2 lifecycle get` 确认它处于 `active` 状态，才能说明节点真正投入工作。

> 不要为了完成这个练习，直接对正在运行的 Nav2 节点执行 `deactivate`、`cleanup` 等状态切换。错误操作会让导航系统停止工作。状态切换实验应放在独立测试节点或单独测试环境中。

## 4.5 再看 YAML：只找四处

打开之前备份的 `nav2_base.yaml`。这次只做“找位置”的练习，不用看懂每个参数。

| 配置入口 | 关注什么 | 你已经在哪儿见过它 |
|---|---|---|
| `planner_server` | `planner_plugins`、`GridBased`、`use_astar` | 第 3 章的全局路径 |
| `controller_server` | `controller_plugins`、`FollowPath`、速度约束 | 第 3 章的速度输出 |
| `global_costmap` | `plugins`、`static_layer`、`obstacle_layer`、`inflation_layer` | 第 2、3 章的全局代价地图 |
| `local_costmap` | `rolling_window`、`voxel_layer`、`inflation_layer` | 第 2 章的局部代价地图 |

还可以顺便看一眼 `velocity_smoother` 段落下的 `max_velocity`、`max_accel` 和 `smoothing_frequency`。**Controller 的速度参数决定了控制器采样时尝试多快的速度；而 Velocity Smoother 的参数则是在指令发往底盘前做最后一道平滑与限幅。**

阅读配置时可以把 **Server（服务器容器）** 和 **Plugin（算法插件）** 区分开：`planner_server` 负责提供规划服务框架，具体用什么算法则由插件决定（Humble 默认用 `GridBased` 挂载 `NavfnPlanner`）；`controller_server` 负责控制框架，默认用 `FollowPath` 挂载 `DWB`。以后在 RM 实车上换用全向轮控制器或别的规划器，本质上就是在 YAML 里替换对应的插件配置。

## 4.6 出问题时，先从哪里查？

遇到问题时，可以参考下面这张表确定排查起点：

| 看到的现象 | 优先怀疑什么 | 可以先查什么 |
|---|---|---|
| RViz 里位置或姿态乱跳 | 定位、TF、时间戳 | `/odom`、TF、`/amcl_pose`、`/clock` |
| 目标发出去了，始终没有路径 | Action 状态、定位、Costmap、Planner | `/navigate_to_pose`、`/compute_path_to_pose`、`/plan`、Planner 日志 |
| 有路径但 `/cmd_vel_nav` 没有有效输出 | Controller、路径跟踪状态、Lifecycle | `/follow_path`、Controller 日志、`ros2 lifecycle get /controller_server` |
| `/cmd_vel_nav` 有输出，但 `/cmd_vel` 没有或不合理 | Velocity Smoother、速度限制、节点状态 | 两个速度 Topic、`ros2 lifecycle get /velocity_smoother` |
| `/cmd_vel` 有指令，但机器人不动 | 底盘接口、驱动、安全保护 | 底盘订阅的话题、通信状态和电控反馈 |
| 明明有障碍，Costmap 看不到 | 传感器、Frame、观测源配置 | `/scan` 频率、传感器 TF、Layer 配置 |
| 机器人在障碍附近犹豫或旋转 | Local Costmap、Controller、恢复行为 | 局部代价地图、速度 Topic、BT / Server 日志 |
| 任务突然取消或失败 | Action 结果、行为树、规划/控制失败 | Action 状态、终端日志、Lifecycle 状态 |

排查故障时最有效的习惯是：**顺着数据流逐段确认——先看输入话题有没有数据、节点是否处于 `active` 状态、输出话题有没有指令，定位到具体哪一环断了，再动手改对应的配置。**

**动手（小练习）：** 确认 Planner 是否处于 `active` 状态，再查出 Controller 当前加载的插件 ID，并到 YAML 中找到它对应的 `plugin` 类型。

```bash
ros2 lifecycle get /planner_server
ros2 param get /controller_server controller_plugins
```

默认配置通常返回 `[FollowPath]`，这是插件 ID，不是算法名称。继续查询它对应的插件类型，并与 YAML 中的配置对照：

```bash
ros2 param get /controller_server FollowPath.plugin
```

> 建议在草稿纸上顺手画一下目标、定位/TF、Costmap、Planner、Controller、Velocity Smoother 和底盘之间的连线，看看自己能否不看前文把整条链路串起来。

---

# 5. 把这套思路放回 RoboMaster

到了这里，再看 RM 导航工程会舒服一些：不必一开始就理解 MID-360、Point-LIO、点云处理、行为树、控制插件的全部细节，先看它们负责给谁提供什么。

## 5.1 RM 哨兵导航可以先拆成三层

```text
比赛决策层
  ├─ 去哪个区域巡逻？
  ├─ 是否需要回补给点？
  └─ 当前任务是否应该取消？
               │  导航目标 / 任务指令
               ▼
导航层（例如 Nav2）
  ├─ 在地图上选路线
  ├─ 结合实时障碍物运动
  └─ 输出底盘运动指令
               │  速度目标
               ▼
电控 / 底盘执行层
  └─ 把期望速度落实为电机运动

雷达 / 定位 / 地图 ──> 向导航层提供位姿和环境信息
```

真实实车工程在 Nav2 下游往往还会接上坐标变换、速度限幅、串口/CAN 通信桥接以及底层电机闭环控制，共同把 `/cmd_vel` 的期望速度转化为轮子运动。

## 5.2 它与 TurtleBot3 有哪些不同？

**底盘不同。** TurtleBot3 是差速驱动，不能像全向轮底盘那样直接横移。RM 哨兵如果采用全向底盘，需要匹配运动学能力的 Controller、速度约束以及底盘指令接口。不能把教学 Demo 的 DWB 差速配置直接照搬上实车。

**定位与传感器不同。** 仿真里我们用地图、里程计、AMCL 和 2D 激光；RM 工程可能使用 3D 激光、LIO、点云预处理。接口会复杂一些，但仍然要回答两类问题：导航需要的位姿从哪里来？障碍物怎么进入 Costmap？

**任务也不同。** 普通导航示例只需要从 A 到 B；RM 机器人还要巡逻、争夺点位、回补给、依据比赛状态改变目标。上层决策可以发导航 Action，Nav2 负责执行导航，不必把全部战术逻辑都塞进 Nav2 的内部行为树。

## 5.3 读一个真实仓库：从接口和配置入手

推荐阅读：

- 北极熊战队 RM2025 哨兵导航：<https://github.com/SMBU-PolarBear-Robotics-Team/pb2025_sentry_nav>
- 北极熊战队导航相关插件：<https://github.com/SMBU-PolarBear-Robotics-Team/pb_nav2_plugins>
- 北极熊战队哨兵行为决策：<https://github.com/SMBU-PolarBear-Robotics-Team/pb2025_sentry_behavior>

建议先看 README、Launch 与参数目录，暂时不用编译运行整个 RM 工程。拿着第 4 章的数据流图，去 `pb2025_sentry_nav` 仓库里找找看：它的 Nav2 配置文件放在哪个目录下？里面配置了什么规划器和控制器插件？

**【对应作业 D-2】** 打开 `pb2025_sentry_nav` 仓库的配置文件，查一下它使用的 Planner 插件和 Controller 插件名称。

---

# 6. 作业与提交

作业不需要填写繁琐的表格或手绘复杂大图，**以“运行截图 + 看到的现象 + 两三句话原理解释”为主**。顺着正文中的【对应作业】提示边做边截，很快就能完成。

## 6.1 必做（80 分）

### A. 跑通导航与动态避障观察（25 分）

1. **基础导航（15 分）**：完成第 1 章操作，在 RViz 中用 `2D Pose Estimate` 初始化位姿，再用 `Nav2 Goal` 完成一次 A→B 导航。
   - **提交**：1 张包含地图、目标、全局路径和机器人的 RViz 截图（可另附 10～20 秒短视频），并用一两句话说明为什么启动后需要先点 `2D Pose Estimate`。
2. **动态放障（10 分）**：按 2.3 节动手练习，在机器人导航途中，从 Gazebo 顶部工具栏拖一个方块/圆柱放到机器人前方路径上。
   - **提交**：1 张放入障碍物后的 RViz 截图，简述 Local/Global Costmap 和机器人运动轨迹发生了什么变化。

### B. Costmap 膨胀半径对照实验（25 分）

按 3.4 节实验一，将 Global Costmap 的 `inflation_radius` 分别设为 `0.35` 和 `0.85`，对尽量相同的起终点发起导航。

- **提交**：
  1. 两张对照截图（分别展示 `0.35` 和 `0.85` 下的 Global Costmap 与全局路径）。
  2. 用两三句话回答：两张图里的代价区域和路径有什么区别？什么情况下改大膨胀半径后路径几乎不变，什么情况下路径会明显外绕？

### C. 关键节点与接口状态验证（15 分）

在导航运行过程中，使用终端命令查看系统状态并截图（合在一两张终端截图里即可）：

1. 运行 `ros2 action list -t` 和 `ros2 lifecycle get /planner_server`（或 `/controller_server`），贴出终端输出截图。
2. 用自己的话简短回答（两三句话即可）：
   - BT Navigator 是靠 `/plan` 话题还是靠 Action 把路径传给 Controller 的？`/plan` 起什么作用？
   - 为什么 `ros2 node list` 能看到节点，还要确认它的 Lifecycle 状态是 `active`？

### D. 故障排查与 RM 实车仓库初探（15 分）

1. **故障排查思路（8 分）**：从下面三个场景中**任选一个**，写出你会按什么顺序检查，并列出至少两个用到的 ROS2 命令或 RViz 观察项：
   - 已经发送了目标，但 RViz 中始终不出现全局路径。
   - 全局路径画出来了，但机器人原地不动。
   - RViz 里能看到地图，但激光扫描线与墙体严重错位、机器人位置乱跳。
2. **看一眼真实 RM 哨兵仓库（7 分）**：打开第 5.3 节推荐的北极熊战队仓库 [`pb2025_sentry_nav`](https://github.com/SMBU-PolarBear-Robotics-Team/pb2025_sentry_nav)，找到它的 Nav2 参数配置文件（YAML）：
   - 写出该配置文件在仓库中的路径，以及它配置的 **Planner 插件名**和 **Controller 插件名**（或贴一张配置文件对应段落的截图），看看与本课默认配置有何不同。

## 6.2 选做（最多加 20 分）

**选做：编写自动巡逻节点（20 分）。** 编写一个 Python 或 C++ 节点，完成以下三个验收场景：

| 场景 | 验收要求 |
|---|---|
| 正常巡逻 | 机器人按 A→B→C 顺序依次到达，在终端打印每段任务的执行结果（成功/失败/取消），不能把目标已发送当作已经到达 |
| 修改点位 | 巡逻点位与顺序从配置读取；不修改节点源码，修改配置中的顺序或增加 D 点后，机器人能按新配置完成巡逻 |
| 失败处理 | 将其中一个目标设在地图封闭外墙外侧的明显不可达区域（距可通行区域 > 0.6 m），展示导航失败后的处理过程；程序能识别失败，不误报该点到达或全部巡逻成功 |

**设计自由度：** 可使用 ROS2 Action 客户端或 `nav2_simple_commander`，配置格式、程序结构和日志样式自行设计。失败后可以停止、跳过或有限次重试，说明选择及理由即可；不能无限重试，也不能隐藏失败结果。失败场景建议用 **Publish Point** 在地图封闭外墙外侧取点（距离外墙/可通行区域 > 0.6 m）：Humble 默认 `planner_server.GridBased.tolerance` 为 `0.5 m`，`tb3_world` 中圆柱较细，点在圆柱中心仍可能在容差范围内规划到边缘；若希望直接测障碍物中心，也可参考 3.4 节自行复制 `nav2_params.yaml` 并将该项设为 `0.0`。不要求额外界面或复杂功能。

**验收材料：** 提交源码、点位配置和准确的启动命令；提供覆盖三个场景的连续录屏（可每个场景单独录制），能看到所用配置、启动命令、RViz 运动过程和终端结果，无需剪辑包装。在报告中简述失败处理策略即可。允许 AI 辅助，提交者需自行运行并核验结果。

**评分：** 正常巡逻 8 分、失败处理 6 分、可复现性 6 分（含修改点位场景）；按实际行为和验证证据评分，不按代码长度或界面复杂度评分。

- *取点小技巧*：不知道地图上某点的 $(x, y)$ 坐标时，可以在终端运行 `ros2 topic echo /clicked_point`，然后用 RViz 顶部工具栏的 **Publish Point** 按钮在地图上点选，直接抄下终端打印出的坐标值；记得给自己的节点开启 `use_sim_time: True`。

## 6.3 提交格式

沿用[培训仓库](https://github.com/Venom-Algorithm/training)的提交方式：把作业提交并推送到**自己的 `training` Fork**，提交仓库链接，不直接推送队伍公共仓库，也不另交压缩包。已有 Fork 的同学先按[仓库首页的同步步骤](https://github.com/Venom-Algorithm/training#以后怎样获取新作业)获取更新，无需重新 Fork 或克隆。

Fork 或同步后，直接在已有的 `04-nav2/` 目录中填写 [报告模板](./report.md)，不用另建目录。也可以用 `report.pdf` 替换 `report.md`。讲义 `README.md` 和配套的 `截图/` 不需要修改；自己的实验截图放到 `images/`。

```text
training/
└── 04-nav2/
    ├── report.md 或 report.pdf  # 必做实验截图、现象描述和简短回答
    ├── images/                 # 报告引用的截图，使用相对路径
    ├── config/                 # 修改过的 YAML；选做另附巡逻点位配置
    └── patrol_node/            # 选做：源码及运行说明 README.md
```

完成选做的同学把源码放进 `patrol_node/`，填写其中的[运行说明模板](./patrol_node/README.md)，并把巡逻点位配置放到 `config/`。

报告开头注明姓名、学号及完成的作业项。完成选做的同学在运行说明中写清依赖、构建和启动命令、点位配置的使用方法及失败处理策略，并在报告中附上三个验收场景的录屏链接（可分别录制）。**录屏应能直接访问，不要把大型视频、bag 文件或 `build/`、`install/`、`log/` 等构建产物提交到 Git。**

确认 `origin` 指向自己的 Fork，再在仓库根目录提交：

```bash
cd "$(git rev-parse --show-toplevel)"
git remote -v
git status
git add 04-nav2
git commit -m "Complete Nav2 training assignment"
git push origin main
```

推送后打开自己的 Fork 页面，确认 `04-nav2/` 中的报告、配置和代码已更新，图片能正常显示、录屏链接可访问。最终提交**自己的仓库链接**（如 `https://github.com/USERNAME/training`），并注明作业目录 `04-nav2/`；完成选做时同时提供录屏链接。

**评分原则：** 必做 A（25 分）+ B（25 分）+ C（15 分）+ D（15 分）= 80 分，选做另行加分。必做实验重在亲手验证，截图真实、能用两三句话把现象和原因对应上即可；选做按 6.2 的功能与验收证据评分。

---

# 附录 A：常用命令速查

```bash
# 核心信息：先看有哪些，再看具体内容
ros2 node list
ros2 topic list -t
ros2 action list -t

# 观察某一数据流（需要消息正在发布）
ros2 topic info /odom -v
ros2 topic echo /odom --once
ros2 topic hz /scan
ros2 topic echo /cmd_vel --once

# 导航任务与内部 Action
ros2 action info /navigate_to_pose
ros2 action info /compute_path_to_pose
ros2 action info /follow_path

# 观察规划路径和速度链路（默认 Humble bringup；实际以运行结果为准）
ros2 topic info /plan -v
ros2 topic info /cmd_vel_nav -v
ros2 topic info /cmd_vel -v

# 查看 Lifecycle 节点与状态
ros2 lifecycle nodes
ros2 lifecycle get /planner_server
ros2 lifecycle get /controller_server
ros2 lifecycle get /velocity_smoother
ros2 lifecycle get /map_server
ros2 lifecycle get /amcl

# 查看服务（例如 Lifecycle 状态转换、Costmap 清理等）
ros2 service list -t
ros2 service list -t | grep -E 'change_state|get_state|clear' 

# 查看 TF
ros2 run tf2_ros tf2_echo map base_link

# 查参数与相关节点
ros2 param list /controller_server
ros2 param get /controller_server controller_plugins

# 查看启动脚本支持什么参数
ros2 launch nav2_bringup tb3_simulation_launch.py --show-args
```

> 注意：实际项目常会对话题名做重映射（remapping）或添加命名空间。遇到话题名称与默认示例不同时，先用 `ros2 topic list -t` 和 `ros2 node info` 查看真实连接关系。

# 附录 B：参考资料（按需查阅，优先中文镜像）

**入门操作与概念：**

1. Nav2 快速入门（中文文档）：<http://dev.nav2.fishros.com/doc/getting_started/index.html> （鱼香ROS汉化镜像，涵盖二进制安装与 Gazebo 仿真导航）
2. Nav2 核心概念精析（中文文档）：<http://dev.nav2.fishros.com/doc/concepts/index.html> （涵盖 Action、Lifecycle、行为树与各 Server 职责）
3. 坐标变换（TF）设置指南（中文文档）：<http://dev.nav2.fishros.com/doc/setup_guides/transformation/setup_transforms.html> （详解 `map`、`odom`、`base_link` 与 TF 树）
4. ROS 2 生命周期与组件容器（中文文档）：<http://dev.nav2.fishros.com/doc/setup_guides/lifecycle_composition/setup_lifecycle_composition.html>
5. TurtleBot3 导航官方指南：<https://emanual.robotis.com/docs/en/platform/turtlebot3/nav_simulation/>

**模块参数与深入配置：**

6. 膨胀层（Inflation Layer）参数配置（中文文档）：<http://dev.nav2.fishros.com/doc/configuration/packages/costmap-plugins/inflation.html>
7. 2D 代价地图（Costmap 2D）配置指南（中文文档）：<http://dev.nav2.fishros.com/doc/configuration/packages/configuring-costmaps.html>
8. 详细行为树架构演练（中文文档）：<http://dev.nav2.fishros.com/doc/behavior_trees/overview/detailed_behavior_tree_walkthrough.html> （解析默认导航 BT 树节点分支与恢复逻辑）
9. Simple Commander Python API（中文文档）：<http://dev.nav2.fishros.com/doc/commander_api/index.html> （针对自动巡逻选做的 Python 导航控制接口）
10. Humble Nav2 Action 接口定义速查：<https://api.nav2.org/humble/actions/> （包含 `NavigateToPose`、`ComputePathToPose`、`FollowPath` 消息结构）
11. Humble `tb3_simulation_launch.py` 启动源码：<https://api.nav2.org/nav2-humble/html/tb3__simulation__launch_8py_source.html>
12. Humble `navigation_launch.py` 启动源码：<https://api.nav2.org/nav2-humble/html/navigation__launch_8py_source.html> （可查看速度重映射与受管节点列表）

**RoboMaster 实战工程：**

13. 北极熊战队 RM2025 哨兵导航仓库：<https://github.com/SMBU-PolarBear-Robotics-Team/pb2025_sentry_nav>
14. 北极熊战队 Nav2 自定义插件仓库：<https://github.com/SMBU-PolarBear-Robotics-Team/pb_nav2_plugins>
15. 北极熊战队哨兵决策行为树：<https://github.com/SMBU-PolarBear-Robotics-Team/pb2025_sentry_behavior>

**最后想说：** 一次入门培训不需要让你立刻会写导航算法。以后看陌生仓库时，如果能先找到目标从哪里进、状态和障碍从哪里来、路径在哪里生成、速度从哪里出去，并且知道该怎样验证，你就已经比“看完一堆配置但不知如何下手”前进了一大步。接下来的东西，完全可以在真实项目里慢慢补。
