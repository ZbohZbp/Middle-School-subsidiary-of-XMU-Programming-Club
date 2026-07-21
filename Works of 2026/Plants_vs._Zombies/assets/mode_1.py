"""
1. 游戏初始化与设置
2. 资源加载模块
3. 游戏对象类(植物、僵尸等)
4. 游戏主逻辑
5. UI交互部分
"""

# ====================== 1. 游戏初始化与设置 ======================
import pygame
import random
import sys
import os
import time
import warnings

# 设置环境变量，禁止pygame欢迎信息
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# 重定向stderr以抑制libpng警告
_original_stderr = sys.stderr
class DevNull:
    def write(self, msg): pass
    def flush(self): pass

# 初始化pygame（临时重定向stderr以隐藏警告）
sys.stderr = DevNull()
pygame.init()
pygame.font.init()
# 恢复stderr
sys.stderr = _original_stderr


def get_game_font(size=20):
    """兼容不同环境的字体加载，优先使用中文字体，失败时回退到默认字体。"""
    candidates = ['Microsoft YaHei', 'SimSun', 'Arial Unicode MS', 'Arial']
    for name in candidates:
        try:
            font = pygame.font.SysFont(name, size)
            if font is not None:
                return font
        except Exception:
            continue
    try:
        return pygame.font.Font(None, size)
    except Exception:
        return pygame.font.Font(pygame.font.get_default_font(), size)


font = get_game_font(20)  # 全局字体设置

# ====================== 2. 资源加载模块 ======================
def load_image(name, scale=1, alpha=None):
    """
    加载游戏图片资源
    
    参数:
        name: 图片文件名
        scale: 缩放比例
        alpha: 透明度(0-1)
    
    返回:
        缩放后的图片Surface对象
    """
    try:
        if name in ['back.png', 'space.png', 'gback.png']:
            image_path = os.path.join(os.path.dirname(__file__), 'background', name)
        elif name in ['sun.png', 'cz.png', 'car.png', 'win.png', 'music.png', 'failure.png', 'trophy.png', 'boom.gif', 'boomdie.gif']:
            image_path = os.path.join(os.path.dirname(__file__), 'effects', name)
        elif name in ['zombie.png', 'hurtzombie.png', 'slowzombie.png']:
            image_path = os.path.join(os.path.dirname(__file__), 'zombies', name)
        elif name == 'hbzd.png':
            image_path = os.path.join(os.path.dirname(__file__), 'plants', 'sunflower', name)
        elif name == 'wdzd.png' or name == 'g.png':
            image_path = os.path.join(os.path.dirname(__file__), 'plants', 'peashooter', name)
        elif name in ['xrk1.png', 'hb1.png', 'wd1.png', 'xdfz1.png', 'xrkz.png', 'hbz.png', 'wdz.png', 'xdfzz.png']:
            # Map old abbreviations to new folder names
            folder_map = {
                'xrk': 'snow_pea',
                'hb': 'sunflower', 
                'wd': 'peashooter',
                'xdfz': 'wall_nut'
            }
            prefix = name.split('.')[0][:-1] if name.endswith('1.png') or name.endswith('z.png') else name.split('.')[0]
            folder = folder_map.get(prefix, prefix)
            image_path = os.path.join(os.path.dirname(__file__), 'plants', folder, name)
        else:
            # Map old abbreviations to new folder names
            folder_map = {
                'xrk': 'snow_pea',
                'hb': 'sunflower',
                'wd': 'peashooter', 
                'xdfz': 'wall_nut'
            }
            prefix = name.split('.')[0]
            folder = folder_map.get(prefix, prefix)
            image_path = os.path.join(os.path.dirname(__file__), 'plants', folder, name)
        if not os.path.exists(image_path):
            # 仅在找不到文件时才输出警告
            print(f"警告: 图片文件 {name} 不存在")
            # 创建一个空白图片作为占位符
            placeholder = pygame.Surface((50, 50), pygame.SRCALPHA)
            placeholder.fill((0, 0, 0, 0))
            return placeholder
        
        image = pygame.image.load(image_path)
        # 转换为显示格式以加速blit（最重要的性能优化）
        if image.get_alpha():
            image = image.convert_alpha()
        else:
            image = image.convert()
        
        width = int(image.get_width() * scale)
        height = int(image.get_height() * scale)
        if scale != 1.0:
            scaled_image = pygame.transform.scale(image, (width, height))
        else:
            scaled_image = image
        
        if alpha is not None:
            scaled_image = scaled_image.convert_alpha()
            scaled_image.set_alpha(int(alpha * 255))
        
        return scaled_image
    except Exception as e:
        # 仅在发生错误时才输出警告
        print(f"加载图片 {name} 时出错: {e}")
        # 创建一个空白图片作为占位符
        placeholder = pygame.Surface((50, 50), pygame.SRCALPHA)
        placeholder.fill((0, 0, 0, 0))
        return placeholder

# 音效加载
def load_sound(name):
    """
    加载游戏音效
    
    参数:
        name: 音效文件名
    
    返回:
        音效对象
    """
    try:
        sound_path = os.path.join(os.path.dirname(__file__), 'sounds', name)
        if not os.path.exists(sound_path):
            # 仅在找不到文件时才输出警告
            print(f"警告: 音效文件 {name} 不存在")
            return None
        
        sound = pygame.mixer.Sound(sound_path)
        return sound
    except Exception as e:
        # 仅在发生错误时才输出警告
        print(f"加载音效 {name} 时出错: {e}")
        return None

