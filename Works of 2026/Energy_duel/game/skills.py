"""技能定义与效果计算模块"""
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any
import math
import random


@dataclass
class StatusEffect:
    """持续状态效果"""
    effect_type: str          # fire_burn, poison, bomb, death_buff, regen_energy, regen_both, no_heal, thorn_shield, shield, death_fight
    duration: int             # 剩余回合数
    value: int                # 效果数值
    source_skill: str         # 来源技能名
    target: int               # 0=自身, 1=对方 (相对施法者)
    delay: int = 0            # 延迟回合数(炸弹用)


class Skill:
    """技能定义"""
    name: str = ""
    category: str = ""        # damage, defense, control, develop
    
    def get_cost(self, x: int) -> dict:
        """返回消耗 {hp: int, energy: int}"""
        raise NotImplementedError
    
    def get_description(self, x: int) -> str:
        """返回技能描述"""
        raise NotImplementedError
    
    def can_use(self, player, x: int) -> bool:
        """检查是否能使用（资源是否足够）"""
        cost = self.get_cost(x)
        if player.hp - cost.get('hp', 0) <= 0 and cost.get('hp', 0) > 0:
            # 生命消耗不能致死（除了特殊情况）
            pass
        if player.energy < cost.get('energy', 0):
            return False
        if player.hp < cost.get('hp', 0):
            return False
        return True
    
    def apply(self, caster, target, x: int, game_state: dict) -> List[str]:
        """应用技能效果，返回日志消息列表"""
        raise NotImplementedError


# ============ 伤害类技能 ============

class Attack(Skill):
    """攻击：能量-x；对对方造成x点伤害"""
    name = "攻击"
    category = "damage"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': x}
    
    def get_description(self, x):
        return f"能量-{x}；造成{x}点伤害"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        damage = x
        # 检查向死buff
        for eff in caster.status_effects:
            if eff.effect_type == 'death_buff':
                damage += eff.value
        # 检查对方护盾/刺盾
        actual_damage, logs = apply_defense(target, damage, caster, self.name)
        target.hp = max(0, target.hp - actual_damage)
        log = [f"【攻击】玩家{game_state['caster_id']}消耗{x}能量，对玩家{game_state['target_id']}造成{actual_damage}点伤害"]
        # 检查死斗效果：生命减少时能量+1
        if actual_damage > 0:
            for eff in target.status_effects:
                if eff.effect_type == 'death_fight' and eff.target == 0:
                    target.energy = min(target.max_energy, target.energy + 1)
                    log.append(f"  死斗效果：玩家{game_state['target_id']}生命减少，能量+1")
        return log + logs


class FireAttack(Skill):
    """火攻：能量-(x+1)；造成2点伤害且若未被防守其下x+1个回合开始能量-1"""
    name = "火攻"
    category = "damage"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': x + 1}
    
    def get_description(self, x):
        return f"能量-{x+1}；造成2点伤害，若未防守则对方{x+1}回合能量-1"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        damage = 2
        for eff in caster.status_effects:
            if eff.effect_type == 'death_buff':
                damage += eff.value
        actual_damage, logs = apply_defense(target, damage, caster, self.name)
        target.hp = max(0, target.hp - actual_damage)
        result = [f"【火攻】玩家{game_state['caster_id']}消耗{x+1}能量，对玩家{game_state['target_id']}造成{actual_damage}点伤害"]
        # 检查是否被防守（对方本回合使用了防御类技能）
        defended = game_state.get(f'p{game_state["target_id"]}_defended', False)
        if not defended:
            target.status_effects.append(StatusEffect(
                effect_type='fire_burn', duration=x + 1, value=1,
                source_skill='火攻', target=0
            ))
            result.append(f"  未被防守！玩家{game_state['target_id']}将在接下来{x+1}回合每回合能量-1")
        else:
            result.append(f"  被防守抵消了持续效果")
        # 死斗效果
        if actual_damage > 0:
            for eff in target.status_effects:
                if eff.effect_type == 'death_fight' and eff.target == 0:
                    target.energy = min(target.max_energy, target.energy + 1)
                    result.append(f"  死斗效果：玩家{game_state['target_id']}生命减少，能量+1")
        return result + logs


