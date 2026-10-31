# core/animation.py
"""
动画模块 —— 帧动画播放器 + 精灵表切割器
==========================================
设计目标：支持逐帧动画，正放/倒放/循环/单次播放，带结束回调。
"""

import pygame


class AnimationPlayer:
    """
    逐帧动画播放器。

    用法：
        anim = AnimationPlayer(frames, fps=8, loop=True)
        anim.update(dt)              # dt 单位：秒
        screen.blit(anim.current_frame, pos)

    特性：
        - 自动循环 / 单次播放
        - 播放结束回调 on_finish
        - 可动态换帧（set_frames）
    """
    def __init__(self, frames, fps=8, loop=True, on_finish=None):
        assert len(frames) > 0, "动画至少需要一帧"
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.on_finish = on_finish

        self._timer = 0.0
        self._index = 0
        self.finished = False

    def update(self, dt):
        if self.finished or self.fps <= 0:
            return
        self._timer += dt
        frame_duration = 1.0 / self.fps
        while self._timer >= frame_duration:
            self._timer -= frame_duration
            self._index += 1
            if self._index >= len(self.frames):
                if self.loop:
                    self._index = 0
                else:
                    self._index = len(self.frames) - 1
                    self.finished = True
                    if self.on_finish:
                        self.on_finish()
                    break

    @property
    def current_frame(self):
        return self.frames[self._index]

    def set_frames(self, frames, fps=None, loop=None):
        """运行时换动画（比如 idle → walk）"""
        assert len(frames) > 0
        self.frames = frames
        if fps is not None:
            self.fps = fps
        if loop is not None:
            self.loop = loop
        self._timer = 0.0
        self._index = 0
        self.finished = False

    def reset(self):
        self._timer = 0.0
        self._index = 0
        self.finished = False


class SpriteSheet:
    """
    精灵表切割器（为将来接真实素材预留）。

    假设精灵表是"横向一排帧"或"矩阵排列"：
        sheet = SpriteSheet("assets/pet/idle.png", frame_w=64, frame_h=64, cols=4, rows=1)
        frames = sheet.slice_all()   # → [surf1, surf2, surf3, surf4]
    """
    def __init__(self, path, frame_w, frame_h, cols, rows):
        self.sheet = pygame.image.load(path).convert_alpha()
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.cols = cols
        self.rows = rows

    def slice_all(self):
        frames = []
        for r in range(self.rows):
            for c in range(self.cols):
                rect = pygame.Rect(
                    c * self.frame_w,
                    r * self.frame_h,
                    self.frame_w,
                    self.frame_h,
                )
                frame = self.sheet.subsurface(rect).copy()
                frames.append(frame)
        return frames

    def slice_row(self, row):
        """只切某一行（适合一张图里有 idle 行、walk 行……）"""
        frames = []
        for c in range(self.cols):
            rect = pygame.Rect(
                c * self.frame_w,
                row * self.frame_h,
                self.frame_w,
                self.frame_h,
            )
            frames.append(self.sheet.subsurface(rect).copy())
        return frames