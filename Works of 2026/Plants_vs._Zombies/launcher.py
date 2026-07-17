# Plants_vs._Zombies
# 植物大战僵尸 —— 邱浩洋
# PyInstaller -F --hidden-import=pygame --paths C:\Users\xiaot\myenv\Lib\site-packages launcher.py

import pygame
from pygame.locals import *
import os
import time
import math
import sys
import importlib
from pathlib import Path

# 全局初始化，避免重复初始化
pygame.init()
pygame.mixer.init()

def _load_font_from_path(font_path, size, bold=False, italic=False):
    """从指定字体文件路径加载字体，避免依赖 pygame 的字体扫描。"""
    if os.path.exists(font_path):
        try:
            return pygame.font.Font(font_path, size)
        except Exception:
            pass
    return pygame.font.SysFont("Arial", size, bold=bold, italic=italic)


def _get_emoji_font_paths():
    """返回常见可显示 emoji 的 Windows 字体文件路径。"""
    return [
        r"C:\Windows\Fonts\seguiemj.ttf",
        r"C:\Windows\Fonts\seguiemj.ttf",
        r"C:\Windows\Fonts\Segoe UI Emoji.ttf",
        r"C:\Windows\Fonts\NotoColorEmoji.ttf",
        r"C:\Windows\Fonts\AppleColorEmoji.ttf",
        r"C:\Windows\Fonts\twmoemot.ttf",
    ]


def _patch_font_fallback():
    """兼容某些环境下 pygame 字体初始化失败的情况，并优先使用可显示中文和 emoji 的字体。"""
    try:
        pygame.font.init()
    except Exception:
        pass

    preferred_paths = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simkai.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        * _get_emoji_font_paths(),
    ]

    original_sysfont = pygame.font.SysFont

    def safe_sysfont(name, size, bold=False, italic=False):
        if not isinstance(name, str) or not name.strip():
            name = "Microsoft YaHei"

        for candidate in [name, "Microsoft YaHei", "SimSun", "Arial", "simsun", "msyh"]:
            try:
                return original_sysfont(candidate, size, bold=bold, italic=italic)
            except Exception:
                continue

        for path in preferred_paths:
            try:
                return _load_font_from_path(path, size, bold=bold, italic=italic)
            except Exception:
                continue

        try:
            return pygame.font.Font(None, size)
        except Exception:
            return pygame.font.Font(pygame.font.get_default_font(), size)

    pygame.font.SysFont = safe_sysfont

_patch_font_fallback()


def get_game_font(size, bold=False):
    """获取适合显示中文的字体对象。"""
    preferred_paths = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyh.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simkai.ttf",
    ]
    for path in preferred_paths:
        font = _load_font_from_path(path, size, bold=bold)
        if font is not None:
            return font
    return pygame.font.SysFont("Microsoft YaHei", size, bold=bold)


def get_emoji_font(size, bold=False):
    """获取更适合显示 emoji 的字体。"""
    for path in _get_emoji_font_paths():
        font = _load_font_from_path(path, size, bold=bold)
        if font is not None:
            return font
    return get_game_font(size, bold=bold)

# 全局资源缓存
resource_cache = {}

def _ensure_game_import_paths():
    """确保游戏模块和资源目录可以被正确导入。"""
    base_dir = Path(__file__).resolve().parent
    candidate_dirs = [str(base_dir), str(base_dir / "assets")]

    if getattr(sys, "frozen", False):
        bundle_dir = Path(sys.executable).resolve().parent
        candidate_dirs.extend([str(bundle_dir), str(bundle_dir / "assets")])

    meipass_dir = getattr(sys, "_MEIPASS", None)
    if meipass_dir:
        meipass_path = Path(meipass_dir)
        candidate_dirs.extend([str(meipass_path), str(meipass_path / "assets")])

    for path in candidate_dirs:
        if path and path not in sys.path:
            sys.path.insert(0, path)


def _load_game_entry(level):
    """根据关卡号动态加载对应的游戏入口函数。"""
    _ensure_game_import_paths()

    entry_map = {
        1: ("mode_1", "main"),
        2: ("mode_2", "level2"),
        3: ("mode_3", "power_growth_mode"),
        4: ("mode_4", "match3_mode"),
        5: ("mode_5", "court_mode"),
    }

    if level not in entry_map:
        raise ValueError(f"不支持的关卡编号: {level}")

    module_name, func_name = entry_map[level]
    candidates = [module_name, f"assets.{module_name}"]

    last_error = None
    for name in candidates:
        try:
            module = importlib.import_module(name)
            func = getattr(module, func_name)
            return func
        except ModuleNotFoundError as exc:
            last_error = exc
            if exc.name not in {name, "assets", "pygame"}:
                raise

    if last_error:
        raise last_error
    raise ImportError(f"无法找到关卡 {level} 对应的入口模块")