class Poison(Skill):
    """毒计：能量-(x+1)；造成1点伤害且若未被防守其下x+1个回合开始生命-1"""
    name = "毒计"
    category = "damage"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': x + 1}
    
    def get_description(self, x):
        return f"能量-{x+1}；造成1点伤害，若未防守则对方{x+1}回合生命-1"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        damage = 1
        for eff in caster.status_effects:
            if eff.effect_type == 'death_buff':
                damage += eff.value
        actual_damage, logs = apply_defense(target, damage, caster, self.name)
        target.hp = max(0, target.hp - actual_damage)
        result = [f"【毒计】玩家{game_state['caster_id']}消耗{x+1}能量，对玩家{game_state['target_id']}造成{actual_damage}点伤害"]
        defended = game_state.get(f'p{game_state["target_id"]}_defended', False)
        if not defended:
            target.status_effects.append(StatusEffect(
                effect_type='poison', duration=x + 1, value=1,
                source_skill='毒计', target=0
            ))
            result.append(f"  未被防守！玩家{game_state['target_id']}将在接下来{x+1}回合每回合生命-1")
        else:
            result.append(f"  被防守抵消了持续效果")
        if actual_damage > 0:
            for eff in target.status_effects:
                if eff.effect_type == 'death_fight' and eff.target == 0:
                    target.energy = min(target.max_energy, target.energy + 1)
                    result.append(f"  死斗效果：玩家{game_state['target_id']}生命减少，能量+1")
        return result + logs


class Bomb(Skill):
    """炸弹：能量-x，对方2+x回合结束后受到2+x伤害"""
    name = "炸弹"
    category = "damage"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': x}
    
    def get_description(self, x):
        return f"能量-{x}；对方{2+x}回合后受到{2+x}点伤害"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        target.status_effects.append(StatusEffect(
            effect_type='bomb', duration=2 + x, value=2 + x,
            source_skill='炸弹', target=0, delay=2 + x
        ))
        return [f"【炸弹】玩家{game_state['caster_id']}消耗{x}能量，在玩家{game_state['target_id']}身上安装了炸弹（{2+x}回合后受到{2+x}点伤害）"]


class DeathSeek(Skill):
    """向死：生命-(x+1)，能量-(x+1)；下x个回合造成伤害+x"""
    name = "向死"
    category = "damage"
    
    def get_cost(self, x):
        return {'hp': x + 1, 'energy': x + 1}
    
    def get_description(self, x):
        return f"生命-{x+1}，能量-{x+1}；下{x}回合造成伤害+{x}"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.hp -= cost['hp']
        caster.energy -= cost['energy']
        caster.status_effects.append(StatusEffect(
            effect_type='death_buff', duration=x, value=x,
            source_skill='向死', target=0
        ))
        # 死斗效果：自身生命减少时能量+1
        for eff in caster.status_effects:
            if eff.effect_type == 'death_fight' and eff.target == 0:
                caster.energy = min(caster.max_energy, caster.energy + 1)
        return [f"【向死】玩家{game_state['caster_id']}消耗{x+1}生命和{x+1}能量，接下来{x}回合造成伤害+{x}"]


class BreakPot(Skill):
    """破釜：生命-(x+1)；对对方造成2x点伤害并令对方能量-x"""
    name = "破釜"
    category = "damage"
    
    def get_cost(self, x):
        return {'hp': x + 1, 'energy': 0}
    
    def get_description(self, x):
        return f"生命-{x+1}；造成{2*x}点伤害，对方能量-{x}"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.hp -= cost['hp']
        damage = 2 * x
        for eff in caster.status_effects:
            if eff.effect_type == 'death_buff':
                damage += eff.value
        actual_damage, logs = apply_defense(target, damage, caster, self.name)
        target.hp = max(0, target.hp - actual_damage)
        target.energy = max(0, target.energy - x)
        result = [f"【破釜】玩家{game_state['caster_id']}消耗{x+1}生命，对玩家{game_state['target_id']}造成{actual_damage}点伤害并削减{x}能量"]
        # 死斗效果
        for eff in caster.status_effects:
            if eff.effect_type == 'death_fight' and eff.target == 0:
                caster.energy = min(caster.max_energy, caster.energy + 1)
        if actual_damage > 0:
            for eff in target.status_effects:
                if eff.effect_type == 'death_fight' and eff.target == 0:
                    target.energy = min(target.max_energy, target.energy + 1)
                    result.append(f"  死斗效果：玩家{game_state['target_id']}生命减少，能量+1")
        return result + logs


