
###############################################################################################################################
# This code was generated using `source_generator.py`. DO NOT MAKE ANY EDITS TO THIS FILE - YOUR CHANGES WILL BE OVERWRITTEN. #
###############################################################################################################################
from __future__ import annotations
from functools import lru_cache

from typing import TYPE_CHECKING

from app.engine.component_system import utils

if TYPE_CHECKING:
    from app.engine.objects.item import ItemObject
    from app.engine.objects.unit import UnitObject

class Defaults():
    @staticmethod
    def can_select(unit) -> bool:
        return unit.team == 'player'

    @staticmethod
    def check_ally(unit1, unit2) -> bool:
        from app.data.database.database import DB
        if unit1 is unit2:
            return True
        elif unit2.team in DB.teams.get_allies(unit1.team):
            return True
        else:
            return unit2.team == unit1.team
        return False

    @staticmethod
    def check_enemy(unit1, unit2) -> bool:
        from app.data.database.database import DB
        if unit2.team in DB.teams.get_allies(unit1.team):
            return False
        else:
            return unit2.team != unit1.team
        return True

    @staticmethod
    def can_trade(unit1, unit2) -> bool:
        return unit1.team == unit2.team and check_ally(unit1, unit2) and not no_trade(unit1) and not no_trade(unit2)

    @staticmethod
    def num_items_offset(unit) -> int:
        return 0

    @staticmethod
    def num_accessories_offset(unit) -> int:
        return 0

    @staticmethod
    def witch_warp(unit) -> list:
        return []

    @staticmethod
    def exp_multiplier(unit1, unit2) -> float:
        return 1.0

    @staticmethod
    def enemy_exp_multiplier(unit1, unit2) -> float:
        return 1.0

    @staticmethod
    def wexp_multiplier(unit1, unit2) -> float:
        return 1.0

    @staticmethod
    def enemy_wexp_multiplier(unit1, unit2) -> float:
        return 1.0

    @staticmethod
    def change_variant(unit) -> str:
        return unit.variant

    @staticmethod
    def change_animation(unit) -> str:
        return unit.klass

    @staticmethod
    def change_ai(unit) -> str:
        return unit.ai

    @staticmethod
    def change_roam_ai(unit) -> str:
        return unit.roam_ai

    @staticmethod
    def has_canto(unit1, target) -> bool:
        return False

    @staticmethod
    def empower_heal(unit1, unit2) -> int:
        return 0

    @staticmethod
    def empower_heal_received(unit2, unit1) -> int:
        return 0

    @staticmethod
    def limit_maximum_range(unit, item) -> int:
        return 1000

    @staticmethod
    def movement_type(unit):
        return None

    @staticmethod
    def sight_range(unit):
        return 0

    @staticmethod
    def empower_splash(unit):
        return 0

    @staticmethod
    def modify_buy_price(unit, item) -> float:
        return 1.0

    @staticmethod
    def modify_sell_price(unit, item) -> float:
        return 1.0

    @staticmethod
    def damage_formula(unit) -> str:
        return 'DAMAGE'

    @staticmethod
    def resist_formula(unit) -> str:
        return 'DEFENSE'

    @staticmethod
    def accuracy_formula(unit) -> str:
        return 'HIT'

    @staticmethod
    def avoid_formula(unit) -> str:
        return 'AVOID'

    @staticmethod
    def crit_accuracy_formula(unit) -> str:
        return 'CRIT_HIT'

    @staticmethod
    def crit_avoid_formula(unit) -> str:
        return 'CRIT_AVOID'

    @staticmethod
    def attack_speed_formula(unit) -> str:
        return 'ATTACK_SPEED'

    @staticmethod
    def defense_speed_formula(unit) -> str:
        return 'DEFENSE_SPEED'

    @staticmethod
    def critical_multiplier_formula(unit) -> str:
        return 'CRIT_MULT'

    @staticmethod
    def critical_addition_formula(unit) -> str:
        return 'CRIT_ADD'

    @staticmethod
    def thracia_critical_multiplier_formula(unit) -> str:
        return 'THRACIA_CRIT'