def load_cached_image(path, scale=1.0, alpha=None):
    """加载图片并缓存，避免重复加载"""
    cache_key = f"{path}_{scale}_{alpha}"
    if cache_key in resource_cache:
        return resource_cache[cache_key]
    
    try:
        image = pygame.image.load(path)
        if scale != 1.0:
            width = int(image.get_width() * scale)
            height = int(image.get_height() * scale)
            image = pygame.transform.scale(image, (width, height))
        
        if alpha is not None:
            image = image.convert_alpha()
            image.set_alpha(int(alpha * 255))
        else:
            # 使用convert()加速渲染
            if path.lower().endswith(('.png', '.gif')):
                image = image.convert_alpha()
            else:
                image = image.convert()
        
        resource_cache[cache_key] = image
        return image
    except (pygame.error, FileNotFoundError) as e:
        print(f"警告: 无法加载图片 {path} - {e}")
        # 创建简单占位图
        placeholder = pygame.Surface((50, 50), pygame.SRCALPHA)
        placeholder.fill((255, 0, 0, 128))
        resource_cache[cache_key] = placeholder
        return placeholder

def create_rounded_surface(width, height, color, radius=15):
    """创建圆角矩形表面"""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (0, 0, width, height), border_radius=radius)
    return surface

class SplashScreen:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption('植物大战僵尸')
        self.clock = pygame.time.Clock()
        
        # 预渲染文本
        self.font = get_game_font(20)
        self.skip_text = self.font.render("单击屏幕任意位置跳过", True, (255, 255, 255))
        self.skip_text_rect = self.skip_text.get_rect(center=(400, 570))
        
        # 使用脏矩形技术，只更新需要的区域
        self.dirty_rects = []
        
        # 加载并缓存商标图片
        self.logos = []
        for i in range(3):
            try:
                logo_path = f'assets/ui/{i}.png'
                logo = load_cached_image(logo_path)
                self.logos.append(logo)
            except (pygame.error, FileNotFoundError) as e:
                print(f"警告: 无法加载图片 assets/ui/{i}.png - {e}")
                # 创建一个占位符图片
                placeholder = pygame.Surface((400, 300))
                placeholder.fill((255, 255, 255))
                font = get_game_font(36)
                text = font.render(f"Logo {i}", True, (0, 0, 0))
                placeholder.blit(text, text.get_rect(center=(200, 150)))
                self.logos.append(placeholder)
        
        # 加载启动音频
        try:
            self.gofirst_sound = pygame.mixer.Sound('assets/ui/gofirst.mp3')
            self.gofirst_sound.play()
        except (pygame.error, FileNotFoundError) as e:
            print(f"警告: 无法加载启动音频 gofirst.mp3 - {e}")
            self.gofirst_sound = None
    
    def run(self):
        """运行启动画面，渐显渐隐依次显示三个图片"""
        # 预先计算位置
        center_x, center_y = 400, 300
        
        # 绘制黑色背景一次
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
        
        for logo in self.logos:
            # 计算logo区域
            max_width, max_height = logo.get_width(), logo.get_height()
            logo_rect = pygame.Rect(
                center_x - max_width//2 - 5,  # 稍微扩大区域确保覆盖
                center_y - max_height//2 - 5,
                max_width + 10,
                max_height + 10
            )
            
            # 渐显效果
            for alpha in range(0, 256, 15):  # 更大步长，加快渐显
                if self._handle_events():
                    return  # 用户跳过
                
                # 只重绘logo区域和文本区域
                pygame.draw.rect(self.screen, (0, 0, 0), logo_rect)
                
                # 应用alpha
                temp_logo = logo.copy()
                temp_logo.set_alpha(alpha)
                self.screen.blit(temp_logo, temp_logo.get_rect(center=(center_x, center_y)))
                
                # 绘制闪烁文本
                self._draw_blinking_text()
                
                # 只更新需要的区域
                pygame.display.update([logo_rect, self.skip_text_rect])
                self.clock.tick(60)
            
            # 完全显示一段时间
            start_time = time.time()
            while time.time() - start_time < 0.6:  # 进一步缩短显示时间
                if self._handle_events():
                    return  # 用户跳过
                
                # 只需更新文本区域
                pygame.draw.rect(self.screen, (0, 0, 0), self.skip_text_rect)
                self._draw_blinking_text()
                pygame.display.update(self.skip_text_rect)
                self.clock.tick(60)
            
            # 渐隐效果
            for alpha in range(255, -1, -15):  # 更大步长，加快渐隐
                if self._handle_events():
                    return  # 用户跳过
                
                # 只重绘logo区域和文本区域
                pygame.draw.rect(self.screen, (0, 0, 0), logo_rect)
                
                # 应用alpha
                temp_logo = logo.copy()
                temp_logo.set_alpha(alpha)
                self.screen.blit(temp_logo, temp_logo.get_rect(center=(center_x, center_y)))
                
                # 绘制闪烁文本
                self._draw_blinking_text()
                
                # 只更新需要的区域
                pygame.display.update([logo_rect, self.skip_text_rect])
                self.clock.tick(60)
    
    def _draw_blinking_text(self):
        """绘制闪烁的提示文本"""
        # 使用sin函数使文本慢速闪烁，预计算透明度
        alpha = int(127.5 + 127.5 * math.sin(time.time() * 2))
        text_surface = self.skip_text.copy()
        text_surface.set_alpha(alpha)
        self.screen.blit(text_surface, self.skip_text_rect)
    
    def _handle_events(self):
        """处理事件，允许用户跳过启动画面"""
        for event in pygame.event.get():
            if event.type == QUIT:
                # 使用与MainMenu类一致的退出方式
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_SPACE:
                    # 停止音频播放
                    if self.gofirst_sound:
                        self.gofirst_sound.stop()
                    return True  # 用户跳过
            elif event.type == MOUSEBUTTONDOWN:
                # 停止音频播放
                if self.gofirst_sound:
                    self.gofirst_sound.stop()
                return True  # 鼠标点击跳过
        return False

