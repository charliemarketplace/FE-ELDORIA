#!/usr/bin/env python3
"""
Root-cause regression guard for the {game.game_vars[...]} interpolation bug
that shipped in CAPITAL Train/Study: bare {expr} in an event command argument
only resolves a handful of known local names (unit, unit2, ...) via
TextEvaluator._evaluate_locals -- it is NOT a general Python-eval. Arbitrary
expressions need {eval:...}/{e:...}; game_vars/level_vars need {v:...}/{var:...}.
Even then, keyword types with can_preprocess=False (e.g. the String type used
by `choice`'s Title and `speak`'s Text) never get ANY brace substitution --
that preprocessing pass is skipped entirely for those arguments, by design
(app/events/event_validators.py's Validator.can_preprocess).

This script proves the fix (the real TextEvaluator class, not a hand-written
stand-in) and then lints every event in events.json for the same bug class
recurring elsewhere.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/verify_text_interpolation.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.frozen = True
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

import pygame
pygame.init()
pygame.display.set_mode((240, 160))

import app.engine.sprites as engine_sprites
from app.engine import game_state
from app.engine.text_evaluator import TextEvaluator

FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))


print('=' * 78)
print('TEXT INTERPOLATION -- root-cause proof + repo-wide lint')
print('=' * 78)

RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
engine_sprites.load_images()
game = game_state.start_level('CAPITAL')

evaluator = TextEvaluator(game_state.LOGGER if hasattr(game_state, 'LOGGER') else __import__('logging').getLogger(), game)
game.game_vars['FeatPick_Kael'] = 'fSpeed +2'

# --- 1. The fixed syntax actually resolves ---
result_fixed = evaluator._evaluate_all("{v:FeatPick_Kael}")
check('1. {v:FeatPick_Kael} resolves to the real game_var value',
      result_fixed == 'fSpeed +2',
      "_evaluate_all(\"{v:FeatPick_Kael}\") = %r (expected 'fSpeed +2')" % result_fixed)

# --- 2. The OLD broken syntax that shipped in CAPITAL Train/Study does NOT resolve ---
old_broken = "{game.game_vars['FeatPick_Kael']}"
result_broken = evaluator._evaluate_all(old_broken)
check('2. old {game.game_vars[...]} syntax is a documented no-op (proves the original bug)',
      result_broken == old_broken,
      '_evaluate_all(%r) = %r (unchanged -- this is exactly what shipped and silently no-opped)' % (old_broken, result_broken))

# --- 3. Repo-wide lint: no event command line should carry the same dead pattern ---
print('\n--- [3] Lint every event for the {game.…}/{level.…} dead-pattern (excl. if/elif/while, which take raw Python) ---')
DEAD_PATTERN = re.compile(r'\{[a-zA-Z_][a-zA-Z0-9_.\[\]\'\" ]*\.(game_vars|level_vars)\[')
RAW_EVAL_COMMANDS = ('if', 'elif', 'while')

offenders = []
for event in DB.events:
    for line in event._source:
        command = line.split(';', 1)[0].strip()
        if command in RAW_EVAL_COMMANDS:
            continue  # raw Python condition, {} here is fine/expected
        if DEAD_PATTERN.search(line):
            offenders.append((event.nid, line))

check('3. no event command argument uses the dead {x.game_vars[...]} pattern',
      len(offenders) == 0,
      'offenders = %s' % offenders if offenders else 'none found')

print('\n' + '=' * 78)
if FAILURES:
    print('RESULT: %d FAILURE(S)' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    sys.exit(1)
else:
    print('RESULT: ALL CHECKS PASSED')
