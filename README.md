# lt_web — Lion Throne in the browser

A WebAssembly (pygbag) build of the Lex Talionis engine running *The Lion Throne*,
with no editor and no embedded audio. Engine source is the game-runtime slice of
LT-Maker build `83ddbf13` (release 2025.03.13a), taken from the packaged
distribution in `../LT_Engine/lion-throne/`.

## Run

```sh
uvx pygbag --ume_block 0 --template lt.tmpl .    # build + serve at http://localhost:8000
uvx pygbag --build --template lt.tmpl .          # build only; static output in build/web/
```

`lt.tmpl` is a customized pygbag page template (dark theme, controls card,
`?` help button). Without `--template` you get pygbag's stock gray page.

`--ume_block 0` skips pygbag's audio-unlock click gate (this build ships no
audio, so there is nothing to unlock; without the flag the page can hang at
"MEDIA USER ACTION REQUIRED").

Native desktop run (for fast iteration on game data edits):

```sh
uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python smoke_test.py
```

## Layout

- `main.py` — pygbag entry point (async bootstrap, WASM shims). Notable:
  top-level `import pygame` is required (pygbag scans main.py's imports to
  decide which WASM wheels to load); `threading.Thread`/`Timer` are shimmed
  (no real threads in WASM); boot milestones mirror to the JS console as
  `LT_BOOT:` lines for headless debugging
- `app/` — engine source (editor and map_maker excluded; `app/editor/lib/math` kept — the engine imports it)
- `lion_throne.ltproj/` — game data; all `.ogg` files stripped, manifests kept
- `resources/`, `sprites/` — engine-level UI assets
- `web_config.json` — `music_base_url`: null (silent) or an https URL serving the
  project's `.ogg` files by filename; external streaming in-browser is future work
- `smoke_test.py` — headless load + import + silent-audio regression test

## Web-only features

- Default controls (GBA-style QWAS, rebindable in-game): arrows move,
  S/Space/Enter confirm (A), A cancel (B), W info (R), Q cycle units (L),
  Tab options menu (Start); full mouse support unchanged
- Fast-forward: number keys **1 / 2 / 5** set game speed ×1/×2/×5 (scaled
  game clock in `engine.update_time`; `get_true_time` stays real-time)
- In-game keybinds and saves write to `saves/` in the browser's in-memory
  filesystem — they work within a session but are lost on page reload
  (persistence via IndexedDB is future work)

## Local modifications to engine source

- `app/engine/driver.py` — `run()` is async, yields to the browser every frame; icon load guarded
- `app/engine/sound.py` — `SoundDict.get` degrades missing sfx files to silence
