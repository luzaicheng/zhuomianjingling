# main.py
"""
Project: Sprite — 终极养成版
功能：真透明 + 点击穿透 + 帧动画 + 状态机 + 右键菜单 + JSON外置台词 + 系统感知 + 养成数值系统
"""

import sys
import pygame
import random
import time
import datetime
import win32api
import win32gui
import win32con
import json
import os


# ============================================================
#  资源与配置路径解析
# ============================================================
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_external_file_path(filename):
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def load_dialogues():
    json_path = get_external_file_path("dialogues.json")
    default_data = {
        "click_quotes": ["不要再戳我啦！", "嘿嘿，好痒~", "我是不是很可爱呀？"],
        "idle_quotes": ["今天也要加油哦~", "写代码辛苦啦~", "好无聊啊，理理我嘛。"],
        "system_quotes": {
            "night_owl": "主人，熬夜会秃头的！快睡觉！",
            "friday": "周五啦！周末要去哪里玩？",
            "lunch": "12点半啦，该吃午饭啦！别饿着。",
            "cpu_hot": "电脑好烫... 谁在跑大程序呀？",
            "typing": "打字好快呀！加油！",
            "new_hour_prefix": "叮咚~ 现在是 "
        },
        "startup_quotes": {
            "0": "今天星期一，又要早起打工了，好困哦...",
            "1": "今天星期二，感觉时间过得好慢，主人加油！",
            "2": "今天星期三，已经熬过一半啦，马上就能休息了！",
            "3": "今天星期四，疯狂星期四！主人要请我吃炸鸡吗？",
            "4": "今天星期五，明天就放假啦，好开心！",
            "5": "今天星期六，周末愉快！主人要带我出去玩吗？",
            "6": "今天星期日，呜呜，明天又要上班/上学了..."
        }
    }

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Error] 读取 dialogues.json 失败: {e}")
            return default_data
    else:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data


# ============================================================
#  引入项目内的其他模块
# ============================================================
from core.speech_bubble import SpeechBubble
from core.system_monitor import SystemMonitor
from core.save_manager import SaveManager
from config import (
    WINDOW_FPS, GRAVITY, MAX_FALL_SPEED, PET_START_X, PET_START_Y,
    DEBUG_MODE, GROUND_OFFSET, DRAG_RELEASE_JUMP, DRAG_RELEASE_JUMP_VY,
    WINDOW_TOPMOST, WINDOW_SHOW_IN_TASKBAR, WINDOW_CLICK_THROUGH,
)
from core.animation import AnimationPlayer
from core.pet_ai import build_pet_fsm
from core.layered_window import LayeredWindow, get_mouse_pos
from assets.placeholder_gen import (
    make_idle_frames, make_walk_frames,
    make_sleep_frames, make_drag_frames,
)


