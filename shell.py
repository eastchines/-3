import sys
import os

def get_base_dir():
    if hasattr(sys, "_MEIPASS"):
        # 打包后exe所在目录
        return os.path.dirname(sys.executable)
    else:
        # 本地直接运行shell.py的时候
        return os.path.abspath(".")

if __name__ == "__main__":
    base_dir = get_base_dir()
    # 把exe所在目录加入模块搜索路径，这样能import外面的main_logic
    sys.path.insert(0, base_dir)

    try:
        import main_logic
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", f"加载 main_logic.py 失败：\n{e}\n\n请确认 main_logic.py 和 pet.exe 在同一个文件夹！")
        sys.exit(1)

    # 启动宠物
    main_logic.run_pet(base_dir)
