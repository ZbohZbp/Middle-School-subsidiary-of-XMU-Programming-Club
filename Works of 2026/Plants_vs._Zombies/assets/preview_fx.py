"""
preview_fx.py — AI生成动效特效模块（供 mode_5.py 导入使用）
==================================================
从 preview_effect.py 提取的核心特效逻辑，移除了独立应用框架。
通过 PreviewFXManager 管理所有特效状态和渲染。

用法：
    from preview_fx import PreviewFXManager, update_preview, draw_preview
    mgr = PreviewFXManager(base_path, fonts)
    update_preview(mgr, dt)
    draw_preview(mgr, surface)
"""
import pygame
import math
import random
import os
import time

# ==================== 常量 ====================
SW, SH = 1280, 720

# ==================== 音乐时间节点 ====================
T_AMBER = 20.0
T_PHASE2 = 33.0
T_PHASE3 = 42.0
T_PHASE4 = 54.0
T_DISTORT = 80.0
T_BRIGHT = 65.0
T_TOTAL = 80.0

BLEND_DURATION = 3.0

# ==================== 各阶段配色定义 ====================
PHASE_COLORS = {
    1: {
        "rain_head": (40, 140, 255),
        "rain_body": (30, 100, 200),
        "rain_tail": (10, 40, 100),
        "bg": (2, 4, 12),
        "border": (30, 100, 180),
        "accent": (60, 160, 255),
        "particle": (40, 120, 220),
        "title": (50, 140, 255),
        "bar_dim": (20, 80, 160),
        "bar_bright": (40, 140, 255),
        "hex": (10, 25, 55, 25),
    },
    1.25: {
        "rain_head": (0, 230, 220),
        "rain_body": (0, 160, 170),
        "rain_tail": (0, 60, 80),
        "bg": (2, 8, 10),
        "border": (0, 160, 180),
        "accent": (0, 255, 240),
        "particle": (0, 180, 190),
        "title": (0, 220, 210),
        "bar_dim": (0, 120, 140),
        "bar_bright": (0, 230, 220),
        "hex": (8, 35, 40, 30),
    },
    1.75: {
        "rain_head": (140, 80, 255),
        "rain_body": (100, 50, 200),
        "rain_tail": (50, 20, 100),
        "bg": (8, 4, 16),
        "border": (100, 60, 180),
        "accent": (160, 100, 255),
        "particle": (120, 60, 220),
        "title": (140, 80, 255),
        "bar_dim": (80, 40, 160),
        "bar_bright": (140, 80, 255),
        "hex": (25, 15, 50, 30),
    },
    2: {
        "rain_head": (180, 40, 255),
        "rain_body": (140, 30, 220),
        "rain_tail": (60, 10, 100),
        "bg": (10, 3, 18),
        "border": (130, 40, 180),
        "accent": (200, 60, 255),
        "particle": (160, 40, 240),
        "title": (180, 50, 255),
        "bar_dim": (120, 30, 180),
        "bar_bright": (180, 40, 255),
        "hex": (35, 12, 55, 35),
    },
    2.5: {
        "rain_head": (255, 40, 180),
        "rain_body": (200, 30, 140),
        "rain_tail": (100, 10, 60),
        "bg": (12, 3, 8),
        "border": (180, 30, 120),
        "accent": (255, 60, 200),
        "particle": (220, 40, 160),
        "title": (255, 50, 180),
        "bar_dim": (160, 20, 100),
        "bar_bright": (255, 40, 180),
        "hex": (45, 10, 35, 35),
    },
    3: {
        "rain_head": (200, 40, 255),
        "rain_body": (160, 30, 220),
        "rain_tail": (80, 10, 120),
        "bg": (10, 3, 18),
        "border": (140, 40, 180),
        "accent": (220, 60, 255),
        "particle": (180, 40, 240),
        "title": (200, 50, 255),
        "bar_dim": (140, 30, 180),
        "bar_bright": (200, 40, 255),
        "hex": (40, 14, 55, 35),
    },
    3.5: {
        "rain_head": (255, 0, 0),
        "rain_body": (200, 0, 0),
        "rain_tail": (120, 0, 0),
        "bg": (14, 0, 0),
        "border": (180, 0, 0),
        "accent": (255, 30, 30),
        "particle": (220, 0, 0),
        "title": (255, 0, 0),
        "bar_dim": (160, 0, 0),
        "bar_bright": (255, 0, 0),
        "hex": (50, 12, 0, 35),
    },
    4: {
        "rain_head": (255, 0, 0),
        "rain_body": (220, 0, 0),
        "rain_tail": (140, 0, 0),
        "bg": (18, 0, 0),
        "border": (200, 0, 0),
        "accent": (255, 40, 40),
        "particle": (240, 0, 0),
        "title": (255, 0, 0),
        "bar_dim": (180, 0, 0),
        "bar_bright": (255, 0, 0),
        "hex": (55, 14, 0, 40),
    },
    4.5: {
        "rain_head": (0, 255, 255),
        "rain_body": (0, 220, 230),
        "rain_tail": (0, 120, 140),
        "bg": (2, 10, 12),
        "border": (0, 200, 220),
        "accent": (0, 255, 255),
        "particle": (0, 230, 240),
        "title": (0, 255, 255),
        "bar_dim": (0, 160, 180),
        "bar_bright": (0, 255, 255),
        "hex": (8, 40, 45, 40),
    },
}

# ==================== 辅助函数 ====================
def lerp(a, b, t):
    return a + (b - a) * max(0, min(1, t))

def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(min(len(c1), len(c2))))

def lerp_color4(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))

# ==================== 预渲染纹理缓存 ====================
_gradient_cache = {}
_circle_cache = {}
_radial_cache = {}

def make_gradient_strip(length, c1, c2, horizontal=False):
    cache_key = (length, c1, c2, horizontal)
    if cache_key in _gradient_cache:
        return _gradient_cache[cache_key]
    if horizontal:
        surf = pygame.Surface((length, 1), pygame.SRCALPHA)
        for i in range(length):
            ratio = i / max(length - 1, 1)
            c = lerp_color(c1, c2, ratio)
            surf.set_at((i, 0), c)
    else:
        surf = pygame.Surface((1, length), pygame.SRCALPHA)
        for i in range(length):
            ratio = i / max(length - 1, 1)
            c = lerp_color(c1, c2, ratio)
            surf.set_at((0, i), c)
    _gradient_cache[cache_key] = surf
    return surf

def make_radial_gradient(radius, center_color, edge_color):
    key = (radius, center_color, edge_color)
    if key in _radial_cache:
        return _radial_cache[key]
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        ratio = 1.0 - r / radius
        c = lerp_color(center_color, edge_color, ratio)
        pygame.draw.circle(surf, c, (radius, radius), r)
    _radial_cache[key] = surf
    return surf

def get_circle_surface(radius, color, alpha):
    a_bucket = (alpha // 10) * 10
    key = (radius, color, a_bucket)
    if key not in _circle_cache:
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, a_bucket), (radius, radius), radius)
        _circle_cache[key] = s
    return _circle_cache[key]

def draw_hex_grid(surface, color, spacing=36):
    h = spacing * 0.866
    cols = int(surface.get_width() / spacing) + 2
    rows = int(surface.get_height() / h) + 2
    for row in range(rows):
        for col in range(cols):
            cx = col * spacing + (spacing / 2 if row % 2 else 0)
            cy = row * h
            pts = []
            for i in range(6):
                angle = math.pi / 3 * i + math.pi / 6
                pts.append((cx + spacing * 0.4 * math.cos(angle),
                            cy + spacing * 0.4 * math.sin(angle)))
            if len(pts) >= 3:
                pygame.draw.polygon(surface, color, pts, 1)

def draw_rr(surface, color, rect, radius):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def draw_gradient(surface, c1, c2, rect):
    x, y, w, h = rect
    for i in range(h):
        ratio = i / max(h - 1, 1)
        c = lerp_color(c1, c2, ratio)
        pygame.draw.line(surface, c, (x, y + i), (x + w, y + i))

def draw_glow_border(surface, rect, color, thickness=2, glow_radius=8):
    x, y, w, h = rect
    for g in range(glow_radius, 0, -1):
        alpha = int(30 * (1 - g / glow_radius))
        gc = (*color[:3], alpha)
        gs = pygame.Surface((w + g * 2, h + g * 2), pygame.SRCALPHA)
        pygame.draw.rect(gs, gc, (0, 0, w + g * 2, h + g * 2), border_radius=10, width=1)
        surface.blit(gs, (x - g, y - g))
    pygame.draw.rect(surface, color, rect, thickness, border_radius=8)

def smooth_step(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / max(edge1 - edge0, 0.001)))
    return t * t * (3 - 2 * t)

# ==================== 混合颜色获取 ====================
def get_blended_colors(music_time):
    if music_time < T_AMBER:
        return PHASE_COLORS[1], 1, 0.0
    elif music_time < T_AMBER + BLEND_DURATION * 0.5:
        t = (music_time - T_AMBER) / (BLEND_DURATION * 0.5)
        return None, 1.125, t
    elif music_time < T_PHASE2 - BLEND_DURATION:
        return PHASE_COLORS[1.25], 1.25, 0.0
    elif music_time < T_PHASE2 - BLEND_DURATION * 0.5:
        t = (music_time - (T_PHASE2 - BLEND_DURATION)) / (BLEND_DURATION * 0.5)
        return None, 1.5, t
    elif music_time < T_PHASE2:
        return PHASE_COLORS[1.75], 1.75, 0.0
    elif music_time < T_PHASE2 + BLEND_DURATION * 0.5:
        t = (music_time - T_PHASE2) / (BLEND_DURATION * 0.5)
        return None, 1.875, t
    elif music_time < T_PHASE2 + BLEND_DURATION:
        t = (music_time - (T_PHASE2 + BLEND_DURATION * 0.5)) / (BLEND_DURATION * 0.5)
        return None, 2, t
    elif music_time < T_PHASE3:
        return PHASE_COLORS[2], 2, 0.0
    elif music_time < T_PHASE3 + BLEND_DURATION * 0.5:
        t = (music_time - T_PHASE3) / (BLEND_DURATION * 0.5)
        return None, 2.25, t
    elif music_time < T_PHASE3 + BLEND_DURATION:
        t = (music_time - (T_PHASE3 + BLEND_DURATION * 0.5)) / (BLEND_DURATION * 0.5)
        return None, 2.75, t
    elif music_time < T_PHASE4:
        return PHASE_COLORS[3], 3, 0.0
    elif music_time < T_PHASE4 + BLEND_DURATION * 0.5:
        t = (music_time - T_PHASE4) / (BLEND_DURATION * 0.5)
        return None, 3.25, t
    elif music_time < T_PHASE4 + BLEND_DURATION:
        t = (music_time - (T_PHASE4 + BLEND_DURATION * 0.5)) / (BLEND_DURATION * 0.5)
        return None, 3.75, t
    elif music_time < T_BRIGHT:
        return PHASE_COLORS[4], 4, 0.0
    elif music_time < T_BRIGHT + BLEND_DURATION * 0.5:
        t = (music_time - T_BRIGHT) / (BLEND_DURATION * 0.5)
        return None, 4.25, t
    elif music_time < T_DISTORT:
        return PHASE_COLORS[4.5], 4.5, 0.0
    else:
        return PHASE_COLORS[4.5], 4.5, 0.0

