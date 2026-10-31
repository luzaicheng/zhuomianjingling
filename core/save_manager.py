# core/save_manager.py
import json
import os
import time
import sys


class SaveManager:
    def __init__(self, filename="save_data.json"):
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.file_path = os.path.join(self.base_dir, filename)
        self.data = self._load()

    def _load(self):
        default_data = {
            "affection": 50,  # 好感度 (0-100)
            "hunger": 100,  # 饱腹度 (0-100)
            "sleep": 100,  # 睡眠度 (0-100)
            "last_time": time.time()
        }

        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 离线时间计算（关掉软件后的时间差）
                now = time.time()
                elapsed_hours = (now - data.get("last_time", now)) / 3600.0

                # 离线扣减：每小时只饿 1 点，困 0.5 点
                data["hunger"] = max(0, data.get("hunger", 100) - int(elapsed_hours * 1))
                data["sleep"] = max(0, data.get("sleep", 100) - int(elapsed_hours * 0.5))

                # 长时间不玩，好感度降低（越饿掉得越快）
                aff_loss = int(elapsed_hours * 1)
                if data["hunger"] < 20:
                    aff_loss += int(elapsed_hours * 2)
                data["affection"] = max(0, data.get("affection", 50) - aff_loss)

                return data
            except Exception as e:
                print(f"[SaveManager] 存档读取失败: {e}")
                return default_data
        return default_data

    def save(self, affection, hunger, sleep):
        self.data["affection"] = affection
        self.data["hunger"] = hunger
        self.data["sleep"] = sleep
        self.data["last_time"] = time.time()
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[SaveManager] 存档保存失败: {e}")