# 加载动画帧
def load_animation(name, frame_count, scale=1.0):
    """
    加载一系列动画帧
    
    参数:
        name: 帧文件名前缀
        frame_count: 帧数量
        scale: 缩放比例
        
    返回:
        帧列表
    """
    frames = []
    for i in range(frame_count):
        try:
            frame_name = f"{name}{i}.png"
            frame = load_image(frame_name, scale)
            frames.append(frame)
        except Exception as e:
            print(f"加载动画帧 {frame_name} 时出错: {e}")
    return frames

# 游戏音效
sounds = {
    'plant': load_sound('by_plant/plant.ogg'),      # 种植植物音效
    'win': load_sound('winmusic.ogg'),     # 胜利音效
    'eaten': load_sound('by_zombie/eaten.ogg'),      # 植物被吃掉音效
    'peashoot': load_sound('by_plant/peashoot.mp3'), # 豌豆发射音效
    'hit': load_sound('by_zombie/hit.mp3'),          # 僵尸受击音效
    'points': load_sound('by_plant/points.ogg'),    # 阳光收集音效
    'died': load_sound('by_zombie/died.mp3')         # 坚果墙死亡音效
}

# 屏幕设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("普普通通的植物大战僵尸")

# 加载背景图片
background = load_image('back.png')

# 主题音乐列表
BASE_MUSIC_FILES = ['fight.mp3', 'peaceful.mp3', 'qidong.mp3', 'space.mp3']
HAKIMI_MUSIC_FILES = ['g1.mp3', 'g2.mp3', 'g3.mp3', 'g4.mp3']

# pygame.mixer.music.set_volume(0.5) # 音量在加载时设置

# 网格设置
GRID_COLS = 9
GRID_COL_WIDTH = SCREEN_WIDTH // GRID_COLS  # 每列宽度
GRID_HEIGHT = SCREEN_HEIGHT // 6  # UI区域高度
LAWN_HEIGHT = SCREEN_HEIGHT - GRID_HEIGHT  # 草坪高度
LAWN_ROWS = 5  # 草坪行数

# 颜色定义
WHITE = (255, 255, 255, 0)
GREEN = (0, 255, 0, 0)
GRAY = (100, 100, 100, 0)
RED = (255, 0, 0, 0)
YELLOW = (255, 255, 0, 0)
PURPLE = (128, 0, 128, 0)  

