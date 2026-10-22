# -*- coding: utf-8 -*-
# ============================================================
#  main_logic.py —— 外置逻辑文件（以后加功能、改规则只改这一个文件）
# ============================================================
#  说明：
#   1. 这个文件和 main.exe 放在同一目录，改完保存，重启 exe 即生效，不用重新打包。
#   2. 本文件【不要 import 任何第三方库】（不要写 import PyQt5 / import os 等），
#      图片、窗口、键鼠接收都由 main.exe 负责，这里只决定“当前显示哪一组哪一帧”。
#   3. 下面“固定接口”的方法名不要删、不要改名，否则 exe 会报错；
#      方法内部逻辑、参数、新增变量都可以自由改。
# ============================================================


class PetLogic:
    # --------------------------------------------------------
    # 【可自由修改】可调参数（改这里就行，不用动 main.exe）
    # --------------------------------------------------------
    BASE_SIZE = 200          # 默认显示边长（像素）
    MAX_TYPE_FRAME = 4       # 普通按键打字动画总帧数
    MAX_SWITCH_FRAME = 4     # Shift 切换过渡总帧数
    TYPE_FRAME_MS = 90       # 打字动画每帧间隔（毫秒，越大越慢）
    SWITCH_FRAME_MS = 120    # 切换过渡每帧间隔（毫秒）
    WALK_FRAME_MS = 180      # 走路每帧间隔（毫秒）
    WALK_SPEED = 4           # 左右游走速度（像素/帧）
    IDLE_TO_WALK_MS = 60000  # 闲置多久自动游走（毫秒，60000=60秒）

    # 状态常量（固定接口内部使用，一般不用改）
    ST_IDLE = "idle"
    ST_TYPING = "typing"
    ST_SWITCHING = "switching"
    ST_WALKING = "walking"

    MD_BEAST = "beast"
    MD_GIRL = "girl"

    def __init__(self):
        # ===== 当前状态 =====
        self.mode = self.MD_BEAST          # 当前形态：beast 兽 / girl 少女
        self.state = self.ST_IDLE          # 当前状态
        self.frame_index = 0

        # ===== 尺寸（由 main.exe 滚轮调用 set_size 修改）=====
        self.pet_w = self.BASE_SIZE
        self.pet_h = self.BASE_SIZE

    # --------------------------------------------------------
    # 固定接口（main.exe 按这些名字调用，请勿删除/改名）
    # --------------------------------------------------------
    def set_size(self, w, h):
        """滚轮缩放：main.exe 把新宽高传进来。"""
        self.pet_w = max(60, int(w))
        self.pet_h = max(60, int(h))

    def on_key_press(self):
        """普通按键：从头播当前形态整套敲击动画。"""
        if self.state == self.ST_SWITCHING:
            return
        if self.state == self.ST_WALKING:
            self.stop_walk()
        self.state = self.ST_TYPING
        self.frame_index = 0

    def on_shift(self):
        """Shift 键：播放切换过渡特效，播完翻转形态。"""
        if self.state == self.ST_SWITCHING:
            return
        if self.state == self.ST_WALKING:
            self.stop_walk()
        self.state = self.ST_SWITCHING
        self.frame_index = 0

    def advance_frame(self):
        """main.exe 定时器每帧调用一次，在这里推进动画索引、判断状态结束。"""
        self.frame_index += 1

        if self.state == self.ST_TYPING:
            if self.frame_index >= self.MAX_TYPE_FRAME:
                self.state = self.ST_IDLE
                self.frame_index = 0

        elif self.state == self.ST_SWITCHING:
            if self.frame_index >= self.MAX_SWITCH_FRAME:
                # 过渡播完，翻转形态
                self.mode = self.MD_GIRL if self.mode == self.MD_BEAST else self.MD_BEAST
                self.state = self.ST_IDLE
                self.frame_index = 0

        elif self.state == self.ST_WALKING:
            self.frame_index %= 4  # 走路 4 帧循环

    def get_frame_info(self):
        """
        返回当前应显示的图片，格式固定为元组 (分组标识, 帧序号)：
          ("beast_idle", 0)   兽待机
          ("girl_idle", 0)    少女待机
          ("beast_type", n)   兽打字第 n 帧
          ("girl_type", n)    少女打字第 n 帧
          ("switch", n)       切换过渡第 n 帧
          ("girl_walk", n)    少女走路第 n 帧
        main.exe 会按分组从 skin 文件夹取对应图片渲染。
        """
        if self.state == self.ST_SWITCHING:
            return ("switch", min(self.frame_index, self.MAX_SWITCH_FRAME - 1))

        if self.state == self.ST_WALKING:
            return ("girl_walk", self.frame_index)

        if self.state == self.ST_TYPING:
            group = "beast_type" if self.mode == self.MD_BEAST else "girl_type"
            return (group, min(self.frame_index, self.MAX_TYPE_FRAME - 1))

        # 待机
        if self.mode == self.MD_BEAST:
            return ("beast_idle", 0)
        return ("girl_idle", 0)

    def start_walk(self):
        """闲置超时：切少女形态开始游走。"""
        self.mode = self.MD_GIRL
        self.state = self.ST_WALKING
        self.frame_index = 0

    def stop_walk(self):
        """结束游走，回当前形态待机。"""
        self.state = self.ST_IDLE
        self.frame_index = 0

    def is_walking(self):
        """main.exe 据此判断是否需要移动窗口位置。"""
        return self.state == self.ST_WALKING

    def get_config(self):
        """把节奏参数告诉 main.exe，main.exe 据此设定定时器。"""
        return {
            "type_frame_ms": self.TYPE_FRAME_MS,
            "switch_frame_ms": self.SWITCH_FRAME_MS,
            "walk_frame_ms": self.WALK_FRAME_MS,
            "walk_speed": self.WALK_SPEED,
            "idle_to_walk_ms": self.IDLE_TO_WALK_MS,
            "base_size": self.BASE_SIZE,
        }