@lru_cache(65535)
def condition(skill, unit: UnitObject, item=None) -> bool:
    if not item:
        item = unit.equipped_weapon
    for component in skill.components:
        if component.defines('condition'):
            if not component.condition(unit, item):
                return False
    return True

def is_grey(skill, unit) -> bool:
    return (not condition(skill, unit) and skill.grey_if_inactive)

def hidden(skill, unit) -> bool:
    return skill.hidden or skill.is_terrain or (skill.hidden_if_inactive and not condition(skill, unit))

def stat_change(unit, stat_nid) -> int:
    bonus = 0
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('stat_change'):
                d = component.stat_change(unit)
                d_bonus = d.get(stat_nid, 0)
                if d_bonus == 0:
                    continue
                # Why did we write the component condition check after the evaluation of the bonus?
                # Was there a good reason?
                if component.ignore_conditional or condition(skill, unit):
                    bonus += d_bonus
    return bonus

def subtle_stat_change(unit, stat_nid) -> int:
    bonus = 0
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('subtle_stat_change'):
                d = component.subtle_stat_change(unit)
                d_bonus = d.get(stat_nid, 0)
                if d_bonus == 0:
                    continue
                if component.ignore_conditional or condition(skill, unit):
                    bonus += d_bonus
    return bonus

def stat_change_contribution(unit, stat_nid) -> dict:
    contribution = {}
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('stat_change') and not component.defines('subtle_stat_change'):
                if component.ignore_conditional or condition(skill, unit):
                    d = component.stat_change(unit)
                    val = d.get(stat_nid, 0)
                    if val != 0:
                        if skill.name in contribution:
                            contribution[skill.name] += val
                        else:
                            contribution[skill.name] = val
    return contribution

def growth_change(unit, stat_nid) -> int:
    bonus = 0
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('growth_change'):
                if component.ignore_conditional or condition(skill, unit):
                    d = component.growth_change(unit)
                    bonus += d.get(stat_nid, 0)
    return bonus

def unit_sprite_flicker_tint(unit) -> list:
    flicker = []
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('unit_sprite_flicker_tint'):
                if component.ignore_conditional or condition(skill, unit):
                    d = component.unit_sprite_flicker_tint(unit, skill)
                    flicker.append(d)
    return flicker

def should_draw_anim(unit) -> list:
    avail = []
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('should_draw_anim'):
                if component.ignore_conditional or condition(skill, unit):
                    d = component.should_draw_anim(unit, skill)
                    avail.append(d)
    return avail

def additional_tags(unit) -> set:
    new_tags = set()
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('additional_tags'):
                if component.ignore_conditional or condition(skill, unit):
                    new_tags = new_tags | set(component.additional_tags(unit, skill))
    return new_tags

def before_crit(actions, playback, attacker, item, defender, item2, mode, attack_info) -> bool:
    for skill in attacker.skills:
        for component in skill.components:
            if component.defines('before_crit'):
                component.before_crit(actions, playback, attacker, item, defender, item2, mode, attack_info)

def on_end_chapter(unit, skill):
    for component in skill.components:
        if component.defines('on_end_chapter'):
            if component.ignore_conditional or condition(skill, unit):
                component.on_end_chapter(unit, skill)
        if component.defines('on_end_chapter_unconditional'):
            component.on_end_chapter_unconditional(unit, skill)

def init(skill):
    """
    Initializes any data on the parent skill if necessary
    """
    for component in skill.components:
        if component.defines('init'):
            component.init(skill)

def before_add(unit, skill):
    for component in skill.components:
        if component.defines('before_add'):
            component.before_add(unit, skill)
    for other_skill in unit.skills:
        for component in other_skill.components:
            if component.defines('before_gain_skill'):
                component.before_gain_skill(unit, skill)

def after_add(unit, skill):
    for component in skill.components:
        if component.defines('after_add'):
            component.after_add(unit, skill)
    for other_skill in unit.skills:
        for component in other_skill.components:
            if component.defines('after_gain_skill'):
                component.after_gain_skill(unit, skill)

def before_remove(unit, skill):
    for component in skill.components:
        if component.defines('before_remove'):
            component.before_remove(unit, skill)

def after_remove(unit, skill):
    for component in skill.components:
        if component.defines('after_remove'):
            component.after_remove(unit, skill)