class LevelButton:
    """统一的关卡按钮类 - 石板风格，向右倾斜"""
    def __init__(self, x, y, plant_image_path, level_num, title, subtitle, scale=0.55):
        self.level_num = level_num
        self.title = title
        self.subtitle = subtitle
        
        # 按钮尺寸 - 石板大小（更大）
        self.width = 260
        self.height = 75
        self.x = x
        self.y = y
        
        # 倾斜角度（向右倾斜3度）
        self.angle = -3
        
        # 加载植物图片或渲染emoji
        if plant_image_path.startswith(":emoji:"):
            emoji_char = plant_image_path[7:]
            emoji_font = get_emoji_font(40)
            self.plant_img = emoji_font.render(emoji_char, True, (50, 50, 50))
        else:
            try:
                self.plant_img = load_cached_image(plant_image_path, scale=scale)
            except:
                self.plant_img = pygame.Surface((45, 45), pygame.SRCALPHA)
                self.plant_img.fill((100, 200, 100, 180))
        
        # 字体
        self.title_font = pygame.font.SysFont('SimSun', 20, bold=True)
        self.sub_font = pygame.font.SysFont('SimSun', 13)
        
        # 预渲染文本
        self.title_text = self.title_font.render(title, True, (50, 50, 50))
        self.sub_text = self.sub_font.render(subtitle, True, (80, 80, 80))
        
        # 石板颜色
        self.normal_color = (140, 140, 130)
        self.hover_color = (160, 160, 150)
        self.border_color = (100, 100, 90)
        
        # 创建倾斜的按钮表面
        self._create_surfaces()
        
    def _create_surfaces(self):
        """创建倾斜后的按钮表面"""
        # 创建按钮基础表面
        button_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 绘制石板背景
        pygame.draw.rect(button_surface, (*self.normal_color, 255), 
                        (0, 0, self.width, self.height), border_radius=8)
        # 绘制石板边框
        pygame.draw.rect(button_surface, self.border_color, 
                        (0, 0, self.width, self.height), 3, border_radius=8)
        
        # 绘制高光效果（顶部浅色条纹）
        highlight_height = 8
        highlight_color = (180, 180, 170)
        pygame.draw.rect(button_surface, (*highlight_color, 255),
                        (3, 3, self.width - 6, highlight_height), border_radius=4)
        
        # 绘制植物图片
        plant_x = 25
        plant_y = self.height // 2
        self.plant_rect = self.plant_img.get_rect(center=(plant_x, plant_y))
        button_surface.blit(self.plant_img, self.plant_rect)
        
        # 绘制标题和副标题
        text_x = 70
        title_y = self.height // 2 - 8
        sub_y = self.height // 2 + 12
        button_surface.blit(self.title_text, (text_x, title_y))
        button_surface.blit(self.sub_text, (text_x, sub_y))
        
        # 旋转按钮
        self.button_normal = pygame.transform.rotate(button_surface, self.angle)
        
        # 创建悬停版本
        hover_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(hover_surface, (*self.hover_color, 255),
                        (0, 0, self.width, self.height), border_radius=8)
        pygame.draw.rect(hover_surface, self.border_color,
                        (0, 0, self.width, self.height), 3, border_radius=8)
        pygame.draw.rect(hover_surface, (180, 180, 170),
                        (3, 3, self.width - 6, highlight_height), border_radius=4)
        hover_surface.blit(self.plant_img, self.plant_rect)
        hover_surface.blit(self.title_text, (text_x, title_y))
        hover_surface.blit(self.sub_text, (text_x, sub_y))
        self.button_hover = pygame.transform.rotate(hover_surface, self.angle)
        
        # 计算旋转后的位置
        orig_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.draw_rect = self.button_normal.get_rect(center=orig_rect.center)
        
    def draw(self, screen, mouse_pos):
        """绘制按钮"""
        # 获取旋转后的碰撞检测矩形
        is_hovered = self.draw_rect.collidepoint(mouse_pos)
        
        # 绘制按钮
        button_img = self.button_hover if is_hovered else self.button_normal
        screen.blit(button_img, self.draw_rect)
        
        return is_hovered
    
    def get_rect(self):
        """获取碰撞检测矩形"""
        return self.draw_rect

