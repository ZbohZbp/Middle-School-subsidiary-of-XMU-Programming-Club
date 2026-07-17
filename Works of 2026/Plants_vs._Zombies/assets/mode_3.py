"""
数字战力成长模式 (Power Growth Mode)

设计思路:
    - 核心玩法: 玩家控制带有数字标识的植物，通过击败数字比自己小的僵尸来成长
    - 成长机制: 击败僵尸后，玩家战力 += 僵尸战力值
    - 风险机制: 碰到战力比自己高的僵尸 → 游戏结束
    - 胜利条件: 击败大Boss (战力 = 玩家战力 × 5)
    
    灵感来源: 球球大作战 + 吸血鬼幸存者的成长机制
    
技术要点:
    - 使用pygame.sprite.Sprite管理游戏对象
    - 自动瞄准系统减少玩家操作负担
    - 战力颜色阶梯给玩家成长反馈

修改日志:
    2026-04-03: 初始创建，实现基础战力成长玩法
"""

import pygame
import random
import sys
import os
import math

# ============================================
# 初始化设置
# ============================================
pygame.init()
pygame.font.init()

# 屏幕设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 150, 255)
PURPLE = (150, 0, 255)
GOLD = (255, 215, 0)
YELLOW = (255, 255, 0)

# ============================================
# 工具函数
# ============================================

# 字体回退链 - 优先使用系统好看的中文字体
# Windows: 微软雅黑 > 黑体 > 等线
# macOS:   PingFang SC
# Linux:   Noto Sans CJK SC
FONT_PRIORITY = ['microsoftyahei', 'simhei', 'dengxian', 'pingfangsc', 'notosanssc']

def get_font(size):
    for name in FONT_PRIORITY:
        try:
            font = pygame.font.SysFont(name, size)
            if font.render('测', True, (0,0,0)).get_width() > 0:
                return font
        except:
            continue
    return pygame.font.Font(None, size)


def get_power_color(power):
    """
    功能: 根据战力返回对应颜色
    
    设计思路:
        使用颜色阶梯给玩家成长反馈
        战力越高颜色越"尊贵"
        
    参数:
        power: int - 当前战力值
        
    返回:
        tuple - RGB颜色值
        
    修改日志:
        2026-04-03: 初始创建
    """
    if power <= 5:
        return GREEN      # 绿色 - 新手
    elif power <= 10:
        return BLUE       # 蓝色 - 进阶
    elif power <= 20:
        return PURPLE     # 紫色 - 高手
    else:
        return GOLD       # 金色 - 大神


def calculate_spawn_power(player_power):
    """
    功能: 计算新僵尸的战力
    
    设计思路:
        保持挑战性，但给玩家成长空间
        生成范围: max(1, 玩家战力-2) 到 玩家战力+3
        这样既有低战力僵尸供玩家收割，也有高战力僵尸构成威胁
        
    参数:
        player_power: int - 玩家当前战力
        
    返回:
        int - 新僵尸的战力值
        
    修改日志:
        2026-04-03: 初始创建
    """
    min_power = max(1, player_power - 2)
    max_power = player_power + 3
    return random.randint(min_power, max_power)


def find_nearest_enemy(player, zombies):
    """
    功能: 查找最近的僵尸用于自动瞄准
    
    设计思路:
        减少玩家操作负担，让玩家专注移动和策略
        只瞄准已经进入屏幕的僵尸，避免在屏幕外就被打死
        
    参数:
        player: PlayerPlant - 玩家对象
        zombies: pygame.sprite.Group - 僵尸组
        
    返回:
        PowerZombie or None - 最近的僵尸，如果没有则返回None
        
    修改日志:
        2026-04-03: 初始创建
        2026-04-03: 增加屏幕边界检查，只瞄准已进入屏幕的僵尸
    """
    nearest = None
    min_distance = float('inf')
    
    for zombie in zombies:
        # 只跳过完全离开屏幕的僵尸；只要有一部分进入画面，就允许继续瞄准并攻击
        if zombie.rect.right < 0 or zombie.rect.left > SCREEN_WIDTH or zombie.rect.bottom < 0 or zombie.rect.top > SCREEN_HEIGHT:
            continue
        
        dx = zombie.rect.centerx - player.rect.centerx
        dy = zombie.rect.centery - player.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < min_distance:
            min_distance = distance
            nearest = zombie
    
    return nearest


# ============================================
# 资源加载函数
# ============================================

def load_image(name, scale=1.0):
    """
    功能: 加载图片资源
    
    设计思路:
        统一封装图片加载，支持缩放
        错误处理防止资源缺失导致崩溃
        使用相对于当前文件的路径，确保从任何工作目录都能正确加载
        
    修改日志:
        2026-04-03: 初始创建
        2026-04-06: 修复路径问题，使用相对于文件的路径
    """
    try:
        # 使用相对于当前文件的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(base_path, name)
        image = pygame.image.load(image_path)
        if scale != 1.0:
            width = int(image.get_width() * scale)
            height = int(image.get_height() * scale)
            image = pygame.transform.scale(image, (width, height))
        return image.convert_alpha()
    except (pygame.error, FileNotFoundError) as e:
        print(f"警告: 无法加载图片 {name} - {e}")
        # 创建占位图
        placeholder = pygame.Surface((50, 50), pygame.SRCALPHA)
        placeholder.fill((255, 0, 0, 128))
        return placeholder


def load_sound(name):
    """
    功能: 加载音效资源
    
    设计思路:
        统一封装音效加载
        错误处理防止音效缺失导致崩溃
        使用相对于当前文件的路径，确保从任何工作目录都能正确加载
        
    修改日志:
        2026-04-03: 初始创建
        2026-04-06: 修复路径问题，使用相对于文件的路径
    """
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        sound_path = os.path.join(base_path, 'sounds', name)
        return pygame.mixer.Sound(sound_path)
    except (pygame.error, FileNotFoundError) as e:
        print(f"警告: 无法加载音效 {name} - {e}")
        return None


# ============================================
# 游戏类定义
# ============================================

