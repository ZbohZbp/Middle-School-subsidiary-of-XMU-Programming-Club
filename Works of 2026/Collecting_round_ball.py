# Collecting_round_ball.py
# 收集圆球

import turtle
import random
import time

# ==================== 游戏配置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 25      # 移动速度
ITEM_BASE_SPEED = 3    # 物品下落基础速度
SPAWN_RATE = 40        # 生成频率
GAME_DURATION = 60     # 游戏时长（秒）

# ==================== 物品类（圆球/炸弹） ====================
class Item:
    def __init__(self, item_type):
        self.turtle = turtle.Turtle()
        self.turtle.shape("circle")
        self.turtle.penup()
        self.turtle.speed(0)
        
        self.type = item_type  # 'good' (绿球) 或 'bad' (红炸弹)
        
        if self.type == 'good':
            self.turtle.color("lime")
            self.turtle.shapesize(1.5)
            self.score_val = 10
        else:
            self.turtle.color("red")
            self.turtle.shapesize(1.2)
            self.score_val = -20
            
        # 随机位置生成
        x = random.randint(-SCREEN_WIDTH // 2 + 40, SCREEN_WIDTH // 2 - 40)
        self.turtle.goto(x, SCREEN_HEIGHT // 2)
        self.active = True
        # 速度随分数略微增加
        self.speed_val = ITEM_BASE_SPEED + random.uniform(0, 2)

    def move(self):
        if self.active:
            self.turtle.sety(self.turtle.ycor() - self.speed_val)
            if self.turtle.ycor() < -SCREEN_HEIGHT // 2:
                self.active = False
                self.turtle.hideturtle()

    def hide(self):
        self.turtle.hideturtle()
        self.active = False

# ==================== 粒子特效类 ====================
class Particle:
    def __init__(self, x, y, color):
        self.turtle = turtle.Turtle()
        self.turtle.shape("circle")
        self.turtle.color(color)
        self.turtle.shapesize(0.3)
        self.turtle.penup()
        self.turtle.speed(0)
        self.turtle.goto(x, y)
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.life = 15

    def update(self):
        self.turtle.setx(self.turtle.xcor() + self.vx)
        self.turtle.sety(self.turtle.ycor() + self.vy)
        self.life -= 1
        if self.life <= 0:
            self.turtle.hideturtle()
            return False
        return True

# ==================== 游戏主类 ====================
class CollectGame:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen.title("收集圆球 - 全向移动版")
        self.screen.bgcolor("black")
        self.screen.tracer(0)

        self.items = []
        self.particles = []
        self.score = 0
        self.is_game_over = False
        self.frame_count = 0
        self.start_time = time.time()
        
        self._setup_player()
        self._setup_ui()
        self._bind_keys()
        
    def _setup_player(self):
        self.player = turtle.Turtle()
        self.player.shape("triangle")
        self.player.color("cyan")
        self.player.shapesize(1.5)
        self.player.penup()
        self.player.speed(0)
        self.player.goto(0, 0)  # 初始位置改为屏幕中心，方便上下移动
        self.player.setheading(90)

    def _setup_ui(self):
        # 分数显示
        self.pen_score = turtle.Turtle()
        self.pen_score.hideturtle()
        self.pen_score.color("white")
        self.pen_score.penup()
        self.pen_score.goto(-SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 - 40)
        
        # 时间条背景
        self.pen_timer_bg = turtle.Turtle()
        self.pen_timer_bg.hideturtle()
        self.pen_timer_bg.color("gray")
        self.pen_timer_bg.penup()
        self.pen_timer_bg.goto(-SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 - 70)
        self.pen_timer_bg.pendown()
        self.pen_timer_bg.forward(200)
        self.pen_timer_bg.penup()

        # 时间条前景
        self.pen_timer_fg = turtle.Turtle()
        self.pen_timer_fg.hideturtle()
        self.pen_timer_fg.color("green")
        self.pen_timer_fg.penup()
        self.pen_timer_fg.goto(-SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 - 70)
        
        self._refresh_ui()

    def _bind_keys(self):
        self.screen.listen()
        # 左右移动
        self.screen.onkeypress(self.move_left, "Left")
        self.screen.onkeypress(self.move_right, "Right")
        # 上下移动 (新增)
        self.screen.onkeypress(self.move_up, "Up")
        self.screen.onkeypress(self.move_down, "Down")
        # 重启
        self.screen.onkeypress(self.restart_game, "r")

    # ---------- 移动控制逻辑 ----------
    def move_left(self):
        if not self.is_game_over:
            x = self.player.xcor()
            if x > -SCREEN_WIDTH // 2 + 30:
                self.player.setx(x - PLAYER_SPEED)
                self.player.setheading(135)

    def move_right(self):
        if not self.is_game_over:
            x = self.player.xcor()
            if x < SCREEN_WIDTH // 2 - 30:
                self.player.setx(x + PLAYER_SPEED)
                self.player.setheading(45)
                
    def move_up(self):
        if not self.is_game_over:
            y = self.player.ycor()
            if y < SCREEN_HEIGHT // 2 - 30:
                self.player.sety(y + PLAYER_SPEED)
                self.player.setheading(90)

    def move_down(self):
        if not self.is_game_over:
            y = self.player.ycor()
            if y > -SCREEN_HEIGHT // 2 + 30:
                self.player.sety(y - PLAYER_SPEED)
                self.player.setheading(270)

    def _reset_heading(self):
        if not self.is_game_over:
             self.player.setheading(90)

    def _spawn_item(self):
        # 70%概率生成好球，30%概率生成炸弹
        item_type = 'good' if random.random() > 0.3 else 'bad'
        self.items.append(Item(item_type))

    def _create_explosion(self, x, y, color):
        for _ in range(8):
            self.particles.append(Particle(x, y, color))

    def _refresh_ui(self):
        self.pen_score.clear()
        self.pen_score.write(f"Score: {self.score}", font=("Arial", 16, "normal"))
        
        # 更新时间条
        elapsed = time.time() - self.start_time
        remaining = max(0, GAME_DURATION - elapsed)
        ratio = remaining / GAME_DURATION
        self.pen_timer_fg.clear()
        self.pen_timer_fg.color("green" if ratio > 0.3 else "red")
        self.pen_timer_fg.pendown()
        self.pen_timer_fg.forward(200 * ratio)
        self.pen_timer_fg.penup()

    def _show_game_over(self):
        pen = turtle.Turtle()
        pen.hideturtle()
        pen.color("yellow")
        pen.penup()
        pen.goto(0, 20)
        pen.write("TIME'S UP!", align="center", font=("Arial", 40, "bold"))
        pen.goto(0, -30)
        pen.color("white")
        pen.write(f"Final Score: {self.score}\nPress 'R' to Restart", align="center", font=("Arial", 20, "normal"))

    def restart_game(self):
        if not self.is_game_over:
            return
        
        # 清理对象
        for item in self.items:
            item.hide()
        for p in self.particles:
            p.turtle.hideturtle()
            
        self.items.clear()
        self.particles.clear()
        self.score = 0
        self.is_game_over = False
        self.frame_count = 0
        self.start_time = time.time()
        self.player.goto(0, 0)  # 重置回中心
        self.player.color("cyan")
        
        # 清除屏幕并重绘UI
        self.screen.clear()
        self.screen.bgcolor("black")
        self._setup_player()
        self._setup_ui()
        self._bind_keys()
        self.game_loop()

    def game_loop(self):
        if self.is_game_over:
            self.screen.update()
            return

        self.frame_count += 1
        
        # 检查时间
        if time.time() - self.start_time >= GAME_DURATION:
            self.is_game_over = True
            self._show_game_over()
            self.screen.update()
            return

        # 生成物品
        if self.frame_count % SPAWN_RATE == 0:
            self._spawn_item()

        # 更新物品
        for item in list(self.items):
            item.move()
            
            # 碰撞检测
            if item.active and self._check_collision(item.turtle):
                self.score += item.score_val
                color = "lime" if item.type == 'good' else "red"
                self._create_explosion(item.turtle.xcor(), item.turtle.ycor(), color)
                item.hide()
                self.items.remove(item)
                self._refresh_ui()
                
            # 移除超出屏幕的物品
            elif not item.active:
                if item in self.items:
                    self.items.remove(item)

        # 更新粒子
        for p in list(self.particles):
            if not p.update():
                self.particles.remove(p)
                
        # 玩家回正方向
        if self.frame_count % 5 == 0:
            self._reset_heading()

        self._refresh_ui()
        self.screen.update()
        self.screen.ontimer(self.game_loop, 12)

    def _check_collision(self, obj_turtle, distance=25):
        return self.player.distance(obj_turtle) < distance

# ==================== 程序入口 ====================
if __name__ == "__main__":
    game = CollectGame()
    game.game_loop()
    turtle.mainloop()