def after_add_from_restore(unit, skill):
    for component in skill.components:
        if component.defines('after_add_from_restore'):
            component.after_add_from_restore(unit, skill)

def before_true_remove(unit, skill):
    """
    This does not intrinsically interact with the turnwheel
    It only fires when the skill is actually removed for the first time
    Not on execute or reverse
    """
    for component in skill.components:
        if component.defines('before_true_remove'):
            component.before_true_remove(unit, skill)

def after_true_remove(unit, skill):
    """
    This does not intrinsically interact with the turnwheel
    It only fires when the skill is actually removed for the first time
    Not on execute or reverse
    """
    for component in skill.components:
        if component.defines('after_true_remove'):
            component.after_true_remove(unit, skill)

def get_text(skill) -> str:
    for component in skill.components:
        if component.defines('text'):
            return component.text()
    return None

def get_cooldown(skill) -> float:
    for component in skill.components:
        if component.defines('cooldown'):
            return component.cooldown()
    return None

def get_hide_skill_icon(unit, skill) -> bool:
    # Check if we should be hiding this skill
    for component in skill.components:
        if component.defines('hide_skill_icon') and \
                component.hide_skill_icon(unit):
            return True
    return False

def get_show_skill_icon(unit, skill) -> bool:
    for component in skill.components:
        if component.defines('show_skill_icon') and \
                (component.ignore_conditional or condition(skill, unit)) and \
                component.show_skill_icon(unit):
            return True
    return False

def trigger_charge(unit, skill):
    for component in skill.components:
        if component.defines('trigger_charge'):
            component.trigger_charge(unit, skill)
    return None

def get_extra_abilities(unit):
    abilities = {}
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('extra_ability'):
                if component.ignore_conditional or condition(skill, unit):
                    new_item = component.extra_ability(unit)
                    if new_item:
                        abilities[new_item.name] = new_item
    return abilities

def ai_priority_multiplier(unit) -> float:
    ai_priority_multiplier = 1
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('ai_priority_multiplier'):
                if component.ignore_conditional or condition(skill, unit):
                    ai_priority_multiplier *= component.ai_priority_multiplier(unit)
    return ai_priority_multiplier

def get_combat_arts(unit):
    from app.engine import action, item_funcs
    from app.engine.game_state import game
    combat_arts = {}
    unit_skills = unit.skills[:]
    for skill in unit_skills:
        if not condition(skill, unit):
            continue
        combat_art = None
        combat_art_weapons = [item for item in item_funcs.get_all_items(unit) if item_funcs.available(unit, item)]
        for component in skill.components:
            if component.defines('combat_art'):
                combat_art = component.combat_art(unit)
            if component.defines('weapon_filter'):
                combat_art_weapons = \
                    [item for item in combat_art_weapons if component.weapon_filter(unit, item)]

        if combat_art and combat_art_weapons:
            good_weapons = []
            # Check which of the good weapons meet the range requirements
            for weapon in combat_art_weapons:
                # activate_combat_art(unit, skill)
                act = action.AddSkill(unit, skill.combat_art.value)
                act.do()
                targets = game.target_system.get_valid_targets(unit, weapon)
                act.reverse()
                # deactivate_combat_art(unit, skill)
                if targets:
                    good_weapons.append(weapon)

            if good_weapons:
                combat_arts[skill.name] = (skill, good_weapons)

    return combat_arts

def activate_combat_art(unit, skill):
    for component in skill.components:
        if component.defines('on_activation'):
            component.on_activation(unit)

def deactivate_combat_art(unit, skill):
    for component in skill.components:
        if component.defines('on_deactivation'):
            component.on_deactivation(unit)

def deactivate_all_combat_arts(unit):
    for skill in unit.skills:
        deactivate_combat_art(unit, skill)

def on_pairup(unit, leader):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('on_pairup'):
                component.on_pairup(unit, leader)

def on_separate(unit, leader):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('on_separate'):
                component.on_separate(unit, leader)

