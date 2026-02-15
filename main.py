import json
import os
import threading
from Star import Star
from ship import Ship, Missile
import dashboard
import command
import physics
from tactical_sim import TacticalManager
from visualizer import SpaceVisualizer


def load_ships_from_config(filename):
    ships = []
    if not os.path.exists(filename):
        print(f"⚠️ 找不到配置文件 {filename}")
        return []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            config = json.load(f)

            if 'ships' in config:
                for s in config['ships']:
                    h_in_meters = s['height']
                    new_ship = Ship(
                        s['name'], s['fuelmass'], s['drymass'], s['area'],
                        s['heat'], s['flowrate'], s['max_thrust'],
                        h_in_meters, s['initial_position']
                    )
                    ships.append(new_ship)

            if 'missile_templates' in config:
                physics.missile_templates = config['missile_templates']
                print(f"✅ 已成功载入导弹模版: {list(physics.missile_templates.keys())}")

        print(f"✅ 已加载 {len(ships)} 艘飞船单位。")
    except Exception as e:
        print(f"❌ 加载出错: {e}")
    return ships


def input_thread(body, ships, tac_manager):
    """
    处理控制台输入的线程
    """
    while True:
        try:
            print("\n" + "=" * 50)
            print(" 指令: [秒数] | intercept [A] [B] | launch [A] [T] [N] | tac_move [N] [x] [y] | status | exit")
            user_input = input("指令 > ").strip().split()
            if not user_input: continue

            # 调用 handle_command 并传入 tac_manager
            if not command.handle_command(user_input, body, ships, tac_manager):
                print("[系统] 关闭中...")
                os._exit(0)
        except Exception as e:
            print(f"⚠️ 指令处理错误: {e}")


def main():
    # 地球物理参数
    Earth = Star("Terra", 5.98e24, 6.38e6)

    # 加载飞船
    ships = load_ships_from_config('ships.json')
    if not ships:
        print("❌ 未能加载飞船数据，程序退出。")
        return

    # 初始化战术管理器
    tac_manager = TacticalManager(Earth)

    with open('projectiles.json', 'r', encoding='utf-8') as f:
        proj_templates = json.load(f)
        tac_manager.proj_manager.templates = proj_templates
    # 打印初始看板
    dashboard.display_dashboard(Earth, ships)

    # 启动指令监听线程
    t = threading.Thread(target=input_thread, args=(Earth, ships, tac_manager), daemon=True)
    t.start()

    print("\n[系统] 轨道图启动中... 请在大地图输入指令。")

    # 启动可视化窗口
    viz = SpaceVisualizer(Earth, ships, tac_manager)
    viz.run_loop()


if __name__ == "__main__":
    main()