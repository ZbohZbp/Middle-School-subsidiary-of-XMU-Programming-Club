"""
植物大战僵尸 - 关卡2
玩家通过WASD控制豌豆射手移动来击败僵尸
可以通过击杀僵尸获得阳光，进而升级豌豆射手
"""

import pygame
import random
import sys
import os
import time



# 初始化pygame
pygame.init()
pygame.font.init()
font = pygame.font.SysFont('SimSun', 20)  # 全局字体设置

# 屏幕设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("我是豌豆射手")

# 颜色定义
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)  # 添加黑色用于弹窗背景

# 显示提示弹窗
def show_input_tip():
    """显示输入法提示弹窗"""
    # 创建半透明背景
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # 黑色半透明背景
    
    # 创建弹窗
    popup_width, popup_height = 400, 200
    popup_x = (SCREEN_WIDTH - popup_width) // 2
    popup_y = (SCREEN_HEIGHT - popup_height) // 2
    popup = pygame.Surface((popup_width, popup_height))
    popup.fill(WHITE)
    
    # 创建提示文本
    tip_font = pygame.font.SysFont('SimSun', 24)
    tip_text = tip_font.render("若无法控制请切换至英文输入法", True, BLACK)
    close_text = tip_font.render("点击任意位置关闭弹窗", True, BLACK)
    
    # 计算文本位置
    tip_x = (popup_width - tip_text.get_width()) // 2
    tip_y = popup_height // 2 - tip_text.get_height()
    close_x = (popup_width - close_text.get_width()) // 2
    close_y = popup_height // 2 + 20
    
    # 绘制文本到弹窗
    popup.blit(tip_text, (tip_x, tip_y))
    popup.blit(close_text, (close_x, close_y))
    
    # 绘制弹窗到屏幕
    screen.blit(overlay, (0, 0))
    screen.blit(popup, (popup_x, popup_y))
    pygame.display.flip()
    
    # 等待用户点击
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
            elif event.type == pygame.KEYDOWN:
                waiting = False

# 音效管理类
class SoundManager:
    def __init__(self):
        self.is_playing_important = False  # 是否正在播放重要音效
        self.important_sound_channel = None  # 重要音效的声道
        self.important_sound_end_time = 0  # 重要音效结束时间
        self.zombie_death_channels = [pygame.mixer.Channel(i) for i in range(1, 5)]  # 为僵尸死亡音效预留4个通道
        self.next_zombie_channel = 0  # 下一个用于播放僵尸死亡音效的通道索引
    
    def play_normal_sound(self, sound):
        """播放普通音效，如果重要音效正在播放则不播放"""
        if sound and not self.is_playing_important:
            sound.set_volume(0.4)  # 普通音效音量增加到0.4（原为0.15）
            sound.play()
    
    def play_important_sound(self, sound):
        """播放重要音效（超进化、超级攻击、升级），会打断其他音效"""
        if sound:
            current_time = pygame.time.get_ticks()
            if self.is_playing_important and current_time < self.important_sound_end_time:
                return False
            
            sound.set_volume(1.0) # Pygame音量范围0.0-1.0
            
            if not self.important_sound_channel:
                self.important_sound_channel = pygame.mixer.Channel(0)
            
            self.important_sound_channel.set_volume(1.0) # 确保声道音量也是1.0
            self.important_sound_channel.play(sound)
            
            # 计算音效大致结束时间 (这里可以根据实际音效长度调整，如果知道的话)
            # Pygame Sound对象没有直接获取长度的方法，除非是music模块加载的
            # 假设重要音效通常较短，或允许被打断
            sound_length_ms = 2000 # 默认2秒，或根据实际情况调整
            try:
                # 如果是 pygame.mixer.SoundType, 它没有 get_length()
                # 如果你知道它是从文件加载的，并且需要精确长度，可能需要在加载时获取
                pass # sound.get_length() 不是标准Sound对象方法
            except AttributeError:
                pass

            self.important_sound_end_time = current_time + sound_length_ms
            self.is_playing_important = True
            pygame.time.set_timer(pygame.USEREVENT + 1, sound_length_ms)
            return True
        return False
    
    def play_zombie_death_sound(self, sound):
        """播放僵尸死亡音效，可以与重要音效同时播放，且多个僵尸死亡音效可以同时播放"""
        if sound:
            # 设置音量
            sound.set_volume(0.4) # 僵尸死亡音效音量增加到0.4（原为0.15）
            
            # 使用轮转的通道播放死亡音效
            channel = self.zombie_death_channels[self.next_zombie_channel]
            channel.play(sound)
            
            # 更新下一个通道索引
            self.next_zombie_channel = (self.next_zombie_channel + 1) % len(self.zombie_death_channels)
    
    def update(self):
        """更新音效管理器状态"""
        current_time = pygame.time.get_ticks()
        if self.is_playing_important and current_time >= self.important_sound_end_time:
            self.is_playing_important = False

# 创建音效管理器实例
sound_manager = SoundManager()

# 资源加载函数
def load_image(name, scale=1, alpha=None):
    """加载游戏图片资源"""
    try:
        if name in ['back.png', 'space.png', 'gback.png']:
            image_path = os.path.join(os.path.dirname(__file__), 'background', name)
        elif name in ['sun.png', 'trophy.png', 'failure.png', 'ha.png', 'music.png']:
            image_path = os.path.join(os.path.dirname(__file__), 'effects', name)
        elif name in ['zombie.png', 'hurtzombie.png', 'slowzombie.png']:
            image_path = os.path.join(os.path.dirname(__file__), 'zombies', name)
        elif name in ['Peashooter.gif', 'Repeater.gif', 'GatlingPea.gif']:
            image_path = os.path.join(os.path.dirname(__file__), 'plants', 'peashooter', name)
        elif name in ['wdzd.png', 'wdzd2.png', 'wdzd1.gif', 'g.png']:
            image_path = os.path.join(os.path.dirname(__file__), 'plants', 'peashooter', name)
        else:
            image_path = os.path.join(os.path.dirname(__file__), name)
            if not os.path.exists(image_path):
                image_path = name  # 尝试直接加载文件名
                
        image = pygame.image.load(image_path)
        
        # 缩放图片
        if scale != 1:
            width = int(image.get_width() * scale)
            height = int(image.get_height() * scale)
            image = pygame.transform.scale(image, (width, height))
        
        # 设置透明度
        if alpha is not None:
            image.set_alpha(int(alpha * 255))
            
        return image
    except Exception as e:
        # 仅在发生严重错误时输出
        print(f"图片加载错误，文件: {name}, 错误: {e}")
        placeholder = pygame.Surface((50, 50), pygame.SRCALPHA)
        placeholder.fill((255, 0, 0, 128))  # 红色半透明占位符
        return placeholder