# ============================================================
#  宠物实体
# ============================================================
class PetEntity:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        import math

        img_path = get_resource_path("assets/pet/test.png")

        if os.path.exists(img_path):
            print(f"[AssetLoader] 正在加载真实图片: {img_path}")
            base_img = pygame.image.load(img_path).convert_alpha()
            mask = pygame.mask.from_surface(base_img)
            rect = mask.get_bounding_rects()[0]
            base_img = base_img.subsurface(rect).copy()

            target_h = 80
            self.visual_h = target_h
            w, h = base_img.get_size()
            target_w = int(w * (target_h / h))
            base_img = pygame.transform.smoothscale(base_img, (target_w, target_h))
            canvas_w = int(target_w * 1.5)
            canvas_h = int(target_h * 1.5)

            def make_deformed_frame(scale_x=1.0, scale_y=1.0, angle=0.0, offset_y=0):
                fw, fh = int(target_w * scale_x), int(target_h * scale_y)
                fw, fh = max(1, fw), max(1, fh)
                surf = pygame.transform.smoothscale(base_img, (fw, fh))
                if angle != 0:
                    surf = pygame.transform.rotate(surf, angle)
                frame = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)
                rect = surf.get_rect()
                rect.midbottom = (canvas_w // 2, canvas_h - 10 + offset_y)
                frame.blit(surf, rect.topleft)
                return frame

            self.frame_sets = {
                "idle": [make_deformed_frame(scale_x=1.0, scale_y=1.0), make_deformed_frame(scale_x=1.04, scale_y=0.96),
                         make_deformed_frame(scale_x=0.98, scale_y=1.02),
                         make_deformed_frame(scale_x=1.02, scale_y=0.98)],
                "walk": [make_deformed_frame(angle=-5, offset_y=0), make_deformed_frame(angle=-2, offset_y=-4),
                         make_deformed_frame(angle=5, offset_y=0), make_deformed_frame(angle=2, offset_y=-4)],
                "drag": [make_deformed_frame(scale_x=0.85, scale_y=1.15, angle=-8),
                         make_deformed_frame(scale_x=0.85, scale_y=1.15, angle=8)],
                "sleep": [make_deformed_frame(scale_x=1.1, scale_y=0.85, offset_y=5),
                          make_deformed_frame(scale_x=1.12, scale_y=0.83, offset_y=6)],
            }
        else:
            print(f"[AssetLoader] 找不到 {img_path}，使用默认占位图")
            self.visual_h = 80
            self.frame_sets = {
                "idle": make_idle_frames(), "walk": make_walk_frames(),
                "sleep": make_sleep_frames(), "drag": make_drag_frames(),
            }

        self.anim = AnimationPlayer(self.frame_sets["idle"], fps=4, loop=True)
        self.rect = self.anim.current_frame.get_rect()
        self.rect.centerx = PET_START_X
        self.rect.bottom = PET_START_Y

        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.dragging = False
        self._drag_offset = (0, 0)
        self.fsm = build_pet_fsm()
        self.fsm.change("idle", self)
        self.bubble = SpeechBubble()

        # 核心属性
        self.affection = 50
        self.hunger = 100
        self.sleep = 100

        # 高级状态标记
        self.flee_timer = 0.0
        self.flee_vx = 0.0
        self.flee_vy = 0.0
        self.is_sleeping_forced = False
        self.is_following_mouse = False
        self.follow_target_x = 0
        self.follow_target_y = 0

    def set_animation(self, name, fps, loop=True):
        if name in self.frame_sets:
            self.anim.set_frames(self.frame_sets[name], fps=fps, loop=loop)
            self.rect.w = self.anim.current_frame.get_width()
            self.rect.h = self.anim.current_frame.get_height()

    def apply_physics(self, dt):
        if self.dragging:
            return

        # 漫游模式
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt

        if self.rect.left < 0:
            self.rect.left = 0
            self.vx = abs(self.vx)
            self.facing = 1
        elif self.rect.right > self.screen_w:
            self.rect.right = self.screen_w
            self.vx = -abs(self.vx)
            self.facing = -1

        if self.rect.top < 0:
            self.rect.top = 0
            self.vy = abs(self.vy)
        elif self.rect.bottom > self.screen_h:
            self.rect.bottom = self.screen_h
            self.vy = -abs(self.vy)

    def start_drag(self, mouse_pos):
        self.dragging = True
        self.vx = self.vy = 0
        self._drag_offset = (self.rect.x - mouse_pos[0], self.rect.y - mouse_pos[1])
        if not self.is_sleeping_forced:
            self.fsm.change("drag", self)

    def update_drag(self, mouse_pos):
        if not self.dragging: return
        self.rect.x = mouse_pos[0] + self._drag_offset[0]
        self.rect.y = mouse_pos[1] + self._drag_offset[1]

    def end_drag(self):
        self.dragging = False
        if not self.is_sleeping_forced:
            if DRAG_RELEASE_JUMP:
                self.vy = DRAG_RELEASE_JUMP_VY
            self.fsm.change("idle", self)

    def start_flee(self, speed=300):
        self.flee_timer = 2.0  # 逃跑时间也缩短一点
        self.bubble.show("太烦啦！我跑啦！", duration=2.0)
        self.flee_vx = random.choice([-1, 1]) * speed
        self.flee_vy = random.choice([-1, 1]) * speed
        self.fsm.change("walk", self)

    def teleport_flee(self):
        self.flee_timer = 3.0
        self.bubble.show("我受不了啦！消失吧你！", duration=2.0)
        self.rect.centerx = random.randint(100, self.screen_w - 100)
        self.rect.centery = random.randint(100, self.screen_h - 100)
        self.flee_vx = random.choice([-1, 1]) * 1500
        self.flee_vy = random.choice([-1, 1]) * 1500
        self.fsm.change("walk", self)

    def update(self, dt):
        # 0. 绝对强制睡眠（最高优先级，封印一切物理与AI）
        if self.is_sleeping_forced:
            self.vx = 0
            self.vy = 0
            self.apply_physics(dt)
            self.anim.update(dt)
            self.bubble.update(dt)
            return  # 👈 直接返回，不执行后续的任何状态机

        # 1. 逃跑状态
        if self.flee_timer > 0:
            self.flee_timer -= dt
            self.vx = self.flee_vx
            self.vy = self.flee_vy
            self.apply_physics(dt)
            self.anim.update(dt)
            self.bubble.update(dt)
            return

        # 2. 饥饿跟随鼠标状态（强制覆盖AI）
        if self.is_following_mouse and not self.is_sleeping_forced:
            dx = self.follow_target_x - self.rect.centerx
            dy = self.follow_target_y - self.rect.centery
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if dist > 60:
                self.vx = (dx / dist) * 150
                self.vy = (dy / dist) * 150

                # 【核心修复】加入死区判断，避免 vx 在 0 附近徘徊时左右疯狂转头
                if self.vx > 10:
                    self.facing = 1
                elif self.vx < -10:
                    self.facing = -1

                # 只在没有进入走路状态时才切换，防止每帧重复触发状态机
                if self.fsm.current.name != "walk":
                    self.fsm.change("walk", self)
            else:
                self.vx = 0
                self.vy = 0
                if self.fsm.current.name != "idle":
                    self.fsm.change("idle", self)

            self.apply_physics(dt)
            self.anim.update(dt)
            self.bubble.update(dt)
            return

        # 3. 正常AI状态
        self.fsm.update(self, dt)
        self.apply_physics(dt)
        self.anim.update(dt)
        self.bubble.update(dt)

    def draw(self, screen):
        frame = self.anim.current_frame
        if self.facing == -1:
            frame = pygame.transform.flip(frame, True, False)
        draw_rect = frame.get_rect()
        draw_rect.midbottom = self.rect.midbottom
        screen.blit(frame, draw_rect.topleft)

        head_y = self.rect.bottom - self.visual_h + 45
        self.bubble.draw(screen, self.rect.centerx, head_y)

        if DEBUG_MODE:
            pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)
            font = pygame.font.SysFont("consolas", 16, bold=True)
            txt = font.render(f"STATE: {self.fsm.current.name}", True, (0, 0, 0))
            screen.blit(txt, (self.rect.x, self.rect.y - 22))


