# dashboard.py
import detect
import physics


def display_dashboard(body, all_ships):
    from ship import Missile
    width = 125
    print("\n" + "=" * width)
    print(f"🛰️ 战略态势看板 - 天体: {body.name} | 系统状态: 运行中")
    print("=" * width)

    # 1. 单位实时数据表
    print(
        f"{'类型':<6} {'名称':<10} {'轨道半径(km)':<15} {'角度(°)':<10} {'燃料(kg)':<12} {'可用Δv(m/s)':<15} {'当前任务'}")
    print("-" * width)
    for s in all_ships:
        unit_type = "MSL" if isinstance(s, Missile) else "SHIP"
        dv = s.calculate_delta_v()
        # 区分颜色或标记
        prefix = " >" if isinstance(s, Missile) else "  "
        print(
            f"{prefix}{unit_type:<4} {s.name:<10} {s.height / 1000:<15.1f} {s.initial_position:<10.1f} {s.fuelmass:<12.1f} {dv:<15.1f} {s.state}")

    print("\n📡 战术侦察与拦截窗口报告:")
    for s1 in all_ships:
        # 只显示非隐藏单位的视角
        if not s1.visible: continue

        print(f"\n[ {s1.name} 视角 ]")
        print(
            f"   {'目标':<8} | {'距离(km)':<10} | {'通信':<6} | {'相对高度':<10} | {'拦截Δv(m/s)':<12} | {'最佳窗口'}")
        print("   " + "-" * (width - 20))

        for s2 in all_ships:
            if s1 == s2 or not s2.visible: continue

            dist = detect.range_find(s1, s2, body)
            occluded = detect.is_occluded(s1, s2, body)
            t_wait = physics.calculate_wait_time(body, s1, s2)
            req_dv = physics.get_hohmann_dv(body, s1, s2.height)

            comm_status = "❌" if occluded else "OK"

            if abs(s1.height - s2.height) < 100:
                rel = "同轨"
            else:
                rel = f"{'+' if s2.height > s1.height else '-'}{abs(s2.height - s1.height) / 1000:.0f}km"

            print(
                f"   {s2.name:<8} | {dist / 1000:<10.1f} | {comm_status:<6} | {rel:<10} | {req_dv:<12.1f} | {t_wait:.1f}s")

    print("\n" + "=" * width)