#!/usr/bin/env python3
"""
Native Python test of CAPITAL level completion mechanics.
Verifies that the engine can load, parse events, and the necessary
game data and Actions exist for Capital City hub completion.

Since the full game state has complex dependencies on graphical assets,
this test verifies the data layer and Action API rather than full execution.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up headless mode before any pygame imports
sys.frozen = True
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.makedirs('saves', exist_ok=True)

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.engine import action

import pygame
pygame.init()
pygame.display.set_mode((240, 160))

# Track results
results = {
    "1_boot_db": False,
    "2_level_data": False,
    "3_events_exist": False,
    "4_units_exist": False,
    "5_items_exist": False,
    "6_skills_exist": False,
    "7_actions_importable": False,
    "8_class_changes_valid": False,
}
details = {}

def log_result(check_id, passed, detail=""):
    """Log a check result."""
    results[check_id] = passed
    if detail:
        details[check_id] = detail
    status = "PASS" if passed else "FAIL"
    print(f"[{check_id}] {status}: {detail}")

print("=" * 70)
print("CAPITAL LEVEL COMPLETION - DATA VERIFICATION TEST")
print("=" * 70)

# ============================================================================
# 1. BOOT: Load DB/RESOURCES
# ============================================================================
print("\n[1] BOOT: Loading DB and RESOURCES...")
try:
    RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
    DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
    print(f"  DB loaded: {len(DB.levels)} levels, {len(DB.units)} units, {len(DB.items)} items, {len(DB.skills)} skills")
    log_result("1_boot_db", True, "DB/RESOURCES loaded successfully")
except Exception as e:
    log_result("1_boot_db", False, f"Boot failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# 2. LEVEL DATA: Verify CAPITAL and S1 levels exist
# ============================================================================
print("\n[2] LEVEL DATA: Checking CAPITAL and S1 levels...")
try:
    capital_level = DB.levels.get('CAPITAL')
    assert capital_level, "CAPITAL level not found"
    print(f"  CAPITAL level found: {capital_level.name}")
    print(f"    Units in level: {len(capital_level.units)}")
    print(f"    Regions: {len(capital_level.regions)}")

    s1_level = DB.levels.get('S1')
    assert s1_level, "S1 level not found"
    print(f"  S1 level found: {s1_level.name}")

    # Verify regions exist
    capital_regions = {r.nid for r in capital_level.regions}
    expected_regions = {'Armory', 'Vendor', 'Train', 'Study', 'Depart'}
    assert expected_regions.issubset(capital_regions), f"Missing regions. Have {capital_regions}"

    log_result("2_level_data", True, "CAPITAL and S1 levels with expected regions found")
except Exception as e:
    log_result("2_level_data", False, f"Level data check failed: {e}")

# ============================================================================
# 3. EVENTS: Verify CAPITAL events exist
# ============================================================================
print("\n[3] EVENTS: Checking CAPITAL events...")
try:
    # Find all CAPITAL events
    capital_events = [e for e in DB.events if e.level_nid == 'CAPITAL']
    capital_event_nids = {e.nid for e in capital_events}

    print(f"  Found {len(capital_events)} CAPITAL events:")
    for nid in sorted(capital_event_nids):
        print(f"    - {nid}")

    # Verify key events exist
    expected_events = {'CAPITAL Intro', 'CAPITAL Train', 'CAPITAL Study', 'CAPITAL Depart'}
    assert expected_events.issubset(capital_event_nids), f"Missing events. Have {capital_event_nids}"

    # Verify Intro event commands mention recruitment
    intro_event = [e for e in capital_events if e.nid == 'CAPITAL Intro'][0]
    intro_script = '\n'.join(intro_event._source)
    assert 'add_unit' in intro_script, "Intro event doesn't add units"
    assert 'game_var' in intro_script, "Intro event doesn't set game_vars"

    # Verify S1 Intro has join conditions
    s1_events = [e for e in DB.events if e.level_nid == 'S1']
    s1_intro = [e for e in s1_events if e.nid == 'S1 Intro']
    assert s1_intro, "S1 Intro event not found"
    s1_intro_script = '\n'.join(s1_intro[0]._source)
    assert '_joined' in s1_intro_script, "S1 Intro doesn't check joined flags"

    log_result("3_events_exist", True, "Key CAPITAL and S1 events with recruitment logic found")
except Exception as e:
    log_result("3_events_exist", False, f"Events check failed: {e}")

# ============================================================================
# 4. UNITS: Verify companion units exist
# ============================================================================
print("\n[4] UNITS: Checking companion units...")
try:
    companions = ['Kael', 'Elara', 'Ren', 'Briar']
    companion_units = {}

    for comp_nid in companions:
        unit = DB.units.get(comp_nid)
        assert unit, f"Unit {comp_nid} not found"
        companion_units[comp_nid] = unit
        print(f"  {comp_nid}: class={unit.klass}, level={unit.level}, bases={dict(unit.bases)}")

    log_result("4_units_exist", True, f"All {len(companions)} companion units found")
except Exception as e:
    log_result("4_units_exist", False, f"Units check failed: {e}")

# ============================================================================
# 5. ITEMS: Verify shop items exist
# ============================================================================
print("\n[5] ITEMS: Checking shop items...")
try:
    # From CAPITAL Vendor event
    shop_items = ['Vulnerary', 'Potion', 'Fire', 'Heal']

    for item_nid in shop_items:
        item = DB.items.get(item_nid)
        assert item, f"Item {item_nid} not found"
        print(f"  {item_nid}: value={item.value}")

    log_result("5_items_exist", True, f"All {len(shop_items)} shop items found")
except Exception as e:
    log_result("5_items_exist", False, f"Items check failed: {e}")

# ============================================================================
# 6. SKILLS: Verify feat skills exist
# ============================================================================
print("\n[6] SKILLS: Checking feat skills...")
try:
    # From CAPITAL Study event
    feat_skills = ['fMaximum HP +5', 'fSkill +3', 'fSpeed +2', 'fDefense +2', 'fLuck +4']

    for skill_nid in feat_skills:
        skill = DB.skills.get(skill_nid)
        assert skill, f"Skill {skill_nid} not found"
        print(f"  {skill_nid} found")

    log_result("6_skills_exist", True, f"All {len(feat_skills)} feat skills found")
except Exception as e:
    log_result("6_skills_exist", False, f"Skills check failed: {e}")

# ============================================================================
# 7. ACTIONS: Verify necessary Action classes exist
# ============================================================================
print("\n[7] ACTIONS: Checking Action classes...")
try:
    # Test importing key Actions
    action_classes = [
        ('ClassChange', action.ClassChange),
        ('AddSkill', action.AddSkill),
        ('GiveItem', action.GiveItem),
        ('GainMoney', action.GainMoney),
        ('SetGameVar', action.SetGameVar),
        ('ArriveOnMap', action.ArriveOnMap),
    ]

    for name, cls in action_classes:
        assert cls, f"Action {name} not found"
        print(f"  {name}: OK")

    log_result("7_actions_importable", True, f"All {len(action_classes)} Actions importable")
except Exception as e:
    log_result("7_actions_importable", False, f"Actions check failed: {e}")

# ============================================================================
# 8. CLASS CHANGES: Verify training classes exist
# ============================================================================
print("\n[8] CLASSES: Checking training classes...")
try:
    # From CAPITAL Train event
    training_classes = ['Fighter', 'Mercenary', 'Archer', 'Mage', 'Cleric']

    for class_nid in training_classes:
        klass = DB.classes.get(class_nid)
        assert klass, f"Class {class_nid} not found"
        print(f"  {class_nid}: tier={klass.tier}, bases={dict(klass.bases)}")

    log_result("8_class_changes_valid", True, f"All {len(training_classes)} training classes found")
except Exception as e:
    log_result("8_class_changes_valid", False, f"Classes check failed: {e}")

# ============================================================================
# VERIFY CAPITAL EVENT FLOW
# ============================================================================
print("\n[BONUS] CAPITAL EVENT FLOW VERIFICATION...")
try:
    intro = [e for e in DB.events if e.nid == 'CAPITAL Intro'][0]
    train = [e for e in DB.events if e.nid == 'CAPITAL Train'][0]
    study = [e for e in DB.events if e.nid == 'CAPITAL Study'][0]
    depart = [e for e in DB.events if e.nid == 'CAPITAL Depart'][0]

    # Intro event: checks safe_zone, gives money, adds companions
    intro_script = '\n'.join(intro._source)
    checks = [
        ('safe_zone set to 1', 'game_var;safe_zone;1' in intro_script),
        ('give_money', 'give_money' in intro_script),
        ('add_unit for Kael', 'add_unit;Kael' in intro_script),
        ('game_var for kael_joined', 'game_var;kael_joined' in intro_script),
    ]

    for desc, check in checks:
        assert check, f"Intro event missing: {desc}"
        print(f"    Intro: {desc} ✓")

    # Train event: class changes
    train_script = '\n'.join(train._source)
    assert 'change_class' in train_script, "Train event doesn't change class"
    assert 'Fighter,Mercenary,Archer,Mage,Cleric' in train_script, "Train event missing class options"
    print(f"    Train: offers classes ✓")

    # Study event: skill grants
    study_script = '\n'.join(study._source)
    assert 'give_skill' in study_script, "Study event doesn't give skills"
    print(f"    Study: grants skills ✓")

    # Depart event: sets next chapter
    depart_script = '\n'.join(depart._source)
    assert 'game_var;safe_zone;0' in depart_script, "Depart event doesn't clear safe_zone"
    assert 'set_next_chapter;S1' in depart_script, "Depart event doesn't set S1 as next"
    assert 'win_game' in depart_script, "Depart event doesn't call win_game"
    print(f"    Depart: transitions to S1 ✓")

    print(f"\n  CAPITAL event flow verified: Intro → Train → Study → Depart → S1")
except Exception as e:
    print(f"  Event flow verification failed: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

passed = sum(1 for v in results.values() if v)
total = len(results)

for check_id, passed_bool in results.items():
    status = "PASS" if passed_bool else "FAIL"
    detail = details.get(check_id, "")
    print(f"  {check_id}: {status}")
    if detail:
        print(f"    {detail}")

print(f"\nTotal: {passed}/{total} checks passed")

if passed == total:
    print("\nALL CHECKS PASSED!")
    print("\nThe CAPITAL hub level has all necessary data and mechanics:")
    print("  - Companion recruitment with unit addition")
    print("  - Class training with valid class changes")
    print("  - Skill granting for character customization")
    print("  - Money and shop system")
    print("  - Chapter advancement to S1 with joined status tracking")
    sys.exit(0)
else:
    print(f"\n{total - passed} CHECK(S) FAILED")
    sys.exit(1)
