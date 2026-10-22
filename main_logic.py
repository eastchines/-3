import os
import threading
import time
from PIL import Image, ImageTk
import pynput.keyboard
import tkinter as tk

# ========== 这里全部是你可以随时修改的配置 ==========
HUNGER_TIME = 3600
IDLE_TIME = 30
PET_SPEED = 2
IMG_NORMAL_BODY = "skin/girl_body.png"
IMG_BEAST = "skin/beast_0.png"
# ==================================================

def start_pet(root, base_dir):
    # 资源路径：直接读exe同目录skin文件夹
    def get_img_path(name):
        return os.path.join(base_dir, name)

    # 加载图片
    img_normal = Image.open(get_img_path(IMG_NORMAL_BODY)).convert("RGBA")
    img_beast = Image.open(get_img_path(IMG_BEAST)).convert("RGBA")
    # 缩放，按需调整大小
    img_normal = img_normal.resize((120, 120))
    img_beast = img_beast.resize((120, 120))
    tk_normal = ImageTk.PhotoImage(img_normal)
    tk_beast = ImageTk.PhotoImage(img_beast)

    # 画布
    canvas = tk.Canvas(root, width=120, height=120, bg="white", highlightthickness=0)
    canvas.pack()
    pet_img_id = canvas.create_image(60, 60, image=tk_normal)
    # 保留引用，防止图片被垃圾回收消失
    canvas.img_ref = tk_normal
    canvas.img_beast_ref = tk_beast

    # 移动变量
    x = root.winfo_x()
    y = root.winfo_y()
    dx = PET_SPEED  # 水平方向速度，正数向右，负数向左
    is_beast = False
    idle_timer = 0
    last_press_time = time.time()

    # 键盘监听线程
    def keyboard_listener():
        nonlocal last_press_time
        def on_press(key):
            last_press_time = time.time()
        listener = pynput.keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
    threading.Thread(target=keyboard_listener, daemon=True).start()

    # 主更新循环（after驱动，不会卡死tk）
    def update_loop():
        nonlocal x, y, dx, is_beast, idle_timer, pet_img_id
        now = time.time()
        # 计算闲置时长
        idle_timer = now - last_press_time

        # 闲置超时切换兽态
        if idle_timer > IDLE_TIME and not is_beast:
            is_beast = True
            canvas.itemconfig(pet_img_id, image=canvas.img_beast_ref)
        elif idle_timer <= IDLE_TIME and is_beast:
            is_beast = False
            canvas.itemconfig(pet_img_id, image=canvas.img_ref)

        # 窗口左右移动、碰到屏幕边界掉头
        screen_w = root.winfo_screenwidth()
        x += dx
        # 左右边界判断
        if x <= 0:
            dx = PET_SPEED
        if x + 120 >= screen_w:
            dx = -PET_SPEED

        root.geometry(f"+{x}+{y}")
        root.after(50, update_loop)

    update_loop()
