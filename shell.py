import sys
import os

def get_base_dir():
    if hasattr(sys, "_MEIPASS"):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(".")

if __name__ == "__main__":
    base_dir = get_base_dir()
    logic_file = os.path.join(base_dir, "main_logic.py")

    if not os.path.exists(logic_file):
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", f"找不到 main_logic.py\n路径：{logic_file}\n请放到和pet.exe同一个文件夹！")
        sys.exit(1)
    try:
        # 直接读取并执行外部脚本，不需要import
        with open(logic_file, "r", encoding="utf-8") as f:
            code = f.read()
        # 给外部脚本传 base_dir
        g_vars = {"BASE_DIR": base_dir}
        exec(code, g_vars)
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", f"加载 main_logic.py 失败：\n{e}")
        sys.exit(1)
