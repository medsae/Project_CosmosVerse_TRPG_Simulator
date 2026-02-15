import math
import random

class ProjectileManager:
    def __init__(self, templates=None):
        self.projectiles = []
        self.templates = templates if templates else {}
        self.default_lifespan = 20.0
        self.default_yield_radius = 5.0

    def spawn(self, owner, x, y, base_angle_deg, template_key):
        """
        带安全偏移的弹丸发射函数
        """
        temp = self.templates.get(template_key, {})
        v_muzzle = temp.get('muzzle_velocity', 1000.0)
        lifespan = temp.get('lifespan', self.default_lifespan)

        # 1. 处理 MOA 散布
        moa_val = temp.get('moa', 0.0)
        spread = (random.random() - 0.5) * moa_val
        final_angle_deg = base_angle_deg + spread
        angle_rad = math.radians(final_angle_deg)

        # 2. 核心修复：安全偏移 (Muzzle Offset)
        # 弹丸生成点必须在飞船碰撞半径之外，通常加 50 米余量
        safe_dist = owner.get_hitbox_radius() + 50.0
        spawn_x = x + safe_dist * math.cos(angle_rad)
        spawn_y = y + safe_dist * math.sin(angle_rad)

        # 3. 继承惯性速度
        ship_vx = getattr(owner, 'vx', 0.0)
        ship_vy = getattr(owner, 'vy', 0.0)
        vx = ship_vx + v_muzzle * math.cos(angle_rad)
        vy = ship_vy + v_muzzle * math.sin(angle_rad)

        # 4. 存入弹丸数据
        self.projectiles.append({
            'x': spawn_x,
            'y': spawn_y,
            'vx': vx,
            'vy': vy,
            'age': 0.0,
            'lifespan': lifespan,
            'active': True,
            'owner': owner,
            'yield_radius': temp.get('yield_radius', self.default_yield_radius)
        })

    def update(self, dt, orbital_n, ships):
        n = orbital_n
        n2 = n ** 2
        active_ships = [s for s in ships if getattr(s, 'visible', True)]

        for p in self.projectiles:
            if not p['active']: continue

            old_x, old_y = p['x'], p['y']

            # Hill 方程物理更新
            ax = 3 * n2 * p['x'] + 2 * n * p['vy']
            ay = -2 * n * p['vx']
            p['vx'] += ax * dt
            p['vy'] += ay * dt
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['age'] += dt

            if p['age'] > p.get('lifespan', self.default_lifespan):
                p['active'] = False
                continue

            # 射线碰撞检测
            for s in active_ships:
                # 虽然有了偏移，但保留 0.1s 安全期是编程稳健性的好习惯
                if s == p['owner'] and p['age'] < 0.1: continue

                sx = getattr(s, 'tac_x', 0.0)
                sy = getattr(s, 'tac_y', 0.0)
                hit_dist = s.get_hitbox_radius() + p.get('yield_radius', self.default_yield_radius)

                if self._check_segment_circle_collision(old_x, old_y, p['x'], p['y'], sx, sy, hit_dist):
                    print(f"🎯 [命中判定] {p['owner'].name} 的弹丸击中了 {s.name}!")
                    s.visible = False
                    p['active'] = False
                    break

    def _check_segment_circle_collision(self, x1, y1, x2, y2, cx, cy, r):
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0: return False
        fx, fy = x1 - cx, y1 - cy
        a = dx**2 + dy**2
        b = 2 * (fx * dx + fy * dy)
        c = (fx**2 + fy**2) - r**2
        discriminant = b**2 - 4 * a * c
        if discriminant < 0: return False
        discriminant = math.sqrt(discriminant)
        t1 = (-b - discriminant) / (2 * a)
        t2 = (-b + discriminant) / (2 * a)
        return (0 <= t1 <= 1) or (0 <= t2 <= 1)