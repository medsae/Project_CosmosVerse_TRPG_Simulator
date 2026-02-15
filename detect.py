from Star import Star  # 从 Star.py 文件导入 Star 类
from ship import Ship  # 从 ship.py 文件导入 Ship 类
import physics
import math


def get_velocity_vector(planet, ship):
    """计算飞船在轨道坐标系下的瞬时速度向量 (vx, vy)"""
    import physics
    mu = 6.67430e-11 * planet.mass
    r = ship.height

    # 1. 计算圆轨道速率 v = sqrt(mu / r)
    v_mag = math.sqrt(mu / r)

    # 2. 获取当前角度（弧度）
    theta_rad = math.radians(ship.initial_position)

    # 3. 计算速度向量分量
    # 顺行时速度方向为 theta + 90度
    # vx = v * cos(theta + pi/2) = -v * sin(theta)
    # vy = v * sin(theta + pi/2) =  v * cos(theta)
    vx = -v_mag * math.sin(theta_rad) * ship.orbit_direction
    vy = v_mag * math.cos(theta_rad) * ship.orbit_direction

    return vx, vy


def get_relative_velocity(ship1, ship2, planet):
    """计算 ship2 相对于 ship1 的速度向量 (rel_vx, rel_vy)"""
    vx1, vy1 = get_velocity_vector(planet, ship1)
    vx2, vy2 = get_velocity_vector(planet, ship2)

    rel_vx = vx2 - vx1
    rel_vy = vy2 - vy1

    return rel_vx, rel_vy
def get_coordinates(planet,ship):
    rad= math.radians(ship.initial_position)
    r = ship.height

    pos_x = r * math.cos(rad)
    pos_y = r * math.sin(rad)

    return pos_x, pos_y  # return two of the result

def range_find(ship1,ship2,planet):
    x1,y1 = get_coordinates(planet,ship1)
    x2,y2 = get_coordinates(planet,ship2)

    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    #using formula to calculate the distance between two ship
    return distance


def is_occluded( ship1, ship2,planet):
 #check if the vision between two ship is occluded
    #get the relevant coordiantes
    x1, y1 = get_coordinates(planet, ship1)
    x2, y2 = get_coordinates(planet, ship2)

    #我不知道这个公式何意味，gemini让我这么写的,这是不是什么线性代数之类的
    # 2. 线段向量 AB 和 向量 AO (O是原点)
    dx, dy = x2 - x1, y2 - y1
    # 线段长度的平方
    segment_len_sq = dx ** 2 + dy ** 2

    if segment_len_sq == 0:
        return False  # 两船重合

    # 3. 找到原点(0,0)在线段AB上的投影点参数 t
    # t = 投影点距离A的比例，0表示在A，1表示在B
    # 公式：t = - (A · AB) / |AB|^2
    t = - (x1 * dx + y1 * dy) / segment_len_sq

    # 4. 限制 t 的范围在 [0, 1] 之间，得到线段上离原点最近的点
    t = max(0, min(1, t))

    # 5. 计算最近点的坐标
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    # 6. 计算最近点到原点的距离
    dist_to_center = math.sqrt(closest_x ** 2 + closest_y ** 2)

    # 7. 如果最短距离小于天体半径，则被遮挡
    occuled = dist_to_center < planet.radius
    return int(occuled)