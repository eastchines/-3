import os
import time
import tkinter as tk
from PIL import Image, ImageTk
import pynput.keyboard

# ========== 配置，以后你就在这里改功能！ ==========
HUNGER_TIME = 3600
IDLE_TIME = 30
PET_SPEED = 2
IMG_NORMAL_BODY = "skin/girl_body.png"
IMG_BEAST = "skin/beast_0.png"
# ================================================

def run_pet(base_dir):
    def get_img_path(name):
        return os.path.join(base_dir, name)

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", root["bg"])
    canvas = tk.Canvas(root, bg="white", highlightthickness=0)
    canvas.pack()

    img_normal = Image.open(get_img_path(IMG_NORMAL_BODY)).convert("RGBA")
    img_beast = Image.open(get_img_path(IMG_BEAST)).convert("RGBA")
    tk_normal = ImageTk.PhotoImage(img_normal)
    tk_beast = ImageTk.PhotoImage(img_beast)

    current_tk_img = tk_normal
    pet_id = canvas.create_image(0, 0, image=current_tk_img, anchor=tk.NW)

    x, y = 100, 100
    last_press_time = time.time()
    is_beast = False

    def on_press(key):
        nonlocal last_press_time
        last_press_time = time.time()
    listener = pynput.keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()

    drag_x, drag_y = 0, 0
    def on_mouse_down(event):
        nonlocal drag_x, drag_y
        drag_x = event.x
        drag_y = event.y
    def on_mouse_move(event):
        nonlocal x, y, drag_x, drag_y
        dx = event.x - drag_x
        dy = event.y - drag_y
        x += dx
        y += dy
        root.geometry(f"+{x}+{y}")
    canvas.bind("<Button-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_move)

    def update_loop():
        nonlocal x, y, is_beast, current_tk_img, last_press_time
        idle_timer = time.time() - last_press_time

        if idle_timer >= IDLE_TIME and not is_beast:
            is_beast = True
            current_tk_img = tk_beast
            canvas.itemconfig(pet_id, image=current_tk_img)
        elif idle_timer < IDLE_TIME and is_beast:
            is_beast = False
            current_tk_img = tk_normal
            canvas.itemconfig(pet_id, image=current_tk_img)

        x += PET_SPEED
        screen_w = root.winfo_screenwidth()
        if x > screen_w - img_normal.width:
            x = 0
        root.geometry(f"{img_normal.width}x{img_normal.height}+{x}+{y}")
        root.after(50, update_loop)
    update_loop()
    root.mainloop()

# exec执行的时候，BASE_DIR由shell传进来
run_pet(BASE_DIR)
