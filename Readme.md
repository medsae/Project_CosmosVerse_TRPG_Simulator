# Readme

# **Orbital Tactical Simulator Project**

## **Overview**

This simulator is a technical framework designed for orbital mechanics and relative tactical engagements in TRPG. It supports two primary simulation layers: a strategic view for large-scale orbital planning and a tactical view for close-range combat using Hill-Clohessy-Wiltshire (HCW) equations.

---

## **Command Reference**

### **Strategic Commands**

These commands are used in the global orbital view to manage time and celestial navigation.

- [time_value]: Enter a number (e.g., 3600) to advance the simulation time by that many seconds.
- status: Display the current status of all vessels including height, fuel, and position.
- intercept [src] [dst]: Calculate and schedule a Hohmann transfer window for vessel A to intercept vessel B.
- y: Confirm and enter Tactical Mode when an Intercept Alert (proximity fuse) is triggered.
- launch [parent] [type] [name]: Deploy a missile from a parent ship. Type must be S, M, or L.
- exit: Terminate the simulation.

### **Tactical Commands**

These commands are only functional while Tactical Mode is active.

- tac_move [name] [dv_x] [dv_y]: Apply a delta-V vector to a vessel in the local tactical frame.
- lock [msl] [tgt]: Assign a target to a missile for its guidance logic.
- fire [ship] [weapon] [angle] [count]: Fire a specified number of rounds at a fixed angle.
- auto_fire [src] [dst] [weapon] [count]: Perform a single fire mission using calculated lead-angle compensation.
- keep_fire [src] [dst] [weapon] [count]: Continuously track a target and fire until the count is depleted.
- tac_set [name] [y] [vx] [vy]: Cheat command to force a vessel's relative position and velocity for testing.
- tac_exit: Synchronize tactical changes back to the global orbit and return to strategic view.

---

## **Configuration Documentation Standards**

The simulator relies on JSON configuration files for weapons, ships, and missile templates. Follow the standards below when editing.

### **Weapon Templates**

Defines the ballistic performance of projectiles.

- muzzle_velocity: Initial speed of the projectile (m/s).
- mass: Mass of the projectile (kg).
- moa: Minute of Angle; represents the dispersion/inaccuracy.
- rpm: Rounds per minute; dictates fire rate for continuous tasks.
- yield_radius: The damage/explosion radius upon impact (m).
- lifespan: Duration the projectile exists before self-destructing (s).

### **Ship Configurations**

Defines the initial state of vessels in the global orbit.

- name: Unique identifier for the vessel.
- fuelmass: Mass of available propellant (kg).
- drymass: Mass of the ship without fuel (kg).
- area: Surface area for thermal/drag calculations (m2).
- heat: Current thermal state.
- flowrate: Propellant consumption rate at max thrust (kg/s).
- max_thrust: Maximum engine output (N).
- height: Initial orbital radius from the center of the planet (m).
- initial_position: Starting orbital angle (degrees, 0-360).

### **Missile Templates**

Defines the performance of deployable autonomous units.

- fuel / dry: Propellant and structural mass (kg).
- thrust: Engine output for propulsion and maneuvering (N).
- flow: Propellant consumption rate (kg/s).
- fuse_range: Distance at which the proximity fuse triggers detonation (m).
- yield_radius: Effective destruction radius of the warhead (m).

---

## **Technical Notes**

1. Fire Control: The Fire Control System (FCS) uses a 4-pass iteration to compensate for orbital drift caused by Coriolis and centrifugal forces.
2. Collision Detection: Projectiles use Continuous Collision Detection (CCD) to ensure high-speed hits are registered regardless of frame rate.
3. Exit Synchronization: Using tac_exit converts local cartesian displacement into orbital altitude and longitudinal phase shifts.

## 项目概述

