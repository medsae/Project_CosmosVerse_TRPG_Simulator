import math
import random
import detect
import guidance
from projectile_manager import ProjectileManager


class TacticalManager:
    def __init__(self, planet):
        self.planet = planet
        self.is_active = False
        self.origin_ship = None
        self.all_ships_ref = []  # 保持对全局飞船列表的引用
        self.local_data = {}  # Key 为 ship 对象，Value 为坐标与速度数据
        self.proj_manager = ProjectileManager()
        self.orbital_n = 0.0

    def activate(self, ship_src, ship_dst, all_ships):
        self.is_active = True
        self.origin_ship = ship_src
        self.all_ships_ref = all_ships
        self.local_data = {}

        # 以源飞船(发射船)为坐标系原点
        x_ref, y_ref = detect.get_coordinates(self.planet, ship_src)

        for ship in all_ships:
            if not getattr(ship, 'visible', True): continue

            # 如果飞船处于大地图转移状态，强行停止进入战术模式
            if getattr(ship, 'state', "") == "TRANSFERRING":
                ship.state = "IDLE"

            xi, yi = detect.get_coordinates(self.planet, ship)
            # 计算相对于原点的初始速度
            rvx, rvy = (0.0, 0.0) if ship == ship_src else detect.get_relative_velocity(ship_src, ship, self.planet)

            # 写入战术局部数据
            self.local_data[ship] = {
                'x': xi - x_ref,
                'y': yi - y_ref,
                'vx': rvx,
                'vy': rvy
            }
            # 同步回 ship 对象用于渲染
            ship.tac_x, ship.tac_y = self.local_data[ship]['x'], self.local_data[ship]['y']

    def register_new_unit(self, ship_obj):
        """当导弹发射时，将其动态加入战术坐标系"""
        if ship_obj not in self.local_data:
            # 初始位置设为微小偏移，防止重叠
            self.local_data[ship_obj] = {
                'x': 0.1, 'y': 0.1,
                'vx': 0.0, 'vy': 0.0
            }
            ship_obj.tac_x, ship_obj.tac_y = 0.1, 0.1
            print(f"📡 [战术系统] 已捕获新对象: {ship_obj.name}")

    def update(self, dt):
        if not self.is_active: return

        # 计算当前高度的平均角速度 (Orbital Mean Motion)
        mu = 6.67430e-11 * self.planet.mass
        n = math.sqrt(mu / (self.origin_ship.height ** 3))
        self.orbital_n = n

        # 获取当前所有可见单位列表，供弹丸检测使用
        active_units = [s for s in self.local_data.keys() if s.visible]

        # --- 第一部分：物理动力学与射击任务更新 ---
        for ship in list(self.local_data.keys()):
            if not ship.visible: continue

            data = self.local_data[ship]

            # 1. 动力驱动处理 (导弹制导或手动推力)
            self._handle_ship_movement(ship, data, dt)

            # 2. Hill's Equations (轨道相对运动方程)
            ddx = 2 * n * data['vy'] + 3 * (n ** 2) * data['x']
            ddy = -2 * n * data['vx']

            data['vx'] += ddx * dt
            data['vy'] += ddy * dt
            data['x'] += data['vx'] * dt
            data['y'] += data['vy'] * dt

            # 同步回对象以便绘图
            ship.tac_x, ship.tac_y = data['x'], data['y']
            ship.vx, ship.vy = data['vx'], data['vy']

            # 3. 处理射击指令 (适配 FiringTask.update(dt, ship, proj_manager))
            firing_tasks = getattr(ship, 'firing_tasks', [])
            for task in firing_tasks[:]:
                if hasattr(task, 'update'):
                    # 关键修改：严格匹配 FiringTask 定义的参数顺序 (dt, ship, proj_manager)
                    task.update(dt, ship, self.proj_manager)

                    # 检查 FiringTask 是否已完成 (根据你的 task.active 逻辑)
                    if not getattr(task, 'active', True) or getattr(task, 'remaining', 0) <= 0:
                        firing_tasks.remove(task)
                else:
                    # 兼容性备选方案：一次性发射
                    self.proj_manager.spawn(
                        owner=ship,
                        x=data['x'],
                        y=data['y'],
                        base_angle_deg=getattr(task, 'angle', 0),
                        template_key=getattr(task, 'weapon_key', 'default')
                    )
                    firing_tasks.remove(task)

        # --- 第二部分：更新弹丸物理与射线检测 ---
        self.proj_manager.update(dt, n, active_units)

        # --- 第三部分：导弹拦截/碰撞判定 ---
        self.check_collisions()

    def _handle_ship_movement(self, ship, data, dt):
        """处理导弹制导与飞船手动推力逻辑"""
        from ship import Missile

        current_fuel = getattr(ship, 'fuelmass', 0.0)
        dry_mass = getattr(ship, 'drymass', 500.0)
        total_mass = current_fuel + dry_mass
        f_max = getattr(ship, 'max_thrust', 5000.0)
        a_limit = (f_max / total_mass) * dt

        # 1. 自动制导 (仅限导弹)
        dv_auto_x, dv_auto_y = 0.0, 0.0
        target = getattr(ship, 'target_vessel', None)

        if isinstance(ship, Missile) and target and target in self.local_data and getattr(target, 'visible', True):
            dv_auto_x, dv_auto_y = guidance.calculate_pn_acceleration(data, self.local_data[target], dt)

        # 2. 手动推力指令 (tac_move)
        dv_man_x, dv_man_y = 0.0, 0.0
        tx = getattr(ship, 'target_dv_x', 0.0)
        ty = getattr(ship, 'target_dv_y', 0.0)

        if abs(tx) > 1e-6 or abs(ty) > 1e-6:
            dv_man_x = math.copysign(min(abs(tx), a_limit), tx)
            dv_man_y = math.copysign(min(abs(ty), a_limit), ty)
            ship.target_dv_x -= dv_man_x
            ship.target_dv_y -= dv_man_y

        # 3. 推力合成与执行
        final_dv_x = dv_auto_x + dv_man_x
        final_dv_y = dv_auto_y + dv_man_y
        final_mag = math.sqrt(final_dv_x ** 2 + final_dv_y ** 2)

        if final_mag > 1e-9:
            if current_fuel <= 0: return
            if final_mag > a_limit:
                ratio = a_limit / final_mag
                final_dv_x *= ratio
                final_dv_y *= ratio
                final_mag = a_limit

            data['vx'] += final_dv_x
            data['vy'] += final_dv_y
            ship.consume_dv(final_mag)

    def check_collisions(self):
        """引信触发逻辑：支持拦截导弹与友军识别(IFF)"""
        all_units = list(self.local_data.keys())
        from ship import Missile

        for msl in all_units:
            if not isinstance(msl, Missile) or not msl.visible:
                continue

            my_launcher = getattr(msl, 'launcher', None)

            for other in all_units:
                if other == msl or not other.visible:
                    continue

                # IFF 检查
                other_launcher = getattr(other, 'launcher', None)
                if other == my_launcher: continue
                if other_launcher == my_launcher and my_launcher is not None: continue

                # 距离计算
                d1, d2 = self.local_data[msl], self.local_data[other]
                dist = math.sqrt((d1['x'] - d2['x']) ** 2 + (d1['y'] - d2['y']) ** 2)

                if dist < getattr(msl, 'fuse_range', 150.0):
                    tag = "[反导拦截]" if isinstance(other, Missile) else "[反舰攻击]"
                    print(f"🎯 {tag} {msl.name} 引信触发！目标: {other.name} | 距离: {dist:.1f}m")
                    self.detonate_warhead(msl, other)
                    break

    def detonate_warhead(self, missile, primary_target):
        """执行弹头爆炸，判定范围内所有单位受损"""
        missile.visible = False
        m_pos = self.local_data[missile]
        yield_r = getattr(missile, 'yield_radius', 300.0)

        print(f"💥 [爆炸] {missile.name} 在坐标({m_pos['x']:.0f}, {m_pos['y']:.0f})处殉爆！")

        for ship in list(self.local_data.keys()):
            if not ship.visible or ship == missile: continue

            state = self.local_data[ship]
            dist = math.sqrt((state['x'] - m_pos['x']) ** 2 + (state['y'] - m_pos['y']) ** 2)

            if dist < yield_r:
                print(f"🔴 [毁伤报告] {ship.name} 在爆炸半径内被击毁！")
                ship.visible = False

    def sync_to_global(self):
        """战术模式结束，将坐标增量同步回大地图轨道"""
        if not self.is_active: return
        for ship in self.all_ships_ref:
            if ship in self.local_data:
                local = self.local_data[ship]
                if ship == self.origin_ship: continue

                # 同步径向高度
                ship.height += local['y']
                # 同步切向位置（转化为角度偏移）
                angle_delta = (local['x'] / ship.height) * (180 / math.pi)
                ship.initial_position = (ship.initial_position + angle_delta) % 360
        self.is_active = False