# ============ 防御类技能 ============

class ThornShield(Skill):
    """刺盾：生命-1能量-x；本回合受到伤害-x，受到攻击时反弹x点伤害"""
    name = "刺盾"
    category = "defense"
    
    def get_cost(self, x):
        return {'hp': 1, 'energy': x}
    
    def get_description(self, x):
        return f"生命-1，能量-{x}；本回合受伤-{x}，被攻击反弹{x}伤害"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.hp -= cost['hp']
        caster.energy -= cost['energy']
        caster.status_effects.append(StatusEffect(
            effect_type='thorn_shield', duration=1, value=x,
            source_skill='刺盾', target=0
        ))
        game_state[f'p{game_state["caster_id"]}_defended'] = True
        # 死斗效果
        for eff in caster.status_effects:
            if eff.effect_type == 'death_fight' and eff.target == 0:
                caster.energy = min(caster.max_energy, caster.energy + 1)
        return [f"【刺盾】玩家{game_state['caster_id']}消耗1生命和{x}能量，本回合受伤-{x}且反弹{x}伤害"]


class Shield(Skill):
    """护盾：能量-x；本回合受到伤害-(x+1)"""
    name = "护盾"
    category = "defense"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': x}
    
    def get_description(self, x):
        return f"能量-{x}；本回合受伤-{x+1}"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        caster.status_effects.append(StatusEffect(
            effect_type='shield', duration=1, value=x + 1,
            source_skill='护盾', target=0
        ))
        game_state[f'p{game_state["caster_id"]}_defended'] = True
        return [f"【护盾】玩家{game_state['caster_id']}消耗{x}能量，本回合受伤-{x+1}"]


# ============ 控制类技能 ============

class Weaken(Skill):
    """弱化：生命-x；令对方能量-(2x-1)"""
    name = "弱化"
    category = "control"
    
    def get_cost(self, x):
        return {'hp': x, 'energy': 0}
    
    def get_description(self, x):
        return f"生命-{x}；对方能量-{2*x-1}"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.hp -= cost['hp']
        energy_loss = 2 * x - 1
        target.energy = max(0, target.energy - energy_loss)
        # 死斗效果
        for eff in caster.status_effects:
            if eff.effect_type == 'death_fight' and eff.target == 0:
                caster.energy = min(caster.max_energy, caster.energy + 1)
        return [f"【弱化】玩家{game_state['caster_id']}消耗{x}生命，玩家{game_state['target_id']}能量-{energy_loss}"]


class ControlStrategy(Skill):
    """御策：能量-(x+1)；随机禁用对方x+1个已使用过的技能两回合"""
    name = "御策"
    category = "control"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': x + 1}
    
    def get_description(self, x):
        return f"能量-{x+1}；随机禁用对方{x+1}个已使用过的技能2回合"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        # 获取对方已使用过但未被额外禁用的技能
        used_skills = [s for s in target.selected_skills if s in target.cooldowns and target.cooldowns[s] <= 0]
        # 也考虑当前可用的技能
        available = [s for s in target.selected_skills]
        to_disable = random.sample(available, min(x + 1, len(available)))
        for skill_name in to_disable:
            target.cooldowns[skill_name] = max(target.cooldowns.get(skill_name, 0), 3)
        result = [f"【御策】玩家{game_state['caster_id']}消耗{x+1}能量，禁用了玩家{game_state['target_id']}的技能：{', '.join(to_disable)}（2回合）"]
        return result


