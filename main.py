# -*- 编码：utf-8 -*-
"" "" ""
main.py —— 固定窗口渲染层（打包成 exe 后不再改动）

逻辑规则、动画节奏、形态切换全部在外部 main_logic.py 中定义。
"" "" ""
  2. 动态加载同级外部 main_logic.py（逻辑可随时修改，无需重新打包）
  3. 全局键盘监听、左键拖动、右键关闭、滚轮缩放、闲置游走窗口移动
  4. 加载失败 / 缺素材 / 缺接口时弹窗提示具体原因，不静默空白

逻辑规则、动画节奏、形态切换全部在外部 main_logic.py 中定义。
"""

导入系统 sys
导入 os os
导入导入导入库.工具 importlib.util
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox
from PyQt5.QtGui import QPixmap, QMouseEvent PyQt5.QtGui import QPixmap, QMouseEvent
from PyQt5.QtCore import Qt, QTimer, pyqtSignal PyQt5.QtCore import Qt, QTimer, pyqtSignal
从 pynput 导入 keyboard pynput import keyboard


# 固定接口：外部 main_logic.py 必须提供这些方法
REQUIRED_METHODS = [[
    "set_size", "on_key_press", "on_shift", "advance_frame","set_size", "on_key_press", "on_shift", "advance_frame",
    "获取帧信息", "开始行走", "停止行走", "是否行走", "获取配置","get_frame_info", "start_walk", "stop_walk", "is_walking", "get_config",
]


def app_dir(): app_dir():
    “exe 或脚本所在目录（打包后以 exe 目录为基准读取外部文件）。”"""exe 或脚本所在目录（打包后以 exe 目录为基准读取外部文件）。"""
    如果 sys 模块中存在 "frozen" 属性，则为 True：if getattr(sys, "frozen", False):
        返回 os.path.dirname(os.path.abspath(sys.executable))return os.path.dirname(os.path.abspath(sys.executable))
    返回 os.path.dirname(os.path.abspath(__file__))return os.path.dirname(os.path.abspath(__file__))


def 加载外部逻辑(): load_external_logic():
    动态加载同级 main_logic.py，失败时弹窗并退出。"""动态加载同级 main_logic.py，失败时弹窗并退出。"""
    logic_path = os.path.join(app_dir(), "main_logic.py")path.join(app_dir(), "main_logic.py")
    如果逻辑路径不存在：if not os.path.exists(logic_path):
        QMessageBox.critical(critical(
            无，"缺少逻辑文件"，None, "缺少逻辑文件",
            f"未找到 main_logic.py：\n{logic_path}\n\n请把 main_logic.py 放到 exe 同一目录。"
        )
        sys.exit(1)
    try:
        spec = importlib.util.spec_from_file_location("external_main_logic", logic_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, "PetLogic"):
            QMessageBox.critical(
                None, "main_logic.py 结构错误",
                "main_logic.py 中缺少 class PetLogic。\n请保留固定接口，只修改内部逻辑。"
            )
            sys.exit(1)
        return module.PetLogic
    except Exception as e:
        QMessageBox.critical(
            None, "main_logic.py 加载失败",
            f"{type(e).__name__}: {e}\n\n请检查 main_logic.py 语法，"
            "不要在里面 import PyQt5 / os 等第三方或系统库。"
        )
        sys.exit(1)


def load_skin(skin_dir):
    """把 skin 图片按分组加载到内存，返回分组字典。"""
    data = {
        "beast_idle": None, "beast_type": [],
        "girl_idle": None, "girl_type": [],
        "girl_walk": [], "switch": [],
    }
    if not os.path.isdir(skin_dir):
        return data
    for fname in sorted(os.listdir(skin_dir)):
        if not fname.lower().endswith(".png"):
            continue
        pm = QPixmap(os.path.join(skin_dir, fname))
        if pm.isNull():
            continue
        if fname == "beast_idle.png":
            data["beast_idle"] = pm
        elif fname.startswith("beast_type_"):
            data["beast_type"].append(pm)
        elif fname == "girl_idle.png":
            data["girl_idle"] = pm
        elif fname.startswith("girl_type_"):
            data["girl_type"].append(pm)
        elif fname.startswith("girl_walk_"):
            data["girl_walk"].append(pm)
        elif fname.startswith("switch_"):
            data["switch"].append(pm)
    return data


def pick_pixmap(data, tag, idx):
    """按分组标识取图，越界回退到本组第 0 张。"""
    if tag in ("beast_idle", "girl_idle"):
        return data[tag]
    group = data.get(tag)
    if group:
        idx = max(0, min(idx, len(group) - 1))
        return group[idx]
    return None


class DesktopPet(QWidget):
    sig_type = pyqtSignal()
    sig_shift = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 加载外部逻辑
        PetLogic = load_external_logic()
        self.logic = PetLogic()

        # 校验固定接口是否齐全
        missing = [m for m in REQUIRED_METHODS if not callable(getattr(self.logic, m, None))]
        if missing:
            QMessageBox.critical(
                None, "main_logic.py 接口缺失",
                "缺少以下方法：\n" + "\n".join(missing) +
                "\n\n请保留 main_logic.py 中的固定接口方法名。"
            )
            sys.exit(1)

        # 读取逻辑层配置
        cfg = self.logic.get_config() or {}
        self.type_ms = cfg.get("type_frame_ms", 90)
        self.switch_ms = cfg.get("switch_frame_ms", 120)
        self.walk_ms = cfg.get("walk_frame_ms", 180)
        self.walk_speed = cfg.get("walk_speed", 4)
        self.idle_ms = cfg.get("idle_to_walk_ms", 60000)
        self.base_size = cfg.get("base_size", 200)

        # 加载皮肤
        self.skin = load_skin(os.path.join(app_dir(), "skin"))
        if self.skin["beast_idle"] is None or self.skin["girl_idle"] is None:
            QMessageBox.critical(
                None, "素材缺失",
                f"未在以下目录找到完整待机图：\n{os.path.join(app_dir(), 'skin')}\n"
                "请确认 skin 文件夹与 exe 同级，且包含 beast_idle.png、girl_idle.png 等图片。"
            )
            sys.exit(1)

        # 缩放状态
        self.scale = 1.0
        self.logic.set_size(self.base_size, self.base_size)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.resize(self.size())

        self.drag_pos = None
        self._walk_dir = 1

        self.sig_type.connect(self._on_type)
        self.sig_shift.connect(self._on_shift)

        # 动画定时器
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick)
        self.anim_timer.start(self.type_ms)

        # 闲置游走定时器
        self.walk_timer = QTimer(self)
        self.walk_timer.setSingleShot(True)
        self.walk_timer.timeout.connect(self._start_walk)

        self._refresh()
        self._reset_walk_timer()
        self.show()

        # 全局键盘监听
        self.key_listener = keyboard.Listener(on_press=self._on_global_key)
        self.key_listener.daemon = True
        self.key_listener.start()

    # ------------------------------------------------------------------
    # 事件分发（主线程）
    # ------------------------------------------------------------------
    def _on_type(self):
        self.logic.on_key_press()
        self._refresh()
        self._reset_walk_timer()

    def _on_shift(self):
        self.logic.on_shift()
        self._refresh()
        self._reset_walk_timer()

    def _start_walk(self):
        self.logic.start_walk()
        self._refresh()

    def _reset_walk_timer(self):
        self.walk_timer.stop()
        self.walk_timer.start(self.idle_ms)

    # ------------------------------------------------------------------
    # 帧推进 + 渲染
    # ------------------------------------------------------------------
    def _tick(self):
        tag, _ = self.logic.get_frame_info()
        if tag == "switch":
            self.anim_timer.setInterval(self.switch_ms)
        elif tag == "girl_walk":
            self.anim_timer.setInterval(self.walk_ms)
        else:
            self.anim_timer.setInterval(self.type_ms)

        self.logic.advance_frame()

        if self.logic.is_walking():
            self._move_walk()

        self._refresh()

    def _refresh(self):
        tag, idx = self.logic.get_frame_info()
        pm = pick_pixmap(self.skin, tag, idx)
        if pm is None:
            return
        scaled = pm.scaled(
            self.logic.pet_w, self.logic.pet_h,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.label.setPixmap(scaled)
        self.label.resize(scaled.size())
        self.resize(scaled.size())

    def _move_walk(self):
        screen = QApplication.primaryScreen().availableGeometry()
        min_x = screen.left()
        max_x = screen.right() - self.width()
        new_x = self.x() + self.walk_speed * self._walk_dir
        if new_x <= min_x:
            new_x = min_x
            self._walk_dir = 1
        elif new_x >= max_x:
            new_x = max_x
            self._walk_dir = -1
        self.move(new_x, self.y())

    # ------------------------------------------------------------------
    # 全局键盘（子线程，只发信号）
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
            if self.logic.is_walking():
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

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.scale += 0.08 if delta > 0 else -0.08
        self.scale = min(1.4, max(0.3, self.scale))
        self.logic.set_size(self.base_size * self.scale, self.base_size * self.scale)
        self._refresh()
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
