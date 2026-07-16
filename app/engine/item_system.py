
###############################################################################################################################
# This code was generated using `source_generator.py`. DO NOT MAKE ANY EDITS TO THIS FILE - YOUR CHANGES WILL BE OVERWRITTEN. #
###############################################################################################################################
from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Set, Tuple, Any
import app.engine.combat.playback as pb

from app.engine.component_system import utils

if TYPE_CHECKING:
    from app.engine.objects.item import ItemObject
    from app.engine.objects.unit import UnitObject

class Defaults():
    @staticmethod
    def full_price(unit: UnitObject, item: ItemObject) -> int:
        return None

    @staticmethod
    def buy_price(unit: UnitObject, item: ItemObject) -> float:
        return None

    @staticmethod
    def sell_price(unit: UnitObject, item: ItemObject) -> float:
        return None

    @staticmethod
    def special_sort(unit: UnitObject, item: ItemObject):
        return None

    @staticmethod
    def num_targets(unit: UnitObject, item: ItemObject) -> int:
        return 1

    @staticmethod
    def minimum_range(unit: UnitObject, item: ItemObject) -> int:
        return 0

    @staticmethod
    def maximum_range(unit: UnitObject, item: ItemObject) -> int:
        return 0

    @staticmethod
    def weapon_type(unit: UnitObject, item: ItemObject):
        return None

    @staticmethod
    def weapon_rank(unit: UnitObject, item: ItemObject):
        return None

    @staticmethod
    def modify_weapon_triangle(unit: UnitObject, item: ItemObject) -> float:
        return 1.0

    @staticmethod
    def effect_animation(unit: UnitObject, item: ItemObject) -> str:
        return None

    @staticmethod
    def damage(unit: UnitObject, item: ItemObject) -> int:
        return None

    @staticmethod
    def hit(unit: UnitObject, item: ItemObject) -> int:
        return None

    @staticmethod
    def crit(unit: UnitObject, item: ItemObject) -> int:
        return None

    @staticmethod
    def exp(playback, unit: UnitObject, item: ItemObject) -> int:
        return 0

    @staticmethod
    def wexp(playback, unit: UnitObject, item: ItemObject, target) -> int:
        return 1

    @staticmethod
    def text_color(unit: UnitObject, item: ItemObject) -> str:
        return None

    @staticmethod
    def weapon_triangle_override(unit: UnitObject, item: ItemObject):
        return None

def get_all_components(unit: UnitObject, item: ItemObject) -> list:
    from app.engine import skill_system
    override_components = skill_system.item_override(unit, item)
    override_component_nids = [c.nid for c in override_components]
    if not item:
        return override_components
    all_components = [c for c in item.components] + override_components
    return all_components

def available(unit: UnitObject, item: ItemObject) -> bool:
    """
    If any hook reports false, then it is false
    """
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('available'):
            if not component.available(unit, item):
                return False
    if item.parent_item:
        for component in item.parent_item.components:
            if component.defines('available'):
                if not component.available(unit, item.parent_item):
                    return False
    return True