def get_current_colors(music_time):
    _, zone, blend_t = get_blended_colors(music_time)
    if zone == 1.125:
        c1, c2 = PHASE_COLORS[1], PHASE_COLORS[1.25]
    elif zone == 1.5:
        c1, c2 = PHASE_COLORS[1.25], PHASE_COLORS[1.75]
    elif zone == 1.875:
        c1, c2 = PHASE_COLORS[1.75], PHASE_COLORS[2]
    elif zone == 2.25:
        c1, c2 = PHASE_COLORS[2], PHASE_COLORS[2.5]
    elif zone == 2.75:
        c1, c2 = PHASE_COLORS[2.5], PHASE_COLORS[3]
    elif zone == 3.25:
        c1, c2 = PHASE_COLORS[3], PHASE_COLORS[3.5]
    elif zone == 3.75:
        c1, c2 = PHASE_COLORS[3.5], PHASE_COLORS[4]
    elif zone == 4.25:
        c1, c2 = PHASE_COLORS[4], PHASE_COLORS[4.5]
    else:
        z = zone if zone in PHASE_COLORS else int(zone)
        return PHASE_COLORS[z]
    result = {}
    for key in c1:
        if len(c1[key]) == 4:
            result[key] = lerp_color4(c1[key], c2[key], blend_t)
        else:
            result[key] = lerp_color(c1[key], c2[key], blend_t)
    return result

def get_effect_intensity(music_time):
    mt = music_time
    if mt < T_PHASE2:
        rain_speed = 0.3 + 0.1 * (mt / T_PHASE2)
    elif mt < T_PHASE3:
        t = (mt - T_PHASE2) / (T_PHASE3 - T_PHASE2)
        rain_speed = 0.4 + 0.5 * t
    elif mt < T_PHASE4:
        t = (mt - T_PHASE3) / (T_PHASE4 - T_PHASE3)
        rain_speed = 0.9 - 0.2 * t
    elif mt < T_DISTORT:
        t = (mt - T_PHASE4) / (T_DISTORT - T_PHASE4)
        rain_speed = 0.7 + 0.6 * t
    else:
        rain_speed = 0.3

    if mt < T_PHASE2 - 2:
        holo = 0.0
    elif mt < T_PHASE2 + BLEND_DURATION:
        holo = max(0, (mt - (T_PHASE2 - 2)) / (BLEND_DURATION + 2))
    elif mt < T_DISTORT:
        holo = 1.0
    else:
        holo = 0.0

    if mt < T_PHASE3 - 1:
        spectrum = 0.0
    elif mt < T_PHASE3 + BLEND_DURATION:
        spectrum = max(0, (mt - (T_PHASE3 - 1)) / (BLEND_DURATION + 1)) * 0.4
    elif mt < T_PHASE4:
        spectrum = 0.4
    elif mt < T_DISTORT:
        t = (mt - T_PHASE4) / (T_DISTORT - T_PHASE4)
        spectrum = 0.4 + 0.6 * t
    else:
        spectrum = 0.0

    if mt < T_PHASE3:
        storm = 0.0
    elif mt < T_PHASE4:
        t = (mt - T_PHASE3) / (T_PHASE4 - T_PHASE3)
        storm = t * 0.3
    elif mt < T_DISTORT:
        t = (mt - T_PHASE4) / (T_DISTORT - T_PHASE4)
        storm = 0.3 + 0.7 * t
    else:
        storm = 0.0

    if mt < T_PHASE4:
        wave = 0.0
    elif mt < T_DISTORT:
        t = (mt - T_PHASE4) / (T_DISTORT - T_PHASE4)
        wave = t
    else:
        wave = 0.0

    if mt < T_PHASE2:
        shock = 0.0
    elif mt < T_PHASE3:
        shock = 0.3
    elif mt < T_PHASE4:
        shock = 0.2
    elif mt < T_DISTORT:
        t = (mt - T_PHASE4) / (T_DISTORT - T_PHASE4)
        shock = 0.3 + 0.7 * t
    else:
        shock = 0.0

    if mt < T_PHASE2:
        streak = 0.0
    elif mt < T_PHASE3:
        streak = 0.5
    elif mt < T_PHASE4:
        streak = 0.3
    elif mt < T_DISTORT:
        t = (mt - T_PHASE4) / (T_DISTORT - T_PHASE4)
        streak = 0.3 + 0.7 * t
    else:
        streak = 0.0

    if mt < T_PHASE4:
        glitch = 0.02
    elif mt < T_DISTORT:
        t = (mt - T_PHASE4) / (T_DISTORT - T_PHASE4)
        glitch = 0.02 + 0.10 * t
    else:
        glitch = 0.02

    if mt < T_PHASE2 - 3:
        hex_alpha = 10
    elif mt < T_PHASE2 + BLEND_DURATION:
        t = (mt - (T_PHASE2 - 3)) / (BLEND_DURATION + 3)
        hex_alpha = int(10 + 35 * t)
    elif mt < T_DISTORT:
        hex_alpha = 45
    else:
        hex_alpha = 10

    if mt < T_DISTORT - 3:
        silence = 0.0
    elif mt < T_DISTORT:
        silence = (mt - (T_DISTORT - 3)) / 3.0 * 0.6
    else:
        silence = 0.0

    return {
        "rain_speed": rain_speed, "holo": holo, "spectrum": spectrum,
        "storm": storm, "wave": wave, "shock": shock, "streak": streak,
        "glitch": glitch, "hex_alpha": hex_alpha, "silence": silence,
    }

def get_visual_params(mt):
    B = BLEND_DURATION
    center_glow_r = 0
    if mt >= T_PHASE4:
        center_glow_r = int(30 * (mt - T_PHASE4))
    pyramid_scale = 1.0
    if mt >= T_PHASE4:
        pyramid_scale = 1.0 + 0.4 * smooth_step(T_PHASE4, T_DISTORT - 3, mt)
    particle_speed_mult = 1.0
    if mt >= T_PHASE4:
        particle_speed_mult = 1.0 + 1.5 * smooth_step(T_PHASE4, T_DISTORT - 3, mt)
    screen_pulse = 0.0
    if mt >= T_PHASE4 + 8:
        intensity = smooth_step(T_PHASE4 + 8, T_DISTORT - 3, mt) * 0.15
        pulse_wave = max(0, math.sin(mt * 2.1)) ** 3
        screen_pulse = intensity * pulse_wave
    if mt < T_PHASE2:
        rain_trail = 20
    elif mt < T_PHASE2 + B:
        rain_trail = int(20 + 20 * smooth_step(T_PHASE2, T_PHASE2 + B, mt))
    elif mt < T_PHASE3:
        rain_trail = 40
    elif mt < T_PHASE3 + B:
        rain_trail = int(40 + 20 * smooth_step(T_PHASE3, T_PHASE3 + B, mt))
    else:
        rain_trail = 60
    title_glitch_offset = 3
    if mt >= T_PHASE4:
        title_glitch_offset = int(3 + 10 * smooth_step(T_PHASE4, T_DISTORT - 3, mt))
    vignette_mult = 1.0
    if mt >= T_PHASE4 + 10:
        vignette_mult = 1.0 + 1.5 * smooth_step(T_PHASE4 + 10, T_DISTORT - 3, mt)
    scanline_alpha = 0
    if mt >= T_PHASE2:
        scanline_alpha = int(15 * smooth_step(T_PHASE2, T_PHASE2 + B, mt))
    if mt >= T_PHASE4:
        scanline_alpha = int(15 + 20 * smooth_step(T_PHASE4, T_PHASE4 + B, mt))
    shockwave_scale = 1.0
    if mt >= T_PHASE4:
        shockwave_scale = 1.0 + 0.8 * smooth_step(T_PHASE4, T_DISTORT - 3, mt)
    transition_scan = 0.0
    if T_PHASE2 <= mt < T_PHASE2 + 1.5:
        transition_scan = smooth_step(T_PHASE2, T_PHASE2 + 0.3, mt) * (1.0 - smooth_step(T_PHASE2 + 0.8, T_PHASE2 + 1.5, mt))
    transition_pulse = 0.0
    if T_PHASE3 <= mt < T_PHASE3 + 1.0:
        transition_pulse = smooth_step(T_PHASE3, T_PHASE3 + 0.2, mt) * (1.0 - smooth_step(T_PHASE3 + 0.5, T_PHASE3 + 1.0, mt))
    transition_shake = 0.0
    if T_PHASE4 <= mt < T_PHASE4 + 1.5:
        transition_shake = smooth_step(T_PHASE4, T_PHASE4 + 0.2, mt) * (1.0 - smooth_step(T_PHASE4 + 0.8, T_PHASE4 + 1.5, mt))
    edge_glow = 0.0
    if mt >= T_PHASE4 + 5:
        edge_glow = smooth_step(T_PHASE4 + 5, T_DISTORT - 5, mt) * 0.5
    spectrum_overflow = 0.0
    if mt >= T_PHASE4 + 10:
        spectrum_overflow = smooth_step(T_PHASE4 + 10, T_DISTORT - 5, mt) * 30
    return {
        "center_glow_r": center_glow_r, "pyramid_scale": pyramid_scale,
        "particle_speed_mult": particle_speed_mult, "screen_pulse": screen_pulse,
        "rain_trail": rain_trail, "title_glitch_offset": title_glitch_offset,
        "vignette_mult": vignette_mult, "scanline_alpha": scanline_alpha,
        "shockwave_scale": shockwave_scale, "transition_scan": transition_scan,
        "transition_pulse": transition_pulse, "transition_shake": transition_shake,
        "edge_glow": edge_glow, "spectrum_overflow": spectrum_overflow,
    }

# ==================== 特效状态 ====================
FAKE_LOG_MESSAGES = [
    ("Init", "系统初始化完成"), ("Init", "加载AI模型配置..."),
    ("Step1", "构建案件基础框架"), ("Step1", "设定案件主题：植物花园"),
    ("Step2", "构建矛盾体系..."), ("Step2", "生成3组逻辑矛盾链"),
    ("Step2", "校验矛盾互斥性... ✓"), ("Step2.5", "生成嫌疑人档案"),
    ("Step2.5", "嫌疑人A: 寒冰射手"), ("Step2.5", "性格标签: 冷静、多疑"),
    ("Step3a", "生成第一轮证词(4条)"), ("Step3a", "证人向日葵: '我亲眼看见...'"),
    ("Step3a", "校验证词可信度... ✓"), ("Step3b", "生成第二轮证词(3条)"),
    ("Step3b", "证人双发射手: '当时我在巡逻...'"),
    ("Step3c", "生成第三轮证词(4条)"),
    ("Step4a", "生成第一轮证据(3件)"), ("Step4a", "证据E01: 夜间充能记录"),
    ("Step4a.5", "R1异议映射: T03↔E01 ✓"),
    ("Step4b", "生成第二轮证据(2件)"), ("Step4b.5", "R2异议映射: T06↔E04 ✓"),
    ("Step4c", "生成第三轮证据(2件)"), ("Step4c.5", "R3异议映射: T10↔E06 ✓"),
    ("Step5a", "生成阶段过渡台词"), ("Step5b", "生成法官评论..."),
    ("Step5c", "法官评论校验通过"), ("Step5d", "生成分支改口台词(4组)"),
    ("Step5e", "E01触发台词已生成"), ("Step5f", "E02触发台词已生成"),
    ("Step5g", "线索触发台词已生成"),
    ("Step5h-R3成功", "R3成功结局台词 ✓"),
    ("Done", "全部校验通过"), ("Done", "案件生成完成！"),
]

