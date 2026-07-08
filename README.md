# lt_web — Lion Throne in the browser

A WebAssembly (pygbag) build of the Lex Talionis engine running *The Lion Throne*,
with no editor and no embedded audio. Engine source is the game-runtime slice of
LT-Maker build `83ddbf13` (release 2025.03.13a), taken from the packaged
distribution in `../LT_Engine/lion-throne/`.

## Run

```sh
uvx pygbag .            # build + serve at http://localhost:8000
uvx pygbag --build .    # build only; static output in build/web/
```

Native desktop run (for fast iteration on game data edits):

```sh
uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python smoke_test.py
```

## Layout

- `main.py` — pygbag entry point (async bootstrap, WASM shims)
- `app/` — engine source (editor and map_maker excluded; `app/editor/lib/math` kept — the engine imports it)
- `lion_throne.ltproj/` — game data; all `.ogg` files stripped, manifests kept
- `resources/`, `sprites/` — engine-level UI assets
- `web_config.json` — `music_base_url`: null (silent) or an https URL serving the
  project's `.ogg` files by filename; external streaming in-browser is future work
- `smoke_test.py` — headless load + import + silent-audio regression test

## Local modifications to engine source

- `app/engine/driver.py` — `run()` is async, yields to the browser every frame; icon load guarded
- `app/engine/sound.py` — `SoundDict.get` degrades missing sfx files to silence