def exp(playback: List[pb.PlaybackBrush], unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    val = 0
    for component in all_components:
        if component.defines('exp'):
            val += component.exp(playback, unit, item)
    return val

def stat_change(unit: UnitObject, item: ItemObject, stat_nid) -> int:
    bonus = 0
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('stat_change'):
            d = component.stat_change(unit)
            bonus += d.get(stat_nid, 0)
    return bonus

def stat_change_contribution(unit: UnitObject, item: ItemObject, stat_nid) -> list:
    contribution = {}
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('stat_change'):
            d = component.stat_change(unit)
            val = d.get(stat_nid, 0)
            if val != 0:
                if item.name in contribution:
                    contribution[item.name] += val
                else:
                    contribution[item.name] = val
    return contribution

def is_broken(unit: UnitObject, item: ItemObject) -> bool:
    """
    If any hook reports true, then it is true
    """
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('is_broken'):
            if component.is_broken(unit, item):
                return True
    if item.parent_item:
        for component in item.parent_item.components:
            if component.defines('is_broken'):
                if component.is_broken(unit, item.parent_item):
                    return True
    return False

def on_broken(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('on_broken'):
            component.on_broken(unit, item)
    if item.parent_item:
        for component in item.parent_item.components:
            if component.defines('on_broken'):
                component.on_broken(unit, item.parent_item)

def is_unusable(unit: UnitObject, item: ItemObject) -> bool:
    """
    If any hook reports true, then it is true
    """
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('is_unusable'):
            if component.is_unusable(unit, item):
                return True
    if item.parent_item:
        for component in item.parent_item.components:
            if component.defines('is_unusable'):
                if component.is_unusable(unit, item.parent_item):
                    return True
    return False

def on_unusable(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('on_unusable'):
            component.on_unusable(unit, item)
    if item.parent_item:
        for component in item.parent_item.components:
            if component.defines('on_unusable'):
                component.on_unusable(unit, item.parent_item)

def valid_targets(unit: UnitObject, item: ItemObject) -> set:
    targets = set()
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('valid_targets'):
            targets |= component.valid_targets(unit, item)
    return targets

def target_restrict(unit: UnitObject, item: ItemObject, def_pos, splash) -> bool:
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('target_restrict'):
            if not component.target_restrict(unit, item, def_pos, splash):
                return False
    return True

def range_restrict(unit: UnitObject, item: ItemObject) -> Tuple[Set, bool]:
    restricted_range = set()
    any_defined = False
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('range_restrict'):
            any_defined = True
            restricted_range |= component.range_restrict(unit, item)
    if any_defined:
        return restricted_range
    else:
        return None

def item_restrict(unit: UnitObject, item: ItemObject, defender, def_item: ItemObject) -> bool:
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('item_restrict'):
            if not component.item_restrict(unit, item, defender, def_item):
                return False
    return True

def ai_priority(unit: UnitObject, item: ItemObject, target: UnitObject, move) -> float:
    custom_ai_flag: bool = False
    ai_priority = 0
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('ai_priority'):
            custom_ai_flag = True
            ai_priority += component.ai_priority(unit, item, target, move)
    if custom_ai_flag:
        return ai_priority
    else:
        # Returns None when no custom ai is available
        return None

def splash(unit: UnitObject, item: ItemObject, position) -> tuple:
    """
    Returns main target position and splash positions
    """
    main_target = []
    splash = []
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('splash'):
            new_target, new_splash = component.splash(unit, item, position)
            main_target.append(new_target)
            splash += new_splash
    # Handle having multiple main targets
    if len(main_target) > 1:
        splash += main_target
        main_target = None
    elif len(main_target) == 1:
        main_target = main_target[0]
    else:
        main_target = None

    # If not default
    if main_target or splash:
        return main_target, splash
    else:  # DEFAULT
        from app.engine import skill_system
        alternate_splash_component = skill_system.alternate_splash(unit)
        if alternate_splash_component and not unsplashable(unit, item):
            main_target, splash = alternate_splash_component.splash(unit, item, position)
            return main_target, splash
        else:
            return position, []

def splash_positions(unit: UnitObject, item: ItemObject, position) -> set:
    positions = set()
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('splash_positions'):
            positions |= component.splash_positions(unit, item, position)
    # DEFAULT
    if not positions:
        from app.engine import skill_system
        alternate_splash_component = skill_system.alternate_splash(unit)
        if alternate_splash_component and not unsplashable(unit, item):
            positions = alternate_splash_component.splash_positions(unit, item, position)
            return positions
        else:
            return {position}
    return positions

def find_hp(actions, target):
    from app.engine import action
    starting_hp = target.get_hp()
    for subaction in actions:
        if isinstance(subaction, action.ChangeHP):
            starting_hp += subaction.num
    return starting_hp

def after_strike(actions, playback: List[pb.PlaybackBrush], unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode, attack_info, strike):
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('after_strike'):
            component.after_strike(actions, playback, unit, item, target, item2, mode, attack_info, strike)
    if item.parent_item:
        for component in item.parent_item.components:
            if component.defines('after_strike'):
                component.after_strike(actions, playback, unit, item.parent_item, target, mode, attack_info, strike)

def on_hit(actions, playback: List[pb.PlaybackBrush], unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, target_pos, mode, attack_info, first_item: ItemObject):
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('on_hit'):
            component.on_hit(actions, playback, unit, item, target, item2, target_pos, mode, attack_info)
    if item.parent_item and first_item:
        for component in item.parent_item.components:
            if component.defines('on_hit'):
                component.on_hit(actions, playback, unit, item.parent_item, target, item2, target_pos, mode, attack_info)

    # Default playback
    if target and find_hp(actions, target) <= target.get_hp(): # only trigger these brushes if damage was net dealt
        if target and find_hp(actions, target) <= 0:
            playback.append(pb.Shake(2))
            if not any(brush.nid == 'hit_sound' for brush in playback):
                playback.append(pb.HitSound('Final Hit'))
        else:
            playback.append(pb.Shake(1))
            if not any(brush.nid == 'hit_sound' for brush in playback):
                playback.append(pb.HitSound('Attack Hit ' + str(random.randint(1, 5))))
        if target and not any(brush.nid in ('unit_tint_add', 'unit_tint_sub') for brush in playback):
            playback.append(pb.UnitTintAdd(target, (255, 255, 255)))

def on_crit(actions, playback: List[pb.PlaybackBrush], unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, target_pos, mode, attack_info, first_item: ItemObject):
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('on_crit'):
            component.on_crit(actions, playback, unit, item, target, item2, target_pos, mode, attack_info)
        elif component.defines('on_hit'):
            component.on_hit(actions, playback, unit, item, target, item2, target_pos, mode, attack_info)
    if item.parent_item and first_item:
        for component in item.parent_item.components:
            if component.defines('on_crit'):
                component.on_crit(actions, playback, unit, item.parent_item, target, item2, target_pos, mode, attack_info)
            elif component.defines('on_hit'):
                component.on_hit(actions, playback, unit, item.parent_item, target, item2, target_pos, mode, attack_info)

    # Default playback
    playback.append(pb.Shake(3))
    if target:
        playback.append(pb.CritVibrate(target))
        if not any(brush.nid == 'hit_sound' for brush in playback):
            if find_hp(actions, target) <= 0:
                playback.append(pb.HitSound('Final Hit'))
            playback.append(pb.HitSound('Critical Hit ' + str(random.randint(1, 2))))
        if not any(brush.nid == 'crit_tint' for brush in playback):
            playback.append(pb.CritTint(target, (255, 255, 255)))

def on_glancing_hit(actions, playback: List[pb.PlaybackBrush], unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, target_pos, mode, attack_info, first_item: ItemObject):
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('on_glancing_hit'):
            component.on_glancing_hit(actions, playback, unit, item, target, item2, target_pos, mode, attack_info)
        elif component.defines('on_hit'):
            component.on_hit(actions, playback, unit, item, target, item2, target_pos, mode, attack_info)
    if item.parent_item and first_item:
        for component in item.parent_item.components:
            if component.defines('on_glancing_hit'):
                component.on_glancing_hit(actions, playback, unit, item.parent_item, target, item2, target_pos, mode, attack_info)
            elif component.defines('on_hit'):
                component.on_hit(actions, playback, unit, item.parent_item, target, item2, target_pos, mode, attack_info)

    # Default playback
    if target and find_hp(actions, target) <= target.get_hp(): # only trigger these brushes if damage was net dealt
        if target and find_hp(actions, target) <= 0:
            playback.append(pb.Shake(2))
            if not any(brush.nid == 'hit_sound' for brush in playback):
                playback.append(pb.HitSound('Final Hit'))
        else:
            playback.append(pb.Shake(4))
            if not any(brush.nid == 'hit_sound' for brush in playback):
                playback.append(pb.HitSound('No Damage'))
        if target and not any(brush.nid in ('unit_tint_add', 'unit_tint_sub') for brush in playback):
            playback.append(pb.UnitTintAdd(target, (255, 255, 255)))

def on_miss(actions, playback: List[pb.PlaybackBrush], unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, target_pos, mode, attack_info, first_item: ItemObject):
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('on_miss'):
            component.on_miss(actions, playback, unit, item, target, item2, target_pos, mode, attack_info)
    if item.parent_item and first_item:
        for component in item.parent_item.components:
            if component.defines('on_miss'):
                component.on_miss(actions, playback, unit, item.parent_item, target, item2, target_pos, mode, attack_info)

    # Default playback
    playback.append(pb.HitSound('Attack Miss 2'))
    playback.append(pb.HitAnim('MapMiss', target))

def item_icon_mod(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, sprite):
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('item_icon_mod'):
            sprite = component.item_icon_mod(unit, item, target, item2, sprite)
    return sprite

def can_unlock(unit: UnitObject, item: ItemObject, region) -> bool:
    all_components = get_all_components(unit, item)
    for component in all_components:
        if component.defines('can_unlock'):
            if component.can_unlock(unit, item, region):
                return True
    return False

def init(item: ItemObject):
    """
    Initializes any data on the parent item if necessary
    Do not put attribute initialization
    (ie, self._property = True) in this function
    """
    for component in item.components:
        if component.defines('init'):
            component.init(item)

def is_weapon(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('is_weapon'):
            values.append(component.is_weapon(unit, item))

    result = utils.all_false_priority(values)
    return result

def is_spell(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('is_spell'):
            values.append(component.is_spell(unit, item))

    result = utils.all_false_priority(values)
    return result

def is_accessory(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('is_accessory'):
            values.append(component.is_accessory(unit, item))

    result = utils.all_false_priority(values)
    return result

def equippable(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('equippable'):
            values.append(component.equippable(unit, item))

    result = utils.all_false_priority(values)
    return result

def can_counter(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('can_counter'):
            values.append(component.can_counter(unit, item))

    result = utils.all_false_priority(values)
    return result

def can_be_countered(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('can_be_countered'):
            values.append(component.can_be_countered(unit, item))

    result = utils.all_false_priority(values)
    return result

def can_double(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('can_double'):
            values.append(component.can_double(unit, item))

    result = utils.all_false_priority(values)
    return result

def can_use(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('can_use'):
            values.append(component.can_use(unit, item))

    result = utils.all_false_priority(values)
    return result

def can_use_in_base(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('can_use_in_base'):
            values.append(component.can_use_in_base(unit, item))

    result = utils.all_false_priority(values)
    return result

def unstealable(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('unstealable'):
            values.append(component.unstealable(unit, item))

    result = utils.all_false_priority(values)
    return result

def allow_same_target(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('allow_same_target'):
            values.append(component.allow_same_target(unit, item))

    result = utils.all_false_priority(values)
    return result

def allow_less_than_max_targets(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('allow_less_than_max_targets'):
            values.append(component.allow_less_than_max_targets(unit, item))

    result = utils.all_false_priority(values)
    return result

def ignore_weapon_advantage(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('ignore_weapon_advantage'):
            values.append(component.ignore_weapon_advantage(unit, item))

    result = utils.all_false_priority(values)
    return result

def unrepairable(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('unrepairable'):
            values.append(component.unrepairable(unit, item))

    result = utils.all_false_priority(values)
    return result

def unsplashable(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('unsplashable'):
            values.append(component.unsplashable(unit, item))

    result = utils.all_false_priority(values)
    return result

def targets_items(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('targets_items'):
            values.append(component.targets_items(unit, item))

    result = utils.all_false_priority(values)
    return result

def menu_after_combat(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('menu_after_combat'):
            values.append(component.menu_after_combat(unit, item))

    result = utils.all_false_priority(values)
    return result

def transforms(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('transforms'):
            values.append(component.transforms(unit, item))

    result = utils.all_false_priority(values)
    return result

def no_attack_after_move(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('no_attack_after_move'):
            values.append(component.no_attack_after_move(unit, item))

    result = utils.all_false_priority(values)
    return result

def no_map_hp_display(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('no_map_hp_display'):
            values.append(component.no_map_hp_display(unit, item))

    result = utils.all_false_priority(values)
    return result

def cannot_dual_strike(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('cannot_dual_strike'):
            values.append(component.cannot_dual_strike(unit, item))

    result = utils.all_false_priority(values)
    return result

def can_attack_after_combat(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('can_attack_after_combat'):
            values.append(component.can_attack_after_combat(unit, item))

    result = utils.all_false_priority(values)
    return result

def simple_target_restrict(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('simple_target_restrict'):
            values.append(component.simple_target_restrict(unit, item))

    result = utils.all_false_priority(values)
    return result

def force_map_anim(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('force_map_anim'):
            values.append(component.force_map_anim(unit, item))

    result = utils.all_false_priority(values)
    return result

def ignore_line_of_sight(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('ignore_line_of_sight'):
            values.append(component.ignore_line_of_sight(unit, item))

    result = utils.all_false_priority(values)
    return result

def ignore_fog_of_war(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('ignore_fog_of_war'):
            values.append(component.ignore_fog_of_war(unit, item))

    result = utils.all_false_priority(values)
    return result

def alerts_when_broken(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('alerts_when_broken'):
            values.append(component.alerts_when_broken(unit, item))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('alerts_when_broken'):
                        values.append(component.alerts_when_broken(unit, item))
                item = orig_item

    result = utils.all_true_priority(values)
    return result

def tradeable(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('tradeable'):
            values.append(component.tradeable(unit, item))

    result = utils.all_true_priority(values)
    return result

def storeable(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('storeable'):
            values.append(component.storeable(unit, item))

    result = utils.all_true_priority(values)
    return result

def discardable(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('discardable'):
            values.append(component.discardable(unit, item))

    result = utils.all_true_priority(values)
    return result

def damage_formula(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('damage_formula'):
            values.append(component.damage_formula(unit, item))

    result = utils.unique(values)
    return result

def resist_formula(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('resist_formula'):
            values.append(component.resist_formula(unit, item))

    result = utils.unique(values)
    return result

def accuracy_formula(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('accuracy_formula'):
            values.append(component.accuracy_formula(unit, item))

    result = utils.unique(values)
    return result

def avoid_formula(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('avoid_formula'):
            values.append(component.avoid_formula(unit, item))

    result = utils.unique(values)
    return result

def crit_accuracy_formula(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('crit_accuracy_formula'):
            values.append(component.crit_accuracy_formula(unit, item))

    result = utils.unique(values)
    return result

def crit_avoid_formula(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('crit_avoid_formula'):
            values.append(component.crit_avoid_formula(unit, item))

    result = utils.unique(values)
    return result

def attack_speed_formula(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('attack_speed_formula'):
            values.append(component.attack_speed_formula(unit, item))

    result = utils.unique(values)
    return result

def defense_speed_formula(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('defense_speed_formula'):
            values.append(component.defense_speed_formula(unit, item))

    result = utils.unique(values)
    return result

def damage_formula_override(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('damage_formula_override'):
            values.append(component.damage_formula_override(unit, item))

    result = utils.unique(values)
    return result

def resist_formula_override(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('resist_formula_override'):
            values.append(component.resist_formula_override(unit, item))

    result = utils.unique(values)
    return result

def accuracy_formula_override(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('accuracy_formula_override'):
            values.append(component.accuracy_formula_override(unit, item))

    result = utils.unique(values)
    return result

def avoid_formula_override(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('avoid_formula_override'):
            values.append(component.avoid_formula_override(unit, item))

    result = utils.unique(values)
    return result

def crit_accuracy_formula_override(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('crit_accuracy_formula_override'):
            values.append(component.crit_accuracy_formula_override(unit, item))

    result = utils.unique(values)
    return result

def crit_avoid_formula_override(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('crit_avoid_formula_override'):
            values.append(component.crit_avoid_formula_override(unit, item))

    result = utils.unique(values)
    return result

def attack_speed_formula_override(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('attack_speed_formula_override'):
            values.append(component.attack_speed_formula_override(unit, item))

    result = utils.unique(values)
    return result

def defense_speed_formula_override(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('defense_speed_formula_override'):
            values.append(component.defense_speed_formula_override(unit, item))

    result = utils.unique(values)
    return result

def full_price(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('full_price'):
            values.append(component.full_price(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.full_price(unit, item)

def buy_price(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('buy_price'):
            values.append(component.buy_price(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.buy_price(unit, item)

def sell_price(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('sell_price'):
            values.append(component.sell_price(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.sell_price(unit, item)

def special_sort(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('special_sort'):
            values.append(component.special_sort(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.special_sort(unit, item)

def num_targets(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('num_targets'):
            values.append(component.num_targets(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.num_targets(unit, item)

def minimum_range(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('minimum_range'):
            values.append(component.minimum_range(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.minimum_range(unit, item)

def maximum_range(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('maximum_range'):
            values.append(component.maximum_range(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.maximum_range(unit, item)

def weapon_type(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('weapon_type'):
            values.append(component.weapon_type(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.weapon_type(unit, item)

def weapon_triangle_override(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('weapon_triangle_override'):
            values.append(component.weapon_triangle_override(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.weapon_triangle_override(unit, item)

def weapon_rank(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('weapon_rank'):
            values.append(component.weapon_rank(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.weapon_rank(unit, item)

def damage(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('damage'):
            values.append(component.damage(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.damage(unit, item)

def hit(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('hit'):
            values.append(component.hit(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.hit(unit, item)

def crit(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('crit'):
            values.append(component.crit(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.crit(unit, item)

def effect_animation(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('effect_animation'):
            values.append(component.effect_animation(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.effect_animation(unit, item)

def text_color(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('text_color'):
            values.append(component.text_color(unit, item))

    result = utils.unique(values)
    return result if values else Defaults.text_color(unit, item)

def target_icon(unit: UnitObject, item: ItemObject, target: UnitObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('target_icon'):
            values.append(component.target_icon(unit, item, target))

    result = utils.union(values)
    return result

def wexp(playbacks: Any, unit: UnitObject, item: ItemObject, target: UnitObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('wexp'):
            values.append(component.wexp(playbacks, unit, item, target))

    result = utils.numeric_accumulate(values)
    return result

def modify_damage(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_damage'):
            values.append(component.modify_damage(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_resist(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_resist'):
            values.append(component.modify_resist(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_accuracy(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_accuracy'):
            values.append(component.modify_accuracy(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_avoid(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_avoid'):
            values.append(component.modify_avoid(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_crit_accuracy(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_crit_accuracy'):
            values.append(component.modify_crit_accuracy(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_crit_damage(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_crit_damage'):
            values.append(component.modify_crit_damage(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_crit_avoid(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_crit_avoid'):
            values.append(component.modify_crit_avoid(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_attack_speed(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_attack_speed'):
            values.append(component.modify_attack_speed(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_defense_speed(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_defense_speed'):
            values.append(component.modify_defense_speed(unit, item))

    result = utils.numeric_accumulate(values)
    return result

def modify_weapon_triangle(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('modify_weapon_triangle'):
            values.append(component.modify_weapon_triangle(unit, item))

    result = utils.numeric_multiply(values)
    return result if values else Defaults.modify_weapon_triangle(unit, item)

def dynamic_damage(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('dynamic_damage'):
            values.append(component.dynamic_damage(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_accuracy(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('dynamic_accuracy'):
            values.append(component.dynamic_accuracy(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_crit_accuracy(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('dynamic_crit_accuracy'):
            values.append(component.dynamic_crit_accuracy(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_attack_speed(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('dynamic_attack_speed'):
            values.append(component.dynamic_attack_speed(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_attacks(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('dynamic_attacks'):
            values.append(component.dynamic_attacks(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def dynamic_multiattacks(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any, attack_info: Any, base_value: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('dynamic_multiattacks'):
            values.append(component.dynamic_multiattacks(unit, item, target, item2, mode, attack_info, base_value))

    result = utils.numeric_accumulate(values)
    return result

def hover_description(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('hover_description'):
            values.append(component.hover_description(unit, item))

    result = utils.unique(values)
    return result

def show_weapon_advantage(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('show_weapon_advantage'):
            values.append(component.show_weapon_advantage(unit, item, target, item2))

    result = utils.unique(values)
    return result

def show_weapon_disadvantage(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('show_weapon_disadvantage'):
            values.append(component.show_weapon_disadvantage(unit, item, target, item2))

    result = utils.unique(values)
    return result

def battle_music(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('battle_music'):
            values.append(component.battle_music(unit, item, target, item2, mode))

    result = utils.unique(values)
    return result

def combat_effect(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('combat_effect'):
            values.append(component.combat_effect(unit, item, target, item2, mode))

    result = utils.unique(values)
    return result

def on_hit_effect(unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('on_hit_effect'):
            values.append(component.on_hit_effect(unit, item, target, item2, mode))

    result = utils.unique(values)
    return result

def on_end_chapter(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('on_end_chapter'):
            values.append(component.on_end_chapter(unit, item))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('on_end_chapter'):
                        values.append(component.on_end_chapter(unit, item))
                item = orig_item

    result = utils.no_return(values)
    return result

def reverse_use(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('reverse_use'):
            values.append(component.reverse_use(unit, item))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('reverse_use'):
                        values.append(component.reverse_use(unit, item))
                item = orig_item

    result = utils.no_return(values)
    return result

def on_equip_item(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('on_equip_item'):
            values.append(component.on_equip_item(unit, item))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('on_equip_item'):
                        values.append(component.on_equip_item(unit, item))
                item = orig_item

    result = utils.no_return(values)
    return result

def on_unequip_item(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('on_unequip_item'):
            values.append(component.on_unequip_item(unit, item))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('on_unequip_item'):
                        values.append(component.on_unequip_item(unit, item))
                item = orig_item

    result = utils.no_return(values)
    return result

def on_add_item(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('on_add_item'):
            values.append(component.on_add_item(unit, item))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('on_add_item'):
                        values.append(component.on_add_item(unit, item))
                item = orig_item

    result = utils.no_return(values)
    return result

def on_remove_item(unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('on_remove_item'):
            values.append(component.on_remove_item(unit, item))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('on_remove_item'):
                        values.append(component.on_remove_item(unit, item))
                item = orig_item

    result = utils.no_return(values)
    return result

def on_upkeep(actions: Any, playback: Any, unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('on_upkeep'):
            values.append(component.on_upkeep(actions, playback, unit, item))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('on_upkeep'):
                        values.append(component.on_upkeep(actions, playback, unit, item))
                item = orig_item

    result = utils.no_return(values)
    return result

def on_endstep(actions: Any, playback: Any, unit: UnitObject, item: ItemObject):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('on_endstep'):
            values.append(component.on_endstep(actions, playback, unit, item))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('on_endstep'):
                        values.append(component.on_endstep(actions, playback, unit, item))
                item = orig_item

    result = utils.no_return(values)
    return result

def start_combat(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('start_combat'):
            values.append(component.start_combat(playback, unit, item, target, item2, mode))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('start_combat'):
                        values.append(component.start_combat(playback, unit, item, target, item2, mode))
                item = orig_item

    result = utils.no_return(values)
    return result

def end_combat(playback: Any, unit: UnitObject, item: ItemObject, target: UnitObject, item2: ItemObject, mode: Any):
    all_components = get_all_components(unit, item)
    values = []
    for component in all_components:
        if component.defines('end_combat'):
            values.append(component.end_combat(playback, unit, item, target, item2, mode))

            if item.parent_item:
                orig_item = item
                item = item.parent_item
                for component in item.components:
                    if component.defines('end_combat'):
                        values.append(component.end_combat(playback, unit, item, target, item2, mode))
                item = orig_item

    result = utils.no_return(values)
    return result
