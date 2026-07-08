import asyncio
import json
import os
import sys
from pathlib import Path

# pygbag scans main.py's imports to decide which WASM wheels to provision;
# the engine imports pygame only deep inside app/, so declare it here.
import pygame
import pygame.image
import pygame.mixer

# --- Platform shims: must run before any app.* import ---

# The engine treats hasattr(sys, 'frozen') as "built distribution" and skips
# runtime codegen. The generated sources (skill_system.py, item_system.py,
# python_event_command_wrappers.py) already ship in app/, so this is correct.
sys.frozen = True

if sys.platform == 'emscripten':
    # WASM Python has no real threads. The engine only uses threads for
    # fire-and-forget IO (save_io, music preloading), so running them
    # synchronously on start() is behaviorally equivalent.
    import threading

    class _SyncThread(threading.Thread):
        def start(self):
            self.run()

        def is_alive(self):
            return False

        def join(self, timeout=None):
            pass

    class _NoopTimer(threading.Timer):
        # Running a Timer's target synchronously could recurse (e.g. lt_log's
        # hourly touch_log reschedules itself), so deferred work is dropped.
        def start(self):
            pass

        def is_alive(self):
            return False

        def join(self, timeout=None):
            pass

    threading.Thread = _SyncThread
    threading.Timer = _NoopTimer

# Engine writes saves/config/logs to a relative saves/ dir
os.makedirs('saves', exist_ok=True)

PROJECT = 'lion_throne'


def apply_audio_config():
    """No audio ships in the web build; the engine degrades missing files to
    silence. If web_config.json sets music_base_url, rewrite song paths to
    point at that external source instead of the (absent) local files.

    Remote fetch is currently only functional on desktop runs; in-browser
    streaming from the URL is future work (needs an async fetch bridge).
    """
    try:
        with open('web_config.json') as fp:
            cfg = json.load(fp)
    except (OSError, json.JSONDecodeError):
        return
    base_url = cfg.get('music_base_url')
    if not base_url:
        return  # default: silent

    from app.data.resources.resources import RESOURCES
    for song in RESOURCES.music:
        for attr in ('full_path', 'battle_full_path', 'intro_full_path'):
            path = getattr(song, attr, None)
            if path and not os.path.exists(path):
                setattr(song, attr, base_url.rstrip('/') + '/' + os.path.basename(path))


def js_log(msg):
    """Mirror boot progress to the browser JS console (visible to tooling)."""
    print(msg)
    if sys.platform == 'emscripten':
        try:
            import platform
            platform.window.console.log('LT_BOOT: ' + str(msg))
        except Exception:
            pass


async def main():
    js_log('main() entered')
    from app import lt_log
    lt_log.create_logger()
    js_log('logger created')

    from app.data.metadata import Metadata
    from app.data.serialization.dataclass_serialization import dataclass_from_dict
    from app.data.resources.resources import RESOURCES
    from app.data.database.database import DB
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

    proj = PROJECT + '.ltproj'
    metadata = dataclass_from_dict(Metadata, json.loads(Path(proj, 'metadata.json').read_text()))
    if metadata.has_fatal_errors:
        raise ValueError("Fatal errors detected in game data. Aborting launch.")

    js_log('metadata ok, loading resources...')
    RESOURCES.load(proj, CURRENT_SERIALIZATION_VERSION)
    js_log('resources loaded, loading database...')
    DB.load(proj, CURRENT_SERIALIZATION_VERSION)
    js_log('database loaded')
    apply_audio_config()

    from app.engine import driver, game_state
    js_log('engine imported')
    title = DB.constants.value('title')
    driver.start(title)
    js_log('driver started: %s' % title)
    game = game_state.start_game()
    js_log('game state created, entering main loop')
    await driver.run(game)


async def boot():
    try:
        await main()
    except Exception:
        import traceback
        js_log('BOOT CRASH:\n' + traceback.format_exc())
        raise


asyncio.run(boot())