# 音效加载
def load_sound(name):
    """加载游戏音效"""
    try:
        sound_path = os.path.join(os.path.dirname(__file__), 'sounds', name)
        if not os.path.exists(sound_path):
            print(f"警告: 音效文件 {name} 不存在")
            return None
        
        sound = pygame.mixer.Sound(sound_path)
        return sound
    except Exception as e:
        print(f"加载音效 {name} 时出错: {e}")
        return None

# 加载文件夹中的所有音效
def load_sounds_from_folder(folder_name):
    """加载指定文件夹中的所有音效文件"""
    sounds_dict = {}
    try:
        folder_path = os.path.join(os.path.dirname(__file__), 'sounds', folder_name)
        if os.path.exists(folder_path):
            for file_name in os.listdir(folder_path):
                if file_name.endswith(('.mp3', '.ogg', '.wav')):
                    sound_path = os.path.join(folder_path, file_name)
                    try:
                        sound = pygame.mixer.Sound(sound_path)
                        sounds_dict[file_name] = sound
                        print(f"成功加载{folder_name}音效: {file_name}")
                    except Exception as e:
                        print(f"加载音效 {file_name} 时出错: {e}")
        else:
            print(f"警告: 音效文件夹 {folder_path} 不存在")
    except Exception as e:
        print(f"加载音效文件夹 {folder_name} 时出错: {e}")
    return sounds_dict

# 游戏音效
sounds = {
    'plant': load_sound('by_plant/plant.ogg'),      # 种植植物音效
    'win': load_sound('winmusic.ogg'),     # 胜利音效
    'eaten': load_sound('by_zombie/eaten.ogg'),      # 植物被吃掉音效
    'peashoot': load_sound('by_plant/peashoot.mp3'), # 豌豆发射音效
    'hit': load_sound('by_zombie/hit.mp3'),          # 僵尸受击音效
    'points': load_sound('by_plant/points.ogg'),    # 阳光收集音效
    'upgrade': load_sound('by_plant/points.ogg'),   # 升级音效 (暂用points.ogg代替)
    'died': load_sound('by_zombie/died.mp3'),        # 僵尸死亡音效
    'brief_enhancement': load_sound('brief_enhancement/enhance_1.mp3'),  # 短暂强化型植物音效
    'full_screen_attack': load_sound('full_screen_attack/attack_1.mp3'),  # 全屏攻击型植物音效
    'haqi': load_sound('by_plant/haqi.mp3')         # 哈基米全屏攻击音效
}

# 加载升级语音
upgrade_sounds = {}
for i in range(1, 4):  # 加载sj1.mp3, sj2.mp3, sj3.mp3
    sound_path = os.path.join(os.path.dirname(__file__), 'sounds', 'upgrade', f'sj{i}.mp3')
    if os.path.exists(sound_path):
        try:
            upgrade_sounds[i] = pygame.mixer.Sound(sound_path)
            print(f"成功加载升级语音: sj{i}.mp3")
        except Exception as e:
            print(f"加载升级语音 sj{i}.mp3 时出错: {e}")
    else:
        print(f"警告: 升级语音文件 sj{i}.mp3 不存在")

# 加载超进化和超级攻击的随机语音
brief_enhancement_sounds = load_sounds_from_folder('brief_enhancement')
full_screen_attack_sounds = load_sounds_from_folder('full_screen_attack')

# 主题音乐定义
CLASSIC_MUSIC_L2 = 'fight.mp3'
SPACE_MUSIC_L2 = 'space.mp3'
HAKIMI_MUSIC_FILES_L2 = ['g1.mp3', 'g2.mp3', 'g3.mp3', 'g4.mp3']

# 加载背景图片
background = load_image('back.png')

# 音乐设置
music_files = ['fight.wav', 'peaceful.wav', 'qidong.wav', 'space.wav']
current_music_index = 0
pygame.mixer.music.set_volume(0.5)

# 背景音乐
music_file_level2 = os.path.join(os.path.dirname(__file__), 'music', 'fight.mp3') # 关卡2固定使用战斗音乐
try:
    pygame.mixer.music.load(music_file_level2)
except:
    print(f"无法加载音乐文件: {music_file_level2}")

