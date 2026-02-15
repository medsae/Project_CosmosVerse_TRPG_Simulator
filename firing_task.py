# firing_task.py

class FiringTask:
    def __init__(self, weapon_key, angle, count, rpm):
        self.weapon_key = weapon_key
        self.angle = angle
        self.remaining = count
        self.interval = 60.0 / rpm if rpm > 0 else 1.0
        self.cooldown = 0.0  # 初始为0，表示可以立即发射第一发
        self.active = True

    def update(self, dt, ship, proj_manager):
        """
        在每一帧被调用，驱动射击逻辑
        """
        if not self.active or self.remaining <= 0:
            self.active = False
            return

        self.cooldown -= dt

        # 处理可能的“一帧多发”情况（当 dt > interval 时）
        while self.cooldown <= 0 and self.remaining > 0:
            # 执行发射
            proj_manager.spawn(
                owner=ship,
                x=getattr(ship, 'tac_x', 0),
                y=getattr(ship, 'tac_y', 0),
                base_angle_deg=self.angle,
                template_key=self.weapon_key
            )

            self.remaining -= 1
            self.cooldown += self.interval  # 累加间隔，保持时序精准

        if self.remaining <= 0:
            self.active = False