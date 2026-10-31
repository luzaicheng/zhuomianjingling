# assets/placeholder_gen.py
"""
占位素材生成器 —— 没真实图片时，用代码画几何体宠物动画帧
==============================================================
生成四组帧列表：idle / walk / sleep / drag，每组 2~4 帧。
"""

import pygame
import math


def _draw_body(surface, cx, cy, scale=1.0, eyes_open=True, mouth=True,
               tilt=0.0, zzz=False):
    """核心绘制函数：身体 + 眼睛 + 嘴巴"""
    w = int(80 * scale)
    h = int(80 * scale)
    body_rect = pygame.Rect(0, 0, w, h)
    body_rect.center = (cx, cy)

    # 身体（带一点点倾斜）
    body = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(body, (80, 200, 255), (0, 0, w, h), border_radius=int(w * 0.25))
    if tilt:
        body = pygame.transform.rotate(body, tilt)
        body_rect = body.get_rect(center=(cx, cy))

    surface.blit(body, body_rect.topleft)

    # 眼睛
    eye_dx = int(w * 0.22)
    eye_r = int(w * 0.14)
    eye_y = cy - int(h * 0.15)
    if eyes_open:
        pygame.draw.circle(surface, (255, 255, 255), (cx - eye_dx, eye_y), eye_r)
        pygame.draw.circle(surface, (255, 255, 255), (cx + eye_dx, eye_y), eye_r)
        pygame.draw.circle(surface, (20, 20, 20), (cx - eye_dx, eye_y + 2), eye_r // 2)
        pygame.draw.circle(surface, (20, 20, 20), (cx + eye_dx, eye_y + 2), eye_r // 2)
    else:
        # 闭眼：画一条横线
        pygame.draw.line(surface, (20, 20, 20),
                         (cx - eye_dx - eye_r, eye_y),
                         (cx - eye_dx + eye_r, eye_y), 3)
        pygame.draw.line(surface, (20, 20, 20),
                         (cx + eye_dx - eye_r, eye_y),
                         (cx + eye_dx + eye_r, eye_y), 3)

    # 嘴巴
    if mouth:
        pygame.draw.arc(surface, (20, 20, 20),
                        (cx - int(w * 0.2), cy + int(h * 0.1),
                         int(w * 0.4), int(h * 0.25)),
                        3.6, 5.8, 3)

    # Zzz
    if zzz:
        font = pygame.font.SysFont("consolas", 20, bold=True)
        text = font.render("Zzz", True, (100, 100, 255))
        surface.blit(text, (cx + int(w * 0.4), cy - int(h * 0.6)))


def _make_frame(cx, cy, **kwargs):
    surf = pygame.Surface((120, 120), pygame.SRCALPHA)
    _draw_body(surf, 60, 60, **kwargs)
    return surf


def make_idle_frames():
    """待机：呼吸起伏 + 偶尔闭眼"""
    frames = []
    for i in range(4):
        breathing = 0.02 * math.sin(i * math.pi / 2)
        frames.append(_make_frame(60, 60, scale=1.0 + breathing))
    # 眨眼
    frames.append(_make_frame(60, 60, eyes_open=False))
    frames.append(_make_frame(60, 60))
    return frames


def make_walk_frames():
    """走路：身体上下颠 + 倾斜"""
    frames = []
    tilts = [0, -8, 0, 8]
    for t in tilts:
        surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        # 上下颠
        y_offset = abs(t) / 8 * 4
        _draw_body(surf, 60, 60 - y_offset, tilt=t)
        frames.append(surf)
    return frames


def make_sleep_frames():
    """睡觉：闭眼 + Zzz + 微微起伏"""
    frames = []
    for i in range(3):
        breathing = 0.03 * math.sin(i * math.pi / 3)
        frames.append(_make_frame(60, 60, scale=1.0 + breathing,
                                  eyes_open=False, mouth=False, zzz=True))
    return frames


def make_drag_frames():
    """被拖拽：快速抖动"""
    frames = []
    for i in range(4):
        jitter = [0, -2, 0, 2][i]
        frames.append(_make_frame(60 + jitter, 60, eyes_open=True))
    return frames