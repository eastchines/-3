# -*- coding: utf-8 -*-
"""
main.py —— 桌宠界面层

功能：
  1. 透明无边框置顶窗口，图片外置在 exe 同级 skin 文件夹，可随时替换
  2. 全局键盘监听：普通按键播完整套打字动画；Shift 播过渡特效后翻转形态
  3. 左键拖动、右键关闭、鼠标滚轮比例缩放
  4. 闲置 60 秒自动切少女形态左右游走；按键/拖动立即打断
  5. 状态机与素材逻辑在 main_logic.py
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox
from PyQt5.QtGui import QPixmap, QMouseEvent
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from pynput import keyboard

from main_logic import PetLogic


# ==================== 可调参数 ====================
TYPE_FRAME_MS = 90        # 打字动画每帧间隔
SWITCH_FRAME_MS = 120     # 切换过渡每帧间隔
WALK_FRAME_MS = 180       # 走路每帧间隔
WALK_SPEED = 4            # 游走速度（像素/帧）
IDLE_TO_WALK_MS = 60000   # 闲置多久开始游走（毫秒）
BASE_SIZE = 200           # 基础尺寸（scale=1 时的边长）
SCALE_MIN = 0.3
SCALE_MAX = 1.4
SCALE_STEP = 0.08         # 滚轮每次缩放比例步进
# =================================================


def base_dir():
    """exe 或脚本所在目录（打包后图片从 exe 同级 skin 读取）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


class DesktopPet(QWidget):
    sig_type = pyqtSignal()
    sig_shift = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 绝对路径定位 skin，打包后也能读到外部图片
        skin_path = os.path.join(base_dir(), "skin")
        self.logic = PetLogic(skin_path)

        # 素材缺失直接弹窗提示，避免空白静默
        if not self.logic.is_ready():
            missing = self.logic.missing_materials()
            detail = "\n".join(missing) if missing else "skin 文件夹不存在或图片无法读取"
            QMessageBox.critical(
                None, "素材缺失",
                f"未在以下目录找到完整素材：\n{skin_path}\n\n缺失图片：\n{detail}"
            )
            sys.exit(1)

        self.scale = 1.0
        self.logic.set_size(BASE_SIZE, BASE_SIZE)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.resize(self.size())

        self.drag_pos = None
        self._walk_dir = 1

        self.sig_type.connect(self._on_type)
        self.sig_shift.connect(self._on_shift)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick)
        self.anim_timer.start(TYPE_FRAME_MS)

        self.walk_timer = QTimer(self)
        self.walk_timer.setSingleShot(True)
        self.walk_timer.timeout.connect(self._start_walk)

        self._refresh_image()
        self._reset_walk_timer()
        self.show()

        self.key_listener = keyboard.Listener(on_press=self._on_global_key)
        self.key_listener.daemon = True
        self.key_listener.start()

    # ------------------------------------------------------------------
    # 事件分发（主线程）
    # ------------------------------------------------------------------
    def _on_type(self):
        self.logic.on_typing()
        self._refresh_image()
        self._reset_walk_timer()

    def _on_shift(self):
        self.logic.on_shift()
        self._refresh_image()
        self._reset_walk_timer()

    def _start_walk(self):
        self.logic.start_walk()
        self._refresh_image()

    def _reset_walk_timer(self):
        self.walk_timer.stop()
        self.walk_timer.start(IDLE_TO_WALK_MS)

    # ------------------------------------------------------------------
    # 帧推进 + 刷新
    # ------------------------------------------------------------------
    def _tick(self):
        if self.logic.state == PetLogic.STATE_SWITCHING:
            self.anim_timer.setInterval(SWITCH_FRAME_MS)
        elif self.logic.state == PetLogic.STATE_WALKING:
            self.anim_timer.setInterval(WALK_FRAME_MS)
        else:
            self.anim_timer.setInterval(TYPE_FRAME_MS)

        self.logic.advance_frame()

        if self.logic.state == PetLogic.STATE_WALKING:
            self._move_walk()

        self._refresh_image()

    def _refresh_image(self):
        pm = self.logic.get_pixmap()
        if pm is not None:
            self.label.setPixmap(pm)
            self.label.resize(pm.size())
            self.resize(pm.size())

    def _move_walk(self):
        screen = QApplication.primaryScreen().availableGeometry()
        min_x = screen.left()
        max_x = screen.right() - self.width()
        new_x = self.x() + WALK_SPEED * self._walk_dir
        if new_x <= min_x:
            new_x = min_x
            self._walk_dir = 1
        elif new_x >= max_x:
            new_x = max_x
            self._walk_dir = -1
        self.move(new_x, self.y())

    # ------------------------------------------------------------------
    # 全局键盘（pynput 子线程，只发信号）
    # ------------------------------------------------------------------
    def _on_global_key(self, key):
        try:
            if key == keyboard.Key.shift or key == keyboard.Key.shift_r:
                self.sig_shift.emit()
            else:
                self.sig_type.emit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 鼠标事件
    # ------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            if self.logic.state == PetLogic.STATE_WALKING:
                self.logic.stop_walk()
            self._reset_walk_timer()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.close()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = None
            self._reset_walk_timer()

    # 滚轮比例缩放
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale += SCALE_STEP
        else:
            self.scale -= SCALE_STEP
        self.scale = min(SCALE_MAX, max(SCALE_MIN, self.scale))
        self.logic.set_size(BASE_SIZE * self.scale, BASE_SIZE * self.scale)
        self._refresh_image()
        event.accept()

    def closeEvent(self, event):
        try:
            self.key_listener.stop()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    sys.exit(app.exec_())

