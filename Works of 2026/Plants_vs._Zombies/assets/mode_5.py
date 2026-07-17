"""
AI植物法庭 - Mode 5
逆转裁判风格法庭推理小游戏
三阶段流程：自动播放证词 → 自由追问 → 集中指证
"""

import pygame
import sys
import os
import math
import random as _rand
import threading
import time

pygame.init()
pygame.font.init()

# ==================== 常量 ====================
SW, SH = 1280, 720
FPS = 60

# ---------- 逆转裁判配色 ----------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 40, 40)
DARK_RED = (160, 20, 20)
GREEN = (0, 200, 80)
DARK_GREEN = (0, 140, 50)
BLUE = (40, 100, 220)
GOLD = (255, 200, 50)
YELLOW = (255, 215, 0)
GRAY = (180, 180, 180)
DARK_GRAY = (80, 80, 80)
LIGHT_GRAY = (220, 220, 220)
ORANGE = (255, 160, 40)
PURPLE = (140, 60, 200)
TEAL = (0, 160, 160)

COURT_BG = (16, 24, 48)
COURT_BG_LIGHT = (24, 36, 64)
WOOD = (101, 67, 33)
WOOD_LIGHT = (139, 101, 60)
WOOD_DARK = (70, 45, 20)
NAMEPLATE_BG = (60, 40, 15)
NAMEPLATE_BORDER = (200, 160, 60)
DIALOG_BG = (12, 18, 36)
DIALOG_BORDER = (160, 140, 80)
PENALTY_RED = (200, 30, 30)
OBJECTION_RED = (200, 0, 0)
OBJECTION_YELLOW = (255, 255, 60)
TESTIMONY_CURRENT = (30, 45, 80)
HISTORY_BG = (18, 25, 45)
PANEL_BG = (22, 30, 52)
PANEL_BORDER = (70, 85, 120)

# ---------- 游戏状态常量 ----------
S_CASE_SELECT = "case_select"
S_BRIEF = "brief"
S_AUTO_PLAY = "auto_play"
S_PREP = "prep"         # 律师思考过渡（AUTO_PLAY → CROSS_EXAM 之间）
S_CROSS_EXAM = "cross_exam"
S_OBJECTION = "objection"
S_JUDGEMENT = "judgement"
S_RESULT = "result"
S_AI_CONFIG = "ai_config"       # AI 配置输入界面
S_AI_GENERATE = "ai_generate"   # AI 生成动画界面

# ==================== 资源路径 ====================
BASE = os.path.dirname(os.path.abspath(__file__))
COURT_DIR = os.path.join(BASE, "court")

SEAT_PATHS = {
    "judge": os.path.join(COURT_DIR, "judge.png"),
    "witness": os.path.join(COURT_DIR, "witness.png"),
    "lawyer": os.path.join(COURT_DIR, "lawyer.png"),
    "defendant": os.path.join(COURT_DIR, "defendant.png"),
}

PORTRAIT_PATHS = {
    "向日葵": os.path.join(BASE, "court_plant", "Plants", "SunFlower", "SunFlower.gif"),
    "坚果": os.path.join(BASE, "court_plant", "Plants", "WallNut", "WallNut.gif"),
    "豌豆射手": os.path.join(BASE, "court_plant", "Plants", "Peashooter", "Peashooter.gif"),
    "双发射手": os.path.join(BASE, "court_plant", "Plants", "Repeater", "Repeater.gif"),
    "辣椒检察官": os.path.join(BASE, "court_plant", "Plants", "Jalapeno", "Jalapeno.gif"),
    "樱桃炸弹": os.path.join(BASE, "court_plant", "Plants", "CherryBomb", "CherryBomb.gif"),
    "大嘴花": os.path.join(BASE, "court_plant", "Plants", "Chomper", "Chomper.gif"),
    "寒冰射手": os.path.join(BASE, "court_plant", "Plants", "SnowPea", "SnowPea.gif"),
    "路灯花": os.path.join(BASE, "court_plant", "Plants", "Plantern", "Plantern.gif"),
    "小喷菇": os.path.join(BASE, "court_plant", "Plants", "PuffShroom", "PuffShroom.gif"),
    "毁灭菇": os.path.join(BASE, "court_plant", "Plants", "DoomShroom", "DoomShroom.gif"),
    "大喷菇": os.path.join(BASE, "court_plant", "Plants", "FumeShroom", "FumeShroom.gif"),
    "忧郁菇": os.path.join(BASE, "court_plant", "Plants", "GloomShroom", "GloomShroom.gif"),
    "胆小菇": os.path.join(BASE, "court_plant", "Plants", "ScaredyShroom", "ScaredyShroom.gif"),
    "大蒜": os.path.join(BASE, "court_plant", "Plants", "Garlic", "Garlic.gif"),
    "南瓜头": os.path.join(BASE, "court_plant", "Plants", "PumpkinHead", "PumpkinHead.gif"),
    "高坚果": os.path.join(BASE, "court_plant", "Plants", "TallNut", "TallNut.gif"),
    "地刺": os.path.join(BASE, "court_plant", "Plants", "Spikeweed", "Spikeweed.gif"),
    "杨桃": os.path.join(BASE, "court_plant", "Plants", "Starfruit", "Starfruit.gif"),
    "倭瓜": os.path.join(BASE, "court_plant", "Plants", "Squash", "Squash.gif"),
}

# 立绘在席位图上的默认偏移（比例，0~1），后续可按素材微调
PORTRAIT_ANCHOR = {
    "witness": (0.5, 0.45),
    "defendant": (0.5, 0.45),
    "lawyer": (0.5, 0.45),
}


# ==================== 案件数据（硬编码） ====================
# 三阶段结构：phase1 推翻证人A → transition A改口 → phase2 推翻证人B → transition B改口
# → phase3 真相揭露（出示关键证据）→ 结局
# 每次异议不是结案，而是把案件推进到下一层！
CASES = [
    {
        "id": "case_002",
        "title": "半夜广场舞案",
        "type": "扰民案",
        "location": "草坪广场",
        "complexity": 2,
        "suspects": [
            {"name": "坚果", "role": "被告", "personality": "老实憨厚",
             "motive": "被冤枉的，只想睡觉", "portrait": "坚果"},
            {"name": "向日葵", "role": "证人一", "personality": "活泼外向",
             "motive": "想参加植物好声音", "portrait": "向日葵"},
            {"name": "双发射手", "role": "证人二", "personality": "冲动自信",
             "motive": "想参加植物好声音", "portrait": "双发射手"},
        ],
        "brief_comment": "辣椒检察官指控坚果深夜在广场跳广场舞扰民。两位证人接连作证，但证词都有致命漏洞。每次异议成功后案件不是结束，而是推向更混乱的下一层……",
        "phases": [
            # ========== Phase 1：推翻向日葵的"亲眼看见" ==========
            {
                "testimonies": [
                    {"id": "T01", "speaker": "辣椒检察官", "seat": "witness", "portrait": "辣椒检察官",
                     "text": "昨晚凌晨两点，有植物在草坪广场跳广场舞！导致附近墓碑集体失眠！",
                     "press": [
                         {"q": "有目击者吗？", "a": "当然有！第一位证人已经准备好了！", "clue": "检察官准备了两名证人"},
                     ]},
                    {"id": "T02", "speaker": "坚果", "seat": "defendant", "portrait": "坚果",
                     "text": "我昨晚九点就睡了！根本不知道什么广场舞！",
                     "press": [
                         {"q": "有人能证明吗？", "a": "我的床可以作证！但……床不会说话。", "clue": "坚果没有实物不在场证明"},
                     ]},
                    {"id": "T03", "speaker": "向日葵", "seat": "witness", "portrait": "向日葵",
                     "text": "我亲眼看见坚果在广场中央扭屁股！",
                     "press": [
                         {"q": "你当时在哪里？", "a": "当时大概凌晨两点，我在温室附近充能。", "clue": "向日葵凌晨两点在温室附近"},
                     ]},
                    {"id": "T04", "speaker": "向日葵", "seat": "witness", "portrait": "向日葵",
                     "text": "他还放着《最炫植物风》！整个广场都在震动！",
                     "press": [
                         {"q": "你确定是亲眼看到的？", "a": "当然！我看得一清二楚！", "clue": "向日葵坚称亲眼所见"},
                     ]},
                ],
                "evidence": [
                    {"id": "E01", "title": "夜间充能记录", "type": "系统记录",
                     "desc": "温室系统记录显示：向日葵于凌晨两点正在进行夜间充能，充能期间无法离开温室。"},
                    {"id": "E02", "title": "广场音响记录", "type": "监控记录",
                     "desc": "广场音响系统记录显示：昨晚播放的是《小植物》，而非向日葵所说的《最炫植物风》。"},
                ],
                "valid_objections": [
                    # 直接证据配对
                    {"testimony_id": "T03", "evidence_id": "E01"},
                    # 多证据可用：E02 也能反驳 T04（音乐记录与向日葵描述不符）
                    {"testimony_id": "T04", "evidence_id": "E02"},
                    # 基于追问线索验证：追问获得的线索也可作为异议依据
                    {"testimony_id": "T03", "required_clues": ["向日葵凌晨两点在温室附近"]},
                ],
                "judge_comment": "向日葵声称亲眼看见坚果跳舞，但充能记录清楚地显示她当时正在温室进行夜间充能，根本无法离开温室半步。这份证词存在致命矛盾！",
                # 多种改口台词，根据不同的异议证据显示不同反应
                "transitions": {
                    "E01": {
                        "speaker": "向日葵", "seat": "witness", "portrait": "向日葵",
                        "text": "好吧……我承认，我确实在温室充能……但我是从窗户看到的！虽然看不太清楚……"
                    },
                    "E02": {
                        "speaker": "向日葵", "seat": "witness", "portrait": "向日葵",
                        "text": "啊？放的是《小植物》吗？我记错了……但我确实看到有人在跳舞！只是音乐记混了……"
                    },
                    "clue": {
                        "speaker": "向日葵", "seat": "witness", "portrait": "向日葵",
                        "text": "好吧……我承认，我其实是在窗户边偷看的……根本没出去……但真的看到有植物在动！"
                    },
                    "default": {
                        "speaker": "向日葵", "seat": "witness", "portrait": "向日葵",
                        "text": "好吧……我承认，我其实是在窗户边偷看的……根本没出去……"
                    }
                },
            },
            # ========== Phase 2：推翻双发射手的"巡逻目击" ==========
            {
                "testimonies": [
                    {"id": "T05", "speaker": "辣椒检察官", "seat": "witness", "portrait": "辣椒检察官",
                     "text": "哼！就算向日葵的证词有问题，还有第二位证人！",
                     "press": [
                         {"q": "第二位证人是谁？", "a": "双发射手！他昨晚一直在广场巡逻！", "clue": "第二位证人是双发射手，在巡逻"},
                     ]},
                    {"id": "T06", "speaker": "双发射手", "seat": "witness", "portrait": "双发射手",
                     "text": "我昨晚在广场巡逻，亲眼看见坚果在广场！",
                     "press": [
                         {"q": "巡逻时间是？", "a": "从午夜十二点到凌晨三点，我一直没离开。", "clue": "双发午夜到三点在巡逻"},
                     ]},
                    {"id": "T07", "speaker": "双发射手", "seat": "witness", "portrait": "双发射手",
                     "text": "他还戴着荧光头带！太显眼了，不可能是别人！",
                     "press": [
                         {"q": "你离他有多近？", "a": "太远了，但那个荧光头带非常显眼，肯定是坚果！", "clue": "双发离得很远，只靠头带辨认"},
                     ]},
                    {"id": "T08", "speaker": "双发射手", "seat": "witness", "portrait": "双发射手",
                     "text": "整个广场只有他一个人，不可能认错！",
                     "press": [
                         {"q": "你确定只有一个人？", "a": "呃……我只注意到戴头带的那个人……其他的没看清。", "clue": "双发只注意到戴头带的人，可能有别人"},
                     ]},
                ],
                "evidence": [
                    {"id": "E01", "title": "夜间充能记录", "type": "系统记录",
                     "desc": "向日葵凌晨两点正在进行夜间充能，无法离开温室。"},
                    {"id": "E03", "title": "仓库领取记录", "type": "工作记录",
                     "desc": "昨天下午，荧光头带被豌豆射手借走，至今未归还。坚果从未领取过头带。"},
                    {"id": "E04", "title": "广场监控截图", "type": "监控记录",
                     "desc": "广场监控显示：凌晨两点，广场上有两个人影在跳舞。由于距离较远，无法辨认身份。"},
                ],
                "valid_objections": [
                    # 直接证据配对：仓库记录证明头带不是坚果的
                    {"testimony_id": "T07", "evidence_id": "E03"},
                    # 多证据可用：监控截图也能反驳（两人影不是坚果）
                    {"testimony_id": "T07", "evidence_id": "E04"},
                    # 基于追问线索验证
                    {"testimony_id": "T07", "required_clues": ["双发离得很远，只靠头带辨认"]},
                    # T08 也可以被反驳（只有一个人？监控显示两人）
                    {"testimony_id": "T08", "evidence_id": "E04"},
                ],
                "judge_comment": "双发射手声称看到坚果戴着荧光头带，但仓库领取记录显示头带昨天下午就被豌豆射手借走了，坚果从未领取过。双发射手看到的'坚果'，其实是戴着头带的其他人！",
                # 多种改口台词，根据不同的异议证据显示不同反应
                "transitions": {
                    "E03": {
                        "speaker": "双发射手", "seat": "witness", "portrait": "双发射手",
                        "text": "等等……头带是豌豆射手借走的？那我看到的确实不是坚果……我只是看到头带在发光就认错了……"
                    },
                    "E04": {
                        "speaker": "双发射手", "seat": "witness", "portrait": "双发射手",
                        "text": "两个人影？！我一直以为只有一个……原来还有别人在广场，我只注意到头带的光了……"
                    },
                    "clue": {
                        "speaker": "双发射手", "seat": "witness", "portrait": "双发射手",
                        "text": "好吧……我离得太远了，确实看不清楚……只看到荧光头带在发光，就以为是坚果……"
                    },
                    "default": {
                        "speaker": "双发射手", "seat": "witness", "portrait": "双发射手",
                        "text": "等等……好像确实戴的是头带……那个人不一定是坚果……我只看到头带在发光……"
                    }
                },
            },
            # ========== Phase 3：真相揭露 ==========
            {
                "testimonies": [
                    {"id": "T09", "speaker": "法官", "seat": "judge", "portrait": "",
                     "text": "所以，向日葵没有亲眼看见，双发射手也认错了人。那到底谁在广场跳舞？",
                     "press": [
                         {"q": "监控有没有拍到？", "a": "监控确实拍到了画面，但还没有人仔细查看过……", "clue": "广场监控有画面，尚未仔细查看"},
                     ]},
                    {"id": "T10", "speaker": "辣椒检察官", "seat": "witness", "portrait": "辣椒检察官",
                     "text": "哼！不管怎样，坚果就是最大的嫌疑人！",
                     "press": [
                         {"q": "你有证据吗？", "a": "我……我有直觉！坚果看起来就像会跳舞的植物！", "clue": "检察官只有直觉，没有实质证据"},
                     ]},
                    {"id": "T11", "speaker": "坚果", "seat": "defendant", "portrait": "坚果",
                     "text": "所以我真的是来睡觉的啊？！",
                     "press": [
                         {"q": "你真的九点就睡了吗？", "a": "是啊！我睡得可香了，还做了个好梦！", "clue": "坚果坚称自己在睡觉"},
                     ]},
                ],
                "evidence": [
                    {"id": "E01", "title": "夜间充能记录", "type": "系统记录",
                     "desc": "向日葵凌晨两点正在进行夜间充能，无法离开温室。"},
                    {"id": "E03", "title": "仓库领取记录", "type": "工作记录",
                     "desc": "荧光头带被豌豆射手借走，坚果从未领取。"},
                    {"id": "E04", "title": "广场监控截图", "type": "监控记录",
                     "desc": "广场监控显示：凌晨两点，广场上有两个人影在跳舞。放大辨认后，可见一人是向日葵（圆脸特征），另一人背着类似双发射手的双管造型。"},
                ],
                "valid_objections": [
                    # 监控截图直接反驳检察官的指控（主要路径）
                    {"testimony_id": "T10", "evidence_id": "E04"},
                    # 充能记录也能反驳（向日葵在温室，检察官的指控无依据）
                    {"testimony_id": "T10", "evidence_id": "E01"},
                    # 仓库记录反驳（坚果没头带，不可能是跳舞的人）
                    {"testimony_id": "T10", "evidence_id": "E03"},
                    # 基于追问线索验证：检察官只有直觉
                    {"testimony_id": "T10", "required_clues": ["检察官只有直觉，没有实质证据"]},
                ],
                "judge_comment": "监控清晰地显示广场上有两个人影在跳舞。放大辨认后，正是向日葵和双发射手！结合两人的改口证词，真相已经水落石出。",
                # 多种改口台词，根据不同的异议证据显示不同反应
                "transitions": {
                    "E04": {
                        "speaker": "向日葵", "seat": "witness", "portrait": "向日葵",
                        "text": "好吧……我们说实话。监控都拍到了……我们想参加植物好声音，半夜偷偷在广场练舞……怕被发现，就一起说是坚果干的……"
                    },
                    "E01": {
                        "speaker": "向日葵", "seat": "witness", "portrait": "向日葵",
                        "text": "我……我确实在温室充能……但是双发射手叫我别说实话……其实我们俩一起去广场练舞了……"
                    },
                    "E03": {
                        "speaker": "双发射手", "seat": "witness", "portrait": "双发射手",
                        "text": "好吧……头带是我借的……我戴着它去广场跳舞了……坚果根本不知道这事……"
                    },
                    "clue": {
                        "speaker": "双发射手", "seat": "witness", "portrait": "双发射手",
                        "text": "行吧行吧……检察官确实没证据……是我们俩干的，半夜去广场练舞，怕被骂就嫁祸给坚果了……"
                    },
                    "default": {
                        "speaker": "向日葵", "seat": "witness", "portrait": "向日葵",
                        "text": "好吧……我们说实话。我们想参加植物好声音，半夜偷偷在广场练舞……怕被发现，就一起说是坚果干的……"
                    }
                },
            },
        ],
        "truth": "向日葵和双发射手为了参加植物好声音，半夜偷偷在草坪广场练舞。她们怕被发现，便串通好一起嫁祸给正在熟睡的坚果。坚果从始至终都在睡觉，完全无辜。",
    },
]

# ==================== 案件运行时修复 ====================
# 角色名映射：修复 AI 常见的角色名变体
_NAME_FIX_MAP = {
    "坚果墙": "坚果",
    "太阳花": "向日葵",
    "土豆雷": "毁灭菇",
    "检察官": "辣椒",
    "法官": "倭瓜",
    "律师": "辣椒",
    "全体": "向日葵",
    "R1证人": "",
    "R2证人": "",
    "R3证人": "",
}

# 有效的角色名集合（用于校验）
_VALID_PORTRAIT_NAMES = set(PORTRAIT_PATHS.keys()) | {"辣椒", "倭瓜", "辣椒检察官"}


def _fix_speaker_name(name: str, case_speakers: set = None) -> str:
    """修复 speaker 名称，映射到有效的角色名。"""
    if not name:
        return name
    # 直接映射（处理已知变体如坚果墙→坚果）
    if name in _NAME_FIX_MAP:
        return _NAME_FIX_MAP[name]
    # 已经在有效集合中
    if name in _VALID_PORTRAIT_NAMES:
        return name
    # 尝试 case 中已有的 speaker（仅完全匹配，避免模糊匹配导致错误）
    if case_speakers and name in case_speakers:
        return name
    return name