class AOEEffect(pygame.sprite.Sprite):
    """
    AOE技能效果类
    
    设计思路:
        - 缩小作用半径（80像素）提升命中精度
        - 降低施法前摇（按住鼠标0.3秒即可释放）
        - 清晰的范围指示器（绿色圆圈显示）
        - 合理的伤害平衡（2倍伤害 × 范围内僵尸数）
        
    参数:
        x, y: 技能释放位置
        damage: 基础伤害值
        radius: 作用半径（默认80像素，较小范围）
        
    修改日志:
        2026-04-03: 初始创建
    """
    
    def __init__(self, x, y, damage, radius=80, start_age=0):
        super().__init__()
        
        self.damage = damage  # AOE伤害直接使用传入值（独立成长）
        self.radius = radius
        self.center = (x, y)
        
        # 动画效果
        self.lifetime = 10  # 持续10帧（加速一倍）
        self.age = start_age  # 支持延迟启动（用于combo三层特效错开）
        
        # 创建爆炸图像
        self.image = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        
        # 加载ha.png图片
        try:
            self.ha_image = load_image('effects/ha.png', 0.5)
            self.ha_rect = self.ha_image.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        except Exception as e:
            print(f"加载ha.png失败: {e}")
            self.ha_image = None
            self.ha_rect = None
    
    def update(self):
        """更新AOE效果动画"""
        self.age += 1
        if self.age >= self.lifetime:
            self.kill()
        
        # 重绘效果
        self._draw_effect()
    
    def _draw_effect(self):
        """绘制AOE爆炸效果"""
        self.image.fill((0, 0, 0, 0))  # 清空图像
        
        # 延迟阶段不绘制
        if self.age < 0:
            return
        
        cx, cy = self.rect.width // 2, self.rect.height // 2
        
        # 渐变爆炸效果
        progress = self.age / self.lifetime
        alpha = max(0, min(255, int(255 * (1 - progress))))
        
        # 外圈
        pygame.draw.circle(self.image, (255, 100, 0, alpha // 2), (cx, cy), self.radius)
        # 内圈
        pygame.draw.circle(self.image, (255, 200, 0, alpha), (cx, cy), max(0, int(self.radius * (1 - progress * 0.5))))
        # 中心点
        pygame.draw.circle(self.image, (255, 255, 200, alpha), (cx, cy), max(0, int(self.radius * 0.2)))
        
        # 绘制ha.png图片
        if self.ha_image and self.ha_rect:
            ha_image = self.ha_image.copy()
            ha_image.set_alpha(alpha)
            self.image.blit(ha_image, self.ha_rect)
    
    def get_affected_zombies(self, zombies):
        """
        获取在范围内的僵尸
        
        返回:
            list - 受影响的僵尸列表
        """
        affected = []
        for zombie in zombies:
            dx = zombie.rect.centerx - self.center[0]
            dy = zombie.rect.centery - self.center[1]
            distance = math.sqrt(dx * dx + dy * dy)
            if distance <= self.radius:
                affected.append(zombie)
        return affected


class AOEIndicator:
    """
    AOE技能指示器类
    
    设计思路:
        - 显示在鼠标位置
        - 实时更新位置
        - 显示蓄力进度
        - 释放时闪烁提示
        
    修改日志:
        2026-04-03: 初始创建
    """
    
    def __init__(self, radius=80):
        self.radius = radius
        self.position = (0, 0)
        self.visible = False
        self.charge_progress = 0.0  # 蓄力进度 0.0 - 1.0
        self.charge_required = 0.3  # 蓄力时间（秒）
        
        # 创建指示器图像
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(0, 0))
    
    def update_position(self, x, y):
        """更新指示器位置"""
        self.position = (x, y)
        self.rect.center = (x, y)
    
    def update_charge(self, delta_time):
        """更新蓄力进度"""
        if self.visible:
            self.charge_progress = min(1.0, self.charge_progress + delta_time / self.charge_required)
        else:
            self.charge_progress = 0.0
    
    def draw(self, surface):
        """绘制指示器"""
        if not self.visible:
            return
        
        cx, cy = self.position[0], self.position[1]
        
        # 外圈（半透明）
        pygame.draw.circle(surface, (0, 200, 0, 50), (cx, cy), self.radius, 3)
        
        # 蓄力进度环
        if self.charge_progress < 1.0:
            # 未蓄满 - 显示进度条
            progress_color = (255, 200, 0)  # 黄色
            pygame.draw.circle(surface, (0, 200, 0, 30), (cx, cy), self.radius, 1)
            
            # 绘制弧形进度
            start_angle = -90
            end_angle = start_angle + int(360 * self.charge_progress)
            rect = pygame.Rect(cx - self.radius, cy - self.radius, self.radius * 2, self.radius * 2)
            pygame.draw.arc(surface, progress_color, rect, 
                          math.radians(start_angle), math.radians(end_angle), 4)
        else:
            # 蓄满 - 显示就绪状态（闪烁绿色）
            if int(pygame.time.get_ticks() / 100) % 2 == 0:
                pygame.draw.circle(surface, (0, 255, 0, 100), (cx, cy), self.radius, 4)
        
        # 中心十字
        cross_size = 10
        pygame.draw.line(surface, (255, 255, 255, 150), 
                        (cx - cross_size, cy), (cx + cross_size, cy), 2)
        pygame.draw.line(surface, (255, 255, 255, 150), 
                        (cx, cy - cross_size), (cx, cy + cross_size), 2)


class PowerBullet(pygame.sprite.Sprite):
    """
    战力子弹类
    
    设计思路:
        - 伤害值 = 发射者的战力
        - 子弹大小随战力增长，提供视觉反馈
        - 速度恒定，直线飞行
        
    修改日志:
        2026-04-03: 初始创建
    """
    
    def __init__(self, x, y, target_x, target_y, power):
        """
        参数:
            x, y: 发射位置
            target_x, target_y: 目标位置（用于计算方向）
            power: int - 发射者的战力（决定伤害和大小）
        """
        super().__init__()
        
        self.power = power
        self.damage = max(1, power)  # 伤害直接等于战力值
        
        # 子弹大小随战力增长（有上限）
        size = min(20 + power * 2, 40)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # 根据战力选择颜色
        color = get_power_color(power)
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        pygame.draw.circle(self.image, WHITE, (size//2, size//2), size//2, 2)
        
        self.rect = self.image.get_rect(center=(x, y))
        
        # 计算飞行方向
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            speed = 16  # 提高子弹飞行速度，让发射更顺畅
            self.speed_x = (dx / distance) * speed
            self.speed_y = (dy / distance) * speed
        else:
            self.speed_x = 16
            self.speed_y = 0
    
    def update(self):
        """更新子弹位置"""
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        
        # 超出屏幕边界则销毁
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()


class PowerZombie(pygame.sprite.Sprite):
    """
    带血量的僵尸类
    
    设计思路:
        - 头顶数字显示当前血量（实时减少）
        - 血量越高移动越慢（平衡性设计）
        - 击败后玩家获得伤害加成
        
    修改日志:
        2026-04-03: 初始创建
        2026-04-03: 将power改为health，头顶显示实时血量
    """
    
    def __init__(self, x, y, health, is_boss=False):
        """
        参数:
            x, y: 生成位置
            health: int - 僵尸血量值
            is_boss: bool - 是否为Boss
        """
        super().__init__()
        
        self.max_health = health
        self.health = health
        self.is_boss = is_boss
        
        # 加载僵尸图片
        if is_boss:
            self.image = load_image('zombies/zombie.png', 1.5)  # Boss更大
        else:
            self.image = load_image('zombies/zombie.png', 1.0)
        
        self.rect = self.image.get_rect(center=(x, y))
        
        # 血量越高移动越慢（Boss除外）
        if is_boss:
            self.speed = 1.2  # Boss移速（+50%）
        else:
            self.speed = max(1.2, (1.2 - health * 0.005) * 1.5)  # 血量越高移速越慢（全局+50%）
        
        # 字体用于绘制血量数字
        self.font = get_font(24 if is_boss else 18)
    
    def update(self, player):
        """
        更新僵尸位置（向玩家移动）
        
        参数:
            player: PlayerPlant - 玩家对象
        """
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            self.rect.x += (dx / distance) * self.speed
            self.rect.y += (dy / distance) * self.speed
    
    def draw_health_number(self, surface):
        """
        绘制头顶血量数字（实时显示当前血量）
        
        参数:
            surface: pygame.Surface - 绘制目标
            
        设计思路:
            实时显示当前血量，让玩家看到攻击效果
            血量低于30%时显示红色警告
        """
        # 血量低于30%显示红色
        health_percent = self.health / self.max_health
        if health_percent <= 0.3:
            color = RED  # 危险 - 快死了
        elif health_percent <= 0.6:
            color = YELLOW  # 警告 - 半血以下
        else:
            color = WHITE  # 正常
        
        # Boss有特殊标识，显示最大血量作为参考
        if self.is_boss:
            text = f"★{int(self.health)}/{self.max_health}"
        else:
            text = str(int(self.health))
        
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.top - 15))
        
        # 绘制背景框
        padding = 4
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(surface, BLACK, bg_rect, border_radius=5)
        pygame.draw.rect(surface, color, bg_rect, 2, border_radius=5)
        
        surface.blit(text_surface, text_rect)
    
    def take_damage(self, damage):
        """
        受到伤害
        
        返回:
            bool - 是否死亡
        """
        self.health -= damage
        return self.health <= 0


class PlayerPlant(pygame.sprite.Sprite):
    """
    玩家控制的植物类
    
    设计思路:
        - 继承Sprite便于碰撞检测
        - damage（伤害）作为核心属性，影响子弹威力
        - 击败僵尸增加damage
        - 自动瞄准最近的敌人，玩家只需专注移动
        
    修改日志:
        2026-04-03: 初始创建
        2026-04-03: 将power改为damage，击败僵尸增加伤害
    """
    
    def __init__(self, x, y):
        """
        参数:
            x, y: 初始位置
        """
        super().__init__()
        
        self.damage = 1  # 初始伤害值（击败僵尸后增加）
        self.lives = 10  # 10点血量系统
        self.max_lives = 10
        self.invincible = False  # 是否无敌
        self.invincible_timer = 0  # 无敌倒计时
        self.blink_timer = 0  # 闪烁计时器
        
        # 加载植物图片（使用豌豆射手）
        self.base_image = load_image('plants/peashooter/Peashooter.gif', 1.2)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        
        # 移动速度
        self.speed = 5
        
        # 射击冷却
        self.shoot_cooldown = 0
        self.shoot_delay = 0.05  # 帧数，进一步加快射速
        
        # 字体
        self.font = get_font(32)
        self.big_font = get_font(48)
        
        # AOE技能系统
        self.aoe_indicator = AOEIndicator(radius=120)
        self.aoe_cooldown = 0
        self.aoe_cooldown_max = 20  # 2秒冷却（60帧/秒）
        
        # COMBO模式（每8次AOE触发，2秒无冷却）
        self.combo_mode = False
        self.combo_timer = 0
        self.base_shoot_cooldown = 0.2  # 基础射速，COMBO结束可永久提升
    
    def update(self, keys, zombies, bullets_group, mouse_buttons=None, mouse_pos=None):
        """
        更新玩家状态
        
        参数:
            keys: pygame.key.get_pressed() 结果
            zombies: pygame.sprite.Group - 僵尸组
            bullets_group: pygame.sprite.Group - 子弹组
        """
        # 移动控制
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
        
        # 归一化对角线移动
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        
        # 边界限制
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # 更新无敌状态
        if self.invincible:
            self.invincible_timer -= 1
            self.blink_timer += 1
            if self.invincible_timer <= 0:
                self.invincible = False
                self.image.set_alpha(255)  # 恢复不透明
        
        # 自动瞄准和射击
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        else:
            target = find_nearest_enemy(self, zombies)
            if target:
                self.shoot(target, bullets_group)
                self.shoot_cooldown = 4 if self.combo_mode else self.base_shoot_cooldown
        
        # AOE技能处理
        self._update_aoe(mouse_buttons, mouse_pos)
    
    def _update_aoe(self, mouse_buttons, mouse_pos):
        """
        更新AOE技能状态
        
        设计思路:
            - 鼠标右键单击直接释放，无需蓄力
            - 指示器始终跟随鼠标显示范围
            - 有3秒冷却时间
        """
        # COMBO模式下AOE冷却缩短为20帧（约0.33秒），不能无限狂轰
        if self.combo_mode:
            self.aoe_indicator.visible = True
            if mouse_pos:
                self.aoe_indicator.update_position(mouse_pos[0], mouse_pos[1])
                self.aoe_indicator.charge_progress = 1.0
                if mouse_buttons and mouse_buttons[2]:
                    if not hasattr(self, '_aoe_mouse_was_pressed') or not self._aoe_mouse_was_pressed:
                        self._aoe_ready_to_release = True
                        self._aoe_mouse_was_pressed = True
                else:
                    self._aoe_mouse_was_pressed = False
            # COMBO模式下也走冷却逻辑，只是冷却更短
            if self.aoe_cooldown > 0:
                self.aoe_cooldown -= 1
            return
        
        # 更新冷却
        if self.aoe_cooldown > 0:
            self.aoe_cooldown -= 1
        
        # 如果没有鼠标输入，隐藏指示器
        if mouse_pos is None:
            self.aoe_indicator.visible = False
            return
        
        # 始终更新指示器位置（在冷却时也显示，方便玩家瞄准）
        self.aoe_indicator.update_position(mouse_pos[0], mouse_pos[1])
        
        # 冷却完毕时显示指示器
        if self.aoe_cooldown <= 0:
            self.aoe_indicator.visible = True
            self.aoe_indicator.charge_progress = 1.0  # 始终显示就绪状态
            
            # 检测右键单击释放（使用边缘触发，避免按住连续释放）
            if mouse_buttons and mouse_buttons[2]:
                if not hasattr(self, '_aoe_mouse_was_pressed') or not self._aoe_mouse_was_pressed:
                    self._aoe_ready_to_release = True
                    self._aoe_mouse_was_pressed = True
            else:
                self._aoe_mouse_was_pressed = False
        else:
            # 冷却中，指示器变暗或隐藏
            self.aoe_indicator.visible = False
            self._aoe_mouse_was_pressed = False
    
    def get_aoe_release_data(self):
        """
        获取AOE释放数据并清除标记
        
        返回:
            tuple or None - (x, y, damage) 如果有可释放的AOE，否则None
        """
        if hasattr(self, '_aoe_ready_to_release') and self._aoe_ready_to_release:
            self._aoe_ready_to_release = False
            if not self.combo_mode:
                self.aoe_cooldown = self.aoe_cooldown_max
            else:
                self.aoe_cooldown = 20  # COMBO模式也需20帧冷却
            return (self.aoe_indicator.position[0], 
                    self.aoe_indicator.position[1], 
                    self.damage * 5)
        return None
    
    def shoot(self, target, bullets_group):
        """
        向目标发射子弹
        
        参数:
            target: PowerZombie - 目标僵尸
            bullets_group: pygame.sprite.Group - 子弹组
        """
        bullet_damage = self.damage * (2 if self.combo_mode else 1)
        bullet = PowerBullet(
            self.rect.centerx, self.rect.centery,
            target.rect.centerx, target.rect.centery,
            bullet_damage
        )
        bullets_group.add(bullet)
    
    def draw_damage_number(self, surface):
        """
        绘制头顶伤害数字和生命值
        
        参数:
            surface: pygame.Surface - 绘制目标
            
        设计思路:
            显示伤害值和剩余生命值（3点血量系统）
            移除发光效果避免重影
        """
        color = get_power_color(self.damage)
        
        # 显示子弹伤害（不含生命值，生命在左上角显示）
        text = f"伤害:{self.damage}"
        
        # 固定字体大小，避免重影
        font = get_font(24)
        
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.top - 20))
        
        # 绘制背景框
        padding = 5
        bg_rect = text_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(surface, BLACK, bg_rect, border_radius=5)
        pygame.draw.rect(surface, color, bg_rect, 2, border_radius=5)
        
        surface.blit(text_surface, text_rect)
    
    def gain_damage(self, amount):
        """
        增加伤害值
        
        参数:
            amount: int - 增加的伤害值
            
        设计思路:
            击败僵尸后增加伤害，让玩家有成长感
        """
        self.damage += amount
    
    def take_damage(self):
        """
        受到伤害（3点血量系统）
        
        返回:
            bool - 是否死亡（生命值为0）
            
        设计思路:
            无敌状态下不受伤害
            受伤后进入2秒无敌状态（120帧），期间闪烁
        """
        # 无敌状态下不受伤
        if self.invincible:
            return False
        
        # 扣一滴血
        self.lives -= 1
        
        # 进入无敌状态（2秒 = 120帧）
        self.invincible = True
        self.invincible_timer = 120
        self.blink_timer = 0
        
        return self.lives <= 0
    
    def draw(self, surface):
        """
        绘制植物（处理无敌闪烁效果）
        
        参数:
            surface: pygame.Surface - 绘制目标
        """
        # 无敌状态下闪烁（每5帧切换一次透明度）
        if self.invincible:
            if (self.blink_timer // 5) % 2 == 0:
                self.image.set_alpha(255)  # 显示
            else:
                self.image.set_alpha(100)  # 半透明
        
        surface.blit(self.image, self.rect)
        
        # COMBO模式金色发光效果
        if self.combo_mode:
            glow = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            glow.fill((255, 215, 0, 60))  # 金色半透明
            surface.blit(glow, self.rect)


# ============================================
# 游戏管理器
# ============================================

class GameManager:
    """
    游戏管理器
    
    设计思路:
        - 统一管理游戏状态
        - 处理僵尸生成逻辑
        - 判定游戏胜负
        
    修改日志:
        2026-04-03: 初始创建
    """
    
    def __init__(self, difficulty=1, theme=0):
        """
        参数:
            difficulty: int - 难度 (0-3)
            theme: int - 主题 (0-2)
        """
        self.difficulty = difficulty
        self.theme = theme
        
        # 创建屏幕
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("超燃豌豆射手")
        self.clock = pygame.time.Clock()
        
        # 增加混音通道数，支持更多音效并发
        pygame.mixer.set_num_channels(32)
        
        # 游戏状态
        self.running = True
        self.game_over = False
        self.victory = False
        self.restart = False
        self.final_boss_defeated = False  # 是否击败最终Boss
        self.return_to_menu = False  # 是否返回主菜单
        self.screen_shake = 0  # 屏幕震动帧数
        self.kill_flash = 0    # 击败闪光帧数
        self.aoe_kill_flash = 0  # AOE击败红色闪光帧数
        self.full_screen_flash = 0  # 全屏AOE金色闪光帧数

        # COMBO特效
        self.combo_particles = []  # COMBO粒子特效
        self.combo_border_pulse = 0  # COMBO边框脉冲
        
        # AOE计数（每8次触发COMBO模式）
        self.aoe_use_count = 0  # AOE使用次数
        
        # 游戏数据
        self.score = 0  # 击败僵尸数
        self.start_time = pygame.time.get_ticks()
        self.game_duration = 95  # 游戏时长95秒
        
        # 连击系统
        self.combo_count = 0  # 当前连击数
        self.combo_timer = 0  # 连击倒计时（帧）
        self.combo_timeout = 120  # 连击超时时间（2秒）
        
        # 精灵组
        self.player = PlayerPlant(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.player_group = pygame.sprite.Group(self.player)
        self.zombies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.aoe_effects = pygame.sprite.Group()  # AOE效果组
        
        # 背景
        self.background = load_image('background/back.png')
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # 字体
        self.font = get_font(24)
        self.big_font = get_font(48)
        
        # 生成计时器
        self.spawn_timer = 0
        self.spawn_delay = 90  # 帧数，初始生成较慢
        self.max_zombies = 15  # 最大僵尸数量限制
        
        # 浮动文字动画列表（用于CD减少等提示）
        self.floating_texts = []
        
        # 音效
        self.sounds = {
            'shoot': load_sound('by_plant/peashoot.mp3'),
            'hit': load_sound('by_zombie/hit.mp3'),
            'die': load_sound('by_zombie/died.mp3'),
            'win': load_sound('winmusic.ogg'),
            'aoe': self._load_aoe_sound(),  # AOE技能音效
            'plant': load_sound('by_plant/plant.ogg'),  # AOE击败僵尸音效
        }
        
        # 加载并播放背景音乐
        self._play_bgm()
    
    def _play_bgm(self):
        """
        播放背景音乐
        
        设计思路:
            循环播放g3.mp3作为战斗BGM
            音量适中不干扰音效
        """
        try:
            pygame.mixer.music.load(os.path.join(os.path.dirname(__file__), 'music', 'g3.mp3'))
            pygame.mixer.music.set_volume(0.3)  # 音量30%
            pygame.mixer.music.play(-1)  # -1表示循环播放
        except Exception as e:
            print(f"加载背景音乐失败: {e}")
    
    def _load_aoe_sound(self):
        """
        加载AOE音效并设置最大音量
        
        pygame音量范围是0.0-1.0，已经是系统最大
        如果还觉得不够大，需要调整系统音量或音效文件本身
        """
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            sound_path = os.path.join(base_path, 'sounds', 'xiao', '消除.mp3')
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(1.0)  # 设置最大音量
            return sound
        except (pygame.error, FileNotFoundError) as e:
            print(f"加载AOE音效失败: {e}")
            return None
    
    def spawn_zombie(self):
        """
        生成普通僵尸
        
        设计思路:
            在屏幕边缘随机位置生成
            血量根据游戏时间动态增加（越往后越难）
            限制最大僵尸数量，避免性能问题
        """
        # 限制最大僵尸数量
        if len(self.zombies) >= self.max_zombies:
            return
        
        # 随机选择屏幕边缘
        side = random.choice(['top', 'bottom', 'left', 'right'])
        
        if side == 'top':
            x = random.randint(0, SCREEN_WIDTH)
            y = -20
        elif side == 'bottom':
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT + 20
        elif side == 'left':
            x = -20
            y = random.randint(0, SCREEN_HEIGHT)
        else:  # right
            x = SCREEN_WIDTH + 20
            y = random.randint(0, SCREEN_HEIGHT)
        
        # 血量随游戏时间平滑增长
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        health = 5 + elapsed * 1.2 + random.randint(-2, 5)
        health = max(5, health)
        
        zombie = PowerZombie(x, y, health, is_boss=False)
        self.zombies.add(zombie)
    
    def _create_aoe_effect(self, x, y, damage):
        """
        创建AOE效果
        
        参数:
            x, y: 技能释放位置
            damage: 基础伤害值
        """
        # COMBO期间的AOE不计入触发计数
        if not self.player.combo_mode:
            self.aoe_use_count += 1
            # 每8次AOE触发COMBO模式（2秒无冷却）
            if self.aoe_use_count % 8 == 0:
                self._trigger_combo_mode()
                return
        
        # COMBO模式下三层特效，每层间隔0.1秒（6帧）
        if self.player.combo_mode:
            for i in range(3):
                aoe = AOEEffect(x, y, damage, radius=120, start_age=-(i * 6))
                self.aoe_effects.add(aoe)
            # 三层各播放一次音效，叠加更响
            if 'aoe' in self.sounds and self.sounds['aoe']:
                for _ in range(3):
                    self.sounds['aoe'].play()
        else:
            aoe = AOEEffect(x, y, damage, radius=120)
            self.aoe_effects.add(aoe)
            if 'aoe' in self.sounds and self.sounds['aoe']:
                self.sounds['aoe'].play()
    
    def _trigger_combo_mode(self):
        """
        触发COMBO模式：2秒内AOE无冷却
        """
        self.player.combo_mode = True
        self.player.combo_timer = 180  # 3秒
        
        # 屏幕震动
        self.screen_shake = 25
        
        # 金色闪光效果
        self.full_screen_flash = 10
        
        # 播放增强音效
        if self.sounds.get('aoe'):
            self.sounds['aoe'].set_volume(1.0)
            self.sounds['aoe'].play()
        
        # 显示COMBO提示
        self._show_combo_text()
    
    def _show_combo_text(self):
        """
        显示COMBO模式触发提示
        """
        big_font = get_font(60)
        text_content = "COMBO模式!"
        text = big_font.render(text_content, True, GOLD)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        if not hasattr(self, 'floating_texts'):
            self.floating_texts = []
        self.floating_texts.append({
            'surface': text,
            'rect': text_rect,
            'lifetime': 60,
            'velocity_y': -2
        })

    def _show_upgrade_text(self):
        """
        显示COMBO结束后的升级提示
        """
        big_font = get_font(48)
        text = big_font.render("全员强化!", True, GOLD)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))

        sub_font = get_font(28)
        shots = 60 / self.player.base_shoot_cooldown
        sub_text = sub_font.render(f"射速+1  |  伤害+5  |  AOE-0.2s", True, (255, 200, 100))
        sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        
        if not hasattr(self, 'floating_texts'):
            self.floating_texts = []
        self.floating_texts.append({
            'surface': text,
            'rect': text_rect,
            'lifetime': 70,
            'velocity_y': -1
        })
        self.floating_texts.append({
            'surface': sub_text,
            'rect': sub_rect,
            'lifetime': 70,
            'velocity_y': -1
        })
    
    def _process_aoe_damage(self):
        """
        处理AOE伤害
        
        设计思路:
            在AOE效果创建的第一帧计算伤害
            避免同一AOE对同一僵尸造成多次伤害
        """
        for aoe in self.aoe_effects:
            # 只在第一帧造成伤害
            if aoe.age == 1:
                affected_zombies = aoe.get_affected_zombies(self.zombies)
                for zombie in affected_zombies:
                    if zombie.take_damage(aoe.damage):
                        self.handle_zombie_death(zombie)
                    else:
                        # 播放受击音效
                        if self.sounds['hit']:
                            self.sounds['hit'].play()
                
                # AOE击败红色闪光
                if any(zombie.health <= 0 for zombie in affected_zombies):
                    self.aoe_kill_flash = 8
    
    def show_final_boss_effect(self):
        """
        显示最终Boss战效果
        
        设计思路:
            全屏变灰，计时暂停，显示提示文字
            AOE冷却缩短为1秒
        """
        # 缩短AOE冷却为0.8秒（48帧）
        self.player.aoe_cooldown_max = 48
        
        # 创建灰色遮罩
        gray_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        gray_overlay.fill((50, 50, 50, 150))  # 半透明灰色
        
        # 显示提示文字
        big_font = get_font(48)
        small_font = get_font(28)
        
        title_text = big_font.render("决战开始！", True, RED)
        subtitle_text = small_font.render("技能CD缩短！", True, YELLOW)
        
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        
        # 暂停游戏并显示效果
        start_time = pygame.time.get_ticks()
        display_duration = 3000  # 显示3秒
        
        while pygame.time.get_ticks() - start_time < display_duration:
            # 绘制当前游戏画面
            self.draw_game()
            
            # 叠加灰色遮罩
            self.screen.blit(gray_overlay, (0, 0))
            
            # 绘制提示文字
            self.screen.blit(title_text, title_rect)
            self.screen.blit(subtitle_text, subtitle_rect)
            
            pygame.display.flip()
            
            # 处理事件（防止卡住）
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
            
            self.clock.tick(60)
        
        # 调整游戏开始时间，补偿暂停的3秒
        self.start_time += display_duration

        # 赠送5秒COMBO模式
        self.player.combo_mode = True
        self.player.combo_timer = 300  # 5秒
        self.screen_shake = 30
        self.full_screen_flash = 15
        self._show_combo_text()
    
    def _play_blackout_transition(self):
        """
        播放黑屏渐变动画
        
        设计思路:
            击败最终Boss后先黑屏，再显示胜利画面
            增加戏剧效果
        """
        # 创建黑色遮罩
        black_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        black_overlay.fill((0, 0, 0))
        
        # 黑屏渐变时间
        fade_duration = 1500  # 1.5秒渐变到全黑
        hold_duration = 500   # 0.5秒保持全黑
        
        start_time = pygame.time.get_ticks()
        
        while True:
            elapsed = pygame.time.get_ticks() - start_time
            
            # 绘制当前游戏画面
            self.draw_game()
            
            # 计算透明度
            if elapsed < fade_duration:
                # 渐变到全黑
                alpha = int(255 * (elapsed / fade_duration))
            elif elapsed < fade_duration + hold_duration:
                # 保持全黑
                alpha = 255
            else:
                # 结束黑屏
                break
            
            # 应用黑色遮罩
            black_overlay.set_alpha(alpha)
            self.screen.blit(black_overlay, (0, 0))
            
            pygame.display.flip()
            
            # 处理事件（只处理退出）
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            
            self.clock.tick(60)
    
    def show_final_boss_victory(self):
        """
        显示击败最终Boss的胜利效果
        
        设计思路:
            全屏金色光效、文字提示、奖杯图标和音效
            一键击杀全屏僵尸，前2秒禁用操作防止误触
            
        返回:
            str - 'menu'表示返回主菜单，'exit'表示退出游戏
        """
        # 先播放黑屏渐变动画
        self._play_blackout_transition()
        
        # 一键击杀全屏所有僵尸
        killed_count = len(self.zombies)
        for zombie in self.zombies:
            zombie.kill()
        self.score += killed_count
        
        # 播放奖杯音效（使用胜利音效）
        if self.sounds['win']:
            try:
                # 停止其他音效，避免冲突
                pygame.mixer.stop()
                self.sounds['win'].set_volume(1.0)  # 确保最大音量
                self.sounds['win'].play()
                print("播放胜利音效成功")
            except Exception as e:
                print(f"播放胜利音效失败: {e}")
        else:
            print("警告: 胜利音效未加载")
        
        # 创建金色光效背景
        gold_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # 显示3秒胜利动画
        start_time = pygame.time.get_ticks()
        display_duration = 3000  # 3秒
        lock_duration = 2000  # 前2秒禁用操作
        
        big_font = get_font(48)
        small_font = get_font(36)
        
        # 加载奖杯图片（使用effects/win.png）
        try:
            trophy = load_image('effects/win.png', 1.5)
            trophy_rect = trophy.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        except Exception as e:
            print(f"加载奖杯图片失败: {e}")
            trophy = None
            trophy_rect = None
        
        waiting_click = True
        while waiting_click:
            # 绘制当前游戏画面
            self.draw_game()
            
            # 计算动画进度（0-1）
            elapsed = pygame.time.get_ticks() - start_time
            progress = min(1.0, elapsed / display_duration)
            
            # 金色光效（闪烁效果）
            alpha = int(100 + 100 * math.sin(progress * math.pi * 4))  # 闪烁
            gold_overlay.fill((255, 215, 0, alpha))  # 金色半透明
            self.screen.blit(gold_overlay, (0, 0))
            
            # 绘制文字
            title_text = big_font.render("你居然击败了最终Boss！", True, (255, 215, 0))  # 金色
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
            self.screen.blit(title_text, title_rect)
            
            # 绘制奖杯
            if trophy and trophy_rect:
                self.screen.blit(trophy, trophy_rect)
            
            # 绘制提示继续（动画结束后显示）
            if elapsed >= display_duration:
                continue_text = small_font.render("点击任意处返回主菜单", True, WHITE)
                continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
                self.screen.blit(continue_text, continue_rect)
            
            pygame.display.flip()
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'exit'
                # 前2秒禁用操作（防止误触）
                if elapsed >= lock_duration:
                    # 动画结束后点击任意处返回主菜单
                    if elapsed >= display_duration:
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            return 'menu'
                        if event.type == pygame.KEYDOWN:
                            return 'menu'
            
            self.clock.tick(60)
    
    def spawn_boss(self, boss_type='mini'):
        """
        生成Boss
        
        参数:
            boss_type: str - 'mini'小Boss, 'elite'精英Boss, 'final'最终Boss
        """
        # Boss从屏幕中央上方出现（更靠近屏幕）
        x = SCREEN_WIDTH // 2
        y = -30
        
        # Boss血量（基于游戏时间递增）
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        if boss_type == 'mini':
            health = 10000
        elif boss_type == 'elite':
            health = 50000
        elif boss_type == 'final':
            health = 250000
        else:
            health = 4000

        boss = PowerZombie(x, y, health, is_boss=True)
        boss.boss_type = boss_type
        self.zombies.add(boss)
        
        # Boss出现提示
        self.show_boss_warning()
    
    def show_boss_warning(self):
        """显示Boss出现警告"""
        # 播放Boss出现音效
        if self.sounds.get('hit'):
            self.sounds['hit'].set_volume(0.3)
            self.sounds['hit'].play()
        
        warning_text = self.big_font.render("BOSS出现！", True, RED)
        text_rect = warning_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        # 红色边框效果
        border_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # 闪烁效果
        for i in range(6):
            self.screen.blit(self.background, (0, 0))
            self.draw_game()
            
            # 红色边框闪烁
            if i % 2 == 0:
                border_surface.fill((0, 0, 0, 0))
                pygame.draw.rect(border_surface, (255, 0, 0, 100), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 20)
                self.screen.blit(border_surface, (0, 0))
                self.screen.blit(warning_text, text_rect)
            
            pygame.display.flip()
            pygame.time.delay(300)
    
    def check_collisions(self):
        """
        碰撞检测
        
        设计思路:
            1. 子弹击中僵尸: 扣血，可能死亡
            2. 僵尸碰到玩家: 玩家受伤，僵尸继续存在（增加压迫感）
        """
        # 子弹与僵尸碰撞
        hits = pygame.sprite.groupcollide(self.zombies, self.bullets, False, True)
        
        for zombie, bullets in hits.items():
            for bullet in bullets:
                if zombie.take_damage(bullet.damage):
                    # 僵尸死亡
                    self.handle_zombie_death(zombie)
                else:
                    # 播放受击音效
                    if self.sounds['hit']:
                        self.sounds['hit'].play()
        
        # 僵尸与玩家碰撞 - 玩家受伤（3点血量系统）
        collisions = pygame.sprite.spritecollide(self.player, self.zombies, False)
        
        for zombie in collisions:
            # 玩家受伤（扣一滴血，无敌状态下不受伤）
            if self.player.take_damage():
                # 玩家死亡（3点血用完）
                self.game_over = True
                self.victory = False
            else:
                # 受伤时屏幕震动
                self.screen_shake = 10  # 震动10帧
    
    def handle_zombie_death(self, zombie):
        """
        处理僵尸死亡
        
        参数:
            zombie: PowerZombie - 死亡的僵尸
            
        设计思路:
            击败僵尸后增加玩家伤害（基于僵尸最大血量）
            让玩家有持续成长感
        """
        # 更新连击系统
        self.combo_count += 1
        self.combo_timer = self.combo_timeout
        
        # 播放死亡音效（音量20%）
        if self.sounds['die']:
            self.sounds['die'].set_volume(0.2)
            self.sounds['die'].play()
        
        # 击败僵尸 → 伤害+1（简单直接）
        damage_gain = 2
        # 检测是否击败最终Boss
        if zombie.is_boss and getattr(zombie, 'boss_type', None) == 'final':
            result = self.show_final_boss_victory()
            self.final_boss_defeated = True
            if result == 'menu':
                self.running = False
                self.return_to_menu = True
            elif result == 'exit':
                self.running = False
                self.return_to_menu = False
        self.player.gain_damage(damage_gain)
        self.score += 1
        
        # 击败效果：轻微震动 + 闪光
        self.screen_shake = 3  # 轻微震动3帧
        self.kill_flash = 5    # 白色闪光5帧
        
        zombie.kill()
    
    def update(self):
        """
        更新游戏状态
        
        设计思路:
            90秒倒计时，坚持到时间结束获胜
            随着时间推移，生成速度加快，僵尸血量增加
        """
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        # 更新玩家
        self.player.update(keys, self.zombies, self.bullets, mouse_buttons, mouse_pos)
        
        # 检查并释放AOE技能
        aoe_data = self.player.get_aoe_release_data()
        if aoe_data:
            x, y, damage = aoe_data
            self._create_aoe_effect(x, y, damage)
        
        # 更新AOE效果
        self.aoe_effects.update()
        self._process_aoe_damage()
        
        # 更新子弹
        self.bullets.update()
        
        # 更新僵尸
        for zombie in self.zombies:
            zombie.update(self.player)
        
        # 更新连击计时器
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo_count = 0  # 连击中断
        
        # COMBO模式计时
        if self.player.combo_mode:
            self.player.combo_timer -= 1
            self.combo_border_pulse = (self.combo_border_pulse + 1) % 60
            # COMBO持续震动反馈
            self.screen_shake = 3
            # DJ打碟风格粒子：中心辐射 + 旋转光晕
            rainbow_colors = [(255,0,0),(255,165,0),(255,255,0),(0,255,0),(0,150,255),(255,0,255)]
            # 中心辐射粒子（大量）
            for _ in range(3):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 6)
                self.combo_particles.append({
                    'x': SCREEN_WIDTH // 2, 'y': SCREEN_HEIGHT // 2,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'life': random.randint(20, 50),
                    'max_life': 50,
                    'size': random.randint(4, 10),
                    'color': random.choice(rainbow_colors),
                    'type': 'radial'
                })
            # 旋转轨道粒子
            if random.random() < 0.3:
                orbit_angle = random.uniform(0, 2 * math.pi)
                orbit_radius = random.randint(100, 350)
                self.combo_particles.append({
                    'x': SCREEN_WIDTH // 2 + math.cos(orbit_angle) * orbit_radius,
                    'y': SCREEN_HEIGHT // 2 + math.sin(orbit_angle) * orbit_radius,
                    'vx': 0, 'vy': 0,
                    'life': random.randint(30, 60),
                    'max_life': 60,
                    'size': random.randint(5, 12),
                    'color': random.choice(rainbow_colors),
                    'type': 'orbit',
                    'orbit_angle': orbit_angle,
                    'orbit_radius': orbit_radius,
                    'orbit_speed': random.uniform(0.02, 0.06)
                })
            # 更新粒子（径向飞散 + 轨道旋转）
            for p in self.combo_particles[:]:
                if p.get('type') == 'orbit':
                    p['orbit_angle'] += p['orbit_speed']
                    p['x'] = SCREEN_WIDTH // 2 + math.cos(p['orbit_angle']) * p['orbit_radius']
                    p['y'] = SCREEN_HEIGHT // 2 + math.sin(p['orbit_angle']) * p['orbit_radius']
                else:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                p['life'] -= 1
                if p['life'] <= 0:
                    self.combo_particles.remove(p)
            if self.player.combo_timer <= 0 and not hasattr(self, 'boss_75_spawned'):
                self.player.combo_mode = False
                self.combo_particles.clear()
                # COMBO结束奖励：永久提升全方位数值
                self.player.base_shoot_cooldown = max(8, self.player.base_shoot_cooldown - 1)
                self.player.damage += 5
                self.player.aoe_cooldown_max = max(60, self.player.aoe_cooldown_max - 12)
                # COMBO结束特效
                self.full_screen_flash = 8
                self._show_upgrade_text()
        
        # 计算剩余时间
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        remaining = self.game_duration - elapsed
        
        # 时间结束 - 获胜
        if remaining <= 0:
            self.game_over = True
            self.victory = True
            return
        
        # 生成新僵尸（节奏随时间加快）
        self.spawn_timer += 1
        
        # 统一递进公式：开局2秒，逐渐加快到0.83秒
        current_spawn_delay = max(50, int((120 - elapsed * 0.7) * 2 / 3))  # 加快50%
        
        if self.spawn_timer >= current_spawn_delay:
            self.spawn_zombie()
            self.spawn_timer = 0
        
        # 30秒、60秒、75秒时生成Boss
        if elapsed == 30 and not hasattr(self, 'boss_30_spawned'):
            self.spawn_boss('mini')
            self.boss_30_spawned = True
        
        if elapsed == 60 and not hasattr(self, 'boss_60_spawned'):
            self.spawn_boss('elite')
            self.boss_60_spawned = True
        
        if elapsed == 75 and not hasattr(self, 'boss_75_spawned'):
            self.spawn_boss('final')
            self.boss_75_spawned = True
            self.show_final_boss_effect()
            # 最终boss出场后永久开启COMBO模式
            self.player.combo_mode = True
            self.player.combo_timer = 999999
        
        # 碰撞检测
        self.check_collisions()
        
        # 更新浮动文字动画
        self._update_floating_texts()
    
    def _update_floating_texts(self):
        """更新浮动文字动画"""
        for text in self.floating_texts[:]:
            text['lifetime'] -= 1
            text['rect'].y += text['velocity_y']
            if text['lifetime'] <= 0:
                self.floating_texts.remove(text)
    
    def draw_game(self):
        """绘制游戏画面"""
        # 计算屏幕震动偏移
        shake_x, shake_y = 0, 0
        if self.screen_shake > 0:
            shake_x = random.randint(-5, 5)
            shake_y = random.randint(-5, 5)
            self.screen_shake -= 1
        
        # 绘制背景（带震动偏移）
        self.screen.blit(self.background, (shake_x, shake_y))
        
        # 绘制子弹
        self.bullets.draw(self.screen)
        
        # 绘制AOE效果
        self.aoe_effects.draw(self.screen)
        
        # 绘制僵尸和血量数字（实时显示）
        for zombie in self.zombies:
            self.screen.blit(zombie.image, zombie.rect)
            zombie.draw_health_number(self.screen)
        
        # 绘制玩家（带无敌闪烁效果）和伤害数字
        self.player.draw(self.screen)
        self.player.draw_damage_number(self.screen)
        
        # 绘制AOE技能指示器（在玩家上方）
        self.player.aoe_indicator.draw(self.screen)
        
        # 绘制浮动文字动画（COMBO提示等）
        for text in self.floating_texts:
            self.screen.blit(text['surface'], text['rect'])
        
        # 击败闪光效果
        if self.kill_flash > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_alpha = int(100 * (self.kill_flash / 5))  # 逐渐减弱
            flash_surface.fill((255, 255, 255, flash_alpha))
            self.screen.blit(flash_surface, (0, 0))
            self.kill_flash -= 1
        
        # AOE击败红色闪光效果
        if self.aoe_kill_flash > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_alpha = int(120 * (self.aoe_kill_flash / 8))  # 逐渐减弱
            flash_surface.fill((255, 50, 50, flash_alpha))  # 红色
            self.screen.blit(flash_surface, (0, 0))
            self.aoe_kill_flash -= 1
        
        # COMBO金色闪光效果
        if self.full_screen_flash > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_alpha = int(150 * (self.full_screen_flash / 10))  # 逐渐减弱
            flash_surface.fill((255, 215, 0, flash_alpha))  # 金色
            self.screen.blit(flash_surface, (0, 0))
            self.full_screen_flash -= 1

        # COMBO粒子特效（彩虹色）
        if self.player.combo_mode and self.combo_particles:
            for p in self.combo_particles:
                alpha = int(255 * p['life'] / p['max_life'])
                size = int(p['size'] * (p['life'] / p['max_life']))
                pygame.draw.circle(self.screen, p['color'], (int(p['x']), int(p['y'])), max(1, size))

        # COMBO金色脉冲边框
        if self.player.combo_mode:
            pulse = abs(self.combo_border_pulse - 30) / 30.0  # 0→1→0 脉冲
            border_alpha = int(60 + 100 * pulse)
            border_width = int(3 + 4 * pulse)
            border_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(border_surface, (255, 215, 0, border_alpha),
                           (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), border_width)
            self.screen.blit(border_surface, (0, 0))
        
        # 绘制UI
        self.draw_ui()
    
    def draw_ui(self):
        """绘制用户界面"""
        # 计算剩余时间
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        remaining = max(0, self.game_duration - elapsed)
        minutes = remaining // 60
        seconds = remaining % 60
        
        # 左上角：伤害和生命值合并为一行
        damage_color = get_power_color(self.player.damage)
        combo_mult = 3 if self.player.combo_mode else 1
        bullet_damage = self.player.damage * combo_mult

        damage_label = f"伤害:{bullet_damage}"
        if self.player.combo_mode:
            damage_label += " (COMBOx3)"
            damage_color = GOLD
        damage_text = self.big_font.render(damage_label, True, damage_color)
        self.screen.blit(damage_text, (10, 10))

        lives_text = f"生命:{self.player.lives}/{self.player.max_lives}"
        lives_surface = self.font.render(lives_text, True, RED)
        lives_x = 10 + damage_text.get_width() + 15
        self.screen.blit(lives_surface, (lives_x, 12))

        # 显示射速（帧数，无小数点）
        if self.player.combo_mode:
            speed_text = self.font.render(f"射速强化中 ({self.player.base_shoot_cooldown}→0.05帧/发)", True, GOLD)
        else:
            speed_text = self.font.render(f"冷却: {self.player.base_shoot_cooldown}帧/发", True, WHITE)
        self.screen.blit(speed_text, (10, 68))
        
        # 无敌状态提示
        if self.player.invincible:
            invincible_text = self.font.render("无敌中!", True, YELLOW)
            self.screen.blit(invincible_text, (10, 100))
        
        # 右上角：倒计时（时间紧迫时变红）
        time_color = RED if remaining <= 10 else WHITE
        time_text = self.big_font.render(f"{minutes:02d}:{seconds:02d}", True, time_color)
        self.screen.blit(time_text, (SCREEN_WIDTH - time_text.get_width() - 10, 10))
        
        # 击败数
        score_text = self.font.render(f"击败: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 10, 60))
        
        # 当前波次/难度提示
        wave_text = self.font.render(f"第 {elapsed // 15 + 1} 波", True, WHITE)
        self.screen.blit(wave_text, (SCREEN_WIDTH - wave_text.get_width() - 10, 90))
        
        # 连击显示（连击数大于1时显示）
        if self.combo_count > 1:
            combo_color = (255, 215, 0) if self.combo_count >= 5 else (255, 165, 0)  # 5连击以上金色
            combo_text = self.big_font.render(f"{self.combo_count} 连击!", True, combo_color)
            combo_x = (SCREEN_WIDTH - combo_text.get_width()) // 2
            combo_y = 100
            # 添加闪烁效果
            if self.combo_timer % 10 < 5:
                self.screen.blit(combo_text, (combo_x, combo_y))
        
        # COMBO计数显示（在右上角）
        remaining = 8 - (self.aoe_use_count % 8)
        aoe_count_color = GOLD if remaining <= 2 else WHITE
        label = "COMBO中!" if self.player.combo_mode else f"COMBO: {remaining}/8"
        aoe_count_text = self.font.render(label, True, aoe_count_color)
        self.screen.blit(aoe_count_text, (SCREEN_WIDTH - aoe_count_text.get_width() - 10, 120))
        
        # COMBO模式倒计时
        if self.player.combo_mode:
            combo_remain = self.player.combo_timer // 60 + 1
            combo_timer_text = self.font.render(f"剩余 {combo_remain}秒", True, GOLD)
            self.screen.blit(combo_timer_text, (SCREEN_WIDTH - combo_timer_text.get_width() - 10, 150))
        
        # AOE技能状态
        aoe_damage = self.player.damage * 5  # 与get_aoe_release_data返回值一致
        
        if self.player.combo_mode:
            # COMBO模式 - 无冷却
            combo_text = self.font.render("AOE无冷却! [疯狂右键]", True, GOLD)
            self.screen.blit(combo_text, (10, SCREEN_HEIGHT - 90))
            aoe_damage_text = self.font.render(f"AOE伤害: {aoe_damage}", True, (100, 255, 100))
            self.screen.blit(aoe_damage_text, (10, SCREEN_HEIGHT - 65))
        elif self.player.aoe_cooldown > 0:
            # 冷却中 - 显示进度
            cooldown_percent = 1 - (self.player.aoe_cooldown / self.player.aoe_cooldown_max)
            bar_width = 100
            bar_height = 10
            bar_x = 10
            bar_y = SCREEN_HEIGHT - 90
            
            # 背景条
            pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            # 进度条
            fill_width = int(bar_width * cooldown_percent)
            pygame.draw.rect(self.screen, (100, 200, 100), (bar_x, bar_y, fill_width, bar_height))
            # 边框
            pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)
            
            aoe_text = self.font.render(f"AOE冷却: {self.player.aoe_cooldown // 10 + 1}s", True, WHITE)
            self.screen.blit(aoe_text, (bar_x + bar_width + 10, bar_y - 5))
            
            # 显示AOE伤害
            aoe_damage_text = self.font.render(f"AOE伤害: {aoe_damage}", True, (100, 255, 100))
            self.screen.blit(aoe_damage_text, (10, SCREEN_HEIGHT - 65))
        else:
            # 就绪状态
            aoe_text = self.font.render("AOE就绪 [右键单击]", True, (100, 255, 100))
            self.screen.blit(aoe_text, (10, SCREEN_HEIGHT - 90))
            
            # 显示AOE伤害
            aoe_damage_text = self.font.render(f"AOE伤害: {aoe_damage}", True, (100, 255, 100))
            self.screen.blit(aoe_damage_text, (10, SCREEN_HEIGHT - 65))
        
        # 操作提示
        hint_text = self.font.render("WASD移动 自动射击 坚持95秒获胜！", True, WHITE)
        self.screen.blit(hint_text, (10, SCREEN_HEIGHT - 35))
    
    def draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 结果文字
        if self.victory:
            result_text = self.big_font.render("胜利！", True, GOLD)
        else:
            result_text = self.big_font.render("游戏结束", True, RED)
        
        text_rect = result_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(result_text, text_rect)
        
        # 统计数据
        stats = [
            f"最终伤害: {self.player.damage}",
            f"剩余生命: {self.player.lives}/{self.player.max_lives}",
            f"击败僵尸: {self.score}",
        ]
        
        y_offset = 0
        for stat in stats:
            stat_text = self.font.render(stat, True, WHITE)
            stat_rect = stat_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
            self.screen.blit(stat_text, stat_rect)
            y_offset += 40
        
        # 提示文字
        hint_text = self.font.render("按 R 重新开始 或 ESC 返回菜单", True, YELLOW)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self.screen.blit(hint_text, hint_rect)
    
    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return 'exit'
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return 'menu'
                
                if self.game_over and event.key == pygame.K_r:
                    self.restart = True
                    self.running = False
                    return 'restart'
        
        return None
    
    def show_rules(self):
        """
        显示游戏规则说明页面
        
        设计思路:
            在游戏开始前显示完整规则，帮助玩家理解核心玩法和技能
        """
        rules = [
            "超燃豌豆射手",
            "",
            "WASD移动  |  自动射击  |  右键AOE",
            "",
            "击败僵尸提升伤害，存活95秒获胜",
            "",
            "右键释放范围爆炸，每8次触发COMBO模式",
            "",
            "按任意键开始..."
        ]
        
        # 绘制半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        
        # 绘制标题
        title_font = get_font(40)
        title_text = title_font.render(rules[0], True, GOLD)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title_text, title_rect)

        # 绘制规则内容
        content_font = get_font(24)
        y_offset = 150
        for line in rules[1:]:
            if not line:
                y_offset += 18
                continue
            
            if "按任意键" in line:
                text_color = (180, 180, 180)
            else:
                text_color = WHITE
            
            text_surface = content_font.render(line, True, text_color)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text_surface, text_rect)
            y_offset += 36
        
        pygame.display.flip()
        
        # 等待玩家按键
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    waiting = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
            self.clock.tick(60)
        
        return True
    
    def run(self):
        """
        运行游戏主循环
        
        返回:
            bool - True表示返回主菜单，False表示退出游戏
        """
        # 显示游戏规则
        if not self.show_rules():
            return False
        
        while self.running:
            result = self.handle_events()
            if result == 'exit':
                return False
            if result == 'menu':
                return True
            if result == 'restart':
                # 重新开始游戏
                new_game = GameManager(self.difficulty, self.theme)
                return new_game.run()
            
            if not self.game_over:
                self.update()
            
            self.draw_game()
            
            if self.game_over:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # 游戏结束，根据标志返回相应值
        if self.final_boss_defeated:
            return self.return_to_menu
        return True


# ============================================
# 入口函数
# ============================================

def power_growth_mode(difficulty=1, theme=0, relax_mode=False):
    """
    数字战力成长模式入口函数
    
    设计思路:
        供launcher.py调用，统一接口
        
    参数:
        difficulty: int - 难度 (0-3)
        theme: int - 主题 (0-2)
        relax_mode: bool - 解压模式（本模式暂不支持）
        
    返回:
        bool - True表示返回主菜单，False表示退出游戏
        
    修改日志:
        2026-04-03: 初始创建
    """
    game = GameManager(difficulty, theme)
    return game.run()


# ============================================
# 修改日志 (CHANGELOG)
# ============================================
# 2026-04-03: 初始创建，实现基础战力成长玩法
#             - 玩家控制植物移动，自动瞄准射击
#             - 僵尸带战力值，击败后吸收战力
#             - Boss系统：小Boss和大Boss
#             - 战力颜色阶梯：绿→蓝→紫→金
# ============================================

if __name__ == '__main__':
    power_growth_mode()
