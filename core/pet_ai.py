# core/pet_ai.py
"""
宠物大脑 —— 具体状态 + 转移逻辑
==================================
包含四个状态：
    IdleState   : 慢呼吸、偶尔走神
    WalkState   : 随机漫步，自动换向
    SleepState  : 睡觉，冒 Zzz（第三阶段接气泡）
    DragState   : 被拖拽时抖动
"""

import random
import pygame

from core.state_machine import State, StateMachine
from core.animation import AnimationPlayer
import config


# ---------- 状态定义 ----------

class IdleState(State):
    def __init__(self):
        super().__init__("idle")

    def on_enter(self, pet):
        super().on_enter(pet)
        if pet:
            pet.set_animation("idle", config.IDLE_FPS, loop=True)
            pet.vx = 0
            pet.vy = 0   #防止切换到发呆状态时还在飘

    def update(self, pet, dt):
        super().update(pet, dt)
        if self.duration >= config.STATE_MIN_DURATION["idle"]:
            self._maybe_transition(pet)

    def _maybe_transition(self, pet):
        weights = config.STATE_TRANSITION_WEIGHTS["idle"]
        choice = random.choices(
            list(weights.keys()), weights=list(weights.values())
        )[0]
        pet.fsm.change(choice, pet)


class WalkState(State):
    def __init__(self):
        super().__init__("walk")
        self._dir_x = 1
        self._dir_y = 1
        self._next_change = 0.0

    def on_enter(self, pet):
        super().on_enter(pet)
        if pet:
            pet.set_animation("walk", config.WALK_FPS, loop=True)

            # 【新增】如果宠物在屏幕边缘，强制让它往屏幕中心走
            margin = 150
            if pet.rect.centerx < margin:
                self._dir_x = 1
            elif pet.rect.centerx > pet.screen_w - margin:
                self._dir_x = -1
            else:
                self._dir_x = random.choice([-1, 1])

            if pet.rect.centery < margin:
                self._dir_y = 1
            elif pet.rect.centery > pet.screen_h - margin:
                self._dir_y = -1
            else:
                self._dir_y = random.choice([-1, 1])

            pet.facing = self._dir_x
            # 设置比较短的换向时间（0.5 ~ 1.5秒），让它频繁转弯
            self._next_change = random.uniform(0.5, 1.5)

    def update(self, pet, dt):
        super().update(self, dt)

        # 赋予 X 和 Y 轴速度
        pet.vx = config.ROAM_SPEED * self._dir_x
        pet.vy = config.ROAM_SPEED * self._dir_y

        self._next_change -= dt
        if self._next_change <= 0:
            # 【修改】每次改变方向时，避开边缘区域
            margin = 100
            if pet.rect.centerx < margin:
                self._dir_x = 1
            elif pet.rect.centerx > pet.screen_w - margin:
                self._dir_x = -1
            else:
                self._dir_x = random.choice([-1, 1])

            if pet.rect.centery < margin:
                self._dir_y = 1
            elif pet.rect.centery > pet.screen_h - margin:
                self._dir_y = -1
            else:
                self._dir_y = random.choice([-1, 1])

            pet.facing = self._dir_x
            # 每 0.5 ~ 1.5 秒换一次方向，拒绝走直线
            self._next_change = random.uniform(0.5, 1.5)

        # 撞墙反弹（X 轴）
        if pet.rect.left <= 0:
            self._dir_x = 1
            pet.facing = 1
        elif pet.rect.right >= pet.screen_w:
            self._dir_x = -1
            pet.facing = -1

        # 撞天花板/地板反弹（Y 轴）
        if pet.rect.top <= 0:
            self._dir_y = 1
        elif pet.rect.bottom >= pet.screen_h:
            self._dir_y = -1

        # 持续时间到了可能切换状态
        if self.duration >= config.STATE_MIN_DURATION["walk"]:
            self._maybe_transition(pet)

    def _maybe_transition(self, pet):
        # 避免在边缘频繁切换状态导致抽搐
        if (pet.rect.left <= 0 or pet.rect.right >= pet.screen_w or
                pet.rect.top <= 0 or pet.rect.bottom >= pet.screen_h):
            return
        weights = config.STATE_TRANSITION_WEIGHTS["walk"]
        choice = random.choices(
            list(weights.keys()), weights=list(weights.values())
        )[0]
        pet.fsm.change(choice, pet)


class SleepState(State):
    def __init__(self):
        super().__init__("sleep")

    def on_enter(self, pet):
        super().on_enter(pet)
        if pet:
            pet.set_animation("sleep", config.SLEEP_FPS, loop=True)
            pet.vx = 0

    def update(self, pet, dt):
        super().update(self, dt) if False else State.update(self, pet, dt)
        if self.duration >= config.STATE_MIN_DURATION["sleep"]:
            weights = config.STATE_TRANSITION_WEIGHTS["sleep"]
            choice = random.choices(
                list(weights.keys()), weights=list(weights.values())
            )[0]
            pet.fsm.change(choice, pet)


class DragState(State):
    def __init__(self):
        super().__init__("drag")

    def on_enter(self, pet):
        super().on_enter(pet)
        if pet:
            pet.set_animation("drag", config.DRAG_FPS, loop=True)

    def update(self, pet, dt):
        State.update(self, pet, dt)
        # 拖拽状态不自动转移，松手由外部触发回 idle


# ---------- 工厂 ----------

def build_pet_fsm():
    fsm = StateMachine()
    fsm.add_state(IdleState())
    fsm.add_state(WalkState())
    fsm.add_state(SleepState())
    fsm.add_state(DragState())
    fsm.set_initial("idle")
    return fsm