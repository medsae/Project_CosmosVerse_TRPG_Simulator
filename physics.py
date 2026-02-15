import math

G = 6.67430e-11


def calculate_wait_time(body, ship_src, ship_dst):
    mu = G * body.mass
    r1, r2 = ship_src.height, ship_dst.height

    # 目标圆轨道的角速度
    omega_dst = math.sqrt(mu / r2 ** 3)

    # 霍曼转移所需时间 (s)
    t_trans = math.pi * math.sqrt(((r1 + r2) / 2) ** 3 / mu)

    # 核心公式：点火时，目标应该处于什么相位？
    # 飞船会走 180 度(pi)，这段时间内目标会走 (omega_dst * t_trans)
    # 目标相对于飞船的理想相位差 alpha (弧度)
    alpha_req = math.pi - (omega_dst * t_trans)

    # 当前实际相位差 (dst - src)
    phi_src = math.radians(ship_src.initial_position)
    phi_dst = math.radians(ship_dst.initial_position)
    phi_rel = (phi_dst - phi_src) % (2 * math.pi)

    # 相对角速度 (假设都是顺行)
    omega_src = math.sqrt(mu / r1 ** 3)
    omega_rel = omega_src - omega_dst

    if abs(omega_rel) < 1e-18: return 0

    # 计算等待时间
    wait_time = (phi_rel - alpha_req) / omega_rel
    period_rel = 2 * math.pi / abs(omega_rel)
    while wait_time < 0: wait_time += period_rel

    return wait_time


# 其他辅助函数保持简单
def get_hohmann_dv(body, ship, target_height):
    mu = G * body.mass
    r1, r2 = ship.height, target_height
    v1 = math.sqrt(mu / r1)
    v_perigee = math.sqrt(mu * (2 / r1 - 2 / (r1 + r2)))
    v2 = math.sqrt(mu / r2)
    v_apogee = math.sqrt(mu * (2 / r2 - 2 / (r1 + r2)))
    return abs(v_perigee - v1) + abs(v2 - v_apogee)


def execute_hohmann_transfer(body, ship, target_height):
    dv = get_hohmann_dv(body, ship, target_height)
    return ship.consume_dv(dv)
# physics.py

def calculate_hohmann_transfer_time(body, ship, target_height):
    """
    计算霍曼转移所需的航行时间（秒）
    公式: t = pi * sqrt( a^3 / mu )
    其中 a 是转移轨道的半长轴: (r1 + r2) / 2
    """
    mu = G * body.mass
    r1 = ship.height
    r2 = target_height
    a_trans = (r1 + r2) / 2
    return math.pi * math.sqrt(a_trans ** 3 / mu)

def time_flow(body, ship, dt):
    mu = G * body.mass
    omega = math.sqrt(mu / ship.height ** 3)
    ship.initial_position = (ship.initial_position + math.degrees(omega) * dt * ship.orbit_direction) % 360