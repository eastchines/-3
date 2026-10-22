import sys
import os
import tkinter as tk
from tkinter import messagebox

# 获取exe所在目录
if getattr(sys, 'frozen', False):
    exe_path = sys.executable
    base_dir = os.path.dirname(exe_path)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

logic_path = os.path.join(base_dir, "main_logic.py")

if not os.path.exists(logic_path):
    tk.Tk().withdraw()
    messagebox.showerror("错误", f"找不到 main_logic.py\n路径: {logic_path}\n请放到和pet.exe同一个文件夹！")
    sys.exit(1)

try:
    # utf-8-sig 自动处理U+FEFF BOM报错
    with open(logic_path, "r", encoding="utf-8-sig") as f:
        logic_code = f.read()
except Exception as e:
    tk.Tk().withdraw()
    messagebox.showerror("错误", f"加载 main_logic.py失败:\n{str(e)}")
    sys.exit(1)

# 创建无边框置顶窗口
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "white")

# 执行外部逻辑，传入窗口和基础目录
namespace = {
    "root": root,
    "base_dir": base_dir
}
exec(logic_code, namespace)

root.mainloop()
