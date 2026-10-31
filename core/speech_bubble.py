# core/speech_bubble.py
import pygame
import math
import random


class SpeechBubble:
    def __init__(self):
        self.text = ""
        self.timer = 0.0
        self.show_time = 3.0
        self.font = pygame.font.SysFont("fangsong", 24, bold=False)
        self.is_active = False

        # 【新增】6 种精心调配的莫兰迪/马卡龙色系
        self.color_palette = [
            (50, 50, 55),  # 1. 莫兰迪深灰 (百搭)
            (70, 100, 140),  # 2. 雾霾蓝 (呼应宠物)
            (160, 80, 90),  # 3. 豆沙红
            (80, 120, 80),  # 4. 抹茶绿
            (120, 90, 150),  # 5. 香芋紫
            (170, 110, 60)  # 6. 暖秋橘
        ]
        self.current_color = self.color_palette[0]

    def show(self, text, duration=3.0):
        self.text = text
        self.show_time = duration
        self.timer = duration
        self.is_active = True
        # 【新增】每次说话时，随机抽取一种颜色
        self.current_color = random.choice(self.color_palette)

    def update(self, dt):
        if self.is_active:
            self.timer -= dt
            if self.timer <= 0:
                self.is_active = False

    def draw(self, screen, anchor_x, anchor_y):
        if not self.is_active:
            return

        alpha = 255
        if self.timer < 0.5:
            alpha = int(255 * (self.timer / 0.5))

        float_offset = math.sin(self.timer * 5) * 4
        draw_y = anchor_y - 30 + float_offset

        # 渲染彩色字芯
        text_surf = self.font.render(self.text, True, self.current_color)
        text_surf.set_alpha(alpha)

        text_rect = text_surf.get_rect()
        text_x = anchor_x - text_rect.width // 2
        text_y = draw_y

        # 【新增】智能阴影算法：计算颜色的亮度
        r, g, b = self.current_color
        brightness = 0.299 * r + 0.587 * g + 0.114 * b

        # 颜色深 -> 用白阴影；颜色浅 -> 用黑阴影
        if brightness < 128:
            shadow_color = (255, 255, 255)
        else:
            shadow_color = (0, 0, 0)

        shadow_surf = self.font.render(self.text, True, shadow_color)
        shadow_surf.set_alpha(int(alpha * 0.4))  # 保持阴影极淡
        screen.blit(shadow_surf, (text_x + 1, text_y + 1))

        # 纯色字芯盖在上面
        screen.blit(text_surf, (text_x, text_y))