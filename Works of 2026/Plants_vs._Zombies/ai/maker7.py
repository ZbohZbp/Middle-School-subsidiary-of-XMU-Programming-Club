

"""
maker7.py — 双轮异议案件生成器 (V2)
=====================================
通过 DeepSeek API 自动生成「逆转裁判」风格的法庭案件 JSON。
输出格式匹配 mode_5.py 的 CASES 结构，可直接被游戏引擎加载。

改进点 (V2):
  - API Key 支持环境变量 DEEPSEEK_API_KEY
  - 指数退避重试 + 自适应 temperature
  - 扩充角色池 / 罪名池 / 地点池
  - 难度控制 (简单 / 普通 / 困难)
  - 主题关键词输入
  - 进度回调 (供游戏引擎集成)
  - 兜底案件 (FALLBACK_CASE)
  - 更严格的逻辑校验
  - Prompt 精简，减少 Token 浪费
"""

import os
import json
import random
import re
import time
import requests
from typing import Optional, Dict, Any, List, Callable

# ======================= 配置区 =======================

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-4fede78b030a4130b5c522fd8ce1fa2f")
BASE_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
MAX_RETRIES = 4
TEMPERATURE = 0.75  # V2: 从 0.9 降低到 0.75，减少创意发散，增加逻辑一致性

# ---------- 案件存储配置 ----------
# 案件存储目录（每个案件保存为独立文件，避免覆盖）
CASES_DIR = "cases"
OUTPUT_FILE = os.path.join(CASES_DIR, "generated_case.json")

# ---------- 角色池（18 种，从 court_plant 素材库中精选） ----------
# 选择原则：性格多样、视觉辨识度高、适合逆转裁判式法庭的不同角色定位
CHARACTER_POOL = [
    "向日葵",   "豌豆射手", "坚果",     "樱桃炸弹",
    "大嘴花",   "寒冰射手", "路灯花",   "小喷菇",
    "毁灭菇",   "大喷菇",   "双发射手", "忧郁菇",
    "胆小菇",   "大蒜",     "南瓜头",   "高坚果",
    "地刺",     "杨桃",
]

# ---------- 素材库锁定（基于 court_plant 文件夹） ----------
# ASSET_MAP 记录每个角色在当前素材库中的立绘状态。
#   "ready"  : 已有 PNG 立绘，mode_5.py PORTRAIT_PATHS 已配置
#   "gif"    : 有 GIF 动图，转成 PNG 即可用
#   "missing": 无任何图片素材，需要制作
# gif_path 指向 court_plant/Plants/{English}/{MainGif}
_ASSET_BASE = "court_plant/Plants"
ASSET_MAP = {
    # ---- 18 个案件角色 ----
    "向日葵":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/SunFlower/SunFlower.gif",
                 "extra": ["SunFlower1.gif", "SunFlower2.gif"]},
    "豌豆射手": {"status": "gif", "gif_path": f"{_ASSET_BASE}/Peashooter/Peashooter.gif"},
    "坚果":     {"status": "gif", "gif_path": f"{_ASSET_BASE}/WallNut/WallNut.gif",
                 "extra": ["Wallnut_cracked1.gif", "Wallnut_cracked2.gif",
                           "WallNutRoll.gif", "HugeWallNutRoll.gif", "BoomWallNutRoll.gif"]},
    "樱桃炸弹": {"status": "gif", "gif_path": f"{_ASSET_BASE}/CherryBomb/CherryBomb.gif",
                 "extra": ["Boom.gif"]},
    "大嘴花":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/Chomper/Chomper.gif",
                 "extra": ["ChomperAttack.gif", "ChomperDigest.gif"]},
    "寒冰射手": {"status": "gif", "gif_path": f"{_ASSET_BASE}/SnowPea/SnowPea.gif"},
    "路灯花":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/Plantern/Plantern.gif"},
    "小喷菇":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/PuffShroom/PuffShroom.gif",
                 "extra": ["PuffShroomSleep.gif"]},
    "毁灭菇":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/DoomShroom/DoomShroom.gif",
                 "extra": ["BeginBoom.gif", "Sleep.gif", "Boom.png"]},
    "大喷菇":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/FumeShroom/FumeShroom.gif",
                 "extra": ["FumeShroomAttack.gif", "FumeShroomBullet.gif", "FumeShroomSleep.gif"]},
    "双发射手": {"status": "gif", "gif_path": f"{_ASSET_BASE}/Repeater/Repeater.gif"},
    "忧郁菇":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/GloomShroom/GloomShroom.gif",
                 "extra": ["GloomShroomAttack.gif", "GloomShroomBullet.gif", "GloomShroomSleep.gif"]},
    "胆小菇":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/ScaredyShroom/ScaredyShroom.gif",
                 "extra": ["ScaredyShroomCry.gif", "ScaredyShroomSleep.gif"]},
    "大蒜":     {"status": "gif", "gif_path": f"{_ASSET_BASE}/Garlic/Garlic.gif",
                 "extra": ["Garlic_body2.gif", "Garlic_body3.gif"]},
    "南瓜头":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/PumpkinHead/PumpkinHead.gif",
                 "extra": ["PumpkinHead1.gif", "PumpkinHead2.gif",
                           "Pumpkin_back.gif", "pumpkin_damage1.gif", "Pumpkin_damage2.gif"]},
    "高坚果":   {"status": "gif", "gif_path": f"{_ASSET_BASE}/TallNut/TallNut.gif",
                 "extra": ["TallnutCracked1.gif", "TallnutCracked2.gif"]},
    "地刺":     {"status": "gif", "gif_path": f"{_ASSET_BASE}/Spikeweed/Spikeweed.gif"},
    "杨桃":     {"status": "gif", "gif_path": f"{_ASSET_BASE}/Starfruit/Starfruit.gif",
                 "extra": ["Star.gif"]},
    # ---- 固定角色（检察官 & 法官，不参与案件但需要立绘） ----
    "辣椒":     {"status": "gif", "gif_path": f"{_ASSET_BASE}/Jalapeno/Jalapeno.gif",
                 "extra": ["JalapenoAttack.gif"]},
    "倭瓜":     {"status": "gif", "gif_path": f"{_ASSET_BASE}/Squash/Squash.gif",
                 "extra": ["SquashAttack.gif"]},
}

# 锁定角色池：仅包含有立绘素材的角色（ready + gif）
# generate_case(use_locked_pool=True) 时会用这个池子替代 CHARACTER_POOL
LOCKED_CHARACTER_POOL = [
    name for name, info in ASSET_MAP.items()
    if info["status"] in ("ready", "gif") and name not in ("辣椒", "倭瓜")
]

# 完整可用角色池（包含固定角色）
ALL_USABLE_CHARACTERS = LOCKED_CHARACTER_POOL + ["辣椒", "倭瓜"]


def get_active_pool(prefs: dict) -> list:
    """根据 prefs 决定使用哪个角色池。"""
    if prefs.get("use_locked_pool", True):
        return LOCKED_CHARACTER_POOL
    return CHARACTER_POOL


def print_asset_status():
    """打印素材状态报告，方便开发者查看哪些角色缺立绘。"""
    print("=" * 60)
    print("素材库立绘状态")
    print("=" * 60)
    ready, gif, missing = [], [], []
    for name, info in ASSET_MAP.items():
        s = info["status"]
        path = info.get("path", info.get("gif_path", "无"))
        label = f"  {name:8s}  [{s:7s}]  {path}"
        if s == "ready":
            ready.append(label)
        elif s == "gif":
            gif.append(label)
        else:
            missing.append(label)
    print(f"\n已有 PNG 立绘 ({len(ready)}):")
    for l in ready:
        print(l)
    print(f"\n有 GIF 动图，需转 PNG ({len(gif)}):")
    for l in gif:
        print(l)
    print(f"\n缺少素材 ({len(missing)}):")
    for l in missing:
        print(l)
    print(f"\n锁定池可用角色: {len(LOCKED_CHARACTER_POOL)} 个")
    print(f"完整角色池: {len(CHARACTER_POOL)} 个")
    print("=" * 60)

# ---------- 罪名池（参考示例，AI可自由发挥） ----------
CRIME_POOL = [
    # 经典
    "偷窃阳光", "偷吃包子", "擅离职守", "破坏草坪",
    "深夜狂奔", "造谣生事", "乱扔垃圾", "冒名顶替",
    "恶意挡路", "偷懒睡觉", "私藏弹药", "非法集会",
    "伪造文件", "偷看日记", "乱涂乱画", "霸占食堂",
    # 社交
    "网络暴力", "拉黑好友", "朋友圈屏蔽", "已读不回",
    "群聊踢人", "恶意举报", "背后说坏话",
    # 职场
    "抢功劳", "甩锅同事", "加班摸鱼", "带薪拉屎",
    "偷用别人杯子", "会议迟到", "谎报加班",
    # 生活
    "偷吃外卖", "半夜K歌", "占用停车位", "空调开太低",
    "乱翻别人东西", "不冲厕所", "借书不还",
    # 学术
    "论文抄袭", "考试作弊", "代写简历", "实验数据造假",
]

# ---------- 地点池（参考示例，AI可自由发挥） ----------
LOCATION_POOL = [
    "植物花园", "屋顶防线", "泳池前线", "浓雾墓地",
    "禅境温室", "蘑菇森林", "后院仓库", "指挥部",
    "阳光银行", "种子交易所", "训练场", "瞭望塔",
    "奶茶店", "图书馆", "食堂", "操场",
    "宿舍楼", "快递站", "健身房", "天台",
    "停车场", "会议室", "实验室", "广播站", "小卖部",
]

EVIDENCE_TYPES = [
    "监控记录", "证人笔录", "聊天记录", "工作记录", "特殊物证",
    "朋友圈截图", "外卖订单", "监控录像", "GPS定位记录",
    "通话记录", "银行流水", "邮件记录",
]

# ---------- 难度配置 ----------
DIFFICULTY_CONFIG = {
    "easy": {
        "label": "简单",
        "complexity": 1,
        "r1_testimonies": (4, 5),   # R1 证词数范围
        "r2_testimonies": (3, 4),
        "r3_testimonies": (3, 4),   # 新增 R3
        "r1_evidence": 3,           # R1 证据数
        "r2_evidence": 3,
        "r3_evidence": 3,           # 新增 R3
        "fail_tolerance": 5,        # 允许失败次数
    },
    "normal": {
        "label": "普通",
        "complexity": 2,
        "r1_testimonies": (5, 6),
        "r2_testimonies": (4, 5),
        "r3_testimonies": (4, 5),
        "r1_evidence": 3,
        "r2_evidence": 3,
        "r3_evidence": 3,
        "fail_tolerance": 3,
    },
    "hard": {
        "label": "困难",
        "complexity": 3,
        "r1_testimonies": (6, 8),
        "r2_testimonies": (5, 7),
        "r3_testimonies": (5, 6),
        "r1_evidence": 4,
        "r2_evidence": 4,
        "r3_evidence": 4,
        "fail_tolerance": 2,
    },
}

# ---------- 角色 → 席位/立绘 映射 ----------
SEAT_MAP = {
    "辣椒": ("lawyer", ""),
    "倭瓜": ("judge", ""),
}
PORTRAIT_MAP = {
    # 18 个案件角色 → 立绘 key（与 PORTRAIT_PATHS 对应）
    "向日葵":   "向日葵",
    "豌豆射手": "豌豆射手",
    "坚果":     "坚果",
    "樱桃炸弹": "樱桃炸弹",
    "大嘴花":   "大嘴花",
    "寒冰射手": "寒冰射手",
    "路灯花":   "路灯花",
    "小喷菇":   "小喷菇",
    "毁灭菇":   "毁灭菇",
    "大喷菇":   "大喷菇",
    "双发射手": "双发射手",
    "忧郁菇":   "忧郁菇",
    "胆小菇":   "胆小菇",
    "大蒜":     "大蒜",
    "南瓜头":   "南瓜头",
    "高坚果":   "高坚果",
    "地刺":     "地刺",
    "杨桃":     "杨桃",
}
DEFAULT_SEAT = "witness"

# ---------- 风格指令 ----------
STYLE_PROMPTS = {
    "搞笑": "整体风格搞笑夸张，台词要有梗，证人撒谎时要越描越黑。",
    "严肃": "整体风格严肃正经，像真正的法庭剧，台词要克制有力。",
    "抽象": "整体风格抽象荒诞，台词可以打破第四面墙，充满无厘头。",
    "恐怖": "整体风格阴森恐怖，台词要有压迫感，证人撒谎时令人毛骨愤然。",
    "温馨": "整体风格温暖治愈，即使有矛盾也充满人情味，结局让人感动。",
    "悬疑": "整体风格悬疑烧脑，线索层层嵌套，台词充满暗示和伏笔。",
    "沙雕": "整体风格极度沙雕，台词要充满椫子和废话文学，越离谱越好。",
}