# ============================================================
#  分层窗口
# ============================================================
class Win32Renderer:
    WIN_W = 350
    WIN_H = 350

    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.width = info.current_w
        self.height = info.current_h

        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        self.big_screen = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        self.layered = LayeredWindow(
            self.WIN_W, self.WIN_H, title="Project Sprite",
            topmost=WINDOW_TOPMOST, show_in_taskbar=WINDOW_SHOW_IN_TASKBAR,
        )
        self.layered.show()

        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0.0
        self.current_click_through = True
        self.layered.set_click_through(True)

    def tick(self):
        self.dt = self.clock.tick(WINDOW_FPS) / 1000.0
        return self.dt

    def clear(self):
        self.big_screen.fill((0, 0, 0, 0))

    def flip(self, pet_rect):
        win_x = int(pet_rect.centerx - self.WIN_W // 2)
        win_y = int(pet_rect.centery - self.WIN_H // 2)
        small_surf = pygame.Surface((self.WIN_W, self.WIN_H), pygame.SRCALPHA)
        small_surf.blit(self.big_screen, (0, 0), pygame.Rect(win_x, win_y, self.WIN_W, self.WIN_H))
        self.layered.render(small_surf, win_x, win_y)

    def quit(self):
        self.layered.destroy()
        pygame.quit()


# ============================================================
#  原生右键菜单（带彩色长条状态）
# ============================================================
def show_context_menu(hwnd, x, y, pet):
    # 辅助函数：生成 10 格长度的彩色进度条
    def make_bar(value, block_char):
        value = max(0, min(100, value))
        filled = int((value / 100.0) * 10)
        empty = 10 - filled
        return block_char * filled + "⬜" * empty

    aff_bar = make_bar(pet.affection, "🟥")
    hun_bar = make_bar(pet.hunger, "🟩")
    slp_bar = make_bar(pet.sleep, "🟦")

    menu = win32gui.CreatePopupMenu()

    # 这里去掉了文字，只用图标 + 彩色长条
    win32gui.AppendMenu(menu, win32con.MF_STRING, 1005, f"❤️ {aff_bar}")
    win32gui.AppendMenu(menu, win32con.MF_STRING, 1004, f"🍖 {hun_bar}")
    win32gui.AppendMenu(menu, win32con.MF_STRING, 1002, f"💤 {slp_bar}")

    win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
    win32gui.AppendMenu(menu, win32con.MF_STRING, 1003, "❌ 退出软件")

    # 临时去掉不激活属性，强制夺取焦点（解决点空白处不消失的 Bug）
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style & ~0x08000000)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass

    cmd = win32gui.TrackPopupMenu(
        menu, win32con.TPM_LEFTALIGN | win32con.TPM_BOTTOMALIGN | win32con.TPM_RETURNCMD,
        x, y, 0, hwnd, None
    )
    win32gui.DestroyMenu(menu)

    # 恢复属性
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
    win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)

    return cmd


