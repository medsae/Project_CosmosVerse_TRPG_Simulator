import pygame
import math
import command


class SpaceVisualizer:
    def __init__(self, body, ships, tac_manager):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1000, 1000
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Orbital Simulator - Tactical Ready")

        self.body = body
        self.ships = ships
        self.tac_manager = tac_manager

        # 视野控制
        self.CX, self.CY = self.WIDTH // 2, self.HEIGHT // 2
        self.offset_x = 0
        self.offset_y = 0
        self.is_dragging = False
        self.last_mouse_pos = (0, 0)

        # 缩放系数
        max_h = max([s.height for s in ships]) if ships else body.radius * 5
        self.scale = (self.WIDTH / 3.0) / max_h
        self.tac_scale = 0.01  # 战术缩放

        self.running = True

    # --- [ 坐标转换 ] ---

    def world_to_screen(self, radius, angle_deg):
        """宏观极坐标转换 (用于绘制星球和轨道上的船)"""
        angle_rad = math.radians(-angle_deg)
        rel_x = radius * math.cos(angle_rad)
        rel_y = radius * math.sin(angle_rad)
        return (self.CX + self.offset_x + int(rel_x * self.scale),
                self.CY + self.offset_y + int(rel_y * self.scale))

    def tac_to_screen(self, x, y):
        """战术直角坐标转换 (用于战术模式下的船和弹丸)"""
        sx = self.CX + self.offset_x + int(x * self.tac_scale)
        sy = self.CY + self.offset_y - int(y * self.tac_scale)  # Y轴翻转
        return (sx, sy)

    # --- [ 渲染逻辑 ] ---

    def _draw_projectiles(self):
        """绘制弹丸及拖尾"""
        if not hasattr(self.tac_manager, 'proj_manager'):
            return

        for p in self.tac_manager.proj_manager.projectiles:
            if not p['active']: continue

            start_pos = self.tac_to_screen(p['x'], p['y'])
            # 拖尾长度计算
            length_factor = 0.05
            end_pos = self.tac_to_screen(
                p['x'] - p['vx'] * length_factor,
                p['y'] - p['vy'] * length_factor
            )

            pygame.draw.line(self.screen, (255, 255, 200), start_pos, end_pos, 1)
            pygame.draw.circle(self.screen, (255, 255, 255), start_pos, 1)

    def draw_tactical_view(self):
        """绘制战术视图"""
        self.screen.fill((10, 10, 30))
        center_x = self.CX + self.offset_x
        center_y = self.CY + self.offset_y
        font = pygame.font.SysFont("Consolas", 14)

        # 1. 绘制网格
        half_w_m = (self.WIDTH / 2) / self.tac_scale
        half_h_m = (self.HEIGHT / 2) / self.tac_scale
        start_x = int((-self.offset_x / self.tac_scale - half_w_m) // 1000) * 1000
        end_x = int((-self.offset_x / self.tac_scale + half_w_m) // 1000) * 1000 + 1000
        start_y = int((self.offset_y / self.tac_scale - half_h_m) // 1000) * 1000
        end_y = int((self.offset_y / self.tac_scale + half_h_m) // 1000) * 1000 + 1000

        for x_m in range(start_x, end_x, 1000):
            sx = center_x + int(x_m * self.tac_scale)
            color = (50, 50, 100) if x_m % 5000 == 0 else (30, 30, 50)
            pygame.draw.line(self.screen, color, (sx, 0), (sx, self.HEIGHT), 1)
        for y_m in range(start_y, end_y, 1000):
            sy = center_y - int(y_m * self.tac_scale)
            color = (50, 50, 100) if y_m % 5000 == 0 else (30, 30, 50)
            pygame.draw.line(self.screen, color, (0, sy), (self.WIDTH, sy), 1)

        # 2. 绘制弹丸
        self._draw_projectiles()

        # 3. 绘制实体
        for ship in list(self.tac_manager.local_data.keys()):
            data = self.tac_manager.local_data[ship]
            if not getattr(ship, 'visible', True): continue

            sx, sy = self.tac_to_screen(data['x'], data['y'])
            color = (0, 255, 255) if ship == self.tac_manager.origin_ship else (255, 80, 80)

            # 图标
            hit_r = max(2, int(ship.get_hitbox_radius() * self.tac_scale))
            pygame.draw.circle(self.screen, color, (sx, sy), hit_r + 4, 1)
            pygame.draw.circle(self.screen, color, (sx, sy), 3)

            # 速度矢量
            pygame.draw.line(self.screen, (0, 255, 100), (sx, sy),
                             (sx + int(data['vx'] * self.tac_scale * 10),
                              sy - int(data['vy'] * self.tac_scale * 10)), 2)

            # 标签修复
            label_text = f"{ship.name} [{data['x'] / 1000:.1f}, {data['y'] / 1000:.1f}]"
            label = font.render(label_text, True, (220, 220, 220))
            self.screen.blit(label, (sx + 12, sy - 12))

        # 战术标题
        font_ui = pygame.font.SysFont("Consolas", 20, bold=True)
        self.screen.blit(font_ui.render("MODE: TACTICAL ENGAGEMENT", True, (255, 50, 50)), (20, 20))

    def draw_macro_view(self):
        """绘制宏观轨道视图"""
        self.screen.fill((5, 5, 20))
        render_center = (self.CX + self.offset_x, self.CY + self.offset_y)
        font = pygame.font.SysFont("Consolas", 14)

        # 1. 行星
        body_px = int(self.body.radius * self.scale)
        pygame.draw.circle(self.screen, (100, 149, 237), render_center, body_px)

        # 2. 飞船与轨道
        for ship in self.ships:
            if not getattr(ship, 'visible', True): continue

            orbit_px = int(ship.height * self.scale)
            pygame.draw.circle(self.screen, (50, 50, 70), render_center, orbit_px, 1)

            # 绘制变轨线
            self.draw_transfer_path(ship)

            # 飞船位置与名字
            sx, sy = self.world_to_screen(ship.height, ship.initial_position)

            color = (255, 255, 255)
            if ship.state == "WAITING":
                color = (255, 255, 0)
            elif ship.state == "TRANSFERRING":
                color = (0, 255, 0)

            pygame.draw.circle(self.screen, color, (sx, sy), 5)
            # 修复：确保名字渲染
            name_label = font.render(ship.name, True, (200, 200, 200))
            self.screen.blit(name_label, (sx + 10, sy - 10))

    def draw_transfer_path(self, ship):
        """绘制预测轨道"""
        if not hasattr(ship, 'target_height') or ship.target_height <= 0: return
        if ship.state not in ["WAITING", "TRANSFERRING"]: return

        r_start = ship.height if ship.state == "WAITING" else getattr(ship, 'start_height', ship.height)
        r_target = ship.target_height
        direction = getattr(ship, 'orbit_direction', 1)

        # 计算起始角度
        if ship.state == "TRANSFERRING":
            progress = 1.0 - (ship.transfer_timer / ship.total_transfer_time)
            base_angle = ship.initial_position - (progress * 180.0 * direction)
        else:
            mu = 6.67430e-11 * self.body.mass
            omega = math.sqrt(mu / (ship.height ** 3))
            wait_time = getattr(ship, 'wait_timer', 0)
            base_angle = ship.initial_position + (math.degrees(omega) * wait_time * direction)

        points = []
        for i in range(0, 181, 10):
            p = i / 180.0
            cur_r = (r_start + r_target) / 2 - (r_target - r_start) / 2 * math.cos(math.pi * p)
            points.append(self.world_to_screen(cur_r, base_angle + i * direction))

        if len(points) > 1:
            color = (0, 255, 100) if ship.state == "TRANSFERRING" else (100, 100, 100)
            pygame.draw.lines(self.screen, color, False, points, 1)

    def draw(self):
        """主绘制入口"""
        if self.tac_manager.is_active:
            self.draw_tactical_view()
        else:
            self.draw_macro_view()
        pygame.display.flip()

    def run_loop(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.WIDTH, self.HEIGHT = event.w, event.h
                    self.CX, self.CY = self.WIDTH // 2, self.HEIGHT // 2
                    self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
                elif event.type == pygame.MOUSEWHEEL:
                    if self.tac_manager.is_active:
                        self.tac_scale *= (1.1 if event.y > 0 else 0.9)
                    else:
                        self.scale *= (1.1 if event.y > 0 else 0.9)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: self.is_dragging, self.last_mouse_pos = True, event.pos
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1: self.is_dragging = False
                elif event.type == pygame.MOUSEMOTION and self.is_dragging:
                    self.offset_x += event.pos[0] - self.last_mouse_pos[0]
                    self.offset_y += event.pos[1] - self.last_mouse_pos[1]
                    self.last_mouse_pos = event.pos

            # 时间推进逻辑
            if command.pending_sim_time > 0:
                if self.tac_manager.is_active:
                    # 战术模式：驱动弹丸和射击任务
                    dt = 0.5
                    while command.pending_sim_time > 0:
                        step = min(dt, command.pending_sim_time)
                        self.tac_manager.update(step)
                        command.pending_sim_time -= step
                else:
                    # 宏观模式
                    dt = 5.0
                    limit = min(command.pending_sim_time, 1000.0)  # 限制单帧最大推进
                    while limit > 0:
                        step = min(dt, limit)
                        for s in self.ships: s.update_logic(self.body, step)
                        limit -= step
                        command.pending_sim_time -= step

                self.ships = [s for s in self.ships if getattr(s, 'visible', True)]

            self.draw()
            clock.tick(60)