# config.py
"""全局配置 —— 第二阶段：动画 / 状态机 / 物理"""
from operator import truediv

# ---- 窗口 / 渲染 ----
TRANSPARENT_COLOR = (255, 0, 255)
WINDOW_FPS = 60
DEBUG_MODE =False     # True和False 时显示或关闭状态文字、碰撞框、FPS

# ---- 物理 ----
GRAVITY = 0.8
MAX_FALL_SPEED = 20
GROUND_OFFSET = 0

# ---- 宠物 ----
PET_START_X = 800
PET_START_Y = 300
PET_SCALE = 1.0

# ---- 动画帧率 ----
IDLE_FPS = 4               # 待机：慢呼吸
WALK_FPS = 8               # 走路：快节奏
SLEEP_FPS = 2              # 睡觉：极慢
DRAG_FPS = 10              # 被拖拽：抖动

# ---- 状态机 ----
# 各状态"持续多久后可能切换"（秒），到点后按概率选择下一个状态
STATE_MIN_DURATION = {
    "idle": 2.0,
    "walk": 3.0,
    "sleep": 8.0,
}
# 每个状态结束后，切换到各状态的概率权重
STATE_TRANSITION_WEIGHTS = {
    "idle":  {"idle": 0.3, "walk": 0.6, "sleep": 0.1},
    "walk":  {"idle": 0.6, "walk": 0.3, "sleep": 0.1},
    "sleep": {"idle": 0.9, "walk": 0.1, "sleep": 0.0},
}

# ---- 漫步 ----
WALK_SPEED = 80            # 像素/秒
WALK_DIRECTION_CHANGE_MIN = 2.0   # 最少持续多久才可能换向
WALK_DIRECTION_CHANGE_MAX = 5.0

# ---- 拖拽 ----
DRAG_RELEASE_JUMP = True   # 松手时给个小上抛，制造"落地"感
DRAG_RELEASE_JUMP_VY = -8  # 上抛初速度

# ---- Win32 分层窗口（第三阶段）----
# 窗口是否置顶（桌宠一般 True）
WINDOW_TOPMOST = True
# 是否在任务栏显示（桌宠一般 False）
WINDOW_SHOW_IN_TASKBAR = False
# 是否允许点击穿透（True = 点宠物以外区域穿透到桌面）
WINDOW_CLICK_THROUGH = True

# ---- 桌面漫游模式 ----
ENABLE_GRAVITY = False     # 关闭重力（True 为一直掉到桌底，False 为全屏漫游）
ROAM_SPEED = 100           # 漫游速度（像素/秒）
ROAM_DIR_CHANGE_MIN = 1.5  # 最少多久换一次方向（秒）
ROAM_DIR_CHANGE_MAX = 4.0  # 最多多久换一次方向（秒）