class EffectsState:
    DEPTH_SIZES = [13, 17, 19, 23]       # 远→近 字体大小
    DEPTH_SPACING = [15, 19, 21, 26]     # 远→近 字符间距
    DEPTH_SPEED = [0.4, 0.7, 0.9, 1.3]   # 远→近 速度倍率
    DEPTH_BRIGHT = [0.4, 0.6, 0.85, 1.0] # 远→近 亮度基底

    def __init__(self, perf_mode=False):
        self.perf_mode = perf_mode
        self._char_cache = {}  # key: (id(font), char, color) -> Surface
        self.rain_fonts = [pygame.font.SysFont('Consolas', s) for s in self.DEPTH_SIZES]
        self.reset()

    def _render_char_cached(self, font, char, color):
        key = (id(font), char, color)
        if key not in self._char_cache:
            self._char_cache[key] = font.render(char, True, color)
        return self._char_cache[key]

    def reset(self):
        col_w = 18 if self.perf_mode else 10
        n_cols = SW // col_w + 1
        tech_charset = "0123456789ABCDEF+-*/=<>[]{}|~"
        self.rain_cols = []
        for ci in range(n_cols):
            depth = random.choices([0, 1, 2, 3], weights=[2, 3, 3, 2])[0]
            clen = random.randint(10, 24)
            speed_base = random.uniform(20, 55)
            chars = [random.choice(tech_charset) for _ in range(clen)]
            self.rain_cols.append({
                "x": ci * col_w, "y": random.randint(-500, 0),
                "speed": speed_base * self.DEPTH_SPEED[depth],
                "chars": chars, "depth": depth,
                "char_idx": random.randint(0, clen - 1),
                "brightness": random.uniform(self.DEPTH_BRIGHT[depth], 1.0),
            })
        self.particles = []
        for _ in range(80):
            self.particles.append({
                "x": random.randint(0, SW), "y": random.randint(0, SH),
                "size": random.randint(1, 3), "speed": random.uniform(10, 50),
                "drift": random.uniform(-5, 5), "alpha": random.randint(80, 200),
            })
        self.light_streaks = []
        self.streak_timer = 0.0
        self.orbits = [
            {"radius": 80 + i * 30, "speed": 0.8 + i * 0.4,
             "offset": i * 2.1, "particles": 3 + i} for i in range(3)
        ]
        self.holo_rot = 0.0
        self.shockwaves = []
        self.storm_particles = []
        for _ in range(30):
            self.storm_particles.append({
                "x": random.uniform(0, SW), "y": random.uniform(0, SH),
                "vx": random.uniform(-40, 40), "vy": random.uniform(-40, 40),
                "size": random.uniform(1, 4), "alpha": 0, "hue": random.random(),
            })
        self.spectrum_bars = [
            {"height": 5, "target": random.uniform(5, 15), "speed": random.uniform(2, 8)}
            for _ in range(32)
        ]
        self.wave_wall = [
            {"phase": random.uniform(0, 6.28), "speed": random.uniform(2, 6),
             "amp": random.uniform(10, 30)} for _ in range(64)
        ]
        self.display_progress = 0.0
        self.fake_logs = []
        self.log_timer = 0.0
        self.log_step_idx = 0
        self.scan_y = 0.0
        self.pulse_rings = []
        self.pulse_ring_timer = 0.0
        self.energy_waves = []
        self.energy_wave_timer = 0.0
        self.meteors = []
        self.meteor_timer = 0.0
        self.string_lights = []
        for _ in range(10):
            self.string_lights.append({
                "x": random.uniform(0, SW), "width": random.uniform(8, 30),
                "speed": random.uniform(8, 25), "alpha": random.uniform(0.3, 0.8),
                "phase": random.uniform(0, 6.28),
            })
        self.golden_dust = []
        for _ in range(35):
            self.golden_dust.append({
                "x": random.uniform(0, SW), "y": random.uniform(0, SH),
                "size": random.uniform(1.5, 4), "speed": random.uniform(8, 25),
                "drift": random.uniform(-6, 6), "alpha": 0,
                "brightness": random.uniform(0.5, 1.0), "phase": random.uniform(0, 6.28),
            })
        self.distort_phase = 0
        self.distort_timer = 0.0
        self.dna_show = False
        self.dna_timer = 0.0
        self.dna_particles = [
            {"x": random.randint(0, SW), "y": random.randint(0, SH),
             "vx": random.uniform(-8, 8), "vy": random.uniform(-15, -3),
             "size": random.randint(1, 3), "alpha": random.randint(30, 100),
             "brightness": random.uniform(0.3, 1.0)} for _ in range(25)
        ]
        self.current_step = "Init"
        self.steps_order = [
            "Init", "Step1", "Step2", "Step2.5", "Step3a", "Step3b", "Step3c",
            "Step4a", "Step4a.5", "Step4b", "Step4b.5", "Step4c", "Step4c.5",
            "Step5a", "Step5b", "Step5c", "Step5d", "Step5e", "Step5f",
            "Step5g", "Step5h-R3成功", "Done"
        ]
        self.step_names = {
            "Init": "初始化", "Step1": "案件基础", "Step2": "矛盾体系",
            "Step2.5": "嫌疑人档案", "Step3a": "第一轮证词", "Step3b": "第二轮证词",
            "Step3c": "第三轮证词", "Step4a": "第一轮证据", "Step4b": "第二轮证据",
            "Step4c": "第三轮证据", "Step4a.5": "R1异议映射", "Step4b.5": "R2异议映射",
            "Step4c.5": "R3异议映射", "Step5a": "过渡台词", "Step5b": "法官评论",
            "Step5c": "法官评论", "Step5d": "分支台词", "Step5e": "分支台词",
            "Step5f": "分支台词", "Step5g": "分支台词",
            "Step5h-R3成功": "R3成功台词", "Done": "生成完成",
        }
        # 缓存 Surface
        self.hex_cache = None
        self.hex_cache_color = None
        self.vignette_cache = None
        self.beam_cache = None
        self.beam_holo_key = -1
        self.neon_cache = None
        self.neon_color = None
        self.panel_log_bg_cache = None
        self.panel_log_border_cache = None
        self.panel_info_bg_cache = None
        self.panel_info_border_cache = None
        self.panel_log_border_color = None
        self.panel_info_border_color = None
        self.panel_bg_color = None
        self.light_beam_strips = {}
        for bw in range(8, 31):
            beam_strip = pygame.Surface((bw, 1), pygame.SRCALPHA)
            for bx in range(bw):
                dist = abs(bx - bw // 2) / max(bw // 2, 1)
                brightness = int(200 * (1 - dist * dist))
                beam_strip.set_at((bx, 0), (255, 255, 255, brightness))
            self.light_beam_strips[bw] = beam_strip
        self.holo_particle_glows = {}
        for intensity_bucket in range(11):
            intensity = intensity_bucket / 10.0
            a = int(50 * intensity)
            pg = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(pg, (255, 255, 255, a), (7, 7), 7)
            self.holo_particle_glows[intensity_bucket] = pg
        self.ring_textures = {}
        for bucket in range(0, 35):
            radius = 5 + bucket * 10
            sz = radius * 2 + 10
            ring = pygame.Surface((sz, sz), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 255, 255, 200), (sz // 2, sz // 2), radius, 2)
            if radius > 10:
                pygame.draw.circle(ring, (255, 255, 255, 100), (sz // 2, sz // 2), radius - 3, 1)
            self.ring_textures[(bucket, 2)] = ring
        for bucket in range(0, 33):
            radius = 10 + bucket * 20
            sz = radius * 2 + 10
            ring = pygame.Surface((sz, sz), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 255, 255, 200), (sz // 2, sz // 2), radius, 3)
            self.ring_textures[(bucket, 3)] = ring
        self.glow_dots = {}
        for sz in [1, 2, 3, 4]:
            dot = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
            pygame.draw.circle(dot, (255, 255, 255, 30), (sz * 2, sz * 2), sz * 2)
            pygame.draw.circle(dot, (255, 255, 255, 180), (sz * 2, sz * 2), sz)
            self.glow_dots[sz] = dot
        self.rebirth_glow_cache = None
        for radius in [350]:
            glow = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            cx, cy = radius + 2, radius + 2
            for r in range(radius, 0, -2):
                ratio = 1 - r / radius
                warm = (255, int(140 + 60 * ratio), int(40 * ratio))
                alpha = int(40 * (1 - ratio))
                pygame.draw.circle(glow, (*warm, alpha), (cx, cy), max(1, r - 1))
            pygame.draw.circle(glow, (255, 240, 220, 200), (cx, cy), 12)
            self.rebirth_glow_cache = glow
        self.card_radial_bg = None
        card_w, card_h = 480, 340
        card_bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_bg.fill((6, 10, 20, 240))
        center_x_c, center_y_c = card_w // 2, card_h // 2
        for r in range(300, 0, -3):
            ratio = 1.0 - r / 300
            cr = int(6 + 8 * ratio)
            cg = int(10 + 12 * ratio)
            cb = int(20 + 15 * ratio)
            ca = int(20 * (1 - ratio))
            pygame.draw.circle(card_bg, (cr, cg, cb, ca), (center_x_c, center_y_c), r)
        self.card_radial_bg = card_bg
        self.card_title_bar = None
        title_h = 48
        title_bar = pygame.Surface((card_w, title_h), pygame.SRCALPHA)
        title_bar.fill((18, 28, 48, 255))
        for hx in range(0, card_w, 2):
            hd = abs(hx - card_w // 2) / (card_w // 2)
            brightness = int(15 * (1 - hd))
            pygame.draw.line(title_bar, (brightness, brightness, brightness, 40), (hx, 0), (hx, title_h), 1)
        for ty in range(0, title_h, 4):
            pygame.draw.line(title_bar, (255, 255, 255, 8), (0, ty), (card_w, ty), 1)
        self.card_title_bar = title_bar


# ==================== 管理器 ====================
class PreviewFXManager:
    """管理预览特效的所有状态、时间线和渲染。"""
    def __init__(self, fonts, base_path=None, perf_mode=False):
        self.fx = EffectsState(perf_mode=perf_mode)
        self.fonts = fonts  # dict: f_huge, f_large, f_med, f_small, f_tiny, f_tiny_cn
        self.base_path = base_path or os.path.dirname(os.path.abspath(__file__))
        self.phase = 0
        self.phase_timer = 0.0
        self.blink = 0.0
        self.music_time = 0.0
        self.distort_sfx_played = False
        self.finish_sfx_played = False
        self.has_distort_sfx = False
        self.has_finish_sfx = False
        self.case_data = None  # 存储生成的案件数据
        self._load_sfx()

    def _load_sfx(self):
        distort_path = os.path.join(self.base_path, "sounds", "court", "losereal.mp3")
        finish_path = os.path.join(self.base_path, "sounds", "court", "finish.mp3")
        self.has_distort_sfx = os.path.exists(distort_path)
        self.has_finish_sfx = os.path.exists(finish_path)
        self._distort_path = distort_path
        self._finish_path = finish_path

    def _play_distort_sfx(self):
        if self.has_distort_sfx and not self.distort_sfx_played:
            try:
                snd = pygame.mixer.Sound(self._distort_path)
                snd.set_volume(0.6)
                snd.play()
                self.distort_sfx_played = True
            except Exception:
                pass

    def _play_finish_sfx(self):
        if self.has_finish_sfx and not self.finish_sfx_played:
            try:
                snd = pygame.mixer.Sound(self._finish_path)
                snd.set_volume(0.7)
                snd.play()
                self.finish_sfx_played = True
            except Exception:
                pass

    def set_music_time(self, t):
        self.music_time = t

    def update_generate(self, dt):
        mt = self.music_time
        eff = get_effect_intensity(mt)
        vp = get_visual_params(mt)
        for col in self.fx.rain_cols:
            # 34s 后才开始明显加速
            if mt > 34.0:
                accel = 1.0 + min(3.0, (mt - 34.0) * 0.08)
            else:
                accel = 1.0
            col["y"] += col["speed"] * dt * accel
            if col["y"] > SH + 200:
                col["y"] = random.randint(-100, 0)
                col["char_idx"] = 0
            col["char_idx"] = (col["char_idx"] + int(dt * 8)) % len(col["chars"])
        psm = vp["particle_speed_mult"]
        for p in self.fx.particles:
            p["y"] -= p["speed"] * dt * psm
            p["x"] += p["drift"] * dt * psm
            p["alpha"] -= 30 * dt
            if p["y"] < -20 or p["alpha"] <= 0:
                p["y"] = SH + random.randint(0, 50)
                p["x"] = random.randint(0, SW)
                p["alpha"] = random.randint(80, 200)
                p["speed"] = random.uniform(15, 60)
                p["drift"] = random.uniform(-8, 8)
        self.fx.scan_y += 120 * dt
        if self.fx.scan_y > SH:
            self.fx.scan_y -= SH
        if eff["streak"] > 0.05:
            self.fx.streak_timer += dt
            interval = max(0.3, 2.5 - eff["streak"] * 2.0)
            if self.fx.streak_timer > interval:
                self.fx.streak_timer = 0.0
                self.fx.light_streaks.append({
                    "x": random.randint(100, SW - 100), "y": random.randint(50, SH - 50),
                    "angle": random.uniform(-45, 45), "length": random.randint(80, 250),
                    "alpha": int(random.randint(120, 200) * eff["streak"]),
                    "speed": random.uniform(40, 100),
                })
        for st in self.fx.light_streaks:
            st["alpha"] -= 80 * dt
            st["x"] += st["speed"] * dt * 0.3
        self.fx.light_streaks = [s for s in self.fx.light_streaks if s["alpha"] > 0]
        if eff["shock"] > 0.05 and random.random() < 0.02 * eff["shock"]:
            self.fx.shockwaves.append({
                "radius": 5, "speed": random.uniform(80, 150),
                "alpha": int(random.randint(100, 200) * eff["shock"]),
            })
        for sw in self.fx.shockwaves:
            sw["radius"] += sw["speed"] * dt
            sw["alpha"] -= 80 * dt
        self.fx.shockwaves = [sw for sw in self.fx.shockwaves if sw["alpha"] > 0]
        if eff["holo"] > 0.01:
            self.fx.holo_rot += dt * (0.5 + eff["holo"] * 0.5)
        if eff["storm"] > 0.01:
            speed = (0.3 + eff["storm"] * 1.2) * psm
            for sp in self.fx.storm_particles:
                sp["x"] += sp["vx"] * dt * speed
                sp["y"] += sp["vy"] * dt * speed
                if sp["x"] < 0 or sp["x"] > SW: sp["vx"] *= -1
                if sp["y"] < 0 or sp["y"] > SH: sp["vy"] *= -1
                sp["alpha"] = int((80 + 70 * abs(math.sin(self.blink * 3 + sp["hue"] * 10))) * eff["storm"])
        spec_mult = eff["spectrum"]
        for bar in self.fx.spectrum_bars:
            target = random.uniform(5, 70) if abs(bar["height"] - bar["target"]) < 2 else bar["target"]
            bar["target"] = target
            target_scaled = target * spec_mult
            diff = target_scaled - bar["height"]
            bar["height"] += diff * min(bar["speed"] * dt, 1.0)
        if eff["wave"] > 0.01:
            for w in self.fx.wave_wall:
                w["phase"] += w["speed"] * dt * eff["wave"]
        ring_rate = 0.3 + eff["rain_speed"] * 0.6
        self.fx.pulse_ring_timer += dt
        if self.fx.pulse_ring_timer > 1.0 / ring_rate and len(self.fx.pulse_rings) < 3:
            self.fx.pulse_ring_timer = 0.0
            self.fx.pulse_rings.append({
                "radius": 5, "max_radius": random.randint(250, 400),
                "speed": 80, "alpha": 200,
            })
        for pr in self.fx.pulse_rings:
            speed_mult = 1.0
            if mt >= T_PHASE3:
                speed_mult = 1.0 + 0.5 * ((mt - T_PHASE3) / (T_DISTORT - T_PHASE3))
            pr["radius"] += pr["speed"] * dt * speed_mult
            fade_ratio = pr["radius"] / pr["max_radius"]
            pr["alpha"] = 200 * (1 - fade_ratio)
        self.fx.pulse_rings = [pr for pr in self.fx.pulse_rings if pr["radius"] < pr["max_radius"]]
        if mt >= T_PHASE2:
            for sl in self.fx.string_lights:
                sl["x"] += sl["speed"] * dt
                sl["phase"] += dt * 1.5
                if sl["x"] > SW + 50:
                    sl["x"] = -50
                    sl["width"] = random.uniform(8, 30)
                    sl["alpha"] = random.uniform(0.3, 0.8)
        if mt >= T_PHASE2:
            dust_intensity = smooth_step(T_PHASE2 + 2, T_PHASE2 + 6, mt)
            for gd in self.fx.golden_dust:
                gd["y"] -= gd["speed"] * dt
                gd["x"] += gd["drift"] * dt
                gd["phase"] += dt * 2.0
                base_alpha = (0.5 + 0.5 * math.sin(gd["phase"])) * gd["brightness"]
                gd["alpha"] = int(base_alpha * 160 * dust_intensity)
                if gd["y"] < -10:
                    gd["y"] = SH + random.uniform(0, 30)
                    gd["x"] = random.uniform(0, SW)
        if mt >= T_PHASE4:
            cresc = smooth_step(T_PHASE4, T_DISTORT - 3, mt)
            ew_interval = max(0.5, 1.5 - 1.0 * cresc)
            self.fx.energy_wave_timer += dt
            if self.fx.energy_wave_timer > ew_interval and len(self.fx.energy_waves) < 5:
                self.fx.energy_wave_timer = 0.0
                self.fx.energy_waves.append({
                    "radius": 10, "max_radius": random.randint(400, 600),
                    "speed": 150, "width": 3, "alpha": 180,
                })
            for ew in self.fx.energy_waves:
                ew["radius"] += ew["speed"] * dt * (1.0 + cresc * 0.8)
                fade_ratio = ew["radius"] / ew["max_radius"]
                ew["alpha"] = 180 * (1 - fade_ratio)
            self.fx.energy_waves = [ew for ew in self.fx.energy_waves if ew["radius"] < ew["max_radius"]]
            meteor_rate = 0.3 + 1.5 * cresc
            max_meteors = max(2, int(8 * psm))
            self.fx.meteor_timer += dt
            if self.fx.meteor_timer > 1.0 / meteor_rate and len(self.fx.meteors) < max_meteors:
                self.fx.meteor_timer = 0.0
                side = random.choice(["left", "right"])
                self.fx.meteors.append({
                    "x": -50 if side == "left" else SW + 50,
                    "y": random.randint(-50, SH // 2),
                    "vx": random.uniform(400, 800) * (1 if side == "left" else -1),
                    "vy": random.uniform(200, 500),
                    "length": random.randint(60, 180),
                    "alpha": int(100 + 100 * cresc),
                    "life": 1.0,
                })
            for m in self.fx.meteors:
                m["x"] += m["vx"] * dt
                m["y"] += m["vy"] * dt
                m["life"] -= dt * 0.8
                m["alpha"] = max(0, m["alpha"] * m["life"])
            self.fx.meteors = [m for m in self.fx.meteors if m["life"] > 0 and m["alpha"] > 5]
        target_progress = min(1.0, mt / T_TOTAL)
        if self.fx.display_progress < target_progress:
            diff = target_progress - self.fx.display_progress
            self.fx.display_progress += diff * min(dt * 3.5, 1.0)
            if diff < 0.002:
                self.fx.display_progress = target_progress
        self.fx.log_timer += dt
        log_speed = max(0.4, 2.0 - eff["rain_speed"] * 1.2)
        # 如果没有外部真实日志注入，才生成假日志
        if not getattr(self, '_has_real_logs', False):
            if self.fx.log_timer > log_speed and self.fx.log_step_idx < len(FAKE_LOG_MESSAGES):
                self.fx.log_timer = 0.0
                step, msg = FAKE_LOG_MESSAGES[self.fx.log_step_idx]
                self.fx.fake_logs.append({"time": mt, "step": step, "msg": msg})
                self.fx.current_step = step
                self.fx.log_step_idx += 1
        if mt >= T_DISTORT:
            self.phase = 1
            self.phase_timer = 0.0
            self.fx.distort_phase = 1
            self.fx.distort_timer = 0.0
            self._play_distort_sfx()

    def update_distortion(self, dt):
        self.fx.distort_timer += dt
        if self.fx.distort_timer > 2.0:
            self.phase = 2
            self.phase_timer = 0.0
            self.fx.distort_phase = 2

    def update_rebirth(self, dt):
        self.fx.distort_timer += dt
        if self.fx.distort_timer > 3.5:
            self.phase = 3
            self.phase_timer = 0.0
            self.fx.distort_phase = 3
            self.fx.dna_show = True
            self.fx.dna_timer = 0.0

    def update_card(self, dt):
        self.fx.dna_timer += dt
        if self.fx.dna_timer >= 1.0 and not self.finish_sfx_played:
            self._play_finish_sfx()
        for dp in self.fx.dna_particles:
            dp["x"] += dp["vx"] * 0.016
            dp["y"] += dp["vy"] * 0.016
            if dp["y"] < -10: dp["y"] = SH + 10; dp["x"] = random.randint(0, SW)
            if dp["x"] < -10: dp["x"] = SW + 10
            if dp["x"] > SW + 10: dp["x"] = -10


# ==================== 公开 API 函数 ====================
def update_preview(mgr, dt):
    """主更新入口。mgr: PreviewFXManager, dt: 帧间隔秒数"""
    mgr.phase_timer += dt
    mgr.blink += dt
    if mgr.phase == 0:
        mgr.update_generate(dt)
    elif mgr.phase == 1:
        mgr.update_distortion(dt)
    elif mgr.phase == 2:
        mgr.update_rebirth(dt)
    elif mgr.phase == 3:
        mgr.update_card(dt)

def draw_preview(mgr, surface):
    """主绘制入口。根据当前阶段分发到对应绘制函数"""
    if mgr.phase == 0:
        draw_preview_generate(mgr, surface)
    elif mgr.phase == 1:
        draw_preview_distortion(mgr, surface)
    elif mgr.phase == 2:
        draw_preview_rebirth(mgr, surface)
    elif mgr.phase == 3:
        draw_preview_card(mgr, surface)

# ---- 绘制：生成阶段 ----
def draw_preview_generate(mgr, s):
    mt = mgr.music_time
    colors = get_current_colors(mt)
    eff = get_effect_intensity(mt)
    vp = get_visual_params(mt)
    silence = eff["silence"]
    master_alpha = 1.0 - silence
    f = mgr.fonts
    fx = mgr.fx

    bg = colors["bg"]
    s.fill(bg)

    shake_ox, shake_oy = 0, 0
    if vp["transition_shake"] > 0.01:
        shake_ox = int(random.randint(-4, 4) * vp["transition_shake"])
        shake_oy = int(random.randint(-3, 3) * vp["transition_shake"])

    hex_c = colors["hex"]
    if hex_c[3] > 5:
        if fx.hex_cache is None or fx.hex_cache_color != hex_c:
            hex_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
            draw_hex_grid(hex_surf, hex_c, 56)
            fx.hex_cache = hex_surf
            fx.hex_cache_color = hex_c
        s.blit(fx.hex_cache, (0, 0))

    if vp["center_glow_r"] > 10:
        ac = colors["accent"]
        gr = vp["center_glow_r"]
        ga = int(25 * master_alpha)
        pygame.draw.circle(s, (*ac, ga), (SW // 2 + shake_ox, SH // 2 + shake_oy), gr)
        pygame.draw.circle(s, (*ac, ga // 3), (SW // 2 + shake_ox, SH // 2 + shake_oy), max(1, gr - 15), 3)

    if vp["transition_scan"] > 0.01:
        scan_pos = int(SH * (mt - T_PHASE2) / 1.5)
        for dy in range(max(0, scan_pos - 60), min(SH, scan_pos + 4)):
            dist = abs(dy - scan_pos)
            alpha = int(180 * vp["transition_scan"] * max(0, 1 - dist / 60))
            ac = colors["accent"]
            pygame.draw.line(s, (*ac, alpha), (0, dy), (SW, dy), 1)

    if vp["transition_pulse"] > 0.01:
        ac = colors["accent"]
        pulse_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
        pa = int(80 * vp["transition_pulse"] * master_alpha)
        pygame.draw.circle(pulse_surf, (*ac, pa), (SW // 2, SH // 2), 200)
        s.blit(pulse_surf, (0, 0))

    log_w, log_x, log_y, log_h = 430, 30, 80, SH - 150
    info_x = log_x + log_w + 30
    info_w = SW - info_x - 40
    info_h = SH - 160
    info_y = 80
    center_x = info_x + info_w // 2
    center_y = info_y + info_h // 2 + 80

    if fx.pulse_rings:
        ac = colors["accent"]
        cx, cy = center_x + shake_ox, center_y + shake_oy
        for pr in fx.pulse_rings:
            r = int(pr["radius"])
            a = int(max(0, pr["alpha"]))
            if r > 5 and a > 5:
                ring_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (*ac, a), (r + 2, r + 2), r, 2)
                s.blit(ring_surf, (cx - r - 2, cy - r - 2))

    rh = colors["rain_head"]
    rb = colors["rain_body"]
    rt = colors["rain_tail"]
    # ---- 字符雨：立体深度 + 缓存渲染 ----
    for col in fx.rain_cols:
        depth = col["depth"]
        fnt = fx.rain_fonts[depth]
        char_spacing = fx.DEPTH_SPACING[depth]
        cx, cy_base = col["x"], col["y"]
        chars, brt = col["chars"], col["brightness"]
        max_chars = [4, 5, 6, 7][depth]
        for j, ch in enumerate(chars):
            if j >= max_chars:
                break
            cy = int(cy_base) - j * char_spacing
            if 0 <= cy < SH and 0 <= cx < SW:
                if j == 0:
                    try:
                        cs = fx._render_char_cached(fnt, ch, rh)
                        cs.set_alpha(int(255 * master_alpha))
                        s.blit(cs, (cx, cy))
                    except: pass
                elif j <= 2:
                    c = lerp_color(rt, rb, brt)
                    fade = int(200 * brt * master_alpha)
                    try:
                        cs = fx._render_char_cached(fnt, ch, c)
                        cs.set_alpha(fade)
                        s.blit(cs, (cx, cy))
                    except: pass
                else:
                    fade = max(10, int((110 * brt - j * 5) * master_alpha))
                    if fade > 8:
                        try:
                            cs = fx._render_char_cached(fnt, ch, rt)
                            cs.set_alpha(fade)
                            s.blit(cs, (cx, cy))
                        except: pass

    pc = colors["particle"]
    for p in fx.particles:
        alpha = int(max(0, p["alpha"] * 0.5 * master_alpha))
        if alpha > 0:
            dot = fx.glow_dots.get(p["size"], fx.glow_dots[2])
            brightness = 0.5 + random.random() * 0.5
            c = (int(pc[0] * brightness), int(pc[1] * brightness), int(pc[2] * brightness))
            tinted = dot.copy()
            tinted.fill((*c, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            s.blit(tinted, (int(p["x"]) - p["size"] * 2, int(p["y"]) - p["size"] * 2))

    holo_a = eff["holo"]
    if holo_a > 0.01:
        ac = colors["accent"]
        for orb in fx.orbits:
            r = orb["radius"]
            for pi in range(orb["particles"]):
                angle = mgr.blink * orb["speed"] + orb["offset"] + pi * (6.28 / orb["particles"])
                px = center_x + math.cos(angle) * r
                py = center_y + math.sin(angle) * r * 0.4
                intensity = 0.4 + 0.6 * ((pi % 3) / 2)
                a = int(50 * holo_a * intensity * master_alpha)
                if a > 0:
                    glow_idx = min(10, max(0, int(round(intensity * 10))))
                    pglow = fx.holo_particle_glows[glow_idx]
                    s.blit(pglow, (int(px) - 7, int(py) - 7))
                c = (int(ac[0] * intensity), int(ac[1] * intensity), int(ac[2] * intensity))
                pygame.draw.circle(s, c, (int(px), int(py)), 3)
        hx, hy = center_x, center_y
        pyramid_size = int(55 * vp["pyramid_scale"])
        rot = fx.holo_rot
        apex = (hx, hy - pyramid_size)
        base_pts = []
        for i in range(4):
            angle = rot + i * math.pi / 2
            bx = hx + math.cos(angle) * pyramid_size * 0.6
            by = hy + math.sin(angle) * pyramid_size * 0.3
            base_pts.append((bx, by))
        ha = int((120 + 90 * abs(math.sin(mgr.blink * 2))) * holo_a * master_alpha)
        ac = colors["accent"]
        for i, bp in enumerate(base_pts):
            brightness = 0.6 + 0.4 * (i / 3)
            c = (int(ac[0] * brightness), int(ac[1] * brightness), int(ac[2] * brightness))
            pygame.draw.line(s, (*c, ha), apex, bp, 2)
        pygame.draw.polygon(s, (*lerp_color(bg, ac, 0.3), ha // 4), base_pts, 0)
        pygame.draw.polygon(s, (*ac, ha), base_pts, 2)
        core_pulse = abs(math.sin(mgr.blink * 3))
        cglow = pygame.Surface((40, 40), pygame.SRCALPHA)
        gc = (min(255, int(ac[0] + 80 * core_pulse)),
              min(255, int(ac[1] + 40 * core_pulse)),
              min(255, int(ac[2] + 30 * core_pulse)))
        pygame.draw.circle(cglow, (*gc, int(80 * holo_a * master_alpha)), (20, 20), 20)
        s.blit(cglow, (hx - 20, hy - 20))
        pygame.draw.circle(s, (min(255, ac[0] + 80), min(255, ac[1] + 60), min(255, ac[2] + 40)),
                           (hx, hy), int(8 * holo_a))

    ac = colors["accent"]
    bright = lerp_color(ac, (255, 255, 255), 0.5)
    for sw in fx.shockwaves:
        r = int(sw["radius"] * vp["shockwave_scale"])
        if r > 0:
            alpha = int(max(0, sw["alpha"]) * master_alpha)
            pygame.draw.circle(s, (*ac, alpha), (center_x + shake_ox, center_y + shake_oy), r, 3)
            if r > 5:
                pygame.draw.circle(s, (*bright, alpha // 2), (center_x + shake_ox, center_y + shake_oy), max(1, r - 5), 2)

    storm_a = eff["storm"]
    if storm_a > 0.01:
        ac = colors["accent"]
        for sp in fx.storm_particles:
            alpha = int(sp["alpha"] * master_alpha)
            size = int(sp["size"])
            c = lerp_color(ac, (255, 255, 255), sp["hue"] * 0.3)
            pygame.draw.circle(s, (*c, alpha), (int(sp["x"]), int(sp["y"])), size + 1)
        if storm_a > 0.3:
            line_a_mult = (storm_a - 0.3) / 0.7
            for i, p1 in enumerate(fx.storm_particles):
                for p2 in fx.storm_particles[i + 1:]:
                    dist = math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])
                    if dist < 150:
                        la = int(35 * (1 - dist / 150) * line_a_mult * master_alpha)
                        pygame.draw.line(s, (*lerp_color(ac, bg, 0.3), la),
                                         (int(p1["x"]), int(p1["y"])),
                                         (int(p2["x"]), int(p2["y"])), 1)

    if fx.energy_waves:
        ac = colors["accent"]
        ecx, ecy = center_x + shake_ox, center_y + shake_oy
        for ew in fx.energy_waves:
            r = int(ew["radius"])
            a = int(max(0, ew["alpha"]))
            w = ew["width"]
            if r > 5 and a > 5:
                ew_surf = pygame.Surface((r * 2 + w * 2 + 4, r * 2 + w * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(ew_surf, (*ac, a), (r + w + 2, r + w + 2), r, w)
                s.blit(ew_surf, (ecx - r - w - 2, ecy - r - w - 2))

    if fx.meteors:
        ac = colors["accent"]
        bright = lerp_color(ac, (255, 255, 255), 0.6)
        for m in fx.meteors:
            ma = int(max(0, m["alpha"]) * master_alpha)
            if ma > 3:
                vlen = math.hypot(m["vx"], m["vy"])
                if vlen > 0:
                    dx = m["vx"] / vlen * m["length"]
                    dy = m["vy"] / vlen * m["length"]
                    mx, my = int(m["x"]), int(m["y"])
                    pygame.draw.line(s, (*ac, ma // 4),
                                     (mx - int(dx), my - int(dy)), (mx, my), 6)
                    pygame.draw.line(s, (*bright, ma),
                                     (mx - int(dx * 0.7), my - int(dy * 0.7)), (mx, my), 2)
                    pygame.draw.circle(s, (*bright, min(255, ma + 40)), (mx, my), 3)

    spec_a = eff["spectrum"]
    if spec_a > 0.02:
        spec_y = info_y + info_h - 70
        spec_w = info_w - 30
        bar_count = len(fx.spectrum_bars)
        bw = spec_w // bar_count
        ac = colors["accent"]
        bright = lerp_color(ac, (255, 255, 255), 0.5)
        overflow_px = int(vp["spectrum_overflow"])
        for si, bar in enumerate(fx.spectrum_bars):
            bh = int(bar["height"])
            bx = info_x + 15 + si * bw
            by = spec_y + 60 - bh
            brightness = 0.4 + 0.6 * (si / max(bar_count - 1, 1))
            c = (int(ac[0] * brightness), int(ac[1] * brightness), int(ac[2] * brightness))
            a = int(180 * spec_a * master_alpha)
            pygame.draw.rect(s, (*c, a), (bx, by, bw - 2, bh))
            if bh > 5:
                pygame.draw.line(s, (*bright, int(150 * spec_a * master_alpha)),
                                 (bx, by), (bx + bw - 2, by), 2)
            if overflow_px > 3 and bh > 20:
                for oy in range(0, overflow_px, 4):
                    oa = int((1 - oy / overflow_px) * 80 * spec_a * master_alpha)
                    if oa > 2:
                        pygame.draw.line(s, (*bright, oa), (bx, by - oy - 1), (bx + bw - 2, by - oy - 1), 1)

    wave_a = eff["wave"]
    if wave_a > 0.01:
        wave_wall_y = SH - 55
        ww_points = []
        for wi, w in enumerate(fx.wave_wall):
            wx = int(wi * (SW / len(fx.wave_wall)))
            wy = wave_wall_y + int(w["amp"] * wave_a * math.sin(w["phase"] + wi * 0.2))
            ww_points.append((wx, wy))
        ac = colors["accent"]
        if len(ww_points) > 1:
            avg_alpha = int(55 * wave_a * master_alpha)
            pygame.draw.lines(s, (*ac, avg_alpha), False, ww_points, 2)

    for st in fx.light_streaks:
        a = int(max(0, st["alpha"]) * master_alpha)
        if a <= 0: continue
        rad = math.radians(st["angle"])
        dx = math.cos(rad) * st["length"]
        dy = math.sin(rad) * st["length"]
        x1, y1 = int(st["x"] - dx / 2), int(st["y"] - dy / 2)
        x2, y2 = int(st["x"] + dx / 2), int(st["y"] + dy / 2)
        ac = colors["accent"]
        bright = lerp_color(ac, (255, 255, 255), 0.6)
        mx, my = int(st["x"]), int(st["y"])
        if a > 3:
            pygame.draw.circle(s, (*ac, int(a * 0.08)), (mx, my), 12, 2)
            pygame.draw.circle(s, (*ac, int(a * 0.05)), (mx, my), 18, 1)
        pygame.draw.line(s, (*bright, int(a * 0.5)), (x1, y1), (x2, y2), 2)

    if mt >= T_PHASE2 and fx.string_lights:
        string_a = smooth_step(T_PHASE2, T_PHASE2 + 5, mt) * master_alpha
        if string_a > 0.01:
            ac = colors["accent"]
            for sl in fx.string_lights:
                sx = int(sl["x"])
                w = int(sl["width"])
                shimmer = 0.5 + 0.5 * math.sin(sl["phase"])
                beam_a = int(sl["alpha"] * shimmer * string_a * 30)
                if beam_a > 2 and -50 < sx < SW + 50:
                    bw = min(max(8, w), 30)
                    strip = fx.light_beam_strips[bw]
                    beam = pygame.transform.scale(strip, (bw, SH))
                    tinted = beam.copy()
                    tinted.fill((*ac, beam_a), special_flags=pygame.BLEND_RGBA_MULT)
                    s.blit(tinted, (sx - bw // 2, 0))

    if mt >= T_PHASE2 and fx.golden_dust:
        dust_a = smooth_step(T_PHASE2 + 2, T_PHASE2 + 6, mt) * master_alpha
        if dust_a > 0.01:
            for gd in fx.golden_dust:
                ga = int(gd["alpha"] * dust_a)
                if ga > 3:
                    warm = (255, int(200 * gd["brightness"]), int(100 * gd["brightness"]))
                    sz = int(gd["size"])
                    dot = fx.glow_dots.get(sz, fx.glow_dots[2])
                    tinted = dot.copy()
                    tinted.fill((*warm, ga), special_flags=pygame.BLEND_RGBA_MULT)
                    s.blit(tinted, (int(gd["x"]) - sz * 2, int(gd["y"]) - sz * 2))

    # 标题栏
    draw_gradient(s, lerp_color(bg, (8, 12, 20), 0.5), bg, (0, 0, SW, 60))
    bc = colors["border"]
    pygame.draw.line(s, bc, (0, 60), (SW, 60), 2)
    pulse = 1 + 0.12 * abs(2 * (mgr.blink * 2 % 1) - 1)
    tc = colors["title"]
    tc_pulse = (min(255, int(tc[0] * pulse)), min(255, int(tc[1] * pulse)), min(255, int(tc[2] * pulse)))
    title_text = "AI CASE GENERATOR v2.0"
    title_surf = f["f_large"].render(title_text, True, tc_pulse)
    title_rect = title_surf.get_rect(center=(SW // 2, 30))
    if random.random() < eff["glitch"]:
        offset = vp["title_glitch_offset"]
        s.blit(f["f_large"].render(title_text, True, lerp_color(tc, bg, 0.3)), title_rect.move(-offset, 0))
        s.blit(f["f_large"].render(title_text, True, lerp_color(tc, (255, 255, 255), 0.5)), title_rect.move(offset, 0))
    s.blit(title_surf, title_rect)

    neon_y = 62
    neon_pulse = 0.6 + 0.4 * abs(math.sin(mgr.blink * 2.5))
    ac = colors["accent"]
    neon_key = (ac[0], ac[1], ac[2])
    if fx.neon_cache is None or fx.neon_color != neon_key:
        half_neon = make_gradient_strip(SW // 2, (ac[0], ac[1], ac[2], 0), (int(ac[0] * 0.4), int(ac[1] * 0.4), int(ac[2] * 0.4), int(80 * neon_pulse)), horizontal=True)
        left_half = pygame.transform.scale(half_neon, (SW // 2, 4))
        right_half = pygame.transform.flip(left_half, True, False)
        fx.neon_cache = pygame.Surface((SW, 4), pygame.SRCALPHA)
        fx.neon_cache.blit(left_half, (0, 0))
        fx.neon_cache.blit(right_half, (SW // 2, 0))
        fx.neon_color = neon_key
    fx.neon_cache.set_alpha(int(200 + 55 * neon_pulse))
    s.blit(fx.neon_cache, (0, neon_y))

    # 计算面板透明度：60s 开始淡出，72s 完全消失
    if mt < 60.0:
        panel_alpha = 255
    elif mt < 72.0:
        panel_alpha = int(255 * (72.0 - mt) / 12.0)
    else:
        panel_alpha = 0

    brd = colors["border"]
    lc = lerp_color(brd, tc, 0.3)

    # 如果面板完全透明，跳过绘制
    if panel_alpha > 0:
        # 淡出时绘制到临时 surface
        if panel_alpha < 255:
            panel_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
            panel_target = panel_surf
        else:
            panel_target = s

        # 日志面板
        bgc = (*bg, 110)
        if fx.panel_log_bg_cache is None or fx.panel_bg_color != bgc:
            fx.panel_log_bg_cache = pygame.Surface((log_w, log_h), pygame.SRCALPHA)
            fx.panel_log_bg_cache.fill(bgc)
            fx.panel_bg_color = bgc
        panel_target.blit(fx.panel_log_bg_cache, (log_x, log_y))
        if fx.panel_log_border_cache is None or fx.panel_log_border_color != brd:
            glow_log = pygame.Surface((SW, SH), pygame.SRCALPHA)
            draw_glow_border(glow_log, (log_x, log_y, log_w, log_h), brd, 2, 8)
            fx.panel_log_border_cache = glow_log
            fx.panel_log_border_color = brd
        panel_target.blit(fx.panel_log_border_cache, (0, 0))
        panel_target.blit(f["f_tiny"].render("◇ SYSTEM LOG", True, lc), (log_x + 12, log_y + 6))

        log_clip = pygame.Rect(log_x + 4, log_y + 26, log_w - 8, log_h - 32)
        panel_target.set_clip(log_clip)
        visible_logs = fx.fake_logs[-30:]
        ly = log_y + 28
        start_t = fx.fake_logs[0]["time"] if fx.fake_logs else 0
        for log_entry in visible_logs:
            if ly > log_y + log_h - 16: break
            elapsed = log_entry["time"] - start_t
            msg, step = log_entry["msg"], log_entry["step"]
            if "校验" in msg or "通过" in msg:
                prefix, clr = "✓", lerp_color(tc, (100, 255, 130), 0.5)
            elif "完成" in step or "Done" in step:
                prefix, clr = "◆", lerp_color(tc, (255, 220, 100), 0.5)
            elif "失败" in msg:
                prefix, clr = "✗", (255, 100, 100)
            else:
                prefix, clr = "▶", tc
            ts = f["f_tiny"].render(f"[{elapsed:05.1f}s]", True, lerp_color(brd, bg, 0.3))
            panel_target.blit(ts, (log_x + 8, ly))
            txt = f"{prefix} {msg}"[:34] + (".." if len(f"{prefix} {msg}") > 34 else "")
            panel_target.blit(f["f_tiny_cn"].render(txt, True, clr), (log_x + 68, ly))
            ly += 17
        if int(mgr.blink * 3) % 2 == 0:
            panel_target.blit(f["f_tiny"].render("█", True, tc), (log_x + 68, ly))
        panel_target.set_clip(None)

        # 右侧信息面板
        if fx.panel_info_bg_cache is None or fx.panel_bg_color != bgc:
            fx.panel_info_bg_cache = pygame.Surface((info_w, info_h), pygame.SRCALPHA)
            fx.panel_info_bg_cache.fill(bgc)
        panel_target.blit(fx.panel_info_bg_cache, (info_x, info_y))
        if fx.panel_info_border_cache is None or fx.panel_info_border_color != brd:
            glow_info = pygame.Surface((SW, SH), pygame.SRCALPHA)
            draw_glow_border(glow_info, (info_x, info_y, info_w, info_h), brd, 2, 8)
            fx.panel_info_border_cache = glow_info
            fx.panel_info_border_color = brd
        panel_target.blit(fx.panel_info_border_cache, (0, 0))

        step_name = fx.step_names.get(fx.current_step, fx.current_step)
        iy = info_y + 15
        panel_target.blit(f["f_tiny"].render("CURRENT STEP", True, lc), (info_x + 15, iy))
        iy += 20
        panel_target.blit(f["f_med"].render(step_name, True, tc), (info_x + 15, iy))
        iy += 35
        panel_target.blit(f["f_tiny"].render("STATUS", True, lc), (info_x + 15, iy))
        iy += 18
        last_msg = fx.fake_logs[-1]["msg"][:26] if fx.fake_logs else "初始化中..."
        panel_target.blit(f["f_small"].render(last_msg, True, (*tc, 200)), (info_x + 15, iy))
        iy += 30

        iy += 10
        panel_target.blit(f["f_tiny"].render("PROGRESS", True, lc), (info_x + 15, iy))
        iy += 20
        bar_w = info_w - 30
        bar_h = 24
        bar_x = info_x + 15
        draw_rr(panel_target, (*brd[:3], 60), (bar_x, iy, bar_w, bar_h), 4)

        bd = colors["bar_dim"]
        bb = colors["bar_bright"]
        dp_val = fx.display_progress
        if dp_val >= 1.0:
            pulse_a = int(180 + 75 * abs(2 * (mgr.blink * 2.0 % 1) - 1))
            panel_target.blit(f["f_small"].render("正在最终校验...", True, (255, 140, 0)),
                   f["f_small"].render("正在最终校验...", True, (255, 140, 0)).get_rect(
                       center=(bar_x + bar_w // 2, iy + bar_h // 2)))
        else:
            fill_w = int(bar_w * dp_val)
            bar_pulse = 0.72 + 0.28 * abs(2 * (mgr.blink * 2.2 % 1) - 1)
            if fill_w > 0:
                bar_grad = make_gradient_strip(bar_h - 4, bd, bb)
                pulsed = bar_grad.copy()
                pulsed.fill((int(bar_pulse * 255), int(bar_pulse * 255), int(bar_pulse * 255), 0),
                           special_flags=pygame.BLEND_RGB_MULT)
                scaled = pygame.transform.scale(pulsed, (fill_w, bar_h - 4))
                panel_target.blit(scaled, (bar_x, iy + 2))
                for gy in range(iy + 4, iy + bar_h - 4, 3):
                    pygame.draw.line(panel_target, (12, 18, 20), (bar_x, gy), (bar_x + fill_w, gy), 1)
            pct_surf = f["f_tiny"].render(f"{int(dp_val * 100)}%", True, bb)
            panel_target.blit(pct_surf, pct_surf.get_rect(center=(bar_x + bar_w // 2, iy + bar_h // 2)))

        dot_y = iy + bar_h + 5
        steps = fx.steps_order
        ip = 0
        if fx.current_step in steps:
            ip = (steps.index(fx.current_step) + 1) / len(steps)
        for si, sname in enumerate(steps):
            dx = bar_x + int(bar_w * si / max(len(steps) - 1, 1))
            is_done = ip >= (si + 1) / len(steps)
            dc = bb if is_done else (20, 30, 35)
            if sname == fx.current_step:
                dp_p = 0.6 + 0.4 * abs(2 * (mgr.blink * 3.0 % 1) - 1)
                dc = (int(bb[0] * dp_p), int(bb[1] * dp_p), int(bb[2] * dp_p))
                pygame.draw.circle(panel_target, dc, (dx, int(dot_y)), 5)
            else:
                pygame.draw.circle(panel_target, dc, (dx, int(dot_y)), 2)

        # 淡出时将临时 surface 绘制到主屏幕
        if panel_alpha < 255:
            panel_surf.set_alpha(panel_alpha)
            s.blit(panel_surf, (0, 0))

    # 底部状态栏
    ac = colors["accent"]
    draw_gradient(s, lerp_color(bg, (6, 8, 12), 0.5), bg, (0, SH - 30, SW, 30))
    wave_y = SH - 15
    for wx in range(0, SW, 4):
        wave_h = int(5 * abs(math.sin(wx * 0.05 + mgr.blink * 6)))
        brightness = 0.5 + 0.5 * abs(math.sin(wx * 0.02 + mgr.blink * 3))
        wc = (int(ac[0] * brightness * 0.5), int(ac[1] * brightness * 0.5), int(ac[2] * brightness * 0.5))
        pygame.draw.line(s, wc, (wx, wave_y - wave_h), (wx, wave_y + wave_h), 2)

    if mt < T_PHASE2:
        status_name = "PIANO SEQUENCE"
    elif mt < T_PHASE3:
        status_name = "STRINGS ENTERING"
    elif mt < T_PHASE4:
        status_name = "EMOTIONAL SUSTAIN"
    elif mt < T_DISTORT:
        status_name = "CRESCENDO"
    else:
        status_name = "FINALIZING"
    s.blit(f["f_tiny"].render(f"STATUS: {status_name}", True, tc), (40, SH - 24))
    s.blit(f["f_tiny"].render(f"♪ {mt:.1f}s", True, lc), (SW - 120, SH - 24))

    # 后处理
    holo_key = round(holo_a * 10)
    if fx.beam_cache is None or fx.beam_holo_key != holo_key:
        beam_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ac = colors["accent"]
        for by2 in range(60, 300, 4):
            progress = (by2 - 60) / 240
            width = int(120 + progress * 350)
            alpha = int(8 * (1 - progress) * max(0.2, holo_a))
            if alpha > 1:
                pygame.draw.line(beam_surf, (*lerp_color(ac, bg, 0.5), alpha),
                                 (SW // 2 - width // 2, by2), (SW // 2 + width // 2, by2), 4)
        fx.beam_cache = beam_surf
        fx.beam_holo_key = holo_key
    s.blit(fx.beam_cache, (0, 0))

    if random.random() < eff["glitch"]:
        gy = random.randint(80, SH - 80)
        gw = random.randint(60, 250)
        gx = random.randint(0, SW - gw)
        shift = random.randint(-25, 25)
        try:
            strip = s.subsurface(pygame.Rect(gx, gy, gw, random.randint(3, 8))).copy()
            s.blit(strip, (gx + shift, gy))
        except ValueError: pass

    vm = vp["vignette_mult"]
    if fx.vignette_cache is None:
        vignette = pygame.Surface((SW, SH), pygame.SRCALPHA)
        for vy in range(0, SH, 2):
            dist = math.sqrt((vy - SH // 2) ** 2) / (SH // 2)
            alpha = int(min(255, dist * dist * 22))
            if alpha > 1:
                pygame.draw.line(vignette, (0, 0, 0, alpha), (0, vy), (SW, vy), 2)
        fx.vignette_cache = vignette
    v_alpha = int(min(255, 255 * vm))
    fx.vignette_cache.set_alpha(v_alpha)
    s.blit(fx.vignette_cache, (0, 0))

    if silence > 0.01:
        dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
        dim.fill((0, 0, 0, int(200 * silence)))
        s.blit(dim, (0, 0))

    if vp["screen_pulse"] > 0.005:
        sp_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ac = colors["accent"]
        sp_a = int(255 * vp["screen_pulse"])
        sp_surf.fill((*ac, sp_a))
        s.blit(sp_surf, (0, 0))

    if vp["edge_glow"] > 0.01:
        ac = colors["accent"]
        eg_a = int(180 * vp["edge_glow"])
        v_strip = make_gradient_strip(40, (ac[0], ac[1], ac[2], eg_a), (ac[0], ac[1], ac[2], 0))
        top_glow = pygame.transform.scale(v_strip, (SW, 40))
        s.blit(top_glow, (0, 0))
        s.blit(pygame.transform.flip(top_glow, False, True), (0, SH - 40))
        h_strip = make_gradient_strip(30, (ac[0], ac[1], ac[2], eg_a), (ac[0], ac[1], ac[2], 0), horizontal=True)
        left_glow = pygame.transform.scale(h_strip, (30, SH))
        s.blit(left_glow, (0, 0))
        s.blit(pygame.transform.flip(left_glow, True, False), (SW - 30, 0))

# ---- 绘制：失真扭曲 ----
def draw_preview_distortion(mgr, s):
    fx = mgr.fx
    s.fill((2, 4, 8))
    t = fx.distort_timer
    duration = 2.0
    if t < 0.2:
        intensity = t / 0.2
    elif t < duration - 0.6:
        intensity = 0.7 + 0.3 * abs(math.sin(t * 8))
    else:
        intensity = max(0, (1.0 - (t - (duration - 0.6)) / 0.6)) * (0.7 + 0.3 * abs(math.sin(t * 8)))
    for _ in range(int(20 * intensity)):
        gy = random.randint(0, SH - 10)
        gw = random.randint(60, SW)
        gx = random.randint(0, max(1, SW - gw))
        shift = int(random.randint(-100, 100) * intensity)
        strip_h = random.randint(2, int(20 * intensity) + 1)
        try:
            strip = s.subsurface(pygame.Rect(gx, gy, min(gw, SW - gx), strip_h)).copy()
            s.blit(strip, (gx + shift, gy))
        except ValueError: pass
    if intensity > 0.15:
        rgb_shift = int(12 * intensity * abs(math.sin(t * 5)))
        if rgb_shift > 0:
            try:
                red = s.subsurface(pygame.Rect(0, 0, SW - rgb_shift, SH)).copy()
                ro = pygame.Surface((SW - rgb_shift, SH), pygame.SRCALPHA)
                ro.fill((255, 0, 0, int(45 * intensity)))
                red.blit(ro, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                s.blit(red, (rgb_shift, 0))
                blue = s.subsurface(pygame.Rect(rgb_shift, 0, SW - rgb_shift, SH)).copy()
                bo = pygame.Surface((SW - rgb_shift, SH), pygame.SRCALPHA)
                bo.fill((0, 0, 255, int(45 * intensity)))
                blue.blit(bo, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                s.blit(blue, (0, 0))
            except ValueError: pass
    for _ in range(int(12 * intensity)):
        bx, by = random.randint(0, SW - 40), random.randint(0, SH - 10)
        bw, bh = random.randint(20, 180), random.randint(3, 25)
        bc = random.choice([(80, 160, 255), (180, 210, 255), (255, 255, 255), (20, 30, 50), (255, 140, 0)])
        bs = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bs.fill((*bc, int(random.randint(50, 160) * intensity)))
        s.blit(bs, (bx, by))
    if random.random() < 0.4 * intensity:
        fc = random.choice([(180, 210, 255), (200, 230, 255), (150, 200, 255)])
        fw, fh = SW // 4, SH // 4
        fs = pygame.Surface((fw, fh), pygame.SRCALPHA)
        fs.fill((*fc, int(random.randint(25, 80) * intensity)))
        for _ in range(4):
            s.blit(fs, (random.randint(0, SW - fw), random.randint(0, SH - fh)))
    scan_gap = max(2, int(4 - 2 * intensity))
    for sy in range(0, SH, scan_gap):
        if random.random() < 0.35 * intensity:
            pygame.draw.line(s, (0, 0, 0, int(random.randint(30, 100) * intensity)), (0, sy), (SW, sy), 1)
    for _ in range(int(6 * intensity)):
        vx = random.randint(0, SW - 10)
        vh = random.randint(60, SH)
        vy = random.randint(0, max(1, SH - vh))
        vshift = int(random.randint(-50, 50) * intensity)
        vw = random.randint(2, int(10 * intensity) + 1)
        try:
            vs = s.subsurface(pygame.Rect(vx, vy, vw, min(vh, SH - vy))).copy()
            s.blit(vs, (vx + vshift, vy))
        except ValueError: pass
    if intensity > 0.4 and random.random() < 0.25:
        sx, sy = int(random.randint(-5, 5) * intensity), int(random.randint(-5, 5) * intensity)
        try:
            ss = s.subsurface(pygame.Rect(max(0, -sx), max(0, -sy), SW - abs(sx), SH - abs(sy))).copy()
            s.fill((0, 0, 0))
            s.blit(ss, (sx, sy))
        except ValueError: pass
    if t > duration - 0.6:
        fp = (t - (duration - 0.6)) / 0.6
        ov = pygame.Surface((SW, SH), pygame.SRCALPHA)
        ov.fill((2, 4, 8, int(255 * min(1.0, fp))))
        s.blit(ov, (0, 0))

# ---- 绘制：重生过渡 ----
def draw_preview_rebirth(mgr, s):
    fx = mgr.fx
    s.fill((2, 4, 8))
    t = fx.distort_timer - 2.0
    rebirth_dur = 1.5
    if t < 0:
        return
    if t < 0.3:
        return
    if t < 1.2:
        p = (t - 0.3) / 0.9
        p = p * p * (3 - 2 * p)
        max_r = 350
        r = int(max_r * p)
        if r > 5 and fx.rebirth_glow_cache:
            glow = fx.rebirth_glow_cache.copy()
            glow.set_alpha(int(min(1, p * 2) * 255))
            scaled = pygame.transform.scale(glow, (r * 2 + 4, r * 2 + 4))
            s.blit(scaled, (SW // 2 - r - 2, SH // 2 - r - 2))
    if 1.2 <= t < rebirth_dur:
        p = (t - 1.2) / 0.3
        if fx.rebirth_glow_cache:
            glow = fx.rebirth_glow_cache.copy()
            glow.set_alpha(int(255 * (1 - p)))
            s.blit(glow, (SW // 2 - 352, SH // 2 - 352))
        dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
        dim.fill((2, 4, 8, int(255 * p * 0.3)))
        s.blit(dim, (0, 0))

# ---- 绘制：卡片 ----
def draw_preview_card(mgr, s):
    fx = mgr.fx
    f = mgr.fonts
    t = fx.dna_timer
    s.fill((2, 4, 8))
    for dp in fx.dna_particles:
        b = dp["brightness"]
        dot = fx.glow_dots[dp["size"]]
        tinted = dot.copy()
        tinted.fill((int(80 * b), int(160 * b), int(255 * b), dp["alpha"]), special_flags=pygame.BLEND_RGBA_MULT)
        sz2 = dp["size"] * 2
        s.blit(tinted, (int(dp["x"]) - sz2, int(dp["y"]) - sz2))
    hex_color = (15, 25, 45, 25)
    if fx.hex_cache is None or fx.hex_cache_color != hex_color:
        hex_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
        draw_hex_grid(hex_surf, hex_color, 70)
        fx.hex_cache = hex_surf
        fx.hex_cache_color = hex_color
    s.blit(fx.hex_cache, (0, 0))
    if t < 1.0:
        if t > 0.3:
            sp = (t - 0.3) / 0.7
            sa = int(200 * sp)
            sh = int(340 * sp)
            pygame.draw.line(s, (255, 140, 0, sa), (SW // 2, SH // 2 - sh // 2), (SW // 2, SH // 2 + sh // 2), 2)
            gw = int(30 * sp)
            gs = pygame.Surface((gw, sh + 20), pygame.SRCALPHA)
            gs.fill((255, 140, 0, sa // 4))
            s.blit(gs, (SW // 2 - gw // 2, SH // 2 - sh // 2 - 10))
        return
    ct = t - 1.0
    cw, ch = 480, 340
    cy = (SH - ch) // 2
    rd = 1.5
    if ct < rd:
        p = ct / rd
        mp = 0.85
        if p < mp:
            e = 1 - (1 - p / mp) ** 2
            angle = e * 370
        else:
            bp = (p - mp) / (1 - mp)
            bv = math.sin(bp * math.pi) * (1 - bp * 0.5)
            angle = 370 - 10 * bv
    else:
        angle = 360
    ar = math.radians(angle)
    sx = abs(math.cos(ar))
    front = math.cos(ar) >= 0
    sp = 1.0
    if rd < ct < rd + 0.3:
        sp = 1.0 + 0.03 * math.sin((ct - rd) / 0.3 * math.pi)
    ba = 0
    if ct > rd:
        ba = int(40 * (0.6 + 0.4 * abs(math.sin((ct - rd) * 1.5))))
    ca = min(255, int(ct * 300))
    if sx < 0.02:
        lx = SW // 2
        ga = min(255, ca)
        pygame.draw.line(s, (255, 140, 0, ga), (lx, cy - 10), (lx, cy + ch + 10), 3)
        lg = pygame.Surface((20, ch + 20), pygame.SRCALPHA)
        pygame.draw.rect(lg, (255, 140, 0, ga // 3), (0, 0, 20, ch + 20))
        s.blit(lg, (lx - 10, cy - 10))
    else:
        sw2 = max(1, int(cw * sx * sp))
        cs = pygame.Surface((cw, ch), pygame.SRCALPHA)
        if front:
            card_bg = fx.card_radial_bg.copy()
            card_bg.set_alpha(min(240, ca))
            cs.blit(card_bg, (0, 0))
            pygame.draw.rect(cs, (255, 140, 0, min(60, ca // 3)), (0, 0, cw, ch), 4, border_radius=12)
            pygame.draw.rect(cs, (255, 160, 40, min(200, ca)), (0, 0, cw, ch), 2, border_radius=12)
            for cx2, cy2 in [(8, 8), (cw - 8, 8), (8, ch - 8), (cw - 8, ch - 8)]:
                pygame.draw.circle(cs, (255, 180, 60, min(200, ca)), (cx2, cy2), 4)
            title_bar = fx.card_title_bar.copy()
            title_bar.set_alpha(min(255, ca))
            cs.blit(title_bar, (0, 0))
            tp2 = 0.6 + 0.4 * abs(math.sin(mgr.blink * 3))
            edge_a = int((1 - abs(0 - cw // 2) / (cw // 2)) * 255 * tp2)
            pygame.draw.line(cs, (255, 140, 0, min(edge_a, ca)), (0, 48), (cw, 48), 2)
            cs.blit(f["f_med"].render("◆ 案件 DNA", True, (255, 180, 60)), (24, 14))
            # 从案件数据中提取真实信息
            cd = mgr.case_data
            if cd:
                title_val = cd.get("title", "未知")
                type_val = cd.get("type", "未知")
                loc_val = cd.get("location", "未知")
                complexity = cd.get("complexity", 2)
                stars = "★" * complexity + "☆" * (3 - complexity)
                phases_val = str(len(cd.get("phases", [])))
                # 计算证据总数
                evidence_count = sum(len(p.get("evidence", [])) for p in cd.get("phases", []))
                items = [("案件标题", title_val), ("罪名类型", type_val),
                         ("案发地点", loc_val), ("难度等级", stars),
                         ("审理阶段", f"{phases_val} 轮"), ("证据总数", str(evidence_count))]
            else:
                items = [("案件标题", "植物花园谋杀案"), ("罪名类型", "蓄意谋杀"),
                         ("案发地点", "向日葵花田"), ("难度等级", "★★☆"),
                         ("审理阶段", "3 轮"), ("证据总数", "7")]
            dy = 48 + 18
            for lb, vl in items:
                pygame.draw.circle(cs, (60, 120, 200, min(150, ca)), (27, dy + 10), 3)
                label_surf = f["f_small"].render(lb, True, (80, 130, 200))
                label_bg = pygame.Surface((label_surf.get_width() + 10, label_surf.get_height() + 4), pygame.SRCALPHA)
                label_bg.fill((30, 40, 60, min(60, ca // 2)))
                cs.blit(label_bg, (34, dy - 2))
                cs.blit(label_surf, (39, dy))
                cs.blit(f["f_small"].render(vl, True, (210, 230, 255)), (120, dy))
                dy += 26
            dy += 6
            sep_grad = make_gradient_strip(cw - 60, (255, 140, 0), (255, 180, 60), horizontal=True)
            sep_scaled = pygame.transform.scale(sep_grad, (cw - 60, 2))
            sep_scaled.set_alpha(min(180, ca))
            cs.blit(sep_scaled, (30, dy))
            dy += 12
            pygame.draw.rect(cs, (40, 20, 10, min(120, ca)), (24, dy - 2, cw - 48, 26), border_radius=4)
            pygame.draw.rect(cs, (255, 140, 0, min(100, ca)), (24, dy - 2, cw - 48, 26), 1, border_radius=4)
            # 显示被告名称
            defendant_name = "未知"
            if cd and cd.get("defendant"):
                defendant_name = cd["defendant"]
            elif cd and cd.get("suspects"):
                defendant_name = cd["suspects"][0].get("name", "未知")
            cs.blit(f["f_small"].render(f"嫌疑人：{defendant_name}", True, (255, 180, 60)), (34, dy + 2))
            dy += 30
            # AI评价（根据案件复杂度生成）
            if cd:
                complexity = cd.get("complexity", 2)
                if complexity <= 1:
                    ai_comment = '"证据确凿，一目了然。"'
                elif complexity == 2:
                    ai_comment = '"破绽百出，值得推敲。"'
                else:
                    ai_comment = '"疑点重重，高手过招。"'
            else:
                ai_comment = '"破绽百出。"'
            cs.blit(f["f_tiny_cn"].render(f"AI评价：{ai_comment}", True, (100, 150, 210)), (34, dy))
            if ct > rd:
                breath_tp = 0.6 + 0.4 * abs(math.sin(mgr.blink * 3))
                tip_h = 32
                tip_strip = make_gradient_strip(tip_h, (255, 140, 0, int(20 * breath_tp)), (255, 160, 40, int(80 * breath_tp)))
                tip_stretched = pygame.transform.scale(tip_strip, (cw, tip_h))
                cs.blit(tip_stretched, (0, ch - tip_h))
                border_a = int(120 * breath_tp)
                pygame.draw.rect(cs, (255, 160, 40, min(border_a, ca)), (0, ch - tip_h, cw, tip_h), 1, border_radius=0)
                tip = "点击任意位置开始庭审 →"
                tc2 = (int(255 * breath_tp), int(180 * breath_tp), int(60 * breath_tp))
                ts = f["f_tiny_cn"].render(tip, True, tc2)
                cs.blit(ts, ts.get_rect(center=(cw // 2, ch - 16)))
        else:
            cs.fill((4, 6, 10, min(240, ca)))
            pygame.draw.rect(cs, (60, 100, 180, min(255, ca)), (0, 0, cw, ch), 2, border_radius=12)
            for i in range(0, cw, 30):
                pygame.draw.line(cs, (30, 50, 90, min(150, ca)), (i, 0), (i, ch), 1)
            for i in range(0, ch, 30):
                pygame.draw.line(cs, (30, 50, 90, min(150, ca)), (0, i), (cw, i), 1)
            cl = f["f_med"].render("◆ CLASSIFIED ◆", True, (60, 100, 180))
            cs.blit(cl, cl.get_rect(center=(cw // 2, ch // 2)))
        cs.set_alpha(ca)
        sc2 = pygame.transform.scale(cs, (sw2, ch))
        bx = SW // 2 - sw2 // 2
        if ba > 0:
            og = pygame.Surface((sw2 + 20, ch + 20), pygame.SRCALPHA)
            pygame.draw.rect(og, (255, 140, 0, ba), (0, 0, sw2 + 20, ch + 20), 3, border_radius=16)
            s.blit(og, (bx - 10, cy - 10))
        s.blit(sc2, (bx, cy))
        if ct < rd and sx < 0.5:
            eg = pygame.Surface((6, ch + 20), pygame.SRCALPHA)
            ea = int(150 * (1 - sx / 0.5))
            eg.fill((255, 140, 0, ea))
            s.blit(eg, (SW // 2 - 3, cy - 10))