# ============================================================
#  主循环
# ============================================================
def main():
    renderer = Win32Renderer()
    pet = PetEntity(renderer.width, renderer.height)
    monitor = SystemMonitor()
    save_manager = SaveManager()

    # 挂载数据
    pet.affection = save_manager.data["affection"]
    pet.hunger = save_manager.data["hunger"]
    pet.sleep = save_manager.data.get("sleep", 100)

    dialogues = load_dialogues()
    startup_quotes = dialogues.get("startup_quotes", {})
    click_quotes = dialogues["click_quotes"]
    idle_quotes = dialogues["idle_quotes"]
    sys_quotes = dialogues["system_quotes"]

    # 启动开场白
    today_weekday = str(datetime.datetime.now().weekday())
    welcome_text = startup_quotes.get(today_weekday, "新的一天，你好呀！")
    pet.bubble.show(welcome_text, duration=4.0)

    prev_mouse_left = False
    is_holding = False
    press_pos = (0, 0)
    chat_timer = 0.0
    click_lock_timer = 0.0
    click_times = []
    continuous_click_start_time = 0.0
    last_click_time = 0.0
    last_save_time = time.time()

    while renderer.running:
        dt = renderer.tick()
        # 【核心修复】限制最大时间步长为 0.05 秒（50毫秒）
        # 哪怕系统卡死了 10 秒，这帧最多也只走 0.05 秒的距离，绝不移形换位
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                renderer.running = False

        left_down = win32api.GetAsyncKeyState(0x01) & 0x8000 != 0
        right_down = win32api.GetAsyncKeyState(0x02) & 0x8000 != 0
        mx, my = win32api.GetCursorPos()

        hitbox = pet.rect.inflate(-20, -20)
        in_pet = hitbox.collidepoint(mx, my)

        # ---- 右键菜单处理 ----
        if right_down and in_pet:
            cmd = show_context_menu(renderer.layered.hwnd, mx, my, pet)

            # 【核心修复】菜单关闭后，强制重置所有鼠标交互状态！
            # 防止菜单点击事件穿透到主循环，引发瞬间移动
            prev_mouse_left = True
            is_holding = False
            press_pos = (mx, my)
            if pet.dragging:
                pet.end_drag()

            if cmd == 1002:  # 💤 点击蓝色睡眠条
                pet.sleep = min(100, pet.sleep + 20)
                pet.fsm.change("sleep", pet)
                pet.bubble.show("呼呼... 睡一会儿...", duration=3.0)
                save_manager.save(pet.affection, pet.hunger, pet.sleep)
            elif cmd == 1004:  # 🍖 点击绿色饱食条
                if pet.hunger >= 100:
                    pet.bubble.show("我已经吃得饱饱的啦~", duration=3.0)
                else:
                    pet.hunger = min(100, pet.hunger + 40)
                    pet.affection = min(100, pet.affection + 5)
                    pet.bubble.show("哇！好吃！谢谢主人！", duration=3.0)
                    save_manager.save(pet.affection, pet.hunger, pet.sleep)
            elif cmd == 1005:  # ❤️ 点击红色好感条
                if not pet.is_sleeping_forced:
                    pet.affection = min(100, pet.affection + 10)
                    pet.bubble.show("嘿嘿，最喜欢主人了~", duration=3.0)
                    save_manager.save(pet.affection, pet.hunger, pet.sleep)
            elif cmd == 1003:  # ❌ 退出
                renderer.running = False

        if click_lock_timer > 0: click_lock_timer -= dt
        if not pet.bubble.is_active: chat_timer += dt

        # ---- 鼠标穿透 ----
        if in_pet or pet.dragging:
            if renderer.current_click_through:
                renderer.layered.set_click_through(False)
                renderer.current_click_through = False
        else:
            if not renderer.current_click_through:
                renderer.layered.set_click_through(True)
                renderer.current_click_through = True

        # ---- 左键点击与拖拽 ----
        if left_down and not prev_mouse_left:
            if in_pet:
                press_pos = (mx, my)
                is_holding = True  # 开启抓取标记

                # Shift 快捷喂食
                shift_down = win32api.GetAsyncKeyState(0x10) & 0x8000 != 0
                if shift_down:
                    pet.hunger = min(100, pet.hunger + 20)
                    pet.bubble.show("吧唧吧唧... 真好吃！", duration=2.0)
                    save_manager.save(pet.affection, pet.hunger, pet.sleep)
                    click_lock_timer = 1.0

                elif not pet.is_sleeping_forced:
                    now_time = time.time()
                    last_click_time = now_time

                    if continuous_click_start_time == 0:
                        continuous_click_start_time = now_time
                    continuous_duration = now_time - continuous_click_start_time

                    if continuous_duration >= 30.0:
                        pet.teleport_flee()
                        continuous_click_start_time = 0.0
                        click_times.clear()
                        click_lock_timer = 4.0
                    elif continuous_duration >= 10.0:
                        pet.start_flee(speed=800)
                        continuous_click_start_time = 0.0
                        click_times.clear()
                        click_lock_timer = 3.0
                    else:
                        click_times = [t for t in click_times if now_time - t < 1.5]
                        click_times.append(now_time)

                        if len(click_times) >= 5:
                            if click_lock_timer <= 0:
                                pet.bubble.show("别戳啦！要晕啦！(＠_＠)", duration=2.0)
                                click_lock_timer = 2.0
                                click_times.clear()
                        else:
                            if click_lock_timer <= 0:
                                pet.affection = min(100, pet.affection + 2)

                                if pet.affection < 10:
                                    pet.bubble.show("哼，别以为摸我一下我就会原谅你...", duration=2.5)
                                elif pet.affection > 80:
                                    pet.bubble.show("最喜欢主人摸摸了！再摸一下嘛~", duration=3.0)
                                else:
                                    pet.bubble.show(random.choice(click_quotes), duration=3.0)

                                click_lock_timer = 0.3

        elif left_down and prev_mouse_left:
            # 按住并移动：触发拖拽
            if is_holding:
                dist = ((mx - press_pos[0]) ** 2 + (my - press_pos[1]) ** 2) ** 0.5
                if not pet.dragging and dist > 5:
                    pet.start_drag(press_pos)
                if pet.dragging:
                    pet.update_drag((mx, my))

        elif not left_down and prev_mouse_left:
            # 松开鼠标：结束拖拽并重置标记
            is_holding = False
            if pet.dragging:
                pet.end_drag()

        # 👇 这就是你找不到的那行“灵魂代码”，把它放回末尾
        prev_mouse_left = left_down

        if not left_down:
            if continuous_click_start_time > 0 and (time.time() - last_click_time > 1.0):
                continuous_click_start_time = 0.0

        # ==========================================
        # 养成数据（属性衰减与状态触发）
        # ==========================================
        # 随时间减少（佛系陪伴模式：饱腹约 16 小时掉光，睡眠约 33 小时掉光，好感极慢）
        pet.hunger = max(0, pet.hunger - 0.002 * dt * 60)
        pet.affection = max(0, pet.affection - 0.0005 * dt * 60)

        if not pet.is_sleeping_forced:
            pet.sleep = max(0, pet.sleep - 0.001 * dt * 60)

        # 强制睡眠触发（低于 5）
        if pet.sleep < 5 and not pet.is_sleeping_forced:
            pet.is_sleeping_forced = True
            pet.bubble.show("Zzz... 呼噜...", duration=99999.0)

        # 强制睡眠恢复（高于 80）
        if pet.is_sleeping_forced:
            pet.sleep = min(100, pet.sleep + 0.8 * dt)
            # 【核心修复】只在不是睡眠状态时才切换，防止每帧重置状态机
            if pet.fsm.current.name != "sleep":
                pet.fsm.change("sleep", pet)

            if pet.sleep >= 80:
                pet.is_sleeping_forced = False
                pet.fsm.change("idle", pet)
                pet.bubble.show("呼啊~ 睡得好饱！", duration=3.0)

        # 饥饿找鼠标（低于 30）
        if pet.hunger < 30 and not pet.dragging and not pet.is_sleeping_forced:
            pet.is_following_mouse = True
            pet.follow_target_x = mx
            pet.follow_target_y = my
            if not pet.bubble.is_active and random.random() < 0.01:
                pet.bubble.show("我饿了！主人喂喂我~", duration=3.0)
        else:
            pet.is_following_mouse = False

        # ---- 核心更新 ----
        pet.update(dt)
        monitor.update(dt)

        # ---- 系统彩蛋 ----
        if not pet.bubble.is_active and not pet.dragging and click_lock_timer <= 0 and not pet.is_sleeping_forced:
            if monitor.is_night_owl:
                pet.bubble.show(sys_quotes["night_owl"], duration=4.0)
                monitor.time_event_cooldown = 3600
                chat_timer = -15.0
            elif monitor.is_new_hour:
                hour = datetime.datetime.now().hour
                pet.bubble.show(f"{sys_quotes['new_hour_prefix']} {hour} 点整哦！", duration=3.0)
                monitor.time_event_cooldown = 3600
                chat_timer = -15.0
            elif chat_timer > 25.0:
                pet.bubble.show(random.choice(idle_quotes), duration=4.0)
                chat_timer = 0.0

        # ---- 定时存档 ----
        if time.time() - last_save_time > 30:
            save_manager.save(pet.affection, pet.hunger, pet.sleep)
            last_save_time = time.time()

        # ---- 渲染 ----
        renderer.clear()
        pet.draw(renderer.big_screen)
        renderer.flip(pet.rect)

    # 退出清理
    save_manager.save(pet.affection, pet.hunger, pet.sleep)
    renderer.quit()
    sys.exit()


if __name__ == "__main__":
    main()