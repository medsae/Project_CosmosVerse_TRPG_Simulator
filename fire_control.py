import math


class FireControl:
    @staticmethod
    def calculate_lead_angle(vessel_src, vessel_dst, tac_manager, weapon_key):
        """
        高精度火控解算：考虑安全偏移、惯性叠加与轨道漂移
        """
        # 1. 获取基础数据
        s_data = tac_manager.local_data.get(vessel_src)
        t_data = tac_manager.local_data.get(vessel_dst)
        if not s_data or not t_data:
            return 0.0

        # 获取武器出速
        weapon_temp = tac_manager.proj_manager.templates.get(weapon_key, {})
        v_muzzle = weapon_temp.get('muzzle_velocity', 1000.0)

        # 获取轨道角速度 n (用于 Hill 方程预测)
        n = getattr(tac_manager, 'orbital_n', 0.0)

        # 获取发射安全偏移量
        safe_dist = vessel_src.get_hitbox_radius() + 50.0

        # 2. 基础相对数据
        dx = t_data['x'] - s_data['x']
        dy = t_data['y'] - s_data['y']
        # 相对速度
        dvx = t_data['vx'] - s_data['vx']
        dvy = t_data['vy'] - s_data['vy']

        # 3. 迭代计算碰撞时间 (t) 与预瞄点
        dist = math.sqrt(dx ** 2 + dy ** 2)
        # 初始估计时间：扣除炮口偏移
        t = max(0, dist - safe_dist) / v_muzzle

        for _ in range(4):  # 增加到 4 次迭代以应对轨道弯曲
            # A. 计算目标在 t 时间后的线性预测位置
            lead_x = dx + dvx * t
            lead_y = dy + dvy * t

            # B. [新增] 轨道漂移修正 (Hill 方程二阶近似)
            # 根据 Hill 方程，子弹在运动中会产生额外的相对加速度
            # ax_drift ≈ 3*n^2*x + 2*n*vy
            # ay_drift ≈ -2*n*vx
            # 我们根据目标的大致方位，预测子弹路径上的平均偏航
            drift_x = 0.5 * (3 * n ** 2 * lead_x + 2 * n * dvy) * t ** 2
            drift_y = 0.5 * (-2 * n * dvx) * t ** 2

            # 修正后的预瞄点（反向补偿漂移）
            target_pos_x = lead_x - drift_x
            target_pos_y = lead_y - drift_y

            # C. 更新飞行时间估计
            current_dist = math.sqrt(target_pos_x ** 2 + target_pos_y ** 2)
            t = max(0, current_dist - safe_dist) / v_muzzle

        # 4. 计算最终射击角度
        # 我们需要解一个矢量三角形：V_final = V_ship + V_muzzle
        # 为了让 V_final 指向目标，我们需要补偿母舰自身的运动
        final_x = dx + dvx * t - (0.5 * (3 * n ** 2 * dx + 2 * n * dvy) * t ** 2)
        final_y = dy + dvy * t - (0.5 * (-2 * n * dvx) * t ** 2)

        angle_rad = math.atan2(final_y, final_x)
        return math.degrees(angle_rad)