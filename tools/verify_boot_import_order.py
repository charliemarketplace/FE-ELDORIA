#!/usr/bin/env python3
"""
Regression guard for a real production bug: the browser build crashed on
every load with

    ImportError: cannot import name 'skill_system' from 'app.engine' (unknown location)

triggered from Database.load() -> restore() -> item component lazy-loading,
which cascades through action/aura_funcs/unit/combat_calcs/item_funcs/
icons/unit_funcs and back into skill_system before it's finished
initializing.

This was never caught by any other native test this session because every
other test script pre-imports app.engine.action/unit_funcs/etc. (directly
or via game_state) BEFORE calling DB.load(), which primes sys.modules and
hides the ordering bug entirely. This script deliberately mimics main.py's
PRE-FIX cold boot order -- import DB and RESOURCES only, nothing else from
app.engine, before calling DB.load() -- NOT main.py's current (now-fixed)
boot order, which primes the cluster via an explicit `import app.engine.action`
before DB.load(). Staying on the cold/unprimed order here is deliberate: it
is the strongest possible regression guard on the underlying circular-import
fragility itself, so DB.load() is the very first thing to pull in the whole
action/skill_system/item_funcs cluster, exactly like the original crashing
browser boot.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/verify_boot_import_order.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.frozen = True
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
pygame.init()
pygame.display.set_mode((240, 160))

# Deliberately minimal imports, matching main.py's real boot order --
# nothing from app.engine.action/unit_funcs/skill_system pre-imported.
from app.data.resources.resources import RESOURCES
from app.data.database.database import DB
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

print('Loading resources (mirrors LT_BOOT: loading resources...)')
RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)

print('Loading database (mirrors LT_BOOT: loading database...) -- this is exactly where the browser crashed')
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)

print('RESULT: ALL CHECKS PASSED -- DB.load() completed with no import errors under cold boot order')
