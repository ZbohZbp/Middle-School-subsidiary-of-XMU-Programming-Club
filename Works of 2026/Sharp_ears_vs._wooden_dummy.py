# Sharp_ears_vs._wooden_dummy.py
# 钟馗抓鬼 —— 唐钰杰，林泽楠

import pygame
import sys

# --- 初始化 Pygame ---
pygame.init()

# --- 常量定义 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLUE = (135, 206, 235)  # 天空蓝
RED = (255, 0, 0)       # 玩家红/血条红
BROWN = (139, 69, 19)   # 平台棕
BLACK = (0, 0, 0)       # 文字黑
GREEN = (0, 255, 0)     # 能量条绿色
YELLOW = (255, 255, 0)  # 能量条黄色
ORANGE = (255, 165, 0)  # 能量条橙色
GRAY = (100, 100, 100)  # 禁用状态灰色
DARK_BLUE = (0, 0, 139) # 深色边框
PURPLE = (128, 0, 128)  # 技能特效色
CYAN = (0, 255, 255)    # 刀光颜色 - 更加明亮显眼
GOLD = (255, 215, 0)    # 第二阶段刀光颜色
# 新增/修改：为木桩角色定义新颜色
MUZHUANG_COLOR = (0, 128, 0)  # 深绿色，代表木桩

# 物理常量
GRAVITY = 0.8
JUMP_STRENGTH = -16
MOVE_SPEED = 5
MOVE_SPEED_SLOW = 2     # 攻击时的移动速度
MAX_JUMPS = 2           # 最大跳跃次数（二段跳）

# UI 布局常量
UI_X = 10
UI_Y_START = 10
BAR_WIDTH = 200
BAR_HEIGHT = 20
BAR_SPACING = 5

# 血量常量
HP_MAX = 200
HP_RECOVERY_RATE = 5.0  # 每秒回复血量

# 能量条常量
ENERGY_MAX = 100
ENERGY_COST_JUMP = 5    # 二段跳消耗
ENERGY_RECOVERY_RATE = 1.5  # 恢复速度
ENERGY_COST_ATTACK = 1  # 普通攻击消耗

# 技能常量
DASH_COST = 7
DASH_COOLDOWN_TIME = 3.0  # 秒
DASH_DISTANCE = 120       # 闪现距离

# 攻击常量
GROUND_ATTACK_COOLDOWN = 0.7  # 地面普攻冷却
AIR_ATTACK_COOLDOWN = 0.37    # 空中普攻冷却
ATTACK_PHASE_DURATION = 0.3   # 每个阶段持续时间
ATTACK_DAMAGE = 15            # 普通攻击伤害
TOTAL_GROUND_ATTACK_DURATION = ATTACK_PHASE_DURATION * 2 # 地面总动作时长 0.6秒
TOTAL_AIR_ATTACK_DURATION = ATTACK_PHASE_DURATION        # 空中总动作时长 0.3秒

