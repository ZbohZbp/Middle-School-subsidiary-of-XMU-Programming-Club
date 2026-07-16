"""游戏核心引擎 - 状态管理、回合逻辑"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .skills import ALL_SKILLS, StatusEffect


@dataclass
class Player:
    """玩家状态"""
    id: int
    hp: int = 7
    energy: int = 5
    max_hp: int = 10
    max_energy: int = 10
    selected_skills: List[str] = field(default_factory=list)
    cooldowns: Dict[str, int] = field(default_factory=dict)
    status_effects: List[StatusEffect] = field(default_factory=list)
    
    def get_available_skills(self) -> List[str]:
        """获取当前可用技能（未被冷却的）"""
        return [s for s in self.selected_skills if self.cooldowns.get(s, 0) <= 0]
    
    def is_alive(self) -> bool:
        return self.hp > 0


class GameEngine:
    """游戏引擎"""
    
    def __init__(self):
        self.players = [Player(id=1), Player(id=2)]
        self.round = 0
        self.phase = 'skill_select'  # skill_select, playing, game_over
        self.logs: List[str] = []
        self.winner: Optional[int] = None
        self.turn_choices: Dict[int, dict] = {}  # player_id -> {skill_name, x}
    
    def set_player_skills(self, player_id: int, skill_names: List[str]):
        """设置玩家选择的技能"""
        player = self.players[player_id - 1]
        player.selected_skills = skill_names
        # 初始化冷却
        for skill_name in skill_names:
            player.cooldowns[skill_name] = 0
    
    def start_game(self):
        """开始游戏"""
        self.phase = 'playing'
        self.round = 1
        self.logs = ["=== 游戏开始 ==="]
    
    def start_round(self) -> List[str]:
        """开始新回合，处理回合开始效果"""
        logs = [f"\n{'='*40}", f"=== 第 {self.round} 回合开始 ===", f"{'='*40}"]

        # 回合开始时先递减冷却，确保技能在下一轮正确生效
        for p in self.players:
            for skill_name in list(p.cooldowns.keys()):
                if p.cooldowns[skill_name] > 0:
                    p.cooldowns[skill_name] -= 1
        
        # 每2回合开始能量+1（第2、4、6...回合触发）
        if self.round >= 2 and self.round % 2 == 0:
            for p in self.players:
                if p.is_alive():
                    p.energy = min(p.max_energy, p.energy + 1)
                    logs.append(f"  玩家{p.id} 每两回合能量回复，能量+1（当前能量：{p.energy}）")
        
        # 处理每个玩家的回合开始持续效果
        for p in self.players:
            if not p.is_alive():
                continue
            
            effects_to_remove = []
            for i, eff in enumerate(p.status_effects):
                # 跳过延迟中的炸弹
                if eff.effect_type == 'bomb' and eff.delay > 0:
                    continue
                
                if eff.effect_type == 'fire_burn':
                    p.energy = max(0, p.energy - eff.value)
                    logs.append(f"  玩家{p.id} 火攻灼烧：能量-{eff.value}（当前能量：{p.energy}）")
                
                elif eff.effect_type == 'poison':
                    p.hp = max(0, p.hp - eff.value)
                    logs.append(f"  玩家{p.id} 毒计发作：生命-{eff.value}（当前生命：{p.hp}）")
                    # 死斗效果
                    for e2 in p.status_effects:
                        if e2.effect_type == 'death_fight' and e2.target == 0:
                            p.energy = min(p.max_energy, p.energy + 1)
                            logs.append(f"    死斗效果：玩家{p.id}生命减少，能量+1")
                
                elif eff.effect_type == 'regen_energy':
                    p.energy = min(p.max_energy, p.energy + eff.value)
                    logs.append(f"  玩家{p.id} 生息回复：能量+{eff.value}（当前能量：{p.energy}）")
                
                elif eff.effect_type == 'regen_both':
                    can_heal = not any(e.effect_type == 'death_fight_no_heal' for e in p.status_effects)
                    if can_heal:
                        p.hp = min(p.max_hp, p.hp + eff.value)
                    p.energy = min(p.max_energy, p.energy + eff.value)
                    heal_text = f"生命+{eff.value}" if can_heal else "生命无法增加(死斗)"
                    logs.append(f"  玩家{p.id} 妄生效果：{heal_text}，能量+{eff.value}")
            
            # 检查胜负
            if not p.is_alive():
                other = self.players[0] if p.id == 2 else self.players[1]
                self.winner = other.id
                self.phase = 'game_over'
                logs.append(f"\n玩家{p.id} 被毒计击倒！玩家{other.id} 获胜！")
                return logs
        
        self.turn_choices = {}
        return logs
    
    def submit_choice(self, player_id: int, skill_name: str, x: int):
        """提交玩家选择"""
        self.turn_choices[player_id] = {'skill_name': skill_name, 'x': x}
    
    def resolve_turn(self) -> List[str]:
        """结算本回合"""
        logs = []
        
        p1 = self.players[0]
        p2 = self.players[1]
        
        choice1 = self.turn_choices.get(1)
        choice2 = self.turn_choices.get(2)
        
        if not choice1 or not choice2:
            return ["错误：玩家未完成选择"]
        
        # 重置防守标记
        game_state = {
            'p1_defended': False,
            'p2_defended': False,
            'caster_id': 0,
            'target_id': 0,
        }
        
        # 第一轮：先结算防御类技能（双方同时设置防御）
        for pid, choice in [(1, choice1), (2, choice2)]:
            if choice.get('skill_name') is None:
                continue
            skill = ALL_SKILLS.get(choice['skill_name'])
            if skill and skill.category == 'defense':
                caster = self.players[pid - 1]
                target = self.players[(2 if pid == 1 else 1) - 1]
                tid = 2 if pid == 1 else 1
                logs.append(f"\n--- 玩家{pid} 防御 ---")
                logs += self._apply_skill(caster, target, choice['skill_name'], choice['x'], pid, tid, game_state)
        
        # 第二轮：结算非防御类技能
        for pid, choice in [(1, choice1), (2, choice2)]:
            if choice.get('skill_name') is None:
                logs.append(f"\n--- 玩家{pid} 跳过本回合 ---")
                continue
            skill = ALL_SKILLS.get(choice['skill_name'])
            if skill and skill.category != 'defense':
                caster = self.players[pid - 1]
                target = self.players[(2 if pid == 1 else 1) - 1]
                tid = 2 if pid == 1 else 1
                logs.append(f"\n--- 玩家{pid} 行动 ---")
                logs += self._apply_skill(caster, target, choice['skill_name'], choice['x'], pid, tid, game_state)
                
                # 检查对方是否被击败
                if not target.is_alive():
                    self.winner = pid
                    self.phase = 'game_over'
                    logs.append(f"\n玩家{tid} 被击败！玩家{pid} 获胜！")
                    return logs
        
        # 更新冷却：使用过的技能在下一回合开始前不可再次使用
        for p in self.players:
            choice = self.turn_choices.get(p.id)
            if choice and choice.get('skill_name'):
                p.cooldowns[choice['skill_name']] = 1
        
        # 递减持续效果
        for p in self.players:
            effects_to_remove = []
            for i, eff in enumerate(p.status_effects):
                if eff.effect_type == 'bomb':
                    eff.delay -= 1
                    if eff.delay <= 0:
                        # 炸弹爆炸
                        p.hp = max(0, p.hp - eff.value)
                        logs.append(f"  炸弹爆炸！玩家{p.id}受到{eff.value}点伤害（生命：{p.hp}）")
                        # 死斗效果
                        for e2 in p.status_effects:
                            if e2.effect_type == 'death_fight' and e2.target == 0:
                                p.energy = min(p.max_energy, p.energy + 1)
                                logs.append(f"    死斗效果：玩家{p.id}生命减少，能量+1")
                        effects_to_remove.append(i)
                    else:
                        eff.duration -= 1
                        if eff.duration <= 0:
                            effects_to_remove.append(i)
                else:
                    eff.duration -= 1
                    if eff.duration <= 0:
                        effects_to_remove.append(i)
            
            # 移除过期效果（倒序删除）
            for i in sorted(effects_to_remove, reverse=True):
                p.status_effects.pop(i)
        
        # 检查胜负
        if not p1.is_alive():
            self.winner = 2
            self.phase = 'game_over'
            logs.append(f"\n玩家1 被击败！玩家2 获胜！")
        elif not p2.is_alive():
            self.winner = 1
            self.phase = 'game_over'
            logs.append(f"\n玩家2 被击败！玩家1 获胜！")
        else:
            # 显示状态
            logs.append(f"\n--- 回合结束状态 ---")
            logs.append(f"  玩家1：生命 {p1.hp}/{p1.max_hp}  能量 {p1.energy}/{p1.max_energy}")
            logs.append(f"  玩家2：生命 {p2.hp}/{p2.max_hp}  能量 {p2.energy}/{p2.max_energy}")
            self.round += 1
        
        return logs
    
    def _apply_skill(self, caster: Player, target: Player, skill_name: str, x: int,
                     caster_id: int, target_id: int, game_state: dict) -> List[str]:
        """应用单个技能"""
        skill = ALL_SKILLS.get(skill_name)
        if not skill:
            return [f"错误：未知技能 {skill_name}"]
        
        # 检查是否可以使用
        if not skill.can_use(caster, x):
            return [f"玩家{caster_id} 资源不足，无法使用 {skill_name}(x={x})，跳过行动"]
        
        game_state['caster_id'] = caster_id
        game_state['target_id'] = target_id
        
        return skill.apply(caster, target, x, game_state)
    
    def get_player(self, player_id: int) -> Player:
        return self.players[player_id - 1]
    
    def get_skill_info(self, skill_name: str, x: int) -> dict:
        """获取技能信息"""
        skill = ALL_SKILLS.get(skill_name)
        if not skill:
            return {}
        return {
            'name': skill.name,
            'category': skill.category,
            'cost': skill.get_cost(x),
            'description': skill.get_description(x),
            'can_use': True,
        }
