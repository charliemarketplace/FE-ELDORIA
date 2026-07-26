---
name: configure-ai-presets-and-groups
description: Author a reusable AI preset (targeting priority, view range, roam vs. tactical) and/or link units into an ai_group so a squad reacts together, for a designer scripting enemy behavior beyond "just attack."
---

## 1. Feature

A designer defines named AI presets in `ai.json` — up to three priority-ordered
behaviours each (e.g. "attack if in range, else return to spawn, else do
nothing") — and assigns one to each unit via its `ai` field. Presets are
data-driven: targeting (enemy/ally/specific tag/class/faction), view range
(tile count or a movement-relative "entire map"/"guard" special value), and a
per-preset offense-vs-safety weighting are all authored, no code required.
Separately, tagging several units on a level with the same `ai_group` string
makes them react as a squad: the first unit to find a target "pings" the
group, waking every other member of that group early instead of waiting for
its own turn in priority order — the classic "ambush squad" trick.

## 2. Details

### 2.1 `AIPrefab` (`app/data/database/ai.py:10-71`)

| Field | Meaning | Default |
|---|---|---|
| `nid` | Preset identifier, assigned to units via their `ai` field | required |
| `priority` | Higher acts earlier within the enemy phase; sorted descending across all AI-controlled units (`app/engine/general_states.py:2488,2497`) | `0` (`AICatalog.create_new` seeds new presets at `20`, `ai.py:112`) |
| `offense_bias` | Float weighting of offense vs. avoiding retaliation in move/attack scoring | `2.0` |
| `roam_ai` | If true, unit uses the free-roam AI (`app/engine/roam/free_roam_ai.py`) instead of grid-tactics `AIController` | `False` |
| `behaviours` | Up to 3 `AIBehaviour` slots, tried in order until one succeeds; `add_behaviour`/`pop_behaviour`/`set_behaviour` mutate the list | 3× `AIBehaviour.DoNothing()` |

`offense_bias` is converted at `app/engine/ai_controller.py:620-623` into
`offense_weight = offense_bias / (offense_bias + 1)` and
`defense_weight = 1 - offense_weight`, both folded into the move-scoring sum
alongside a small distance tiebreaker (`:624-628`) — at the default `2.0` an
AI weighs its own expected damage output roughly 2:1 over damage it would take
in return.

### 2.2 `AIBehaviour` (`app/data/database/ai.py:73-104`)

| Field | Meaning | Default |
|---|---|---|
| `action` | One of `AI_ActionTypes = ['None','Attack','Support','Steal','Interact','Move_to','Move_away_from','Wait']` (`ai.py:4`) | `'None'` |
| `target` | One of `AI_TargetTypes = ['None','Enemy','Ally','Unit','Position','Event','Terrain','Time']` (`ai.py:5`) | `'None'` |
| `target_spec` | `[spec_type, spec_nid]`, `spec_type` ∈ `unit_spec = ['All','Class','Tag','Name','Team','Faction','Party','ID']` (`ai.py:6`), or a plain string (region/event sub-nid) for `Interact` targets | `None` |
| `invert_targeting` | XOR the `target_spec` match — target everyone *except* the spec | `False` |
| `view_range` | How far the unit looks for a target — see special codes below | `0` |
| `roam_speed` | Movement speed, only meaningful when `roam_ai=True` (`app/engine/roam/free_roam_ai.py`) | `100` |
| `desired_proximity` | Roam-AI-only: how close to stay to its target | `0` |
| `condition` | Arbitrary expression string; behaviour only tried if this evaluates truthy (`evaluate.evaluate(condition, unit, position=...)`, `ai_controller.py:67-68`) | `''` (always tried) |

**`view_range` special codes** (`app/engine/ai_controller.py:200-209`,
mirrored at `:697-699,730-742,768-771` for movement targeting): `-4` = entire
map (no distance filter); `-3` = `movement()×2 + max item range`; `-2` =
`movement() + max item range`; `-1` = `max item range` only, with **no
movement at all unless the unit's `ai_group` is active**
(`ai_controller.py:217-225,219`) — this is the "Guard" stance, and
`AIBehaviour.guard_ai()`/`AIPrefab.guard_ai()` (`ai.py:61-71,103-104`) detect
it purely for UI (boundary/highlight rendering of stationary units, gated by
the `zero_move` constant); any other integer = a literal fixed tile range;
`0` (the unset default) never finds a target, which is why the unused slots
in every preset use `view_range: 0`. Note: `app/default_data/default_ai.txt`
documents an older, different numbering for these codes — that file is stale
and does not match current `ai_controller.py` behavior.

### 2.3 AI groups — squad-wide coordination

- Level-scoped DB record: `AIGroup` (`app/data/database/ai_groups.py:6-8`,
  fields `nid`, `trigger_threshold: int = 0`), stored per-level
  (`app/data/database/levels.py:46`, `self.ai_groups = Data[AIGroup]()`).
- **Auto-heal on load**: `LevelPrefab.restore()` (`app/data/database/
  levels.py:83-99`) deletes any `AIGroup` no unit references anymore, and —
  critically — synthesizes `AIGroup(nid, 1)` for any `ai_group` string a unit
  carries that isn't yet in the level's `ai_groups` list. This means a
  designer can just type an `ai_group` name on a unit without ever touching
  the level's `ai_groups` array, and get a working group at the default
  `trigger_threshold=1` — but that also means the threshold-tuning knob
  (requiring N units to notice before the squad reacts) is silently skipped
  unless the designer explicitly adds the entry with a higher threshold.
- Runtime object: `AIGroupObject` (`app/engine/objects/ai_group.py:5-38`) —
  `trigger(unit_nid, num_units_in_group)` (`:13-20`) adds the unit to a
  `triggered` set and returns true once
  `len(triggered) >= min(trigger_threshold, num_units_in_group)`; `clear()`
  empties it (called on every unit at end of turn,
  `app/engine/general_states.py:2556-2558`).
- Trigger call sites: `ai_controller.py:274-296` (attack-goal path) and
  `:300-319` (move-goal path) — when a unit with a set `ai_group` finds a
  target, it calls `game.get_ai_group(unit.ai_group).trigger(...)`
  (`game_state.py:1094-1104`, returns `None` if the nid isn't registered on
  `game.level.ai_groups`); if the trigger fires, `ai_group_ping()`
  (`ai_controller.py:331-336`) marks the group `active`
  (`action.AIGroupPing`) and resets `has_run_ai = False` on every other
  same-team unit sharing that `ai_group` who hasn't yet moved/attacked — so
  the whole squad can act within the *same* enemy phase instead of only the
  spotting unit. `game.ai_group_active(nid)` (`game_state.py:1108-1121`) is
  what `-1`/"Guard" units poll to know whether to finally move.
- Units join a group purely via their own `ai_group: NID` field
  (`app/engine/objects/unit.py:65`); it also determines turn-order clustering
  in `general_states.py:2479-2521` (`cur_group`) — once one member of a
  group is chosen to act, the state machine keeps picking from that same
  group (sorted by distance-to-enemy, then priority) before moving on.
- Not to be confused with `unit_groups` (spawn/positioning groups used by
  reinforcement events) — a same-sounding but unrelated concept.

## 3. Code files

- `app/data/database/ai.py:1-115` — `AIPrefab`, `AIBehaviour`, `AICatalog`,
  the `AI_ActionTypes`/`AI_TargetTypes`/`unit_spec` vocabularies.
- `app/data/database/ai_groups.py:1-8` — `AIGroup` DB record.
- `app/data/database/levels.py:46,83-99` — per-level `ai_groups` storage and
  the `restore()` auto-heal logic.
- `app/engine/objects/ai_group.py:1-38` — `AIGroupObject` runtime
  trigger/threshold logic.
- `app/engine/ai_controller.py:200-336,620-628` — `view_range` resolution,
  the trigger/ping call sites, `ai_group_ping`, `offense_bias` weighting.
- `app/engine/game_state.py:1094-1133` — `get_ai_group`, `ai_group_active`,
  `get_units_in_ai_group`.
- `app/engine/general_states.py:2479-2521,2556-2558` — `cur_group`
  turn-order clustering and per-turn `AIGroupObject.clear()`.

## 4. Working example in this repo

`lion_throne.ltproj/game_data/ai.json` authors 17 presets (lines 1-657),
including `Guard` (priority 20, single `Attack`/`Enemy`/`view_range: -1`
behaviour — never moves unless its group is active), `Defend` (`Attack`/
`Enemy`/`-2`, then `Move_to`/`Position`/`"Starting"`/`-4` — falls back to
returning to spawn), `FollowBoss` (`Move_to`/`Ally` with `target_spec:
["Tag","Boss"]`), and `MonsterRoamAI` (`roam_ai: true`, single `Wait`
behaviour). For AI groups: level `S1` (`lion_throne.ltproj/game_data/
levels.json:166`) places units `S1_Unsafe1`/`S1_Unsafe2` (`:334-364`), both
`"ai": "Attack"` and `"ai_group": "S1UnsafeSquad"` — yet `S1`'s own
`"ai_groups": []` array (`:443`) is empty, so this squad only works because
of the `LevelPrefab.restore()` auto-heal described above, and both units get
the default `trigger_threshold=1` (i.e. either one spotting the player wakes
the other immediately — the threshold-tuning knob is unexercised here).
Similar `S2UnsafeSquad`/`S3UnsafeSquad`/`S4UnsafeSquad` groups exist on their
respective levels the same way. Of the 94 unit entries in `levels.json`, 22
use the `Attack` preset, 12 `Defend`, 9 `Guard`, 9 `Pursue`, confirming these
presets are the actual backbone of this project's enemy AI, not just sample
data.

## 5. Test

`tools/test_enemy_pool.py` (around line 255-280) checks only that `ai_group`
survives the procedural-enemy-generation pipeline
(`generated.ai_group == 'ProcTestGroup'`) — it never drives `AIController`,
`AIGroupObject.trigger`, threshold behavior, or any behaviour/targeting logic.
No test covers `view_range` resolution, `offense_bias` weighting, or the
`LevelPrefab.restore()` auto-heal. A `tools/test_ai_groups.py` should exist
that, after `harness.boot()` on a level with two `ai_group`-tagged units and
an explicit `AIGroup(nid, trigger_threshold=2)` registered, asserts
`ai_group.trigger()` returns `False` after only one unit calls it and `True`
once the second does, and that `ai_group_ping` correctly clears `has_run_ai`
on the sibling; a second case should load a level whose `ai_groups` list is
empty despite a unit referencing a group nid, and assert
`LevelPrefab.restore()` synthesizes a `trigger_threshold=1` entry rather than
leaving `game.get_ai_group(nid)` returning `None`.
