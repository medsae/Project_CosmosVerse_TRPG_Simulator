import json
import os
from Star import Star

def load_all_stars(filename='stars.json'):
    """
    加载所有可用的恒星数据并返回列表
    """
    if not os.path.exists(filename):
        print(f"⚠️ 找不到配置文件 {filename}，仅提供默认地球。")
        return [Star("Terra", 5.98e24, 6.38e6)]

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            stars = [Star(s['name'], s['mass'], s['radius']) for s in data.get("stars", [])]
            return stars if stars else [Star("Terra", 5.98e24, 6.38e6)]
    except Exception as e:
        print(f"❌ 加载出错: {e}")
        return [Star("Terra", 5.98e24, 6.38e6)]