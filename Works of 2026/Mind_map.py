# Mind_map
# 思维导图

import tkinter as tk
from tkinter import scrolledtext, messagebox
import turtle

# 主窗口
root = tk.Tk()
root.title("思维导图自动设计")
root.geometry("600x400")

# 绘制思维导图
def draw_mindmap():
    content = input_box.get("1.0", tk.END).strip()
    if not content:
        messagebox.showwarning("提醒", "请先输入文本内容！")
        return
    # 分割层级，按换行拆分节点
    nodes = content.splitlines()
    if len(nodes) == 0:
        return

    # 初始化画笔
    t = turtle.Turtle()
    turtle.setup(800, 600)
    t.speed(2)
    t.hideturtle()
    t.pensize(2)

    # 中心主题
    center_x, center_y = 0, 0
    t.penup()
    t.goto(center_x, center_y)
    t.pendown()
    t.color("#1f77b4")
    t.write(nodes[0], font=("微软雅黑", 16, "bold"), align="center")

    # 分支绘制
    offset = 80
    angle = -60
    for idx, word in enumerate(nodes[1:]):
        t.penup()
        t.goto(center_x, center_y)
        t.pendown()
        t.color("#ff7f0e")
        t.setheading(angle + idx * 30)
        t.forward(offset)
        t.write(word, font=("微软雅黑", 12), align="left")

    turtle.done()

# 界面组件
tk.Label(root, text="输入文本，每行一个节点", font=("微软雅黑",12)).pack(pady=5)
input_box = scrolledtext.ScrolledText(root, width=70, height=12, font=("微软雅黑",11))
input_box.pack(padx=10)

tk.Button(root, text="一键生成思维导图", command=draw_mindmap,
          font=("微软雅黑",12), bg="#409eff", fg="white").pack(pady=15)

root.mainloop()