# 玩家控制的豌豆射手类
class PlayerPeashooter:
    def __init__(self, x, y, theme_index=0):
        # 初始化网格位置
        self.grid_x = 0
        self.grid_y = 2
        self.theme_index = theme_index # 保存主题索引
        
        # 计算实际坐标
        self.x = self.grid_x * (SCREEN_WIDTH // 9) + (SCREEN_WIDTH // 18)  # 9列，居中
        self.y = 140 + self.grid_y * 100  # 每行100像素高，整体下移40像素(原30+10)
        
        self.level = 1  # 1: 豌豆射手, 2: 双发射手, 3: 机枪射手
        self.images = {
            1: load_image('Peashooter.gif', 1.0),
            2: load_image('Repeater.gif', 1.0),
            3: load_image('GatlingPea.gif', 1.0)
        }
        self.image = self.images[self.level]
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.shoot_cooldown = 0
        self.cooldown_max = {1: 30, 2: 20, 3: 13}  # 修改机枪射手冷却时间从10增加到15
        self.shoot_count = {1: 1, 2: 2, 3: 3}  # 不同等级的射击数量
        self.bullet_damage = 20  # 基础子弹伤害
        self.time_played = 0  # 游戏时间计时器（帧数）
        self.power_up_interval = 1200  # 每20秒（1200帧）提升一次能力
        self.power_level = 0  # 能力提升等级
        self.power_up_effect_timer = 0  # 强化特效计时器
        self.countdown_display = 0  # 升级倒计时显示
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        self.kills = 0  # 击杀数
        self.sun_value = 0  # 阳光值
        self.move_cooldown = 0  # 移动冷却
        
        # 超进化状态相关
        self.super_mode = False  # 是否处于超进化状态
        self.super_timer = 0  # 超进化状态计时器（帧数）
        self.super_duration = 60  # 超进化状态持续时间（1秒 = 60帧）
        self.bullet_alternator = 0  # 用于交替子弹类型
        self.super_cost = 200  # 初始超进化消耗200阳光
        self.super_cost_increment = 50  # 每次使用后增加50阳光
        self.super_max_cost = 400  # 超进化最高价格为400
        self.super_use_count = 0  # 记录使用次数
        self.double_column = False  # 是否发射双列子弹
        
        # 新增：全屏发射子弹功能
        self.super_attack_cooldown = 0  # 全屏攻击冷却时间
        self.super_attack_cooldown_max = 600  # 10秒冷却时间 (60帧/秒 * 10秒)
        
        # ha.png 特效相关变量
        self.ha_image = load_image('ha.png') # 加载ha.png
        if self.ha_image:
            self.ha_image_rect = self.ha_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        else: # 如果图片加载失败，提供一个降级方案
            self.ha_image_rect = pygame.Rect(0,0,0,0) 
        self.show_ha_effect = False
        self.ha_effect_timer = 0
        self.ha_effect_alpha = 0
        self.ha_effect_total_duration = 60 # 1秒 (60 FPS)
        self.ha_effect_fade_duration = 30  # 0.5秒渐显/渐隐
        
    def handle_keydown(self, key):
        """处理按键按下事件"""
        if key == 112:  # P键
            print("检测到P键按下，尝试触发全屏攻击")
            # 触发 ha.png 特效
            self.show_ha_effect = True
            self.ha_effect_timer = 0
            self.ha_effect_alpha = 0 # 开始时完全透明

            if self.sun_value >= 100:
                self.sun_value -= 100
                return self.activate_super_attack()
            else:
                print(f"阳光不足，无法使用全屏攻击，需要100阳光")
                return False # 即使阳光不足，ha.png效果也会显示
                
        # 如果按下U键，尝试触发超进化
        elif key == 117:  # U键
            print("检测到U键按下，尝试激活超级模式")
            if self.level == 3:  # 只有等级3(机枪射手)才能触发超级模式
                return self.activate_super_mode()  # 返回是否成功激活
            return False
        
        if self.move_cooldown <= 0:
            moved = False
            
            # 处理移动
            if key == 119:  # W键
                if self.grid_y > 0:
                    self.grid_y -= 1
                    moved = True
            elif key == 115:  # S键
                if self.grid_y < 4:  # 5行，索引0-4
                    self.grid_y += 1
                    moved = True
            elif key == 97:  # A键
                if self.grid_x > 0:
                    self.grid_x -= 1
                    moved = True
            elif key == 100:  # D键
                if self.grid_x < 8:  # 9列，索引0-8
                    self.grid_x += 1
                    moved = True
            
            if moved:
                # 更新实际坐标
                self.x = self.grid_x * (SCREEN_WIDTH // 9) + (SCREEN_WIDTH // 18)
                self.y = 140 + self.grid_y * 100
                self.move_cooldown = 10  # 设置移动冷却时间
                return True
                
        return False
        
    def update(self, bullets):
        # 如果移动了，更新坐标
        self.x = self.grid_x * (SCREEN_WIDTH // 9) + (SCREEN_WIDTH // 18)
        self.y = 140 + self.grid_y * 100
        
        # 更新移动冷却
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
        
        # 更新碰撞矩形
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        
        # 更新游戏时间计时器
        self.time_played += 1
        
        # 更新升级倒计时显示
        self.countdown_display = self.power_up_interval - (self.time_played % self.power_up_interval)
        
        # 检查是否需要提升能力（仅限机枪射手）
        if self.level == 3 and self.time_played % self.power_up_interval == 0 and self.time_played > 0:
            self.power_level += 1
            # 每次提升减少1帧冷却时间，最低到5帧
            new_cooldown = max(5, self.cooldown_max[3] - self.power_level)
            self.cooldown_max[3] = new_cooldown
            # 每次提升增加1点伤害
            self.bullet_damage += 1
            # 激活强化特效
            self.power_up_effect_timer = 60  # 1秒特效
            print(f"机枪射手能力提升！等级: {self.power_level}, 冷却时间: {new_cooldown}帧, 伤害: {self.bullet_damage}")
            
            # 播放对应等级的升级语音
            sound_index = min(self.power_level, 3)  # 最多播放到第3个语音
            if sound_index in upgrade_sounds and upgrade_sounds[sound_index]:
                sound_manager.play_important_sound(upgrade_sounds[sound_index])
            else:
                # 如果没有对应等级的语音，播放普通升级音效
                if sounds['upgrade']:
                    sound_manager.play_important_sound(sounds['upgrade'])
        
        # 更新超进化状态
        if self.super_mode:
            self.super_timer -= 1
            if self.super_timer <= 0:
                self.super_mode = False
                print("超级模式结束！")
                # 恢复正常状态
                Bullet.current_speed = Bullet.default_speed
        
        # 更新强化特效计时器
        if self.power_up_effect_timer > 0:
            self.power_up_effect_timer -= 1
        
        # 自动射击
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        else:
            self.shoot(bullets)
            # 根据是否处于超进化状态决定射击冷却时间
            if self.super_mode:
                self.shoot_cooldown = self.cooldown_max[self.level] // 2  # 超进化状态下射击间隔减半
            else:
                self.shoot_cooldown = self.cooldown_max[self.level]

        # 更新 ha.png 特效
        if self.show_ha_effect:
            self.ha_effect_timer += 1
            if self.ha_effect_timer <= self.ha_effect_fade_duration: # 渐显阶段
                self.ha_effect_alpha = (self.ha_effect_timer / self.ha_effect_fade_duration) * 255
            elif self.ha_effect_timer <= self.ha_effect_total_duration: # 渐隐阶段
                # 计算渐隐进度 (从0到1)
                fade_out_progress = (self.ha_effect_timer - self.ha_effect_fade_duration) / self.ha_effect_fade_duration
                self.ha_effect_alpha = (1 - fade_out_progress) * 255
            else: # 特效结束
                self.show_ha_effect = False
                self.ha_effect_alpha = 0
            
            self.ha_effect_alpha = max(0, min(255, int(self.ha_effect_alpha))) #确保alpha在0-255之间
    
    def shoot(self, bullets):
        # 根据等级发射不同数量的豌豆
        count = self.shoot_count[self.level]
        spacing = 10  # 豌豆之间的间距
        
        double_column = self.super_mode and self.kills >= 100
        columns = [20] if not double_column else [10, 30]
        
        bullet_image_name = 'wdzd.png' # 默认子弹
        if self.theme_index == 2: # 哈基米主题索引为2
            bullet_image_name = 'g.png'
        elif self.super_mode and self.level == 3: # 机枪射手超进化使用特殊子弹
            bullet_image_name = 'wdzd1.gif'
        # 可根据需要为其他等级的超进化模式或其他特定条件改变 bullet_image_name
        # 例如，如果普通豌豆超进化也用特殊子弹，在这里添加逻辑

        for column in columns:
            for i in range(count):
                offset = (i - (count-1)/2) * spacing
                bullets.append(Bullet(self.x + column, self.y + offset, bullet_image_name))
        
        if sounds['peashoot']:
            sound_manager.play_normal_sound(sounds['peashoot'])
    
    def try_upgrade(self):
        # 尝试升级
        if self.level < 3 and self.sun_value >= self.level * 100:
            self.sun_value -= self.level * 100
            self.level += 1
            self.image = self.images[self.level]
            self.width = self.image.get_width()
            self.height = self.image.get_height()
            
            # 播放升级音效
            if sounds['upgrade']:
                sound_manager.play_important_sound(sounds['upgrade'])
            
            return True
        return False
    
    def activate_super_mode(self):
        """激活超进化状态，需要消耗阳光，且每次使用后价格上涨"""
        # 检查阳光是否足够
        if self.sun_value >= self.super_cost:
            self.sun_value -= self.super_cost  # 消耗阳光
            self.super_mode = True
            self.super_timer = self.super_duration
            print(f"超级模式激活！消耗{self.super_cost}阳光，持续时间: {self.super_duration}帧")
            
            # 增加下一次超进化的价格，但不超过最高限制
            self.super_use_count += 1
            self.super_cost = min(self.super_cost + self.super_cost_increment, self.super_max_cost)
            
            # 加快子弹速度
            Bullet.current_speed = Bullet.default_speed * 2
            
            # 播放随机短暂强化音效
            if brief_enhancement_sounds:
                # 从字典中随机选择一个音效播放
                sound_keys = list(brief_enhancement_sounds.keys())
                if sound_keys:
                    random_key = random.choice(sound_keys)
                    try:
                        sound_manager.play_important_sound(brief_enhancement_sounds[random_key])
                    except:
                        print(f"无法播放短暂强化音效: {random_key}")
            elif sounds['brief_enhancement']:  # 如果没有找到随机音效，使用默认音效
                try:
                    sound_manager.play_important_sound(sounds['brief_enhancement'])
                except:
                    print("无法播放短暂强化型植物音效")
                    
            return True
        else:
            print(f"阳光不足，无法激活超级模式，需要{self.super_cost}阳光")
            return False
    
    def activate_super_attack(self):
        """激活全屏攻击，发射子弹覆盖所有行"""
        print("启动全屏攻击！发射子弹覆盖所有行，消耗100阳光")
        
        temp_bullets = []
        for row in range(5):
            row_y = 140 + row * 100
            bullet_count = 5
            for i in range(bullet_count):
                x_pos = self.x + 20
                y_offset = (i - (bullet_count-1)/2) * 15
                temp_bullets.append(Bullet(x_pos, row_y + y_offset, 'wdzd1.gif'))
        
        # 选择并播放全屏攻击音效
        sound_to_play = None
        
        if self.theme_index == 2: # 哈基米主题
            if sounds.get('haqi'):
                sound_to_play = sounds['haqi']
                print("哈基米主题：使用 haqi.mp3 作为全屏攻击音效")
            else:
                print("警告: 哈基米主题的全屏攻击音效 haqi.mp3 未加载，尝试使用默认音效。")

        if not sound_to_play: # 非哈基米主题或haqi.mp3加载失败
            # 尝试从 ['attack_4.mp3', 'attack_5.mp3'] 中随机选择一个可用的音效
            preferred_super_sounds_names = ['attack_4.mp3', 'attack_5.mp3']
            available_preferred_sounds = [s_name for s_name in preferred_super_sounds_names if s_name in full_screen_attack_sounds and full_screen_attack_sounds[s_name]]

            if available_preferred_sounds:
                chosen_sound_name = random.choice(available_preferred_sounds)
                sound_to_play = full_screen_attack_sounds[chosen_sound_name]
                print(f"从优先列表随机选择音效 {chosen_sound_name} 作为全屏攻击音效")

            # 如果优先列表中的音效都不可用或列表为空，则回退到使用随机brief_enhancement音效
            if not sound_to_play and brief_enhancement_sounds:
                # 从所有可用的brief_enhancement音效中选择（排除已尝试的优先音效，如果它们在brief_enhancement_sounds中）
                # 或者更简单：如果上面没选到，就从所有brief_enhancement里随机选
                available_brief_enhancement_keys = [key for key in brief_enhancement_sounds.keys() if brief_enhancement_sounds[key]] # 确保sound对象存在
                if available_brief_enhancement_keys:
                    random_key = random.choice(available_brief_enhancement_keys)
                    sound_to_play = brief_enhancement_sounds[random_key]
                    print(f"从brief_enhancement文件夹随机选择音效 {random_key} 作为全屏攻击音效")
            
            if not sound_to_play and sounds.get('full_screen_attack'): # 默认全屏攻击音效
                sound_to_play = sounds['full_screen_attack']
                print("使用默认 full_screen_attack.mp3 作为全屏攻击音效")

        if sound_to_play:
            sound_manager.play_important_sound(sound_to_play)
        else:
            print("警告: 无法找到合适的超级攻击音效，播放默认射击音效。")
            if sounds['peashoot']:
                sound_manager.play_normal_sound(sounds['peashoot'])
        
        return temp_bullets
    
    def draw(self):
        # 绘制植物本体
        screen.blit(self.image, (self.x - self.width//2, self.y - self.height//2))
        
        # 如果处于超进化状态，添加闪光效果
        if self.super_mode:
            # 创建半透明的闪光效果
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            glow_color = (255, 255, 0, 128)  # 黄色半透明
            pygame.draw.ellipse(glow_surf, glow_color, (0, 0, self.width + 20, self.height + 20))
            
            # 根据超进化剩余时间闪烁
            if self.super_timer % 10 < 5:  # 每10帧闪烁一次
                screen.blit(glow_surf, (self.x - (self.width + 20)//2, self.y - (self.height + 20)//2))
            
            # 显示超进化状态剩余时间
            progress = self.super_timer / self.super_duration
            bar_width = 50
            pygame.draw.rect(screen, (50, 50, 50), (self.x - bar_width//2, self.y - self.height//2 - 10, bar_width, 5))
            pygame.draw.rect(screen, (255, 215, 0), (self.x - bar_width//2, self.y - self.height//2 - 10, int(bar_width * progress), 5))
        
        # 如果正在显示强化特效
        if self.power_up_effect_timer > 0:
            # 创建半透明的闪光效果
            glow_surf = pygame.Surface((self.width + 30, self.height + 30), pygame.SRCALPHA)
            glow_color = (0, 255, 0, 128)  # 绿色半透明
            pygame.draw.ellipse(glow_surf, glow_color, (0, 0, self.width + 30, self.height + 30))
            
            # 根据特效剩余时间闪烁
            if self.power_up_effect_timer % 6 < 3:  # 快速闪烁
                screen.blit(glow_surf, (self.x - (self.width + 30)//2, self.y - (self.height + 30)//2))
            
            # 显示升级文字
            upgrade_font = pygame.font.SysFont('SimSun', 16)
            upgrade_text = upgrade_font.render(f"+1 强化!", True, (0, 255, 0))
            screen.blit(upgrade_text, (self.x - upgrade_text.get_width()//2, self.y - self.height//2 - 20))
        
        # 如果是机枪射手，显示升级倒计时
        if self.level == 3:
            # 计算倒计时秒数
            countdown_seconds = self.countdown_display // 60
            # 只有在倒计时小于等于5秒时才显示数字
            if countdown_seconds <= 5:
                countdown_font = pygame.font.SysFont('SimSun', 24)
                countdown_text = countdown_font.render(f"{countdown_seconds}", True, (255, 255, 0))
                screen.blit(countdown_text, (self.x - countdown_text.get_width()//2, self.y - self.height - 30))

        # 绘制 ha.png 特效
        if self.show_ha_effect and self.ha_image and self.ha_effect_alpha > 0:
            temp_ha_image = self.ha_image.copy()
            temp_ha_image.set_alpha(int(self.ha_effect_alpha))
            screen.blit(temp_ha_image, self.ha_image_rect)

# 僵尸类
class Zombie:
    def __init__(self, row=None, health_multiplier=1.0):
        self.x = SCREEN_WIDTH
        # 根据行号计算y坐标，与豌豆射手使用相同的行高计算方式
        if row is None:
            row = random.randint(0, 4)  # 随机选择一行(0-4)
        self.row = row
        self.y = 140 + row * 100  # 与豌豆射手使用相同的行高，整体下移40像素
        self.base_health = 100  # 基础血量
        self.health = int(self.base_health * health_multiplier)  # 根据倍率调整血量
        self.max_health = self.health  # 记录最大血量，用于显示血条
        self.speed = 1
        self.image = load_image('zombie.png', 1.0)
        self.hurt_image = load_image('hurtzombie.png', 1.0)
        self.hit_timer = 0
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        # 创建一个更大的碰撞矩形
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        
    def update(self):
        self.x -= self.speed
        # 更新碰撞矩形
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        
        if self.hit_timer > 0:
            self.hit_timer -= 1
            
        return self.x < 0  # 返回是否到达左边界
    
    def draw(self):
        if self.hit_timer > 0:
            screen.blit(self.hurt_image, (self.x - self.width//2, self.y - self.height//2))
        else:
            screen.blit(self.image, (self.x - self.width//2, self.y - self.height//2))
            
        # 绘制血条
        bar_width = 50
        bar_height = 5
        bar_x = self.x - bar_width//2
        bar_y = self.y - self.height//2 - 15
        
        # 血条背景
        pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # 血条前景（根据当前血量比例）
        health_ratio = max(0, self.health / self.max_health)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

# 子弹类
class Bullet:
    default_speed = 4
    current_speed = default_speed
    def __init__(self, x, y, bullet_type='wdzd.png'):
        self.x = x
        self.y = y  # 使用豌豆射手的准确y坐标
        self.speed = Bullet.current_speed  # 使用当前全局速度而不是默认速度
        self.image = load_image(bullet_type, 0.8)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        # 创建一个更大的碰撞矩形，提高碰撞检测的准确性
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height, self.width, self.height*2)
        
    def update(self):
        self.x += self.speed
        # 更新碰撞矩形
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height, self.width, self.height*2)
        return self.x > SCREEN_WIDTH  # 返回是否超出屏幕
    
    def draw(self):
        screen.blit(self.image, (self.x - self.width//2, self.y - self.height//2))

# 阳光类
class Sun:
    def __init__(self, x, y, value=25):
        self.x = x
        self.y = y
        self.value = value
        self.speed = 1 # Speed for falling, if we re-introduce falling later
        self.image = load_image('sun.png', 0.5)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        # self.lifetime = 300 # 移除 lifetime，不再自动收集
        self.collected = False
        self.clicked_collected = False # 标记是否通过点击收集
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        self.target_x = 50
        self.target_y = 15
        self.move_speed = 15
        self.reached_target = False
        
    def update(self):
        # self.lifetime -= 1 # 移除 lifetime 相关的更新
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        
        # 移除基于 lifetime 的自动收集逻辑
        # if self.lifetime <= 0 and not self.collected:
        #     self.collected = True
        #     if sounds['points']:
        #         sound_manager.play_normal_sound(sounds['points'])
        
        if self.collected and self.clicked_collected: # 只有通过点击收集的阳光才会移动
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = (dx**2 + dy**2)**0.5
            
            if distance < 5:
                if not self.reached_target:
                    self.reached_target = True
                    return True # 表示已到达目标并可以被主循环移除和增加阳光值
                return False # 已经到达，等待被移除
            else:
                if distance > 0:
                    self.x += dx/distance * self.move_speed
                    self.y += dy/distance * self.move_speed
        
        return False # 默认情况下，阳光停留在原地，除非被点击并到达目标
    
    def draw(self):
        # 无论是否收集，都绘制阳光，直到它到达目标位置
        screen.blit(self.image, (self.x - self.width//2, self.y - self.height//2))

# 显示胜利画面
def show_victory_screen():
    win_image = load_image('trophy.png', 1.0)
    if sounds['win']:
        sound_manager.play_important_sound(sounds['win'])
    
    while True:
        screen.blit(win_image, (SCREEN_WIDTH//2 - win_image.get_width()//2, SCREEN_HEIGHT//2 - win_image.get_height()//2))
        
        # 显示返回主菜单提示
        back_text = font.render("点击任意位置返回主菜单", True, WHITE)
        screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, SCREEN_HEIGHT//2 + 100))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                return True

# 显示失败画面
def show_failure_screen():
    failure_image = load_image('failure.png', 1.0)
    if sounds['eaten']:
        sound_manager.play_important_sound(sounds['eaten'])
    
    while True:
        screen.blit(failure_image, (SCREEN_WIDTH//2 - failure_image.get_width()//2, SCREEN_HEIGHT//2 - failure_image.get_height()//2))
        
        # 显示返回主菜单提示
        back_text = font.render("点击任意位置返回主菜单", True, WHITE)
        screen.blit(back_text, (SCREEN_WIDTH//2 - back_text.get_width()//2, SCREEN_HEIGHT//2 + 100))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                return True

# 主游戏函数
def level2(difficulty=1, theme=0, relax_mode=True):
    """
    关卡2主函数
    
    参数:
        difficulty: 难度级别 (0: 简单, 1: 普通, 2: 困难, 3: 测试)
        theme: 游戏主题 (0: 经典, 1: 宇宙, 2: 哈基米)
        relax_mode: 是否为解压模式（默认开启）
        
    返回:
        bool: 是否需要重新启动主菜单
    """
    # 显示输入法提示弹窗
    show_input_tip()
    
    # 根据难度设置胜利条件
    if relax_mode:
        ZOMBIE_MAX = 250 # 解压模式
        base_zombie_speed = 0.5
        base_spawn_rate = 120
    elif difficulty == 0:  # 简单
        ZOMBIE_MAX = 100 # 简单难度
        base_zombie_speed = 0.8
        base_spawn_rate = 180
    elif difficulty == 1:  # 普通
        ZOMBIE_MAX = 150 # 普通难度
        base_zombie_speed = 1.0
        base_spawn_rate = 120
    elif difficulty == 2:  # 困难
        ZOMBIE_MAX = 200 # 困难难度 (保持上一轮的200)
        base_zombie_speed = 1.2
        base_spawn_rate = 90
    else:  # 测试 (difficulty == 3)
        ZOMBIE_MAX = 50 # 保持50，方便测试
        base_zombie_speed = 0.5
        base_spawn_rate = 300
    
    # 初始化当前僵尸速度和刷新率
    zombie_speed = base_zombie_speed # 这行现在代表基础速度，实际速度会再乘以倍率
    spawn_rate = base_spawn_rate

    # 新增：当前新生成僵尸的实际移动速度，初始为基础速度
    current_actual_zombie_movement_speed = base_zombie_speed
    
    # 根据主题设置背景和音乐
    actual_music_to_load = ""
    current_hakimi_music_idx = 0 # 只用于哈基米主题音乐切换

    if theme == 0:  # 经典主题
        background = load_image('back.png')
        actual_music_to_load = os.path.join(os.path.dirname(__file__), 'music', CLASSIC_MUSIC_L2)
    elif theme == 1:  # 宇宙主题
        background = load_image('space.png')
        actual_music_to_load = os.path.join(os.path.dirname(__file__), 'music', SPACE_MUSIC_L2)
    elif theme == 2: # 哈基米主题
        background = load_image('gback.png')
        actual_music_to_load = os.path.join(os.path.dirname(__file__), 'music', HAKIMI_MUSIC_FILES_L2[current_hakimi_music_idx])
    
    # 播放背景音乐
    try:
        pygame.mixer.music.load(actual_music_to_load)
        pygame.mixer.music.set_volume(0.15) # Set volume for level 2 music (was 0.3)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"无法加载音乐文件: {actual_music_to_load}, error: {e}")
    
    # 初始化游戏对象
    player = PlayerPeashooter(0, 0, theme_index=theme)

    # 初始化玩家等级相关的刷新/血量倍率
    level_spawn_health_multiplier = 1.0
    if player.level == 2:
        level_spawn_health_multiplier = 1.75
    elif player.level == 3:
        level_spawn_health_multiplier = 3.0

    current_spawn_health_multiplier = level_spawn_health_multiplier # 初始的刷新/血量倍率
    zombies = []
    bullets = []
    suns = []

    # 音乐按钮设置
    music_button_img = load_image('music.png', 0.7) # 按钮图标
    music_button_rect = pygame.Rect(SCREEN_WIDTH - 60, SCREEN_HEIGHT - 60, 50, 50) # 右下角
    
    # 解压模式下设置全局变量
    if relax_mode:
        # 修改Bullet类的默认速度
        Bullet.default_speed = 5
    else:
        Bullet.default_speed = 4
    
    # 初始化当前子弹速度为默认值
    Bullet.current_speed = Bullet.default_speed
    
    zombie_spawn_timer = 0
    zombie_count = 0
    
    # 记录上一次玩家等级，用于检测等级变化
    previous_level = player.level
    
    # 记录上一次击杀数，用于检测击杀数变化
    previous_kills = 0
    
    clock = pygame.time.Clock()
    running = True
    
    # 游戏主循环
    while running:
        # 更新音效管理器
        sound_manager.update()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return False
            elif event.type == pygame.USEREVENT + 1:
                # 重要音效播放结束
                sound_manager.is_playing_important = False
            elif event.type == pygame.KEYDOWN:
                # 处理按键事件
                if event.key == pygame.K_u:
                    if player.level == 3:
                        success = player.activate_super_mode()
                        if not success:
                            print(f"阳光不足，无法激活超级模式，需要{player.super_cost}阳光")
                    else:
                        player.try_upgrade()
                elif event.key == pygame.K_p:
                    result = player.handle_keydown(event.key)
                    if result and isinstance(result, list):
                        bullets.extend(result)
                elif player.handle_keydown(event.key):
                    pass
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if music_button_rect.collidepoint(event.pos):
                    if theme == 2: # 只在哈基米主题下切换音乐
                        current_hakimi_music_idx = (current_hakimi_music_idx + 1) % len(HAKIMI_MUSIC_FILES_L2)
                        music_to_load_path = os.path.join(os.path.dirname(__file__), 'music', HAKIMI_MUSIC_FILES_L2[current_hakimi_music_idx])
                        try:
                            pygame.mixer.music.load(music_to_load_path)
                            pygame.mixer.music.set_volume(0.15) # (was 0.3)
                            pygame.mixer.music.play(-1)
                            print(f"[哈基米主题] 切换音乐到: {HAKIMI_MUSIC_FILES_L2[current_hakimi_music_idx]}")
                        except Exception as e:
                            print(f"无法加载哈基米音乐: {music_to_load_path}, error: {e}")
                    else:
                        # 其他主题点击音乐按钮不执行切换，可以考虑播放提示音或无操作
                        print(f"当前主题 ({['经典', '宇宙', '哈基米'][theme]}) 不支持音乐切换。")
                else:
                    # 处理鼠标点击事件（非音乐按钮）
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    for sun in suns:
                        if sun.rect.collidepoint(mouse_x, mouse_y) and not sun.collected:
                            sun.collected = True
                            sun.clicked_collected = True  # 设置点击收集标记
                            # 直接增加阳光值
                            player.sun_value += sun.value
                            # 添加日志输出，用于调试
                            print(f"阳光被点击收集, 值: {sun.value}, 当前阳光总数: {player.sun_value}")
                            # 播放阳光收集音效
                            if sounds['points']:
                                sound_manager.play_normal_sound(sounds['points'])
        
        # 获取按键状态
        keys = pygame.key.get_pressed()
        
        # 更新玩家
        player.update(bullets)
        
        # 检测玩家等级变化，并相应调整僵尸刷新速度和血量相关倍率
        if player.level != previous_level:
            level_spawn_health_multiplier = 1.0
            if player.level == 2:
                level_spawn_health_multiplier = 1.75
            elif player.level == 3:
                level_spawn_health_multiplier = 3.0
            
            current_spawn_health_multiplier = max(level_spawn_health_multiplier, kill_spawn_health_multiplier if 'kill_spawn_health_multiplier' in locals() else 1.0)
            spawn_rate = int(base_spawn_rate / current_spawn_health_multiplier)
            previous_level = player.level
        
        # 检测击杀数变化，并调整僵尸刷新/血量倍率 和 僵尸移动速度
        if player.kills != previous_kills:
            # 调整后的刷新频率和血量倍率曲线 (目标：200击杀时达到8.0x)
            if player.kills >= 200:
                kill_spawn_health_multiplier = 8.0
            elif player.kills >= 150: # 150-199 kills (50 range): 5.5x to 8.0x (2.5 diff)
                progress = (player.kills - 150) / 50.0
                kill_spawn_health_multiplier = 5.5 + progress * 2.5
            elif player.kills >= 100: # 100-149 kills (50 range): 3.5x to 5.5x (2.0 diff)
                progress = (player.kills - 100) / 50.0
                kill_spawn_health_multiplier = 3.5 + progress * 2.0
            elif player.kills >= 50:  # 50-99 kills (50 range): 2.0x to 3.5x (1.5 diff)
                progress = (player.kills - 50) / 50.0
                kill_spawn_health_multiplier = 2.0 + progress * 1.5
            else:  # 0-49 kills (50 range): 1.0x to 2.0x (1.0 diff)
                progress = player.kills / 50.0 # 从0.0到 aproape 1.0
                kill_spawn_health_multiplier = 1.0 + progress * 1.0
            kill_spawn_health_multiplier = max(1.0, kill_spawn_health_multiplier) # 确保至少为1.0
            
            current_spawn_health_multiplier = max(level_spawn_health_multiplier, kill_spawn_health_multiplier)
            spawn_rate = int(base_spawn_rate / current_spawn_health_multiplier)

            # 僵尸移动速度倍率曲线 (目标：200击杀时达到2.0x)
            zombie_movement_speed_multiplier = 1.0
            if player.kills >= 200:
                zombie_movement_speed_multiplier = 2.0
            elif player.kills >= 150: # 150-199: 1.7x to 2.0x (0.3 diff over 50 kills)
                progress = (player.kills - 150) / 50.0
                zombie_movement_speed_multiplier = 1.7 + progress * 0.3
            elif player.kills >= 100: # 100-149: 1.4x to 1.7x (0.3 diff over 50 kills)
                progress = (player.kills - 100) / 50.0
                zombie_movement_speed_multiplier = 1.4 + progress * 0.3
            elif player.kills >= 50:  # 50-99: 1.2x to 1.4x (0.2 diff over 50 kills)
                progress = (player.kills - 50) / 50.0
                zombie_movement_speed_multiplier = 1.2 + progress * 0.2
            else: # 0-49: 1.0x to 1.2x (0.2 diff over 50 kills)
                progress = player.kills / 50.0
                zombie_movement_speed_multiplier = 1.0 + progress * 0.2
            zombie_movement_speed_multiplier = max(1.0, zombie_movement_speed_multiplier) # 确保至少为1.0
            
            current_actual_zombie_movement_speed = base_zombie_speed * zombie_movement_speed_multiplier
            
            if player.kills % 25 == 0 or player.kills == 1:
                print(f"击杀数: {player.kills}, 刷新/血量倍率: {current_spawn_health_multiplier:.2f}x, 新僵尸移速: {current_actual_zombie_movement_speed:.2f} (基础: {base_zombie_speed}, 倍率 {zombie_movement_speed_multiplier:.2f}x)")
            
            previous_kills = player.kills
        
        # 生成僵尸
        zombie_spawn_timer += 1
        if zombie_spawn_timer >= spawn_rate and zombie_count < ZOMBIE_MAX:
            row = random.randint(0, 4)
            health_multiplier = 1.0
            if current_spawn_health_multiplier > 1.0:
                health_multiplier = 1.0 + (current_spawn_health_multiplier - 1.0) * 0.25
            
            zombie = Zombie(row, health_multiplier)
            zombie.speed = current_actual_zombie_movement_speed # 应用动态计算的移动速度
            zombie.original_speed = current_actual_zombie_movement_speed # 确保 original_speed 也更新
            zombies.append(zombie)
            zombie_count += 1
            zombie_spawn_timer = 0
            
            # 每25只僵尸打印一次当前僵尸状态
            if zombie_count % 25 == 0:
                print(f"生成第{zombie_count}只僵尸 - 速度: {zombie.speed:.2f}, 血量: {zombie.health}/{zombie.base_health} ({health_multiplier:.2f}倍)")
        
        # 更新僵尸
        for zombie in zombies[:]:
            if zombie.update():  # 僵尸到达左边界
                zombies.remove(zombie)
                return show_failure_screen()
            
            # 检测与玩家碰撞
            if zombie.rect.colliderect(player.rect):
                zombies.remove(zombie)
                return show_failure_screen()
        
        # 更新子弹
        for bullet in bullets[:]:
            if bullet.update():  # 子弹超出屏幕
                bullets.remove(bullet)
                continue
            
            # 检测子弹与僵尸碰撞
            for zombie in zombies[:]:
                if bullet.rect.colliderect(zombie.rect):
                    # 使用玩家当前的子弹伤害
                    damage = player.bullet_damage
                    zombie.health -= damage
                    zombie.hit_timer = 5
                    bullets.remove(bullet)
                    
                    if sounds['hit']:
                        # 使用音效管理器播放受击音效
                        sound_manager.play_normal_sound(sounds['hit'])
                    
                    if zombie.health <= 0:
                        # 僵尸死亡，播放死亡音效
                        if sounds['died']:
                            # 使用音效管理器播放死亡音效，允许多个死亡音效同时播放
                            sound_manager.play_zombie_death_sound(sounds['died'])
                        # 生成阳光
                        suns.append(Sun(zombie.x, zombie.y, 50))  # 每个僵尸掉落50阳光
                        zombies.remove(zombie)
                        player.kills += 1
                    
                    break
        
        # 更新阳光
        for sun in suns[:]:
            update_result = sun.update()
            if update_result and sun.reached_target: # 确保是到达目标后才移除和加分
                # 阳光被手动收集并到达目标，增加玩家阳光值
                # player.sun_value 已经在鼠标点击事件中增加了，这里不再重复增加
                # 但是我们需要在这里移除它，因为update_result为True代表可以移除了
                suns.remove(sun)
                # Log for debugging when sun is removed after reaching target
                print(f"Sun removed after reaching target. Current sun_value: {player.sun_value}")
        
        # 检查胜利条件
        if player.kills >= ZOMBIE_MAX:
            return show_victory_screen()
        
        # 渲染
        screen.blit(background, (0, 0))
        
        # 绘制游戏对象
        for sun in suns:
            sun.draw()
        
        for bullet in bullets:
            bullet.draw()
        
        for zombie in zombies:
            zombie.draw()
        
        player.draw()
        
        # 绘制UI
        # 顶部信息栏背景
        pygame.draw.rect(screen, (139, 69, 19), (0, 0, SCREEN_WIDTH, 80))  # 修改高度到80像素
        
        # 显示阳光数量 - 左上角
        sun_image = load_image('sun.png', 0.3)
        screen.blit(sun_image, (10, 10))
        sun_text = font.render(f'{player.sun_value}', True, YELLOW)
        screen.blit(sun_text, (50, 10)) # Y adjusted
        
        # 如果是解压模式，显示对应提示 - 左上角旁边
        if relax_mode:
            relax_text = font.render("解压模式: 击杀400只僵尸获胜", True, (255, 255, 0))
            screen.blit(relax_text, (120, 10)) # Y adjusted
        
        # 显示击杀数/目标数 - 右上角
        kill_text = font.render(f'击杀: {player.kills}/{ZOMBIE_MAX}', True, WHITE)
        screen.blit(kill_text, (SCREEN_WIDTH - 150, 10)) # Y adjusted
        
        # 显示当前等级 - 中上第二行 (下移一行防止重叠)
        level_names = ["豌豆射手", "双发射手", "机枪射手"]
        level_text = font.render(f'等级: {level_names[player.level-1]}', True, WHITE)
        screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 35)) # Y adjusted
        
        # 第二行 - 显示分开的信息
        
        # 显示升级提示 - 左侧第二行
        if player.level < 3:
            upgrade_cost = player.level * 100
            upgrade_text = font.render(f'升级需要: {upgrade_cost} 阳光 (按U升级)', True, YELLOW)
            screen.blit(upgrade_text, (20, 60)) # Y adjusted
        
        # 计算当前僵尸血量倍率
        health_multiplier = 1.0
        if current_spawn_health_multiplier > 1.0:
            health_multiplier = 1.0 + (current_spawn_health_multiplier - 1.0) * 0.25
        
        # 显示当前僵尸血量倍率 - 右侧第二行
        health_text = font.render(f'僵尸血量: {health_multiplier:.1f}x', True, (255, 150, 150))
        screen.blit(health_text, (SCREEN_WIDTH - 240, 35)) # Y adjusted
        
        # 显示当前僵尸刷新速度 - 右侧第三行
        speed_text = font.render(f'僵尸刷新速度: {current_spawn_health_multiplier:.1f}x', True, (255, 200, 200))
        screen.blit(speed_text, (SCREEN_WIDTH - 240, 60)) # Y adjusted
        
        # 第三行 - 超进化信息
        # 如果玩家是机枪射手，显示超进化提示 - 中间第三行
        if player.level == 3:
            if player.super_mode:
                super_text = font.render("超进化中!", True, (255, 0, 0))
                screen.blit(super_text, (SCREEN_WIDTH // 2 - super_text.get_width() // 2, 60)) # Y adjusted
            else:
                super_text = font.render(f"按U键消耗{player.super_cost}阳光进入超进化状态!", True, (255, 215, 0))
                screen.blit(super_text, (SCREEN_WIDTH // 2 - super_text.get_width() // 2, 60)) # Y adjusted
            
            # 显示机枪射手的增强状态
            power_text = font.render(f"机枪强化等级: {player.power_level} | 伤害: {player.bullet_damage}", True, (100, 255, 100))
            screen.blit(power_text, (20, 85)) # Y adjusted (below the 80px bar)
            
            # 显示下一次增强的倒计时
            next_power_up = player.countdown_display
            next_power_up_seconds = next_power_up // 60
            countdown_text = font.render(f"下次强化: {next_power_up_seconds}秒", True, (100, 255, 100))
            screen.blit(countdown_text, (20, 105)) # Y adjusted (below the 80px bar)
        
        # 添加全屏攻击提示 - 左下角
        super_attack_text = font.render("按P键消耗100阳光发动全屏攻击!", True, (0, 255, 255))
        screen.blit(super_attack_text, (10, SCREEN_HEIGHT - 60))
        
        # 显示操作提示
        controls_text = font.render('WASD移动 鼠标点击收集阳光', True, WHITE)
        screen.blit(controls_text, (10, SCREEN_HEIGHT - 30))
        
        # 绘制音乐切换按钮
        screen.blit(music_button_img, music_button_rect)

        pygame.display.flip()
        clock.tick(60)
    
    return False

if __name__ == "__main__":
    level2(1, 0)  # 默认普通难度，经典主题
    pygame.quit()
    sys.exit() 