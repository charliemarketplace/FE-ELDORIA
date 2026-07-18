"""Native smoke test: verify data loads and engine modules import (no display)."""
import os
import sys

sys.frozen = True
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.makedirs('saves', exist_ok=True)

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
print('TITLE:', DB.constants.value('title'))
print('levels:', len(DB.levels), '| units:', len(DB.units), '| items:', len(DB.items), '| skills:', len(DB.skills))

# Content-integrity check: every item/skill/unit/level field that references
# another piece of content (e.g. a skill's "ability" component pointing at an
# item nid) must resolve to something that actually exists. A dangling
# reference here doesn't fail to load -- it silently returns None at runtime
# and crashes the game the first time that content is actually used (e.g. a
# missing ability item crashes on the unit's next status upkeep). Catching it
# at build time instead of during someone's playthrough is the whole point.
from app.data.validation.db_validation import DBChecker
checker = DBChecker(DB, RESOURCES)
content_errors = checker.validate_for_errors()
content_warnings = checker.validate_for_warnings()
for warning in content_warnings:
    print('CONTENT_WARNING:', warning)
if content_errors:
    for error in content_errors:
        print('CONTENT_ERROR:', error)
    print('CONTENT_VALIDATION_FAILED: %d error(s), %d warning(s)' % (len(content_errors), len(content_warnings)))
    sys.exit(1)
print('CONTENT_VALIDATION_OK (%d warning(s))' % len(content_warnings))

# Engine modules create surfaces at import time; init a dummy display first
import pygame
pygame.init()
pygame.display.set_mode((240, 160))

# Import the heavy engine modules to catch anything missing from the bundle
from app.engine import driver, game_state, general_states, save  # noqa
from app.engine import skill_system, item_system  # generated code
from app.events import event_commands  # noqa
print('ENGINE_IMPORTS_OK')

# Audio files are stripped from the web build: playing any song/sfx must
# degrade to silence, never raise.
from app.engine.sound import get_sound_thread, MUSIC, SFX
st = get_sound_thread()
song_nids = [s.nid for s in RESOURCES.music][:3]
sfx_nids = [s.nid for s in RESOURCES.sfx][:3]
for nid in song_nids:
    st.fade_in(nid)
    assert MUSIC.get(nid) is None
for nid in sfx_nids:
    st.play_sfx(nid)
st.load_songs(set(song_nids))
print('SILENT_AUDIO_OK (tested songs: %s | sfx: %s)' % (song_nids, sfx_nids))
