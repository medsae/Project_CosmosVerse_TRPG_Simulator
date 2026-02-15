# guidance.py
import math


def calculate_pn_acceleration(missile_data, target_data, dt, n=4.0):
    """
    增强版比例导引律：解决初始静止及视线重合时的启动问题
    """
    # 1. 相对几何关系
    dx = target_data['x'] - missile_data['x']
    dy = target_data['y'] - missile_data['y']
    r_sq = dx ** 2 + dy ** 2
    r = math.sqrt(r_sq)

    if r < 5.0:  # 距离过近停止制导
        return 0.0, 0.0

    # 2. 相对速度
    dvx = target_data['vx'] - missile_data['vx']
    dvy = target_data['vy'] - missile_data['vy']

    # 3. 计算视线角速度 (LOS Rate)
    # Omega = (r x v) / |r|^2
    omega_los = (dx * dvy - dy * dvx) / r_sq

    # 4. 计算闭合速度 (Closing Velocity)
    # vr < 0 表示距离在缩短
    vr = (dvx * dx + dvy * dy) / r

    # --- 核心逻辑改进 ---

    # A. 基础 PN 加速度 (垂直于视线)
    accel_pn_mag = n * abs(vr) * omega_los
    ax_pn = -(dy / r) * accel_pn_mag
    ay_pn = (dx / r) * accel_pn_mag

    # B. 启动补偿 (Bias Force)
    # 如果相对速度太小，或者 omega_los 接近 0，导弹会“发呆”
    # 我们加入一个指向目标的直接推力 (Pure Pursuit 倾向)
    bias_mag = 15.0  # 给予 15m/s^2 的基础指向推力
    ax_bias = (dx / r) * bias_mag
    ay_bias = (dy / r) * bias_mag

    # C. 合成指令
    # 初始阶段 bias 占主导，一旦产生 omega_los，PN 占主导
    ax = ax_pn + ax_bias
    ay = ay_pn + ay_bias

    # 返回本帧的速度改变量
    return ax * dt, ay * dt