import math
import guidance


class Ship:
    def __init__(self, name, fuelmass, drymass, area, heat, flowrate, max_thrust, height, initial_position,
                 orbit_direction=1):
        self.name, self.fuelmass, self.drymass = name, fuelmass, drymass
        self.height, self.initial_position = height, initial_position
        self.orbit_direction = orbit_direction
        self.area, self.heat, self.flowrate, self.max_thrust = area, heat, flowrate, max_thrust
        self.visible, self.state = True, "IDLE"
        self.target_height = 0.0
        self.start_height = 0.0
        self.wait_timer = 0.0
        self.transfer_timer = 0.0
        self.total_transfer_time = 0.0
        self.angle_at_burn = 0.0

    def calculate_isp(self):
        return self.max_thrust / (self.flowrate * 9.8) if self.flowrate > 0 else 0

    def calculate_delta_v(self):
        isp = self.calculate_isp()
        return isp * 9.8 * math.log((self.fuelmass + self.drymass) / self.drymass) if self.drymass > 0 else 0

    def set_intercept_task(self, wait_time, transfer_time, target_height):
        self.wait_timer = wait_time
        self.transfer_timer = transfer_time
        self.total_transfer_time = transfer_time
        self.target_height = target_height
        self.state = "WAITING"

    def update_logic(self, body, dt):
        import physics
        if self.state == "IDLE":
            physics.time_flow(body, self, dt)

        elif self.state == "WAITING":
            physics.time_flow(body, self, dt)
            self.wait_timer -= dt
            if self.wait_timer <= 0:
                if physics.execute_hohmann_transfer(body, self, self.target_height):
                    self.start_height = self.height
                    self.angle_at_burn = self.initial_position  # 记录点火角度
                    self.state = "TRANSFERRING"
                else:
                    self.state = "IDLE"

        elif self.state == "TRANSFERRING":
            self.transfer_timer -= dt
            progress = max(0, min(1, 1.0 - (self.transfer_timer / self.total_transfer_time)))

            # --- 强制线性角度演进 ---
            # 无论物理引擎dt是多少，T秒内必须走完180度
            total_arc = 180.0 * self.orbit_direction
            self.initial_position = (self.angle_at_burn + progress * total_arc) % 360

            # --- 强制平滑高度演进 (余弦/正弦爬升) ---
            cos_factor = math.cos(math.pi * progress)
            self.height = (self.start_height + self.target_height) / 2 - (
                        self.target_height - self.start_height) / 2 * cos_factor

            if self.transfer_timer <= 0:
                self.height = self.target_height
                self.state = "IDLE"

    def consume_dv(self, dv_required):
        isp = self.calculate_isp()
        if isp <= 0: return False
        m0 = self.fuelmass + self.drymass
        m1 = m0 / math.exp(dv_required / (isp * 9.8))
        needed = m0 - m1
        if self.fuelmass >= needed:
            self.fuelmass -= needed
            return True
        return False


    def get_hitbox_radius(self):
        """将面积转换为判定半径 (r = sqrt(Area/pi))"""
        if self.area <= 0: return 5.0  # 即使是极小单位，也给一个 5 米的最小碰撞体积
        return math.sqrt(self.area / math.pi)


class Missile(Ship):
    def __init__(self, name, fuelmass, drymass, area, heat, flowrate, max_thrust,
                 height, initial_position, orbit_direction,
                 fuse_range=150.0, yield_radius=350.0, **kwargs):

        super().__init__(name, fuelmass, drymass, area, heat, flowrate, max_thrust,
                         height, initial_position, orbit_direction)

        self.fuse_range = fuse_range
        self.yield_radius = yield_radius
        self.target_vessel = None
        self.launcher = None
        self.spawn_time = 0.0

    def update_logic(self, body, dt):
        """宏观轨道更新逻辑"""
        super().update_logic(body, dt)
        self.spawn_time += dt

        if self.target_vessel and self.target_vessel.visible and self.visible:
            # 大地图欧几里得距离计算
            r1 = self.height
            a1 = math.radians(self.initial_position)
            r2 = self.target_vessel.height
            a2 = math.radians(self.target_vessel.initial_position)

            dist = math.sqrt(r1**2 + r2**2 - 2*r1*r2*math.cos(a1 - a2))

            # 宏观引爆判定：如果在非战术模式下靠得足够近，也判定为命中
            if dist < self.fuse_range:
                print(f"\n🎯 [远航截击] {self.name} 在宏观轨道成功拦截 {self.target_vessel.name}!")
                self.target_vessel.visible = False
                self.visible = False

    def get_guidance_command(self, target_state, missile_state):
        """战术模式接口"""
        if not self.target_vessel or not self.target_vessel.visible:
            return 0.0, 0.0

        ax, ay = guidance.proportional_navigation(
            missile_state,
            target_state,
            nav_ratio=4.0
        )
        return ax, ay

    def get_hitbox_radius(self):
        """导弹物理碰撞半径"""
        return 5.0