本模拟器是一个专为轨道力学和相对战术交战的TRPG规则书设计的技术框架。它支持两个主要的模拟层级：用于大规模轨道规划的“战略视图”和基于 Hill-Clohessy-Wiltshire (HCW) 方程的近距离战斗“战术视图”。

---

## 指令参考

### 战略指令 (Strategic Commands)

这些指令在全局轨道视图中使用，用于管理时间推进和天体导航。

- [时间数值]: 输入数字（如 3600）将模拟时间推进指定的秒数。
- status: 显示所有舰船的当前状态，包括高度、燃料和位置。
- intercept [源舰] [目标舰]: 计算并规划 A 舰拦截 B 舰的霍曼转移窗口，设定点火倒计时。
- y: 当触发拦截熔断（近距离警报）时，输入 y 确认并进入战术模式。
- launch [母舰] [型号] [名称]: 从母舰部署一枚导弹。型号必须为 S、M 或 L。
- exit: 终止模拟程序。

### 战术指令 (Tactical Commands)

这些指令仅在战术模式激活时有效。

- tac_move [名称] [dv_x] [dv_y]: 在局部战术坐标系中为舰船施加一个增量速度（delta-V）矢量。
- lock [导弹名] [目标名]: 为导弹分配战术目标，激活其制导逻辑。
- fire [舰名] [武器键] [角度] [数量]: 以固定角度发射指定数量的弹药。
- auto_fire [源] [目] [武器键] [数量]: 使用预瞄角补偿算法执行一次性射击任务。
- keep_fire [源] [目] [武器键] [数量]: 持续跟踪目标并自动修正弹道，直到射击数量耗尽。
- tac_set [名称] [y] [vx] [vy]: 作弊指令，强制设置舰船的相对位置和速度，用于功能测试。
- tac_exit: 将战术模式下的位置变动同步回全局轨道，并返回战略视图。

---

## 配置文档编辑规范

模拟器依赖 JSON 格式的配置文件来定义武器、舰船和导弹模板。编辑时请遵循以下标准。

### 武器模板 (Weapon Templates)

定义弹丸的弹道性能。

- muzzle_velocity: 弹丸初速 (m/s)。
- mass: 单枚弹丸质量 (kg)。
- moa: 分角（Minute of Angle）；代表射击散布/不确定度。
- rpm: 每分钟射速；决定持续射击任务的频率。
- yield_radius: 弹药击中时的爆炸/杀伤半径 (m)。
- lifespan: 弹丸在自毁前存在的持续时间 (s)。

### 舰船配置 (Ship Configurations)

定义全局轨道中舰船的初始状态。

- name: 舰船的唯一识别名称。
- fuelmass: 可用推进剂质量 (kg)。
- drymass: 舰船不含燃料的结构质量 (kg)。
- area: 用于热力或阻力计算的表面积 (m2)。
- heat: 初始热量状态。
- flowrate: 最大推力时的推进剂消耗速率 (kg/s)。
- max_thrust: 发动机最大推力输出 (N)。
- height: 距离行星中心的初始轨道半径 (m)。
- initial_position: 初始轨道角度（度，0-360）。

### 导弹模板 (Missile Templates)

定义可部署的自主单元性能。

- fuel / dry: 推进剂质量与结构质量 (kg)。
- thrust: 用于推进和机动的发动机推力 (N)。
- flow: 推进剂消耗速率 (kg/s)。
- fuse_range: 近炸引信触发检测距离 (m)。
- yield_radius: 战斗部的有效摧毁半径 (m)。

---

## 技术笔记

1. 火控系统 (FCS)：火控逻辑使用 4 次迭代算法来补偿由科里奥利力和离心力引起的轨道漂移。
2. 碰撞检测：弹丸使用连续碰撞检测 (CCD) 技术，确保无论帧率如何，高速移动的物体都能准确记录命中。
3. 退出同步：使用 tac_exit 指令会将战术坐标系下的笛卡尔位移转换为大地图中的轨道高度变化和经度相位偏移。