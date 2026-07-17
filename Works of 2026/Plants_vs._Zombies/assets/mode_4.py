"""
植物消消乐 - Mode 4
"""

import pygame
import random
import sys
import os

pygame.init()
pygame.font.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
GOLD = (255, 215, 0)

GRID_SIZE = 8
CELL_SIZE = 60
GRID_OFFSET_X = (SCREEN_WIDTH - GRID_SIZE * CELL_SIZE) // 2
GRID_OFFSET_Y = 120

PLANT_TYPES = ['peashooter', 'sunflower', 'snow_pea', 'wall_nut']
PLANT_COLORS = {
    'peashooter': GREEN,
    'sunflower': YELLOW,
    'snow_pea': BLUE,
    'wall_nut': BROWN
}

# 胜利目标分数
WIN_SCORE = 1000


def load_image(name):
    try:
        paths = {
            'peashooter': os.path.join(os.path.dirname(__file__), 'plants', 'peashooter', 'wd.png'),
            'sunflower': os.path.join(os.path.dirname(__file__), 'plants', 'sunflower', 'hb.png'),
            'snow_pea': os.path.join(os.path.dirname(__file__), 'plants', 'snow_pea', 'xrk.png'),
            'wall_nut': os.path.join(os.path.dirname(__file__), 'plants', 'wall_nut', 'xdfz.png'),
            'cherry': os.path.join(os.path.dirname(__file__), 'plants', 'cherry_bomb', 'ytzd.png')
        }
        return pygame.image.load(paths[name])
    except:
        return None


class SoundManager:
    """音效管理器"""
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.load_sounds()
    
    def load_sounds(self):
        """加载音效 - 从xiao文件夹"""
        sound_files = {
            'swap': 'sounds/xiao/交换.mp3',
            'match1': 'sounds/xiao/消除.mp3',
            'match2': 'sounds/xiao/消除2.mp3',
            'match3': 'sounds/xiao/消除3.mp3',
            'match4': 'sounds/xiao/消除4.mp3',
            'good': 'sounds/xiao/good.mp3',
            'unbelievable': 'sounds/xiao/unbelievable.mp3',
            'win': 'winmusic.mp3',
            'select': 'seedlift.mp3',
            'fall': 'sounds/xiao/消除2.mp3'
        }
        
        for name, filename in sound_files.items():
            try:
                path = os.path.join(os.path.dirname(__file__), filename)
                self.sounds[name] = pygame.mixer.Sound(path)
            except:
                self.sounds[name] = None
    
    def play(self, name):
        """播放音效"""
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()
    
    def play_match(self, match_count):
        """根据消除数量播放对应音效"""
        if match_count >= 4 and self.sounds.get('match4'):
            self.sounds['match4'].play()
        elif match_count >= 3 and self.sounds.get('match3'):
            self.sounds['match3'].play()
        elif match_count >= 2 and self.sounds.get('match2'):
            self.sounds['match2'].play()
        elif self.sounds.get('match1'):
            self.sounds['match1'].play()
    
    def play_combo(self, combo_count):
        """播放连消奖励音效"""
        if combo_count >= 3:
            if self.sounds.get('unbelievable'):
                self.sounds['unbelievable'].play()
        elif combo_count == 2:
            if self.sounds.get('good'):
                self.sounds['good'].set_volume(1.0)  # 最大音量
                self.sounds['good'].play()


