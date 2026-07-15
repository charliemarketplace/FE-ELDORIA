# Eldoria — a Lex Talionis browser game

> **This repo is a fork of `lt_web` (which runs *The Lion Throne*).** Eldoria
> was created by cloning that project, trimming its content down to just the
> EMBER campaign (7 levels: `CAPITAL`, `S1`, `S2`, `SHUB`, `S3`, `S4`, `S5`),
> and rebranding (`title`/`game_nid` → "Eldoria"/"ELDORIA"). The engine and
> workflow are shared with `lt_web`; only the game content and a handful of
> engine patches (`app/engine/equations.py` SAFE-zone movement, dialogue
> timing fixes, interactable-region highlighting) are Eldoria-specific.
>
> **Editing game content (units, items, skills, levels, events)?**
> Read [`CONTENT_GUIDE.md`](CONTENT_GUIDE.md) first — it documents the whole
> .ltproj data model, cross-references, discovery recipes, and the
> edit→test→rebuild workflow. Then [`AUTHORING_CASE_STUDY.md`](AUTHORING_CASE_STUDY.md)
> for the proven end-to-end process (incl. headless browser verification and
> AI-generated map art). **Both of those docs were written for the original
> `lt_web`/Lion Throne project and describe its content (13 levels, demo
> chapters `TRIAL`/`TOWN`/`RIVER`/`DEBUG`, 243 events, etc.) — those specific
> facts do not apply to Eldoria's actual content.** Re-verify any concrete
> number or nid against the live files (`lion_throne.ltproj/game_data/*.json`)
> rather than trusting either doc; the *techniques* they describe (JSON model,
> event authoring, AI art pipeline) still apply as-is. API keys for
> generation tooling live in `.env` (gitignored, never committed).

A WebAssembly (pygbag) build of the Lex Talionis engine running *Eldoria*,
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

- Level jump for testing: `http://localhost:8000/?level=<nid>` boots
  directly into that chapter (editor test-play path), skipping the title
  screen — e.g. `?level=CAPITAL` opens the hub level, `?level=S1` opens the
  first EMBER chapter, in ~9 s. Eldoria's levels are `CAPITAL`, `S1`, `S2`,
  `SHUB`, `S3`, `S4`, `S5`. Wrong nids log the valid list to the JS console
  and fall back to the title screen. (`lt_web`'s demo/test chapters —
  `DEBUG`/`TRIAL`/`TOWN`/`RIVER` — were trimmed out of this fork and do not
  exist here.)
- Default controls (GBA-style QWAS, rebindable in-game): arrows move,
  S/Space/Enter confirm (A), A cancel (B), W info (R), Q cycle units (L),
  Tab options menu (Start); full mouse support unchanged
- Fast-forward: number keys **1 / 2 / 5** set game speed ×1/×2/×5 (scaled
  game clock in `engine.update_time`; `get_true_time` stays real-time)
- Save persistence: `saves/` is mirrored into browser localStorage after
  every game save / settings write (hooks on `save.save_io` and
  `config.save_config` in main.py) and restored at boot, so saves and
  keybinds survive page reloads. The 💾 button downloads all saves as
  `lion_throne_saves.json`; 📂 imports one (then reloads). localStorage
  is per-browser/per-origin, ~5 MB quota

## Local modifications to engine source

- `app/engine/driver.py` — `run()` is async, yields to the browser every frame; icon load guarded
- `app/engine/sound.py` — `SoundDict.get` degrades missing sfx files to silence