def _fix_case_data(case: dict) -> dict:
    """
    运行时修复案件数据中的常见问题：
    1. 修复角色名变体（坚果墙→坚果，太阳花→向日葵等）
    2. 修复 portrait 映射
    3. 修复分支台词中的无效 speaker
    """
    if not isinstance(case, dict):
        return case

    # 收集案件中所有有效的 speaker 名
    case_speakers = set()
    for p in case.get("phases", []):
        for t in p.get("testimonies", []):
            if t.get("speaker"):
                case_speakers.add(t["speaker"])
    for s in case.get("suspects", []):
        if s.get("name"):
            case_speakers.add(s["name"])

    # 修复 suspects 中的 portrait
    for s in case.get("suspects", []):
        if "portrait" in s and s["portrait"] not in _VALID_PORTRAIT_NAMES:
            fixed = _fix_speaker_name(s["portrait"], case_speakers)
            if fixed in _VALID_PORTRAIT_NAMES:
                s["portrait"] = fixed

    # 修复 phases 中的数据
    for phase in case.get("phases", []):
        # 修复 testimonies
        for t in phase.get("testimonies", []):
            if t.get("speaker"):
                orig = t["speaker"]
                fixed = _fix_speaker_name(orig, case_speakers)
                if fixed != orig:
                    t["speaker"] = fixed
                    print(f"[案件修复] speaker: {orig} -> {fixed}")
            # 修复 portrait
            if t.get("portrait") and t["portrait"] not in _VALID_PORTRAIT_NAMES:
                fixed = _fix_speaker_name(t["portrait"], case_speakers)
                if fixed in _VALID_PORTRAIT_NAMES:
                    t["portrait"] = fixed
                else:
                    # 使用 speaker 作为 portrait 回退
                    if t.get("speaker") in _VALID_PORTRAIT_NAMES:
                        t["portrait"] = t["speaker"]

        # 修复 transition
        tran = phase.get("transition", {})
        if tran.get("speaker"):
            orig = tran["speaker"]
            fixed = _fix_speaker_name(orig, case_speakers)
            if fixed != orig:
                tran["speaker"] = fixed
                print(f"[案件修复] transition speaker: {orig} -> {fixed}")
        if tran.get("portrait") and tran["portrait"] not in _VALID_PORTRAIT_NAMES:
            fixed = _fix_speaker_name(tran["portrait"], case_speakers)
            if fixed in _VALID_PORTRAIT_NAMES:
                tran["portrait"] = fixed
            elif tran.get("speaker") in _VALID_PORTRAIT_NAMES:
                tran["portrait"] = tran["speaker"]

    # 修复 _meta.branches 中的 speaker
    branches = case.get("_meta", {}).get("branches", {})
    for branch_name, lines in branches.items():
        if not isinstance(lines, list):
            continue
        for line in lines:
            if line.get("speaker"):
                orig = line["speaker"]
                fixed = _fix_speaker_name(orig, case_speakers)
                if fixed != orig:
                    line["speaker"] = fixed
                    print(f"[案件修复] branch {branch_name} speaker: {orig} -> {fixed}")

    return case


def _validate_case_playable(case: dict) -> tuple:
    """
    检查案件是否可玩，返回 (is_playable, issues)。
    在 _fix_case_data 之后调用。
    """
    issues = []

    # 1. 检查每轮是否有矛盾证词
    for i, phase in enumerate(case.get("phases", [])):
        testimonies = phase.get("testimonies", [])
        contra_count = sum(1 for t in testimonies if t.get("is_contradiction"))
        if contra_count == 0:
            issues.append(f"第{i+1}轮没有矛盾证词")
        elif contra_count > 2:
            issues.append(f"第{i+1}轮矛盾证词过多({contra_count}个)")

    # 2. 检查每轮是否有 valid_objection 指向矛盾证词
    for i, phase in enumerate(case.get("phases", [])):
        testimonies = phase.get("testimonies", [])
        objections = phase.get("valid_objections", [])
        contra_ids = {t["id"] for t in testimonies if t.get("is_contradiction")}
        mapped_contra = set()
        for obj in objections:
            if obj.get("testimony_id") in contra_ids:
                mapped_contra.add(obj["testimony_id"])
        if contra_ids and not mapped_contra:
            issues.append(f"第{i+1}轮矛盾证词没有对应的异议映射")

    # 3. 检查所有 speaker 是否有效
    all_speakers = set()
    for phase in case.get("phases", []):
        for t in phase.get("testimonies", []):
            if t.get("speaker"):
                all_speakers.add(t["speaker"])
    invalid = all_speakers - _VALID_PORTRAIT_NAMES
    if invalid:
        issues.append(f"无效角色名: {', '.join(invalid)}")

    # 4. 检查证据和证词 ID 在 objections 中是否存在
    for i, phase in enumerate(case.get("phases", [])):
        t_ids = {t["id"] for t in phase.get("testimonies", [])}
        e_ids = {e["id"] for e in phase.get("evidence", [])}
        for obj in phase.get("valid_objections", []):
            if obj.get("testimony_id") not in t_ids:
                issues.append(f"第{i+1}轮 objection 指向不存在的证词: {obj.get('testimony_id')}")
            if obj.get("evidence_id") not in e_ids:
                issues.append(f"第{i+1}轮 objection 指向不存在的证据: {obj.get('evidence_id')}")

    # 5. 检查 branches 是否完整
    branches = case.get("_meta", {}).get("branches", {})
    num_rounds = case.get("_meta", {}).get("num_rounds", 2)
    required = ["r1_success", "r1_fail", "r2_success", "r2_fail"]
    if num_rounds >= 3:
        required.extend(["r3_success", "r3_fail"])
    for key in required:
        if key not in branches or not branches[key]:
            issues.append(f"分支台词缺失: {key}")

    return len(issues) == 0, issues


# ==================== 加载外部案件 ====================
# 必须在 _fix_case_data 和 _validate_case_playable 定义之后执行

# 1. 兼容旧格式：加载单个 generated_case.json
_GEN_CASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "generated_case.json")
if os.path.exists(_GEN_CASE_PATH):
    try:
        import json as _json
        with open(_GEN_CASE_PATH, "r", encoding="utf-8") as _f:
            _gen = _json.load(_f)
        if isinstance(_gen, dict) and "title" in _gen:
            _fixed = _fix_case_data(_gen)
            _playable, _issues = _validate_case_playable(_fixed)
            if _playable:
                CASES.append(_fixed)
            else:
                print(f"加载AI案件失败: 案件不可玩 - {_issues}")
        elif isinstance(_gen, list):
            for _item in _gen:
                if isinstance(_item, dict) and "title" in _item:
                    _fixed = _fix_case_data(_item)
                    _playable, _issues = _validate_case_playable(_fixed)
                    if _playable:
                        CASES.append(_fixed)
                    else:
                        print(f"加载AI案件失败: 案件不可玩 - {_issues}")
    except Exception as _e:
        print(f"加载AI案件失败: {_e}")

# 2. 新格式：从 cases/ 目录加载所有案件文件（不覆盖，独立存储）
_CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cases")
if os.path.exists(_CASES_DIR):
    try:
        import json as _json
        # 收集已加载的案件 id，用于去重
        _loaded_ids = {c.get("id") for c in CASES}
        for _fname in sorted(os.listdir(_CASES_DIR)):
            if not _fname.endswith(".json"):
                continue
            _fpath = os.path.join(_CASES_DIR, _fname)
            try:
                with open(_fpath, "r", encoding="utf-8") as _f:
                    _case_data = _json.load(_f)
                if isinstance(_case_data, dict) and "title" in _case_data:
                    _fixed = _fix_case_data(_case_data)
                    # 去重：跳过已加载的案件
                    if _fixed.get("id") in _loaded_ids:
                        continue
                    _playable, _issues = _validate_case_playable(_fixed)
                    if _playable:
                        CASES.append(_fixed)
                        _loaded_ids.add(_fixed.get("id"))
                    else:
                        print(f"加载案件文件失败 {_fname}: 案件不可玩 - {_issues}")
                elif isinstance(_case_data, list):
                    for _item in _case_data:
                        if isinstance(_item, dict) and "title" in _item:
                            _fixed = _fix_case_data(_item)
                            # 去重：跳过已加载的案件
                            if _fixed.get("id") in _loaded_ids:
                                continue
                            _playable, _issues = _validate_case_playable(_fixed)
                            if _playable:
                                CASES.append(_fixed)
                                _loaded_ids.add(_fixed.get("id"))
                            else:
                                print(f"加载案件文件失败 {_fname}: 案件不可玩 - {_issues}")
            except Exception as _e2:
                print(f"加载案件文件失败 {_fname}: {_e2}")
    except Exception as _e:
        print(f"扫描案件目录失败: {_e}")