class Cell:
    def __init__(self, row, col, plant_type):
        self.row = row
        self.col = col
        self.type = plant_type
        self.image = load_image(plant_type)
        self.selected = False
        self.anim_x = 0
        self.anim_y = 0
        self.scale = 1.0
        self.alpha = 255
        
    def get_screen_pos(self):
        x = GRID_OFFSET_X + self.col * CELL_SIZE + self.anim_x
        y = GRID_OFFSET_Y + self.row * CELL_SIZE + self.anim_y
        return x, y
        
    def draw(self, screen):
        x, y = self.get_screen_pos()
        
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        if self.selected:
            pygame.draw.rect(screen, YELLOW, rect)
        else:
            pygame.draw.rect(screen, GRAY, rect)
        pygame.draw.rect(screen, DARK_GRAY, rect, 2)
        
        if self.image and self.alpha > 0:
            img = self.image.copy()
            if self.alpha < 255:
                img.set_alpha(self.alpha)
            size = int(CELL_SIZE * self.scale)
            if size > 0:
                img = pygame.transform.scale(img, (size, size))
                img_rect = img.get_rect(center=(x + CELL_SIZE//2, y + CELL_SIZE//2))
                screen.blit(img, img_rect)
        else:
            color = PLANT_COLORS.get(self.type, GREEN)
            r = int(20 * self.scale)
            if r > 0:
                pygame.draw.circle(screen, color, (x + CELL_SIZE//2, y + CELL_SIZE//2), r)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('植物消消乐')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('SimSun', 28, bold=True)
        self.small_font = pygame.font.SysFont('SimSun', 22, bold=True)
        self.big_font = pygame.font.SysFont('SimSun', 48, bold=True)
        
        # 初始化音效
        self.sounds = SoundManager()
        
        self.reset()
        
        try:
            self.background = pygame.image.load(os.path.join(os.path.dirname(__file__), 'background', 'back.png'))
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.background = None
        
        try:
            pygame.mixer.music.load(os.path.join(os.path.dirname(__file__), 'music', 'peaceful.mp3'))
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
        except:
            pass
    
    def reset(self):
        self.grid = []
        self.score = 0
        self.selected_cell = None
        self.animating = False
        self.swap_cells_pair = None
        self.swap_progress = 0
        self.matches_to_remove = []
        self.falling_cells = []
        self.game_won = False
        self.win_animation_time = 0
        self.combo_count = 0  # 连消计数
        self.last_action_matches = 0  # 本次行动的消除组数
        self.elapsed_time = 0  # 正计时（秒）
        self.create_grid()
        
        # 初始消除匹配，直到没有匹配为止
        while True:
            matches = self.find_matches()
            if not matches:
                break
            # 直接移除匹配，不播放动画
            for row, col in matches:
                self.grid[row][col] = None
            self.fill_empty_no_anim()
    
    def create_grid(self):
        self.grid = []
        for row in range(GRID_SIZE):
            row_cells = []
            for col in range(GRID_SIZE):
                plant_type = random.choice(PLANT_TYPES)
                row_cells.append(Cell(row, col, plant_type))
            self.grid.append(row_cells)
    
    def get_cell_at_pos(self, pos):
        x, y = pos
        if GRID_OFFSET_X <= x < GRID_OFFSET_X + GRID_SIZE * CELL_SIZE:
            if GRID_OFFSET_Y <= y < GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE:
                col = (x - GRID_OFFSET_X) // CELL_SIZE
                row = (y - GRID_OFFSET_Y) // CELL_SIZE
                if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                    return self.grid[row][col]
        return None
    
    def find_matches(self):
        matches = set()
        
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE - 2):
                t = self.grid[row][col].type
                if t == self.grid[row][col+1].type == self.grid[row][col+2].type:
                    matches.add((row, col))
                    matches.add((row, col+1))
                    matches.add((row, col+2))
        
        for row in range(GRID_SIZE - 2):
            for col in range(GRID_SIZE):
                t = self.grid[row][col].type
                if t == self.grid[row+1][col].type == self.grid[row+2][col].type:
                    matches.add((row, col))
                    matches.add((row+1, col))
                    matches.add((row+2, col))
        
        return matches
    
    def start_swap(self, cell1, cell2):
        if abs(cell1.row - cell2.row) + abs(cell1.col - cell2.col) != 1:
            return False
        
        self.swap_cells_pair = (cell1, cell2)
        self.swap_progress = 0
        self.animating = True
        
        # 播放交换音效
        self.sounds.play('swap')
        
        dx = cell2.col - cell1.col
        dy = cell2.row - cell1.row
        self.swap_direction = (dx * CELL_SIZE, dy * CELL_SIZE)
        
        return True
    
    def update_swap_animation(self, dt):
        if not self.swap_cells_pair:
            return
        
        speed = 10
        self.swap_progress += speed
        
        cell1, cell2 = self.swap_cells_pair
        dx, dy = self.swap_direction
        progress = min(self.swap_progress / CELL_SIZE, 1.0)
        
        cell1.anim_x = dx * progress
        cell1.anim_y = dy * progress
        cell2.anim_x = -dx * progress
        cell2.anim_y = -dy * progress
        
        if self.swap_progress >= CELL_SIZE:
            # 交换完成，检查匹配
            cell1.anim_x = 0
            cell1.anim_y = 0
            cell2.anim_x = 0
            cell2.anim_y = 0
            
            # 交换类型
            cell1.type, cell2.type = cell2.type, cell1.type
            cell1.image, cell2.image = cell2.image, cell1.image
            
            matches = self.find_matches()
            if matches:
                self.matches_to_remove = list(matches)
                self.swap_cells_pair = None
                self.animating = False
            else:
                # 无匹配，交换回来
                cell1.type, cell2.type = cell2.type, cell1.type
                cell1.image, cell2.image = cell2.image, cell1.image
                self.swap_cells_pair = None
                self.animating = False
                if self.selected_cell:
                    self.selected_cell.selected = False
                self.selected_cell = None
    
    def update_remove_animation(self, dt):
        if not self.matches_to_remove:
            return
        
        speed = 15
        all_done = True
        
        for row, col in self.matches_to_remove:
            cell = self.grid[row][col]
            if cell:
                cell.scale -= 0.1
                cell.alpha -= 25
                if cell.scale > 0 and cell.alpha > 0:
                    all_done = False
        
        if all_done:
            # 计算本次消除了多少组（每3个为一组）
            match_groups = len(self.matches_to_remove) // 3
            if len(self.matches_to_remove) % 3 > 0:
                match_groups += 1
            
            # 增加连消计数
            self.combo_count += 1
            self.last_action_matches += match_groups
            
            # 播放消除音效（根据消除数量）
            self.sounds.play_match(len(self.matches_to_remove))
            
            self.score += len(self.matches_to_remove) * 10
            for row, col in self.matches_to_remove:
                self.grid[row][col] = None
            self.matches_to_remove = []
            self.start_fall_animation()
            
            # 检查是否达到胜利条件
            if self.score >= WIN_SCORE and not self.game_won:
                self.game_won = True
                self.sounds.play('win')
    
    def fill_empty_no_anim(self):
        # 无动画填充空格
        for col in range(GRID_SIZE):
            plants = []
            for row in range(GRID_SIZE):
                if self.grid[row][col] is not None:
                    plants.append(self.grid[row][col].type)
            # 补充新植物
            while len(plants) < GRID_SIZE:
                plants.insert(0, random.choice(PLANT_TYPES))
            # 重新创建格子
            for row in range(GRID_SIZE):
                self.grid[row][col] = Cell(row, col, plants[row])

    def start_fall_animation(self):
        self.falling_cells = []
        for col in range(GRID_SIZE):
            empty_count = 0
            for row in range(GRID_SIZE - 1, -1, -1):
                if self.grid[row][col] is None:
                    empty_count += 1
                elif empty_count > 0:
                    cell = self.grid[row][col]
                    self.grid[row][col] = None
                    self.grid[row + empty_count][col] = cell
                    cell.row = row + empty_count
                    cell.anim_y = -empty_count * CELL_SIZE
                    self.falling_cells.append(cell)
            
            # 生成新植物
            for i in range(empty_count):
                new_cell = Cell(i, col, random.choice(PLANT_TYPES))
                new_cell.anim_y = -(empty_count - i) * CELL_SIZE - CELL_SIZE
                self.grid[i][col] = new_cell
                self.falling_cells.append(new_cell)
        
        # 播放下落音效
        if self.falling_cells:
            self.sounds.play('fall')
    
    def update_fall_animation(self, dt):
        if not self.falling_cells:
            return
        
        speed = 15
        still_falling = False
        
        for cell in self.falling_cells:
            if cell.anim_y < 0:
                cell.anim_y += speed
                if cell.anim_y > 0:
                    cell.anim_y = 0
                still_falling = True
            elif cell.anim_y > 0:
                cell.anim_y -= speed
                if cell.anim_y < 0:
                    cell.anim_y = 0
                still_falling = True
        
        if not still_falling:
            self.falling_cells = []
            # 检查新匹配
            matches = self.find_matches()
            if matches:
                self.matches_to_remove = list(matches)
            else:
                # 没有新匹配，本次行动结束，播放连消奖励音效
                if self.combo_count >= 2:
                    self.sounds.play_combo(self.combo_count)
                # 重置连消计数
                self.combo_count = 0
                self.last_action_matches = 0
    
    def update(self, dt):
        if self.game_won:
            self.win_animation_time += dt
            return
        
        # 正计时
        self.elapsed_time += dt
            
        if self.swap_cells_pair:
            self.update_swap_animation(dt)
        elif self.matches_to_remove:
            self.update_remove_animation(dt)
        elif self.falling_cells:
            self.update_fall_animation(dt)
    
    def draw(self):
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((100, 180, 100))
        
        # 标题
        title = self.font.render('植物消消乐', True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - 60, 10))
        
        # 分数显示
        score_text = self.small_font.render(f'分数: {self.score}', True, WHITE)
        self.screen.blit(score_text, (10, 45))
        
        # 目标分数
        target_text = self.small_font.render(f'目标: {WIN_SCORE}', True, GOLD)
        self.screen.blit(target_text, (10, 70))
        
        # 时间显示
        time_text = self.small_font.render(f'时间: {int(self.elapsed_time)}秒', True, WHITE)
        self.screen.blit(time_text, (10, 95))
        
        # 进度条背景
        bar_width = 200
        bar_height = 20
        bar_x = SCREEN_WIDTH - bar_width - 20
        bar_y = 60
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
        
        # 进度条
        progress = min(self.score / WIN_SCORE, 1.0)
        pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, int(bar_width * progress), bar_height))
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # 进度文字
        progress_text = self.small_font.render(f'{int(progress * 100)}%', True, WHITE)
        self.screen.blit(progress_text, (bar_x + bar_width//2 - 15, bar_y + 25))
        
        # 绘制网格
        for row in self.grid:
            for cell in row:
                if cell:
                    cell.draw(self.screen)
        
        # 提示
        if not self.game_won:
            hint = self.small_font.render('点击两个相邻植物交换', True, WHITE)
            self.screen.blit(hint, (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT - 30))
        
        # 胜利画面
        if self.game_won:
            # 半透明遮罩
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            # 胜利文字
            win_text = self.big_font.render('胜利!', True, GOLD)
            win_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(win_text, win_rect)
            
            # 最终分数
            final_score = self.font.render(f'最终分数: {self.score}', True, WHITE)
            score_rect = final_score.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10))
            self.screen.blit(final_score, score_rect)
            
            # 耗时
            time_used = self.font.render(f'耗时: {int(self.elapsed_time)}秒', True, GOLD)
            time_rect = time_used.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(time_used, time_rect)
            
            # 提示继续
            continue_text = self.small_font.render('点击任意处继续', True, WHITE)
            continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
            # 闪烁效果
            if int(self.win_animation_time * 3) % 2 == 0:
                self.screen.blit(continue_text, continue_rect)
    
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
        
        # 胜利后点击返回主菜单
        if self.game_won:
            if event.type == pygame.MOUSEBUTTONDOWN:
                return False
            return True
        
        if self.animating or self.swap_cells_pair or self.matches_to_remove or self.falling_cells:
            return True
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                cell = self.get_cell_at_pos(event.pos)
                if cell:
                    # 播放选择音效
                    self.sounds.play('select')
                    
                    if self.selected_cell is None:
                        self.selected_cell = cell
                        cell.selected = True
                    elif self.selected_cell == cell:
                        self.selected_cell.selected = False
                        self.selected_cell = None
                    else:
                        if self.start_swap(self.selected_cell, cell):
                            self.selected_cell.selected = False
                            self.selected_cell = None
                        else:
                            self.selected_cell.selected = False
                            self.selected_cell = cell
                            cell.selected = True
        
        return True
    
    def run(self):
        running = True
        back_to_launcher = False
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if not self.handle_event(event):
                    if self.game_won and event.type == pygame.MOUSEBUTTONDOWN:
                        back_to_launcher = True
                    running = False
            
            self.update(dt)
            self.draw()
            pygame.display.flip()
        
        pygame.mixer.music.stop()
        return back_to_launcher


def match3_mode():
    return Game().run()


if __name__ == '__main__':
    match3_mode()
