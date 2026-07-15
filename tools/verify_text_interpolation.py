#!/usr/bin/env python3
"""
Root-cause regression guard for the {game.game_vars[...]} interpolation bug
that shipped in CAPITAL Train/Study.

The real mechanism (verified directly against app/events/event_validators.py
and app/engine/text_evaluator.py, not assumed): most event-command keyword
types -- including the String type used by `speak`'s Text and `choice`'s
Title -- DO get run through TextEvaluator._evaluate_all before the command
function sees them (Validator.can_preprocess defaults to True; String does
not override it). Only EvaluableString (used by `choice`'s Choices arg,
which does its own separate live-reevaluation in event_functions.choice)
opts out via can_preprocess=False.

The actual bug is one level deeper: even when _evaluate_all DOES run, it
only resolves a fixed set of recognized forms --
  - {e:expr} / {eval:expr}   -> arbitrary Python via evaluate.evaluate()
  - {v:Name} / {var:Name}    -> game.game_vars/level_vars[Name]
  - {d:...} {f:...} {s:...} {i:...} (and their long forms) -> other DB lookups
  - a BARE {name} that is an exact key in local_args (unit, unit2, ...)
    via TextEvaluator._evaluate_locals -- a dict lookup, not a Python eval.
Anything else -- e.g. a bare {game.game_vars['X']} or {unit.klass}, which is
neither a recognized prefix nor an exact local_args key -- falls through
_evaluate_locals' else branch and is written back UNCHANGED. This is a
silent no-op: no exception, no log spam, the literal braces show up on
screen or the argument is passed through as garbage text. This is what
shipped in CAPITAL Train/Study's change_class/give_item/give_skill calls.

This script proves the above against the real TextEvaluator class (not a
hand-written stand-in), then lints every event in events.json for the same
bug class recurring elsewhere -- generalized to ANY bare (non-prefixed)
{...} token containing '.', '[', or '(' (i.e. looks like an attempted
attribute/subscript/call expression), since that can never match a plain
local_args dict key regardless of which names happen to be in scope.

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
WARNINGS = []


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

# --- 2b. Same no-op for a compound attribute-access form (e.g. {unit.klass}),
#     to prove the lint below (which generalizes past game_vars/level_vars
#     specifically) is guarding against a real, reproduced failure mode. ---
compound_broken = "{unit.klass}"
result_compound = evaluator._evaluate_all(compound_broken)
check('2b. bare {unit.klass}-style compound access is also a documented no-op',
      result_compound == compound_broken,
      '_evaluate_all(%r) = %r (unchanged -- confirms _evaluate_locals only does exact-key lookup, not attribute access)' % (compound_broken, result_compound))

# --- 3. Repo-wide lint: no bare (non-prefixed) {...} token should look like
#     an attempted Python expression (contains '.', '[', or '(') -- that can
#     never resolve via TextEvaluator._evaluate_locals' exact dict lookup,
#     no matter which local names happen to be in scope for that event.
# ---------------------------------------------------------------------------
print('\n--- [3] Lint every event for bare {expr} tokens that can never resolve ---')

KNOWN_PREFIXES = ('e:', 'eval:', 'd:', 'data:', 'f:', 'field:',
                  'v:', 'var:', 's:', 'skill:', 'i:', 'item:',
                  'command:', 'c:')
KNOWN_LITERAL_TOKENS = {'br', 'clear', 'sub_break', 'no_wait', 'semicolon',
                        'comma', 'p', 'w', 'wait'}
RAW_EVAL_COMMANDS = ('if', 'elif', 'while')
BRACE_TOKEN = re.compile(r'\{([^{}]*)\}')

hard_offenders = []   # will never resolve, regardless of context
soft_unknowns = []    # bare simple name, not in our known-literal list -- may be a
                      # valid local_arg (e.g. a trigger_script custom arg) we can't
                      # verify statically; reported for visibility, not a failure

for event in DB.events:
    for line in event._source:
        command = line.split(';', 1)[0].strip()
        if command in RAW_EVAL_COMMANDS:
            continue  # raw Python condition, {} here is fine/expected
        for inner in BRACE_TOKEN.findall(line):
            if inner.startswith(KNOWN_PREFIXES):
                continue
            if inner in KNOWN_LITERAL_TOKENS:
                continue
            if any(ch in inner for ch in '.[('):
                hard_offenders.append((event.nid, line, inner))
            elif inner and not inner[0].isalpha():
                continue  # not an identifier-shaped token, ignore
            else:
                soft_unknowns.append((event.nid, line, inner))

check('3. no event command argument uses a bare {expr}-with-.()[ pattern that can never resolve',
      len(hard_offenders) == 0,
      'offenders = %s' % hard_offenders if hard_offenders else 'none found')

if soft_unknowns:
    print('  [INFO] %d bare {name} token(s) not in the known-literal set (may be valid '
        'local_args like {unit}/{unit2}/{position}/{item}/{created_unit} depending on '
        'event context -- not flagged as failures, listed for a human to eyeball):' % len(soft_unknowns))
    seen = set()
    for nid, line, inner in soft_unknowns:
        key = (nid, inner)
        if key in seen:
            continue
        seen.add(key)
        print('    %s: {%s}  (%s)' % (nid, inner, line))

print('\n' + '=' * 78)
if FAILURES:
    print('RESULT: %d FAILURE(S)' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    sys.exit(1)
else:
    print('RESULT: ALL CHECKS PASSED')
