# -*- coding: utf-8 -*-
"""
main_logic.py —— 桌宠逻辑层（素材加载 + 状态机 + 帧推进 + 取图缩放）

状态流转：
  idle ──普通按键──▶ typing ──播完4帧──▶ idle
  idle ──Shift────▶ switching ──播完4帧──▶ idle（同时翻转 beast/girl 形态）
  idle ──闲置60秒─▶ walking（强制切到 girl 形态左右游走）

说明：本文件被 main.py 内置打包，skin 路径由 main.py 以绝对路径传入。
"""

import os
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class PetLogic:
    STATE_IDLE = "idle"
    STATE_TYPING = "typing"
    STATE_SWITCHING = "switching"
    STATE_WALKING = "walking"

    MODE_BEAST = "beast"
    MODE_GIRL = "girl"

    def __init__(self, skin_folder="skin"):
        self.skin_folder = skin_folder

        # ===== 素材 =====
        self.beast_idle = None
        self.beast_type = []
        self.girl_idle = None
        self.girl_type = []
        self.girl_walk = []
        self.switch_frames = []

        # ===== 状态 =====
        self.mode = self.MODE_BEAST
        self.state = self.STATE_IDLE
        self.frame_index = 0

        # ===== 显示尺寸（main.py 滚轮调用 set_size 更新）=====
        self.pet_w = 200
        self.pet_h = 200

        self._load_images()

    # ------------------------------------------------------------------
    # 素材加载
    # ------------------------------------------------------------------
    def _load_images(self):
        if not os.path.isdir(self.skin_folder):
            return
        for fname in sorted(os.listdir(self.skin_folder)):
            if not fname.lower().endswith(".png"):
                continue
            fpath = os.path.join(self.skin_folder, fname)
            pm = QPixmap(fpath)
            if pm.isNull():
                continue
            if fname == "beast_idle.png":
                self.beast_idle = pm
            elif fname.startswith("beast_type_"):
                self.beast_type.append(pm)
            elif fname == "girl_idle.png":
                self.girl_idle = pm
            elif fname.startswith("girl_type_"):
                self.girl_type.append(pm)
            elif fname.startswith("girl_walk_"):
                self.girl_walk.append(pm)
            elif fname.startswith("switch_"):
                self.switch_frames.append(pm)

    def is_ready(self):
        """两套待机图都加载成功才算素材齐全，否则 main.py 弹窗提示。"""
        return self.beast_idle is not None and self.girl_idle is not None

    def missing_materials(self):
        """返回缺失的关键文件名清单，供 main.py 弹窗展示。"""
        need = ["beast_idle.png", "girl_idle.png"]
        for i in (1, 2, 3, 4):
            need.append(f"beast_type_{i:02d}.png")
            need.append(f"girl_type_{i:02d}.png")
        existing = set(os.listdir(self.skin_folder)) if os.path.isdir(self.skin_folder) else set()
        return [n for n in need if n not in existing]

    # ------------------------------------------------------------------
    # 尺寸
    # ------------------------------------------------------------------
    def set_size(self, w, h):
        self.pet_w = max(60, int(w))
        self.pet_h = max(60, int(h))

    # ------------------------------------------------------------------
    # 事件入口（main.py 调用）
    # ------------------------------------------------------------------
    def on_typing(self):
        """普通按键：从头播当前形态整套敲击帧。"""
        if self.state == self.STATE_SWITCHING:
            return
        if self.state == self.STATE_WALKING:
            self.stop_walk()
        self.state = self.STATE_TYPING
        self.frame_index = 0

    def on_shift(self):
        """Shift：播放过渡特效，播完翻转形态。"""
        if self.state == self.STATE_SWITCHING:
            return
        if self.state == self.STATE_WALKING:
            self.stop_walk()
        self.state = self.STATE_SWITCHING
        self.frame_index = 0

    def start_walk(self):
        self.mode = self.MODE_GIRL
        self.state = self.STATE_WALKING
        self.frame_index = 0

    def stop_walk(self):
        self.state = self.STATE_IDLE
        self.frame_index = 0

    # ------------------------------------------------------------------
    # 定时器每帧推进（只改状态）
    # ------------------------------------------------------------------
    def advance_frame(self):
        self.frame_index += 1

        if self.state == self.STATE_TYPING:
            frames = self._current_type_frames()
            if frames and self.frame_index >= len(frames):
                self.state = self.STATE_IDLE
                self.frame_index = 0

        elif self.state == self.STATE_SWITCHING:
            if self.switch_frames and self.frame_index >= len(self.switch_frames):
                self.mode = self.MODE_GIRL if self.mode == self.MODE_BEAST else self.MODE_BEAST
                self.state = self.STATE_IDLE
                self.frame_index = 0

        elif self.state == self.STATE_WALKING and self.girl_walk:
            self.frame_index %= len(self.girl_walk)

    # ------------------------------------------------------------------
    # 对外取图（纯读取，不修改状态；统一强制缩放到 pet_w/pet_h）
    # ------------------------------------------------------------------
    def get_pixmap(self):
        if self.state == self.STATE_SWITCHING and self.switch_frames:
            idx = min(self.frame_index, len(self.switch_frames) - 1)
            return self._scale(self.switch_frames[idx])

        if self.state == self.STATE_WALKING and self.girl_walk:
            return self._scale(self.girl_walk[self.frame_index % len(self.girl_walk)])

        if self.state == self.STATE_TYPING:
            frames = self._current_type_frames()
            if frames:
                idx = min(self.frame_index, len(frames) - 1)
                return self._scale(frames[idx])

        idle = self.beast_idle if self.mode == self.MODE_BEAST else self.girl_idle
        return self._scale(idle)

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    def _current_type_frames(self):
        return self.beast_type if self.mode == self.MODE_BEAST else self.girl_type

    def _scale(self, pm):
        if pm is None or pm.isNull():
            return None
        return pm.scaled(
            self.pet_w, self.pet_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