# 修改：将 Player 类重命名为 ShunFengEr (顺风耳)
class ShunFengEr(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill(RED)  # 顺风耳保持红色
        self.rect = self.image.get_rect()
        self.rect.center = (100, SCREEN_HEIGHT - 150)  # 初始位置靠左
        
        self.vel_y = 0
        self.on_ground = False
        self.jump_count = 0
        
        # 状态系统
        self.hp = HP_MAX
        self.energy = ENERGY_MAX
        self.last_update_time = pygame.time.get_ticks()
        
        # 技能系统
        self.dash_cooldown = 0.0  
        
        # 朝向系统: 1 表示向右, -1 表示向左
        self.facing = 1 
        
        # 攻击系统
        self.attack_cooldown = 0.0
        self.is_attacking = False
        self.attack_timer = 0.0
        self.attack_phase = 0 # 0: 未攻击, 1: 第一阶段(斜下), 2: 第二阶段(斜上)
        self.is_air_attack = False # 标记当前是否为空中攻击
        self.attack_hit_done = False # 本次攻击是否已造成伤害

    def jump(self):
        """处理跳跃逻辑"""
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
            self.jump_count = 1
            return True
        elif self.jump_count < MAX_JUMPS:
            if self.jump_count == 0:
                self.vel_y = JUMP_STRENGTH
                self.jump_count += 1
                return True
            elif self.jump_count == 1:
                if self.energy >= ENERGY_COST_JUMP:
                    self.vel_y = JUMP_STRENGTH
                    self.jump_count += 1
                    self.energy -= ENERGY_COST_JUMP
                    return True
                else:
                    return False
        return False

    def dash(self):
        """释放闪现技能"""
        if self.dash_cooldown > 0:
            return False
        if self.energy < DASH_COST:
            return False
        
        self.rect.x += DASH_DISTANCE * self.facing
        
        # 边界检查
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            
        self.energy -= DASH_COST
        self.dash_cooldown = DASH_COOLDOWN_TIME
        return True

    def attack(self, is_on_ground):
        """
        释放普通近战攻击
        is_on_ground: bool, 角色是否在地面
        """
        if self.attack_cooldown > 0:
            return False
        if self.energy < ENERGY_COST_ATTACK:
            return False
        
        self.energy -= ENERGY_COST_ATTACK
        self.is_air_attack = not is_on_ground
        self.attack_hit_done = False
        
        if is_on_ground:
            # 地面攻击：完整流程，长冷却
            self.attack_cooldown = GROUND_ATTACK_COOLDOWN
            self.attack_timer = TOTAL_GROUND_ATTACK_DURATION
            self.attack_phase = 1 # 从第一阶段开始
        else:
            # 空中攻击：跳过第一阶段，直接第二阶段，短冷却，不减速逻辑在update中处理
            self.attack_cooldown = AIR_ATTACK_COOLDOWN
            self.attack_timer = TOTAL_AIR_ATTACK_DURATION
            self.attack_phase = 2 # 直接从第二阶段开始
            
        self.is_attacking = True
        return True

    def get_attack_hitbox(self):
        """获取当前攻击命中的碰撞区域"""
        if self.attack_phase == 1:
            width, height = 60, 50
            x = self.rect.right if self.facing == 1 else self.rect.left - width
            y = self.rect.centery - 20
        else:
            width, height = 70, 45
            x = self.rect.right if self.facing == 1 else self.rect.left - width
            y = self.rect.top + 5

        return pygame.Rect(x, y, width, height)

    def try_damage_target(self, target):
        """若攻击命中目标，则对目标造成伤害一次"""
        if not self.is_attacking or self.attack_hit_done:
            return
        if self.attack_phase not in (1, 2):
            return

        if self.get_attack_hitbox().colliderect(target.rect):
            target.hp = max(0, target.hp - ATTACK_DAMAGE)
            self.attack_hit_done = True

    def update(self, platforms, targets=None):
        current_time = pygame.time.get_ticks()
        time_passed = (current_time - self.last_update_time) / 1000.0
        self.last_update_time = current_time
        
        # 1. 血量恢复
        if self.hp < HP_MAX:
            self.hp += HP_RECOVERY_RATE * time_passed
            if self.hp > HP_MAX:
                self.hp = HP_MAX
        
        # 2. 能量恢复
        if self.energy < ENERGY_MAX:
            self.energy += ENERGY_RECOVERY_RATE * time_passed
            if self.energy > ENERGY_MAX:
                self.energy = ENERGY_MAX
        
        # 3. 技能冷却减少
        if self.dash_cooldown > 0:
            self.dash_cooldown -= time_passed
            if self.dash_cooldown < 0:
                self.dash_cooldown = 0
        
        # 4. 攻击状态管理
        if self.attack_cooldown > 0:
            self.attack_cooldown -= time_passed
            if self.attack_cooldown < 0:
                self.attack_cooldown = 0
        
        if self.is_attacking:
            self.attack_timer -= time_passed
            
            # 地面攻击的阶段切换逻辑
            if not self.is_air_attack and self.attack_phase == 1 and self.attack_timer <= ATTACK_PHASE_DURATION:
                self.attack_phase = 2 # 切换到第二阶段
            
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.attack_phase = 0
                self.is_air_attack = False
                self.attack_hit_done = False

        # 5. 处理攻击命中判定（在移动前后都可以，但这里放在移动前更直观）
        if targets:
            for target in targets:
                self.try_damage_target(target)

        # 6. 水平移动与朝向更新
        keys = pygame.key.get_pressed()
        moving_left = keys[pygame.K_a]
        moving_right = keys[pygame.K_d]
        
        # 攻击期间降低移动速度逻辑：
        # 只有在地面攻击(is_attacking 且 非 is_air_attack)时才减速
        # 空中攻击不减速
        is_ground_attacking = self.is_attacking and not self.is_air_attack
        current_speed = MOVE_SPEED_SLOW if is_ground_attacking else MOVE_SPEED
        
        if moving_left:
            self.rect.x -= current_speed
            self.facing = -1
        if moving_right:
            self.rect.x += current_speed
            self.facing = 1
            
        # 边界限制
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # 7. 重力与垂直移动
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # 8. 碰撞检测
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.bottom + self.vel_y:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_count = 0

# 新增：创建木桩角色类
class MuZhuang(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill(MUZHUANG_COLOR)  # 木桩使用深绿色
        self.rect = self.image.get_rect()
        self.rect.center = (700, SCREEN_HEIGHT - 150)  # 初始位置靠右，与顺风耳区分
        
        self.vel_y = 0
        self.on_ground = False
        self.jump_count = 0
        
        # 状态系统（与顺风耳相同）
        self.hp = HP_MAX
        self.energy = ENERGY_MAX
        self.last_update_time = pygame.time.get_ticks()
        
        # 技能系统（木桩没有闪现和攻击，所以不需要相关属性）
        # 朝向系统: 1 表示向右, -1 表示向左
        self.facing = 1 

    def jump(self):
        """处理跳跃逻辑（与顺风耳完全相同）"""
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
            self.jump_count = 1
            return True
        elif self.jump_count < MAX_JUMPS:
            if self.jump_count == 0:
                self.vel_y = JUMP_STRENGTH
                self.jump_count += 1
                return True
            elif self.jump_count == 1:
                if self.energy >= ENERGY_COST_JUMP:
                    self.vel_y = JUMP_STRENGTH
                    self.jump_count += 1
                    self.energy -= ENERGY_COST_JUMP
                    return True
                else:
                    return False
        return False

    def update(self, platforms):
        """更新木桩状态（仅包含移动、跳跃、血量和能量恢复，无攻击和闪现）"""
        current_time = pygame.time.get_ticks()
        time_passed = (current_time - self.last_update_time) / 1000.0
        self.last_update_time = current_time
        
        # 1. 血量恢复（与顺风耳相同）
        if self.hp < HP_MAX:
            self.hp += HP_RECOVERY_RATE * time_passed
            if self.hp > HP_MAX:
                self.hp = HP_MAX
        
        # 2. 能量恢复（与顺风耳相同）
        if self.energy < ENERGY_MAX:
            self.energy += ENERGY_RECOVERY_RATE * time_passed
            if self.energy > ENERGY_MAX:
                self.energy = ENERGY_MAX

        # 3. 水平移动与朝向更新（使用不同的控制键）
        keys = pygame.key.get_pressed()
        moving_left = keys[pygame.K_LEFT]   # 左箭头
        moving_right = keys[pygame.K_RIGHT] # 右箭头
        
        # 木桩移动不减速，因为它没有攻击
        current_speed = MOVE_SPEED
        
        if moving_left:
            self.rect.x -= current_speed
            self.facing = -1
        if moving_right:
            self.rect.x += current_speed
            self.facing = 1
            
        # 边界限制
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # 4. 重力与垂直移动（与顺风耳相同）
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # 5. 碰撞检测（与顺风耳相同）
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.bottom + self.vel_y:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_count = 0

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

def get_font(size):
    font_names = ['microsoftyahei', 'msyh', 'simhei', 'simsun', 'arial']
    for name in font_names:
        try:
            return pygame.font.SysFont(name, size)
        except:
            continue
    return pygame.font.Font(None, size)

# 修改：draw_ui 函数现在需要绘制两个角色的UI
def draw_ui(screen, shunfeng, muzhuang):
    """绘制所有UI元素：两个角色的血条、能量条、技能图标"""
    font_small = get_font(18)
    
    # --- 绘制顺风耳的UI (左侧) ---
    current_y = UI_Y_START + 10
    
    # 1. 绘制顺风耳血条
    hp_text = font_small.render(f"顺风耳 HP: {int(shunfeng.hp)}/{HP_MAX}", True, BLACK)
    screen.blit(hp_text, (UI_X, current_y - 20))
    
    hp_bg_rect = pygame.Rect(UI_X, current_y, BAR_WIDTH, BAR_HEIGHT)
    pygame.draw.rect(screen, BLACK, hp_bg_rect, 2)
    
    hp_percentage = shunfeng.hp / HP_MAX
    hp_color = RED if hp_percentage < 0.3 else GREEN if hp_percentage > 0.6 else YELLOW
    
    hp_fill_width = int(BAR_WIDTH * hp_percentage)
    hp_fill_rect = pygame.Rect(UI_X + 2, current_y + 2, 
                               max(0, hp_fill_width - 4), BAR_HEIGHT - 4)
    pygame.draw.rect(screen, hp_color, hp_fill_rect)
    
    current_y += BAR_HEIGHT + BAR_SPACING
    
    # 2. 绘制顺风耳能量条
    energy_text = font_small.render(f"顺风耳 Energy: {int(shunfeng.energy)}/{ENERGY_MAX}", True, BLACK)
    screen.blit(energy_text, (UI_X, current_y - 20))
    
    energy_bg_rect = pygame.Rect(UI_X, current_y, BAR_WIDTH, BAR_HEIGHT)
    pygame.draw.rect(screen, BLACK, energy_bg_rect, 2)
    
    energy_percentage = shunfeng.energy / ENERGY_MAX
    if energy_percentage > 0.6:
        energy_color = GREEN
    elif energy_percentage > 0.3:
        energy_color = YELLOW
    else:
        energy_color = ORANGE
    
    energy_fill_width = int(BAR_WIDTH * energy_percentage)
    energy_fill_rect = pygame.Rect(UI_X + 2, current_y + 2, 
                                   max(0, energy_fill_width - 4), BAR_HEIGHT - 4)
    pygame.draw.rect(screen, energy_color, energy_fill_rect)
    
    current_y += BAR_HEIGHT + BAR_SPACING + 10 # 增加间距给技能区
    
    # 3. 绘制顺风耳技能指示器
    skill_x = UI_X
    skill_y = current_y
    skill_box_size = 30
    
    # Dash 技能
    dash_rect = pygame.Rect(skill_x, skill_y, skill_box_size, skill_box_size)
    if shunfeng.dash_cooldown > 0:
        dash_color = GRAY
        cooldown_pct = shunfeng.dash_cooldown / DASH_COOLDOWN_TIME
        mask_height = int(skill_box_size * cooldown_pct)
        mask_rect = pygame.Rect(skill_x, skill_y + (skill_box_size - mask_height), skill_box_size, mask_height)
        pygame.draw.rect(screen, (50, 50, 50), mask_rect) 
    else:
        dash_color = PURPLE if shunfeng.energy >= DASH_COST else GRAY 
        
    pygame.draw.rect(screen, BLACK, dash_rect, 2)
    pygame.draw.rect(screen, dash_color, dash_rect.inflate(-4, -4))
    
    if shunfeng.dash_cooldown > 0:
        cd_text = font_small.render(f"{shunfeng.dash_cooldown:.1f}", True, WHITE)
        text_rect = cd_text.get_rect(center=dash_rect.center)
        screen.blit(cd_text, text_rect)
    else:
        key_text = font_small.render("H", True, WHITE)
        text_rect = key_text.get_rect(center=dash_rect.center)
        screen.blit(key_text, text_rect)
        
    dash_label = font_small.render("Dash (H)", True, BLACK)
    screen.blit(dash_label, (skill_x + 40, skill_y + 5))
    
    # Attack 技能
    attack_x = skill_x + 80
    attack_rect = pygame.Rect(attack_x, skill_y, skill_box_size, skill_box_size)
    if shunfeng.attack_cooldown > 0:
        attack_color = GRAY
        max_cd = GROUND_ATTACK_COOLDOWN
        if shunfeng.is_air_attack or (not shunfeng.is_attacking and shunfeng.attack_cooldown < AIR_ATTACK_COOLDOWN + 0.05):
             max_cd = AIR_ATTACK_COOLDOWN
             
        cooldown_pct = shunfeng.attack_cooldown / max_cd
        mask_height = int(skill_box_size * cooldown_pct)
        mask_rect = pygame.Rect(attack_x, skill_y + (skill_box_size - mask_height), skill_box_size, mask_height)
        pygame.draw.rect(screen, (50, 50, 50), mask_rect)
    else:
        attack_color = CYAN if shunfeng.energy >= ENERGY_COST_ATTACK else GRAY
        
    pygame.draw.rect(screen, BLACK, attack_rect, 2)
    pygame.draw.rect(screen, attack_color, attack_rect.inflate(-4, -4))
    
    if shunfeng.attack_cooldown > 0:
        cd_text = font_small.render(f"{shunfeng.attack_cooldown:.2f}", True, WHITE)
        text_rect = cd_text.get_rect(center=attack_rect.center)
        screen.blit(cd_text, text_rect)
    else:
        key_text = font_small.render("J", True, WHITE)
        text_rect = key_text.get_rect(center=attack_rect.center)
        screen.blit(key_text, text_rect)
        
    attack_label = font_small.render("Atk (J)", True, BLACK)
    screen.blit(attack_label, (attack_x + 40, skill_y + 5))

    # --- 绘制木桩的UI (右侧) ---
    right_ui_x = SCREEN_WIDTH - BAR_WIDTH - UI_X - 20  # 右侧UI起始X坐标
    current_y = UI_Y_START + 10
    
    # 1. 绘制木桩血条
    hp_text_mz = font_small.render(f"木桩 HP: {int(muzhuang.hp)}/{HP_MAX}", True, BLACK)
    screen.blit(hp_text_mz, (right_ui_x, current_y - 20))
    
    hp_bg_rect_mz = pygame.Rect(right_ui_x, current_y, BAR_WIDTH, BAR_HEIGHT)
    pygame.draw.rect(screen, BLACK, hp_bg_rect_mz, 2)
    
    hp_percentage_mz = muzhuang.hp / HP_MAX
    hp_color_mz = MUZHUANG_COLOR if hp_percentage_mz > 0.6 else YELLOW if hp_percentage_mz > 0.3 else (200, 0, 0)  # 深绿 -> 黄 -> 暗红
    
    hp_fill_width_mz = int(BAR_WIDTH * hp_percentage_mz)
    hp_fill_rect_mz = pygame.Rect(right_ui_x + 2, current_y + 2, 
                                  max(0, hp_fill_width_mz - 4), BAR_HEIGHT - 4)
    pygame.draw.rect(screen, hp_color_mz, hp_fill_rect_mz)
    
    current_y += BAR_HEIGHT + BAR_SPACING
    
    # 2. 绘制木桩能量条
    energy_text_mz = font_small.render(f"木桩 Energy: {int(muzhuang.energy)}/{ENERGY_MAX}", True, BLACK)
    screen.blit(energy_text_mz, (right_ui_x, current_y - 20))
    
    energy_bg_rect_mz = pygame.Rect(right_ui_x, current_y, BAR_WIDTH, BAR_HEIGHT)
    pygame.draw.rect(screen, BLACK, energy_bg_rect_mz, 2)
    
    energy_percentage_mz = muzhuang.energy / ENERGY_MAX
    if energy_percentage_mz > 0.6:
        energy_color_mz = GREEN
    elif energy_percentage_mz > 0.3:
        energy_color_mz = YELLOW
    else:
        energy_color_mz = ORANGE
    
    energy_fill_width_mz = int(BAR_WIDTH * energy_percentage_mz)
    energy_fill_rect_mz = pygame.Rect(right_ui_x + 2, current_y + 2, 
                                      max(0, energy_fill_width_mz - 4), BAR_HEIGHT - 4)
    pygame.draw.rect(screen, energy_color_mz, energy_fill_rect_mz)
    
    # 木桩没有技能图标区域


def draw_attack_effect(screen, player):
    """绘制攻击刀光效果（仅对顺风耳有效）"""
    if not player.is_attacking:
        return
    
    # 刀光参数
    slash_width = 50
    slash_height = 70 
    
    # 根据阶段决定颜色和角度
    # 注意：空中攻击直接是 phase 2
    if player.attack_phase == 1:
        color = WHITE
        # 第一阶段：斜向下
        start_pos = (0, 0)
        end_pos = (slash_width, slash_height)
    else: # phase 2
        color = GOLD
        # 第二阶段：斜向上
        start_pos = (0, slash_height)
        end_pos = (slash_width, 0)

    offset_x = 10 if player.facing == 1 else -10 - slash_width
    offset_y = -10 # 稍微向上偏移一点，使其看起来更像挥砍
    
    # 计算刀光位置（相对于角色中心）
    slash_x = player.rect.centerx + offset_x
    slash_y = player.rect.centery - slash_height // 2 + offset_y
    
    # 创建刀光表面
    slash_surface = pygame.Surface((slash_width, slash_height), pygame.SRCALPHA)
    
    # 绘制更粗的线条以增加可见度
    pygame.draw.line(slash_surface, color, start_pos, end_pos, 8)
    # 添加一个内部亮线增加层次感
    pygame.draw.line(slash_surface, CYAN if player.attack_phase == 1 else WHITE, start_pos, end_pos, 4)
    
    # 如果朝向左，翻转图像
    if player.facing == -1:
        slash_surface = pygame.transform.flip(slash_surface, True, False)
        
    screen.blit(slash_surface, (slash_x, slash_y))


def draw_instructions(screen, show_instructions, current_page):
    if not show_instructions:
        return
    
    panel_width = 400  # 稍微加宽以容纳更多内容
    panel_height = 480 
    panel_x = (SCREEN_WIDTH - panel_width) // 2
    panel_y = (SCREEN_HEIGHT - panel_height) // 2
    
    border_width = 5
    padding = 15
    footer_height = 40
    
    content_start_y = panel_y + padding + 35
    content_end_y = panel_y + panel_height - footer_height - 5
    
    info_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    s = pygame.Surface((info_rect.width, info_rect.height), pygame.SRCALPHA)
    s.fill((255, 255, 255, 250))
    screen.blit(s, (info_rect.x, info_rect.y))
    
    pygame.draw.rect(screen, DARK_BLUE, info_rect, border_width)
    
    separator_y = panel_y + panel_height - footer_height
    pygame.draw.line(screen, GRAY, 
                     (panel_x + 5, separator_y), 
                     (panel_x + panel_width - 5, separator_y), 2)

    title_font = get_font(26)
    content_font = get_font(18)
    hint_font = get_font(16)
    
    # 修改：更新帮助页面，包含两个角色的控制说明
    pages = [
        {
            "title": "Page 1: 角色控制",
            "lines": [
                "=== 顺风耳 (红色) ===",
                "[A / D]   : 左右移动",
                "[W]       : 跳跃 / 二段跳",
                "[H]       : 闪现技能",
                "[J]       : 普通攻击",
                "",
                "=== 木桩 (绿色) ===",
                "[← / →]   : 左右移动",
                "[↑]       : 跳跃 / 二段跳",
                "",
                "[P]       : 切换此面板",
                "[ESC]     : 退出游戏",
                "",
                "提示:",
                "地面攻击: 完整连招，会减速。",
                "空中攻击: 快速斩击，无减速。"
            ]
        },
        {
            "title": "Page 2: 系统说明",
            "lines": [
                "通用属性 (两角色相同):",
                "- 最大生命值   : 200",
                "- 生命恢复     : 5 / 秒",
                "- 最大能量值   : 100",
                "- 能量恢复     : 1.5 / 秒",
                "- 二段跳消耗   : 5 能量",
                "",
                "顺风耳专属技能:",
                "- 攻击消耗     : 1 能量",
                "- 闪现消耗     : 7 能量 (3秒冷却)",
                "- 地面攻击冷却 : 0.7 秒",
                "- 空中攻击冷却 : 0.37 秒",
                "",
                "木桩特性:",
                "- 无攻击技能",
                "- 无闪现技能",
                "- 移动不因攻击减速"
            ]
        }
    ]
    
    page_data = pages[current_page]
    
    title_text = title_font.render(page_data["title"], True, BLACK)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 25))
    screen.blit(title_text, title_rect)
    
    y_offset = content_start_y
    line_height = 22
    
    for line in page_data["lines"]:
        if y_offset + line_height > content_end_y:
            break
        if line == "":
            y_offset += 10
            continue
        text_surface = content_font.render(line, True, BLACK)
        screen.blit(text_surface, (panel_x + padding, y_offset))
        y_offset += line_height
        
    footer_y_center = separator_y + (footer_height // 2)
    
    page_indicator = hint_font.render(f"{current_page + 1} / {len(pages)}", True, BLACK)
    ind_rect = page_indicator.get_rect(center=(SCREEN_WIDTH // 2, footer_y_center))
    screen.blit(page_indicator, ind_rect)
    
    prev_color = GRAY if current_page == 0 else BLACK
    next_color = GRAY if current_page == len(pages) - 1 else BLACK
    
    prev_hint = hint_font.render("[ [ Prev", True, prev_color)
    next_hint = hint_font.render("Next ] ]", True, next_color)
    
    screen.blit(prev_hint, (panel_x + 15, footer_y_center - prev_hint.get_height()//2))
    screen.blit(next_hint, (panel_x + panel_width - 15 - next_hint.get_width(), footer_y_center - next_hint.get_height()//2))


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Python RPG: 双角色测试 - 顺风耳 vs 木桩")
    clock = pygame.time.Clock()

    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()

    # 修改：创建两个角色实例
    shunfeng = ShunFengEr()  # 顺风耳
    muzhuang = MuZhuang()    # 木桩
    all_sprites.add(shunfeng, muzhuang)

    ground = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
    all_sprites.add(ground)
    platforms.add(ground)

    plat1 = Platform(300, 450, 150, 20)
    plat2 = Platform(550, 350, 150, 20)
    plat3 = Platform(150, 250, 150, 20)
    
    all_sprites.add(plat1, plat2, plat3)
    platforms.add(plat1, plat2, plat3)

    show_instructions = False
    current_page = 0
    
    show_hint = True
    hint_start_time = pygame.time.get_ticks()
    hint_duration = 3000 

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # 顺风耳的控制
                if event.key == pygame.K_w:
                    shunfeng.jump()
                if event.key == pygame.K_h:
                    shunfeng.dash()
                if event.key == pygame.K_j:  # 按下 J 键攻击
                    # 传入当前是否在地面的状态
                    shunfeng.attack(shunfeng.on_ground)
                # 木桩的控制
                if event.key == pygame.K_UP:  # 上箭头跳跃
                    muzhuang.jump()
                
                # 通用控制
                if event.key == pygame.K_p:
                    show_instructions = not show_instructions
                    show_hint = False
                
                if show_instructions:
                    if event.key == pygame.K_LEFTBRACKET:
                        if current_page > 0:
                            current_page -= 1
                    if event.key == pygame.K_RIGHTBRACKET:
                        if current_page < 1:
                            current_page += 1

        # 更新两个角色状态
        shunfeng.update(platforms, [muzhuang])
        muzhuang.update(platforms)

        screen.fill(BLUE)
        all_sprites.draw(screen)
        
        # 绘制攻击特效（仅顺风耳有）
        draw_attack_effect(screen, shunfeng)
        
        # 绘制 UI（需要传入两个角色）
        draw_ui(screen, shunfeng, muzhuang)
        
        # 绘制帮助面板
        draw_instructions(screen, show_instructions, current_page)
        
        # 绘制初始提示
        if show_hint and current_time - hint_start_time < hint_duration:
            hint_font = get_font(24)
            hint_text = hint_font.render("按 [P] 查看帮助 | 顺风耳: [W][A][D][H][J] | 木桩: [↑][←][→]", True, BLACK)
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            
            hint_bg = pygame.Surface((hint_rect.width + 20, hint_rect.height + 10), pygame.SRCALPHA)
            hint_bg.fill((255, 255, 255, 180))
            screen.blit(hint_bg, (hint_rect.x - 10, hint_rect.y - 5))
            screen.blit(hint_text, hint_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
