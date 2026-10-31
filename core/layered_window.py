# core/layered_window.py
"""
Win32 分层窗口（Layered Window）
=====================================
用 UpdateLayeredWindow 实现：
    - 逐像素 Alpha 透明（真透明，无锯齿）
    - 点击穿透（点非宠物区域，事件穿透到桌面）
    - 无边框、无任务栏图标、可置顶

依赖：pip install pywin32
平台：Windows 10 / 11（已在 Win11 验证）
"""

import ctypes
import ctypes.wintypes
import pygame
import win32api
import win32con
import win32gui
import win32ui
import win32process


# ---------- 常量 ----------
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008
WS_EX_NOACTIVATE = 0x08000000

ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01


class LayeredWindow:
    """
    分层窗口封装。
    用法：
        win = LayeredWindow(width, height)
        win.show()
        # 每一帧：
        win.render(pygame_surface)   # 传入带 alpha 的 Surface
        # 退出：
        win.destroy()
    """

    def __init__(self, width, height, title="Project Sprite",
                 topmost=True, show_in_taskbar=False):
        self.width = width
        self.height = height
        self.title = title
        self.topmost = topmost
        self.show_in_taskbar = show_in_taskbar
        self.hwnd = None
        self._hinstance = win32api.GetModuleHandle(None)

        self._register_class()
        self._create_window()
        self._init_drawing()

    # ---------- 窗口类注册 ----------
    def _register_class(self):
        wc = win32gui.WNDCLASS()
        wc.hInstance = self._hinstance
        wc.lpszClassName = "ProjectSpriteLayeredWindow"
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = 0
        wc.lpfnWndProc = self._wnd_proc
        try:
            win32gui.RegisterClass(wc)
        except win32gui.error:
            # 已注册过就忽略
            pass

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        # 基本消息处理，退出交给 Python 主循环判断
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    # ---------- 创建窗口 ----------
    def _create_window(self):
        ex_style = WS_EX_LAYERED | WS_EX_NOACTIVATE
        if self.topmost:
            ex_style |= WS_EX_TOPMOST
        if not self.show_in_taskbar:
            ex_style |= WS_EX_TOOLWINDOW

        style = win32con.WS_POPUP

        self.hwnd = win32gui.CreateWindowEx(
            ex_style,
            "ProjectSpriteLayeredWindow",
            self.title,
            style,
            0, 0, self.width, self.height,
            0, 0, self._hinstance, None,
        )

        # 设置窗口位置到屏幕上（默认左上角，宠物自己的坐标在渲染层处理）
        win32gui.SetWindowPos(
            self.hwnd, win32con.HWND_TOPMOST if self.topmost else win32con.HWND_NOTOPMOST,
            0, 0, self.width, self.height,
            win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE,
        )

    # ---------- 绘制准备 ----------
    def _init_drawing(self):
        # 屏幕 DC
        self._screen_dc = win32gui.GetDC(0)
        # 内存 DC
        self._mem_dc = win32ui.CreateDCFromHandle(self._screen_dc)
        self._buffer_dc = self._mem_dc.CreateCompatibleDC()
        # 兼容位图
        self._bitmap = win32ui.CreateBitmap()
        self._bitmap.CreateCompatibleBitmap(self._mem_dc, self.width, self.height)
        self._buffer_dc.SelectObject(self._bitmap)

    # ---------- 对外接口 ----------
    def show(self):
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)

    def set_click_through(self, enable):
        """开 / 关点击穿透"""
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        if enable:
            ex_style |= WS_EX_TRANSPARENT
        else:
            ex_style &= ~WS_EX_TRANSPARENT

        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style)

        # 【核心修复】强制刷新窗口框架，让穿透样式立刻生效，不留延迟
        win32gui.SetWindowPos(
            self.hwnd, 0, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
        )

    def set_position(self, x, y):
        """移动窗口（宠物走到哪，窗口跟到哪）—— 如果全屏方案不需要"""
        win32gui.SetWindowPos(
            self.hwnd, 0, x, y, 0, 0,
            win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER,
        )

    def render(self, pygame_surface, x, y):
        """把局部 Surface 贴到分层窗口，并动态更新窗口位置"""
        # 1. 获取 BGRA 字节流（不翻转）
        data = pygame.image.tostring(pygame_surface, "BGRA")

        # 2. Win32 预乘 Alpha 处理（极速消除白边）
        import numpy as np
        arr = np.frombuffer(data, dtype=np.uint8).reshape((self.height, self.width, 4)).astype(np.float32)

        b, g, r, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
        a_factor = a / 255.0
        arr[..., 0] = b * a_factor
        arr[..., 1] = g * a_factor
        arr[..., 2] = r * a_factor

        data = arr.astype(np.uint8).tobytes()

        # 4. 写入 GDI 内存
        gdi32 = ctypes.windll.gdi32
        h_bitmap = self._bitmap.GetHandle()
        gdi32.SetBitmapBits(h_bitmap, len(data), data)

        blend = (AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)

        # 5. 更新窗口
        try:
            win32gui.UpdateLayeredWindow(
                self.hwnd,
                self._screen_dc,
                (x, y),
                (self.width, self.height),
                self._buffer_dc.GetSafeHdc(),
                (0, 0),
                0,
                blend,
                ULW_ALPHA,
            )
        except Exception as e:
            print(f"[LayeredWindow] UpdateLayeredWindow 失败: {e}")

    def destroy(self):
        try:
            win32gui.DestroyWindow(self.hwnd)
        except Exception:
            pass
        try:
            self._buffer_dc.DeleteDC()
            self._mem_dc.DeleteDC()
            win32gui.ReleaseDC(0, self._screen_dc)
        except Exception:
            pass


# ---------- 鼠标查询辅助函数 ----------
def get_mouse_pos():
    """获取鼠标在屏幕上的绝对坐标"""
    return win32api.GetCursorPos()


def is_window_under_mouse(hwnd):
    """判断当前鼠标是否在某窗口上（用于点击穿透切换）"""
    try:
        pt = get_mouse_pos()
        h = win32gui.WindowFromPoint(pt)
        return h == hwnd
    except Exception:
        return False