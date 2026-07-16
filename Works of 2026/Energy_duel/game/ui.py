"""tkinter 游戏界面 - 终局战场版"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from .skills import ALL_SKILLS, SKILL_CATEGORIES
from .game_engine import GameEngine

try:
    import pygame
except Exception:
    pygame = None

# ============ 主题配色：暗黑能量战场 ============
COLORS = {
    'bg_dark': '#07090f',
    'bg_panel': '#101827',
    'bg_panel_2': '#151f32',
    'bg_card': '#1a2540',
    'bg_card_hot': '#223052',
    'accent_blue': '#2fd9ff',
    'accent_gold': '#ffd35a',
    'accent_red': '#ff3f68',
    'accent_green': '#44e88d',
    'hp_red': '#ff3f68',
    'hp_yellow': '#ffbd45',
    'hp_green': '#44e88d',
    'energy_blue': '#2fd9ff',
    'bar_empty': '#263247',
    'bar_shadow': '#06080d',
    'text_primary': '#f4f8ff',
    'text_secondary': '#aebbd0',
    'text_dim': '#68768c',
    'p1_color': '#22d9ff',
    'p2_color': '#ff4d6d',
    'btn_primary': '#1fba73',
    'btn_warning': '#e8942e',
    'btn_info': '#227bff',
    'log_bg': '#080b12',
    'log_damage': '#ff708a',
    'log_heal': '#61f0a2',
    'log_buff': '#81d8ff',
    'log_system': '#ffe18a',
}

CAT_COLORS = {
    'damage': '#ff4d6d',
    'defense': '#45b4ff',
    'control': '#bd7cff',
    'develop': '#52e99a',
}

FONTS = {
    'title': ('Microsoft YaHei UI', 23, 'bold'),
    'sub_title': ('Microsoft YaHei UI', 14, 'bold'),
    'body': ('Microsoft YaHei UI', 10),
    'body_bold': ('Microsoft YaHei UI', 10, 'bold'),
    'mono': ('Consolas', 10),
    'number': ('Consolas', 12, 'bold'),
}


class GameUI:
    """游戏主界面"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("能量博弈 · 终局战场")
        self.root.geometry("1180x780")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS['bg_dark'])
        
        self.engine = GameEngine()
        self.selected_x = {1: None, 2: None}
        self.skill_buttons = {}
        self._next_round_frame = None
        self._active_dialog = None
        self._bgm_started = False
        self._bgm_available = False
        self._bgm_error = None
        self._ui_tick = 0
        
        self._init_bgm()
        self._create_widgets()
        self._show_skill_select_phase()
        self._animate_ui()
    
    # ============ 音频与动效 ============
    
    def _init_bgm(self):
        """初始化局内循环 BGM"""
        self.bgm_path = Path(__file__).resolve().parent.parent / "audio" / "g3.mp3"
        if pygame is None:
            self._bgm_error = "未安装 pygame，BGM 未启用"
            return
        if not self.bgm_path.exists():
            self._bgm_error = "未找到 audio/g3.mp3"
            return
        try:
            pygame.mixer.init()
            self._bgm_available = True
        except Exception as exc:
            self._bgm_error = f"音频初始化失败：{exc}"
    
    def _play_bgm(self):
        """开始循环播放 BGM"""
        if self._bgm_started or not self._bgm_available:
            return
        try:
            pygame.mixer.music.load(str(self.bgm_path))
            pygame.mixer.music.set_volume(0.42)
            pygame.mixer.music.play(-1)
            self._bgm_started = True
            if hasattr(self, 'bgm_label'):
                self.bgm_label.config(text="BGM: g3.mp3  循环播放中", fg=COLORS['accent_green'])
        except Exception as exc:
            self._bgm_error = f"BGM 播放失败：{exc}"
            if hasattr(self, 'bgm_label'):
                self.bgm_label.config(text=self._bgm_error, fg=COLORS['accent_red'])
    
    def _stop_bgm(self):
        """停止 BGM"""
        if pygame and self._bgm_started:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self._bgm_started = False
    
    def _animate_ui(self):
        """轻量 UI 呼吸动效"""
        self._ui_tick = (self._ui_tick + 1) % 120
        if hasattr(self, 'vs_label'):
            pulse = self._ui_tick < 60
            self.vs_label.config(fg=COLORS['accent_gold'] if pulse else COLORS['accent_blue'])
        if hasattr(self, 'core_label'):
            self.core_label.config(fg=COLORS['accent_blue'] if self._ui_tick < 60 else COLORS['accent_gold'])
        self.root.after(520, self._animate_ui)

    # ============ 主界面构建 ============
    
    def _create_widgets(self):
        """创建主界面组件"""
        # 顶部标题栏
        self.header = tk.Frame(self.root, bg=COLORS['bg_dark'], height=72)
        self.header.pack(fill=tk.X, padx=18, pady=(14, 6))
        self.header.pack_propagate(False)
        
        title_wrap = tk.Frame(self.header, bg=COLORS['bg_dark'],
                              highlightbackground=COLORS['line'] if 'line' in COLORS else COLORS['bar_empty'],
                              highlightthickness=0)
        title_wrap.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            title_wrap, text="ENERGY DUEL / 终局战场",
            font=("Consolas", 9, "bold"),
            fg=COLORS['accent_blue'], bg=COLORS['bg_dark']
        ).pack(pady=(2, 0))
        
        self.round_label = tk.Label(
            title_wrap, text="⚔  准备阶段  ⚔",
            font=FONTS['title'],
            fg=COLORS['accent_gold'], bg=COLORS['bg_dark']
        )
        self.round_label.pack(pady=(2, 0))
        self.bgm_label = tk.Label(
            title_wrap,
            text="BGM: 待机" if not self._bgm_error else self._bgm_error,
            font=("Consolas", 9, "bold"),
            fg=COLORS['text_secondary'] if not self._bgm_error else COLORS['accent_red'],
            bg=COLORS['bg_dark']
        )
        self.bgm_label.pack(pady=(2, 0))
        
        # 中间游戏区域
        self.game_frame = tk.Frame(self.root, bg=COLORS['bg_dark'])
        self.game_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=6)
        
        # 玩家1面板（左）
        self.p1_frame = tk.Frame(self.game_frame, bg=COLORS['bg_panel'],
                                  highlightbackground=COLORS['p1_color'],
                                  highlightthickness=3, bd=0)
        self.p1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=5)
        
        # 中间 VS 分隔
        vs_frame = tk.Frame(self.game_frame, bg=COLORS['bg_dark'], width=78)
        vs_frame.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=5)
        vs_frame.pack_propagate(False)
        self.vs_label = tk.Label(vs_frame, text="VS", font=("Impact", 34, "bold"),
                 fg=COLORS['accent_gold'], bg=COLORS['bg_dark'])
        self.vs_label.pack(pady=(118, 0))
        self.core_label = tk.Label(vs_frame, text="⚡", font=("Segoe UI Emoji", 26),
                 fg=COLORS['accent_blue'], bg=COLORS['bg_dark'])
        self.core_label.pack(pady=(8, 8))
        tk.Label(vs_frame, text="ROUND\nCORE", font=("Consolas", 8, "bold"),
                 fg=COLORS['text_dim'], bg=COLORS['bg_dark'], justify=tk.CENTER).pack()
        
        # 玩家2面板（右）
        self.p2_frame = tk.Frame(self.game_frame, bg=COLORS['bg_panel'],
                                  highlightbackground=COLORS['p2_color'],
                                  highlightthickness=3, bd=0)
        self.p2_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=5)
        
        # 创建玩家面板内容
        self.p1_widgets = self._create_player_panel(self.p1_frame, 1)
        self.p2_widgets = self._create_player_panel(self.p2_frame, 2)
        
        # 底部战场态势条
        self.battle_status = tk.Frame(self.root, bg=COLORS['bg_panel_2'],
                                      highlightbackground=COLORS['bar_empty'], highlightthickness=1)
        self.battle_status.pack(fill=tk.X, padx=18, pady=(2, 6))
        tk.Label(self.battle_status, text="BATTLEFIELD STATUS", font=("Consolas", 8, "bold"),
                 fg=COLORS['accent_gold'], bg=COLORS['bg_panel_2']).pack(side=tk.LEFT, padx=10, pady=5)
        tk.Label(self.battle_status, text="同步结算 · 资源博弈 · 冷却封锁", font=FONTS['body'],
                 fg=COLORS['text_secondary'], bg=COLORS['bg_panel_2']).pack(side=tk.LEFT, padx=16)
        
        # 底部日志
        self.log_frame = tk.Frame(self.root, bg=COLORS['bg_dark'])
        self.log_frame.pack(fill=tk.X, padx=18, pady=(6, 12))
        
        # 指挥台装饰
        command_strip = tk.Frame(self.log_frame, bg=COLORS['bg_panel_2'], highlightbackground=COLORS['bar_empty'], highlightthickness=1)
        command_strip.pack(fill=tk.X, pady=(0, 6))
        tk.Label(command_strip, text="COMMAND CHANNEL", font=("Consolas", 8, "bold"),
                 fg=COLORS['accent_blue'], bg=COLORS['bg_panel_2']).pack(side=tk.LEFT, padx=10, pady=5)
        tk.Label(command_strip, text="伤害 / 回复 / 控制 / 回合事件实时记录", font=FONTS['body'],
                 fg=COLORS['text_secondary'], bg=COLORS['bg_panel_2']).pack(side=tk.LEFT, padx=18)
        
        log_label = tk.Label(self.log_frame, text="▣ 战斗日志 / BATTLE LOG",
                            font=FONTS['body_bold'],
                            fg=COLORS['accent_gold'], bg=COLORS['bg_dark'], anchor=tk.W)
        log_label.pack(fill=tk.X, pady=(0, 4))
        
        self.log_text = tk.Text(
            self.log_frame, height=8, font=FONTS['mono'],
            bg=COLORS['log_bg'], fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            selectbackground=COLORS['accent_blue'],
            relief=tk.FLAT, padx=14, pady=10,
            highlightbackground=COLORS['bar_empty'],
            highlightcolor=COLORS['accent_blue'],
            highlightthickness=1
        )
        scrollbar = tk.Scrollbar(self.log_frame, command=self.log_text.yview,
                                  bg=COLORS['bg_panel'], troughcolor=COLORS['bg_dark'])
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 日志颜色标签
        self.log_text.tag_configure('damage', foreground=COLORS['log_damage'])
        self.log_text.tag_configure('heal', foreground=COLORS['log_heal'])
        self.log_text.tag_configure('buff', foreground=COLORS['log_buff'])
        self.log_text.tag_configure('system', foreground=COLORS['log_system'],
                                    font=("Consolas", 10, "bold"))
        self.log_text.tag_configure('header', foreground=COLORS['accent_gold'],
                                    font=("Consolas", 11, "bold"))
        self.log_text.tag_configure('info', foreground=COLORS['text_secondary'])
    
    def _create_player_panel(self, parent: tk.Frame, player_id: int) -> dict:
        """创建玩家状态面板"""
        widgets = {}
        color = COLORS['p1_color'] if player_id == 1 else COLORS['p2_color']
        side_name = "左阵营" if player_id == 1 else "右阵营"
        
        # 玩家标题
        title_frame = tk.Frame(parent, bg=color, height=48)
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text=f"  PLAYER {player_id}  ·  {side_name}",
                 font=FONTS['sub_title'],
                 fg="#061019", bg=color).pack(side=tk.LEFT, padx=14, pady=9)
        tk.Label(title_frame, text="READY", font=("Consolas", 10, "bold"),
                 fg="#061019", bg=color).pack(side=tk.RIGHT, padx=14)
        
        content = tk.Frame(parent, bg=COLORS['bg_panel'])
        content.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)
        
        # 战术读数区
        tactical = tk.Frame(content, bg=COLORS['bg_panel_2'], highlightbackground=COLORS['bar_empty'], highlightthickness=1)
        tactical.pack(fill=tk.X, pady=(0, 12))
        tk.Label(tactical, text="TACTICAL HUD", font=("Consolas", 8, "bold"),
                 fg=color, bg=COLORS['bg_panel_2']).pack(anchor=tk.W, padx=10, pady=(6, 0))
        data_row = tk.Frame(tactical, bg=COLORS['bg_panel_2'])
        data_row.pack(fill=tk.X, padx=10, pady=(2, 8))
        tk.Label(data_row, text="冷却监控", font=FONTS['body'],
                 fg=COLORS['text_secondary'], bg=COLORS['bg_panel_2']).pack(side=tk.LEFT)
        tk.Label(data_row, text="资源压制", font=FONTS['body'],
                 fg=COLORS['text_secondary'], bg=COLORS['bg_panel_2']).pack(side=tk.LEFT, padx=22)
        tk.Label(data_row, text="技能矩阵", font=FONTS['body'],
                 fg=COLORS['text_secondary'], bg=COLORS['bg_panel_2']).pack(side=tk.LEFT)
        
        # 生命条
        tk.Label(content, text="❤ 生命值 / HP", font=FONTS['body_bold'],
                 fg=COLORS['accent_red'], bg=COLORS['bg_panel'], anchor=tk.W).pack(fill=tk.X, pady=(6, 3))
        hp_frame = tk.Frame(content, bg=COLORS['bg_panel'])
        hp_frame.pack(fill=tk.X, pady=3)
        
        hp_canvas = tk.Canvas(hp_frame, width=310, height=26, bg=COLORS['bar_shadow'],
                              highlightthickness=1, highlightbackground=COLORS['bar_empty'])
        hp_canvas.pack(side=tk.LEFT)
        widgets['hp_canvas'] = hp_canvas
        
        hp_label = tk.Label(hp_frame, text="7 / 10", font=FONTS['number'],
                           fg=COLORS['text_primary'], bg=COLORS['bg_panel'], width=8)
        hp_label.pack(side=tk.LEFT, padx=10)
        widgets['hp_label'] = hp_label
        
        # 能量条
        tk.Label(content, text="⚡ 能量值 / ENERGY", font=FONTS['body_bold'],
                 fg=COLORS['accent_blue'], bg=COLORS['bg_panel'], anchor=tk.W).pack(fill=tk.X, pady=(12, 3))
        energy_frame = tk.Frame(content, bg=COLORS['bg_panel'])
        energy_frame.pack(fill=tk.X, pady=3)
        
        energy_canvas = tk.Canvas(energy_frame, width=310, height=26, bg=COLORS['bar_shadow'],
                                  highlightthickness=1, highlightbackground=COLORS['bar_empty'])
        energy_canvas.pack(side=tk.LEFT)
        widgets['energy_canvas'] = energy_canvas
        
        energy_label = tk.Label(energy_frame, text="5 / 10", font=FONTS['number'],
                               fg=COLORS['text_primary'], bg=COLORS['bg_panel'], width=8)
        energy_label.pack(side=tk.LEFT, padx=10)
        widgets['energy_label'] = energy_label
        
        # 分隔线
        sep = tk.Frame(content, bg=COLORS['bar_empty'], height=1)
        sep.pack(fill=tk.X, pady=(14, 10))
        
        # 状态效果
        tk.Label(content, text="▣ 状态矩阵 / STATUS", font=FONTS['body_bold'],
                 fg=COLORS['text_secondary'], bg=COLORS['bg_panel'], anchor=tk.W).pack(fill=tk.X, pady=(0, 4))
        status_text = tk.Text(content, height=6, width=35, font=FONTS['body'],
                             bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                             relief=tk.FLAT, padx=10, pady=8,
                             highlightbackground=COLORS['bar_empty'],
                             highlightcolor=color,
                             highlightthickness=1,
                             insertbackground=COLORS['text_primary'])
        status_text.pack(fill=tk.BOTH, expand=True, pady=4)
        status_text.config(state=tk.DISABLED)
        widgets['status_text'] = status_text
        
        return widgets
    
    # ============ 绘制条 ============
    
    def _draw_hp_bar(self, canvas: tk.Canvas, hp: int, max_hp: int):
        """绘制生命条"""
        canvas.delete("all")
        w = 310
        h = 26
        seg_w = w / max_hp
        canvas.create_rectangle(0, 0, w, h, fill=COLORS['bar_shadow'], outline="")
        
        for i in range(max_hp):
            x1 = i * seg_w
            x2 = (i + 1) * seg_w
            if i < hp:
                if i < 3:
                    color = COLORS['hp_red']
                elif i < 6:
                    color = COLORS['hp_yellow']
                else:
                    color = COLORS['hp_green']
            else:
                color = COLORS['bar_empty']
            canvas.create_rectangle(x1 + 2, 3, x2 - 2, h - 3,
                                   fill=color, outline="", width=0)
            if i < hp:
                canvas.create_line(x1 + 3, 5, x2 - 3, 5, fill="#ffffff", width=1)
        canvas.create_text(w / 2, h / 2, text=f"HP {hp}/{max_hp}",
                           fill="#ffffff", font=("Consolas", 9, "bold"))
    
    def _draw_energy_bar(self, canvas: tk.Canvas, energy: int, max_energy: int):
        """绘制能量条"""
        canvas.delete("all")
        w = 310
        h = 26
        seg_w = w / max_energy
        canvas.create_rectangle(0, 0, w, h, fill=COLORS['bar_shadow'], outline="")
        
        for i in range(max_energy):
            x1 = i * seg_w
            x2 = (i + 1) * seg_w
            color = COLORS['energy_blue'] if i < energy else COLORS['bar_empty']
            canvas.create_rectangle(x1 + 2, 3, x2 - 2, h - 3,
                                   fill=color, outline="", width=0)
            if i < energy:
                canvas.create_line(x1 + 3, 5, x2 - 3, 5, fill="#e9fbff", width=1)
        canvas.create_text(w / 2, h / 2, text=f"ENERGY {energy}/{max_energy}",
                           fill="#061019", font=("Consolas", 9, "bold"))
    
    def _update_status_text(self, text_widget: tk.Text, player):
        """更新状态效果显示"""
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        
        type_info = {
            'fire_burn': ('🔥 灼烧', COLORS['log_damage']),
            'poison': ('☠ 中毒', COLORS['log_damage']),
            'bomb': ('💣 炸弹', COLORS['log_damage']),
            'death_buff': ('⚔ 向死之力', COLORS['log_buff']),
            'regen_energy': ('⚡ 能量回复', COLORS['log_heal']),
            'regen_both': ('✨ 生命能量回复', COLORS['log_heal']),
            'death_fight': ('🗡 死斗(受伤回能)', COLORS['log_buff']),
            'death_fight_no_heal': ('🚫 死斗(禁回复)', COLORS['log_damage']),
            'thorn_shield': ('🛡 刺盾', COLORS['log_buff']),
            'shield': ('🛡 护盾', COLORS['log_buff']),
        }
        
        if not player.status_effects:
            text_widget.insert(tk.END, "  无状态效果", 'dim')
        else:
            for eff in player.status_effects:
                name, _color = type_info.get(eff.effect_type, (eff.effect_type, COLORS['text_primary']))
                delay_text = f" (延迟{eff.delay}回合)" if eff.delay > 0 else ""
                text_widget.insert(tk.END, f"  {name}: {eff.duration}回合{delay_text}\n")
        
        # 冷却中的技能
        cd_skills = [s for s in player.selected_skills if player.cooldowns.get(s, 0) > 0]
        if cd_skills:
            text_widget.insert(tk.END, "\n  ⏳ 冷却中:\n")
            for s in cd_skills:
                text_widget.insert(tk.END, f"    {s}: {player.cooldowns[s]}回合\n")
        
        text_widget.tag_configure('dim', foreground=COLORS['text_dim'])
        text_widget.config(state=tk.DISABLED)
    
    def _update_display(self):
        """更新界面显示"""
        p1 = self.engine.get_player(1)
        p2 = self.engine.get_player(2)
        
        self._draw_hp_bar(self.p1_widgets['hp_canvas'], p1.hp, p1.max_hp)
        self.p1_widgets['hp_label'].config(text=f"{p1.hp} / {p1.max_hp}")
        self._draw_energy_bar(self.p1_widgets['energy_canvas'], p1.energy, p1.max_energy)
        self.p1_widgets['energy_label'].config(text=f"{p1.energy} / {p1.max_energy}")
        self._update_status_text(self.p1_widgets['status_text'], p1)
        
        self._draw_hp_bar(self.p2_widgets['hp_canvas'], p2.hp, p2.max_hp)
        self.p2_widgets['hp_label'].config(text=f"{p2.hp} / {p2.max_hp}")
        self._draw_energy_bar(self.p2_widgets['energy_canvas'], p2.energy, p2.max_energy)
        self.p2_widgets['energy_label'].config(text=f"{p2.energy} / {p2.max_energy}")
        self._update_status_text(self.p2_widgets['status_text'], p2)
        
        if self.engine.phase == 'playing':
            self.round_label.config(text=f"⚔  第 {self.engine.round} 回合  ⚔")
            if hasattr(self, 'bgm_label') and self._bgm_started:
                self.bgm_label.config(text="BGM: g3.mp3  循环播放中", fg=COLORS['accent_green'])
        elif self.engine.phase == 'game_over':
            self.round_label.config(text="⚔  游戏结束  ⚔")
        else:
            self.round_label.config(text="⚔  准备阶段  ⚔")
    
    def _add_log(self, messages: list):
        """添加日志（带颜色）"""
        self.log_text.config(state=tk.NORMAL)
        for msg in messages:
            tag = None
            if '===' in msg:
                tag = 'header'
            elif '伤害' in msg or '削减' in msg or '反弹' in msg or '发作' in msg or '爆炸' in msg or '灼烧' in msg:
                tag = 'damage'
            elif '恢复' in msg or '回复' in msg or '修复' in msg or '+1' in msg:
                tag = 'heal'
            elif 'buff' in msg or '效果' in msg or '禁用' in msg or '死斗' in msg or '防守' in msg:
                tag = 'buff'
            elif '回合' in msg and ('开始' in msg or '结束' in msg):
                tag = 'system'
            self.log_text.insert(tk.END, msg + "\n", tag if tag else ())
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    # ============ 技能选择阶段 ============
    
    def _close_active_dialog(self):
        """关闭当前正在显示的弹窗，避免回合切换时出现层级冲突。"""
        if self._active_dialog is not None:
            if hasattr(self._active_dialog, 'winfo_exists') and self._active_dialog.winfo_exists():
                self._active_dialog.destroy()
            self._active_dialog = None

    def _show_skill_select_phase(self):
        self._close_active_dialog()
        self._update_display()
        self._show_skill_select_dialog(1)
    
    def _style_dialog(self, dialog):
        """统一弹窗样式"""
        dialog.configure(bg=COLORS['bg_dark'])
    
    def _show_skill_select_dialog(self, player_id: int):
        """显示技能选择弹窗"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"玩家 {player_id} - 选择10个技能")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.focus_force()
        dialog.lift()
        dialog.attributes('-topmost', True)
        self._style_dialog(dialog)
        self.root.update_idletasks()
        dialog.attributes('-topmost', False)
        self._active_dialog = dialog
        self._active_dialog = dialog
        
        color = COLORS['p1_color'] if player_id == 1 else COLORS['p2_color']
        
        # 标题
        title_bar = tk.Frame(dialog, bg=color, height=52)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text=f"PLAYER {player_id} · 选择10个技能进入战场",
                 font=FONTS['sub_title'], fg="#061019", bg=color).pack(pady=12)
        
        selected_vars = {}
        
        # 推荐技能组合
        presets = {
            '均衡型（推荐新手）': ['攻击', '火攻', '破釜', '护盾', '刺盾', '弱化', '死斗', '修复', '生息', '忘隙'],
            '进攻型': ['攻击', '火攻', '毒计', '炸弹', '向死', '破釜', '护盾', '弱化', '修复', '生息'],
            '防守反击型': ['攻击', '破釜', '护盾', '刺盾', '弱化', '死斗', '修复', '生息', '妄生', '忘隙'],
            '控制型': ['攻击', '火攻', '护盾', '弱化', '御策', '息兵', '死斗', '修复', '生息', '妄生'],
        }
        
        preset_frame = tk.Frame(dialog, bg=COLORS['bg_panel'],
                                highlightbackground=COLORS['bar_empty'], highlightthickness=1)
        preset_frame.pack(padx=15, pady=(10, 5), fill=tk.X)
        
        tk.Label(preset_frame, text="⚡ 推荐组合 / PRESET DECKS", font=FONTS['body_bold'],
                 fg=COLORS['accent_gold'], bg=COLORS['bg_panel'], anchor=tk.W).pack(fill=tk.X, padx=12, pady=(8, 4))
        
        def apply_preset(preset_name):
            for var in selected_vars.values():
                var.set(False)
            for skill_name in presets[preset_name]:
                if skill_name in selected_vars:
                    selected_vars[skill_name].set(True)
        
        btn_row = tk.Frame(preset_frame, bg=COLORS['bg_panel'])
        btn_row.pack(padx=10, pady=(0, 8), fill=tk.X)
        for preset_name in presets:
            tk.Button(btn_row, text=preset_name, font=FONTS['body'],
                     bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                     activebackground=COLORS['accent_blue'], activeforeground="#061019",
                     relief=tk.FLAT, padx=10, pady=5, cursor="hand2",
                     command=lambda n=preset_name: apply_preset(n)).pack(side=tk.LEFT, padx=4)
        
        # 技能列表区域（可滚动）
        skill_outer = tk.Frame(dialog, bg=COLORS['bg_dark'])
        skill_outer.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        canvas = tk.Canvas(skill_outer, bg=COLORS['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(skill_outer, command=canvas.yview,
                                  bg=COLORS['bg_panel'], troughcolor=COLORS['bg_dark'])
        frame = tk.Frame(canvas, bg=COLORS['bg_dark'])
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 按类别显示技能
        categories = {'damage': [], 'defense': [], 'control': [], 'develop': []}
        for name, skill in ALL_SKILLS.items():
            categories[skill.category].append((name, skill))
        
        row = 0
        cat_labels = {'damage': '🗡 伤害类', 'defense': '🛡 防御类', 'control': '🎯 控制类', 'develop': '🌱 发育类'}
        for cat, _ in SKILL_CATEGORIES.items():
            cat_name = cat_labels.get(cat, cat)
            cat_color = CAT_COLORS.get(cat, COLORS['text_primary'])
            tk.Label(frame, text=cat_name, font=FONTS['body_bold'],
                     fg=cat_color, bg=COLORS['bg_dark'], anchor=tk.W).grid(
                row=row, column=0, columnspan=4, sticky=tk.W, pady=(12, 4), padx=(5, 0))
            row += 1
            
            col = 0
            for name, skill in categories[cat]:
                var = tk.BooleanVar()
                selected_vars[name] = var
                
                desc = skill.get_description(1).split("；")[0][:18]
                cb = tk.Checkbutton(
                    frame, text=f"{name} ({desc})", variable=var,
                    font=FONTS['body'], bg=COLORS['bg_dark'],
                    fg=COLORS['text_primary'], selectcolor=COLORS['bg_card_hot'],
                    activebackground=COLORS['bg_dark'], activeforeground=cat_color,
                    anchor=tk.W
                )
                cb.grid(row=row, column=col, sticky=tk.W, padx=5)
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            if col != 0:
                row += 1
        
        # 底部确认区
        bottom = tk.Frame(dialog, bg=COLORS['bg_panel'], height=50)
        bottom.pack(fill=tk.X, padx=0, pady=0)
        bottom.pack_propagate(False)
        
        count_label = tk.Label(bottom, text="已选择: 0/10", font=FONTS['sub_title'],
                              fg=COLORS['text_primary'], bg=COLORS['bg_panel'])
        count_label.pack(side=tk.LEFT, padx=20)
        
        def update_count(*args):
            count = sum(1 for v in selected_vars.values() if v.get())
            count_label.config(text=f"已选择: {count}/10",
                             fg=COLORS['accent_green'] if count == 10 else COLORS['text_primary'])
        
        for var in selected_vars.values():
            var.trace_add("write", update_count)
        
        def confirm():
            selected = [name for name, var in selected_vars.items() if var.get()]
            if len(selected) != 10:
                messagebox.showwarning("错误", f"请选择恰好10个技能（当前：{len(selected)}个）")
                return
            
            self.engine.set_player_skills(player_id, selected)
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()
            
            if player_id == 1:
                self._show_skill_select_dialog(2)
            else:
                self.engine.start_game()
                self._play_bgm()
                self._add_log(["双方技能选择完毕，游戏开始！"])
                self._add_log([f"玩家1技能: {', '.join(self.engine.get_player(1).selected_skills)}"])
                self._add_log([f"玩家2技能: {', '.join(self.engine.get_player(2).selected_skills)}"])
                self._start_new_round()
        
        tk.Button(bottom, text="✔ 确认选择", command=confirm,
                 font=FONTS['sub_title'], bg=COLORS['btn_primary'], fg="white",
                 activebackground=COLORS['accent_green'], activeforeground="#061019",
                 relief=tk.FLAT, padx=28, pady=7, cursor="hand2").pack(side=tk.RIGHT, padx=20, pady=8)
    
    # ============ 回合制对战 ============
    
    def _start_new_round(self):
        self._close_active_dialog()
        logs = self.engine.start_round()
        self._add_log(logs)
        self._update_display()
        
        if self.engine.phase == 'game_over':
            self._show_game_over()
            return
        
        self.selected_x = {1: None, 2: None}
        self.root.after(50, lambda: self._show_turn_dialog(1))
    
    def _show_turn_dialog(self, player_id: int):
        """显示回合选择弹窗"""
        player = self.engine.get_player(player_id)
        available = player.get_available_skills()
        color = COLORS['p1_color'] if player_id == 1 else COLORS['p2_color']
        
        self._close_active_dialog()
        dialog = tk.Toplevel(self.root)
        dialog.title(f"第{self.engine.round}回合 - 玩家{player_id}")
        dialog.geometry("640x520")
        dialog.transient(self.root)
        dialog.focus_force()
        dialog.lift()
        dialog.attributes('-topmost', True)
        self._style_dialog(dialog)
        self.root.update_idletasks()
        dialog.attributes('-topmost', False)
        self._active_dialog = dialog
        
        # 标题栏
        title_bar = tk.Frame(dialog, bg=color, height=52)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text=f"⚔ PLAYER {player_id} · 第 {self.engine.round} 回合",
                 font=FONTS['sub_title'], fg="#061019", bg=color).pack(side=tk.LEFT, padx=16)
        tk.Label(title_bar,
                 text=f"❤ {player.hp}/{player.max_hp}   ⚡ {player.energy}/{player.max_energy}",
                 font=FONTS['body_bold'], fg="#061019", bg=color).pack(side=tk.RIGHT, padx=16)
        
        # 选择x值
        x_frame = tk.Frame(dialog, bg=COLORS['bg_panel'],
                          highlightbackground=COLORS['bar_empty'], highlightthickness=1)
        x_frame.pack(padx=15, pady=10, fill=tk.X)
        
        tk.Label(x_frame, text="选择强度 x：", font=FONTS['body_bold'],
                 fg=COLORS['accent_gold'], bg=COLORS['bg_panel']).pack(side=tk.LEFT, padx=(12, 5))
        
        selected_x = tk.IntVar(value=1)
        
        def update_skill_buttons():
            x = selected_x.get()
            for btn_name, btn_data in skill_btns.items():
                skill = ALL_SKILLS[btn_name]
                cost = skill.get_cost(x)
                can_use = player.energy >= cost.get('energy', 0) and player.hp > cost.get('hp', 0)
                
                cost_parts = []
                if cost.get('hp', 0) > 0:
                    cost_parts.append(f"❤-{cost['hp']}")
                if cost.get('energy', 0) > 0:
                    cost_parts.append(f"⚡-{cost['energy']}")
                cost_str = ' '.join(cost_parts) if cost_parts else '免费'
                
                effect = skill.get_description(x).split('；', 1)[-1]
                btn_data['button'].config(
                    text=f"{btn_name}  [{cost_str}]  → {effect}",
                    state=tk.NORMAL if can_use else tk.DISABLED,
                    bg=COLORS['bg_card'] if can_use else COLORS['bar_empty'],
                )
        
        for x_val in [1, 2, 3]:
            rb = tk.Radiobutton(
                x_frame, text=f" x={x_val} ", variable=selected_x, value=x_val,
                font=("Consolas", 11, "bold"), bg=COLORS['bg_panel'],
                fg=COLORS['text_primary'], selectcolor=COLORS['bg_card_hot'],
                activebackground=COLORS['bg_panel'], activeforeground=COLORS['accent_gold'],
                command=update_skill_buttons
            )
            rb.pack(side=tk.LEFT, padx=8)
        
        # 技能按钮区域
        skill_frame = tk.Frame(dialog, bg=COLORS['bg_dark'])
        skill_frame.pack(padx=15, pady=5, fill=tk.BOTH, expand=True)
        
        tk.Label(skill_frame, text="选择技能 / SKILL COMMAND", font=FONTS['body_bold'],
                 fg=COLORS['accent_blue'], bg=COLORS['bg_dark'], anchor=tk.W).pack(fill=tk.X)
        
        canvas = tk.Canvas(skill_frame, bg=COLORS['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(skill_frame, command=canvas.yview,
                                  bg=COLORS['bg_panel'], troughcolor=COLORS['bg_dark'])
        scroll_frame = tk.Frame(canvas, bg=COLORS['bg_dark'])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        skill_btns = {}
        
        def select_skill(skill_name):
            x = selected_x.get()
            self.engine.submit_choice(player_id, skill_name, x)
            self._close_active_dialog()
            if player_id == 1:
                self.root.after(0, lambda: self._show_turn_dialog(2))
            else:
                self.root.after(0, self._resolve_round)
        
        for skill_name in available:
            skill = ALL_SKILLS[skill_name]
            x = selected_x.get()
            cost = skill.get_cost(x)
            
            cost_parts = []
            if cost.get('hp', 0) > 0:
                cost_parts.append(f"❤-{cost['hp']}")
            if cost.get('energy', 0) > 0:
                cost_parts.append(f"⚡-{cost['energy']}")
            cost_str = ' '.join(cost_parts) if cost_parts else '免费'
            
            cat_color = CAT_COLORS.get(skill.category, COLORS['text_primary'])
            
            btn = tk.Button(
                scroll_frame, text=f" {skill_name}  [{cost_str}]",
                font=FONTS['body_bold'], anchor=tk.W,
                bg=COLORS['bg_card'], fg=COLORS['text_primary'],
                activebackground=color, activeforeground="#061019",
                relief=tk.FLAT, padx=12, pady=8, cursor="hand2",
                highlightbackground=cat_color, highlightthickness=2,
                command=lambda s=skill_name: select_skill(s)
            )
            btn.pack(fill=tk.X, padx=2, pady=3)
            skill_btns[skill_name] = {'button': btn, 'skill': skill}
        
        # 跳过按钮
        skip_frame = tk.Frame(dialog, bg=COLORS['bg_dark'])
        skip_frame.pack(pady=(0, 10))
        tk.Button(skip_frame, text="⏭ 跳过本回合", font=FONTS['body_bold'],
                 command=lambda: select_skill(None),
                 bg=COLORS['btn_warning'], fg="white",
                 activebackground=COLORS['accent_gold'], activeforeground="#061019",
                 relief=tk.FLAT, padx=24, pady=7, cursor="hand2").pack()
        
        update_skill_buttons()
    
    def _resolve_round(self):
        self._close_active_dialog()
        logs = self.engine.resolve_turn()
        self._add_log(logs)
        self._update_display()
        
        if self.engine.phase == 'game_over':
            self._show_game_over()
        else:
            self.root.after(0, self._start_new_round)
    
    def _show_next_round_button(self):
        if self._next_round_frame:
            self._next_round_frame.destroy()
        
        self._next_round_frame = tk.Frame(self.root, bg=COLORS['bg_dark'])
        self._next_round_frame.pack(pady=8)
        
        def next_round():
            if self._next_round_frame is not None:
                self._next_round_frame.destroy()
                self._next_round_frame = None
            self.root.update_idletasks()
            self.root.after(0, self._start_new_round)
        
        tk.Button(
            self._next_round_frame, text=f"▶  进入第 {self.engine.round} 回合",
            font=FONTS['sub_title'], bg=COLORS['btn_info'], fg="white",
            activebackground=COLORS['accent_blue'], activeforeground="#061019",
            relief=tk.FLAT, padx=46, pady=12, cursor="hand2",
            command=next_round
        ).pack()
    
    def _show_game_over(self):
        self._close_active_dialog()
        self._update_display()
        self._stop_bgm()
        if hasattr(self, 'bgm_label'):
            self.bgm_label.config(text="BGM: 已停止", fg=COLORS['text_secondary'])
        winner = self.engine.winner
        color = COLORS['p1_color'] if winner == 1 else COLORS['p2_color']
        
        dialog = tk.Toplevel(self.root)
        dialog.title("游戏结束")
        dialog.geometry("420x320")
        dialog.transient(self.root)
        dialog.grab_set()
        self._style_dialog(dialog)
        
        tk.Label(dialog, text="🏆", font=("Segoe UI Emoji", 48),
                 bg=COLORS['bg_dark']).pack(pady=(30, 10))
        tk.Label(dialog, text="游戏结束！", font=FONTS['title'],
                 fg=COLORS['accent_gold'], bg=COLORS['bg_dark']).pack()
        tk.Label(dialog, text=f"PLAYER {winner} 获胜！",
                 font=("Microsoft YaHei UI", 24, "bold"), fg=color, bg=COLORS['bg_dark']).pack(pady=15)
        
        def restart():
            dialog.destroy()
            self._restart_game()
        
        tk.Button(dialog, text="🔄 重新开始", command=restart,
                 font=FONTS['sub_title'], bg=COLORS['btn_primary'], fg="white",
                 activebackground=COLORS['accent_green'], activeforeground="#061019",
                 relief=tk.FLAT, padx=34, pady=12, cursor="hand2").pack(pady=20)
    
    def _restart_game(self):
        self._close_active_dialog()
        if self._next_round_frame:
            self._next_round_frame.destroy()
            self._next_round_frame = None
        self.engine = GameEngine()
        self._stop_bgm()
        if hasattr(self, 'bgm_label'):
            self.bgm_label.config(text="BGM: 待机" if not self._bgm_error else self._bgm_error,
                                  fg=COLORS['text_secondary'] if not self._bgm_error else COLORS['accent_red'])
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._show_skill_select_phase()


def start_game():
    """启动游戏"""
    root = tk.Tk()
    game = GameUI(root)
    root.mainloop()
