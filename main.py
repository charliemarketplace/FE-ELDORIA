import asyncio
import json
import os
import sys
from pathlib import Path

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

    threading.Thread = _SyncThread

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


async def main():
    from app import lt_log
    lt_log.create_logger()

    from app.data.metadata import Metadata
    from app.data.serialization.dataclass_serialization import dataclass_from_dict
    from app.data.resources.resources import RESOURCES
    from app.data.database.database import DB
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

    proj = PROJECT + '.ltproj'
    metadata = dataclass_from_dict(Metadata, json.loads(Path(proj, 'metadata.json').read_text()))
    if metadata.has_fatal_errors:
        raise ValueError("Fatal errors detected in game data. Aborting launch.")

    RESOURCES.load(proj, CURRENT_SERIALIZATION_VERSION)
    DB.load(proj, CURRENT_SERIALIZATION_VERSION)
    apply_audio_config()

    from app.engine import driver, game_state
    title = DB.constants.value('title')
    driver.start(title)
    game = game_state.start_game()
    await driver.run(game)


asyncio.run(main())