class MainMenu:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption('植物大战僵尸 - 主菜单')
        self.clock = pygame.time.Clock()
        
        # 加载背景
        try:
            self.background = pygame.transform.smoothscale(
                load_cached_image('assets/ui/menu.png'), self.screen.get_size())
        except (pygame.error, FileNotFoundError) as e:
            print(f"警告: 无法加载背景图片 - {e}")
            # 创建一个渐变背景作为替代
            self.background = pygame.Surface((800, 600))
            for y in range(600):
                color_val = int(50 + (y / 600) * 50)
                pygame.draw.line(self.background, (20, color_val, 20), (0, y), (800, y))
        
        # 创建关卡按钮 - 石板风格，垂直排列在右侧，整体上移
        button_x = 480
        start_y = 80
        gap = 85
        
        self.level_buttons = [
            LevelButton(button_x, start_y, 'assets/plants/peashooter/wd.png', 1,
                       "经典模式", "", scale=0.55),
            LevelButton(button_x, start_y + gap, 'assets/plants/gatling_pea/GatlingPea.gif', 2,
                       "豌豆射手", "", scale=0.55),
            LevelButton(button_x, start_y + gap * 2, 'assets/plants/sunflower/hb.png', 3,
                       "数字战力", "", scale=0.5),
            LevelButton(button_x, start_y + gap * 3, 'assets/plants/wall_nut/xdfz.png', 4,
                       "植物消消乐", "", scale=0.55),
            LevelButton(button_x, start_y + gap * 4, ':emoji:⚖', 5,
                       "AI植物法庭", "", scale=0.55),
            ]
        
        # 主题选择按钮 - 放在左下角
        self.themes = ["经典", "宇宙", "哈基米"]
        self.current_theme = 0
        self.theme_rect = pygame.Rect(50, 520, 150, 45)
        
        # 字体
        self.font = pygame.font.SysFont('SimSun', 24)
        self.small_font = get_game_font(18)
        self.title_font = get_game_font(48, bold=True)
        
        # 预渲染主题按钮文本
        self._prerender_theme_texts()
        
        # 标题动画 - 放在左侧避免被按钮挡住
        self.title_y = 50
        self.title_offset = 0
        
        # 加载动画资源
        try:
            self.gogogo_image = load_cached_image('assets/ui/gogogo.png')
            self.gogogo_image = pygame.transform.scale(self.gogogo_image, 
                (int(self.gogogo_image.get_width() * 0.8), int(self.gogogo_image.get_height() * 0.8)))
            self.gogogo_rect = self.gogogo_image.get_rect(center=(-300, 300))
        except (pygame.error, FileNotFoundError) as e:
            print(f"警告: 无法加载gogogo图片 - {e}")
            self.gogogo_image = pygame.Surface((200, 100))
            self.gogogo_image.fill((255, 255, 0))
            font = pygame.font.SysFont('SimSun', 36)
            text = font.render("GO!", True, (0, 0, 0))
            self.gogogo_image.blit(text, text.get_rect(center=(100, 50)))
            self.gogogo_rect = self.gogogo_image.get_rect(center=(-300, 300))
        
        # 预缩放不同大小的gogogo图像
        self.gogogo_scaled_images = {}
        
        # 初始化音频
        try:
            pygame.mixer.music.load('assets/ui/title.mp3')
            pygame.mixer.music.play(-1)
            self.title_music = True
        except (pygame.error, FileNotFoundError) as e:
            print(f"警告: 无法加载主菜单音乐 - {e}")
            self.title_music = None
        
        try:
            self.gogogo_sound = pygame.mixer.Sound('assets/ui/gogogo.mp3')
        except (pygame.error, FileNotFoundError) as e:
            print(f"警告: 无法加载gogogo音效 - {e}")
            self.gogogo_sound = None
        
        # 使用脏矩形技术
        self.dirty_rects = []

    def _prerender_theme_texts(self):
        """预渲染主题按钮文本"""
        self.theme_texts = {}
        for i, theme in enumerate(self.themes):
            self.theme_texts[i] = self.font.render(f"主题: {theme}", True, (255, 255, 255))

    def draw_theme_button(self, mouse_pos):
        """绘制主题选择按钮"""
        is_hovered = self.theme_rect.collidepoint(mouse_pos)
        
        # 按钮颜色
        bg_color = (100, 80, 60) if is_hovered else (80, 60, 40)
        border_color = (180, 160, 120)
        
        # 绘制圆角按钮
        pygame.draw.rect(self.screen, bg_color, self.theme_rect, border_radius=8)
        pygame.draw.rect(self.screen, border_color, self.theme_rect, 2, border_radius=8)
        
        # 绘制文本
        text = self.theme_texts[self.current_theme]
        text_rect = text.get_rect(center=self.theme_rect.center)
        self.screen.blit(text, text_rect)
        
        return is_hovered

    def draw_title(self):
        """绘制游戏标题 - 放在左侧"""
        # 标题浮动动画
        self.title_offset = math.sin(time.time() * 2) * 5
        
        # 主标题位置（左侧）
        title_x = 200
        
        # 主标题
        title_text = "植物大战僵尸"
        # 阴影
        shadow = self.title_font.render(title_text, True, (0, 50, 0))
        shadow_rect = shadow.get_rect(center=(title_x + 2, self.title_y + self.title_offset + 2))
        self.screen.blit(shadow, shadow_rect)
        # 主文字
        title = self.title_font.render(title_text, True, (76, 175, 80))
        title_rect = title.get_rect(center=(title_x, self.title_y + self.title_offset))
        self.screen.blit(title, title_rect)
        
        # 副标题
        sub = self.small_font.render("选择游戏模式", True, (200, 200, 200))
        sub_rect = sub.get_rect(center=(title_x, self.title_y + 45 + self.title_offset))
        self.screen.blit(sub, sub_rect)

    def run(self):
        """运行主菜单"""
        running = True
        
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            # 绘制背景
            self.screen.blit(self.background, (0, 0))
            
            # 绘制标题
            self.draw_title()
            
            # 绘制关卡按钮
            for button in self.level_buttons:
                button.draw(self.screen, mouse_pos)
            
            # 绘制主题按钮
            self.draw_theme_button(mouse_pos)
            
            # 更新显示
            pygame.display.flip()
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == MOUSEBUTTONDOWN:
                    # 检查关卡按钮点击
                    for button in self.level_buttons:
                        if button.get_rect().collidepoint(event.pos):
                            self.start_game(button.level_num)
                            running = False
                            break
                    
                    # 检查主题按钮点击
                    if self.theme_rect.collidepoint(event.pos):
                        self.current_theme = (self.current_theme + 1) % len(self.themes)
            
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def _get_scaled_gogogo(self, scale_factor):
        """获取指定比例的gogogo图像，使用缓存避免重复缩放"""
        scale_factor = round(scale_factor, 2)
        if scale_factor in self.gogogo_scaled_images:
            return self.gogogo_scaled_images[scale_factor]
        
        width = int(self.gogogo_image.get_width() * scale_factor)
        height = int(self.gogogo_image.get_height() * scale_factor)
        scaled = pygame.transform.scale(self.gogogo_image, (width, height))
        
        if len(self.gogogo_scaled_images) < 10:
            self.gogogo_scaled_images[scale_factor] = scaled
            
        return scaled
    
    def start_game(self, level):
        """启动游戏"""
        import sys
        
        # 在屏幕中心显示图片
        screen_center = self.screen.get_rect().center
        self.gogogo_rect.center = (screen_center[0] - 800, screen_center[1])
        
        # 初始化动画
        self.screen.blit(self.background, (0, 0))
        initial_scale = 0.3
        initial_image = self._get_scaled_gogogo(initial_scale)
        self.screen.blit(initial_image, initial_image.get_rect(center=(screen_center[0] - 800, screen_center[1])))
        pygame.display.flip()
        
        # 播放音效（如果可用）
        if self.gogogo_sound:
            self.gogogo_sound.play()
        
        # 动画区域
        animation_rect = pygame.Rect(0, 0, self.screen.get_width(), self.screen.get_height())
        
        # 使用时间戳实现平滑动画
        start_time = time.time()
        duration = 2.0
        
        while time.time() - start_time < duration:
            # 处理退出事件
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    break
            
            # 计算动画进度 (0.0 - 1.0)
            progress = min(1.0, (time.time() - start_time) / duration)
            
            # 使用缓动函数使动画更自然
            eased_progress = self._ease_out_quad(progress)
            
            # 计算动画参数
            scale_factor = 0.3 + 0.7 * eased_progress
            current_x = screen_center[0] - 800 + (800 * eased_progress)
            current_y = screen_center[1]
            
            # 绘制背景和动画
            self.screen.blit(self.background, (0, 0))
            
            # 使用缓存的缩放图像
            scaled_image = self._get_scaled_gogogo(scale_factor)
            scaled_rect = scaled_image.get_rect(center=(current_x, current_y))
            self.screen.blit(scaled_image, scaled_rect)
            
            pygame.display.update(animation_rect)
            self.clock.tick(60)
        
        # 停止音乐（如果正在播放）
        if self.title_music:
            pygame.mixer.music.stop()
        
        # 清理缓存的缩放图像，节省内存
        self.gogogo_scaled_images.clear()
        
        # 获取主题设置，难度固定为普通（1）
        difficulty = 1
        theme = self.current_theme
        
        # 根据选择的关卡启动不同的游戏模式
        restart = False

        try:
            entry_func = _load_game_entry(level)
            if level == 1:
                restart = entry_func(difficulty, theme)
            elif level == 2:
                restart = entry_func(difficulty, theme, True)
            elif level == 3:
                restart = entry_func(difficulty, theme, False)
            else:
                restart = entry_func()
        except Exception as e:
            print(f"错误: 无法加载游戏模块 - {e}")
            font = pygame.font.SysFont('SimSun', 24)
            error_text = font.render(f"错误: 无法加载游戏模块 - {e}", True, (255, 0, 0))
            
            self.screen.blit(self.background, (0, 0))
            self.screen.blit(error_text, error_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2)))
            pygame.display.flip()
            
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN:
                        waiting = False
                pygame.time.delay(100)
            
            restart = True
        
        # 恢复主菜单窗口大小
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption('植物大战僵尸 - 主菜单')

        # 停止Mode 5可能残留的音乐
        pygame.mixer.music.stop()

        # 如果需要重新启动主菜单
        if restart:
            if self.title_music:
                pygame.mixer.music.load('assets/ui/title.mp3')
                pygame.mixer.music.play(-1)
            self.run()
    
    def _ease_out_quad(self, t):
        """平方缓出函数，使动画更自然"""
        return t * (2 - t)

if __name__ == '__main__':
    try:
        # 先显示启动前的商标界面
        splash = SplashScreen()
        splash.run()
        
        # 清理部分资源缓存，节省内存
        keys_to_remove = [k for k in resource_cache.keys() if 'assets/ui/' in k and k.endswith('.png')]
        for key in keys_to_remove:
            resource_cache.pop(key, None)
        
        # 然后进入主菜单
        menu = MainMenu()
        menu.run()
    except Exception as e:
        print(f"严重错误: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
