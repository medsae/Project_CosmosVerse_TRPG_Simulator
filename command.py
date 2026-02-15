from firing_task import FiringTask
from fire_control import FireControl
import physics
import dashboard
import math
import detect
import os
from tactical_config import TACTICAL_THRESHOLD

# --- 全局变量 ---
pending_sim_time = 0.0
last_alert_pair = None


def format_timespan(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    parts = []
    if h > 0: parts.append(f"{h}h")
    if m > 0: parts.append(f"{m}m")
    if s > 0 or not parts: parts.append(f"{s}s")
    return " ".join(parts)


def handle_command(cmd_input, body, ships, tac_manager):
    global pending_sim_time, last_alert_pair
    if not cmd_input:
        return True

    cmd_str = cmd_input[0].lower()

    try:
        # === 模式 0: 战术模式激活 (y) ===
        if cmd_str == 'y':
            if last_alert_pair:
                s1, s2 = last_alert_pair
                tac_manager.activate(s1, s2, ships)
                last_alert_pair = None
            else:
                print("⚠️ 当前没有待处理的警报，无法进入战术模式。")
            return True

        # === 模式 1: 时间推进 ===
        elif cmd_str.isdigit() or (cmd_str.replace('.', '', 1).isdigit()):
            total_time = float(cmd_str)
            dt = 1.0
            elapsed = 0.0

            while elapsed < total_time:
                # 1. 优先跑战术更新
                if tac_manager.is_active:
                    # [新增逻辑] 处理持续自动射击指令的更新
                    for s in ships:
                        if getattr(s, 'visible', True) and hasattr(s, 'auto_target_data'):
                            target, weapon, r_count = s.auto_target_data
                            if r_count > 0 and getattr(target, 'visible', True):
                                # 每一秒重新计算一次火控预瞄（对抗轨道偏航）
                                lead = FireControl.calculate_lead_angle(s, target, tac_manager, weapon)
                                rpm = tac_manager.proj_manager.templates.get(weapon, {}).get('rpm', 600)
                                if not hasattr(s, 'firing_tasks'): s.firing_tasks = []
                                # 每次下达一发的任务，由 TacticalManager 逐秒处理
                                s.firing_tasks.append(FiringTask(weapon, lead, 1, rpm))
                                s.auto_target_data[2] -= 1
                            elif not getattr(target, 'visible', True):
                                delattr(s, 'auto_target_data')
                                print(f" [FCS] 目标 {target.name} 已销毁，停止射击。")

                    tac_manager.update(dt)
                else:
                    # 大地图物理更新
                    for s in ships:
                        if getattr(s, 'visible', True):
                            s.update_logic(body, dt)

                # 2. 拦截熔断检查 (仅在大地图模式)
                if not tac_manager.is_active:
                    break_simulation = False
                    for i in range(len(ships)):
                        for j in range(i + 1, len(ships)):
                            s1, s2 = ships[i], ships[j]
                            is_related = (getattr(s1, 'launcher', None) == s2 or getattr(s2, 'launcher', None) == s1)
                            if is_related: continue
                            if not getattr(s1, 'visible', True) or not getattr(s2, 'visible', True): continue

                            dist_m = detect.range_find(s1, s2, body)
                            if dist_m < TACTICAL_THRESHOLD:
                                print(f"\n [拦截熔断] 检测到 {s1.name} 与 {s2.name} 接近中！")
                                print(f"当前距离: {dist_m:.2f}m")
                                last_alert_pair = (s1, s2)
                                break_simulation = True
                                break
                        if break_simulation: break
                    if break_simulation: return True
                elapsed += dt
            return True

        # === 模式 2: 拦截 (intercept) ===
        elif cmd_str == 'intercept' and len(cmd_input) >= 3:
            src_name, dst_name = cmd_input[1], cmd_input[2]
            ship_src = next((s for s in ships if s.name == src_name), None)
            ship_dst = next((s for s in ships if s.name == dst_name), None)
            if ship_src and ship_dst:
                ship_src.target_vessel = ship_dst
                wait_time = physics.calculate_wait_time(body, ship_src, ship_dst)
                t_spent = physics.calculate_hohmann_transfer_time(body, ship_src, ship_dst.height)
                ship_src.set_intercept_task(wait_time, t_spent, ship_dst.height)
                print(f"  任务确认: {ship_src.name} -> {ship_dst.name}")
                print(f"   - 点火倒计时: {wait_time:.1f}s")
                print(f"   - 转移时间: {t_spent:.1f}s")
            return True

        # === 模式 3: 战术锁定 (lock) ===
        elif cmd_str == 'lock' and len(cmd_input) >= 3:
            msl_name, tgt_name = cmd_input[1], cmd_input[2]
            msl = next((s for s in ships if s.name == msl_name), None)
            tgt = next((s for s in ships if s.name == tgt_name), None)
            if msl and tgt:
                msl.target_vessel = tgt
                print(f" [火控锁定] {msl_name} ➔ {tgt_name}。")
            return True

        # === 模式 4: 战术机动 (tac_move) ===
        elif cmd_str == 'tac_move' and len(cmd_input) >= 4:
            ship = next((s for s in ships if s.name == cmd_input[1]), None)
            if ship:
                ship.target_dv_x = float(cmd_input[2])
                ship.target_dv_y = float(cmd_input[3])
                print(f"✅ [机动指令] {ship.name} 设定 dV: ({cmd_input[2]}, {cmd_input[3]}) m/s")
            return True

        # === 模式 5: 战术射击 (fire / auto_fire / keep_fire) ===
        elif cmd_str == 'fire' and len(cmd_input) >= 5:
            if not tac_manager.is_active: return True
            ship = next((s for s in ships if s.name == cmd_input[1]), None)
            if ship:
                weapon = cmd_input[2]
                rpm = tac_manager.proj_manager.templates.get(weapon, {}).get('rpm', 60)
                if not hasattr(ship, 'firing_tasks'): ship.firing_tasks = []
                ship.firing_tasks.append(FiringTask(weapon, float(cmd_input[3]), int(cmd_input[4]), rpm))
                print(f" {ship.name} 开火指令已下达。")
            return True

        elif cmd_str == 'auto_fire' and len(cmd_input) >= 5:
            if not tac_manager.is_active: return True
            src = next((s for s in ships if s.name == cmd_input[1]), None)
            dst = next((s for s in ships if s.name == cmd_input[2]), None)
            if src and dst:
                lead = FireControl.calculate_lead_angle(src, dst, tac_manager, cmd_input[3])
                rpm = tac_manager.proj_manager.templates.get(cmd_input[3], {}).get('rpm', 600)
                if not hasattr(src, 'firing_tasks'): src.firing_tasks = []
                src.firing_tasks.append(FiringTask(cmd_input[3], lead, int(cmd_input[4]), rpm))
                print(f" [FCS] 计算预瞄完成: {lead:.2f}°")
            return True

        elif cmd_str == 'keep_fire' and len(cmd_input) >= 5:
            # 持续跟踪射击指令: keep_fire [src] [dst] [weapon] [total_rounds]
            if not tac_manager.is_active: return True
            src = next((s for s in ships if s.name == cmd_input[1]), None)
            dst = next((s for s in ships if s.name == cmd_input[2]), None)
            if src and dst:
                src.auto_target_data = [dst, cmd_input[3], int(cmd_input[4])]
                print(f" [FCS] 持续火控跟踪已启动: {src.name} -> {dst.name}")
            return True

        # === 模式 6: 部署 (launch) ===
        elif cmd_str == 'launch' and len(cmd_input) >= 4:
            parent = next((s for s in ships if s.name == cmd_input[1]), None)
            m_type, new_name = cmd_input[2].upper(), cmd_input[3]
            if parent and m_type in getattr(physics, 'missile_templates', {}):
                t = physics.missile_templates[m_type]
                from ship import Missile
                new_msl = Missile(
                    name=new_name, fuelmass=t['fuel'], drymass=t['dry'],
                    area=parent.area * 0.1, heat=parent.heat, flowrate=t['flow'],
                    max_thrust=t['thrust'], height=parent.height,
                    initial_position=parent.initial_position + 0.00001,
                    orbit_direction=parent.orbit_direction,
                    fuse_range=t.get('fuse_range', 150), yield_radius=t.get('yield_radius', 350)
                )
                new_msl.launcher = parent
                new_msl.target_dv_x = 0.0
                new_msl.target_dv_y = 0.0
                ships.append(new_msl)
                if tac_manager.is_active:
                    tac_manager.register_new_unit(new_msl)
                    p_data = tac_manager.local_data.get(parent)
                    if p_data:
                        tac_manager.local_data[new_msl].update({'vx':p_data['vx'], 'vy':p_data['vy'], 'x':p_data['x'], 'y':p_data['y']})
                print(f" [部署] {new_name} 已就位。")
            return True

        # === 模式 7: 作弊指令 (tac_set) ===
        elif cmd_str == 'tac_set' and len(cmd_input) >= 6:
            if not tac_manager.is_active:
                print("⚠️ 只能在战术模式下使用 tac_set。")
                return True
            target_name = cmd_input[1]
            target_obj = next((s for s in tac_manager.local_data.keys() if s.name == target_name), None)
            if target_obj:
                new_vals = [float(x) for x in cmd_input[2:6]] # x, y, vx, vy
                data = tac_manager.local_data[target_obj]
                data['x'], data['y'], data['vx'], data['vy'] = new_vals
                target_obj.tac_x, target_obj.tac_y = new_vals[0], new_vals[1]
                target_obj.vx, target_obj.vy = new_vals[2], new_vals[3]
                print(f"🛠️ [作弊] {target_name} 坐标已重置为: Pos({new_vals[0]},{new_vals[1]}) Vel({new_vals[2]},{new_vals[3]})")
            else:
                print(f"⚠️ 战术区未找到单位: {target_name}")
            return True
            # === 模式 8: 退出战术模式 (tac_exit) ===
        elif cmd_str == 'tac_exit':
            if tac_manager.is_active:
                # 1. 将战术坐标增量同步回大地图轨道参数
                tac_manager.sync_to_global()
                # 2. 清除所有飞船的战术临时属性
                for s in ships:
                    if hasattr(s, 'auto_target_data'): delattr(s, 'auto_target_data')
                    if hasattr(s, 'firing_tasks'): s.firing_tasks = []

                print(" [系统] 战术模式已关闭，坐标数据已同步至大地图。")
            else:
                print("⚠️ 当前不处于战术模式。")
            return True
        # === 基础指令 ===
        elif cmd_str == 'status':
            dashboard.display_dashboard(body, ships)
            return True
        elif cmd_str == 'exit':
            return False

    except Exception as e:
        print(f"⚠️ 指令执行异常: {e}")
    return True