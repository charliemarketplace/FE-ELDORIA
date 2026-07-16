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


def restore_saves():
    """Copy persisted save files from browser localStorage into saves/.

    Must run before any app.engine import: config.py reads saves/config.ini
    at import time.
    """
    if sys.platform != 'emscripten':
        return
    try:
        import base64
        import platform
        data = json.loads(str(platform.window.lt_saves_dump()) or '{}')
        count = 0
        for rel, b64 in data.items():
            rel = rel.replace('\\', '/')
            if not rel.startswith('saves/') or '..' in rel:
                continue
            os.makedirs(os.path.dirname(rel), exist_ok=True)
            with open(rel, 'wb') as fp:
                fp.write(base64.b64decode(b64))
            count += 1
        js_log('restored %d save file(s) from browser storage' % count)
    except Exception:
        import traceback
        js_log('save restore failed:\n' + traceback.format_exc())


def persist_saves():
    """Mirror the saves/ dir into browser localStorage (replaces prior mirror)."""
    if sys.platform != 'emscripten':
        return
    try:
        import base64
        import platform
        data = {}
        for root, _, files in os.walk('saves'):
            for fn in files:
                if fn.endswith('.log') or fn.endswith('.txt'):
                    continue
                path = os.path.join(root, fn)
                with open(path, 'rb') as fp:
                    data[path.replace(os.sep, '/')] = base64.b64encode(fp.read()).decode('ascii')
        result = str(platform.window.lt_saves_put_all(json.dumps(data)))
        if result != 'ok':
            js_log('save persist warning: %s' % result)
    except Exception:
        import traceback
        js_log('save persist failed:\n' + traceback.format_exc())


def hook_save_persistence():
    """Persist to localStorage after every game save or settings write."""
    from app.engine import save as save_module
    import app.engine.config as cf_module

    orig_save_io = save_module.save_io
    def save_io_and_persist(*args, **kwargs):
        orig_save_io(*args, **kwargs)
        persist_saves()
    save_module.save_io = save_io_and_persist

    orig_save_config = cf_module.save_config
    def save_config_and_persist(*args, **kwargs):
        orig_save_config(*args, **kwargs)
        persist_saves()
    cf_module.save_config = save_config_and_persist


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


def get_url_param(name):
    """Read a query-string parameter from the hosting page's URL."""
    if sys.platform != 'emscripten':
        return None
    try:
        import platform
        from urllib.parse import parse_qs
        qs = parse_qs(str(platform.window.location.search).lstrip('?'))
        vals = qs.get(name)
        return vals[0] if vals else None
    except Exception:
        return None


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
    restore_saves()
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
    # Prime the fragile action/aura_funcs/unit/combat_calcs/item_funcs/icons/
    # unit_funcs/skill_system import cluster at a clean, non-circular entry
    # point BEFORE DB.load() below gets a chance to reach it cold via its own
    # lazy item/skill component loading. action.py's own imports transitively
    # resolve nearly the entire cluster non-circularly, so importing it here
    # first avoids the circular-import crash that lazy-loading would otherwise
    # hit first under pygbag's import machinery (see tools/verify_boot_import_order.py).
    import app.engine.action  # noqa: F401
    js_log('resources loaded, loading database...')
    DB.load(proj, CURRENT_SERIALIZATION_VERSION)
    js_log('database loaded')
    apply_audio_config()

    from app.engine import driver, game_state
    js_log('engine imported')
    hook_save_persistence()
    title = DB.constants.value('title')
    driver.start(title)
    js_log('driver started: %s' % title)
    # Debug mode is hidden on web (persisted configs may still have it on).
    # QA can re-enable with ?debug=1 in the URL.
    import app.engine.config as cf_module
    cf_module.SETTINGS['debug'] = 1 if get_url_param('debug') else 0
    # ?level=<nid> boots straight into that chapter (same path as the
    # editor's test-play), e.g. /?level=DEBUG — skips title screen and saves.
    level_nid = get_url_param('level')
    if level_nid and DB.levels.get(level_nid):
        js_log('jumping directly to level %s' % level_nid)
        game = game_state.start_level(level_nid)
        if cf_module.SETTINGS['debug']:
            # QA QoL: fill out the previously-recruitable roster and
            # autolevel to the chapter's power band when jumping straight
            # into a level with debug mode on. See app/engine/debug_jump.py.
            from app.engine import debug_jump
            debug_jump.install(game, level_nid)
    else:
        if level_nid:
            js_log('level %r not found; valid nids: %s'
                   % (level_nid, [lv.nid for lv in DB.levels]))
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