item_override_recursion_stack = set()
def item_override(unit, item: ItemObject):
    all_override_components = []
    components_so_far = set()
    if not unit or not item:
        return all_override_components
    for skill in reversed(unit.skills):
        for component in skill.components:
            if component.nid == 'item_override':
                # Conditions for item overrides might rely on e.g.
                # what item is equipped, which would itself
                # make an item override call on the same skill.
                # Therefore, we simply assume - probably safely -
                # that the skill cannot influence its own condition.
                if skill.nid not in item_override_recursion_stack:
                    item_override_recursion_stack.add(skill.nid)
                    if condition(skill, unit):
                        new_override_components = list(component.get_components(unit))
                        new_override_components = [comp for comp in new_override_components if comp.nid not in components_so_far]
                        components_so_far |= set([comp.nid for comp in new_override_components])
                        all_override_components += new_override_components
                    item_override_recursion_stack.remove(skill.nid)
                break
    return all_override_components

def available(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('available'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.available(unit, item))

    result = utils.all_true_priority(values)
    return result

def pass_through(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('pass_through'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.pass_through(unit))

    result = utils.all_false_priority(values)
    return result

def vantage(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('vantage'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.vantage(unit))

    result = utils.all_false_priority(values)
    return result

def desperation(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('desperation'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.desperation(unit))

    result = utils.all_false_priority(values)
    return result

def ignore_terrain(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('ignore_terrain'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.ignore_terrain(unit))

    result = utils.all_false_priority(values)
    return result

def crit_anyway(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('crit_anyway'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.crit_anyway(unit))

    result = utils.all_false_priority(values)
    return result

def ignore_region_status(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('ignore_region_status'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.ignore_region_status(unit))

    result = utils.all_false_priority(values)
    return result

def no_double(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('no_double'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.no_double(unit))

    result = utils.all_false_priority(values)
    return result

def def_double(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('def_double'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.def_double(unit))

    result = utils.all_false_priority(values)
    return result

def ignore_rescue_penalty(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('ignore_rescue_penalty'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.ignore_rescue_penalty(unit))

    result = utils.all_false_priority(values)
    return result

def ignore_forced_movement(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('ignore_forced_movement'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.ignore_forced_movement(unit))

    result = utils.all_false_priority(values)
    return result

def distant_counter(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('distant_counter'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.distant_counter(unit))

    result = utils.all_false_priority(values)
    return result

def ignore_fatigue(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('ignore_fatigue'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.ignore_fatigue(unit))

    result = utils.all_false_priority(values)
    return result

def no_attack_after_move(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('no_attack_after_move'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.no_attack_after_move(unit))

    result = utils.all_false_priority(values)
    return result

def has_dynamic_range(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('has_dynamic_range'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.has_dynamic_range(unit))

    result = utils.all_false_priority(values)
    return result

def disvantage(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('disvantage'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.disvantage(unit))

    result = utils.all_false_priority(values)
    return result

def close_counter(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('close_counter'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.close_counter(unit))

    result = utils.all_false_priority(values)
    return result

def attack_stance_double(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('attack_stance_double'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.attack_stance_double(unit))

    result = utils.all_false_priority(values)
    return result

def show_skill_icon(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('show_skill_icon'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.show_skill_icon(unit))

    result = utils.all_false_priority(values)
    return result

def hide_skill_icon(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('hide_skill_icon'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.hide_skill_icon(unit))

    result = utils.all_false_priority(values)
    return result

def ignore_dying_in_combat(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('ignore_dying_in_combat'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.ignore_dying_in_combat(unit))

    result = utils.all_false_priority(values)
    return result

def no_trade(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('no_trade'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.no_trade(unit))

    result = utils.all_false_priority(values)
    return result

def can_unlock(unit: UnitObject, region: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('can_unlock'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.can_unlock(unit, region))

    result = utils.any_false_priority(values)
    return result

def has_canto(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('has_canto'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.has_canto(unit, target))

    result = utils.any_false_priority(values)
    return result

def has_immune(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('has_immune'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.has_immune(unit))

    result = utils.any_false_priority(values)
    return result

def alternate_splash(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('alternate_splash'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.alternate_splash(unit))

    result = utils.unique(values)
    return result

def can_select(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('can_select'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.can_select(unit))

    result = utils.unique(values)
    return result if values else Defaults.can_select(unit)

def movement_type(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('movement_type'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.movement_type(unit))

    result = utils.unique(values)
    return result if values else Defaults.movement_type(unit)

def sight_range(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('sight_range'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.sight_range(unit))

    result = utils.unique(values)
    return result if values else Defaults.sight_range(unit)

def num_items_offset(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('num_items_offset'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.num_items_offset(unit))

    result = utils.unique(values)
    return result if values else Defaults.num_items_offset(unit)

def num_accessories_offset(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('num_accessories_offset'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.num_accessories_offset(unit))

    result = utils.unique(values)
    return result if values else Defaults.num_accessories_offset(unit)

def change_variant(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('change_variant'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.change_variant(unit))

    result = utils.unique(values)
    return result if values else Defaults.change_variant(unit)

def change_animation(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('change_animation'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.change_animation(unit))

    result = utils.unique(values)
    return result if values else Defaults.change_animation(unit)

def change_ai(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('change_ai'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.change_ai(unit))

    result = utils.unique(values)
    return result if values else Defaults.change_ai(unit)

def change_roam_ai(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('change_roam_ai'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.change_roam_ai(unit))

    result = utils.unique(values)
    return result if values else Defaults.change_roam_ai(unit)

@lru_cache(65535)
def witch_warp(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('witch_warp'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.witch_warp(unit))

    result = utils.unique(values)
    return result if values else Defaults.witch_warp(unit)

def damage_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('damage_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.damage_formula(unit))

    result = utils.unique(values)
    return result

def resist_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('resist_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.resist_formula(unit))

    result = utils.unique(values)
    return result

def accuracy_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('accuracy_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.accuracy_formula(unit))

    result = utils.unique(values)
    return result

def avoid_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('avoid_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.avoid_formula(unit))

    result = utils.unique(values)
    return result

def crit_accuracy_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('crit_accuracy_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.crit_accuracy_formula(unit))

    result = utils.unique(values)
    return result

def crit_avoid_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('crit_avoid_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.crit_avoid_formula(unit))

    result = utils.unique(values)
    return result

def attack_speed_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('attack_speed_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.attack_speed_formula(unit))

    result = utils.unique(values)
    return result

def defense_speed_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('defense_speed_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.defense_speed_formula(unit))

    result = utils.unique(values)
    return result

def critical_multiplier_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('critical_multiplier_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.critical_multiplier_formula(unit))

    result = utils.unique(values)
    return result if values else Defaults.critical_multiplier_formula(unit)

def critical_addition_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('critical_addition_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.critical_addition_formula(unit))

    result = utils.unique(values)
    return result if values else Defaults.critical_addition_formula(unit)

def thracia_critical_multiplier_formula(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('thracia_critical_multiplier_formula'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.thracia_critical_multiplier_formula(unit))

    result = utils.unique(values)
    return result if values else Defaults.thracia_critical_multiplier_formula(unit)

def damage_formula_override(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('damage_formula_override'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.damage_formula_override(unit))

    result = utils.unique(values)
    return result

def resist_formula_override(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('resist_formula_override'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.resist_formula_override(unit))

    result = utils.unique(values)
    return result

def accuracy_formula_override(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('accuracy_formula_override'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.accuracy_formula_override(unit))

    result = utils.unique(values)
    return result

def avoid_formula_override(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('avoid_formula_override'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.avoid_formula_override(unit))

    result = utils.unique(values)
    return result

def crit_accuracy_formula_override(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('crit_accuracy_formula_override'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.crit_accuracy_formula_override(unit))

    result = utils.unique(values)
    return result

def crit_avoid_formula_override(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('crit_avoid_formula_override'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.crit_avoid_formula_override(unit))

    result = utils.unique(values)
    return result

def attack_speed_formula_override(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('attack_speed_formula_override'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.attack_speed_formula_override(unit))

    result = utils.unique(values)
    return result

def defense_speed_formula_override(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('defense_speed_formula_override'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.defense_speed_formula_override(unit))

    result = utils.unique(values)
    return result

def modify_buy_price(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_buy_price'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_buy_price(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.modify_buy_price(unit, item)

def modify_sell_price(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_sell_price'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_sell_price(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.modify_sell_price(unit, item)

def limit_maximum_range(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('limit_maximum_range'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.limit_maximum_range(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.limit_maximum_range(unit, item)

def check_ally(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('check_ally'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.check_ally(unit, target))

    result = utils.unique(values)
    return result if values else Defaults.check_ally(unit, target)

def check_enemy(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('check_enemy'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.check_enemy(unit, target))

    result = utils.unique(values)
    return result if values else Defaults.check_enemy(unit, target)

def can_trade(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('can_trade'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.can_trade(unit, target))

    result = utils.unique(values)
    return result if values else Defaults.can_trade(unit, target)

def exp_multiplier(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('exp_multiplier'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.exp_multiplier(unit, target))

    result = utils.unique(values)
    return result if values else Defaults.exp_multiplier(unit, target)

def enemy_exp_multiplier(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('enemy_exp_multiplier'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.enemy_exp_multiplier(unit, target))

    result = utils.unique(values)
    return result if values else Defaults.enemy_exp_multiplier(unit, target)

def wexp_multiplier(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('wexp_multiplier'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.wexp_multiplier(unit, target))

    result = utils.unique(values)
    return result if values else Defaults.wexp_multiplier(unit, target)

def enemy_wexp_multiplier(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('enemy_wexp_multiplier'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.enemy_wexp_multiplier(unit, target))

    result = utils.unique(values)
    return result if values else Defaults.enemy_wexp_multiplier(unit, target)

def canto_movement(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('canto_movement'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.canto_movement(unit, target))

    result = utils.maximum(values)
    return result

def empower_splash(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('empower_splash'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.empower_splash(unit))

    result = utils.numeric_accumulate(values)
    return result

def empower_heal(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('empower_heal'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.empower_heal(unit, target))

    result = utils.numeric_accumulate(values)
    return result

def empower_heal_received(unit: UnitObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('empower_heal_received'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.empower_heal_received(unit, target))

    result = utils.numeric_accumulate(values)
    return result

def modify_damage(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_damage'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_damage(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_resist(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_resist'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_resist(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_accuracy(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_accuracy'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_accuracy(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_avoid(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_avoid'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_avoid(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_crit_accuracy(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_crit_accuracy'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_crit_accuracy(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_crit_avoid(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_crit_avoid'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_crit_avoid(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_crit_damage(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_crit_damage'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_crit_damage(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_attack_speed(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_attack_speed'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_attack_speed(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_defense_speed(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_defense_speed'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_defense_speed(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_maximum_range(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_maximum_range'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_maximum_range(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_minimum_range(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('modify_minimum_range'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.modify_minimum_range(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_damage(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_damage'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_damage(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_resist(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_resist'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_resist(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_accuracy(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_accuracy'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_accuracy(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_avoid(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_avoid'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_avoid(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_crit_accuracy(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_crit_accuracy'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_crit_accuracy(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_crit_avoid(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_crit_avoid'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_crit_avoid(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_attack_speed(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_attack_speed'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_attack_speed(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_defense_speed(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_defense_speed'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_defense_speed(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_attacks(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_attacks'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_attacks(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_multiattacks(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('dynamic_multiattacks'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.dynamic_multiattacks(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def mana(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('mana'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.mana(playback, unit, item, target))

    result = utils.numeric_accumulate(values)
    return result

def damage_multiplier(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('damage_multiplier'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.damage_multiplier(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_multiply(values)
    return result

def resist_multiplier(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('resist_multiplier'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.resist_multiplier(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_multiply(values)
    return result

def crit_multiplier(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('crit_multiplier'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.crit_multiplier(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_multiply(values)
    return result

def battle_music(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('battle_music'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.battle_music(playback, unit, item, target, item2, mode))

    result = utils.unique(values)
    return result

def on_death(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('on_death'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.on_death(unit))

    result = utils.no_return(values)
    return result

def on_add_item(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('on_add_item'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.on_add_item(unit, item))

    result = utils.no_return(values)
    return result

def on_remove_item(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('on_remove_item'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.on_remove_item(unit, item))

    result = utils.no_return(values)
    return result

def on_equip_item(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('on_equip_item'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.on_equip_item(unit, item))

    result = utils.no_return(values)
    return result

def on_unequip_item(unit: UnitObject, item: ItemObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('on_unequip_item'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.on_unequip_item(unit, item))

    result = utils.no_return(values)
    return result

def start_sub_combat(actions: Any, playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('start_sub_combat'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.start_sub_combat(actions, playback, unit, item, target, item2, mode, attack_info))

    result = utils.no_return(values)
    return result

def end_sub_combat(actions: Any, playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('end_sub_combat'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.end_sub_combat(actions, playback, unit, item, target, item2, mode, attack_info))

    result = utils.no_return(values)
    return result

def after_strike(actions: Any, playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, strike: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('after_strike'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.after_strike(actions, playback, unit, item, target, item2, mode, attack_info, strike))

    result = utils.no_return(values)
    return result

def after_take_strike(actions: Any, playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, strike: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('after_take_strike'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.after_take_strike(actions, playback, unit, item, target, item2, mode, attack_info, strike))

    result = utils.no_return(values)
    return result

def on_upkeep(actions: Any, playback: Any, unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('on_upkeep'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.on_upkeep(actions, playback, unit))

            if component.defines('on_upkeep_unconditional'):
                values.append(component.on_upkeep_unconditional(actions, playback, unit))

    result = utils.no_return(values)
    return result

def on_endstep(actions: Any, playback: Any, unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('on_endstep'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.on_endstep(actions, playback, unit))

            if component.defines('on_endstep_unconditional'):
                values.append(component.on_endstep_unconditional(actions, playback, unit))

    result = utils.no_return(values)
    return result

def start_combat(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('start_combat'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.start_combat(playback, unit, item, target, item2, mode))

            if component.defines('start_combat_unconditional'):
                values.append(component.start_combat_unconditional(playback, unit, item, target, item2, mode))

    result = utils.no_return(values)
    return result

def cleanup_combat(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('cleanup_combat'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.cleanup_combat(playback, unit, item, target, item2, mode))

            if component.defines('cleanup_combat_unconditional'):
                values.append(component.cleanup_combat_unconditional(playback, unit, item, target, item2, mode))

    result = utils.no_return(values)
    return result

def end_combat(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('end_combat'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.end_combat(playback, unit, item, target, item2, mode))

            if component.defines('end_combat_unconditional'):
                values.append(component.end_combat_unconditional(playback, unit, item, target, item2, mode))

    result = utils.no_return(values)
    return result

def pre_combat(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('pre_combat'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.pre_combat(playback, unit, item, target, item2, mode))

            if component.defines('pre_combat_unconditional'):
                values.append(component.pre_combat_unconditional(playback, unit, item, target, item2, mode))

    result = utils.no_return(values)
    return result

def post_combat(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('post_combat'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.post_combat(playback, unit, item, target, item2, mode))

            if component.defines('post_combat_unconditional'):
                values.append(component.post_combat_unconditional(playback, unit, item, target, item2, mode))

    result = utils.no_return(values)
    return result

def test_on(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('test_on'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.test_on(playback, unit, item, target, item2, mode))

            if component.defines('test_on_unconditional'):
                values.append(component.test_on_unconditional(playback, unit, item, target, item2, mode))

    result = utils.no_return(values)
    return result

def test_off(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('test_off'):
                if component.ignore_conditional or condition(skill, unit, item):
                    values.append(component.test_off(playback, unit, item, target, item2, mode))

            if component.defines('test_off_unconditional'):
                values.append(component.test_off_unconditional(playback, unit, item, target, item2, mode))

    result = utils.no_return(values)
    return result

def usable_wtypes(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('usable_wtypes'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.usable_wtypes(unit))

    result = utils.union(values)
    return result

def forbidden_wtypes(unit: UnitObject):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('forbidden_wtypes'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.forbidden_wtypes(unit))

    result = utils.union(values)
    return result

def target_icon(unit: UnitObject, icon_unit: Any):
    values = []
    for skill in unit.skills[:]:
        for component in skill.components:
            if component.defines('target_icon'):
                if component.ignore_conditional or condition(skill, unit):
                    values.append(component.target_icon(unit, icon_unit))

    result = utils.union(values)
    return result

def reset_cache():
    condition.cache_clear()
    witch_warp.cache_clear()