# ==================== 工具函数 ====================
def load_image(path, fallback_size=(100, 100), fallback_color=(60, 60, 80), fallback_text=""):
    """加载图片，失败时返回带文字的占位图"""
    if os.path.exists(path):
        try:
            img = pygame.image.load(path)
            if path.lower().endswith('.png'):
                return img.convert_alpha()
            return img.convert()
        except Exception:
            pass
    surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
    pygame.draw.rect(surf, fallback_color, (0, 0, *fallback_size), border_radius=8)
    pygame.draw.rect(surf, (120, 120, 140), (0, 0, *fallback_size), 2, border_radius=8)
    if fallback_text:
        f = pygame.font.SysFont('Microsoft YaHei', min(18, fallback_size[1] // 3))
        t = f.render(fallback_text, True, (180, 180, 200))
        surf.blit(t, t.get_rect(center=(fallback_size[0] // 2, fallback_size[1] // 2)))
    return surf


def fit_image(image, max_w, max_h):
    """等比缩放图片到指定最大尺寸内（contain 模式，允许放大）"""
    w, h = image.get_size()
    if w == 0 or h == 0:
        return image
    scale = min(max_w / w, max_h / h)
    if scale == 1.0:
        return image
    return pygame.transform.smoothscale(image, (int(w * scale), int(h * scale)))


def fit_cover(image, target_w, target_h):
    """等比缩放图片铺满目标区域，居中裁切（cover 模式）"""
    w, h = image.get_size()
    if w == 0 or h == 0:
        return image
    scale = max(target_w / w, target_h / h)
    nw, nh = int(w * scale), int(h * scale)
    if nw < 1: nw = 1
    if nh < 1: nh = 1
    scaled = pygame.transform.smoothscale(image, (nw, nh))
    # 居中裁切
    cx = max(0, (nw - target_w) // 2)
    cy = max(0, (nh - target_h) // 2)
    return scaled.subsurface(pygame.Rect(cx, cy, min(target_w, nw), min(target_h, nh)))


def render_text_wrapped(surface, text, font, color, rect, line_spacing=5):
    """在指定矩形区域内自动换行渲染文本，返回已用高度"""
    x, y, max_w, max_h = rect
    lh = font.get_linesize()
    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    cy = y
    for ln in lines:
        if cy + lh > y + max_h:
            break
        surface.blit(font.render(ln, True, color), (x, cy))
        cy += lh + line_spacing
    return cy - y


def draw_rr(surface, color, rect, radius=10):
    """绘制圆角矩形填充"""
    x, y, w, h = rect if isinstance(rect, (list, tuple)) else (rect.x, rect.y, rect.w, rect.h)
    if w <= 0 or h <= 0:
        return
    pygame.draw.rect(surface, color, (x, y, w, h), border_radius=min(radius, w // 2, h // 2))


def draw_rr_outline(surface, color, rect, radius=10, thickness=2):
    """绘制圆角矩形边框"""
    x, y, w, h = rect if isinstance(rect, (list, tuple)) else (rect.x, rect.y, rect.w, rect.h)
    if w <= 0 or h <= 0:
        return
    pygame.draw.rect(surface, color, (x, y, w, h), thickness,
                     border_radius=min(radius, w // 2, h // 2))


def draw_gradient(surface, c1, c2, rect):
    """绘制垂直渐变"""
    x, y, w, h = rect if isinstance(rect, (list, tuple)) else (rect.x, rect.y, rect.w, rect.h)
    if h <= 0 or w <= 0:
        return
    for i in range(h):
        r = i / max(h - 1, 1)
        c = tuple(int(c1[j] + (c2[j] - c1[j]) * r) for j in range(3))
        pygame.draw.line(surface, c, (x, y + i), (x + w, y + i))


def draw_glow_border(surface, rect, color, thickness=2, glow_radius=8):
    """绘制霓虹发光边框"""
    if not isinstance(rect, pygame.Rect):
        rect = pygame.Rect(rect)
    for i in range(glow_radius, 0, -1):
        alpha = int(35 * (1 - i / glow_radius))
        glow_rect = rect.inflate(i * 2, i * 2)
        pygame.draw.rect(surface, (*color, alpha), glow_rect, 1, border_radius=6)
    pygame.draw.rect(surface, (*color, 220), rect, thickness, border_radius=6)


def draw_hex_grid(surface, color, spacing=36):
    """绘制六边形蜂窝网格"""
    h = spacing * 0.866
    for row in range(-1, SH // int(h) + 2):
        for col in range(-1, SW // spacing + 2):
            x = col * spacing + (row % 2) * spacing * 0.5
            y = row * h
            pts = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                pts.append((x + spacing * 0.42 * math.cos(angle),
                            y + spacing * 0.42 * math.sin(angle)))
            pygame.draw.polygon(surface, color, pts, 2)


def draw_tech_corner(surface, x, y, w, h, color, size=12):
    """绘制科技风L形角标"""
    # 左上
    pygame.draw.line(surface, color, (x, y + size), (x, y), 2)
    pygame.draw.line(surface, color, (x, y), (x + size, y), 2)
    # 右上
    pygame.draw.line(surface, color, (x + w - size, y), (x + w, y), 2)
    pygame.draw.line(surface, color, (x + w, y), (x + w, y + size), 2)
    # 左下
    pygame.draw.line(surface, color, (x, y + h - size), (x, y + h), 2)
    pygame.draw.line(surface, color, (x, y + h), (x + size, y + h), 2)
    # 右下
    pygame.draw.line(surface, color, (x + w - size, y + h), (x + w, y + h), 2)
    pygame.draw.line(surface, color, (x + w, y + h), (x + w, y + h - size), 2)


# ==================== 游戏主类 ====================
class CourtGame:
    """逆转裁判风格法庭游戏 — 三阶段流程"""

    # ---------- 布局常量 ----------
    DIALOG_H = 140
    FLOAT_PAD = 16

    def __init__(self):
        self.screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption('AI植物法庭')
        self.clock = pygame.time.Clock()

        # ---- 字体 ----
        self.f_huge = pygame.font.SysFont('Microsoft YaHei', 52, bold=True)
        self.f_large = pygame.font.SysFont('Microsoft YaHei', 34, bold=True)
        self.f_med = pygame.font.SysFont('Microsoft YaHei', 24, bold=True)
        self.f_small = pygame.font.SysFont('Microsoft YaHei', 20)
        self.f_tiny = pygame.font.SysFont('Microsoft YaHei', 16)
        self.f_dialog = pygame.font.SysFont('Microsoft YaHei', 26)
        self.f_name = pygame.font.SysFont('Microsoft YaHei', 22, bold=True)

        # ---- 加载席位图 ----
        self.seat_imgs = {}
        for key, path in SEAT_PATHS.items():
            self.seat_imgs[key] = load_image(
                path, fallback_size=(850, 450), fallback_color=(35, 45, 65),
                fallback_text={"judge": "法官席", "witness": "证人席",
                               "lawyer": "律师席", "defendant": "被告席"}.get(key, key))

        # ---- 加载植物立绘 ----
        self.portraits = {}
        for name, path in PORTRAIT_PATHS.items():
            img = load_image(path, fallback_size=(150, 150), fallback_color=(50, 70, 50),
                             fallback_text=name[:2])
            # 向日葵 GIF 包含上下两帧，只取上半部分
            if name == "向日葵":
                w, h = img.get_size()
                if h > w * 1.5:  # 高度明显大于宽度，可能是双帧
                    half_h = h // 2
                    img = img.subsurface(pygame.Rect(0, 0, w, half_h))
            self.portraits[name] = img

        # ---- 预渲染异议文字 ----
        try:
            af = pygame.font.SysFont('Microsoft YaHei', 140, bold=True)
        except Exception:
            af = pygame.font.SysFont('SimSun', 140, bold=True)
        self._obj_yellow = af.render("异议あり!", True, OBJECTION_YELLOW)
        self._obj_white = af.render("异议あり!", True, WHITE)

        # ---- 预计算胜利星星 ----
        _rand.seed(42)
        self.win_stars = [(_rand.randint(0, SW), _rand.randint(0, SH),
                           _rand.randint(1, 3)) for _ in range(60)]
        _rand.seed()

        # ---- 音效 ----
        self.snd_objection = None
        try:
            snd_path = os.path.join(BASE, "sounds", "court", "yiyi.mp3")
            if os.path.exists(snd_path):
                self.snd_objection = pygame.mixer.Sound(snd_path)
                self.snd_objection.set_volume(0.8)
        except Exception:
            pass

        # ---- 背景音乐 ----
        self.bgm_path = os.path.join(BASE, "sounds", "court", "court.mp3")
        self.menu_bgm_path = os.path.join(BASE, "music", "space.mp3")
        self.bgm_playing = False
        self.menu_bgm_playing = False

        # ---- 游戏状态 ----
        self._reset_game()

    # ==================== 背景音乐 ====================
    def _play_bgm(self):
        """开始播放法庭背景音乐"""
        try:
            if os.path.exists(self.bgm_path):
                # 如果当前在播放菜单音乐，先停止
                if self.menu_bgm_playing:
                    pygame.mixer.music.stop()
                    self.menu_bgm_playing = False
                if not self.bgm_playing:
                    pygame.mixer.music.load(self.bgm_path)
                    pygame.mixer.music.set_volume(0.3)
                    pygame.mixer.music.play(-1)
                    self.bgm_playing = True
        except Exception:
            pass

    def _stop_bgm(self):
        """停止背景音乐"""
        try:
            if self.bgm_playing:
                pygame.mixer.music.stop()
                self.bgm_playing = False
        except Exception:
            pass

    def _play_menu_bgm(self):
        """播放菜单/配置界面背景音乐"""
        try:
            if os.path.exists(self.menu_bgm_path) and not self.menu_bgm_playing:
                pygame.mixer.music.load(self.menu_bgm_path)
                pygame.mixer.music.set_volume(0.4)
                pygame.mixer.music.play(-1)
                self.menu_bgm_playing = True
        except Exception:
            pass

    def _stop_menu_bgm(self):
        """停止菜单背景音乐"""
        try:
            if self.menu_bgm_playing:
                pygame.mixer.music.stop()
                self.menu_bgm_playing = False
        except Exception:
            pass

    def _apply_gen_result(self):
        """应用AI生成结果，切换到简报"""
        if not self.ai_gen_case:
            return
        # 停止菜单BGM和配乐，恢复法庭BGM
        self._stop_menu_bgm()
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        # 清理预览特效资源
        if hasattr(self, '_preview_fx'):
            del self._preview_fx
        new_case = self.ai_gen_case
        new_case["id"] = f"ai_{len(CASES):03d}"
        CASES.append(new_case)
        self.case = new_case
        self.life = 3
        self.current_phase = 0
        # 清除回退缓存
        self._case_transitions_backup = None
        self._case_transition_backup = None
        self._load_phase(0)
        self.state = S_BRIEF
        self._play_bgm()

    # ==================== 状态重置 ====================
    def _reset_game(self):
        self.state = S_CASE_SELECT
        self.case = None
        self.life = 3
        self.running = True
        self.return_to_menu = False
        # 停止所有音乐并重置标记
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.menu_bgm_playing = False
        self.bgm_playing = False

        # 清理 AI 生成状态（防止残留引用）
        self._ai_shared = None
        self._gen_dna_show = False
        self._gen_dna_timer = 0.0
        self._gen_dna_alpha = 0
        self._gen_logs = []
        self._gen_log_idx = 0
        self._gen_log_timer = 0.0
        self._gen_target_progress = 0.0
        self._gen_display_progress = 0.0
        self._gen_start_time = 0.0
        self._gen_eval_text = ""
        self.ai_gen_case = None
        self.ai_gen_error = None
        self.ai_gen_done = False

        # 双阶段
        self.current_phase = 0

        # 打字机
        self.tw_chars = 0
        self.tw_timer = 0.0
        self.tw_speed = 0.04
        self.tw_done = False
        self.tw_text = ""
        self.tw_speaker = ""
        self.tw_seat = ""
        self.tw_portrait_key = ""

        # AUTO_PLAY
        self.auto_idx = 0
        self.auto_wait = 0.0
        self.auto_delay = 1.5

        # CROSS_EXAM（笔记本）
        self.note_scroll = 0
        self.press_done = {}  # tid -> bool
        self.show_notebook = False  # 笔记本默认收起，手动打开
        self.show_evidence = False
        self.show_profiles = False
        self.show_clues = False
        self.evidence_sel = None

        # 双面板滑入动画
        self.cross_anim_active = False
        self.cross_anim_timer = 0.0
        self.cross_anim_dur = 0.45
        self.cross_anim_nb_dx = 0   # 笔记本 x 偏移
        self.cross_anim_rp_dx = 0   # 右侧面板 x 偏移

        # OBJECTION（直接证据选择）
        self.obj_tid = None
        self.obj_eid = None
        self.obj_evidence_used = None  # 记录异议成功时使用的证据ID
        self.obj_reason = ""           # 记录异议成功时的理由

        # 异议动画
        self.oa_active = False
        self.oa_timer = 0.0
        self.oa_dur = 1.8
        self.oa_shake = 0

        # 判决/结果
        self.judge_ok = False
        self.result_type = None
        self.blink = 0.0

        # AI 生成相关
        self.ai_prefs = {
            "style": "搞笑",
            "difficulty": "normal",
            "defendant": "",
            "crime_type": "",
            "template": "",
            "real_criminal": "",
            "theme": "",
            "use_locked_pool": True,
        }
        self.ai_pref_text = ""      # 偏好自由输入
        self.ai_input = ""          # 主题关键词输入
        self.ai_input_active = False  # "pref" / "theme" / False
        self.ime_composing = ""     # IME 组字中内容
        self.ai_gen_step = ""      # 当前步骤名
        self.ai_gen_msg = ""       # 当前步骤消息
        self.ai_gen_done = False   # 生成完成标志
        self.ai_gen_case = None    # 生成结果
        self.ai_gen_error = None   # 错误信息
        self.ai_gen_dots = 0       # 加载动画点数
        self.ai_gen_timer = 0.0   # 动画计时器
        self.perf_mode = False    # 性能模式开关
        self.perf_switch_anim = 0.0  # 滑块动画位置 0.0~1.0
        # AI 配置界面背景粒子
        _rand.seed(123)
        self.ai_bg_particles = []
        for i in range(35):
            self.ai_bg_particles.append({
                "x": _rand.randint(0, SW),
                "y": _rand.randint(0, SH),
                "vx": _rand.uniform(-0.3, 0.3),
                "vy": _rand.uniform(-0.2, 0.2),
                "size": _rand.randint(2, 5),
                "alpha": _rand.randint(40, 100),
                "phase": _rand.uniform(0, 6.28),
                "color": (200, 180, 100) if i % 2 == 0 else (100, 180, 200),
            })
        _rand.seed()

    def _start_case(self, idx):
        # 清除回退缓存
        self._case_transitions_backup = None
        self._case_transition_backup = None
        self.case = CASES[idx]
        self.life = 3
        self.current_phase = 0
        self._load_phase(0)
        self.state = S_BRIEF
        # 播放背景音乐
        self._play_bgm()

    def _start_ai_generate(self):
        """启动线程化AI生成，不退出游戏"""
        import json
        from threading import Thread
        from preview_fx import PreviewFXManager, T_DISTORT

        # 同步输入框内容到偏好
        self.ai_prefs["theme"] = self.ai_input

        # ---- AI 免责声明提示 ----
        self.ai_gen_step = "Notice"
        self.ai_gen_msg = "案件内容全部由 AI 生成，可能存在不稳定、不合理或重复的情况，请谅解"
        self.ai_gen_done = False
        self.ai_gen_error = None
        self.ai_gen_case = None

        # 显示提示界面（阻塞 2.5 秒）
        notice_start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - notice_start < 2500:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    self.return_to_menu = True
                    self._stop_bgm()
                    self._stop_menu_bgm()
                    return
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.state = S_AI_CONFIG
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    break
            else:
                # 绘制提示界面
                self.screen.fill(COURT_BG)
                ticks = pygame.time.get_ticks()
                t_sec = ticks / 1000.0
                # 背景粒子
                for p in self.ai_bg_particles[:20]:
                    pulse = 0.5 + 0.5 * math.sin(t_sec * 2 + p["phase"])
                    a = int(p["alpha"] * pulse)
                    c = p["color"]
                    pygame.draw.circle(self.screen, (c[0], c[1], c[2], a), (int(p["x"]), int(p["y"])), p["size"])
                # 提示面板
                panel = pygame.Rect(SW // 2 - 350, SH // 2 - 100, 700, 200)
                panel_surf = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
                panel_surf.fill((20, 30, 50, 220))
                self.screen.blit(panel_surf, (panel.x, panel.y))
                draw_rr_outline(self.screen, GOLD, panel, 12, 3)
                # 标题
                title = self.f_large.render("提示", True, GOLD)
                self.screen.blit(title, title.get_rect(center=(SW // 2, panel.y + 40)))
                # 提示文字
                notice_text = "案件内容全部由 AI 生成，可能存在不稳定、不合理或重复的情况"
                notice_surf = self.f_med.render(notice_text, True, (200, 210, 230))
                self.screen.blit(notice_surf, notice_surf.get_rect(center=(SW // 2, panel.y + 95)))
                # 副提示
                sub = self.f_small.render("点击鼠标或按任意键跳过", True, (100, 110, 130))
                self.screen.blit(sub, sub.get_rect(center=(SW // 2, panel.y + 150)))
                pygame.display.flip()
                pygame.time.delay(16)
                continue
            break

        # 创建线程共享状态
        self._ai_shared = {
            "step": "Init",
            "msg": "初始化中...",
            "done": False,
            "error": None,
            "case": None,
            "logs": [],
        }

        # 重置生成状态
        self.ai_gen_step = "Init"
        self.ai_gen_msg = "初始化中..."
        self.ai_gen_done = False
        self.ai_gen_error = None
        self.ai_gen_case = None

        # ---- 创建预览特效管理器 ----
        self._stop_bgm()  # 暂停法庭BGM
        fonts = {
            "f_huge": self.f_huge,
            "f_large": self.f_large,
            "f_med": self.f_med,
            "f_small": self.f_small,
            "f_tiny": self.f_tiny,
            "f_tiny_cn": self.f_tiny,
        }
        self._preview_fx = PreviewFXManager(fonts, base_path=BASE, perf_mode=self.perf_mode)

        # 加载并播放配乐 star.mp3
        self._preview_music_start = 0.0
        star_path = os.path.join(BASE, "music", "star.mp3")
        if os.path.exists(star_path):
            try:
                pygame.mixer.music.load(star_path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play()
                # 标记菜单BGM已被配乐取代，避免后续 _stop_menu_bgm() 误停 star.mp3
                self.menu_bgm_playing = False
                self._preview_music_start = time.time()
            except Exception as e:
                print(f"[警告] 无法加载 star.mp3: {e}")
                self._preview_music_start = time.time()
        else:
            self._preview_music_start = time.time()

        # 进度回调（由子线程调用）
        def _progress_cb(step, msg):
            self._ai_shared["step"] = step
            self._ai_shared["msg"] = msg
            import time as _time
            self._ai_shared.setdefault("logs", []).append({
                "time": _time.time(),
                "step": step,
                "msg": msg,
            })

        # 子线程：导入 maker7 并生成案件
        def _thread_fn():
            try:
                ai_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ai")
                if ai_dir not in sys.path:
                    sys.path.insert(0, ai_dir)
                from maker7 import generate_case, save_case, save_case_to_dir

                case = generate_case(self.ai_prefs, progress_cb=_progress_cb)
                self._ai_shared["case"] = case
                self._ai_shared["done"] = True

                # 保存到 cases/ 目录（独立文件，不覆盖）
                try:
                    save_case_to_dir(case)
                except Exception:
                    pass
                # 兼容旧格式：同时保存到 generated_case.json
                try:
                    out_path = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "..", "generated_case.json"
                    )
                    save_case(case, out_path)
                except Exception:
                    pass
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                print(f"[AI生成线程异常] {e}\n{tb}")
                self._ai_shared["error"] = f"{e}\n{tb}"
                self._ai_shared["done"] = True

        t = Thread(target=_thread_fn, daemon=True)
        t.start()

        # 停止菜单BGM，切换到生成动画状态
        self._stop_menu_bgm()
        self.state = S_AI_GENERATE

    def _load_phase(self, phase_idx):
        """加载指定阶段的数据到 case"""
        self.current_phase = phase_idx
        phases = self.case.get("phases", [])
        if not phases or phase_idx >= len(phases):
            return
        p = phases[phase_idx]
        # 将阶段数据合并到 case 顶层，供绘制代码直接读取
        self.case["testimonies"] = p["testimonies"]
        self.case["evidence"] = p["evidence"]
        self.case["valid_objections"] = p.get("valid_objections", [])
        self.case["phase_judge_comment"] = p.get("judge_comment", "")
        
        # 首次调用时保存案件级回退（兼容旧格式：case顶层有transition/transitions）
        if not hasattr(self, '_case_transitions_backup') or self._case_transitions_backup is None:
            self._case_transitions_backup = self.case.get("transitions", {})
        if not hasattr(self, '_case_transition_backup') or self._case_transition_backup is None:
            self._case_transition_backup = self.case.get("transition", {})
        
        # 优先使用阶段级，缺失时回退到案件级
        phase_tran = p.get("transition", {})
        self.case["_transition"] = phase_tran if phase_tran else self._case_transition_backup
        
        phase_trans = p.get("transitions", {})
        self.case["transitions"] = phase_trans if phase_trans else self._case_transitions_backup
        # 重置阶段内状态
        self.press_done = {t["id"]: False for t in self.case["testimonies"]}
        self.note_scroll = 0
        self.show_notebook = True   # 进入推理阶段自动打开
        self.show_evidence = False
        self.show_profiles = False
        self.show_clues = False
        self.evidence_sel = None
        self.obj_tid = None
        self.obj_eid = None
        self.obj_evidence_used = None
        self.obj_reason = ""

    # ==================== 主循环 ====================
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    self.return_to_menu = True
                    self._stop_bgm()
                    self._stop_menu_bgm()
                    break
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    # AI_CONFIG 输入框激活时：取消输入，不退回选关
                    if self.state == S_AI_CONFIG and self.ai_input_active:
                        self.ai_input_active = False
                        self.ime_composing = ""
                        pygame.key.stop_text_input()
                    elif self.state == S_CASE_SELECT:
                        self.running = False
                        self.return_to_menu = True
                        self._stop_bgm()
                        self._stop_menu_bgm()
                    elif self.state not in (S_AUTO_PLAY,):
                        # 从游戏状态退回选关：停止BGM并清理AI线程引用
                        self._stop_bgm()
                        self._stop_menu_bgm()
                        if self.state == S_AI_GENERATE:
                            self._ai_shared = None  # 防止后台线程写入过期引用
                        self.state = S_CASE_SELECT
                        self.case = None
                self._handle(ev)
            self._update(dt)
            self._draw()
            pygame.display.flip()
        return self.return_to_menu

    # ==================== 事件分发 ====================
    def _handle(self, ev):
        m = {
            S_CASE_SELECT: self._ev_case_sel,
            S_BRIEF: self._ev_brief,
            S_AUTO_PLAY: self._ev_auto,
            S_PREP: self._ev_prep,
            S_CROSS_EXAM: self._ev_cross,
            S_OBJECTION: self._ev_obj,
            S_JUDGEMENT: self._ev_judge,
            S_RESULT: self._ev_result,
            S_AI_CONFIG: self._ev_ai_config,
            S_AI_GENERATE: self._ev_ai_generate,
        }.get(self.state)
        if m:
            m(ev)

    # ==================== 更新 ====================
    def _update(self, dt):
        self.blink += dt

        # === 菜单BGM状态管理 ===
        if self.state in (S_CASE_SELECT, S_AI_CONFIG):
            self._play_menu_bgm()
        else:
            self._stop_menu_bgm()

        # === AI生成 — 线程轮询（仅在线程活跃时同步状态） ===
        if self.state == S_AI_GENERATE and hasattr(self, '_ai_shared') and self._ai_shared:
            self.ai_gen_step = self._ai_shared["step"]
            self.ai_gen_msg = self._ai_shared["msg"]

            # 同步真实日志到预览特效系统
            if hasattr(self, '_preview_fx') and self._preview_fx:
                real_logs = self._ai_shared.get("logs", [])
                if len(real_logs) > len(self._preview_fx.fx.fake_logs):
                    # 标记使用真实日志，禁用假日志生成
                    self._preview_fx._has_real_logs = True
                    # 将新日志追加到预览特效
                    for log in real_logs[len(self._preview_fx.fx.fake_logs):]:
                        self._preview_fx.fx.fake_logs.append(log)

            if self._ai_shared["done"]:
                if self._ai_shared["error"]:
                    self.ai_gen_error = self._ai_shared["error"]
                    self.ai_gen_done = True
                elif self._ai_shared["case"]:
                    # AI完成，保存结果（无论当前处于哪个阶段）
                    self.ai_gen_case = self._ai_shared["case"]
                    # 将案件数据传递给预览特效管理器，用于显示案件DNA
                    if hasattr(self, '_preview_fx') and self._preview_fx:
                        self._preview_fx.case_data = self.ai_gen_case
                    # 如果还在生成阶段（phase=0）且音乐未到失真点，继续等待
                    # 否则由阶段转换逻辑处理
                self._ai_shared = None

        # === AI生成 — 音乐时间更新（独立于 _ai_shared 状态） ===
        if self.state == S_AI_GENERATE and hasattr(self, '_preview_fx') and self._preview_fx:
            if pygame.mixer.music.get_busy():
                self._preview_fx.music_time = time.time() - self._preview_music_start
            else:
                self._preview_fx.music_time += dt

        # === AI生成 — 预览特效动画 ===
        if self.state == S_AI_GENERATE and hasattr(self, '_preview_fx') and self._preview_fx:
            from preview_fx import update_preview, T_DISTORT as _T_DISTORT
            update_preview(self._preview_fx, dt)

            # 如果AI已完成且音乐到达失真点，手动触发失真
            if self.ai_gen_case and self._preview_fx.phase == 0 and self._preview_fx.music_time >= _T_DISTORT:
                self._preview_fx.phase = 1
                self._preview_fx.phase_timer = 0.0
                self._preview_fx.fx.distort_phase = 1
                self._preview_fx.fx.distort_timer = 0.0
                self._preview_fx._play_distort_sfx()

            # 如果AI已完成但音乐还没到80s，强制在80s触发失真
            if self.ai_gen_case and self._preview_fx.phase == 0 and self._preview_fx.music_time < _T_DISTORT:
                # 检查是否生成完成超过2秒（防止卡住太久）
                pass  # 正常等待音乐时间线

            # 进入卡片阶段后自动应用结果
            if self._preview_fx.phase == 3 and self._preview_fx.fx.dna_timer > 3.0:
                if not hasattr(self, '_preview_auto_applied') or not self._preview_auto_applied:
                    self._preview_auto_applied = True

        # 打字机
        if not self.tw_done and self.tw_text:
            self.tw_timer += dt
            self.tw_chars = min(int(self.tw_timer / self.tw_speed), len(self.tw_text))
            if self.tw_chars >= len(self.tw_text):
                self.tw_done = True

        # AUTO_PLAY 自动推进
        if self.state == S_AUTO_PLAY and self.tw_done:
            self.auto_wait += dt
            if self.auto_wait >= self.auto_delay:
                self.auto_idx += 1
                if self.auto_idx >= len(self.case["testimonies"]):
                    # 切换到律师思考过渡阶段
                    self.state = S_PREP
                    self._tw_reset("让我仔细分析这些证词，找出其中的破绽...", "律师", "lawyer", "")
                else:
                    self._begin_auto()

        # 异议动画
        if self.oa_active:
            self.oa_timer += dt
            self.oa_shake = int(10 * max(0, 1 - self.oa_timer / 0.4))
            if self.oa_timer >= self.oa_dur:
                self.oa_active = False
                self.oa_timer = 0
                self.oa_shake = 0
                self._resolve_obj()

        # 双面板滑入动画
        if self.cross_anim_active:
            self.cross_anim_timer += dt
            t = min(self.cross_anim_timer / self.cross_anim_dur, 1.0)
            e = 1.0 - (1.0 - t) ** 3  # ease-out cubic
            self.cross_anim_nb_dx = int(-640 * (1.0 - e))
            self.cross_anim_rp_dx = int(592 * (1.0 - e))
            if t >= 1.0:
                self.cross_anim_active = False
                self.cross_anim_nb_dx = 0
                self.cross_anim_rp_dx = 0

    # ==================== 打字机辅助 ====================
    def _tw_reset(self, text, speaker="", seat="", portrait_key=""):
        self.tw_text = text
        self.tw_chars = 0
        self.tw_timer = 0.0
        self.tw_done = False
        self.tw_speaker = speaker
        self.tw_seat = seat
        self.tw_portrait_key = portrait_key

    def _tw_skip(self):
        self.tw_chars = len(self.tw_text)
        self.tw_done = True

    def _begin_auto(self):
        t = self.case["testimonies"][self.auto_idx]
        self._tw_reset(t["text"], t["speaker"], t["seat"], t.get("portrait", ""))
        self.auto_wait = 0.0

    # ==================== 数据查询 ====================
    def _testi(self, tid):
        if not self.case:
            return None
        for t in self.case["testimonies"]:
            if t["id"] == tid:
                return t
        return None

    def _suspect(self, name):
        if not self.case:
            return None
        for s in self.case["suspects"]:
            if s["name"] == name:
                return s
        return None

    # ==================== 异议判定 ====================
    def _resolve_obj(self):
        """
        检查异议是否有效。
        每条 valid_objection 格式: {testimony_id, evidence_id, reason}
        """
        # 注：异议音效已在 _ev_obj 中点击"提出异议"时立即播放，此处不再重复播放

        valid_list = self.case.get("valid_objections", [])
        ok = False
        self.obj_evidence_used = None
        self.obj_reason = ""

        for vo in valid_list:
            if (self.obj_tid == vo.get("testimony_id")
                    and self.obj_eid == vo.get("evidence_id")):
                ok = True
                self.obj_evidence_used = self.obj_eid
                self.obj_reason = vo.get("reason", "")
                break

        self.judge_ok = ok
        if not ok:
            self.life -= 1
        self.state = S_JUDGEMENT

    # ============================================================
    #   事件处理 — 各状态
    # ============================================================

    # ---- 关卡选择 ----
    def _ev_case_sel(self, ev):
        # 鼠标滚轮滚动
        if ev.type == pygame.MOUSEWHEEL:
            if not hasattr(self, '_case_scroll'):
                self._case_scroll = 0
            self._case_scroll -= ev.y * 40
            return

        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return
        mx, my = ev.pos
        scroll = getattr(self, '_case_scroll', 0)
        list_top = 105
        card_ch, card_gap = 130, 10

        # 案件卡片点击（考虑滚动偏移）
        for i in range(len(CASES)):
            r = pygame.Rect(
                (SW - 620) // 2,
                list_top + i * (card_ch + card_gap) - scroll,
                620, card_ch
            )
            if r.collidepoint(mx, my) and list_top <= my <= SH - 140:
                self._start_case(i)
                return

        # AI 生成按钮（固定底部）
        ai_r = pygame.Rect((SW - 620) // 2, SH - 125, 620, 75)
        if ai_r.collidepoint(mx, my):
            self.state = S_AI_CONFIG
            return
        # 返回 — 文字链接区域
        back_rect = pygame.Rect(50, SH - 32, 140, 25)
        if back_rect.collidepoint(mx, my):
            self.running = False
            self.return_to_menu = True
            self._stop_bgm()
            self._stop_menu_bgm()

    # ---- 案件简报 ----
    def _ev_brief(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            btn = pygame.Rect(SW // 2 - 140, SH - 80, 280, 52)
            if btn.collidepoint(*ev.pos):
                self.state = S_AUTO_PLAY
                self.auto_idx = 0
                self._begin_auto()

    # ---- 自动播放 ----
    def _ev_auto(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if not self.tw_done:
                self._tw_skip()
            else:
                self.auto_wait = self.auto_delay

    # ---- 律师思考过渡 ----
    def _ev_prep(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if not self.tw_done:
                self._tw_skip()
            else:
                # 台词结束，进入推理阶段
                self.state = S_CROSS_EXAM
                self.note_scroll = 0
                self.cross_anim_active = True
                self.cross_anim_timer = 0.0
                self.cross_anim_nb_dx = -640
                self.cross_anim_rp_dx = 592

    # ---- 自由追问（笔记本模式） ----
    def _ev_cross(self, ev):
        if self.oa_active:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                self.oa_timer = self.oa_dur
            return

        # 档案覆盖层优先
        if self.show_profiles:
            self._ev_profiles_panel(ev)
            return

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            mx, my = ev.pos

            # 证词列表中的按钮
            for i, t in enumerate(self.case["testimonies"]):
                # 追问按钮
                press_r = self._press_btn_r(i)
                if press_r and press_r.collidepoint(mx, my) and not self.press_done.get(t["id"], False):
                    self.press_done[t["id"]] = True
                    return
                # 异议按钮
                obj_r = self._obj_btn_r(i)
                if obj_r and obj_r.collidepoint(mx, my):
                    self.obj_tid = t["id"]
                    self.obj_eid = None
                    self.state = S_OBJECTION
                    return

            # 右侧证据列表点击
            rp = self._right_panel_r()
            if rp.collidepoint(mx, my):
                for i, evd in enumerate(self.case["evidence"]):
                    ir = self._evidence_item_r(i)
                    if ir and ir.collidepoint(mx, my):
                        self.evidence_sel = i if self.evidence_sel != i else None
                        return

            # 档案小按钮
            if self._profiles_mini_btn_r().collidepoint(mx, my):
                self.show_profiles = True
                return

        if ev.type == pygame.MOUSEWHEEL:
            lr = self._notebook_r()
            if lr.collidepoint(*pygame.mouse.get_pos()):
                mx_s = max(0, len(self.case["testimonies"]) * 240 - lr.height + 20)  # 200改为240
                self.note_scroll = max(0, min(mx_s, self.note_scroll - ev.y * 40))

    def _ev_evidence_panel(self, ev):
        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return
        mx, my = ev.pos
        panel = self._overlay_r()
        if not panel.collidepoint(mx, my):
            return
        # 点击证据项
        for i, e in enumerate(self.case["evidence"]):
            ir = pygame.Rect(panel.left + 20, panel.top + 70 + i * 52, 340, 44)
            if ir.collidepoint(mx, my):
                self.evidence_sel = i
                return

    def _ev_profiles_panel(self, ev):
        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return
        mx, my = ev.pos
        panel = self._overlay_r()
        if not panel.collidepoint(mx, my):
            return

    def _ev_clues_panel(self, ev):
        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return
        mx, my = ev.pos
        panel = self._overlay_r()
        if not panel.collidepoint(mx, my):
            return

    # ---- 集中指证（直接证据选择） ----
    def _ev_obj(self, ev):
        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return
        mx, my = ev.pos
        # 与 _dr_obj_overlay 使用相同的面板区域
        pw, ph = 520, 480
        px = (SW - pw) // 2
        py = (SH - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # 选证据（正方形网格）
        grid_x = panel.left + 24
        grid_y = panel.top + 136
        sq = 90
        for i, e in enumerate(self.case["evidence"]):
            col = i % 2
            row = i // 2
            ix = grid_x + col * (sq + 14)
            iy = grid_y + row * (sq + 14)
            ir = pygame.Rect(ix, iy, sq, sq)
            if ir.collidepoint(mx, my):
                self.obj_eid = e["id"]

        # 提出异议
        ob = pygame.Rect(panel.centerx + 20, panel.bottom - 55, 150, 42)
        if ob.collidepoint(mx, my) and self.obj_eid:
            self.state = S_CROSS_EXAM
            self.oa_active = True
            self.oa_timer = 0
            # 立即播放异议音效，不要等动画结束
            if self.snd_objection:
                self.snd_objection.play()

        # 取消
        cb = pygame.Rect(panel.centerx - 170, panel.bottom - 55, 150, 42)
        if cb.collidepoint(mx, my):
            self.state = S_CROSS_EXAM
            self.obj_tid = None
            self.obj_eid = None

    # ---- 判决 ----
    def _ev_judge(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            btn = pygame.Rect(SW // 2 - 130, SH - 80, 260, 50)
            if btn.collidepoint(*ev.pos):
                if self.judge_ok:
                    # 检查是否还有下一阶段
                    phases = self.case.get("phases", [])
                    if self.current_phase + 1 < len(phases):
                        # 进入下一阶段
                        self._load_phase(self.current_phase + 1)
                        self.state = S_AUTO_PLAY
                        self.auto_idx = 0
                        self._begin_auto()
                    else:
                        # 最终胜利
                        self.result_type = "win"
                        self.state = S_RESULT
                elif self.life <= 0:
                    self.result_type = "lose"
                    self.state = S_RESULT
                else:
                    # 失败，返回当前阶段继续推理
                    self.state = S_CROSS_EXAM
                    self.obj_tid = None
                    self.obj_eid = None

    # ---- 结果 ----
    def _ev_result(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            mx, my = ev.pos
            if pygame.Rect(SW // 2 - 260, SH - 80, 230, 50).collidepoint(mx, my):
                self._reset_game()
            elif pygame.Rect(SW // 2 + 30, SH - 80, 230, 50).collidepoint(mx, my):
                self.running = False
                self.return_to_menu = True
                self._stop_bgm()
                self._stop_menu_bgm()

    # ============================================================
    #   布局矩形（悬浮窗）
    # ============================================================
    def _case_card_r(self, i):
        cw, ch = 600, 130
        return pygame.Rect((SW - cw) // 2, 110 + i * (ch + 10), cw, ch)

    def _notebook_r(self):
        """笔记本主面板 — 左侧（支持滑入动画偏移）"""
        w = 640
        h = SH - self.FLOAT_PAD * 2
        dx = self.cross_anim_nb_dx if self.cross_anim_active else 0
        return pygame.Rect(self.FLOAT_PAD + dx, self.FLOAT_PAD, w, h)

    def _right_panel_r(self):
        """右侧信息面板 — 证据+线索（支持滑入动画偏移）"""
        # 右侧面板固定宽度的正常位置
        normal_x = self.FLOAT_PAD + 640 + 16  # = 16 + 640 + 16 = 672
        normal_w = SW - normal_x - self.FLOAT_PAD  # = 1280 - 672 - 16 = 592
        dx = self.cross_anim_rp_dx if self.cross_anim_active else 0
        return pygame.Rect(normal_x + dx, self.FLOAT_PAD, normal_w, SH - self.FLOAT_PAD * 2)

    def _testimony_item_r(self, i):
        """证词条目 — 在笔记本内"""
        nr = self._notebook_r()
        y = nr.y + 40 + i * 240 - self.note_scroll  # 间距从200增加到240
        if y + 225 < nr.y or y > nr.bottom:  # 高度从185增加到225
            return None
        return pygame.Rect(nr.x + 10, y, nr.width - 20, 225)  # 高度从185增加到225

    def _press_btn_r(self, i):
        """追问按钮 — 在证词条目内"""
        tr = self._testimony_item_r(i)
        if tr is None:
            return None
        return pygame.Rect(tr.right - 170, tr.bottom - 40, 75, 30)  # 位置上移，高度增加

    def _obj_btn_r(self, i):
        """异议按钮 — 在证词条目内"""
        tr = self._testimony_item_r(i)
        if tr is None:
            return None
        return pygame.Rect(tr.right - 85, tr.bottom - 40, 75, 30)  # 位置上移，高度增加

    def _profiles_mini_btn_r(self):
        """档案小按钮 — 右下角"""
        return pygame.Rect(SW - 130, SH - 48, 110, 40)

    def _notebook_toggle_btn_r(self):
        """笔记本开关按钮 — 底部居中"""
        return pygame.Rect(SW // 2 - 120, SH - 48, 240, 40)

    def _evidence_item_r(self, i):
        """证据正方形 — 在右侧面板网格内"""
        rp = self._right_panel_r()
        grid_x = rp.x + 14
        grid_y = rp.y + 46
        sq = 108
        col = i % 2
        row = i // 2
        ix = grid_x + col * (sq + 10)
        iy = grid_y + row * (sq + 10)
        return pygame.Rect(ix, iy, sq, sq)

    def _overlay_r(self):
        return pygame.Rect(140, 50, SW - 280, SH - 100)

    # ============================================================
    #   绘制总入口
    # ============================================================
    def _draw(self):
        sx = sy = 0
        if self.oa_shake > 0:
            sx = _rand.randint(-self.oa_shake, self.oa_shake)
            sy = _rand.randint(-self.oa_shake, self.oa_shake)

        drawer = {
            S_CASE_SELECT: self._dr_case_sel,
            S_BRIEF: self._dr_brief,
            S_AUTO_PLAY: self._dr_auto,
            S_PREP: self._dr_prep,
            S_CROSS_EXAM: self._dr_cross,
            S_OBJECTION: self._dr_cross,   # 覆盖层在 cross 上
            S_JUDGEMENT: self._dr_judgement,
            S_RESULT: self._dr_result,
            S_AI_CONFIG: self._dr_ai_config,
            S_AI_GENERATE: self._dr_ai_generate,
        }.get(self.state)

        if drawer:
            if sx or sy:
                tmp = pygame.Surface((SW, SH))
                drawer(tmp)
                self.screen.fill(BLACK)
                self.screen.blit(tmp, (sx, sy))
            else:
                drawer(self.screen)

        if self.oa_active:
            self._dr_oa_anim(self.screen)

    # ============================================================
    #   通用悬浮窗绘制
    # ============================================================
    def _dr_float_panel(self, s, rect, alpha=200, bg_color=(16, 24, 48),
                         border_color=(70, 85, 120), radius=8, border_w=2):
        """绘制半透明悬浮面板，支持 Rect 或 tuple (x, y, w, h)"""
        if not isinstance(rect, pygame.Rect):
            rect = pygame.Rect(rect)
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        r, g, b = bg_color
        pygame.draw.rect(panel, (r, g, b, alpha),
                         (0, 0, rect.width, rect.height), border_radius=radius)
        pygame.draw.rect(panel, (*border_color, min(255, alpha + 55)),
                         (0, 0, rect.width, rect.height), width=border_w, border_radius=radius)
        s.blit(panel, rect.topleft)

    # ============================================================
    #   绘制 — 关卡选择
    # ============================================================
    def _dr_case_sel(self, s):
        ticks = pygame.time.get_ticks()
        t_sec = ticks / 1000.0
        mouse = pygame.mouse.get_pos()

        # ---- 1. 背景 ----
        s.fill((6, 10, 22))
        # 六边形网格背景
        hex_r = 30
        for row in range(-1, SH // hex_r + 2):
            for col in range(-1, int(SW / (hex_r * 1.7)) + 2):
                hx = col * hex_r * 1.73 + (row % 2) * hex_r * 0.865
                hy = row * hex_r * 1.5
                pts = []
                for a in range(6):
                    angle = math.radians(a * 60 - 30)
                    pts.append((hx + hex_r * 0.5 * math.cos(angle), hy + hex_r * 0.5 * math.sin(angle)))
                pygame.draw.polygon(s, (12, 18, 32), pts, 1)
        # 动态数据流横线（顶部）
        for i in range(5):
            dy = 5 + i * 3
            dx = int((ticks * (0.3 + i * 0.1) + i * 200) % (SW + 200)) - 100
            dw = int(60 + 40 * math.sin(t_sec * 2 + i))
            da = int(30 + 20 * math.sin(t_sec * 3 + i * 0.7))
            line_surf = pygame.Surface((dw, 1), pygame.SRCALPHA)
            line_surf.fill((60, 100, 180, da))
            s.blit(line_surf, (dx, dy))
        # 背景粒子 + 连线网络
        particle_count = 12 if self.perf_mode else 30
        pts = []
        for i, p in enumerate(self.ai_bg_particles[:particle_count]):
            p["x"] += p["vx"] * 0.6
            p["y"] += p["vy"] * 0.6
            if p["x"] < 0: p["x"] = SW
            if p["x"] > SW: p["x"] = 0
            if p["y"] < 0: p["y"] = SH
            if p["y"] > SH: p["y"] = 0
            pulse = 0.5 + 0.5 * math.sin(t_sec * 1.5 + p["phase"])
            a = int(p["alpha"] * pulse * 0.7)
            cold_c = (100, 150, 200)
            pygame.draw.circle(s, (cold_c[0], cold_c[1], cold_c[2], a), (int(p["x"]), int(p["y"])), p["size"])
            pts.append((p["x"], p["y"], a))
        # 粒子连线
        if not self.perf_mode:
            for i in range(len(pts)):
                for j in range(i + 1, min(i + 4, len(pts))):
                    dx = pts[i][0] - pts[j][0]
                    dy = pts[i][1] - pts[j][1]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < 120:
                        la = int(min(pts[i][2], pts[j][2]) * (1 - dist / 120) * 0.3)
                        if la > 5:
                            pygame.draw.line(s, (80, 120, 180, la), (int(pts[i][0]), int(pts[i][1])),
                                           (int(pts[j][0]), int(pts[j][1])), 1)

        # ---- 2. 标题 — 脉冲光效 + 扫描线 + 故障抖动 ----
        title_text = "AI 植物法庭"
        title_surf = self.f_huge.render(title_text, True, (180, 210, 255))
        title_rect = title_surf.get_rect(center=(SW // 2, 48))
        # 多层发光
        for layer in range(3):
            la = int(40 - layer * 12 + 25 * math.sin(t_sec * 3 + layer * 0.5))
            ls = self.f_huge.render(title_text, True, (180, 210, 255))
            ls.set_alpha(max(0, la))
            offset = layer * 2
            s.blit(ls, title_rect.move(0, offset + 1))
        # 故障效果（偶尔偏移）
        glitch = math.sin(t_sec * 8) > 0.85
        if glitch:
            s.blit(title_surf, title_rect.move(_rand.randint(-2, 2), 0))
        s.blit(title_surf, title_rect)
        # 扫描线
        scan_w = int(220 + 60 * math.sin(t_sec * 1.5))
        scan_x = SW // 2 - scan_w // 2
        pygame.draw.line(s, (120, 160, 220), (scan_x, 78), (scan_x + scan_w, 78), 2)
        # 两侧旋转装饰
        dc = (120, 150, 200)
        for idx, dx in enumerate([-260, 260]):
            cx = SW // 2 + dx
            rot = t_sec * (1.5 if idx == 0 else -1.5)
            for arm in range(4):
                angle = rot + arm * math.pi / 2
                x1 = cx + 6 * math.cos(angle)
                y1 = 48 + 6 * math.sin(angle)
                x2 = cx + 14 * math.cos(angle)
                y2 = 48 + 14 * math.sin(angle)
                pygame.draw.line(s, dc, (x1, y1), (x2, y2), 2)
            pygame.draw.circle(s, dc, (cx, 48), 4)
        s.blit(self.f_small.render("~ 逆转裁判风格法庭推理 ~", True, (80, 110, 160)),
               self.f_small.render("~ 逆转裁判风格法庭推理 ~", True, (80, 110, 160))
               .get_rect(center=(SW // 2, 88)))

        # ---- 3. 案件列表（可滚动）----
        card_ch = 120
        card_gap = 14
        list_top = 110
        list_bottom = SH - 140
        list_h = list_bottom - list_top
        total_h = len(CASES) * (card_ch + card_gap)
        if not hasattr(self, '_case_scroll'):
            self._case_scroll = 0
        max_scroll = max(0, total_h - list_h)
        self._case_scroll = max(0, min(self._case_scroll, max_scroll))

        clip_rect = pygame.Rect(0, list_top, SW, list_h)
        s.set_clip(clip_rect)

        # 难度颜色
        diff_colors = {1: (60, 200, 100), 2: (255, 200, 50), 3: (255, 60, 80)}
        diff_names = {1: "简单", 2: "普通", 3: "困难"}

        for i, c in enumerate(CASES):
            r = pygame.Rect(
                (SW - 640) // 2,
                list_top + i * (card_ch + card_gap) - self._case_scroll,
                640, card_ch
            )
            if r.bottom < list_top or r.top > list_bottom:
                continue
            hov = r.collidepoint(mouse)
            # 卡片3D倾斜效果
            tilt_x = 0
            if hov:
                mx_rel = (mouse[0] - r.centerx) / (r.w / 2)
                tilt_x = max(-3, min(3, mx_rel * 3))
            r = r.move(int(tilt_x), -3 if hov else 0)
            # 阴影层
            if hov:
                shadow = pygame.Surface((r.w + 8, r.h + 8), pygame.SRCALPHA)
                draw_rr(shadow, (0, 0, 0, 40), pygame.Rect(4, 4, r.w, r.h), 10)
                s.blit(shadow, (r.x - 4, r.y - 4))
            # 玻璃拟态底色
            card_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            card_surf.fill((14, 22, 42, 220))
            s.blit(card_surf, (r.x, r.y))
            # 流光边框（更亮）
            flow = 0.5 + 0.5 * math.sin(t_sec * 1.5 + i * 0.5)
            br = int(80 + 50 * flow) if hov else 50
            border_c = (br, int(100 + 40 * flow), int(180 + 40 * flow))
            draw_rr_outline(s, border_c, r, 10, 2)
            # 左侧难度色条（加宽发光）
            diff_c = diff_colors.get(c["complexity"], (100, 100, 100))
            bar_rect = pygame.Rect(r.x, r.y, 5, r.h)
            draw_rr(s, diff_c, bar_rect, 0)
            # 色条顶部脉冲
            bar_pulse = int(8 + 4 * math.sin(t_sec * 3 + i))
            bp_surf = pygame.Surface((bar_pulse * 2 + 2, bar_pulse * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(bp_surf, (*diff_c, 60), (bar_pulse + 1, bar_pulse + 1), bar_pulse)
            s.blit(bp_surf, (r.x - bar_pulse, r.y - bar_pulse + r.h // 2))
            if hov:
                glow_bar = pygame.Surface((12, r.h), pygame.SRCALPHA)
                glow_bar.fill((*diff_c, 50))
                s.blit(glow_bar, (r.x - 3, r.y))
            # 顶部横条 + 数据流装饰
            draw_gradient(s, (30, 55, 100), (14, 24, 45), (r.x + 5, r.y, r.w - 5, 28))
            pygame.draw.line(s, (50, 85, 150), (r.x + 5, r.y + 28), (r.right, r.y + 28), 1)
            # 数据流动点
            dot_pos = int((ticks * 0.05 + i * 80) % (r.w - 20))
            pygame.draw.circle(s, (100, 160, 240, 120), (r.x + 10 + dot_pos, r.y + 14), 2)
            # 标题
            s.blit(self.f_med.render(c["title"], True, (180, 210, 250)),
                   self.f_med.render(c["title"], True, (180, 210, 250))
                   .get_rect(center=(r.centerx, r.y + 15)))
            # 信息行
            info_y = r.y + 38
            info_items = [
                ("类型", c["type"]),
                ("地点", c["location"]),
                ("难度", diff_names.get(c["complexity"], "未知")),
            ]
            info_x = r.x + 24
            for lbl, val in info_items:
                s.blit(self.f_tiny.render(lbl + ":", True, (70, 100, 150)), (info_x, info_y))
                info_x += self.f_tiny.size(lbl + ":")[0] + 4
                s.blit(self.f_tiny.render(val, True, (180, 210, 255)), (info_x, info_y))
                info_x += self.f_tiny.size(val)[0] + 28
            # 案件编号角标
            case_num = f"#{i + 1:02d}"
            s.blit(self.f_tiny.render(case_num, True, (50, 70, 110)), (r.right - 50, r.y + 32))
            # 开庭按钮
            btn = pygame.Rect(r.right - 120, r.bottom - 38, 100, 32)
            bh = btn.collidepoint(mouse)
            if bh:
                glow_s = pygame.Surface((btn.w + 12, btn.h + 8), pygame.SRCALPHA)
                draw_rr(glow_s, (60, 120, 240, 60), pygame.Rect(0, 0, btn.w + 12, btn.h + 8), 8)
                s.blit(glow_s, (btn.x - 6, btn.y - 4))
            draw_rr(s, (50, 100, 220) if bh else (30, 60, 140), btn, 8)
            draw_rr_outline(s, (120, 180, 255) if bh else (60, 100, 180), btn, 8, 2)
            s.blit(self.f_small.render("开庭", True, (220, 240, 255)),
                   self.f_small.render("开庭", True, (220, 240, 255)).get_rect(center=btn.center))
            # 箭头（动态）
            arrow_c = (160, 200, 255) if bh else (80, 120, 180)
            ax = btn.right - 16
            ay = btn.centery
            arrow_off = int(2 * math.sin(t_sec * 4))
            pygame.draw.polygon(s, arrow_c, [(ax + arrow_off, ay - 4), (ax + 6 + arrow_off, ay), (ax + arrow_off, ay + 4)])

        s.set_clip(None)

        # 滚动条
        if total_h > list_h:
            sb_h = max(30, int(list_h * list_h / total_h))
            sb_y = list_top + int(self._case_scroll / max_scroll * (list_h - sb_h)) if max_scroll > 0 else list_top
            sb_x = (SW + 640) // 2 + 14
            draw_rr(s, (18, 28, 48), (sb_x, list_top, 5, list_h), 3)
            draw_rr(s, (80, 130, 200), (sb_x, sb_y, 5, sb_h), 3)

        # ---- 4. AI 生成按钮（更炫酷）----
        ai_y = SH - 128
        ai_r = pygame.Rect((SW - 640) // 2, ai_y, 640, 78)
        ai_hov = ai_r.collidepoint(mouse)
        # 多层脉冲发光
        for ring in range(2):
            pulse_b = 0.5 + 0.5 * math.sin(t_sec * (2.5 - ring * 0.5) + ring * math.pi)
            pb_a = int(25 + 20 * pulse_b)
            offset = (ring + 1) * 6
            pb_surf = pygame.Surface((ai_r.w + offset * 2, ai_r.h + offset * 2), pygame.SRCALPHA)
            draw_rr(pb_surf, (80, 150, 240, pb_a), pygame.Rect(0, 0, ai_r.w + offset * 2, ai_r.h + offset * 2), 14)
            s.blit(pb_surf, (ai_r.x - offset, ai_r.y - offset))
        # 卡片本体
        ai_surf = pygame.Surface((ai_r.w, ai_r.h), pygame.SRCALPHA)
        ai_surf.fill((16, 30, 60, 230))
        s.blit(ai_surf, (ai_r.x, ai_r.y))
        draw_rr_outline(s, (120, 180, 255) if ai_hov else (60, 110, 200), ai_r, 12, 2)
        # 内部扫描线
        scan_y = int(8 + 4 * math.sin(t_sec * 2))
        pygame.draw.line(s, (60, 100, 180, 40), (ai_r.x + 20, ai_r.y + scan_y), (ai_r.right - 20, ai_r.y + scan_y), 1)
        s.blit(self.f_med.render("AI 生成案件", True, (170, 210, 255) if ai_hov else (130, 180, 240)),
               self.f_med.render("AI 生成案件", True, (170, 210, 255) if ai_hov else (130, 180, 240))
               .get_rect(center=(ai_r.centerx, ai_r.y + 28)))
        s.blit(self.f_tiny.render("由 AI 实时生成全新案件 · 无限可能", True, (100, 140, 200) if ai_hov else (60, 90, 160)),
               self.f_tiny.render("由 AI 实时生成全新案件 · 无限可能", True, (100, 140, 200) if ai_hov else (60, 90, 160))
               .get_rect(center=(ai_r.centerx, ai_r.y + 55)))

        # ---- 5. 返回 — 文字链接 ----
        back_text = "< 返回主菜单"
        back_x = 50
        back_y = SH - 32
        back_hov = pygame.Rect(back_x, back_y, 140, 25).collidepoint(mouse)
        back_c = (180, 190, 210) if back_hov else (90, 100, 130)
        s.blit(self.f_small.render(back_text, True, back_c), (back_x, back_y))
        if back_hov:
            tw = self.f_small.size(back_text)[0]
            pygame.draw.line(s, back_c, (back_x, back_y + 22), (back_x + tw, back_y + 22), 1)

        # ---- 6. 底部状态栏 ----
        pygame.draw.line(s, (30, 45, 70), (40, SH - 42), (SW - 40, SH - 42), 1)
        s.blit(self.f_tiny.render("AI 司法档案系统 v2.0", True, (60, 75, 100)), (50, SH - 34))
        hint_txt = self.f_tiny.render("滚轮浏览  |  点击开庭  |  AI生成新案件", True, (60, 75, 100))
        s.blit(hint_txt, hint_txt.get_rect(right=SW - 50, top=SH - 34))

    # ============================================================
    #   事件 — AI 生成动画界面（仅处理错误时返回）
    # ============================================================
    def _ev_ai_generate(self, ev):
        # 使用 preview_fx 的阶段系统
        _fx = getattr(self, '_preview_fx', None)
        _phase = _fx.phase if _fx else 0

        # 失真阶段（phase=1）和重生阶段（phase=2）不响应任何输入
        if _phase in (1, 2):
            return

        # 卡片阶段（phase=3）：点击/按键进入游戏
        if _phase == 3 and self.ai_gen_case:
            if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1) or \
               (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE)):
                self._apply_gen_result()
                return

        # 生成阶段（phase=0）且AI已完成：也可以点击进入（跳过动画）
        if _phase == 0 and self.ai_gen_case:
            if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1) or \
               (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE)):
                self._apply_gen_result()
                return

        # 错误时处理返回按钮（线程状态由 _update 统一轮询）
        if self.ai_gen_error and ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            mx, my = ev.pos
            # 错误时返回按钮
            pw, ph = 600, 300
            py = (SH - ph) // 2
            back_btn = pygame.Rect(SW // 2 - 80, py + 270, 160, 40)
            if back_btn.collidepoint(mx, my):
                self.state = S_CASE_SELECT
                return
        if self.ai_gen_error and ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.state = S_CASE_SELECT

    # ============================================================
    #   绘制 — AI 生成动画界面
    # ============================================================
    def _dr_ai_generate(self, s):
        from preview_fx import draw_preview
        if hasattr(self, '_preview_fx') and self._preview_fx:
            draw_preview(self._preview_fx, s)
        else:
            s.fill((2, 4, 8))


    # ============================================================
    #   绘制 — 案件简报
    # ============================================================
    def _dr_brief(self, s):
        c = self.case
        # ---- 法官席全屏背景 ----
        judge_img = self.seat_imgs.get("judge")
        if judge_img:
            try:
                bg = fit_cover(judge_img, SW, SH)
                s.blit(bg, (0, 0))
            except Exception:
                s.fill(COURT_BG)
        else:
            s.fill(COURT_BG)
        # 半透明遮罩
        dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        s.blit(dim, (0, 0))

        # ---- 案件标题（顶部金色面板） ----
        title_r = pygame.Rect((SW - 600) // 2, 30, 600, 56)
        self._dr_float_panel(s, title_r, alpha=230, bg_color=(50, 40, 0),
                              border_color=GOLD, radius=8, border_w=3)
        s.blit(self.f_huge.render(c["title"], True, GOLD),
               self.f_huge.render(c["title"], True, GOLD)
               .get_rect(center=title_r.center))

        # ---- 法官宣读案宗对话框 ----
        dialog_r = pygame.Rect(80, 110, SW - 160, 440)
        self._dr_float_panel(s, dialog_r, alpha=220, bg_color=(12, 18, 36),
                              border_color=(160, 140, 80), radius=8, border_w=2)
        # 法官名牌
        np_w, np_h = 140, 30
        self._dr_float_panel(s, (dialog_r.x + 20, dialog_r.y + 12, np_w, np_h),
                              alpha=220, bg_color=(60, 40, 15), border_color=(200, 160, 60), radius=3)
        s.blit(self.f_name.render("法官", True, WHITE),
               self.f_name.render("法官", True, WHITE)
               .get_rect(center=(dialog_r.x + 20 + np_w // 2, dialog_r.y + 12 + np_h // 2)))

        # 案宗内容（使用换行防止溢出）
        ty = dialog_r.y + 52
        content_w = dialog_r.width - 60
        # 案件基本信息
        info_text = f'本次庭审审理的是「{c["type"]}」案件。案发地点：{c["location"]}。'
        ty += render_text_wrapped(s, info_text, self.f_dialog, WHITE,
                                  (dialog_r.x + 30, ty, content_w, 60), line_spacing=4)
        ty += 4

        # 被告
        defendant = c.get("suspects", [{}])[0].get("name", c.get("title", ""))
        ty += render_text_wrapped(s, f'被告：{defendant}。', self.f_dialog, LIGHT_GRAY,
                                  (dialog_r.x + 30, ty, content_w, 40), line_spacing=4)
        ty += 4

        # 嫌疑人（换行防止名字过多溢出）
        suspects = c.get("suspects", [])
        if suspects:
            names = "、".join(su["name"] for su in suspects)
            ty += render_text_wrapped(s, f'涉案嫌疑人：{names}。', self.f_dialog, LIGHT_GRAY,
                                      (dialog_r.x + 30, ty, content_w, 60), line_spacing=4)
            ty += 4

        # 案件概述（动态计算剩余高度）
        brief = c.get("brief_comment", "")
        if brief:
            pygame.draw.line(s, PANEL_BORDER,
                             (dialog_r.x + 30, ty), (dialog_r.right - 30, ty), 1)
            ty += 8
            s.blit(self.f_small.render("案件概述：", True, ORANGE), (dialog_r.x + 30, ty))
            ty += 22
            remaining_h = dialog_r.bottom - ty - 40  # 底部留 40px
            if remaining_h > 40:
                render_text_wrapped(s, brief, self.f_dialog, LIGHT_GRAY,
                                    (dialog_r.x + 30, ty, content_w, remaining_h), line_spacing=6)

        # 底部提示
        s.blit(self.f_small.render("——现在开庭——", True, GRAY),
               self.f_small.render("——现在开庭——", True, GRAY)
               .get_rect(center=(dialog_r.centerx, dialog_r.bottom - 30)))

        # 开庭按钮
        btn = pygame.Rect(SW // 2 - 140, SH - 80, 280, 52)
        mouse = pygame.mouse.get_pos()
        hov = btn.collidepoint(mouse)
        draw_rr(s, (180, 30, 30) if hov else OBJECTION_RED, btn, 6)
        draw_rr_outline(s, NAMEPLATE_BORDER, btn, 6, 2)
        s.blit(self.f_large.render("开 庭", True, WHITE),
               self.f_large.render("开 庭", True, WHITE).get_rect(center=btn.center))

    # ============================================================
    #   绘制 — 自动播放
    # ============================================================
    def _dr_auto(self, s):
        self._dr_scene(s, self.tw_seat, self.tw_portrait_key,
                        self.tw_speaker, self.tw_text[:self.tw_chars])
        # 悬浮进度条（右上角生命值下方）
        total = len(self.case["testimonies"])
        pr = pygame.Rect(SW - 150, 56, 130, 28)
        self._dr_float_panel(s, pr, alpha=180, bg_color=(16, 24, 48),
                              border_color=(70, 85, 120), radius=4)
        s.blit(self.f_tiny.render(f'证词 {self.auto_idx + 1}/{total}', True, GRAY),
               self.f_tiny.render(f'证词 {self.auto_idx + 1}/{total}', True, GRAY)
               .get_rect(center=pr.center))

    # ---- 律师思考过渡 ----
    def _dr_prep(self, s):
        self._dr_scene(s, "lawyer", "", "律师", self.tw_text[:self.tw_chars])

    # ============================================================
    #   分镜场景 — 席位图全屏 + 悬浮对话框
    # ============================================================
    def _dr_scene(self, s, seat_type, portrait_key, speaker, shown_text):
        # ---- 席位背景铺满全屏 ----
        seat_img = self.seat_imgs.get(seat_type)
        if seat_img:
            try:
                bg = fit_cover(seat_img, SW, SH)
                s.blit(bg, (0, 0))
            except Exception:
                s.fill(COURT_BG)
        else:
            s.fill(COURT_BG)

        # ---- 立绘叠加（居中偏左） ----
        # 法官席背景本身就是法官形象，不需要叠加植物立绘
        if seat_type != "judge" and portrait_key and portrait_key in self.portraits:
            pimg = self.portraits[portrait_key]
            pmax_w = int(SW * 0.196)
            pmax_h = int(SH * 0.35)
            pscaled = fit_image(pimg, pmax_w, pmax_h)
            anchor = PORTRAIT_ANCHOR.get(seat_type, (0.5, 0.45))
            px = int(SW * anchor[0]) - pscaled.get_width() // 2
            py = int(SH * anchor[1]) - pscaled.get_height() // 2
            s.blit(pscaled, (px, py))

        # ---- 悬浮名牌（左上角） ----
        info = self._suspect(speaker) if speaker != "律师" else None
        np_w, np_h = 180, 50
        np_x, np_y = 20, 16
        self._dr_float_panel(s, (np_x, np_y, np_w, np_h), alpha=210,
                              bg_color=(60, 40, 15), border_color=(200, 160, 60))
        s.blit(self.f_name.render(speaker, True, WHITE),
               self.f_name.render(speaker, True, WHITE)
               .get_rect(center=(np_x + np_w // 2, np_y + 18)))
        if info:
            s.blit(self.f_tiny.render(info["role"], True, GRAY),
                   self.f_tiny.render(info["role"], True, GRAY)
                   .get_rect(center=(np_x + np_w // 2, np_y + 38)))

        # ---- 悬浮生命值（右上角） ----
        self._dr_life(s)

        # ---- 悬浮对话框（底部居中） ----
        dr = self._float_dialog_r()
        self._dr_float_panel(s, dr, alpha=210,
                              bg_color=(12, 18, 36), border_color=(160, 140, 80), radius=6)
        # 对话框内名牌
        dn_w, dn_h = 140, 28
        dn_x, dn_y = dr.x + 14, dr.y + 10
        self._dr_float_panel(s, (dn_x, dn_y, dn_w, dn_h), alpha=220,
                              bg_color=(60, 40, 15), border_color=(200, 160, 60), radius=3)
        s.blit(self.f_name.render(speaker, True, WHITE),
               self.f_name.render(speaker, True, WHITE)
               .get_rect(center=(dn_x + dn_w // 2, dn_y + dn_h // 2)))
        # 文本
        render_text_wrapped(s, shown_text, self.f_dialog, WHITE,
                            (dr.x + 18, dr.y + 46, dr.width - 36, dr.height - 56),
                            line_spacing=5)
        # 闪烁指示器
        if self.tw_done:
            if int(self.blink * 3) % 2:
                s.blit(self.f_small.render("▼", True, GOLD),
                       (dr.right - 30, dr.bottom - 28))

    def _float_dialog_r(self):
        """悬浮对话框 — 底部居中"""
        dw = SW - 80
        dx = 40
        dy = SH - self.DIALOG_H - 20
        return pygame.Rect(dx, dy, dw, self.DIALOG_H)

    # ============================================================
    #   绘制 — 推理桌面（三栏整合）
    # ============================================================
    def _dr_cross(self, s):
        # ---- 律师席全屏背景 ----
        seat_img = self.seat_imgs.get("lawyer")
        if seat_img:
            try:
                bg = fit_cover(seat_img, SW, SH)
                s.blit(bg, (0, 0))
            except Exception:
                s.fill(COURT_BG)
        else:
            s.fill(COURT_BG)
        # 半透明遮罩
        dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 100))
        s.blit(dim, (0, 0))

        # ---- 悬浮生命值 ----
        self._dr_life(s)

        # ---- 左侧：证词笔记（始终显示） ----
        self._dr_notebook(s)

        # ---- 右侧：证据 + 线索 ----
        self._dr_right_panel(s)

        # ---- 档案按钮（小，右下角） ----
        self._dr_profiles_mini_btn(s)

        # ---- 异议覆盖层 ----
        if self.state == S_OBJECTION:
            self._dr_obj_overlay(s)

    # ---- 左侧：证词笔记面板 ----
    def _dr_notebook(self, s):
        nr = self._notebook_r()
        self._dr_float_panel(s, nr, alpha=210, bg_color=(20, 28, 48),
                              border_color=(200, 160, 60), radius=10, border_w=2)

        # 标题
        s.blit(self.f_med.render("— 案件笔记 —", True, GOLD),
               (nr.x + 16, nr.y + 8))
        pygame.draw.line(s, PANEL_BORDER, (nr.x + 8, nr.y + 36),
                         (nr.right - 8, nr.y + 36), 1)

        # 裁剪
        clip = pygame.Rect(nr.x + 2, nr.y + 38, nr.width - 4, nr.height - 40)
        s.set_clip(clip)
        mouse = pygame.mouse.get_pos()

        for i, t in enumerate(self.case["testimonies"]):
            tr = self._testimony_item_r(i)
            if tr is None:
                continue

            pressed = self.press_done.get(t["id"], False)

            # 条目背景
            hov = tr.collidepoint(mouse)
            bg = (28, 38, 62) if hov else (22, 30, 50)
            panel_s = pygame.Surface((tr.width, tr.height), pygame.SRCALPHA)
            pygame.draw.rect(panel_s, (*bg, 220), (0, 0, tr.width, tr.height), border_radius=6)
            s.blit(panel_s, tr.topleft)

            # 序号+发言人
            s.blit(self.f_tiny.render(f'[{t["id"]}]', True, GOLD), (tr.x + 10, tr.y + 8))
            s.blit(self.f_small.render(t["speaker"], True, WHITE), (tr.x + 65, tr.y + 6))

            # 证词文本（扩大区域，避免长文本溢出到按钮区）
            text_h = 56
            render_text_wrapped(s, t["text"], self.f_small, LIGHT_GRAY,
                                (tr.x + 10, tr.y + 32, tr.width - 20, text_h), line_spacing=3)

            # 追问按钮
            press_r = self._press_btn_r(i)
            if press_r and not pressed:
                hov_p = press_r.collidepoint(mouse)
                self._dr_float_panel(s, press_r, alpha=220,
                                      bg_color=(50, 70, 50) if hov_p else (35, 50, 35),
                                      border_color=GOLD, radius=4)
                s.blit(self.f_tiny.render("追问", True, WHITE),
                       self.f_tiny.render("追问", True, WHITE).get_rect(center=press_r.center))
            elif press_r and pressed:
                self._dr_float_panel(s, press_r, alpha=180,
                                      bg_color=(30, 50, 30), border_color=GREEN, radius=4)
                s.blit(self.f_tiny.render("追问✓", True, GREEN),
                       self.f_tiny.render("追问✓", True, GREEN).get_rect(center=press_r.center))

            # 异议按钮
            obj_r = self._obj_btn_r(i)
            if obj_r:
                hov_o = obj_r.collidepoint(mouse)
                self._dr_float_panel(s, obj_r, alpha=220,
                                      bg_color=(220, 40, 40) if hov_o else OBJECTION_RED,
                                      border_color=OBJECTION_YELLOW, radius=4)
                s.blit(self.f_tiny.render("异议!", True, WHITE),
                       self.f_tiny.render("异议!", True, WHITE).get_rect(center=obj_r.center))

            # 追问回答（在证词文本下方，按钮上方，三者垂直排列不重叠）
            if pressed and t.get("press"):
                p = t["press"][0]
                # 文本区结束位置：tr.y + 32 + text_h ≈ tr.y + 88
                ay = tr.y + 95  # 从92增加到95，增加间距
                answer_h = 70  # 从46增加到70，增加回答框高度
                self._dr_float_panel(s, (tr.x + 10, ay, tr.width - 20, answer_h), alpha=180,
                                      bg_color=(30, 50, 30), border_color=(80, 140, 80), radius=4)
                s.blit(self.f_tiny.render(f'追问：{p["q"]}', True, (150, 200, 150)),
                       (tr.x + 14, ay + 8))  # 从6增加到8
                s.blit(self.f_tiny.render(f'回答：{p["a"]}', True, LIGHT_GRAY),
                       (tr.x + 14, ay + 30))  # 从24增加到30，增加行间距

        s.set_clip(None)

    # ---- 右侧：证据 + 线索面板 ----
    def _dr_right_panel(self, s):
        mouse = pygame.mouse.get_pos()
        rp = self._right_panel_r()
        self._dr_float_panel(s, rp, alpha=210, bg_color=(18, 26, 46),
                              border_color=(200, 160, 60), radius=10, border_w=2)

        # ===== 标题 =====
        s.blit(self.f_med.render("— 证据档案 —", True, GOLD), (rp.x + 14, rp.y + 8))
        pygame.draw.line(s, PANEL_BORDER, (rp.x + 8, rp.y + 36),
                         (rp.right - 8, rp.y + 36), 1)

        # ===== 上半区：证据网格（左）+ 详情（右）=====
        grid_x = rp.x + 14
        grid_y = rp.y + 46
        grid_w = 240
        detail_x = grid_x + grid_w + 14
        detail_w = rp.right - detail_x - 14
        zone_h = 250

        # --- 证据网格：2列正方形 ---
        for i, ev in enumerate(self.case["evidence"]):
            col = i % 2
            row = i // 2
            sq = 108
            ix = grid_x + col * (sq + 10)
            iy = grid_y + row * (sq + 10)
            ir = pygame.Rect(ix, iy, sq, sq)
            sel = (self.evidence_sel == i)
            hov = ir.collidepoint(mouse)
            bg = TEAL if sel else ((35, 48, 78) if hov else (25, 32, 55))
            draw_rr(s, bg, ir, 6)
            if sel:
                draw_rr_outline(s, OBJECTION_YELLOW, ir, 6, 2)
            # 图标区（上半 60%）
            icon_r = pygame.Rect(ir.x + 8, ir.y + 8, ir.width - 16, int(ir.height * 0.55))
            draw_rr(s, (18, 24, 42), icon_r, 4)
            # 证据编号居中
            s.blit(self.f_small.render(ev["id"], True, GOLD if sel else DARK_GRAY),
                   self.f_small.render(ev["id"], True, GOLD if sel else DARK_GRAY)
                   .get_rect(center=(icon_r.centerx, icon_r.centery - 6)))
            # 类型小字
            s.blit(self.f_tiny.render(ev["type"], True, GRAY),
                   self.f_tiny.render(ev["type"], True, GRAY)
                   .get_rect(center=(icon_r.centerx, icon_r.centery + 12)))
            # 标题（下半）
            title_y = ir.y + int(ir.height * 0.65) + 4
            render_text_wrapped(s, ev["title"], self.f_tiny, WHITE if sel else LIGHT_GRAY,
                                (ir.x + 6, title_y, ir.width - 12, 34), line_spacing=3)

        # --- 详情侧栏 ---
        if self.evidence_sel is not None and 0 <= self.evidence_sel < len(self.case["evidence"]):
            ev = self.case["evidence"][self.evidence_sel]
            dr = pygame.Rect(detail_x, grid_y, detail_w, zone_h)
            self._dr_float_panel(s, dr, alpha=200, bg_color=(22, 30, 52),
                                  border_color=PANEL_BORDER, radius=8)
            # 标题
            s.blit(self.f_med.render(ev["title"], True, GOLD), (dr.x + 14, dr.y + 12))
            pygame.draw.line(s, PANEL_BORDER, (dr.x + 10, dr.y + 42),
                             (dr.right - 10, dr.y + 42), 1)
            # 编号+类型
            s.blit(self.f_tiny.render(f'编号：{ev["id"]}', True, DARK_GRAY),
                   (dr.x + 14, dr.y + 50))
            s.blit(self.f_tiny.render(f'类型：{ev["type"]}', True, GRAY),
                   (dr.x + 14, dr.y + 70))
            # 描述
            render_text_wrapped(s, ev["desc"], self.f_small, LIGHT_GRAY,
                                (dr.x + 14, dr.y + 100, dr.width - 28, dr.height - 114), line_spacing=5)
        else:
            # 未选中提示
            hint_r = pygame.Rect(detail_x, grid_y, detail_w, zone_h)
            self._dr_float_panel(s, hint_r, alpha=180, bg_color=(22, 30, 52),
                                  border_color=PANEL_BORDER, radius=8)
            s.blit(self.f_small.render("← 点击左侧证据", True, DARK_GRAY),
                   self.f_small.render("← 点击左侧证据", True, DARK_GRAY)
                   .get_rect(center=hint_r.center))

        # ===== 下半：线索板 =====
        clue_top = grid_y + zone_h + 14
        s.blit(self.f_med.render("— 线索板 —", True, GOLD), (rp.x + 14, clue_top))
        pygame.draw.line(s, PANEL_BORDER, (rp.x + 8, clue_top + 28),
                         (rp.right - 8, clue_top + 28), 1)

        cy = clue_top + 38
        has_clue = False
        for t in self.case["testimonies"]:
            if self.press_done.get(t["id"], False) and t["press"]:
                p = t["press"][0]
                clue = p.get("clue", "")
                if clue and clue != "无":
                    has_clue = True
                    cr = pygame.Rect(rp.x + 14, cy, rp.width - 28, 55)
                    self._dr_float_panel(s, cr, alpha=180, bg_color=(25, 35, 55),
                                          border_color=(100, 140, 100), radius=4)
                    s.blit(self.f_tiny.render(f'🔍 {clue}', True, LIGHT_GRAY),
                           (cr.x + 10, cr.y + 6))
                    s.blit(self.f_tiny.render(f'来源：{t["speaker"]} - {t["id"]}', True, DARK_GRAY),
                           (cr.x + 10, cr.y + 30))
                    cy += 62

        if not has_clue:
            s.blit(self.f_small.render("暂无线索", True, DARK_GRAY),
                   self.f_small.render("暂无线索", True, DARK_GRAY)
                   .get_rect(center=(rp.centerx, clue_top + 70)))
            s.blit(self.f_tiny.render("对证词进行追问以收集线索", True, GRAY),
                   self.f_tiny.render("对证词进行追问以收集线索", True, GRAY)
                   .get_rect(center=(rp.centerx, clue_top + 95)))

    # ---- 档案小按钮 ----
    def _dr_profiles_mini_btn(self, s):
        mouse = pygame.mouse.get_pos()
        br = self._profiles_mini_btn_r()
        hov = br.collidepoint(mouse)
        self._dr_float_panel(s, br, alpha=220,
                              bg_color=(60, 60, 80) if hov else DARK_GRAY,
                              border_color=(100, 100, 120), radius=4)
        s.blit(self.f_tiny.render("人物档案", True, WHITE),
               self.f_tiny.render("人物档案", True, WHITE).get_rect(center=br.center))

    # ---- 悬浮生命值（右上角） ----
    def _dr_life(self, s):
        # 悬浮背景框
        lw, lh = 200, 36
        lr = pygame.Rect(SW - lw - 12, 8, lw, lh)
        self._dr_float_panel(s, lr, alpha=180, bg_color=(16, 24, 48),
                              border_color=(70, 85, 120), radius=4)
        # 标签
        s.blit(self.f_tiny.render("机会", True, GRAY), (lr.x + 10, lr.y + 8))
        # 天平图标
        for i in range(3):
            cx = lr.x + 65 + i * 40
            cy = lr.y + lh // 2
            if i < self.life:
                pygame.draw.circle(s, GOLD, (cx, cy), 13)
                pygame.draw.circle(s, NAMEPLATE_BORDER, (cx, cy), 13, 2)
                s.blit(self.f_tiny.render("⚖", True, WOOD_DARK),
                       self.f_tiny.render("⚖", True, WOOD_DARK)
                       .get_rect(center=(cx, cy)))
            else:
                pygame.draw.circle(s, (50, 20, 20), (cx, cy), 13)
                pygame.draw.circle(s, PENALTY_RED, (cx, cy), 13, 2)
                s.blit(self.f_tiny.render("X", True, PENALTY_RED),
                       self.f_tiny.render("X", True, PENALTY_RED)
                       .get_rect(center=(cx, cy)))

    # ---- 悬浮底部按钮 ----
    # ---- 证据面板（已整合到右侧，保留兼容） ----
    def _dr_evidence_panel(self, s):
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        s.blit(overlay, (0, 0))

        panel = self._overlay_r()
        self._dr_float_panel(s, panel, alpha=240, bg_color=(18, 25, 45),
                              border_color=(200, 160, 60), radius=10, border_w=3)
        draw_gradient(s, WOOD, WOOD_DARK, (panel.x, panel.y, panel.width, 50))
        s.blit(self.f_large.render("证 据 档 案", True, GOLD),
               self.f_large.render("证 据 档 案", True, GOLD)
               .get_rect(center=(panel.centerx, panel.y + 26)))

        for i, ev in enumerate(self.case["evidence"]):
            ir = pygame.Rect(panel.left + 20, panel.top + 70 + i * 52, 340, 44)
            sel = (self.evidence_sel == i)
            bg = TEAL if sel else (25, 32, 55)
            draw_rr(s, bg, ir, 4)
            if sel:
                draw_rr_outline(s, OBJECTION_YELLOW, ir, 4, 2)
            s.blit(self.f_tiny.render(f'[{ev["id"]}]', True, GOLD if sel else DARK_GRAY), (ir.x + 8, ir.y + 4))
            s.blit(self.f_small.render(ev["title"], True, WHITE if sel else GRAY), (ir.x + 60, ir.y + 3))
            s.blit(self.f_tiny.render(ev["type"], True, GRAY if sel else DARK_GRAY), (ir.x + 60, ir.y + 25))

        # 右侧详情
        dr = pygame.Rect(panel.left + 380, panel.top + 70, 520, 460)
        draw_rr(s, (22, 30, 52), dr, 6)
        if self.evidence_sel is not None and 0 <= self.evidence_sel < len(self.case["evidence"]):
            ev = self.case["evidence"][self.evidence_sel]
            s.blit(self.f_med.render(ev["title"], True, GOLD), (dr.x + 20, dr.y + 20))
            s.blit(self.f_tiny.render(f'类型：{ev["type"]}', True, GRAY), (dr.x + 20, dr.y + 60))
            s.blit(self.f_tiny.render(f'编号：{ev["id"]}', True, DARK_GRAY), (dr.x + 20, dr.y + 85))
            pygame.draw.line(s, PANEL_BORDER, (dr.x + 20, dr.y + 120), (dr.right - 20, dr.y + 120), 1)
            render_text_wrapped(s, ev["desc"], self.f_dialog, LIGHT_GRAY,
                                (dr.x + 20, dr.y + 140, dr.width - 40, dr.height - 160), line_spacing=6)
        else:
            s.blit(self.f_small.render("← 请选择左侧证据查看详情", True, GRAY),
                   (dr.x + 80, dr.y + 200))

    # ---- 人物档案面板（悬浮覆盖） ----
    def _dr_profiles_panel(self, s):
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        s.blit(overlay, (0, 0))

        panel = self._overlay_r()
        self._dr_float_panel(s, panel, alpha=240, bg_color=(18, 25, 45),
                              border_color=(200, 160, 60), radius=10, border_w=3)
        draw_gradient(s, WOOD, WOOD_DARK, (panel.x, panel.y, panel.width, 50))
        s.blit(self.f_large.render("人 物 档 案", True, GOLD),
               self.f_large.render("人 物 档 案", True, GOLD)
               .get_rect(center=(panel.centerx, panel.y + 26)))

        cw = (panel.width - 80) // 3
        for i, su in enumerate(self.case["suspects"]):
            cx = panel.left + 20 + i * (cw + 20)
            cy = panel.top + 70
            cr = pygame.Rect(cx, cy, cw, 480)
            draw_rr(s, (25, 32, 55), cr, 6)
            draw_rr_outline(s, PANEL_BORDER, cr, 6)

            portrait = self.portraits.get(su.get("portrait", ""))
            if portrait:
                sc = pygame.transform.smoothscale(portrait, (120, 120))
                s.blit(sc, sc.get_rect(center=(cx + cw // 2, cy + 80)))
            else:
                pygame.draw.circle(s, GRAY, (cx + cw // 2, cy + 80), 50)

            npr = pygame.Rect(cx + 10, cy + 155, cw - 20, 30)
            draw_rr(s, NAMEPLATE_BG, npr, 3)
            draw_rr_outline(s, NAMEPLATE_BORDER, npr, 3)
            s.blit(self.f_small.render(su["name"], True, WHITE),
                   self.f_small.render(su["name"], True, WHITE).get_rect(center=npr.center))

            iy = cy + 200
            for lbl, val in [("角色", su["role"]), ("性格", su["personality"]),
                             ("动机", su["motive"])]:
                s.blit(self.f_tiny.render(f'{lbl}：', True, GOLD), (cx + 15, iy))
                render_text_wrapped(s, val, self.f_tiny, LIGHT_GRAY,
                                    (cx + 15, iy + 20, cw - 30, 50), line_spacing=3)
                iy += 75

    # ---- 线索板面板 ----
    def _dr_clues_panel(self, s):
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        s.blit(overlay, (0, 0))

        panel = self._overlay_r()
        self._dr_float_panel(s, panel, alpha=240, bg_color=(18, 25, 45),
                              border_color=(200, 160, 60), radius=10, border_w=3)
        draw_gradient(s, WOOD, WOOD_DARK, (panel.x, panel.y, panel.width, 50))
        s.blit(self.f_large.render("线 索 板", True, GOLD),
               self.f_large.render("线 索 板", True, GOLD)
               .get_rect(center=(panel.centerx, panel.y + 26)))

        # 收集所有已追问的线索
        y = panel.top + 70
        has_clue = False
        for t in self.case["testimonies"]:
            if self.press_done.get(t["id"], False) and t["press"]:
                p = t["press"][0]
                clue = p.get("clue", "")
                if clue and clue != "无":
                    has_clue = True
                    cr = pygame.Rect(panel.left + 20, y, panel.width - 40, 60)
                    self._dr_float_panel(s, cr, alpha=200, bg_color=(25, 35, 55),
                                          border_color=(100, 140, 100), radius=6)
                    s.blit(self.f_small.render(f'🔍 {clue}', True, LIGHT_GRAY),
                           (cr.x + 14, cr.y + 8))
                    s.blit(self.f_tiny.render(f'来源：{t["speaker"]} - {t["id"]}', True, GRAY),
                           (cr.x + 14, cr.y + 36))
                    y += 72

        if not has_clue:
            s.blit(self.f_med.render("暂无线索", True, DARK_GRAY),
                   self.f_med.render("暂无线索", True, DARK_GRAY)
                   .get_rect(center=(panel.centerx, panel.centery)))
            s.blit(self.f_small.render("对证词进行追问以收集线索", True, GRAY),
                   self.f_small.render("对证词进行追问以收集线索", True, GRAY)
                   .get_rect(center=(panel.centerx, panel.centery + 35)))

    # ---- 指证覆盖层（居中窄面板，不遮挡两侧桌面） ----
    def _dr_obj_overlay(self, s):
        mouse = pygame.mouse.get_pos()
        # 居中窄面板
        pw, ph = 520, 480
        px = (SW - pw) // 2
        py = (SH - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # 只在面板周围画一个 subtle 暗角，不是全屏遮罩
        # 四角阴影
        for corner in [
            (0, 0, px, SH),                # 左
            (px + pw, 0, SW - px - pw, SH), # 右
            (px, 0, pw, py),               # 上
            (px, py + ph, pw, SH - py - ph) # 下
        ]:
            shadow = pygame.Surface((corner[2], corner[3]), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 120))
            s.blit(shadow, (corner[0], corner[1]))

        self._dr_float_panel(s, panel, alpha=250, bg_color=(14, 20, 38),
                              border_color=OBJECTION_RED, radius=12, border_w=3)
        draw_gradient(s, OBJECTION_RED, DARK_RED, (panel.x, panel.y, panel.width, 52))

        # 标题
        s.blit(self.f_large.render("选择支持异议的证据", True, WHITE),
               self.f_large.render("选择支持异议的证据", True, WHITE)
               .get_rect(center=(panel.centerx, panel.y + 28)))

        # 目标证词（大字显示）
        st = self._testi(self.obj_tid)
        if st:
            t_r = pygame.Rect(panel.left + 20, panel.top + 62, panel.width - 40, 60)
            self._dr_float_panel(s, t_r, alpha=200, bg_color=(30, 20, 15),
                                  border_color=ORANGE, radius=6)
            s.blit(self.f_tiny.render(f'目标证词 [{st["id"]}] {st["speaker"]}', True, ORANGE),
                   (t_r.x + 12, t_r.y + 6))
            render_text_wrapped(s, st["text"], self.f_small, LIGHT_GRAY,
                                (t_r.x + 12, t_r.y + 26, t_r.width - 24, 30), line_spacing=3)

        # 证据网格（2列正方形）
        grid_x = panel.left + 24
        grid_y = panel.top + 136
        sq = 90
        for i, ev in enumerate(self.case["evidence"]):
            col = i % 2
            row = i // 2
            ix = grid_x + col * (sq + 14)
            iy = grid_y + row * (sq + 14)
            ir = pygame.Rect(ix, iy, sq, sq)
            sel = (self.obj_eid == ev["id"])
            hov = ir.collidepoint(mouse)
            bg = TEAL if sel else ((38, 50, 82) if hov else (28, 36, 60))
            draw_rr(s, bg, ir, 6)
            if sel:
                draw_rr_outline(s, OBJECTION_YELLOW, ir, 6, 2)
            # 图标区
            icon_r = pygame.Rect(ir.x + 6, ir.y + 6, ir.width - 12, int(ir.height * 0.5))
            draw_rr(s, (18, 24, 42), icon_r, 4)
            s.blit(self.f_tiny.render(ev["id"], True, GOLD if sel else DARK_GRAY),
                   self.f_tiny.render(ev["id"], True, GOLD if sel else DARK_GRAY)
                   .get_rect(center=(icon_r.centerx, icon_r.centery - 2)))
            s.blit(self.f_tiny.render(ev["type"], True, GRAY),
                   self.f_tiny.render(ev["type"], True, GRAY)
                   .get_rect(center=(icon_r.centerx, icon_r.centery + 12)))
            # 标题
            title_y = ir.y + int(ir.height * 0.58) + 2
            render_text_wrapped(s, ev["title"], self.f_tiny, WHITE if sel else LIGHT_GRAY,
                                (ir.x + 4, title_y, ir.width - 8, 32), line_spacing=2)

        # 按钮
        self._dr_btn(s, pygame.Rect(panel.centerx - 170, panel.bottom - 55, 150, 42),
                      "取消", DARK_GRAY, mouse)
        ob = pygame.Rect(panel.centerx + 20, panel.bottom - 55, 150, 42)
        hov = ob.collidepoint(mouse) and self.obj_eid is not None
        bg = (220, 40, 40) if hov else OBJECTION_RED
        draw_rr(s, bg if self.obj_eid else (60, 30, 30), ob, 4)
        if self.obj_eid:
            draw_rr_outline(s, OBJECTION_YELLOW, ob, 4, 2)
        s.blit(self.f_med.render("提出异议!", True,
                                  WHITE if self.obj_eid else DARK_GRAY),
               self.f_med.render("提出异议!", True,
                                 WHITE if self.obj_eid else DARK_GRAY)
               .get_rect(center=ob.center))

    # ---- 通用按钮 ----
    def _dr_btn(self, s, rect, text, color, mouse, enabled=True, bold=False):
        if not enabled:
            draw_rr(s, (40, 45, 60), rect, 4)
            draw_rr_outline(s, (60, 65, 80), rect, 4)
            s.blit(self.f_small.render(text, True, DARK_GRAY),
                   self.f_small.render(text, True, DARK_GRAY).get_rect(center=rect.center))
        else:
            hov = rect.collidepoint(mouse)
            bg = tuple(min(c + 40, 255) for c in color) if hov else color
            draw_rr(s, bg, rect, 4)
            draw_rr_outline(s, NAMEPLATE_BORDER, rect, 4)
            f = self.f_med if bold else self.f_small
            s.blit(f.render(text, True, WHITE),
                   f.render(text, True, WHITE).get_rect(center=rect.center))

    # ============================================================
    #   异议演出动画
    # ============================================================
    def _dr_oa_anim(self, s):
        p = min(self.oa_timer / self.oa_dur, 1.0)

        # Phase 1: 红色闪光 + 斜线切割
        if p < 0.25:
            t = p / 0.25
            flash = pygame.Surface((SW, SH), pygame.SRCALPHA)
            flash.fill((200, 0, 0, int(200 * (1 - t))))
            s.blit(flash, (0, 0))
            line_s = pygame.Surface((SW, SH), pygame.SRCALPHA)
            off = int(SW * 2 * t) - SW
            pts = [(off - 200, SH), (off, SH), (off + SH + 200, 0), (off + SH, 0)]
            pygame.draw.polygon(line_s, (255, 255, 255, 200), pts)
            s.blit(line_s, (0, 0))

        # Phase 2: 大字
        if p >= 0.15:
            t2 = (p - 0.15) / 0.85
            bg = pygame.Surface((SW, SH), pygame.SRCALPHA)
            bg.fill((150, 0, 0, int(120 * max(0, 1 - t2 * 0.5))))
            s.blit(bg, (0, 0))

            if t2 < 0.2:
                sc = 0.2 + (t2 / 0.2) * 0.9
            elif t2 < 0.35:
                sc = 1.1 - (t2 - 0.2) / 0.15 * 0.1
            else:
                sc = 1.0
            tw = int(self._obj_yellow.get_width() * sc)
            th = int(self._obj_yellow.get_height() * sc)
            if tw > 0 and th > 0:
                alpha = min(255, int(255 * min(t2 / 0.2, 1.0)))
                for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4)]:
                    img = pygame.transform.smoothscale(self._obj_white, (tw, th))
                    img.set_alpha(alpha)
                    s.blit(img, img.get_rect(center=(SW // 2 + dx, SH // 2 + dy)))
                img2 = pygame.transform.smoothscale(self._obj_yellow, (tw, th))
                img2.set_alpha(alpha)
                s.blit(img2, img2.get_rect(center=(SW // 2, SH // 2)))

        # Phase 3: 放射线
        if 0.15 <= p < 0.6:
            t3 = (p - 0.15) / 0.45
            la = int(100 * (1 - t3))
            if la > 0:
                ls = pygame.Surface((SW, SH), pygame.SRCALPHA)
                cx, cy = SW // 2, SH // 2
                for a in range(0, 360, 12):
                    rad = math.radians(a)
                    inner = 100 + int(200 * t3)
                    outer = inner + 600
                    sx2 = cx + int(inner * math.cos(rad))
                    sy2 = cy + int(inner * math.sin(rad))
                    ex = cx + int(outer * math.cos(rad))
                    ey = cy + int(outer * math.sin(rad))
                    pygame.draw.line(ls, (255, 255, 200, la), (sx2, sy2), (ex, ey), 2)
                s.blit(ls, (0, 0))

    # ============================================================
    #   判决界面（法官席全屏背景 + 悬浮信息）
    # ============================================================
    def _dr_judgement(self, s):
        # 法官席全屏背景
        judge_img = self.seat_imgs.get("judge")
        if judge_img:
            try:
                bg = fit_cover(judge_img, SW, SH)
                s.blit(bg, (0, 0))
            except Exception:
                s.fill(COURT_BG)
        else:
            s.fill(COURT_BG)
        # 遮罩
        dim = pygame.Surface((SW, SH), pygame.SRCALPHA)

        phases = self.case.get("phases", [])
        has_next_phase = self.judge_ok and (self.current_phase + 1 < len(phases))

        if self.judge_ok:
            dim.fill((0, 50, 0, 60))
            s.blit(dim, (0, 0))

            if has_next_phase:
                # ---- 阶段成功，还有下一阶段 ----
                title_r = pygame.Rect((SW - 600) // 2, 40, 600, 60)
                self._dr_float_panel(s, title_r, alpha=230, bg_color=(0, 60, 20),
                                      border_color=GOLD, radius=8, border_w=3)
                s.blit(self.f_huge.render("异议成立！出现新情况...", True, GOLD),
                       self.f_huge.render("异议成立！出现新情况...", True, GOLD)
                       .get_rect(center=title_r.center))

                # 法官评论
                comment_r = pygame.Rect(140, 120, 1000, 90)
                self._dr_float_panel(s, comment_r, alpha=220, bg_color=(16, 24, 48),
                                      border_color=GOLD, radius=8, border_w=2)
                render_text_wrapped(s, self.case.get("phase_judge_comment", ""), self.f_dialog, WHITE,
                                    (comment_r.x + 20, comment_r.y + 12, comment_r.width - 40, 66), line_spacing=5)

                # 证人改口（反转）- 支持多改口台词
                # 优先使用 transitions 字典（根据证据选择不同台词）
                transitions = self.case.get("transitions", {})
                trans = None
                if transitions:
                    # 根据使用的证据选择对应的改口台词
                    if self.obj_evidence_used and self.obj_evidence_used in transitions:
                        trans = transitions[self.obj_evidence_used]
                    elif "default" in transitions:
                        trans = transitions["default"]
                # 兼容旧格式：单个 transition
                if trans is None:
                    trans = self.case.get("_transition", {})
                if trans:
                    trans_r = pygame.Rect(140, 220, 1000, 180)
                    self._dr_float_panel(s, trans_r, alpha=220, bg_color=(40, 30, 15),
                                          border_color=ORANGE, radius=8, border_w=2)
                    s.blit(self.f_large.render("证人改口", True, ORANGE), (trans_r.x + 20, trans_r.y + 10))
                    # 名牌
                    np_w, np_h = 140, 28
                    self._dr_float_panel(s, (trans_r.x + 20, trans_r.y + 48, np_w, np_h), alpha=220,
                                          bg_color=(60, 40, 15), border_color=(200, 160, 60), radius=3)
                    s.blit(self.f_name.render(trans.get("speaker", ""), True, WHITE),
                           self.f_name.render(trans.get("speaker", ""), True, WHITE)
                           .get_rect(center=(trans_r.x + 20 + np_w // 2, trans_r.y + 48 + np_h // 2)))
                    render_text_wrapped(s, trans.get("text", ""), self.f_dialog, LIGHT_GRAY,
                                        (trans_r.x + 20, trans_r.y + 84, trans_r.width - 40, 90), line_spacing=5)

                btn_text, btn_color = "继续调查", BLUE
            else:
                # ---- 最终胜利 ----
                title_r = pygame.Rect((SW - 500) // 2, 40, 500, 60)
                self._dr_float_panel(s, title_r, alpha=230, bg_color=(0, 60, 20),
                                      border_color=GOLD, radius=8, border_w=3)
                s.blit(self.f_huge.render("异议成立!", True, GOLD),
                       self.f_huge.render("异议成立!", True, GOLD)
                       .get_rect(center=title_r.center))

                # 证人最终坦白（真相大白）
                trans = self.case.get("_transition", {})
                y_off = 120
                if trans:
                    trans_r = pygame.Rect(140, y_off, 1000, 130)
                    self._dr_float_panel(s, trans_r, alpha=220, bg_color=(40, 30, 15),
                                          border_color=ORANGE, radius=8, border_w=2)
                    s.blit(self.f_large.render("真相大白", True, ORANGE), (trans_r.x + 20, trans_r.y + 10))
                    np_w, np_h = 140, 28
                    self._dr_float_panel(s, (trans_r.x + 20, trans_r.y + 48, np_w, np_h), alpha=220,
                                          bg_color=(60, 40, 15), border_color=(200, 160, 60), radius=3)
                    s.blit(self.f_name.render(trans.get("speaker", ""), True, WHITE),
                           self.f_name.render(trans.get("speaker", ""), True, WHITE)
                           .get_rect(center=(trans_r.x + 20 + np_w // 2, trans_r.y + 48 + np_h // 2)))
                    render_text_wrapped(s, trans.get("text", ""), self.f_dialog, LIGHT_GRAY,
                                        (trans_r.x + 20, trans_r.y + 84, trans_r.width - 40, 60), line_spacing=5)
                    y_off = 270

                # 真相悬浮面板
                truth_r = pygame.Rect(140, y_off, 1000, 150)
                self._dr_float_panel(s, truth_r, alpha=220, bg_color=(16, 24, 48),
                                      border_color=GOLD, radius=8, border_w=2)
                s.blit(self.f_large.render("案件真相", True, GOLD), (truth_r.x + 20, truth_r.y + 10))
                render_text_wrapped(s, self.case["truth"], self.f_dialog, LIGHT_GRAY,
                                    (truth_r.x + 20, truth_r.y + 50, truth_r.width - 40, 90), line_spacing=5)
                # 法官宣判悬浮面板
                judge_r = pygame.Rect(140, y_off + 160, 1000, 130)
                self._dr_float_panel(s, judge_r, alpha=220, bg_color=(16, 24, 48),
                                      border_color=NAMEPLATE_BORDER, radius=8, border_w=2)
                s.blit(self.f_large.render("法官宣判", True, GOLD), (judge_r.x + 20, judge_r.y + 10))
                render_text_wrapped(s, self.case.get("phase_judge_comment", ""), self.f_dialog, WHITE,
                                    (judge_r.x + 20, judge_r.y + 50, judge_r.width - 40, 70), line_spacing=5)
                btn_text, btn_color = "查看结果", DARK_GREEN
        else:
            dim.fill((50, 0, 0, 60))
            s.blit(dim, (0, 0))
            if self.life <= 0:
                # 悬浮标题
                title_r = pygame.Rect((SW - 400) // 2, 40, 400, 60)
                self._dr_float_panel(s, title_r, alpha=230, bg_color=(100, 0, 0),
                                      border_color=PENALTY_RED, radius=8, border_w=3)
                s.blit(self.f_huge.render("败诉!", True, WHITE),
                       self.f_huge.render("败诉!", True, WHITE)
                       .get_rect(center=title_r.center))
                s.blit(self.f_large.render("生命值耗尽，案件败诉...", True, LIGHT_GRAY),
                       self.f_large.render("生命值耗尽，案件败诉...", True, LIGHT_GRAY)
                       .get_rect(center=(SW // 2, 130)))
                ans_r = pygame.Rect(200, 180, 880, 280)
                self._dr_float_panel(s, ans_r, alpha=220, bg_color=(25, 30, 50),
                                      border_color=GOLD, radius=8, border_w=2)
                s.blit(self.f_med.render("正确答案（任一即可）：", True, GOLD), (ans_r.x + 20, ans_r.y + 14))
                vy = ans_r.y + 48
                for vo in self.case.get("valid_objections", []):
                    if vy + 40 > ans_r.bottom:
                        break
                    t = self._testi(vo.get("testimony_id", ""))
                    e = next((ev for ev in self.case["evidence"] if ev["id"] == vo.get("evidence_id", "")), None)
                    t_name = t["speaker"] if t else "?"
                    e_name = e["title"] if e else "?"
                    reason = vo.get("reason", "")
                    line = f'• {t_name} + {e_name}'
                    if reason:
                        line += f'  ——{reason}'
                    s.blit(self.f_tiny.render(line, True, LIGHT_GRAY), (ans_r.x + 24, vy))
                    vy += 22
                btn_text, btn_color = "查看结果", OBJECTION_RED
            else:
                title_r = pygame.Rect((SW - 500) // 2, 40, 500, 60)
                self._dr_float_panel(s, title_r, alpha=230, bg_color=(120, 0, 0),
                                      border_color=OBJECTION_RED, radius=8, border_w=3)
                s.blit(self.f_huge.render("异议无效!", True, WHITE),
                       self.f_huge.render("异议无效!", True, WHITE)
                       .get_rect(center=title_r.center))
                s.blit(self.f_large.render(f'举证失败，剩余机会：{self.life}', True, LIGHT_GRAY),
                       self.f_large.render(f'举证失败，剩余机会：{self.life}', True, LIGHT_GRAY)
                       .get_rect(center=(SW // 2, 160)))
                warn_r = pygame.Rect((SW - 600) // 2, 210, 600, 50)
                self._dr_float_panel(s, warn_r, alpha=200, bg_color=(60, 30, 10),
                                      border_color=ORANGE, radius=6)
                s.blit(self.f_med.render("请重新审视证据和证词，找出真正的矛盾！",
                                          True, ORANGE),
                       self.f_med.render("请重新审视证据和证词，找出真正的矛盾！", True, ORANGE)
                       .get_rect(center=warn_r.center))
                btn_text, btn_color = "继续推理", BLUE

        btn = pygame.Rect(SW // 2 - 130, SH - 80, 260, 50)
        mouse = pygame.mouse.get_pos()
        hov = btn.collidepoint(mouse)
        bg = tuple(min(c + 30, 255) for c in btn_color) if hov else btn_color
        self._dr_float_panel(s, btn, alpha=230, bg_color=bg, border_color=NAMEPLATE_BORDER,
                              radius=6, border_w=2)
        s.blit(self.f_med.render(btn_text, True, WHITE),
               self.f_med.render(btn_text, True, WHITE).get_rect(center=btn.center))

    # ============================================================
    #   结果界面（席位背景 + 悬浮信息）
    # ============================================================
    def _dr_result(self, s):
        # 用法官席背景
        judge_img = self.seat_imgs.get("judge")
        if judge_img:
            try:
                bg = fit_cover(judge_img, SW, SH)
                s.blit(bg, (0, 0))
            except Exception:
                s.fill(COURT_BG)
        else:
            s.fill(COURT_BG)

        if self.result_type == "win":
            # 金色遮罩
            dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
            dim.fill((40, 30, 0, 80))
            s.blit(dim, (0, 0))
            for sx, sy, sr in self.win_stars:
                pygame.draw.circle(s, GOLD, (sx, sy), sr)
            title_r = pygame.Rect((SW - 400) // 2, 40, 400, 60)
            self._dr_float_panel(s, title_r, alpha=230, bg_color=(50, 40, 0),
                                  border_color=GOLD, radius=8, border_w=3)
            s.blit(self.f_huge.render("胜 诉!", True, GOLD),
                   self.f_huge.render("胜 诉!", True, GOLD)
                   .get_rect(center=title_r.center))

            # ---- 法官宣判对话框 ----
            verdict_r = pygame.Rect(80, 120, SW - 160, 420)
            self._dr_float_panel(s, verdict_r, alpha=220, bg_color=(12, 18, 36),
                                  border_color=(160, 140, 80), radius=8, border_w=2)
            # 法官名牌
            np_w, np_h = 140, 30
            self._dr_float_panel(s, (verdict_r.x + 20, verdict_r.y + 12, np_w, np_h),
                                  alpha=220, bg_color=(60, 40, 15), border_color=(200, 160, 60), radius=3)
            s.blit(self.f_name.render("法官", True, WHITE),
                   self.f_name.render("法官", True, WHITE)
                   .get_rect(center=(verdict_r.x + 20 + np_w // 2, verdict_r.y + 12 + np_h // 2)))

            # 宣判内容（使用自动换行，防止名字过长溢出）
            ty = verdict_r.y + 52
            defendant = self.case.get("suspects", [{}])[0].get("name", "")
            real_criminal = self.case.get("_meta", {}).get("real_criminal", "")
            truth = self.case.get("truth", "")
            content_w = verdict_r.width - 60
            # 无罪宣判
            if defendant:
                verdict_text = f'经本庭审理，被告{defendant}的嫌疑已被洗清，宣布无罪！'
                ty += render_text_wrapped(s, verdict_text, self.f_dialog, WHITE,
                                          (verdict_r.x + 30, ty, content_w, 80), line_spacing=4)
                ty += 6
            # 真凶
            if real_criminal:
                criminal_text = f'真正的罪犯是——{real_criminal}！'
                ty += render_text_wrapped(s, criminal_text, self.f_dialog, OBJECTION_YELLOW,
                                          (verdict_r.x + 30, ty, content_w, 60), line_spacing=4)
                ty += 6
            # 真相
            if truth:
                pygame.draw.line(s, PANEL_BORDER,
                                 (verdict_r.x + 30, ty), (verdict_r.right - 30, ty), 1)
                ty += 8
                s.blit(self.f_small.render("案件真相：", True, ORANGE), (verdict_r.x + 30, ty))
                ty += 22
                # 动态计算剩余可用高度
                remaining_h = verdict_r.bottom - ty - 40  # 底部留 40px 给提示文字
                render_text_wrapped(s, truth, self.f_dialog, LIGHT_GRAY,
                                    (verdict_r.x + 30, ty, content_w, remaining_h), line_spacing=6)

            # 底部
            s.blit(self.f_small.render("正义得到了伸张！", True, GOLD),
                   self.f_small.render("正义得到了伸张！", True, GOLD)
                   .get_rect(center=(verdict_r.centerx, verdict_r.bottom - 24)))

            # 案件信息
            info_r = pygame.Rect((SW - 500) // 2, 510, 500, 36)
            self._dr_float_panel(s, info_r, alpha=180, bg_color=(16, 24, 48),
                                  border_color=(70, 85, 120), radius=4)
            s.blit(self.f_tiny.render(
                f'案件：{self.case["title"]}  |  剩余机会：{self.life}', True, LIGHT_GRAY),
                   (info_r.x + 14, info_r.y + 8))
        else:
            dim = pygame.Surface((SW, SH), pygame.SRCALPHA)
            dim.fill((30, 0, 0, 100))
            s.blit(dim, (0, 0))
            title_r = pygame.Rect((SW - 400) // 2, 140, 400, 70)
            self._dr_float_panel(s, title_r, alpha=230, bg_color=(80, 0, 0),
                                  border_color=PENALTY_RED, radius=8, border_w=3)
            s.blit(self.f_huge.render("败诉...", True, PENALTY_RED),
                   self.f_huge.render("败诉...", True, PENALTY_RED)
                   .get_rect(center=title_r.center))
            s.blit(self.f_large.render("真相仍隐藏在迷雾之中...", True, LIGHT_GRAY),
                   self.f_large.render("真相仍隐藏在迷雾之中...", True, LIGHT_GRAY)
                   .get_rect(center=(SW // 2, 260)))

        mouse = pygame.mouse.get_pos()
        restart = pygame.Rect(SW // 2 - 260, SH - 80, 230, 50)
        menu = pygame.Rect(SW // 2 + 30, SH - 80, 230, 50)

        hr = restart.collidepoint(mouse)
        self._dr_float_panel(s, restart, alpha=220,
                              bg_color=(60, 80, 180) if hr else BLUE,
                              border_color=NAMEPLATE_BORDER, radius=6, border_w=2)
        s.blit(self.f_med.render("重新开始", True, WHITE),
               self.f_med.render("重新开始", True, WHITE).get_rect(center=restart.center))

        hm = menu.collidepoint(mouse)
        self._dr_float_panel(s, menu, alpha=220,
                              bg_color=(60, 60, 60) if hm else DARK_GRAY,
                              border_color=PANEL_BORDER, radius=6, border_w=2)
        s.blit(self.f_med.render("返回菜单", True, WHITE),
               self.f_med.render("返回菜单", True, WHITE).get_rect(center=menu.center))

    # ============================================================
    #   事件 — AI 配置界面
    # ============================================================
    def _ev_ai_config(self, ev):
        # 如果正在输入
        if self.ai_input_active:
            if ev.type == pygame.TEXTINPUT:
                if self.ai_input_active == "pref" and len(self.ai_pref_text) < 80:
                    self.ai_pref_text += ev.text
                elif self.ai_input_active == "theme" and len(self.ai_input) < 50:
                    self.ai_input += ev.text
                return
            if ev.type == pygame.TEXTEDITING:
                self.ime_composing = ev.text
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    self.ai_input_active = False
                    self.ime_composing = ""
                    pygame.key.stop_text_input()
                elif ev.key == pygame.K_ESCAPE:
                    self.ai_input_active = False
                    self.ime_composing = ""
                    pygame.key.stop_text_input()
                elif ev.key == pygame.K_BACKSPACE:
                    if self.ai_input_active == "pref":
                        self.ai_pref_text = self.ai_pref_text[:-1]
                    elif self.ai_input_active == "theme":
                        self.ai_input = self.ai_input[:-1]
            return
        
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            mx, my = ev.pos
            
            # 偏好输入框
            pref_box = pygame.Rect(240, 238, 800, 56)
            if pref_box.collidepoint(mx, my):
                self.ai_input_active = "pref"
                pygame.key.start_text_input()
                pygame.key.set_text_input_rect(pref_box)
                return

            # 主题输入框
            theme_box = pygame.Rect(240, 378, 800, 56)
            if theme_box.collidepoint(mx, my):
                self.ai_input_active = "theme"
                pygame.key.start_text_input()
                pygame.key.set_text_input_rect(theme_box)
                return

            # 性能模式开关 — 滑块轨道
            track_x = SW // 2 - 120
            track_y = 460
            perf_track = pygame.Rect(track_x, track_y, 60, 28)
            if perf_track.collidepoint(mx, my):
                self.perf_mode = not self.perf_mode
                return

            # 开始生成
            start_btn = pygame.Rect(SW // 2 - 170, 510, 340, 68)
            if start_btn.collidepoint(mx, my):
                self._apply_prefs()
                self._start_ai_generate()
                return

            # 返回 — 文字链接区域
            back_x = 180 + 30
            back_y = 110 + 540 - 38
            back_rect = pygame.Rect(back_x, back_y, 120, 25)
            if back_rect.collidepoint(mx, my):
                self.state = S_CASE_SELECT
                return

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.state = S_CASE_SELECT
            elif ev.key == pygame.K_RETURN:
                self._apply_prefs()
                self._start_ai_generate()

    def _apply_prefs(self):
        """将输入框内容解析为 ai_prefs"""
        self.ai_prefs["theme"] = self.ai_input
        pref = self.ai_pref_text.strip()
        if not pref:
            return
        # 确保 maker7 可导入
        ai_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ai")
        if ai_dir not in sys.path:
            sys.path.insert(0, ai_dir)
        from maker7 import CHARACTER_POOL, CRIME_POOL
        # 风格识别（支持更多风格）
        for kw, val in [("搞笑", "搞笑"), ("严肃", "严肃"), ("抽象", "抽象"),
                        ("恐怖", "恐怖"), ("温馨", "温馨"), ("悬疑", "悬疑"),
                        ("沙雕", "沙雕")]:
            if kw in pref:
                self.ai_prefs["style"] = val
        for kw, val in [("简单", "easy"), ("普通", "normal"), ("困难", "hard")]:
            if kw in pref:
                self.ai_prefs["difficulty"] = val
        for ch in CHARACTER_POOL:
            if ch in pref:
                self.ai_prefs["defendant"] = ch
                break
        # 罪名：优先匹配池内，否则将用户输入整段作为 crime_type
        crime_matched = False
        for cr in CRIME_POOL:
            if cr in pref:
                self.ai_prefs["crime_type"] = cr
                crime_matched = True
                break
        if not crime_matched:
            # 尝试从偏好文本中提取“罪名”相关信息
            # 如果用户输入里包含明显的罪名描述，直接作为 crime_type
            import re
            # 匹配 2-6 字中文词（可能是自定义罪名）
            m = re.search(r'[\u4e00-\u9fff]{2,6}', pref.replace(self.ai_prefs.get("defendant", ""), ""))
            if m:
                self.ai_prefs["crime_type"] = m.group()
        # 将完整偏好文本作为 custom_prompt 传给 maker7
        self.ai_prefs["custom_prompt"] = pref

    # ============================================================
    #   绘制 — AI 配置界面
    # ============================================================
    def _dr_ai_config(self, s):
        ticks = pygame.time.get_ticks()
        mouse = pygame.mouse.get_pos()
        t_sec = ticks / 1000.0

        # ---- 1. 背景 — 六边形网格 + 粒子 + 连线 ----
        s.fill((10, 14, 30))
        # 六边形网格
        hex_r = 35
        for row in range(-1, SH // hex_r + 2):
            for col in range(-1, int(SW / (hex_r * 1.7)) + 2):
                hx = col * hex_r * 1.73 + (row % 2) * hex_r * 0.865
                hy = row * hex_r * 1.5
                pts = []
                for a in range(6):
                    angle = math.radians(a * 60 - 30)
                    pts.append((hx + hex_r * 0.45 * math.cos(angle), hy + hex_r * 0.45 * math.sin(angle)))
                pygame.draw.polygon(s, (18, 24, 42), pts, 1)
        # 动态数据流横线
        for i in range(6):
            dy = 6 + i * 3
            dx = int((ticks * (0.25 + i * 0.08) + i * 250) % (SW + 250)) - 125
            dw = int(80 + 50 * math.sin(t_sec * 1.5 + i))
            da = int(25 + 18 * math.sin(t_sec * 2.5 + i * 0.6))
            line_surf = pygame.Surface((dw, 1), pygame.SRCALPHA)
            line_surf.fill((180, 140, 60, da))
            s.blit(line_surf, (dx, dy))
        # 粒子 + 连线
        particle_count = 15 if self.perf_mode else 40
        pts = []
        for i, p in enumerate(self.ai_bg_particles[:particle_count]):
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["x"] < 0: p["x"] = SW
            if p["x"] > SW: p["x"] = 0
            if p["y"] < 0: p["y"] = SH
            if p["y"] > SH: p["y"] = 0
            pulse = 0.5 + 0.5 * math.sin(t_sec * 2 + p["phase"])
            a = int(p["alpha"] * pulse)
            c = p["color"]
            pygame.draw.circle(s, (c[0], c[1], c[2], a), (int(p["x"]), int(p["y"])), p["size"])
            pts.append((p["x"], p["y"], a, c))
        # 粒子连线（金色/青色）
        if not self.perf_mode:
            for i in range(len(pts)):
                for j in range(i + 1, min(i + 3, len(pts))):
                    dx = pts[i][0] - pts[j][0]
                    dy = pts[i][1] - pts[j][1]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < 150:
                        la = int(min(pts[i][2], pts[j][2]) * (1 - dist / 150) * 0.25)
                        if la > 5:
                            lc = pts[i][3]
                            pygame.draw.line(s, (lc[0], lc[1], lc[2], la), (int(pts[i][0]), int(pts[i][1])),
                                           (int(pts[j][0]), int(pts[j][1])), 1)

        # ---- 2. 标题 — 多层发光 + 故障抖动 + 旋转装饰 ----
        title_text = "AI 案件生成"
        title_surf = self.f_huge.render(title_text, True, GOLD)
        title_rect = title_surf.get_rect(center=(SW // 2, 60))
        # 多层发光
        for layer in range(3):
            la = int(50 - layer * 15 + 30 * math.sin(t_sec * 3 + layer * 0.5))
            ls = self.f_huge.render(title_text, True, GOLD)
            ls.set_alpha(max(0, la))
            s.blit(ls, title_rect.move(0, layer * 2 + 1))
        # 故障效果
        glitch = math.sin(t_sec * 7) > 0.82
        if glitch:
            s.blit(title_surf, title_rect.move(_rand.randint(-2, 2), 0))
        s.blit(title_surf, title_rect)
        # 扫描线
        scan_w = int(200 + 80 * math.sin(t_sec * 1.5))
        scan_x = SW // 2 - scan_w // 2
        pygame.draw.line(s, GOLD, (scan_x, 88), (scan_x + scan_w, 88), 2)
        # 旋转装饰
        dc = (180, 150, 80)
        for idx, dx in enumerate([-240, 240]):
            cx = SW // 2 + dx
            rot = t_sec * (1.2 if idx == 0 else -1.2)
            for arm in range(4):
                angle = rot + arm * math.pi / 2
                x1 = cx + 6 * math.cos(angle)
                y1 = 60 + 6 * math.sin(angle)
                x2 = cx + 15 * math.cos(angle)
                y2 = 60 + 15 * math.sin(angle)
                pygame.draw.line(s, dc, (x1, y1), (x2, y2), 2)
            pygame.draw.circle(s, dc, (cx, 60), 4)

        # ---- 3. 面板 — 玻璃拟态 + 边缘流光 + 内部扫描线 ----
        panel_r = pygame.Rect(180, 110, 920, 540)
        panel_surf = pygame.Surface((panel_r.w, panel_r.h), pygame.SRCALPHA)
        panel_surf.fill((20, 30, 50, 220))
        s.blit(panel_surf, (panel_r.x, panel_r.y))
        # 流光边框
        flow = 0.5 + 0.5 * math.sin(t_sec * 1.2)
        br = int(190 + 45 * flow)
        border_c = (br, int(170 + 35 * flow), int(70 + 25 * flow))
        draw_rr_outline(s, border_c, panel_r, 12, 3)
        # 顶部内阴影线
        pygame.draw.line(s, (50, 65, 95), (panel_r.x + 20, panel_r.y + 2), (panel_r.right - 20, panel_r.y + 2), 1)
        # 四角装饰
        cl = 100
        corners = [
            (panel_r.x + 4, panel_r.y + 4, 1, 1),
            (panel_r.right - 14, panel_r.y + 4, -1, 1),
            (panel_r.x + 4, panel_r.bottom - 14, 1, -1),
            (panel_r.right - 14, panel_r.bottom - 14, -1, -1),
        ]
        for cx, cy, sx, sy in corners:
            pygame.draw.line(s, (cl, cl, cl), (cx, cy), (cx + 12 * sx, cy), 2)
            pygame.draw.line(s, (cl, cl, cl), (cx, cy), (cx, cy + 12 * sy), 2)
        # 面板内部扫描线
        scan_py = int(panel_r.y + 10 + (panel_r.h - 20) * ((t_sec * 0.3) % 1))
        pygame.draw.line(s, (60, 80, 120, 30), (panel_r.x + 10, scan_py), (panel_r.right - 10, scan_py), 1)

        # ---- 4. 输入框 — 终端风格 + 内部扫描线 + 聚焦流光 ----
        # 偏好输入
        dot_c = (220, 180, 90)
        pygame.draw.circle(s, dot_c, (228, 175), 4)
        s.blit(self.f_large.render("案件偏好", True, ORANGE), (240, 165))
        s.blit(self.f_tiny.render("可输入被告、罪名、风格、难度等，留空则随机", True, (100, 110, 130)), (240, 205))

        pref_box = pygame.Rect(240, 238, 800, 56)
        pref_active = (self.ai_input_active == "pref")
        ibg = (22, 32, 52) if pref_active else (18, 26, 42)
        draw_rr(s, ibg, pref_box, 8)
        if pref_active:
            fa = 0.5 + 0.5 * math.sin(t_sec * 4)
            fb = int(110 + 60 * fa)
            ibd = (fb, int(170 + 50 * fa), 255)
        else:
            ibd = (55, 70, 100)
        draw_rr_outline(s, ibd, pref_box, 8, 2)
        # 左侧竖线
        pygame.draw.line(s, ibd, (pref_box.x + 6, pref_box.y + 10), (pref_box.x + 6, pref_box.y + 46), 3)
        # 内部扫描线（仅聚焦时）
        if pref_active:
            scan_iy = int(pref_box.y + 8 + (pref_box.h - 16) * ((t_sec * 0.5) % 1))
            pygame.draw.line(s, (80, 140, 255, 25), (pref_box.x + 10, scan_iy), (pref_box.right - 10, scan_iy), 1)

        pref_display = self.ai_pref_text if (pref_active or self.ai_pref_text) else "如：坚果 偷窃阳光 搞笑 困难"
        tc = WHITE if (pref_active or self.ai_pref_text) else (60, 70, 90)
        show_pref = pref_display + (self.ime_composing if pref_active else "")
        s.blit(self.f_med.render(show_pref, True, tc), (pref_box.x + 18, pref_box.y + 14))

        if pref_active and ticks % 1000 < 500:
            cx = pref_box.x + 18 + self.f_med.size(show_pref)[0]
            pygame.draw.line(s, WHITE, (cx, pref_box.y + 12), (cx, pref_box.y + 44), 2)

        # 主题输入
        pygame.draw.circle(s, dot_c, (228, 322), 4)
        s.blit(self.f_large.render("主题关键词", True, ORANGE), (240, 312))
        s.blit(self.f_tiny.render("如：广场舞、奶茶、考试，可留空", True, (100, 110, 130)), (240, 352))

        theme_box = pygame.Rect(240, 378, 800, 56)
        theme_active = (self.ai_input_active == "theme")
        ibg2 = (22, 32, 52) if theme_active else (18, 26, 42)
        draw_rr(s, ibg2, theme_box, 8)
        if theme_active:
            fa2 = 0.5 + 0.5 * math.sin(t_sec * 4)
            fb2 = int(110 + 60 * fa2)
            ibd2 = (fb2, int(170 + 50 * fa2), 255)
        else:
            ibd2 = (55, 70, 100)
        draw_rr_outline(s, ibd2, theme_box, 8, 2)
        pygame.draw.line(s, ibd2, (theme_box.x + 6, theme_box.y + 10), (theme_box.x + 6, theme_box.y + 46), 3)
        if theme_active:
            scan_iy2 = int(theme_box.y + 8 + (theme_box.h - 16) * ((t_sec * 0.5 + 0.3) % 1))
            pygame.draw.line(s, (80, 140, 255, 25), (theme_box.x + 10, scan_iy2), (theme_box.right - 10, scan_iy2), 1)

        theme_display = self.ai_input if (theme_active or self.ai_input) else "点击输入主题..."
        tc2 = WHITE if (theme_active or self.ai_input) else (60, 70, 90)
        show_theme = theme_display + (self.ime_composing if theme_active else "")
        s.blit(self.f_med.render(show_theme, True, tc2), (theme_box.x + 18, theme_box.y + 14))

        if theme_active and ticks % 1000 < 500:
            cx = theme_box.x + 18 + self.f_med.size(show_theme)[0]
            pygame.draw.line(s, WHITE, (cx, theme_box.y + 12), (cx, theme_box.y + 44), 2)

        if self.ai_input_active:
            s.blit(self.f_tiny.render("Enter 确认    Esc 取消", True, GRAY),
                   self.f_tiny.render("Enter 确认    Esc 取消", True, GRAY)
                   .get_rect(center=(SW // 2, 448)))

        # ---- 5. 性能模式开关 — 滑块式（加发光）----
        target = 1.0 if self.perf_mode else 0.0
        self.perf_switch_anim += (target - self.perf_switch_anim) * 0.15
        track_x = SW // 2 - 120
        track_y = 460
        track_r = pygame.Rect(track_x, track_y, 60, 28)
        if self.perf_mode:
            track_bg = (50, 160, 70)
            track_brd = (100, 230, 120)
            # 发光
            glow_s = pygame.Surface((track_r.w + 8, track_r.h + 8), pygame.SRCALPHA)
            draw_rr(glow_s, (80, 200, 100, 40), pygame.Rect(0, 0, track_r.w + 8, track_r.h + 8), 16)
            s.blit(glow_s, (track_r.x - 4, track_r.y - 4))
        else:
            track_bg = (120, 60, 60)
            track_brd = (180, 120, 120)
        draw_rr(s, track_bg, track_r, 14)
        draw_rr_outline(s, track_brd, track_r, 14, 2)
        knob_x = track_x + 6 + int(self.perf_switch_anim * 26)
        knob_y = track_y + 3
        pygame.draw.circle(s, (240, 240, 240), (knob_x + 11, knob_y + 11), 11)
        pygame.draw.circle(s, (200, 200, 200), (knob_x + 11, knob_y + 11), 11, 2)
        perf_label = "性能模式"
        perf_status = "开启" if self.perf_mode else "关闭"
        perf_lbl_c = (100, 240, 120) if self.perf_mode else (220, 170, 170)
        s.blit(self.f_small.render(perf_label, True, GRAY), (track_x + 72, track_y + 3))
        s.blit(self.f_small.render(perf_status, True, perf_lbl_c), (track_x + 72, track_y + 20))

        # ---- 6. 开始生成按钮 — 多层发光 + 按下涟漪 ----
        start_btn = pygame.Rect(SW // 2 - 170, 510, 340, 68)
        hov = start_btn.collidepoint(mouse)
        # 多层脉冲发光
        for ring in range(2):
            pulse_b = 0.5 + 0.5 * math.sin(t_sec * (2.5 - ring * 0.5) + ring * math.pi)
            pb_a = int(30 + 25 * pulse_b)
            offset = (ring + 1) * 8
            pb_surf = pygame.Surface((start_btn.w + offset * 2, start_btn.h + offset * 2), pygame.SRCALPHA)
            draw_rr(pb_surf, (220, 60, 60, pb_a), pygame.Rect(0, 0, start_btn.w + offset * 2, start_btn.h + offset * 2), 14)
            s.blit(pb_surf, (start_btn.x - offset, start_btn.y - offset))
        if hov:
            glow_r = pygame.Rect(start_btn.x - 8, start_btn.y - 6, start_btn.w + 16, start_btn.h + 12)
            glow_surf = pygame.Surface((glow_r.w, glow_r.h), pygame.SRCALPHA)
            draw_rr(glow_surf, (230, 80, 80, 50), pygame.Rect(0, 0, glow_r.w, glow_r.h), 12)
            s.blit(glow_surf, (glow_r.x, glow_r.y))
        btn_bg = (240, 80, 80) if hov else (210, 55, 55)
        draw_rr(s, btn_bg, start_btn, 12)
        btn_brd = (250, 210, 120) if hov else (220, 180, 80)
        draw_rr_outline(s, btn_brd, start_btn, 12, 3)
        # 内部扫描线
        scan_by = int(start_btn.y + 10 + (start_btn.h - 20) * ((t_sec * 0.4) % 1))
        pygame.draw.line(s, (255, 200, 100, 30), (start_btn.x + 20, scan_by), (start_btn.right - 20, scan_by), 1)
        btn_txt = self.f_large.render("开始生成", True, WHITE)
        s.blit(btn_txt, btn_txt.get_rect(center=start_btn.center))

        # ---- 7. 返回 — 文字链接 ----
        back_text = "< 返回选案"
        back_x = panel_r.x + 30
        back_y = panel_r.bottom - 38
        back_hov = pygame.Rect(back_x, back_y, 120, 25).collidepoint(mouse)
        back_c = (190, 190, 210) if back_hov else (100, 110, 130)
        s.blit(self.f_small.render(back_text, True, back_c), (back_x, back_y))
        if back_hov:
            tw = self.f_small.size(back_text)[0]
            pygame.draw.line(s, back_c, (back_x, back_y + 22), (back_x + tw, back_y + 22), 1)

        # ---- 8. 底部状态栏 ----
        pygame.draw.line(s, (40, 50, 70), (40, SH - 38), (SW - 40, SH - 38), 1)
        s.blit(self.f_tiny.render("AI 司法档案系统 v2.0", True, (70, 80, 100)), (50, SH - 30))
        hint_txt = self.f_tiny.render("Enter 开始  |  Esc 返回", True, (70, 80, 100))
        s.blit(hint_txt, hint_txt.get_rect(right=SW - 50, top=SH - 30))


# ==================== 入口函数 ====================
def court_mode():
    game = CourtGame()
    return game.run()


if __name__ == "__main__":
    court_mode()