# 植物类
class Plant:
    def __init__(self, x, y, plant_type='hb', theme_index=0):
        self.x = x
        self.y = y
        # 坚果墙有更高的生命值
        self.health = 300 if plant_type == 'xdfz' else 100
        self.attack_cooldown = 0
        self.plant_type = plant_type
        # 坚果墙图像特殊处理
        scale = 1.3 if plant_type == 'xdfz' else 1.0
        self.image = load_image(f'{plant_type}.png', scale)
        self.hit_timer = 0
        self.slow_timer = 0
        self.original_cooldown = 120  # 攻击冷却时间，约0.5发/秒
        self.current_cooldown = 60
        self.excited_timer = 0  # 兴奋状态计时器
        self.being_eaten = False  # 是否正在被僵尸吃
        self.opacity = 255  # 透明度，255为完全不透明
        # 坚果墙碰撞区域稍大
        rect_size = 70 if plant_type == 'xdfz' else 60
        self.rect = pygame.Rect(self.x - rect_size//2, self.y - rect_size//2, rect_size, rect_size)
        self.theme_index = theme_index  # Store theme index
        self.zombies_eating_me = []  # 跟踪正在吃这个植物的僵尸
        # 爆炸效果
        self.exploding = False  # 是否正在爆炸
        self.explosion_timer = 0  # 爆炸动画计时器
        self.explosion_frames = 10  # 爆炸动画总帧数
        self.current_explosion_frame = 0  # 当前爆炸帧
        try:
            self.explosion_image = load_image('boom.gif', 1.5)  # 爆炸图像
        except:
            self.explosion_image = None
    
    def draw(self):
        # 如果植物正在爆炸，绘制爆炸效果
        if self.exploding and self.explosion_image:
            screen.blit(self.explosion_image, (self.x - self.explosion_image.get_width()//2, self.y - self.explosion_image.get_height()//2))
            self.explosion_timer += 1
            if self.explosion_timer >= 30:
                self.exploding = False
            return
        
        # 计算绘制位置
        draw_x = self.x - self.image.get_width() // 2
        draw_y = self.y - self.image.get_height() // 2
        
        if self.opacity < 255:
            # 只有被吃时才复制图像（绝大多数帧跳过此分支）
            image_copy = self.image.copy()
            image_copy.set_alpha(self.opacity)
            screen.blit(image_copy, (draw_x, draw_y))
        else:
            screen.blit(self.image, (draw_x, draw_y))
        
        # 受击/减速叠加层（用预创建的小surface而非每帧新建）
        if self.hit_timer > 0:
            overlay = pygame.Surface((self.image.get_width(), self.image.get_height()), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, 128))
            screen.blit(overlay, (draw_x, draw_y))
            self.hit_timer -= 1
        elif self.slow_timer > 0:
            overlay = pygame.Surface((self.image.get_width(), self.image.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 255, 128))
            screen.blit(overlay, (draw_x, draw_y))
            self.slow_timer -= 1
        
        # 更新碰撞检测区域
        rect_size = 70 if self.plant_type == 'xdfz' else 60
        self.rect = pygame.Rect(self.x - rect_size//2, self.y - rect_size//2, rect_size, rect_size)
    
    def update(self, zombies=None, bullets=None):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # 如果正在被吃，降低透明度
        if self.being_eaten:
            # 坚果墙被吃的速度更慢
            self.opacity -= 0.5 if self.plant_type == 'xdfz' else 1
            if self.opacity <= 0:
                self.health = 0  # 植物被吃掉
                
                # 坚果墙的反伤功能和爆炸效果
                if self.plant_type == 'xdfz' and self.zombies_eating_me:
                    # 播放死亡音效
                    if sounds['died']:
                        sounds['died'].play()
                        
                    # 触发爆炸效果
                    self.exploding = True
                    
                    # 被吃死时对第一个吃它的僵尸造成致命伤害
                    if len(self.zombies_eating_me) > 0 and self.zombies_eating_me[0] in zombies:
                        first_zombie = self.zombies_eating_me[0]
                        first_zombie.health = 0
                        # 设置为爆炸死亡
                        first_zombie.dying = True
                        first_zombie.boom_effect = True
                
                return 'eaten'  # 返回被吃掉的信号
        
        # 向日葵产生阳光
        if self.plant_type == 'xrk' and not self.being_eaten:
            if not hasattr(self, 'sun_timer'):
                self.sun_timer = 0
            self.sun_timer += 1
            if self.sun_timer >= 600:  # 10秒产生一次阳光
                self.sun_timer = 0
                return 'sun'
        
        # 检查同一行是否有僵尸，并且植物没有被吃
        if self.plant_type in ['hb', 'wd'] and self.attack_cooldown == 0 and zombies and bullets is not None and not self.being_eaten:
            for zombie in zombies:
                if abs(zombie.y - self.y) < (LAWN_HEIGHT // LAWN_ROWS) // 2:
                    bullet_img = None
                    if self.plant_type == 'hb':
                        bullet_img = 'hbzd.png'
                    elif self.plant_type == 'wd':
                        if self.theme_index == 2: # Hakimi theme
                            bullet_img = 'g.png'
                        else:
                            bullet_img = 'wdzd.png'
                    
                    if bullet_img:
                        bullets.append(Bullet(self.x, self.y, bullet_img))
                        self.attack_cooldown = self.current_cooldown
                        
                        # 播放豌豆发射音效
                        if self.plant_type == 'wd' and sounds['peashoot']:
                            sounds['peashoot'].play()
                    
                    break
        
        return None
    




# 僵尸类
class Zombie:
    def __init__(self, y):
        self.x = SCREEN_WIDTH
        self.y = y
        self.health = 100
        self.speed = 1
        self.image = load_image('zombie.png', 1.0)
        self.hurt_image = load_image('hurtzombie.png', 1.0)
        self.slow_image = load_image('slowzombie.png', 1.0)
        self.hit_timer = 0
        self.slow_timer = 0
        self.original_speed = 1
        self.eating = False  # 是否正在吃植物
        self.attack_cooldown = 0  # 攻击冷却
        self.attack_damage = 1  # 攻击伤害（影响植物透明度降低速度）
        self.target_plant = None  # 正在攻击的植物
        self.rect = pygame.Rect(self.x - 30, self.y - 30, 60, 60)  # 碰撞检测区域
        self.dying = False  # 是否正在死亡
        self.dying_timer = 100  # 死亡渐隐效果的持续时间
        self.opacity = 255  # 透明度
        self.boom_effect = False  # 是否有爆炸效果
        self.boom_frame = 0  # 当前爆炸帧
        # 尝试加载爆炸效果图像
        try:
            self.boom_image = load_image('boomdie.gif', 1.3)
        except:
            self.boom_image = None
    
    def draw(self):
        if self.dying:
            if self.dying_timer > 0:
                if self.boom_effect and self.boom_image:
                    # 爆炸效果直接blit，避免copy
                    self.boom_image.set_alpha(self.opacity)
                    screen.blit(self.boom_image, (self.x - self.boom_image.get_width()//2, self.y - self.boom_image.get_height()//2))
                    self.boom_image.set_alpha(255)  # 恢复供下次使用
                else:
                    # 普通死亡渐隐效果 — 仅在透明度变化时才copy
                    current_img = self.image
                    if self.hit_timer > 0:
                        current_img = self.hurt_image
                    elif self.slow_timer > 0:
                        current_img = self.slow_image
                    
                    if self.opacity < 255:
                        alpha_img = current_img.copy()
                        alpha_img.set_alpha(self.opacity)
                        screen.blit(alpha_img, (self.x - current_img.get_width()//2, self.y - current_img.get_height()//2))
                    else:
                        screen.blit(current_img, (self.x - current_img.get_width()//2, self.y - current_img.get_height()//2))
                
                # 更新渐隐效果
                self.dying_timer -= 1
                self.opacity = int(self.dying_timer * 255 / 100)
            return
            
        if self.hit_timer > 0:
            screen.blit(self.hurt_image, (self.x - self.hurt_image.get_width()//2, self.y - self.hurt_image.get_height()//2))
            self.hit_timer -= 1
        elif self.slow_timer > 0:
            screen.blit(self.slow_image, (self.x - self.slow_image.get_width()//2, self.y - self.slow_image.get_height()//2))
            self.slow_timer -= 1
        else:
            screen.blit(self.image, (self.x - self.image.get_width()//2, self.y - self.image.get_height()//2))
        
        # 更新碰撞检测区域
        self.rect = pygame.Rect(self.x - 30, self.y - 30, 60, 60)
    
    def update(self, plants=None):
        # 更新僵尸状态
        if self.slow_timer > 0:
            self.speed = self.original_speed * 0.5  # 减速50%
        else:
            self.speed = self.original_speed
        
        # 检查是否正在吃植物
        if self.eating and self.target_plant:
            # 僵尸停止移动，开始攻击植物
            if self.attack_cooldown <= 0:
                self.target_plant.being_eaten = True
                # 将僵尸添加到植物的攻击者列表中
                if self not in self.target_plant.zombies_eating_me:
                    self.target_plant.zombies_eating_me.append(self)
                self.attack_cooldown = 30  # 每半秒攻击一次
            else:
                self.attack_cooldown -= 1
            return
        
        # 如果没有在吃植物，则移动
        if not self.eating:
            self.x -= self.speed
        
        # 检查是否碰到植物
        if plants:
            for plant in plants:
                if self.rect.colliderect(plant.rect) and not self.eating:  # 修改为仅检查自身未在吃植物
                    self.eating = True
                    self.target_plant = plant
                    plant.being_eaten = True
                    # 将僵尸添加到植物的攻击者列表中
                    if self not in plant.zombies_eating_me:
                        plant.zombies_eating_me.append(self)
                    return
        
        # 如果目标植物已经不存在，重置状态
        if self.target_plant is None and self.eating:
            self.eating = False

# 子弹类
class Bullet:
    def __init__(self, x, y, bullet_type='hbzd.png'):
        self.x = x + 20  # 向前偏移20像素
        self.y = y - 20  # 向上偏移20像素
        self.speed = 2.8  # 子弹飞行速度
        self.bullet_type = bullet_type
        self.image = load_image(bullet_type, 0.8)
    
    def draw(self):
        screen.blit(self.image, (self.x - self.image.get_width()//2, self.y - self.image.get_height()//2))
    
    def update(self):
        self.x += self.speed

# 阳光类
class Sun:
    def __init__(self, x, y, sun_value_ref=None):
        self.x = x
        self.y = y
        self.speed = 0.8  # 阳光下落速度
        self.value = 25
        self.image = load_image('sun.png', 0.6)
        self.lifetime = 0
        self.collected = False
        self.target_x = 40
        self.target_y = 25
        self.move_speed = 16
        self.sun_value_ref = sun_value_ref
    
    def draw(self):
        screen.blit(self.image, (self.x - self.image.get_width()//2, self.y - self.image.get_height()//2))
    
    def collect(self):
        """统一处理阳光收集，确保值正确增加。"""
        if self.collected:
            return False

        self.collected = True
        self.target_x = 40
        self.target_y = 25
        self.move_speed = 4  # 回收动画速度

        if self.sun_value_ref is not None:
            self.sun_value_ref[0] += self.value

        if sounds.get('points'):
            sounds['points'].play()
        return True

    def update(self, mouse_pos=None):
        self.lifetime += 1

        if mouse_pos is None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
        else:
            mouse_x, mouse_y = mouse_pos

        if not self.collected and ((mouse_x - self.x)**2 + (mouse_y - self.y)**2) <= 900:
            self.collect()

        if self.collected:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist_sq = dx*dx + dy*dy

            if dist_sq < 25:  # 5^2，用平方距离避免开平方
                return True
            elif dist_sq > 0:
                dist = dist_sq ** 0.5
                self.x += dx/dist * self.move_speed
                self.y += dy/dist * self.move_speed
                return False
            return False
        elif self.lifetime >= 150:  # 约2.5秒后自动回收
            self.collect()
            return False
        else:
            self.y += self.speed
            if self.y > SCREEN_HEIGHT:
                return True
            return False

# 处理键盘按键事件
def handle_keydown(event, selected_plant):
    """处理键盘按键事件"""
    if event.key == pygame.K_1:
        return 'xrk'  # 向日葵
    elif event.key == pygame.K_2:
        return 'hb'  # 寒冰射手
    elif event.key == pygame.K_3:
        return 'wd'  # 豌豆射手
    elif event.key == pygame.K_4:
        return 'xdfz'  # 坚果墙
    elif event.key == pygame.K_5:
        return 'cz'  # 铲子
    return selected_plant

# 处理鼠标移动事件
def handle_mouse_motion(event, GRID_HEIGHT, selected_plant, GRID_COL_WIDTH, GRID_COLS, LAWN_HEIGHT, LAWN_ROWS, preview_plant_pos):
    """处理鼠标移动事件"""
    mouse_x, mouse_y = pygame.mouse.get_pos()
    if mouse_y >= GRID_HEIGHT and selected_plant != 'cz':
        # 计算预览位置
        col = min(max(0, mouse_x // GRID_COL_WIDTH), GRID_COLS - 1)
        row = min(max(1, (mouse_y - GRID_HEIGHT) // (LAWN_HEIGHT // LAWN_ROWS) + 1), LAWN_ROWS)
        return (
            col * GRID_COL_WIDTH + GRID_COL_WIDTH // 2,
            GRID_HEIGHT + (row - 1) * (LAWN_HEIGHT // LAWN_ROWS) + (LAWN_HEIGHT // LAWN_ROWS) // 2
        )
    return None

# 处理鼠标点击事件
def handle_mouse_click(event, music_button_rect, current_music_idx_in_list, current_active_music_list, 
                     GRID_HEIGHT, plant_ui_images, selected_plant, SCREEN_WIDTH,
                     suns, plants, plant_prices, sun_value, GRID_COL_WIDTH, GRID_COLS,
                     LAWN_HEIGHT, LAWN_ROWS, sounds, theme_idx):
    """处理鼠标点击事件"""
    # 检查是否点击了音乐按钮
    if music_button_rect.collidepoint(event.pos):
        new_music_idx = (current_music_idx_in_list + 1) % len(current_active_music_list)
        try:
            music_to_load = current_active_music_list[new_music_idx]
            music_path = os.path.join(os.path.dirname(__file__), 'music', music_to_load)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.5) # 确保音量一致性
            pygame.mixer.music.play(-1)
            print(f"切换音乐到: {music_to_load}")
            return new_music_idx, selected_plant
        except Exception as e:
            print(f"无法加载音乐文件: {music_path if 'music_path' in locals() else music_to_load}, error: {e}")
            return current_music_idx_in_list, selected_plant # 错误则返回旧索引
    
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    # 检查是否点击了植物选择区域
    if mouse_y < GRID_HEIGHT:
        for i, plant_type in enumerate(['xrk', 'hb', 'wd', 'xdfz', 'cz']):
            if plant_type == 'cz':
                x = SCREEN_WIDTH - 50
            else:
                x = 100 + i * 100
            y = GRID_HEIGHT // 2
            img = plant_ui_images[plant_type]
            if (abs(mouse_x - x) < img.get_width()//2 and 
                abs(mouse_y - y) < img.get_height()//2):

                if selected_plant == plant_type:
                    return current_music_idx_in_list, None
                else:
                    return current_music_idx_in_list, plant_type
    else:
        # 检查是否点击了阳光
        for sun in suns[:]:
            if ((mouse_x - sun.x)**2 + (mouse_y - sun.y)**2) <= 900:  # 30^2
                sun.collect()
                return current_music_idx_in_list, selected_plant
        
        # 如果没有点击阳光，则种植植物或使用铲子
        if selected_plant == 'cz':
            # 使用铲子移除植物
            for plant in plants[:]:
                if ((mouse_x - plant.x)**2 + (mouse_y - plant.y)**2) <= 900:  # 30^2
                    # 退还部分阳光(原价的50%)
                    refund = plant_prices.get(plant.plant_type, 100) * 0.5
                    sun_value[0] += int(refund)
                    plants.remove(plant)
                    
                    # 播放铲除植物的音效
                    if sounds['plant']:
                        sounds['plant'].play()
                    
                    return current_music_idx_in_list, None
        else:
            price = plant_prices.get(selected_plant, 100)
            if sun_value[0] >= price and selected_plant:  # 检查是否有足够的阳光
                # 计算点击的列(0-8)
                col = min(max(0, mouse_x // GRID_COL_WIDTH), GRID_COLS - 1)
                # 计算点击的行(1-5)
                row = min(max(1, (mouse_y - GRID_HEIGHT) // (LAWN_HEIGHT // LAWN_ROWS) + 1), LAWN_ROWS)
                
                # 计算锁定到网格中心的坐标
                plant_x = col * GRID_COL_WIDTH + GRID_COL_WIDTH // 2
                plant_y = GRID_HEIGHT + (row - 1) * (LAWN_HEIGHT // LAWN_ROWS) + (LAWN_HEIGHT // LAWN_ROWS) // 2
                
                # 检查该位置是否已有植物
                can_plant = True
                for plant in plants:
                    if abs(plant.x - plant_x) < GRID_COL_WIDTH // 2 and abs(plant.y - plant_y) < (LAWN_HEIGHT // LAWN_ROWS) // 2:
                        can_plant = False
                        break
                
                if can_plant:
                    plants.append(Plant(plant_x, plant_y, selected_plant, theme_index=theme_idx))
                    sun_value[0] -= price
                    
                    # 播放种植音效
                    if sounds['plant']:
                        sounds['plant'].play()
                    
                    return current_music_idx_in_list, None
    
    return current_music_idx_in_list, selected_plant

# 生成僵尸
def spawn_zombies(zombie_spawn_timer, zombie_count, ZOMBIE_MAX, GRID_HEIGHT, LAWN_HEIGHT, LAWN_ROWS, zombie_speed, zombies, first_zombie_delay):
    """生成僵尸"""
    # 第一只僵尸到达前有冷却时间，给玩家准备时间
    if first_zombie_delay > 0:
        first_zombie_delay -= 1
        return zombie_spawn_timer, zombie_count, first_zombie_delay
    
    zombie_spawn_timer += 1
    if zombie_spawn_timer >= 420:  # 每7秒生成一个僵尸
        zombie_spawn_timer = 0
        # 随机选择一行(1-5)生成僵尸
        row = random.randint(1, LAWN_ROWS)
        zombie_y = GRID_HEIGHT + (row - 1) * (LAWN_HEIGHT // LAWN_ROWS) + (LAWN_HEIGHT // LAWN_ROWS) // 2
        if zombie_count < ZOMBIE_MAX:
            new_zombie = Zombie(zombie_y)
            new_zombie.speed = zombie_speed
            new_zombie.original_speed = zombie_speed
            zombies.append(new_zombie)
            zombie_count += 1
    return zombie_spawn_timer, zombie_count, first_zombie_delay

# 生成阳光
def spawn_suns(sun_spawn_timer, SCREEN_WIDTH, GRID_HEIGHT, sun_value, suns):
    """生成阳光"""
    sun_spawn_timer += 1
    if sun_spawn_timer >= 300:  # 每5秒生成一个阳光
        sun_spawn_timer = 0
        # 确保阳光生成位置不会重叠在UI区域
        suns.append(Sun(random.randint(50, SCREEN_WIDTH - 50), GRID_HEIGHT + 50, sun_value))
    return sun_spawn_timer

# 更新植物状态
def update_plants(plants, zombies, bullets, suns, sun_value, sounds):
    """更新植物状态"""
    plants_to_remove = []
    for i, plant in enumerate(plants):
        result = plant.update(zombies, bullets)
        
        # 处理植物产生的结果
        if result == 'sun':
            suns.append(Sun(plant.x, plant.y, sun_value))
        elif result == 'eaten':
            # 植物被吃掉，播放音效
            if sounds['eaten']:
                sounds['eaten'].play()
            plants_to_remove.append(i)
            
            # 重置吃掉这个植物的僵尸状态
            for zombie in zombies:
                if zombie.target_plant == plant:
                    zombie.eating = False
                    zombie.target_plant = None
        
        # 子弹发射逻辑已在 Plant.update() 中统一处理（含主题支持）
        # 此处不再重复，避免双重遍历僵尸
    
    # 移除被吃掉的植物
    for i in sorted(plants_to_remove, reverse=True):
        if i < len(plants):
            plants.pop(i)

# 更新僵尸状态
def update_zombies(zombies, plants):
    """更新僵尸状态"""
    # 所有僵尸都正常更新移动，符合原版游戏逻辑
    for zombie in zombies[:]:
        zombie.update(plants)
        
        if zombie.x < 0:  # 僵尸到达左边界
            print("游戏结束!")
            # 停止当前背景音乐
            pygame.mixer.music.stop()
            
            failure_image = load_image('failure.png', 1.0, None)
            while True:
                screen.blit(failure_image, (SCREEN_WIDTH//2 - failure_image.get_width()//2, SCREEN_HEIGHT//2 - failure_image.get_height()//2))
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        return True  # 返回True表示需要重新启动主菜单
            return False  # 这行代码不会执行，但为了逻辑完整性添加
        elif zombie.health <= 0:  # 僵尸被消灭
            if not zombie.dying:  # 如果僵尸还没进入死亡状态，设置死亡状态
                zombie.dying = True
                continue
            
            # 只有当僵尸的死亡动画完成后才从列表中移除
            if zombie.dying_timer <= 0:
                zombies.remove(zombie)
    return False  # 默认不重新启动主菜单

# 更新子弹状态
def update_bullets(bullets, zombies, SCREEN_WIDTH, sounds):
    """更新子弹状态"""
    for bullet in bullets[:]:
        bullet.update()
        if bullet.x > SCREEN_WIDTH:  # 子弹超出屏幕
            bullets.remove(bullet)
            continue
            
        # 检测子弹和僵尸碰撞
        bullet_hit = False
        for zombie in zombies[:]:
            if (abs(bullet.x - zombie.x) < 30 and 
                abs(bullet.y - zombie.y) < 30):
                zombie.health -= 20
                if bullet.bullet_type == 'hbzd.png':  # 寒冰子弹
                    zombie.slow_timer = 180  # 3秒减速效果
                zombie.hit_timer = 2  # 被击中时变红5帧
                
                # 播放僵尸受击音效
                if sounds['hit']:
                    sounds['hit'].play()
                
                # 标记子弹已击中目标
                bullet_hit = True
                
                # 检查僵尸是否被消灭
                if zombie.health <= 0:
                    zombies.remove(zombie)
                
                break
        
        # 如果子弹击中目标，从子弹列表中移除
        if bullet_hit and bullet in bullets:
            bullets.remove(bullet)

# 检查胜利条件
def check_victory(zombie_count, ZOMBIE_MAX, zombies):
    """检查胜利条件"""
    return zombie_count >= ZOMBIE_MAX and len(zombies) == 0

# 显示胜利画面
def show_victory_screen():
    """显示胜利画面"""
    # 停止当前背景音乐
    pygame.mixer.music.stop()
    
    win_image = load_image('trophy.png', 1.0)  # 使用trophy.png作为胜利图片
    # 播放胜利音效
    if sounds['win']:
        sounds['win'].play()
    while True:
        screen.blit(win_image, (SCREEN_WIDTH//2 - win_image.get_width()//2, SCREEN_HEIGHT//2 - win_image.get_height()//2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 重新开始游戏
                return True  # 返回True表示需要重新启动主菜单
            elif event.type == pygame.QUIT:
                return False  # 返回False表示直接退出游戏

# 缓存渲染用的字体和静态文本，避免每帧创建
_render_font = pygame.font.SysFont('SimSun', 24)
_difficulty_names = ["简单", "普通", "困难", "测试"]
_theme_names = ["经典", "宇宙", "哈基米"]
# 预渲染不会变化的文本
_difficulty_labels = [f'难度: {n}' for n in _difficulty_names]
_theme_labels = [f'主题: {n}' for n in _theme_names]
_render_difficulty_texts = [_render_font.render(label, True, (255, 255, 255)) for label in _difficulty_labels]
_render_theme_texts = [_render_font.render(label, True, (255, 255, 255)) for label in _theme_labels]
_render_sun_label = _render_font.render('', True, (255, 255, 0))  # 占位

def render_game(screen, background, music_button_img, music_button_rect, plants, zombies, bullets,
               SCREEN_WIDTH, GRID_HEIGHT, preview_plant_pos, selected_plant, plant_preview_images,
               plant_game_images, suns, zombie_count, ZOMBIE_MAX, plant_ui_images, GREEN,
               sun_image, sun_value, YELLOW, difficulty, theme):
    """渲染游戏画面"""
    # 绘制完整背景
    screen.blit(background, (0, 0))
    # 绘制音乐按钮
    screen.blit(music_button_img, music_button_rect)

    # 绘制植物
    for plant in plants:
        plant.draw()
    
    # 绘制僵尸
    for zombie in zombies:
        zombie.draw()
    
    # 绘制子弹
    for bullet in bullets:
        bullet.draw()
    
    # 绘制植物选择UI背景
    pygame.draw.rect(screen, (139, 69, 19), (0, 0, SCREEN_WIDTH, GRID_HEIGHT))
    
    # 绘制植物预览
    if preview_plant_pos and selected_plant != 'cz' and plant_preview_images.get(selected_plant):
        preview_img = plant_preview_images[selected_plant]
        if preview_img:
            screen.blit(preview_img, (
                preview_plant_pos[0] - preview_img.get_width()//2,
                preview_plant_pos[1] - preview_img.get_height()//2
            ))
            
    # 绘制植物素材跟随鼠标
    if selected_plant != 'cz' and plant_game_images.get(selected_plant):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        plant_img = plant_game_images[selected_plant]
        screen.blit(plant_img, (
            mouse_x - plant_img.get_width()//2,
            mouse_y - plant_img.get_height()//2
        ))
    
    # 最后绘制阳光，确保在最上层（传入鼠标位置避免重复get_pos）
    mouse_pos = pygame.mouse.get_pos()
    for sun in suns[:]:
        if sun.update(mouse_pos):
            suns.remove(sun)
        else:
            sun.draw()

    # 僵尸数量显示（需每帧渲染，因为数量变化）
    zombie_text = _render_font.render(f'僵尸: {zombie_count}/{ZOMBIE_MAX}', True, (255, 255, 255))
    text_width = zombie_text.get_width()
    screen.blit(zombie_text, (SCREEN_WIDTH - text_width - 20, SCREEN_HEIGHT - 40))
    
    # 绘制植物选择UI
    for i, plant_type in enumerate(['xrk', 'hb', 'wd', 'xdfz', 'cz']):
        if plant_type == 'cz':
            x = SCREEN_WIDTH - 50
        else:
            x = 100 + i * 100
        y = GRID_HEIGHT // 2
        img = plant_ui_images[plant_type]
        screen.blit(img, (x - img.get_width()//2, y - img.get_height()//2))
        
        # 绘制选中高亮
        if selected_plant == plant_type:
            pygame.draw.rect(screen, GREEN, (x - img.get_width()//2 - 5, y - img.get_height()//2 - 5, 
                                          img.get_width() + 10, img.get_height() + 10), 2)
    
    # 显示阳光数量和图片
    screen.blit(sun_image, (10, 10))
    sun_text = _render_font.render(f'{sun_value[0]}', True, YELLOW)
    screen.blit(sun_text, (40, 15))
    
    # 难度和主题使用预渲染文本
    screen.blit(_render_difficulty_texts[difficulty], (SCREEN_WIDTH - 150, 15))
    screen.blit(_render_theme_texts[theme], (SCREEN_WIDTH - 150, 45))

# 游戏主循环
def main(difficulty=1, theme=0):
    """
    游戏主循环
    
    参数:
        difficulty: 难度级别 (0: 简单, 1: 普通, 2: 困难, 3: 测试)
        theme: 游戏主题 (0: 经典, 1: 宇宙, 2: 哈基米)
        
    返回:
        bool: 是否需要重新启动主菜单
    """
    # 初始化游戏状态
    clock = pygame.time.Clock()
    plants = []
    zombies = []
    bullets = []
    suns = []
    zombie_spawn_timer = 0
    sun_spawn_timer = 0
    sun_value = [100]  # 初始阳光100
    selected_plant = None  # 初始不选择任何植物
    plant_prices = {'xrk': 50, 'hb': 175, 'wd': 100, 'xdfz': 100}  # 植物价格
    
    # 根据难度设置参数
    if difficulty == 0:  # 简单
        ZOMBIE_MAX = 8 # 僵尸数量
        zombie_speed = 0.5 # 僵尸速度
    elif difficulty == 1:  # 普通
        ZOMBIE_MAX = 10
        zombie_speed = 0.8
    elif difficulty == 2:  # 困难
        ZOMBIE_MAX = 14
        zombie_speed = 1.2
    else:  # 测试
        ZOMBIE_MAX = 1
        zombie_speed = 0.8
    
    first_zombie_delay = 600  # 第一只僵尸延迟10秒（600帧）
    
    active_music_list = []
    current_music_idx_for_active_list = 0
    
    # 根据主题设置背景和音乐
    if theme == 0:  # 经典主题
        background = load_image('back.png')
        active_music_list = BASE_MUSIC_FILES
        current_music_idx_for_active_list = 0 # fight.mp3
    elif theme == 1:  # 宇宙主题
        background = load_image('space.png')
        active_music_list = BASE_MUSIC_FILES
        current_music_idx_for_active_list = 3 # space.mp3 (索引3对应BASE_MUSIC_FILES中的space.mp3)
    elif theme == 2: # 哈基米主题
        background = load_image('gback.png')
        active_music_list = HAKIMI_MUSIC_FILES
        current_music_idx_for_active_list = 0 # g1.mp3
    
    # 加载游戏资源
    plant_ui_images = {
        'xrk': load_image('xrk1.png', 1.0), 
        'hb': load_image('hb1.png', 1.0), 
        'wd': load_image('wd1.png', 1.0), 
        'xdfz': load_image('xdfz1.png', 1.0),  # 坚果墙UI图标保持原样
        'cz': load_image('cz.png', 0.17),
    }
    
    plant_game_images = {
        'xrk': load_image('xrk.png', 1.0),
        'hb': load_image('hb.png', 1.0),
        'wd': load_image('wd.png', 1.0),
        'xdfz': load_image('xdfz.png', 1.3),  # 坚果墙游戏内图像放大      
        'cz': load_image('cz.png', 0.17),
    }
    
    plant_preview_images = {
        'xrk': load_image('xrkz.png', 1.0),
        'hb': load_image('hbz.png', 1.0),
        'wd': load_image('wdz.png', 1.0),
        'xdfz': load_image('xdfzz.png', 1.3),  # 坚果墙预览图像放大
    }
    
    sun_image = load_image('sun.png', 0.3)
    selected_plant_highlight = None
    preview_plant_pos = None
    
    # 音乐按钮设置
    music_button_rect = pygame.Rect(20, SCREEN_HEIGHT - 50, 40, 40)
    music_button_img = load_image('music.png', 0.8)
    
    # 播放初始音乐
    try:
        if active_music_list: # 确保列表不为空
            initial_music_path = os.path.join(os.path.dirname(__file__), 'music', active_music_list[current_music_idx_for_active_list])
            pygame.mixer.music.load(initial_music_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
            print(f"初始音乐: {active_music_list[current_music_idx_for_active_list]}")
        else:
            print("警告: 当前主题的音乐列表为空，无法播放初始音乐。")
    except Exception as e:
        print(f"无法加载初始音乐文件: {initial_music_path if 'initial_music_path' in locals() else '未知'}, error: {e}")
    
    # 游戏主循环
    running = True
    zombie_count = 0  # 已生成僵尸计数
    while running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return False  # 直接退出游戏
            elif event.type == pygame.KEYDOWN:
                selected_plant = handle_keydown(event, selected_plant)
            elif event.type == pygame.MOUSEMOTION:
                preview_plant_pos = handle_mouse_motion(event, GRID_HEIGHT, selected_plant, GRID_COL_WIDTH, GRID_COLS, LAWN_HEIGHT, LAWN_ROWS, preview_plant_pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    current_music_idx_for_active_list, selected_plant = handle_mouse_click(
                        event, music_button_rect, current_music_idx_for_active_list, active_music_list, 
                                      GRID_HEIGHT, plant_ui_images, selected_plant, SCREEN_WIDTH,
                                      suns, plants, plant_prices, sun_value, GRID_COL_WIDTH, GRID_COLS,
                        LAWN_HEIGHT, LAWN_ROWS, sounds, theme
                    )
        
        # 生成游戏对象
        zombie_spawn_timer, zombie_count, first_zombie_delay = spawn_zombies(
            zombie_spawn_timer, zombie_count, ZOMBIE_MAX, 
            GRID_HEIGHT, LAWN_HEIGHT, LAWN_ROWS, zombie_speed, zombies, first_zombie_delay)
        
        sun_spawn_timer = spawn_suns(sun_spawn_timer, SCREEN_WIDTH, GRID_HEIGHT, sun_value, suns)
        
        # 更新游戏状态
        update_plants(plants, zombies, bullets, suns, sun_value, sounds)
        restart = update_zombies(zombies, plants)
        if restart:
            return True  # 重新启动主菜单
        update_bullets(bullets, zombies, SCREEN_WIDTH, sounds)
        
        # 检查胜利条件
        if check_victory(zombie_count, ZOMBIE_MAX, zombies):
            if show_victory_screen():
                # 重新启动主菜单
                return True
            else:
                return False  # 直接退出游戏
        
        # 渲染游戏画面
        render_game(screen, background, music_button_img, music_button_rect, plants, zombies, bullets,
                   SCREEN_WIDTH, GRID_HEIGHT, preview_plant_pos, selected_plant, plant_preview_images,
                   plant_game_images, suns, zombie_count, ZOMBIE_MAX, plant_ui_images, GREEN,
                   sun_image, sun_value, YELLOW, difficulty, theme)
        
        pygame.display.flip()
        clock.tick(60)
    
    return False  # 默认直接退出游戏

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()
