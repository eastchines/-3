import sys
import os
import tkinter as tk
from tkinter import messagebox

# 动态加载同目录外置逻辑脚本
def load_external_logic():
    script_path = os.path.join(os.path.dirname(sys.executable), "main_logic.py")
    if not os.path.exists(script_path):
        messagebox.showerror("错误", "缺少 main_logic.py，请和exe放在同一个文件夹！")
        sys.exit(1)
    import importlib.util
    spec = importlib.util.spec_from_file_location("external_logic", script_path)
    logic_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(logic_mod)
    return logic_mod

if __name__ == "__main__":
    base_dir = os.path.dirname(sys.executable)
    os.chdir(base_dir)
    logic = load_external_logic()
    # 把tk根窗口传给外置脚本，所有渲染、逻辑交给外部py
    root = tk.Tk()
    root.title("桌面宠物")
    root.resizable(True, True) # 允许自由缩放窗口
    logic.start_pet(root, base_dir)
    root.mainloop()