class Ceasefire(Skill):
    """息兵：随机禁用自身x个技能三回合；增加已禁用技能数的一半的能量（向上取整）"""
    name = "息兵"
    category = "control"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': 0}
    
    def get_description(self, x):
        return f"随机禁用自身{x}个技能3回合；恢复已禁用数/2的能量(向上取整)"
    
    def apply(self, caster, target, x, game_state):
        # 获取可用技能（未被禁用的）
        available = [s for s in caster.selected_skills if caster.cooldowns.get(s, 0) <= 0]
        to_disable = random.sample(available, min(x, len(available)))
        for skill_name in to_disable:
            caster.cooldowns[skill_name] = 4
        # 计算已禁用技能数
        disabled_count = sum(1 for s in caster.selected_skills if caster.cooldowns.get(s, 0) > 0)
        energy_gain = math.ceil(disabled_count / 2)
        caster.energy = min(caster.max_energy, caster.energy + energy_gain)
        result = [f"【息兵】玩家{game_state['caster_id']}禁用了自身技能：{', '.join(to_disable)}（3回合），恢复了{energy_gain}能量"]
        return result


class DeathFight(Skill):
    """死斗：能量-x；双方下2x回合无法增加生命且你生命减少后能量加一"""
    name = "死斗"
    category = "control"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': x}
    
    def get_description(self, x):
        return f"能量-{x}；双方{2*x}回合无法增加生命，你生命减少时能量+1"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        # 双方都添加无法增加生命的效果
        caster.status_effects.append(StatusEffect(
            effect_type='death_fight_no_heal', duration=2 * x, value=0,
            source_skill='死斗', target=0
        ))
        target.status_effects.append(StatusEffect(
            effect_type='death_fight_no_heal', duration=2 * x, value=0,
            source_skill='死斗', target=0
        ))
        # 施法者添加生命减少能量+1的效果
        caster.status_effects.append(StatusEffect(
            effect_type='death_fight', duration=2 * x, value=1,
            source_skill='死斗', target=0
        ))
        return [f"【死斗】玩家{game_state['caster_id']}消耗{x}能量，双方{2*x}回合无法增加生命，且自身生命减少时能量+1"]


# ============ 发育类技能 ============

class Repair(Skill):
    """修复：能量-2x；生命+1+x"""
    name = "修复"
    category = "develop"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': 2 * x}
    
    def get_description(self, x):
        return f"能量-{2*x}；生命+{1+x}"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        heal = 1 + x
        # 检查是否有无法增加生命的效果
        can_heal = not any(e.effect_type == 'death_fight_no_heal' for e in caster.status_effects)
        if can_heal:
            caster.hp = min(caster.max_hp, caster.hp + heal)
            return [f"【修复】玩家{game_state['caster_id']}消耗{2*x}能量，恢复{heal}生命"]
        else:
            return [f"【修复】玩家{game_state['caster_id']}消耗{2*x}能量，但无法增加生命（死斗效果）"]


class EnergyRegen(Skill):
    """生息：能量-(x+1)；下2x+1个回合开始能量+1"""
    name = "生息"
    category = "develop"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': x + 1}
    
    def get_description(self, x):
        return f"能量-{x+1}；下{2*x+1}回合每回合能量+1"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        caster.status_effects.append(StatusEffect(
            effect_type='regen_energy', duration=2 * x + 1, value=1,
            source_skill='生息', target=0
        ))
        return [f"【生息】玩家{game_state['caster_id']}消耗{x+1}能量，接下来{2*x+1}回合每回合能量+1"]


class Swap(Skill):
    """奇谋：生命-(x+1)，能量+x；互换自身生命与能量"""
    name = "奇谋"
    category = "develop"
    
    def get_cost(self, x):
        return {'hp': x + 1, 'energy': 0}
    
    def get_description(self, x):
        return f"生命-{x+1}，能量+{x}；互换自身生命与能量"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.hp -= cost['hp']
        caster.energy = min(caster.max_energy, caster.energy + x)
        # 互换
        old_hp = caster.hp
        old_energy = caster.energy
        caster.hp = min(caster.max_hp, old_energy)
        caster.energy = min(caster.max_energy, old_hp)
        # 死斗效果
        for eff in caster.status_effects:
            if eff.effect_type == 'death_fight' and eff.target == 0:
                caster.energy = min(caster.max_energy, caster.energy + 1)
        return [f"【奇谋】玩家{game_state['caster_id']}消耗{x+1}生命+{x}能量后，互换生命与能量（生命={caster.hp}，能量={caster.energy}）"]