# ======================= 工具函数 =======================

def call_ai(prompt: str,
            system_msg: str = None,
            temperature: float = TEMPERATURE,
            max_tokens: int = 1200) -> Optional[str]:
    """调用 DeepSeek API，返回文本内容。"""
    if system_msg is None:
        system_msg = (
            "你是一个专业的游戏案件编剧。你的输出必须且只能是一段合法的 JSON。"
            "不要输出任何解释文字、markdown 代码块标记、注释或其他非 JSON 内容。"
        )
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    try:
        resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=90)
        if resp.status_code != 200:
            print(f"  API 状态码异常: {resp.status_code} — {resp.text[:200]}")
            return None
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            print("  响应缺少 choices")
            return None
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            print("  content 为空")
            return None
        content = content.strip()
        # 清理 markdown 代码块（AI 常见坏习惯）
        content = re.sub(r'^```(?:json)?\s*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content)
        return content.strip()
    except requests.exceptions.Timeout:
        print("  请求超时 (90s)")
        return None
    except requests.exceptions.ConnectionError:
        print("  网络连接失败")
        return None
    except Exception as e:
        print(f"  请求异常: {e}")
        return None


def safe_json_parse(text: str) -> Optional[dict]:
    """安全解析 JSON，支持提取嵌入的数组/对象。"""
    if not text:
        return None
    # 直接尝试
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 尝试提取 JSON 数组
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    # 尝试提取 JSON 对象
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def retry_call(prompt: str,
               validator: Callable,
               step_name: str,
               max_retries: int = MAX_RETRIES,
               temperature: float = TEMPERATURE,
               max_tokens: int = 1200,
               prompt_modifier: Callable = None,
               progress_cb: Callable = None) -> dict:
    """带指数退避的重试调用。失败时逐步提高 temperature 打破重复输出。"""
    for attempt in range(1, max_retries + 1):
        current_prompt = prompt
        # 重试时修改 prompt 并微调 temperature
        current_temp = min(temperature + (attempt - 1) * 0.05, 1.0)
        if attempt > 1 and prompt_modifier:
            current_prompt = prompt_modifier(prompt, attempt)

        _report(progress_cb, step_name, f"第 {attempt} 次尝试...")
        text = call_ai(current_prompt, temperature=current_temp, max_tokens=max_tokens)

        if not text:
            wait = min(2 ** attempt, 16)
            _report(progress_cb, step_name, f"AI 返回空，等待 {wait}s...")
            time.sleep(wait)
            continue

        data = safe_json_parse(text)
        if not data:
            wait = min(2 ** (attempt - 1), 8)
            _report(progress_cb, step_name, f"JSON 解析失败，等待 {wait}s...")
            print(f"  原始返回: {text[:300]}...")
            time.sleep(wait)
            continue

        if validator(data):
            _report(progress_cb, step_name, "校验通过")
            return data

        _report(progress_cb, step_name, f"校验未通过 (attempt {attempt})")
        print(f"  返回: {json.dumps(data, ensure_ascii=False)[:300]}")

    raise RuntimeError(f"[{step_name}] 重试 {max_retries} 次后仍失败")


def _report(cb: Optional[Callable], step: str, msg: str):
    """统一的进度上报函数。"""
    if cb:
        try:
            cb(step, msg)
        except Exception:
            pass
    print(f"[{step}] {msg}")


def get_seat(speaker: str, defendant: str) -> str:
    """根据角色名确定席位。"""
    if speaker == defendant:
        return "defendant"
    if speaker in SEAT_MAP:
        return SEAT_MAP[speaker][0]
    return DEFAULT_SEAT


def get_portrait(speaker: str) -> str:
    """根据角色名确定立绘 key。"""
    return PORTRAIT_MAP.get(speaker, speaker)


# ======================= 校验函数 =======================

def validate_step1(data: dict, active_pool: list = None) -> bool:
    """校验案件基础信息。"""
    pool = active_pool or CHARACTER_POOL
    required = ("case_title", "defendant", "crime", "location")
    if not all(k in data for k in required):
        print("  缺少必需字段")
        return False
    # 被告检查（放宽：允许 AI 自由创建角色）
    # 不再强制要求被告必须在角色池内
    if len(data["crime"]) > 15:
        print(f"  罪名过长: {len(data['crime'])}字")
        return False
    if len(data.get("location", "")) > 10:
        print(f"  地点名过长")
        return False
    if len(data.get("case_title", "")) > 12:
        print(f"  标题过长: {len(data['case_title'])}字")
        return False
    return True


def validate_step2(data: dict, step1: dict, active_pool: list = None,
                   num_rounds: int = 3) -> bool:
    """校验三轮矛盾核心。"""
    pool = active_pool or CHARACTER_POOL
    if "contradictions" not in data or not isinstance(data["contradictions"], list):
        print("  缺少 contradictions 数组")
        return False
    if len(data["contradictions"]) != num_rounds:
        print(f"  需要 {num_rounds} 个矛盾点，实际 {len(data['contradictions'])} 个")
        return False

    valid_types = {"时间矛盾", "地点矛盾", "身份矛盾", "动机矛盾",
                   "逻辑矛盾", "行为矛盾", "关系矛盾"}
    defendant = step1["defendant"]
    witnesses = set()

    for i, c in enumerate(data["contradictions"]):
        for k in ("witness", "type", "surface_truth", "deep_truth"):
            if k not in c:
                print(f"  矛盾{i+1} 缺少字段: {k}")
                return False
        if c["witness"] == defendant:
            print(f"  矛盾{i+1} 证人不能是被告 ({defendant})")
            return False
        # 证人不在池中不再拒绝（允许 AI 创建新角色）
        if c["type"] not in valid_types:
            print(f"  矛盾{i+1} 类型无效: {c['type']} (警告，不拒绝)")
        if len(c.get("surface_truth", "")) < 5:
            print(f"  矛盾{i+1} surface_truth 太短")
            return False
        witnesses.add(c["witness"])

    if len(witnesses) < num_rounds:
        print(f"  {num_rounds}轮矛盾的证人必须全部不同")
        return False

    if "r1_cliffhanger" not in data or len(data.get("r1_cliffhanger", "")) < 3:
        print("  缺少 r1_cliffhanger 或太短")
        return False
    # 三轮需要 r2_cliffhanger
    if num_rounds >= 3:
        if "r2_cliffhanger" not in data or len(data.get("r2_cliffhanger", "")) < 3:
            print("  缺少 r2_cliffhanger 或太短")
            return False
    if "truth" not in data or len(data["truth"]) < 10:
        print("  缺少 truth 或太短")
        return False

    # 真凶检查
    rc = data.get("real_criminal", "")
    if rc == defendant:
        print("  真凶不能是被告")
        return False
    # 真凶不在池中不再拒绝（允许 AI 创建新角色）

    return True


def validate_step2_5(data: dict, step1: dict = None, step2: dict = None,
                     active_pool: list = None) -> bool:
    """校验嫌疑人档案。"""
    pool = active_pool or CHARACTER_POOL
    required = ("r1_misleading", "r2_misleading",
                 "r1_evidence_count", "r2_evidence_count", "suspects")
    if not all(k in data for k in required):
        print("  缺少必需字段")
        return False
    if not isinstance(data["r1_misleading"], list) or len(data["r1_misleading"]) < 1:
        print("  r1_misleading 不足")
        return False
    if not isinstance(data["r2_misleading"], list) or len(data["r2_misleading"]) < 1:
        print("  r2_misleading 不足")
        return False
    if not isinstance(data["suspects"], list) or len(data["suspects"]) < 3:
        print(f"  suspects 不足: {len(data.get('suspects', []))}")
        return False

    defendant = step1["defendant"] if step1 else None
    real_criminal = step2.get("real_criminal", "") if step2 else ""
    truth = step2.get("truth", "") if step2 else ""
    crime = step1.get("crime", "") if step1 else ""
    suspect_names = set()
    real_motive = ""
    for s in data["suspects"]:
        if not all(k in s for k in ("name", "role", "personality", "motive")):
            print("  suspect 缺少字段")
            return False
        suspect_names.add(s["name"])
        if s["name"] == real_criminal:
            real_motive = s.get("motive", "")

    # 必须包含被告和真凶
    if defendant and defendant not in suspect_names:
        print(f"  suspects 中缺少被告: {defendant}")
        return False
    if real_criminal and real_criminal not in suspect_names:
        print(f"  suspects 中缺少真凶: {real_criminal}")
        return False

    # 动机-真相一致性校验
    if truth and real_motive:
        truth_lower = truth.lower()
        motive_lower = real_motive.lower()
        # 检查明显矛盾的关键词对
        contradiction_pairs = [
            ("偷", "保护"), ("盗", "守护"), ("抢", "归还"),
            ("杀", "救"), ("陷害", "帮助"), ("撒谎", "诚实"),
        ]
        for bad, good in contradiction_pairs:
            if bad in truth_lower and good in motive_lower:
                print(f"  真凶动机与真相矛盾: 真相含'{bad}'但动机含'{good}'")
                return False

    if not (2 <= data["r1_evidence_count"] <= 5):
        print("  r1_evidence_count 超出范围")
        return False
    if not (2 <= data["r2_evidence_count"] <= 5):
        print("  r2_evidence_count 超出范围")
        return False
    return True


def _normalize_press(press_data):
    """
    将 AI 可能返回的各种 press 格式统一为 [{q, a, clue}, ...] 数组。
    返回标准化后的 press 列表，如果无法修复则返回 None。
    """
    # 已经是正确格式
    if isinstance(press_data, list):
        result = []
        for p in press_data:
            if isinstance(p, dict):
                # 检查是否是 {q, a, clue} 格式
                if all(k in p for k in ("q", "a", "clue")):
                    result.append(p)
                # 检查是否是 {type, text} 格式（错误格式，尝试转换）
                elif "type" in p and "text" in p:
                    # 尝试从 text 中提取 q/a/clue
                    text = p["text"]
                    if isinstance(text, str):
                        # 简单启发式：如果有问号可能是问题
                        if "?" in text or "？" in text:
                            result.append({"q": text, "a": "（证人沉默）", "clue": text})
                        else:
                            result.append({"q": "（追问）", "a": "（回答）", "clue": text})
        if result:
            return result
        return None

    # 是对象而非数组（如 {"q": "...", "a": "...", "clue": "..."}）
    if isinstance(press_data, dict):
        if all(k in press_data for k in ("q", "a", "clue")):
            return [press_data]
        return None

    return None


def validate_testimonies(data: list,
                         expected_witness: str = None,
                         defendant: str = None,
                         active_pool: list = None,
                         auto_fix: bool = True) -> bool:
    """校验证词列表。支持自动修复常见格式错误。"""
    pool = active_pool or CHARACTER_POOL
    if not isinstance(data, list) or len(data) < 3:
        print(f"  证词数量不足: {len(data) if isinstance(data, list) else 'N/A'}")
        return False

    contradiction_count = 0
    seen_ids = set()
    fixed_count = 0

    for t in data:
        if not all(k in t for k in ("id", "speaker", "text")):
            print(f"  证词缺少必需字段: {t.get('id', '?')}")
            return False

        # ID 唯一性
        if t["id"] in seen_ids:
            print(f"  证词 ID 重复: {t['id']}")
            return False
        seen_ids.add(t["id"])

        # 证词文本长度
        if len(t.get("text", "")) < 5:
            print(f"  证词 {t['id']} 文本太短")
            return False

        # 追问点 - 尝试自动修复格式问题
        press = t.get("press")
        if auto_fix and press is not None:
            normalized = _normalize_press(press)
            if normalized:
                if normalized != press:
                    fixed_count += 1
                t["press"] = normalized
                press = normalized

        if not isinstance(press, list) or len(press) < 1:
            print(f"  证词 {t['id']} 追问点不足")
            return False

        for p in press:
            if not isinstance(p, dict):
                print(f"  证词 {t['id']} press 项不是对象")
                return False
            if not all(k in p for k in ("q", "a", "clue")):
                print(f"  证词 {t['id']} 追问缺少字段，当前: {list(p.keys())}")
                return False
            if not isinstance(p.get("clue"), str):
                print(f"  证词 {t['id']} clue 必须是字符串")
                return False

        # 矛盾统计
        if t.get("is_contradiction"):
            contradiction_count += 1

    if fixed_count > 0:
        print(f"  自动修复 {fixed_count} 条证词的 press 格式")

    # 1-2 条矛盾
    if contradiction_count < 1 or contradiction_count > 2:
        print(f"  矛盾证词数应为 1-2，实际 {contradiction_count}")
        return False

    return True


def validate_evidence(data: list, min_count: int = 2) -> bool:
    """校验证据列表。"""
    if not isinstance(data, list) or len(data) < min_count:
        print(f"  证据数量不足: {len(data) if isinstance(data, list) else 'N/A'}")
        return False

    seen_ids = set()
    for ev in data:
        if not all(k in ev for k in ("id", "title", "type", "desc")):
            print(f"  证据缺少字段: {ev.get('id', '?')}")
            return False
        if ev["id"] in seen_ids:
            print(f"  证据 ID 重复: {ev['id']}")
            return False
        seen_ids.add(ev["id"])
        if ev["type"] not in EVIDENCE_TYPES:
            print(f"  证据 {ev['id']} 类型无效: {ev['type']}")
            return False
    return True


def validate_transition(data: dict) -> bool:
    """校验过渡台词。"""
    if not all(k in data for k in ("speaker", "text")):
        return False
    if len(data.get("text", "")) < 10:
        print("  过渡台词太短")
        return False
    return True


def validate_branch(data: list, min_lines: int = 3) -> bool:
    """校验分支台词。"""
    if not isinstance(data, list) or len(data) < min_lines:
        print(f"  分支台词不足: {len(data) if isinstance(data, list) else 'N/A'}")
        return False
    for line in data:
        if not all(k in line for k in ("speaker", "text")):
            print("  分支台词缺少 speaker/text")
            return False
    return True


# ======================= Prompt 构建 =======================

_SYS = (
    "你是一个专业的游戏案件编剧。你的输出必须且只能是一段合法的 JSON。"
    "不要输出任何解释文字、markdown 代码块标记、注释或其他非 JSON 内容。"
)


def _style_instruction(prefs: dict) -> str:
    """根据用户选择的风格返回对应的风格指令。"""
    style = prefs.get("style", "搞笑")
    return STYLE_PROMPTS.get(style, STYLE_PROMPTS["搞笑"])


# 随机主题词库（当用户没有输入主题时自动抽取）
_RANDOM_THEMES = [
    "神秘失窃", "背叛阴谋", "时间谜题", "身份伪造", "密室因杀",
    "诅咒传说", "毒药谋杀", "双重间谍", "记忆篡改", "宝藏争夺",
    "假死骗局", "魔法失控", "梦境入侵", "复仇计划", "禁忌实验",
    "诅咒宝物", "镜中世界", "时间倒流", "影子分身", "禁忌契约",
    "消失的证据", "被篡改的遗书", "地下拍卖", "神秘的邀请函",
    "被谁诅的生日", "失窃的奖杯", "神秘的访客", "破碎的不在场证明",
    "梦境杀人", "时间旅行者的困境", "双重身份", "记忆窃贼",
]

_RANDOM_HOOKS = [
    "案件要有一个意想不到的反转，",
    "案件背后隐藏着一段悲伤的往事，",
    "真正的动机出人意料，",
    "案件表面上简单但背后有复杂的阴谋，",
    "关键证据被巧妙地隐藏了，",
    "案件与多年前的一个秘密有关，",
]


def _theme_instruction(prefs: dict) -> str:
    """注入主题关键词。如果用户没有输入，自动随机生成一个。"""
    theme = prefs.get("theme", "")
    if theme:
        return f"案件主题围绕「{theme}」展开，围绕该主题自由发挥创意。"
    # 自动随机生成主题
    rand_theme = random.choice(_RANDOM_THEMES)
    rand_hook = random.choice(_RANDOM_HOOKS)
    return f"{rand_hook}案件主题围绕「{rand_theme}」展开。"


def _custom_prompt_instruction(prefs: dict) -> str:
    """注入玩家自定义偏好描述。"""
    custom = prefs.get("custom_prompt", "")
    if custom:
        return f"\n【玩家自定义要求】{custom}\n请尽量满足上述要求，自由发挥创意。"
    return ""


def build_step1_prompt(prefs: dict, active_pool: list = None) -> str:
    pool = active_pool or CHARACTER_POOL
    roles = "、".join(pool)
    crimes = "、".join(CRIME_POOL[:20]) + "等"
    locations = "、".join(LOCATION_POOL[:15]) + "等"
    extra = _theme_instruction(prefs)
    extra += _custom_prompt_instruction(prefs)
    extra += f"\n{_style_instruction(prefs)}"
    if prefs.get("defendant"):
        extra += f"\n被告必须是：{prefs['defendant']}"
    if prefs.get("crime_type"):
        extra += f"\n罪名必须使用：{prefs['crime_type']}"
    # 如果用户指定了罪名，不再展示罪名池
    crime_line = f"罪名必须使用：{prefs['crime_type']}。" if prefs.get("crime_type") else f"罪名参考：{crimes}（也可以自创罪名，要符合主题和角色）"
    # 角色锁定提示（仅对有立绘的角色保留）
    locked_hint = ""
    if active_pool:
        locked_hint = (
            f"\n\n【素材提示】必须使用以下角色（有立绘）：{roles}。"
            f"严禁创造角色池外的角色。"
        )
    return (
        f"生成一个法庭案件的基本信息，自由发挥创意。\n"
        f"角色必须从以下列表中选择：{roles}。严禁创造新的植物角色。\n"
        f"{crime_line}\n"
        f"地点参考：{locations}（也可以自创场景）。\n{extra}\n"
        f"{locked_hint}\n"
        f"输出纯JSON：\n"
        f'{{"case_title": "标题(<=8字)", "defendant": "角色", '
        f'"crime": "罪名(<=8字)", "location": "地点"}}'
    )


def build_step2_prompt(step1: dict, prefs: dict, active_pool: list = None,
                       num_rounds: int = 3) -> str:
    pool = active_pool or CHARACTER_POOL
    roles = "、".join(pool)
    real_extra = ""
    if prefs.get("real_criminal"):
        real_extra = f"\n真凶必须是：{prefs['real_criminal']}"

    # 构建每轮矛盾描述
    round_desc = ""
    for i in range(1, num_rounds + 1):
        if i < num_rounds:
            round_desc += (
                f"【第{i}轮矛盾】（{'表面' if i == 1 else '中间'}矛盾）\n"
                f"- 证人{i}证词有破绽，玩家指出后揭露部分真相，留下悬念\n\n"
            )
        else:
            round_desc += (
                f"【第{num_rounds}轮矛盾】（终极矛盾）\n"
                f"- 最终线索/证人登场，玩家指出后揭露完整真相，锁定真凶\n\n"
            )

    # 构建 cliffhanger 描述
    cliffhanger_desc = "- r1_cliffhanger：第一轮悬念（一句话）"
    if num_rounds >= 3:
        cliffhanger_desc += "\n- r2_cliffhanger：第二轮悬念（一句话）"

    # 构建 contradictions JSON 模板
    contra_template = []
    for i in range(1, num_rounds + 1):
        deep_desc = f"R{i}指向的深层真相" if i < num_rounds else "完整真相"
        contra_template.append(
            f'{{"witness": "R{i}证人", "type": "矛盾类型", '
            f'"surface_truth": "R{i}揭露的表面真相", '
            f'"deep_truth": "{deep_desc}"}}'
        )

    extra = _custom_prompt_instruction(prefs)
    return (
        f"基于案件生成「{num_rounds}轮异议」的核心矛盾设计，自由发挥创意。\n"
        f"被告：{step1['defendant']}，罪名：{step1['crime']}{real_extra}{extra}\n\n"
        f"这是需要玩家「{num_rounds}次异议」才能获胜的案件：\n\n"
        f"{round_desc}"
        f"要求：\n"
        f"- contradictions 数组恰好 {num_rounds} 个元素，{num_rounds}个证人必须不同\n"
        f"- 证人必须从以下列表中选择：[{roles}]，不能是被告({step1['defendant']})，严禁创造新角色\n"
        f"- type 自由设计矛盾类型，参考：时间矛盾/地点矛盾/身份矛盾/动机矛盾/逻辑矛盾/行为矛盾/关系矛盾\n"
        f"- truth：完整真相描述（50-100字，讲清谁干了什么、怎么被发现的）\n"
        f"{cliffhanger_desc}\n"
        f"- real_criminal：真凶，不能是被告，必须从 [{roles}] 中选择，严禁使用新角色\n\n"
        f"【素材提示】必须使用 [{roles}] 中的角色（有立绘），严禁引入角色池外的植物角色。\n\n"
        f"输出纯JSON：\n"
        f'{{"real_criminal": "真凶", "truth": "完整真相描述", '
        f'"r1_cliffhanger": "第一轮悬念", '
        + (f'"r2_cliffhanger": "第二轮悬念", ' if num_rounds >= 3 else '')
        + f'"contradictions": ['
        + ", ".join(contra_template)
        + "]}}"
    )


def build_step2_5_prompt(step1: dict, step2: dict, prefs: dict,
                         active_pool: list = None, num_rounds: int = 3) -> str:
    pool = active_pool or CHARACTER_POOL
    roles = "、".join(pool)

    # 构建每轮证人描述
    witness_desc = ""
    for i in range(num_rounds):
        witness_desc += f"R{i+1}矛盾证人：{step2['contradictions'][i]['witness']}\n"

    # 构建每轮误导线索和证据数量字段
    misleading_fields = []
    evidence_fields = []
    for i in range(1, num_rounds + 1):
        misleading_fields.append(f'"r{i}_misleading": ["误导1", "误导2"]')
        evidence_fields.append(f'"r{i}_evidence_count": 3')

    # 嫌疑人数量参考
    suspect_count = f"{num_rounds + 1}-{num_rounds + 2}"
    extra = _custom_prompt_instruction(prefs)

    truth = step2.get("truth", "")
    real_criminal = step2.get("real_criminal", "")

    return (
        f"设计案件的嫌疑人档案和叙事节奏，自由发挥创意。\n"
        f"被告：{step1['defendant']}，真凶：{real_criminal}\n"
        f"完整真相：{truth}\n"
        f"{witness_desc}\n"
        f"【关键约束】嫌疑人动机必须与完整真相逻辑一致！\n"
        f"- 真凶「{real_criminal}」的 motive 必须直接解释其为何犯下「{step1['crime']}」，"
        f"不能与真相矛盾（例如真相说是盗窃，动机就不能是'保护财产'）\n"
        f"- 其他嫌疑人的 motive 可以有嫌疑但最终应能被排除\n\n"
        f"要求：\n"
        f"- 案件共 {num_rounds} 轮异议，每轮至少 2 条误导线索\n"
        f"- 每轮 3-4 条证据\n"
        f"- suspects：{suspect_count} 个嫌疑人（必须包含被告「{step1['defendant']}」"
        f"和真凶「{real_criminal}」），每人有：\n"
        f"  - name：角色名（必须从 [{roles}] 中选择，严禁创造新角色）\n"
        f"  - role：身份/职业（5-10字）\n"
        f"  - personality：性格描述（10-20字）\n"
        f"  - motive：作案动机（10-20字，必须与真相逻辑一致）\n"
        f"  - 所有嫌疑人名字必须严格来自角色池，禁止出现类似'坚果墙''太阳花'等变体名称\n{extra}\n"
        f"输出纯JSON：\n"
        f'{{'
        + ", ".join(misleading_fields) + ", "
        + ", ".join(evidence_fields) + ", "
        + f'"suspects": ['
        f'{{"name": "角色", "role": "身份", '
        f'"personality": "性格", "motive": "动机"}}]}}'
    )


def build_testimonies_prompt(case_info: dict, phase_idx: int,
                             difficulty: dict = None,
                             active_pool: list = None,
                             prefs: dict = None) -> str:
    """生成证词 prompt。phase_idx: 0=第一阶段, 1=第二阶段。"""
    pool = active_pool or CHARACTER_POOL
    phase_num = phase_idx + 1
    c = case_info["contradictions"][phase_idx]
    defendant = case_info["defendant"]
    id_offset = case_info.get(f"r{phase_num}_id_offset", 0)
    misleading_key = f"r{phase_num}_misleading"
    misleading = case_info.get("structure", {}).get(misleading_key, [])

    # 难度控制证词数量
    if difficulty:
        min_t, max_t = difficulty.get(f"r{phase_num}_testimonies", (4, 6))
        count_hint = f"{min_t}-{max_t}"
    else:
        min_t, max_t = 4, 6
        count_hint = "4-6"

    extra_context = ""
    if phase_num == 2:
        extra_context = (
            f"\n\n【第二轮背景】\n"
            f"第一轮异议成功后揭露了：{case_info['contradictions'][0]['surface_truth']}\n"
            f"第一轮悬念：{case_info.get('r1_cliffhanger', '事情没那么简单')}\n"
            f"第二轮是更深入的新线索和新证词。"
        )

    sample_id = f"T{id_offset + 1:02d}"
    contra_id = f"T{id_offset + 3:02d}"
    
    # 角色参考列表
    roles = "、".join(pool[:10]) + "等"
    extra = _custom_prompt_instruction(prefs) if prefs else ""

    return (
        f"为第{phase_num}阶段生成证词列表（{count_hint}条），自由发挥创意。\n\n"
        f"案件信息：\n"
        f"- 被告：{defendant}（{case_info['crime']}）\n"
        f"- 本轮矛盾证人：{c['witness']}\n"
        f"- 本轮矛盾类型：{c['type']}\n"
        f"- 本轮表面真相：{c['surface_truth']}\n"
        f"- 误导线索：{json.dumps(misleading, ensure_ascii=False)}"
        f"{extra_context}\n{extra}\n\n"
        f"【证词要求】\n"
        f"1. id 从 {sample_id} 开始递增（T01、T02、T03...）\n"
        f"2. speaker 必须使用案件已有角色或以下列表中的角色：{roles}。严禁引入新角色。\n"
        f"   注意：法官固定为'倭瓜'，检察官固定为'辣椒'，禁止使用'检察官''法官'等通用名称作为speaker。\n"
        f"3. text 是证词内容（15-30字）\n"
        f"4. 每条证词必须有 1-2 个追问点（press）：\n"
        f"   - q：追问问题\n"
        f"   - a：证人回答（15-25字）\n"
        f"   - clue：线索描述（字符串，5-15字。无线索时写空字符串\"\"，不要写\"无\"）\n"
        f"5. 恰好 1-2 条证词的 is_contradiction 为 true，其余 false\n"
        f"6. 矛盾证词必须有 1 个追问的 clue 为非空字符串\n"
        f"7. 整体风格要有趣，撒谎时有微妙不合理\n\n"
        f"输出纯JSON数组：\n"
        f'[{{"id": "{sample_id}", "speaker": "角色名", '
        f'"text": "证词内容", "is_contradiction": false, '
        f'"press": [{{"q": "追问问题", "a": "回答", "clue": ""}}]}}, '
        f'{{"id": "{contra_id}", "speaker": "{c["witness"]}", '
        f'"text": "含矛盾的证词", "is_contradiction": true, '
        f'"press": [{{"q": "追问", "a": "回答", "clue": "关键线索"}}]}}]'
    )


def build_phase_complete_prompt(case_info: dict, phase_idx: int,
                                 difficulty: dict = None,
                                 active_pool: list = None,
                                 prefs: dict = None) -> str:
    """
    【V2 核心优化】为第 phase_idx 轮同时生成：证词 + 证据 + 异议映射。
    所有内容在一个 prompt 中生成，确保逻辑自洽。
    """
    phase_num = phase_idx + 1
    c = case_info["contradictions"][phase_idx]
    defendant = case_info["defendant"]
    id_offset = case_info.get(f"r{phase_num}_id_offset", 0)
    pool = active_pool or CHARACTER_POOL
    roles = "、".join(pool)

    # 难度控制
    if difficulty:
        min_t, max_t = difficulty.get(f"r{phase_num}_testimonies", (4, 6))
        ev_count = difficulty.get(f"r{phase_num}_evidence", 3)
    else:
        min_t, max_t = 4, 6
        ev_count = 3

    # 误导线索
    misleading_key = f"r{phase_num}_misleading"
    misleading = case_info.get("structure", {}).get(misleading_key, [])

    # 轮次背景
    extra_context = ""
    if phase_num == 2:
        extra_context = (
            f"\n\n【第二轮背景】\n"
            f"第一轮异议成功后揭露了：{case_info['contradictions'][0]['surface_truth']}\n"
            f"第一轮悬念：{case_info.get('r1_cliffhanger', '事情没那么简单')}\n"
            f"第二轮是更深入的新线索和新证词。"
        )
    elif phase_num == 3:
        extra_context = (
            f"\n\n【第三轮背景】\n"
            f"前两轮已揭露：{case_info['contradictions'][0]['surface_truth']}；"
            f"{case_info['contradictions'][1]['surface_truth']}\n"
            f"第三轮是终极真相揭露。"
        )

    sample_id = f"T{id_offset + 1:02d}"
    contra_id = f"T{id_offset + 3:02d}"
    # 证据ID也要跨轮递增，避免E01/E02重复
    ev_id_offset = phase_idx * 10  # R1: E01-E09, R2: E11-E19, R3: E21-E29
    ev_start = f"E{ev_id_offset + 1:02d}"
    ev_types = "、".join(EVIDENCE_TYPES)
    extra = _custom_prompt_instruction(prefs) if prefs else ""

    return (
        f"为第{phase_num}阶段生成完整的证词、证据和异议映射关系。\n\n"
        f"【案件信息】\n"
        f"- 被告：{defendant}（{case_info['crime']}）\n"
        f"- 本轮矛盾证人：{c['witness']}\n"
        f"- 本轮矛盾类型：{c['type']}\n"
        f"- 表面真相：{c['surface_truth']}\n"
        f"- 深层真相：{c.get('deep_truth', '')}\n"
        f"- 误导线索：{json.dumps(misleading, ensure_ascii=False)}"
        f"{extra_context}\n"
        f"{extra}\n\n"
        f"【角色限制——严格遵守】\n"
        f"- 所有 speaker 必须是以下角色之一：{roles}\n"
        f"- 严禁创造角色池外的名字（如'坚果墙''太阳花''土豆雷'等）\n"
        f"- 检察官固定为'辣椒'，法官固定为'倭瓜'\n\n"
        f"【第一部分：证词列表（{min_t}-{max_t}条）】\n"
        f"1. id 从 {sample_id} 开始递增\n"
        f"2. 恰好 1-2 条证词的 is_contradiction 为 true\n"
        f"   - 矛盾证词必须由证人{c['witness']}说出\n"
        f"   - 矛盾证词的内容必须包含一个可被证据直接反驳的具体陈述\n"
        f"   - 矛盾类型：{c['type']}。证词内容必须符合这个矛盾类型\n"
        f"     * 时间矛盾：证词说某个时间做了A，但实际那个时间在B\n"
        f"     * 地点矛盾：证词说在某个地点，但实际在另一个地点\n"
        f"     * 身份矛盾：证词说看到了某人，但实际是另一个人\n"
        f"     * 行为矛盾：证词说做了某事，但实际没做或做了相反的事\n"
        f"     * 逻辑矛盾：证词中的陈述自相矛盾或违反常识\n"
        f"3. 每条证词 text 15-30字\n"
        f"4. 每条证词必须有 press 字段，press 是包含 1-2 个对象的数组\n"
        f"   每个 press 对象必须严格包含三个字段：q（追问问题）、a（证人回答）、clue（关键线索）\n"
        f"   示例格式：\"press\": [{{\"q\": \"你当时在哪里？\", \"a\": \"我在花园。\", \"clue\": \"监控显示你当时在仓库\"}}]\n"
        f"5. 矛盾证词的追问 clue 必须非空\n"
        f"6. 整体风格有趣，撒谎时有微妙不合理\n\n"
        f"【第二部分：证据列表（{ev_count}条）】\n"
        f"1. id 从 {ev_start} 开始递增（第{phase_num}轮专用，不要和其他轮重复）\n"
        f"2. E01 是关键证据，必须直接、明确地反驳矛盾证词中的具体陈述\n"
        f"   - 证据描述必须包含与证词直接冲突的事实（时间/地点/人物/行为）\n"
        f"   - 玩家读完证据描述后，能立刻意识到'这和证词说的不一样'\n"
        f"3. 其他证据提供补充信息或部分误导\n"
        f"4. type 参考：{ev_types}（也可自创）\n"
        f"5. title 简短（2-6字），desc 详细（25-45字）\n"
        f"6. 严禁：证据支持证词却被标为反驳；证据和证词说的是两回事\n\n"
        f"【第三部分：异议映射关系】\n"
        f"1. 只有证据能直接、明确反驳证词时，才能建立对应\n"
        f"2. 矛盾证词必须有至少1个直接反驳的证据\n"
        f"3. 每个 reason 必须具体说明冲突点（如'证词说在A地，但监控显示在B地'）\n"
        f"4. 总共 2-5 个对应关系，不要把所有证据配对到同一条证词\n\n"
        f'输出纯JSON：{{"testimonies": [...], "evidence": [...], "valid_objections": [...]}}'
    )


def build_evidence_prompt(case_info: dict, phase_idx: int,
                          difficulty: dict = None,
                          testimonies: list = None,
                          prefs: dict = None) -> str:
    """【保留兼容】单独生成证据的 prompt。"""
    phase_num = phase_idx + 1
    c = case_info["contradictions"][phase_idx]
    if difficulty:
        count = difficulty.get(f"r{phase_num}_evidence", 3)
    else:
        count = case_info.get("structure", {}).get(f"r{phase_num}_evidence_count", 3)

    clues_context = ""
    if testimonies:
        clue_items = []
        for t in testimonies:
            if t.get("press"):
                for p in t["press"]:
                    clue = p.get("clue", "")
                    if clue and clue != "无":
                        clue_items.append(f"  - {t['speaker']}追问线索：{clue}")
        if clue_items:
            clues_context = f"\n已揭露的追问线索：\n" + "\n".join(clue_items) + "\n"

    contra_testimonies = [t for t in (testimonies or []) if t.get("is_contradiction")]
    contra_context = ""
    if contra_testimonies:
        contra_context = "\n【本轮矛盾证词（必须用证据直接反驳）】\n"
        for t in contra_testimonies:
            contra_context += f"- {t['id']} {t['speaker']}: \"{t['text']}\"\n"
            for p in t.get("press", []):
                if p.get("clue"):
                    contra_context += f"  追问线索: {p['clue']}\n"

    ev_types = "、".join(EVIDENCE_TYPES)
    extra = _custom_prompt_instruction(prefs) if prefs else ""
    return (
        f"为第{phase_num}阶段生成证据列表（{count}条）。\n\n"
        f"案件信息：\n"
        f"- 被告：{case_info['defendant']}（{case_info['crime']}）\n"
        f"- 本轮矛盾证人：{c['witness']}\n"
        f"- 本轮矛盾类型：{c['type']}\n"
        f"- 表面真相：{c['surface_truth']}\n"
        f"- 深层真相：{c.get('deep_truth', '')}\n"
        f"{contra_context}"
        f"{clues_context}\n"
        f"【证据设计要求——必须严格遵守】\n"
        f"1. E01 是关键证据，必须直接、明确地反驳矛盾证词中的具体陈述\n"
        f"   - 证据描述必须包含与证词直接冲突的事实（时间/地点/人物/行为）\n"
        f"   - 玩家读完证据描述后，能立刻意识到'这和证词说的不一样'\n"
        f"2. 其他证据提供补充信息，可以部分误导但不能逻辑混乱\n"
        f"3. 每条证据的 desc 必须自洽，不能和案件设定矛盾\n"
        f"4. type 参考：{ev_types}（也可自创）\n"
        f"5. title 简短（2-6字），desc 详细（25-45字）\n"
        f"6. 严禁出现以下逻辑错误：\n"
        f"   - 证据支持证词却被标为反驳\n"
        f"   - 证据和证词说的是两回事（如证词说A时间，证据说B地点）\n"
        f"   - 证据描述含糊，无法判断是否与证词冲突\n{extra}\n"
        f"输出数组：\n"
        f'[{{"id": "E01", "title": "证据名", "type": "类型", "desc": "详细描述"}}, ...]'
    )


def build_objection_mapping_prompt(testimonies: list, evidence: list,
                                     case_info: dict, phase_idx: int) -> str:
    """构建异议对应关系 prompt。在证词+证据都生成后单独调用。"""
    phase_num = phase_idx + 1
    defendant = case_info.get("defendant", "")
    crime = case_info.get("crime", "")
    contradictions = case_info.get("contradictions", [])
    c = contradictions[phase_idx] if phase_idx < len(contradictions) else {}

    # 列出证词（标注矛盾）
    test_lines = []
    for t in testimonies:
        contra_mark = " ⚠️矛盾" if t.get("is_contradiction") else ""
        test_lines.append(
            f'{t["id"]}: {t["speaker"]} — "{t["text"]}"{contra_mark}'
        )
    test_str = "\n".join(test_lines)

    # 列出证据
    ev_lines = []
    for ev in evidence:
        ev_lines.append(f'{ev["id"]}: {ev["title"]} — {ev["desc"]}')
    ev_str = "\n".join(ev_lines)

    # 矛盾背景
    contra_info = ""
    if c:
        contra_info = (
            f"\n本轮矛盾类型：{c.get('type', '未知')}\n"
            f"表面真相：{c.get('surface_truth', '')}\n"
        )

    return (
        f"根据以下第{phase_num}阶段的证词和证据，确定「异议对应关系」。\n"
        f"被告：{defendant}（{crime}）\n"
        f"{contra_info}\n"
        f"【证词】\n{test_str}\n\n"
        f"【证据】\n{ev_str}\n\n"
        f"【核心规则——必须严格遵守】\n"
        f"1. 只有证据描述能直接、明确反驳证词内容时，才能建立对应关系\n"
        f"2. '直接反驳'的标准：证据中的事实与证词中的陈述在时间上冲突、"
        f"地点上冲突、人物身份上冲突、或行为描述上冲突\n"
        f"3. 如果证据只是'不支持'证词但不能明确反驳，不要建立对应\n"
        f"4. 如果证据描述和证词说的是两回事（如证词说时间A，证据说地点B），不要建立对应\n"
        f"5. 每个reason必须具体说明冲突点（如'证词说在A地，但监控显示在B地'）\n"
        f"6. 矛盾证词（标⚠️的）必须有至少1个直接反驳的证据\n"
        f"7. 非矛盾证词如果有明确反驳证据，也可列出（但非必须）\n"
        f"8. 总共2-5个对应关系，不要把所有证据配对到同一条证词\n\n"
        f"【示例——正确的对应关系】\n"
        f"证词：'我昨晚9点在北门值班' → 证据：'监控显示该植物昨晚9点在仓库' → 地点冲突\n"
        f"证词：'我亲眼看到 defendant 偷东西' → 证据：'充能记录显示证人当时在温室无法离开' → 行动能力冲突\n\n"
        f"【示例——错误的对应关系】\n"
        f"证词：'我晚上在睡觉' → 证据：'监控拍到该植物在睡觉' → 这是支持不是反驳！\n"
        f"证词：'时间是午夜12点' → 证据：'阳光在11点被领取' → 说的是不同事情，不构成直接反驳\n\n"
        f"输出纯JSON数组：\n"
        f'[{{"testimony_id": "T03", "evidence_id": "E01", '
        f'"reason": "证词说X，但证据显示Y"}}]'
    )


def validate_objection_mapping(data: list, testimonies: list,
                                evidence: list) -> bool:
    """校验异议对应关系。"""
    if not isinstance(data, list) or len(data) < 2:
        print(f"  异议对应不足: {len(data) if isinstance(data, list) else 'N/A'}")
        return False

    t_ids = {t["id"] for t in testimonies}
    e_ids = {e["id"] for e in evidence}
    contra_tids = {t["id"] for t in testimonies if t.get("is_contradiction")}

    seen = set()
    has_contra_mapping = False

    for item in data:
        if not all(k in item for k in ("testimony_id", "evidence_id", "reason")):
            print("  异议对应缺少字段")
            return False

        tid = item["testimony_id"]
        eid = item["evidence_id"]

        if tid not in t_ids:
            print(f"  testimony_id 无效: {tid}")
            return False
        if eid not in e_ids:
            print(f"  evidence_id 无效: {eid}")
            return False

        key = (tid, eid)
        if key in seen:
            print(f"  重复对应: {tid}-{eid}")
            return False
        seen.add(key)

        if tid in contra_tids:
            has_contra_mapping = True

        if len(item.get("reason", "")) < 3:
            print(f"  reason 太短: {item.get('reason', '')}")
            return False

    # 矛盾证词必须有至少1个对应
    if contra_tids and not has_contra_mapping:
        print("  矛盾证词没有对应的异议映射")
        return False

    return True


def build_transition_prompt(case_info: dict, phase_idx: int = 0,
                             objection_mappings: list = None) -> str:
    c = case_info["contradictions"][phase_idx]
    phase_num = phase_idx + 1

    # 异议映射上下文（如果有的话）
    mapping_info = ""
    if objection_mappings:
        lines = []
        for m in objection_mappings:
            lines.append(f"  - 证据{m['evidence_id']}反驳{m['testimony_id']}：{m.get('reason', '')}")
        mapping_info = f"\n本阶段异议成功的关键逻辑：\n" + "\n".join(lines) + "\n"

    # 下一阶段证人（如果有的话）
    next_info = ""
    if phase_idx + 1 < len(case_info["contradictions"]):
        next_witness = case_info["contradictions"][phase_idx + 1]["witness"]
        next_info = f"\n下一阶段证人：{next_witness}\n"

    return (
        f"写第{phase_num}阶段异议成功后，证人改口/反转的过渡台词。\n"
        f"这是连接第{phase_num}阶段和第{phase_num+1}阶段的桥梁。\n\n"
        f"被告：{case_info['defendant']}\n"
        f"本阶段证人：{c['witness']}\n"
        f"揭露的表面真相：{c['surface_truth']}\n"
        f"深层真相：{c.get('deep_truth', '')}\n"
        f"{mapping_info}"
        f"{next_info}"
        f"悬念钩子：{case_info.get('r1_cliffhanger', '事情没那么简单') if phase_idx == 0 else '真相即将揭晓'}\n\n"
        f"要求：\n"
        f"- speaker：改口的角色（通常是本阶段证人）\n"
        f"- text：改口台词（30-60字），要体现出异议证据击中了要害，证人被迫承认部分事实，但试图用新的辩解搪塞\n"
        f"- 搞笑风格，越描越黑\n\n"
        f'输出纯JSON：{{"speaker": "角色名", "text": "改口台词"}}'
    )


def build_judge_comment_prompt(case_info: dict, phase_idx: int) -> str:
    phase_num = phase_idx + 1
    c = case_info["contradictions"][phase_idx]
    if phase_idx == 1:
        context = (
            f"这是最终阶段，真相完整揭露。"
            f"完整真相：{case_info.get('truth', c['deep_truth'])}"
        )
    else:
        context = (
            f"这是第一阶段，只揭露部分真相。"
            f"悬念：{case_info.get('r1_cliffhanger', '')}"
        )
    return (
        f"写第{phase_num}阶段异议成功后的法官评论（judge_comment）。\n"
        f"{context}\n\n"
        f"被告：{case_info['defendant']}\n"
        f"矛盾证人：{c['witness']}\n"
        f"矛盾类型：{c['type']}\n\n"
        f"要求：一段话（30-60字），总结本阶段的矛盾发现，语气严肃但搞笑。\n"
        f'输出纯JSON：{{"comment": "评论内容"}}'
    )


# ---------- 分支台词 Prompt ----------

def _build_r1_success_prompt(case_data: dict) -> str:
    valid_chars = "、".join(ALL_USABLE_CHARACTERS)
    return (
        f"写第一轮异议成功后的台词（5-7句）。这是「部分反转」，不是最终胜利。\n\n"
        f"第一轮证人：{case_data['contradictions'][0]['witness']}\n"
        f"表面真相：{case_data['contradictions'][0]['surface_truth']}\n"
        f"悬念钩子：{case_data.get('r1_cliffhanger', '事情没那么简单')}\n\n"
        f"【台词结构】\n"
        f"1. 证人慌张（1句） 2. 试图辩解（1-2句） 3. 被迫承认部分真相（1-2句）\n"
        f"4. 留下悬念（1句） 5. 检察官震惊（1句） 6. 法官宣布休庭继续调查（1句）\n\n"
        f"【角色限制】speaker 必须是以下角色之一：{valid_chars}。\n"
        f"检察官固定为'辣椒'，法官固定为'倭瓜'。严禁使用角色池外的名字。\n"
        f"每句15-25字，搞笑风格。\n"
        f'输出纯JSON数组：[{{"speaker": "角色", "text": "台词", '
        f'"emotion": "nervous/angry/normal/shocked"}}, ...]'
    )


def _build_r1_fail_prompt(case_data: dict) -> str:
    valid_chars = "、".join(ALL_USABLE_CHARACTERS)
    return (
        f"写第一轮异议失败后的台词（4-5句）。\n"
        f"被告：{case_data['defendant']}，"
        f"证人：{case_data['contradictions'][0]['witness']}\n\n"
        f"1. 检察官嘲笑（1句） 2. 证人松口气（1句）\n"
        f"3. 检察官强调嫌疑（1-2句） 4. 法官宣布继续（1句）\n\n"
        f"【角色限制】speaker 必须是以下角色之一：{valid_chars}。\n"
        f"检察官固定为'辣椒'，法官固定为'倭瓜'。严禁使用角色池外的名字。\n"
        f"每句15-25字，搞笑。\n"
        f'输出纯JSON数组：[{{"speaker": "角色", "text": "台词", '
        f'"emotion": "angry/normal/smug"}}, ...]'
    )


def _build_r2_success_prompt(case_data: dict) -> str:
    valid_chars = "、".join(ALL_USABLE_CHARACTERS)
    truth = case_data.get('truth', case_data['contradictions'][1]['deep_truth'])
    return (
        f"写第二轮异议成功后的最终反转台词（6-8句）。全案高潮！\n"
        f"真凶：{case_data['real_criminal']}，被告：{case_data['defendant']}\n"
        f"完整真相：{truth}\n\n"
        f"1. R2证人慌张（1句） 2. R1证人也慌了/指认（1句） 3. 真凶嘴硬（1句）\n"
        f"4. 真凶崩溃承认（1-2句） 5. 检察官震惊（1句）\n"
        f"6. 被告反应（1句） 7. 法官宣判（1-2句）\n\n"
        f"【角色限制】speaker 必须是以下角色之一：{valid_chars}。\n"
        f"检察官固定为'辣椒'，法官固定为'倭瓜'。严禁使用角色池外的名字。\n"
        f"每句15-25字，搞笑。\n"
        f'输出纯JSON数组：[{{"speaker": "角色", "text": "台词", '
        f'"emotion": "nervous/shocked/angry/relieved/normal"}}, ...]'
    )


def _build_r2_fail_prompt(case_data: dict) -> str:
    valid_chars = "、".join(ALL_USABLE_CHARACTERS)
    return (
        f"写第二轮异议失败后的最终失败台词（4-6句）。\n"
        f"被告：{case_data['defendant']}，"
        f"真凶（未被揭露）：{case_data['real_criminal']}\n\n"
        f"1. 检察官嘲笑两次失败（1句） 2. 总结陈词（1-2句）\n"
        f"3. 真凶偷笑（1句） 4. 法官宣判有罪（1-2句）\n\n"
        f"【角色限制】speaker 必须是以下角色之一：{valid_chars}。\n"
        f"检察官固定为'辣椒'，法官固定为'倭瓜'。严禁使用角色池外的名字。\n"
        f"每句15-25字，搞笑。\n"
        f'输出纯JSON数组：[{{"speaker": "角色", "text": "台词", '
        f'"emotion": "angry/smug/normal/sad"}}, ...]'
    )


def _build_r3_success_prompt(case_data: dict) -> str:
    valid_chars = "、".join(ALL_USABLE_CHARACTERS)
    truth = case_data.get('truth', case_data['contradictions'][2]['deep_truth'] if len(case_data.get('contradictions', [])) >= 3 else '')
    return (
        f"写第三轮异议成功后的终极真相揭露台词（8-10句）。全案最终高潮！\n"
        f"真凶：{case_data['real_criminal']}，被告：{case_data['defendant']}\n"
        f"完整真相：{truth}\n\n"
        f"1. R3证人崩溃（1句） 2. R2证人指认真凶（1句） 3. R1证人附和（1句）\n"
        f"4. 真凶最终崩溃承认（2句） 5. 检察官震惊道歉（1句）\n"
        f"6. 被告反应（1句） 7. 法官宣判无罪（1-2句） 8. 全场反应（1句）\n\n"
        f"【角色限制】speaker 必须是以下角色之一：{valid_chars}。\n"
        f"检察官固定为'辣椒'，法官固定为'倭瓜'。\n"
        f"R3证人必须用真实角色名（如{case_data['contradictions'][2]['witness']}），R2证人用{case_data['contradictions'][1]['witness']}，R1证人用{case_data['contradictions'][0]['witness']}。\n"
        f"严禁使用'全体''R2证人''R1证人''土豆雷'等角色池外的名字。\n"
        f"每句15-25字，搞笑，高潮感。\n"
        f'输出纯JSON数组：[{{"speaker": "角色", "text": "台词", '
        f'"emotion": "nervous/shocked/angry/relieved/normal/crying"}}, ...]'
    )


def _build_r3_fail_prompt(case_data: dict) -> str:
    valid_chars = "、".join(ALL_USABLE_CHARACTERS)
    return (
        f"写第三轮异议失败后的最终失败台词（5-7句）。\n"
        f"被告：{case_data['defendant']}，"
        f"真凶（未被揭露）：{case_data['real_criminal']}\n\n"
        f"1. 检察官嘲笑三次失败（1句） 2. 总结陈词（1-2句）\n"
        f"3. 真凶得意偷笑（1句） 4. 证人们困惑（1句）\n"
        f"5. 法官宣判有罪（1-2句） 6. 被告绝望（1句）\n\n"
        f"【角色限制】speaker 必须是以下角色之一：{valid_chars}。\n"
        f"检察官固定为'辣椒'，法官固定为'倭瓜'。严禁使用角色池外的名字。\n"
        f"每句15-25字，搞笑，悲壮感。\n"
        f'输出纯JSON数组：[{{"speaker": "角色", "text": "台词", '
        f'"emotion": "angry/smug/normal/sad/despair"}}, ...]'
    )


def build_all_branches_prompt(case_data: dict, num_rounds: int = 2) -> str:
    """
    【V2 优化】一次生成所有分支台词（成功/失败）。
    将 6 次 API 调用合并为 1 次。
    """
    valid_chars = "、".join(ALL_USABLE_CHARACTERS)
    defendant = case_data['defendant']
    real_criminal = case_data['real_criminal']
    truth = case_data.get('truth', '')

    # 构建每轮信息
    rounds_info = ""
    for i in range(num_rounds):
        c = case_data['contradictions'][i]
        rounds_info += (
            f"\n【第{i+1}轮】\n"
            f"- 证人：{c['witness']}\n"
            f"- 类型：{c['type']}\n"
            f"- 表面真相：{c['surface_truth']}\n"
            f"- 深层真相：{c.get('deep_truth', '')}\n"
        )

    # 构建各分支的结构要求
    branches_structure = ""
    for i in range(1, num_rounds + 1):
        is_final = (i == num_rounds)
        if is_final:
            branches_structure += (
                f"\n'{f'r{i}_success'}': 最终胜利台词（6-8句）。\n"
                f"  结构：R{i}证人慌张→R{i-1}证人指认→真凶嘴硬→崩溃承认→"
                f"检察官震惊→被告反应→法官宣判无罪\n"
                f"\n'{f'r{i}_fail'}': 最终失败台词（4-6句）。\n"
                f"  结构：检察官嘲笑→总结陈词→真凶偷笑→法官宣判有罪→被告绝望\n"
            )
        else:
            branches_structure += (
                f"\n'{f'r{i}_success'}': 部分反转台词（5-7句）。\n"
                f"  结构：证人慌张→试图辩解→被迫承认部分真相→"
                f"留下悬念→检察官震惊→法官宣布继续调查\n"
                f"\n'{f'r{i}_fail'}': 阶段失败台词（4-5句）。\n"
                f"  结构：检察官嘲笑→证人松口气→检察官强调嫌疑→法官宣布继续\n"
            )

    return (
        f"一次性生成案件所有分支台词（成功/失败）。\n\n"
        f"被告：{defendant}，真凶：{real_criminal}\n"
        f"完整真相：{truth}\n"
        f"{rounds_info}\n\n"
        f"【角色限制——严格遵守】\n"
        f"- speaker 必须是以下角色之一：{valid_chars}\n"
        f"- 检察官固定为'辣椒'，法官固定为'倭瓜'\n"
        f"- 严禁使用'全体''R2证人''R1证人''土豆雷'等角色池外的名字\n"
        f"- 每句15-25字，搞笑风格\n\n"
        f"【各分支结构要求】{branches_structure}\n\n"
        f"【输出格式要求——严格遵守】\n"
        f"- 每条台词对象必须包含两个字段：speaker（说话角色）和 text（台词内容）\n"
        f"- 严禁使用 content 字段，必须使用 text 字段\n"
        f"- 示例格式：{{\"speaker\": \"辣椒\", \"text\": \"哈哈哈，真相大白了！\"}}\n\n"
        f'输出纯JSON：{{"branches": {{'
        f'"r1_success": [{{"speaker": "角色", "text": "台词"}}, ...], '
        f'"r1_fail": [{{"speaker": "角色", "text": "台词"}}, ...], '
        f'"r2_success": [{{"speaker": "角色", "text": "台词"}}, ...], '
        f'"r2_fail": [{{"speaker": "角色", "text": "台词"}}, ...]'
        + (', "r3_success": [...], "r3_fail": [...]' if num_rounds >= 3 else '')
        + f'}}}}'
    )


# ======================= AI 自校验 =======================

def build_phase_validation_prompt(testimonies: list, evidence: list,
                                   valid_objections: list, contradiction: dict,
                                   active_pool: list = None) -> str:
    """
    构建 AI 自校验 prompt，让 AI 检查生成的阶段数据是否有逻辑问题。
    """
    pool = active_pool or CHARACTER_POOL
    valid_names = set(pool) | {"辣椒", "倭瓜"}

    # 收集所有角色名
    speakers = set()
    for t in testimonies:
        if t.get("speaker"):
            speakers.add(t["speaker"])

    # 收集矛盾证词
    contra_texts = []
    for t in testimonies:
        if t.get("is_contradiction"):
            contra_texts.append(f"- {t['id']} {t['speaker']}: \"{t['text']}\"")

    # 收集证据
    ev_texts = []
    for ev in evidence:
        ev_texts.append(f"- {ev['id']} {ev['title']}: {ev['desc']}")

    # 收集映射
    mapping_texts = []
    for m in valid_objections:
        mapping_texts.append(
            f"- {m['evidence_id']} → {m['testimony_id']}: {m.get('reason', '')}"
        )

    invalid_speakers = [s for s in speakers if s not in valid_names]

    return (
        f"请检查以下法庭游戏阶段数据的逻辑一致性。\n\n"
        f"【矛盾证词】\n" + "\n".join(contra_texts) + "\n\n"
        f"【证据】\n" + "\n".join(ev_texts) + "\n\n"
        f"【异议映射】\n" + "\n".join(mapping_texts) + "\n\n"
        f"【角色池】{', '.join(pool)}，辣椒（检察官），倭瓜（法官）\n\n"
        f"【检查项】\n"
        f"1. 矛盾证词是否包含可被证据明确反驳的具体陈述？\n"
        f"2. 每个映射关系的证据描述是否直接、明确地反驳对应证词？\n"
        f"3. 是否有证据'支持'证词却被标为反驳的逻辑错误？\n"
        f"4. 是否有证据和证词说的是'两回事'（如证词说时间A，证据说地点B）？\n"
        f"5. 所有 speaker 是否在角色池内？\n"
        f"   当前发现的无效角色：{invalid_speakers if invalid_speakers else '无'}\n\n"
        f"【输出格式】\n"
        f'{{"valid": true/false, "issues": ["问题1描述", "问题2描述", ...]}}\n'
        f"- valid=true 表示没有严重问题\n"
        f"- valid=false 时 issues 必须列出所有发现的问题\n"
        f"输出纯JSON，不要任何解释文字。"
    )


def ai_validate_phase(testimonies: list, evidence: list,
                       valid_objections: list, contradiction: dict,
                       active_pool: list = None,
                       progress_cb: Callable = None) -> tuple:
    """
    使用 AI 检查阶段数据的逻辑一致性。
    返回: (is_valid: bool, issues: list)
    """
    prompt = build_phase_validation_prompt(
        testimonies, evidence, valid_objections, contradiction, active_pool
    )

    _report(progress_cb, "AI校验", "正在检查逻辑一致性...")

    text = call_ai(prompt, temperature=0.3, max_tokens=800)
    if not text:
        _report(progress_cb, "AI校验", "AI 校验调用失败，跳过")
        return True, []

    data = safe_json_parse(text)
    if not data:
        _report(progress_cb, "AI校验", "AI 校验返回格式错误，跳过")
        return True, []

    is_valid = data.get("valid", True)
    issues = data.get("issues", [])

    if not is_valid and issues:
        _report(progress_cb, "AI校验", f"发现问题: {len(issues)} 个")
        for issue in issues:
            print(f"  [AI校验] {issue}")
        return False, issues

    _report(progress_cb, "AI校验", "逻辑检查通过")
    return True, []


# ======================= Prompt modifier =======================

def modifier_emphasize(prompt: str, attempt: int) -> str:
    """重试时追加格式强调，打破 AI 重复输出。"""
    return (
        prompt
        + f"\n\n【重要提醒-第{attempt}次】请只输出一个 JSON 数组。"
          f"不要输出任何解释文字。不要输出 markdown 代码块。"
          f"输出必须是合法的 JSON 数组。"
    )


def modifier_json_object(prompt: str, attempt: int) -> str:
    """重试时强调输出 JSON 对象（非数组）。"""
    return (
        prompt
        + f"\n\n【重要提醒-第{attempt}次】请只输出一个 JSON 对象（不是数组）。"
          f"不要输出任何解释文字或 markdown。"
    )


# ======================= 兜底案件 =======================

FALLBACK_CASE = {
    "id": "fallback_00001",
    "title": "阳光失踪案",
    "type": "偷窃阳光",
    "location": "植物花园",
    "complexity": 2,
    "suspects": [
        {"name": "向日葵", "role": "阳光生产者", "personality": "开朗活泼",
         "motive": "工作压力大，想休假"},
        {"name": "坚果", "role": "防线守卫", "personality": "沉默寡言",
         "motive": "觉得阳光分配不公"},
        {"name": "豌豆射手", "role": "前线战士", "personality": "冲动好战",
         "motive": "想用阳光升级武器"},
    ],
    "phases": [
        {
            "testimonies": [
                {"id": "T01", "speaker": "向日葵", "seat": "witness",
                 "portrait": "向日葵",
                 "text": "我昨晚9点就回房间休息了，一整晚都没出门。",
                 "is_contradiction": False,
                 "press": [{"q": "有没有听到异常声响？",
                            "a": "大概11点听到走廊有很沉重的脚步声。",
                            "clue": "11点有沉重脚步声"}]},
                {"id": "T02", "speaker": "豌豆射手", "seat": "witness",
                 "portrait": "豌豆射手",
                 "text": "我训练到10点就回去了，之后什么都没看到。",
                 "is_contradiction": False,
                 "press": [{"q": "对其他嫌疑人有了解吗？",
                            "a": "坚果最近老抱怨阳光分配不公平。",
                            "clue": "坚果抱怨分配不公"}]},
                {"id": "T03", "speaker": "坚果", "seat": "defendant",
                 "portrait": "坚果",
                 "text": "我昨晚一直在北门值班，从没离开过值班岗位。",
                 "is_contradiction": True,
                 "press": [{"q": "有人能证明你一直在北门吗？",
                            "a": "值班表上有我名字……但值班表可以自己改。",
                            "clue": "值班表可自改"}]},
                {"id": "T04", "speaker": "向日葵", "seat": "witness",
                 "portrait": "向日葵",
                 "text": "我记得昨晚走廊确实有响动，但不确定是谁。",
                 "is_contradiction": False,
                 "press": [{"q": "你能听出是谁的脚步声吗？",
                            "a": "脚步声很重，像是比较沉的植物。",
                            "clue": "脚步声沉重"}]},
            ],
            "evidence": [
                {"id": "E01", "title": "监控记录", "type": "监控记录",
                 "desc": "昨晚11点有一个圆形身影出现在阳光仓库附近。"},
                {"id": "E02", "title": "泥土脚印", "type": "特殊物证",
                 "desc": "仓库门口发现圆形压痕，深度表明是较重的植物留下的。"},
                {"id": "E03", "title": "值班表", "type": "工作记录",
                 "desc": "坚果昨晚值班区域在北门。但值班表可以自行更改。"},
            ],
            "valid_objections": [
                {"testimony_id": "T03", "evidence_id": "E01", "reason": "值班记录显示坚果昨晚在北门值班，与证词中'从没离开过'矛盾"},
                {"testimony_id": "T03", "evidence_id": "E02", "reason": "泥土脚印与坚果的圆形体型不符"},
                {"testimony_id": "T03", "evidence_id": "E03", "reason": "值班表可自行更改，不能作为不在场证明"},
            ],
            "judge_comment": "坚果声称从未离开北门，但证据清楚地表明他去过仓库。第一处矛盾已确认！",
        },
        {
            "testimonies": [
                {"id": "T05", "speaker": "坚果", "seat": "defendant",
                 "portrait": "坚果",
                 "text": "好吧……我确实离开过北门，但那是去巡逻！",
                 "is_contradiction": True,
                 "press": [{"q": "巡逻？有申请记录吗？",
                            "a": "巡逻不需要申请……呃，我是临时起意的。",
                            "clue": "巡逻无申请"}]},
                {"id": "T06", "speaker": "豌豆射手", "seat": "witness",
                 "portrait": "豌豆射手",
                 "text": "巡逻路线是固定的，北门区域不包括仓库那边。",
                 "is_contradiction": False,
                 "press": [{"q": "你确定巡逻不经过仓库？",
                            "a": "当然，巡逻路线图写得清清楚楚。",
                            "clue": "仓库不在巡逻路线"}]},
                {"id": "T07", "speaker": "向日葵", "seat": "witness",
                 "portrait": "向日葵",
                 "text": "我记得巡逻队要经过花园中心，但仓库在西边，差得远呢。",
                 "is_contradiction": False,
                 "press": [{"q": "坚果说他是去巡逻，你怎么看？",
                            "a": "巡逻不可能走到仓库那边去的……他撒谎。",
                            "clue": "巡逻不经过仓库"}]},
            ],
            "evidence": [
                {"id": "E01", "title": "巡逻路线图", "type": "工作记录",
                 "desc": "标准巡逻路线从北门出发，经花园中心返回，全程不经过西侧仓库区域。"},
                {"id": "E02", "title": "监控记录", "type": "监控记录",
                 "desc": "昨晚11点圆形身影出现在仓库附近。"},
                {"id": "E03", "title": "泥土脚印", "type": "特殊物证",
                 "desc": "仓库门口圆形压痕，深度表明是较重的植物。"},
            ],
            "valid_objections": [
                {"testimony_id": "T05", "evidence_id": "E01", "reason": "巡逻路线图显示仓库不在巡逻范围内"},
                {"testimony_id": "T05", "evidence_id": "E02", "reason": "监控显示圆形身影在仓库，但坚果声称在北门"},
                {"testimony_id": "T05", "evidence_id": "E03", "reason": "泥土脚印与坚果体型特征不符"},
            ],
            "judge_comment": "坚果的巡逻借口同样站不住脚。巡逻路线根本不经过仓库，真相只有一个！",
        },
    ],
    "transition": {
        "speaker": "坚果", "seat": "defendant", "portrait": "坚果",
        "text": "好吧……我承认我说谎了。我确实离开过北门……但我那是去巡逻！而且我发现仓库门已经开着了！",
    },
    "truth": "坚果利用职务之便，在值班期间偷溜到仓库盗走了阳光。先是用虚假的值班记录掩盖行踪，被揭穿后又编造巡逻借口。",
    "brief_comment": "双阶段案件：B模式，需两轮异议。R1推翻地点矛盾，R2揭露身份矛盾。",
    "_meta": {
        "real_criminal": "坚果",
        "r1_cliffhanger": "坚果承认离开了北门，但声称是去巡逻。",
        "contradictions": [
            {"witness": "坚果", "type": "地点矛盾",
             "surface_truth": "坚果离开过北门",
             "deep_truth": "坚果去仓库偷了阳光"},
            {"witness": "坚果", "type": "身份矛盾",
             "surface_truth": "巡逻借口不成立",
             "deep_truth": "坚果利用职务之便盗窃阳光"},
        ],
        "branches": {
            "r1_success": [], "r1_fail": [],
            "r2_success": [], "r2_fail": [],
        },
        "difficulty": "normal",
        "fail_tolerance": 3,
    },
}


# ======================= 主流程 =======================

def _generate_phase_complete(skeleton: dict, phase_idx: int, difficulty: dict,
                              active_pool: list, prefs: dict,
                              progress_cb: Callable = None) -> dict:
    """
    【V2】使用合并 prompt 一次性生成某轮的证词+证据+映射。
    如果 AI 校验发现问题，自动重试一次。
    """
    phase_num = phase_idx + 1
    _report(progress_cb, f"Step3-{phase_num}", f"正在生成第{phase_num}阶段完整数据...")

    # 第一次生成
    phase_data = retry_call(
        build_phase_complete_prompt(skeleton, phase_idx, difficulty, active_pool, prefs),
        lambda d: _validate_phase_complete(d, skeleton, phase_idx, active_pool),
        f"Step3-{phase_num}完整生成",
        temperature=TEMPERATURE, max_tokens=2500,
        prompt_modifier=modifier_emphasize,
        progress_cb=progress_cb,
    )

    testimonies = phase_data.get("testimonies", [])
    evidence = phase_data.get("evidence", [])
    valid_objections = phase_data.get("valid_objections", [])

    # 强制修正证据 ID 为跨轮递增（无论 AI 返回什么）
    ev_id_offset = phase_idx * 10  # R1:1, R2:11, R3:21
    old_to_new = {}
    for idx, ev in enumerate(evidence):
        old_id = ev.get("id", f"E{idx+1:02d}")
        new_id = f"E{ev_id_offset + idx + 1:02d}"
        if old_id != new_id:
            old_to_new[old_id] = new_id
            ev["id"] = new_id

    # 同步修正映射中的证据 ID
    if old_to_new:
        for vo in valid_objections:
            eid = vo.get("evidence_id", "")
            if eid in old_to_new:
                vo["evidence_id"] = old_to_new[eid]

    # 处理证词（添加 seat/portrait）
    defendant = skeleton["defendant"]
    for t in testimonies:
        if not t.get("is_contradiction"):
            t["is_contradiction"] = False
        t["seat"] = get_seat(t["speaker"], defendant)
        t["portrait"] = get_portrait(t["speaker"])

    # AI 自校验
    contradiction = skeleton["contradictions"][phase_idx]
    is_valid, issues = ai_validate_phase(
        testimonies, evidence, valid_objections,
        contradiction, active_pool, progress_cb
    )

    # 如果校验失败，用 issues 反馈重试一次
    if not is_valid and issues:
        _report(progress_cb, f"Step3-{phase_num}", f"发现问题，正在修正...")
        feedback = "\n".join(f"- {issue}" for issue in issues)
        retry_prompt = (
            build_phase_complete_prompt(skeleton, phase_idx, difficulty, active_pool, prefs)
            + f"\n\n【修正要求】上一轮生成存在以下问题，请修正后重新输出：\n{feedback}\n"
        )
        phase_data = retry_call(
            retry_prompt,
            lambda d: _validate_phase_complete(d, skeleton, phase_idx, active_pool),
            f"Step3-{phase_num}修正",
            temperature=TEMPERATURE, max_tokens=2500,
            prompt_modifier=modifier_emphasize,
            progress_cb=progress_cb,
        )
        testimonies = phase_data.get("testimonies", [])
        evidence = phase_data.get("evidence", [])
        valid_objections = phase_data.get("valid_objections", [])
        for t in testimonies:
            if not t.get("is_contradiction"):
                t["is_contradiction"] = False
            t["seat"] = get_seat(t["speaker"], defendant)
            t["portrait"] = get_portrait(t["speaker"])

    print(f"Step3-{phase_num}: {len(testimonies)} 条证词, {len(evidence)} 条证据, {len(valid_objections)} 个映射")
    return {
        "testimonies": testimonies,
        "evidence": evidence,
        "valid_objections": valid_objections,
    }


def _validate_phase_complete(data: dict, skeleton: dict, phase_idx: int,
                              active_pool: list) -> bool:
    """校验合并生成的阶段数据。"""
    if not isinstance(data, dict):
        print("  阶段数据不是字典")
        return False

    testimonies = data.get("testimonies", [])
    evidence = data.get("evidence", [])
    valid_objections = data.get("valid_objections", [])

    if not testimonies or not evidence:
        print("  证词或证据为空")
        return False

    # 校验证词
    defendant = skeleton["defendant"]
    witness = skeleton["contradictions"][phase_idx]["witness"]
    if not validate_testimonies(testimonies, witness, defendant, active_pool):
        return False

    # 校验证据
    if not validate_evidence(evidence):
        return False

    # 校验映射
    if not validate_objection_mapping(valid_objections, testimonies, evidence):
        return False

    return True


def generate_case(prefs: dict,
                  progress_cb: Callable = None) -> dict:
    """
    【V2】生成一个双轮/三轮异议案件。
    优化：合并证词+证据+映射生成，合并分支台词，增加AI自校验。

    参数:
      prefs: 用户偏好字典
      progress_cb: 进度回调 (step_name: str, message: str) -> None

    返回: 匹配 mode_5.py CASES 结构的 dict
    """
    # 解析难度
    diff_key = prefs.get("difficulty", "normal")
    difficulty = DIFFICULTY_CONFIG.get(diff_key, DIFFICULTY_CONFIG["normal"])

    # 解析角色池
    active_pool = get_active_pool(prefs)
    _report(progress_cb, "Init",
            f"角色池 ({len(active_pool)}): {', '.join(active_pool)}")

    try:
        # ---- Step 1: 案件基础 ----
        _report(progress_cb, "Step1", "正在生成案件基础信息...")
        step1 = retry_call(
            build_step1_prompt(prefs, active_pool),
            lambda d: validate_step1(d, active_pool),
            "Step1",
            max_tokens=300, progress_cb=progress_cb,
        )
        print(f"Step1: {json.dumps(step1, ensure_ascii=False)}")

        # ---- Step 2: 矛盾核心 ----
        _report(progress_cb, "Step2", "正在构建矛盾体系...")
        step2 = retry_call(
            build_step2_prompt(step1, prefs, active_pool),
            lambda d: validate_step2(d, step1, active_pool),
            "Step2", max_tokens=800, progress_cb=progress_cb,
        )
        print(f"Step2: {json.dumps(step2, ensure_ascii=False)}")

        # ---- Step 2.5: 嫌疑人档案 ----
        _report(progress_cb, "Step2.5", "正在设计嫌疑人档案...")
        step2_5 = retry_call(
            build_step2_5_prompt(step1, step2, prefs, active_pool),
            lambda d: validate_step2_5(d, step1, step2, active_pool),
            "Step2.5", max_tokens=800, progress_cb=progress_cb,
        )
        print(f"Step2.5: {json.dumps(step2_5, ensure_ascii=False)}")

        # 确定轮数
        num_rounds = len(step2.get("contradictions", []))
        if num_rounds < 2:
            num_rounds = 2
        print(f"轮数: {num_rounds}")

        # ---- 构建骨架 ----
        defendant = step1["defendant"]
        skeleton = {
            "case_title": step1["case_title"],
            "defendant": defendant,
            "crime": step1["crime"],
            "location": step1.get("location", random.choice(LOCATION_POOL)),
            "real_criminal": step2["real_criminal"],
            "truth": step2["truth"],
            "r1_cliffhanger": step2["r1_cliffhanger"],
            "contradictions": step2["contradictions"],
            "structure": step2_5,
            "r1_id_offset": 0,
        }

        # ---- Step 3: 证词 ----
        def _gen_testimonies(phase_idx):
            _report(progress_cb, f"Step3-{phase_idx+1}T", f"正在生成第{phase_idx+1}阶段证词...")
            tests = retry_call(
                build_testimonies_prompt(skeleton, phase_idx, difficulty, active_pool, prefs),
                lambda d: validate_testimonies(d, skeleton["contradictions"][phase_idx]["witness"],
                                                defendant, active_pool),
                f"Step3-{phase_idx+1}T", max_tokens=1200,
                prompt_modifier=modifier_emphasize,
                progress_cb=progress_cb,
            )
            for t in tests:
                if not t.get("is_contradiction"):
                    t["is_contradiction"] = False
                t["seat"] = get_seat(t["speaker"], defendant)
                t["portrait"] = get_portrait(t["speaker"])
            return tests

        r1_test = _gen_testimonies(0)
        max_r1_id = max((int(t["id"][1:]) for t in r1_test if t["id"].startswith("T")), default=0)
        skeleton["r2_id_offset"] = max_r1_id

        r2_test = _gen_testimonies(1)
        max_r2_id = max((int(t["id"][1:]) for t in r2_test if t["id"].startswith("T")), default=max_r1_id)
        skeleton["r3_id_offset"] = max_r2_id

        r3_test = []
        if num_rounds >= 3 and len(step2.get("contradictions", [])) >= 3:
            r3_test = _gen_testimonies(2)

        # ---- Step 4: 证据 ----
        def _gen_evidence(phase_idx, tests):
            _report(progress_cb, f"Step4-{phase_idx+1}E", f"正在生成第{phase_idx+1}阶段证据...")
            ev = retry_call(
                build_evidence_prompt(skeleton, phase_idx, difficulty, tests, prefs),
                validate_evidence, f"Step4-{phase_idx+1}E",
                max_tokens=800,
                prompt_modifier=modifier_emphasize,
                progress_cb=progress_cb,
            )
            # 强制修正证据 ID 为跨轮递增
            ev_id_offset = phase_idx * 10
            for idx, item in enumerate(ev):
                item["id"] = f"E{ev_id_offset + idx + 1:02d}"
            return ev

        r1_ev = _gen_evidence(0, r1_test)
        r2_ev = _gen_evidence(1, r2_test)
        r3_ev = []
        if r3_test:
            r3_ev = _gen_evidence(2, r3_test)

        # ---- Step 4.5: 异议映射 ----
        def _gen_mapping(phase_idx, tests, ev):
            _report(progress_cb, f"Step4.5-{phase_idx+1}M", f"正在生成第{phase_idx+1}阶段映射...")
            mapping = retry_call(
                build_objection_mapping_prompt(tests, ev, skeleton, phase_idx),
                lambda d: validate_objection_mapping(d, tests, ev),
                f"Step4.5-{phase_idx+1}M", max_tokens=600,
                prompt_modifier=modifier_emphasize,
                progress_cb=progress_cb,
            )
            return mapping

        r1_valid = _gen_mapping(0, r1_test, r1_ev)
        r2_valid = _gen_mapping(1, r2_test, r2_ev)
        r3_valid = []
        if r3_test and r3_ev:
            r3_valid = _gen_mapping(2, r3_test, r3_ev)

        # ---- Step 5a: 过渡台词 ----
        _report(progress_cb, "Step5a", "正在编写过渡台词...")
        r1_transition = retry_call(
            build_transition_prompt(skeleton, 0, r1_valid),
            validate_transition, "Step5a-过渡R1",
            temperature=TEMPERATURE, max_tokens=400,
            prompt_modifier=modifier_json_object,
            progress_cb=progress_cb,
        )
        r1_transition["seat"] = get_seat(r1_transition["speaker"], defendant)
        r1_transition["portrait"] = get_portrait(r1_transition["speaker"])

        r2_transition = retry_call(
            build_transition_prompt(skeleton, 1, r2_valid),
            validate_transition, "Step5a-过渡R2",
            temperature=TEMPERATURE, max_tokens=400,
            prompt_modifier=modifier_json_object,
            progress_cb=progress_cb,
        )
        r2_transition["seat"] = get_seat(r2_transition["speaker"], defendant)
        r2_transition["portrait"] = get_portrait(r2_transition["speaker"])

        r3_transition = {}
        if r3_test:
            r3_transition = retry_call(
                build_transition_prompt(skeleton, 2, r3_valid),
                validate_transition, "Step5a-过渡R3",
                temperature=TEMPERATURE, max_tokens=400,
                prompt_modifier=modifier_json_object,
                progress_cb=progress_cb,
            )
            r3_transition["seat"] = get_seat(r3_transition["speaker"], defendant)
            r3_transition["portrait"] = get_portrait(r3_transition["speaker"])

        # ---- Step 5b/c: 法官评论 ----
        _report(progress_cb, "Step5b", "正在编写法官评论...")

        def _validate_comment(data):
            return (isinstance(data, dict)
                    and "comment" in data
                    and len(data["comment"]) > 10)

        r1_comment_data = retry_call(
            build_judge_comment_prompt(skeleton, 0),
            _validate_comment, "Step5b-评论R1",
            max_tokens=200,
            prompt_modifier=modifier_json_object,
            progress_cb=progress_cb,
        )
        r1_comment = r1_comment_data.get("comment", "矛盾已确认。")

        r2_comment_data = retry_call(
            build_judge_comment_prompt(skeleton, 1),
            _validate_comment, "Step5c-评论R2",
            max_tokens=200,
            prompt_modifier=modifier_json_object,
            progress_cb=progress_cb,
        )
        r2_comment = r2_comment_data.get("comment", "真相只有一个！")

        r3_comment = ""
        if r3_test:
            r3_comment_data = retry_call(
                build_judge_comment_prompt(skeleton, 2),
                _validate_comment, "Step5c-评论R3",
                max_tokens=200,
                prompt_modifier=modifier_json_object,
                progress_cb=progress_cb,
            )
            r3_comment = r3_comment_data.get("comment", "真相大白！")

        # ---- Step 5d: 分支台词（逐组生成，更稳定）----
        _report(progress_cb, "Step5d", "正在编写分支台词...")
        branches = {}

        def _gen_branch(prompt_fn, key, min_lines):
            _report(progress_cb, f"Step5d-{key}", f"正在生成 {key}...")
            data = retry_call(
                prompt_fn(skeleton),
                lambda d: validate_branch(d, min_lines),
                f"Step5d-{key}", max_tokens=600,
                prompt_modifier=modifier_emphasize,
                progress_cb=progress_cb,
            )
            # 统一字段名：content -> text
            for line in data:
                if "content" in line and "text" not in line:
                    line["text"] = line.pop("content")
            branches[key] = data

        _gen_branch(_build_r1_success_prompt, "r1_success", 3)
        _gen_branch(_build_r1_fail_prompt, "r1_fail", 3)
        _gen_branch(_build_r2_success_prompt, "r2_success", 3)
        _gen_branch(_build_r2_fail_prompt, "r2_fail", 3)
        if num_rounds >= 3:
            _gen_branch(_build_r3_success_prompt, "r3_success", 3)
            _gen_branch(_build_r3_fail_prompt, "r3_fail", 3)
        print("Step5d: 分支台词全部完成")

        # ---- 组装最终案件 ----
        _report(progress_cb, "Done", "正在组装案件数据...")

        phases = [
            {
                "testimonies": r1_test,
                "evidence": r1_ev,
                "valid_objections": r1_valid,
                "judge_comment": r1_comment,
                "transition": r1_transition,
            },
            {
                "testimonies": r2_test,
                "evidence": r2_ev,
                "valid_objections": r2_valid,
                "judge_comment": r2_comment,
                "transition": r2_transition,
            },
        ]
        if r3_test and r3_ev:
            phases.append({
                "testimonies": r3_test,
                "evidence": r3_ev,
                "valid_objections": r3_valid,
                "judge_comment": r3_comment,
                "transition": r3_transition,
            })

        if num_rounds >= 3:
            brief_comment = (
                f"三阶段案件，需三轮异议。"
                f"R1推翻{step2['contradictions'][0]['type']}，"
                f"R2揭露{step2['contradictions'][1]['type']}，"
                f"R3揭露{step2['contradictions'][2]['type']}。"
            )
        else:
            brief_comment = (
                f"双阶段案件，需两轮异议。"
                f"R1推翻{step2['contradictions'][0]['type']}，"
                f"R2揭露{step2['contradictions'][1]['type']}。"
            )

        final_case = {
            "id": f"ai_case_{int(time.time()) % 100000:05d}",
            "title": skeleton["case_title"],
            "type": skeleton["crime"],
            "location": skeleton["location"],
            "complexity": difficulty["complexity"],
            "suspects": step2_5["suspects"],
            "phases": phases,
            "truth": skeleton["truth"],
            "brief_comment": brief_comment,
            "_meta": {
                "real_criminal": skeleton["real_criminal"],
                "r1_cliffhanger": skeleton["r1_cliffhanger"],
                "contradictions": step2["contradictions"],
                "difficulty": diff_key,
                "num_rounds": num_rounds,
                "fail_tolerance": difficulty["fail_tolerance"],
                "branches": branches,
            },
        }
        return final_case

    except Exception as e:
        import traceback as _tb
        print(f"\n生成失败，使用兜底案件。错误: {e}\n{_tb.format_exc()}")
        _report(progress_cb, "Error", f"生成失败: {e}，使用兜底案件")
        return FALLBACK_CASE


def _validate_branches(data: dict, num_rounds: int) -> bool:
    """校验合并生成的分支台词。"""
    if not isinstance(data, dict):
        print("  分支数据不是字典")
        return False
    branches = data.get("branches", {})
    required = ["r1_success", "r1_fail", "r2_success", "r2_fail"]
    if num_rounds >= 3:
        required.extend(["r3_success", "r3_fail"])
    for key in required:
        if key not in branches or not isinstance(branches[key], list):
            print(f"  分支缺少: {key}")
            return False
        if len(branches[key]) < 2:
            print(f"  分支 {key} 台词太少: {len(branches[key])}")
            return False
    return True


# ======================= 保存 & 入口 =======================

def save_case(case: dict, filename: str = OUTPUT_FILE):
    """保存案件到 JSON 文件。"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(case, f, ensure_ascii=False, indent=2)
    print(f"案件已保存至 {filename}")


def save_case_to_dir(case: dict, base_dir: str = CASES_DIR) -> str:
    """
    将案件保存到 cases/ 目录，使用带时间戳的独立文件名，避免覆盖。
    返回保存的文件路径。
    """
    import os
    os.makedirs(base_dir, exist_ok=True)
    # 文件名格式: cases/case_{时间戳}_{案件标题}.json
    safe_title = "".join(c for c in case.get("title", "untitled") if c.isalnum() or c in "_").strip()
    if not safe_title:
        safe_title = "untitled"
    timestamp = int(time.time()) % 100000
    filename = f"case_{timestamp:05d}_{safe_title[:20]}.json"
    filepath = os.path.join(base_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(case, f, ensure_ascii=False, indent=2)
    
    print(f"案件已保存至 {filepath}")
    return filepath


def load_cases_from_dir(base_dir: str = CASES_DIR) -> list:
    """
    从 cases/ 目录加载所有案件文件。
    返回案件字典列表。
    """
    import os
    if not os.path.exists(base_dir):
        return []
    cases = []
    for fname in sorted(os.listdir(base_dir)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(base_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "title" in data:
                cases.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "title" in item:
                        cases.append(item)
        except Exception as e:
            print(f"加载案件文件失败 {fname}: {e}")
    return cases


def get_user_preferences() -> dict:
    """交互式获取用户偏好。"""
    print("双轮异议案件生成器 V2 | 全部回车 = 随机生成")
    prefs = {}
    prompts = [
        ("defendant", f"被告角色 ({', '.join(CHARACTER_POOL[:6])}...)"),
        ("real_criminal", "真凶角色"),
        ("crime_type", f"罪名 ({', '.join(CRIME_POOL[:6])}...)"),
        ("style", "风格（搞笑/严肃/抽象/恐怖/温馨/悬疑/沙雕）"),
        ("theme", "主题关键词（如：广场舞、奶茶、考试）"),
        ("difficulty", "难度（easy/normal/hard）"),
    ]
    for key, text in prompts:
        val = input(f"  {text}: ").strip()
        if val:
            prefs[key] = val
    print("开始生成...\n")
    return prefs


if __name__ == "__main__":
    import sys as _sys
    
    # 支持 --prefs-file 参数，从游戏传入预设偏好
    preloaded = {}
    if "--prefs-file" in _sys.argv:
        idx = _sys.argv.index("--prefs-file")
        if idx + 1 < len(_sys.argv):
            try:
                with open(_sys.argv[idx + 1], "r", encoding="utf-8") as f:
                    preloaded = json.load(f)
                print(f"已从游戏加载预设: {json.dumps(preloaded, ensure_ascii=False)}")
            except Exception as e:
                print(f"加载预设失败: {e}")
    
    # 合并预设 + 终端交互输入
    prefs = preloaded.copy()
    print("=" * 50)
    print("双轮异议案件生成器 V2 | 全部回车 = 使用已有设置或随机生成")
    print("=" * 50)
    prompts = [
        ("defendant", f"被告角色 ({', '.join(CHARACTER_POOL[:6])}...)"),
        ("real_criminal", "真凶角色"),
        ("crime_type", f"罪名 ({', '.join(CRIME_POOL[:6])}...)"),
        ("style", f"风格（搞笑/严肃/抽象/恐怖/温馨/悬疑/沙雕）"),
        ("theme", "主题关键词（如：广场舞、奶茶、考试）"),
        ("difficulty", "难度（easy/normal/hard）"),
    ]
    for key, text in prompts:
        default = prefs.get(key, "")
        if default:
            hint = f"{text} [{default}]: "
        else:
            hint = f"{text}: "
        val = input(f"  {hint}").strip()
        if val:
            prefs[key] = val
    
    # 去除非 maker7 字段
    for k in list(prefs.keys()):
        if k not in {"defendant", "real_criminal", "crime_type", "style", "theme", "difficulty", "custom_prompt"}:
            del prefs[k]
    print("\n开始生成...\n")

    # 简单的终端进度展示
    def _terminal_progress(step: str, msg: str):
        print(f"  >> [{step}] {msg}")

    case = generate_case(prefs, progress_cb=_terminal_progress)

    print("\n生成成功！")
    print(f"  标题: {case['title']}")
    print(f"  类型: {case['type']}  地点: {case['location']}")
    print(f"  难度: {case['complexity']}  "
          f"(失败容限: {case['_meta']['fail_tolerance']})")
    print(f"  嫌疑人: {len(case['suspects'])} 人")
    for i, p in enumerate(case["phases"]):
        print(f"  Phase{i+1}: {len(p['testimonies'])} 证词 | "
              f"{len(p['evidence'])} 证据 | "
              f"{len(p['valid_objections'])} 个有效异议组合")
    print(f"  过渡: {case['phases'][0].get('transition', {}).get('speaker', '?')} - "
          f"{case['phases'][0].get('transition', {}).get('text', '?')[:30]}...")
    print(f"  真相: {case['truth'][:50]}...")
    save_case(case)
    print("请按任意键返回游戏...")
    input()
