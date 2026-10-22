import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import QPoint
import importlib.util

# 加载外部 main_logic.py
def load_logic():
    base_dir = os.path.dirname(sys.executable) if hasattr(sys, 'frozen') else os.path.dirname(__file__)
    logic_path = os.path.join(base_dir, "main_logic.py")
    if not os.path.exists(logic_path):
        raise Exception("找不到外部 main_logic.py，请和exe放在同一目录！")
    spec = importlib.util.spec_from_file_location("main_logic", logic_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PetLogic()

class PetWindow(QWidget):
    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        self.base_dir = os.path.dirname(sys.executable) if hasattr(sys, 'frozen') else os.path.dirname(__file__)
        self.skin_dir = os.path.join(self.base_dir, "skin")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.img_label = None
        self.resize(self.logic.pet_w, self.logic.pet_h)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(120)
        self.drag_pos = QPoint()

    def get_image(self, name, idx):
        path = os.path.join(self.skin_dir, f"{name}_{idx}.png")
        if not os.path.exists(path):
            return None
        pix = QPixmap(path)
        pix = pix.scaled(self.logic.pet_w, self.logic.pet_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pix

    def update_frame(self):
        group, frame = self.logic.get_frame_info()
        pix = self.get_image(group, frame)
        if pix:
            self.setPixmap(pix)

    def setPixmap(self, pix):
        if self.img_label is None:
            from PyQt5.QtWidgets import QLabel
            self.img_label = QLabel(self)
            self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setPixmap(pix)
        self.img_label.resize(self.size())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.close()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        step = 20
        if delta > 0:
            w = self.width() + step
            h = self.height() + step
        else:
            w = max(80, self.width() - step)
            h = max(80, self.height() - step)
        self.resize(w, h)
        self.logic.set_size(w, h)

    def keyPressEvent(self, event):
        self.logic.on_key_press()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        pet_logic = load_logic()
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "加载逻辑失败", str(e))
        sys.exit(1)
    win = PetWindow(pet_logic)
    win.show()
    sys.exit(app.exec_())