class Delusion(Skill):
    """妄生：生命-2x；下3x个回合开始生命+1，能量+1"""
    name = "妄生"
    category = "develop"
    
    def get_cost(self, x):
        return {'hp': 2 * x, 'energy': 0}
    
    def get_description(self, x):
        return f"生命-{2*x}；下{3*x}回合每回合生命+1能量+1"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.hp -= cost['hp']
        caster.status_effects.append(StatusEffect(
            effect_type='regen_both', duration=3 * x, value=1,
            source_skill='妄生', target=0
        ))
        # 死斗效果
        for eff in caster.status_effects:
            if eff.effect_type == 'death_fight' and eff.target == 0:
                caster.energy = min(caster.max_energy, caster.energy + 1)
        return [f"【妄生】玩家{game_state['caster_id']}消耗{2*x}生命，接下来{3*x}回合每回合生命+1能量+1"]


class RushAttack(Skill):
    """急攻：生命-x；能量调整为2x"""
    name = "急攻"
    category = "develop"
    
    def get_cost(self, x):
        return {'hp': x, 'energy': 0}
    
    def get_description(self, x):
        return f"生命-{x}；能量调整为{2*x}"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.hp -= cost['hp']
        caster.energy = min(caster.max_energy, 2 * x)
        # 死斗效果
        for eff in caster.status_effects:
            if eff.effect_type == 'death_fight' and eff.target == 0:
                caster.energy = min(caster.max_energy, caster.energy + 1)
        return [f"【急攻】玩家{game_state['caster_id']}消耗{x}生命，能量调整为{caster.energy}"]


class ForgetGrudge(Skill):
    """忘隙：能量-x；生命+x，对方能量+x"""
    name = "忘隙"
    category = "develop"
    
    def get_cost(self, x):
        return {'hp': 0, 'energy': x}
    
    def get_description(self, x):
        return f"能量-{x}；生命+{x}，对方能量+{x}"
    
    def apply(self, caster, target, x, game_state):
        cost = self.get_cost(x)
        caster.energy -= cost['energy']
        # 检查是否能增加生命
        can_heal = not any(e.effect_type == 'death_fight_no_heal' for e in caster.status_effects)
        if can_heal:
            caster.hp = min(caster.max_hp, caster.hp + x)
        target.energy = min(target.max_energy, target.energy + x)
        heal_text = f"+{x}生命" if can_heal else "无法增加生命"
        return [f"【忘隙】玩家{game_state['caster_id']}消耗{x}能量，自身{heal_text}，对方能量+{x}"]


# ============ 辅助函数 ============

def apply_defense(target, damage, caster, skill_name):
    """处理防御效果，返回 (实际伤害, 日志列表)"""
    logs = []
    actual_damage = damage
    
    # 检查刺盾
    for eff in target.status_effects:
        if eff.effect_type == 'thorn_shield':
            actual_damage = max(0, actual_damage - eff.value)
            # 反弹伤害给攻击者
            reflect = eff.value
            caster.hp = max(0, caster.hp - reflect)
            logs.append(f"  刺盾反弹{reflect}点伤害给攻击者")
            break
    
    # 检查护盾（如果刺盾没有完全减免）
    if actual_damage > 0:
        for eff in target.status_effects:
            if eff.effect_type == 'shield':
                actual_damage = max(0, actual_damage - eff.value)
                break
    
    return actual_damage, logs


# ============ 技能注册表 ============

ALL_SKILLS = {
    # 伤害类
    '攻击': Attack(),
    '火攻': FireAttack(),
    '毒计': Poison(),
    '炸弹': Bomb(),
    '向死': DeathSeek(),
    '破釜': BreakPot(),
    # 防御类
    '刺盾': ThornShield(),
    '护盾': Shield(),
    # 控制类
    '弱化': Weaken(),
    '御策': ControlStrategy(),
    '息兵': Ceasefire(),
    '死斗': DeathFight(),
    # 发育类
    '修复': Repair(),
    '生息': EnergyRegen(),
    '奇谋': Swap(),
    '妄生': Delusion(),
    '急攻': RushAttack(),
    '忘隙': ForgetGrudge(),
}

SKILL_CATEGORIES = {
    'damage': '伤害类',
    'defense': '防御类',
    'control': '控制类',
    'develop': '发育类',
}
