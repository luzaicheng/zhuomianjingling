# core/system_monitor.py
import time
import win32api
import datetime
import psutil


class SystemMonitor:
    def __init__(self):
        self.last_mouse_pos = win32api.GetCursorPos()
        self.last_active_time = time.time()

        self.is_typing = False
        self.is_idle = False

        self.type_cooldown = 0.0
        self.idle_cooldown = 0.0

        # 时间彩蛋冷却
        self.time_event_cooldown = 0.0
        self.last_hour = datetime.datetime.now().hour
        self.last_date = datetime.datetime.now().day

    def update(self, dt):
        now = datetime.datetime.now()

        # --- 鼠标/键盘活跃度 ---
        current_mouse_pos = win32api.GetCursorPos()
        if current_mouse_pos != self.last_mouse_pos:
            self.last_mouse_pos = current_mouse_pos
            self.last_active_time = time.time()

        typing_detected = False
        for key in [0x41, 0x42, 0x43, 0x44, 0x45, 0x53, 0x57, 0x20, 0x0D]:
            if win32api.GetAsyncKeyState(key) & 0x8000:
                typing_detected = True
                break
        if typing_detected:
            self.last_active_time = time.time()

        # 冷却递减
        if self.type_cooldown > 0: self.type_cooldown -= dt
        if self.idle_cooldown > 0: self.idle_cooldown -= dt
        if self.time_event_cooldown > 0: self.time_event_cooldown -= dt

        # --- 触发条件判断 ---
        self.is_typing = typing_detected and self.type_cooldown <= 0
        self.is_idle = (time.time() - self.last_active_time > 120.0) and self.idle_cooldown <= 0

        # 🎁 彩蛋1：深夜修仙警告
        self.is_night_owl = (now.hour >= 23 or now.hour < 5) and self.time_event_cooldown <= 0

        # 🎁 彩蛋2：整点报时
        self.is_new_hour = (now.hour != self.last_hour) and self.time_event_cooldown <= 0
        self.last_hour = now.hour

        # 🎁 彩蛋3：周五/周末狂欢
        self.is_friday = (now.weekday() == 4 and now.hour >= 18) and self.time_event_cooldown <= 0

        # 🎁 彩蛋4：午休时间 (12:00 - 13:00)
        self.is_lunch_time = (now.hour == 12 and now.minute < 30) and self.time_event_cooldown <= 0

        # 🎁 彩蛋5：电脑发高烧 (CPU > 80%)
        self.is_cpu_hot = (psutil.cpu_percent(interval=None) > 80.0) and self.type_cooldown <= 0