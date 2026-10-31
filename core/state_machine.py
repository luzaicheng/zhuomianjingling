# core/state_machine.py
"""
通用有限状态机（FSM）
========================
设计目标：状态 + 转移条件 + 进入/退出钩子，宠物 AI 用它驱动。
"""

import random


class State:
    """
    一个状态的抽象。
    子类可重写 on_enter / on_exit / update。
    """
    def __init__(self, name):
        self.name = name
        self.duration = 0.0   # 该状态已持续多久

    def on_enter(self, pet):
        self.duration = 0.0
        print(f"[FSM] 进入状态: {self.name}")

    def on_exit(self, pet):
        pass

    def update(self, pet, dt):
        self.duration += dt


class StateMachine:
    """
    极简 FSM。
    用法：
        fsm = StateMachine()
        fsm.add_state(IdleState())
        fsm.add_state(WalkState())
        fsm.set_initial("idle")
        fsm.update(pet, dt)
        fsm.change("walk")
    """
    def __init__(self):
        self.states = {}
        self.current = None

    def add_state(self, state):
        self.states[state.name] = state

    def set_initial(self, name):
        self.current = self.states[name]
        self.current.on_enter(None)   # pet 在第一次 update 时传

    def change(self, name, pet=None):
        if name not in self.states:
            print(f"[FSM] 未知状态: {name}")
            return
        if self.current:
            self.current.on_exit(pet)
        self.current = self.states[name]
        self.current.on_enter(pet)

    def update(self, pet, dt):
        if self.current:
            self.current.update(pet, dt)