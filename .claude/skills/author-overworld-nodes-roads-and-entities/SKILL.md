---
name: author-overworld-nodes-roads-and-entities
description: Author the overworld's world-map skeleton — reveal nodes and roads progressively via events, toggle a node's menu options on/off, and spawn/move standalone "dummy" entities for cinematics or reinforcements — distinct from the roster-based entry gating on a node.
---

## 1. Feature

Beyond deciding *whether* a node is enterable (already covered by
`req_unit_count`/`req_unit_level` roster gating, excluded from this
catalogue), the overworld system lets a designer control the map's
progressive reveal: fade in a node or the road between two nodes as the
story unlocks new territory, enable/disable individual custom menu options
on a node (e.g. a "Talk to the Merchant" option that only appears once a
side-quest starts), and create free-standing "entity" sprites on the
overworld map for cinematics or visible enemy reinforcements — all
independent of the player's actual travelling party, which the engine
creates and positions automatically from `parties.json`.

## 2. Details

### 2.1 Party entities are automatic, not authored

Every entry in `DB.parties` (`lion_throne.ltproj/game_data/parties.json`)
gets exactly one `OverworldEntityObject` of type `PARTY` created for it the
moment an overworld loads — `Overworld.from_prefab()`
(`app/engine/objects/overworld/overworld.py:159-175`) loops
`party_registry.keys()` and calls
`OverworldEntityObject.from_party_prefab(None, pnid, unit_registry)` for
each, using the party's `leader` unit for the map sprite/sound
(`app/engine/objects/overworld/overworld_entity.py:41-66`). There is no
event command to "spawn the player's party" — it already exists,
initially with `on_node = None` (off-map) until something (typically
`set_overworld_position`, or the normal chapter-completion flow) places it
on a node. `create_overworld_entity`/`disable_overworld_entity` (§2.4)
instead manage a *different* entity kind — `UNIT`-type "dummy" entities —
for anything that isn't a real travelling party.

### 2.2 Revealing nodes and roads

| Command | File:line | Behaviour |
|---|---|---|
| `reveal_overworld_node;OverworldNodeNid[;immediate]` | `event_commands.py:3369-3377`, `overworld_event_functions.py:176-190` | Calls `overworld.enable_node(nid)` (adds to `enabled_nodes`, then `regenerate_explored_graph()`); without `immediate`, the node's sprite plays a `fade_in` transition and the event blocks for `node.sprite.transition_time`. |
| `reveal_overworld_road;Node1;Node2[;immediate]` | `event_commands.py:3379-3387`, `overworld_event_functions.py:192-213` | **Silently no-ops** unless both `Node1` and `Node2` are already in `overworld.revealed_node_nids` *and* are graph-neighbors (`overworld.connected_nodes(node1, force=True)`) — reveal both endpoint nodes first, in the same or an earlier event, or the road never appears and no error is logged. Also no-ops (this time via `self.logger.error`) if the two nodes aren't connected by any road in `overworlds.json` `map_paths` at all. |

Both are additive-only — there's no `hide_overworld_node`/
`hide_overworld_road` command; once revealed, a node/road stays revealed
for the rest of the save (state lives in `Overworld.enabled_nodes`/
`enabled_roads`, which are saved — `overworld.py:177+`).

### 2.3 Node menu options

A node's `menu_options` (`app/data/database/overworld_node.py:15`, a
`NodeEventCatalogue` of `NodeMenuEvent`s) are custom entries shown in the
party's node menu (`OverworldPartyOptionMenu`,
`app/engine/overworld/overworld_states.py:382-449`) alongside the built-in
"Base Camp" option. Each option independently tracks **enabled** and
**visible** state per node, seeded from the option's authored
`enabled`/`visible` defaults at overworld load
(`overworld.py:170-174`), and can be flipped at runtime:

- `set_overworld_menu_option_enabled;OverworldNodeNid;OverworldNodeMenuOption;Setting`
  (`event_commands.py:3426-3433`) → `overworld.toggle_menu_option_enabled(...)`.
- `set_overworld_menu_option_visible;OverworldNodeNid;OverworldNodeMenuOption;Setting`
  (`event_commands.py:3434-3441`) → `overworld.toggle_menu_option_visible(...)`.

Per both commands' own docstrings: **visibility gates enabled-ness in the
UI**, not the reverse — `OverworldPartyOptionMenu.start()`
(`overworld_states.py:400-411`) filters the option list down to only the
*visible* options first, then marks each of those `ignore`d/not based on
*enabled*. An option that's enabled but not visible never appears in the
menu at all; the player can't discover it exists.

### 2.4 Standalone "dummy" entities (cinematics/reinforcements)

- `create_overworld_entity;Nid[;Unit][;Team]` (`event_commands.py:3389-3398`,
  `overworld_event_functions.py:215-231`) — creates a `UNIT`-type entity
  (`OverworldEntityObject.from_unit_prefab`) using `Unit`'s map sprite.
  **`Unit` is technically optional in the keyword list but functionally
  required**: the implementation only does anything `if unit:` — omit it
  and the command silently does nothing (no entity, no error logged).
  `Team` defaults to `'player'` if omitted or not a valid `DB.teams` nid
  (`overworld_event_functions.py:228-229`). Passing the `delete` flag
  instead deletes the entity with that `Nid` and ignores `Unit`/`Team`
  entirely.
- `disable_overworld_entity;Nid[;no_animate]`
  (`event_commands.py:3400-3406`, `overworld_event_functions.py:233-243`)
  — fades the entity's sprite out (unless `no_animate`) and clears its
  `on_node`/`display_position`, effectively hiding it without deleting the
  object (contrast with `create_overworld_entity`'s `delete` flag, which
  removes it outright).
- `set_overworld_position;OverworldEntity;OverworldLocation[;no_animate]`
  (`event_commands.py:3347-3353`, `overworld_event_functions.py:44-77`) —
  moves any entity (party or dummy) to a raw `(x, y)` coordinate or onto a
  named node. Moving onto a node **requires that node already be revealed**
  (`if overworld_node_nid not in overworld.revealed_node_nids:` → logs an
  error and returns, `overworld_event_functions.py:67-70`) — reveal the
  destination node first.
- `overworld_move_unit;OverworldEntity[;OverworldLocation][;Speed][;PointList]`
  (nickname `omove`, `event_commands.py:3355-3367`,
  `overworld_event_functions.py:78-174`) — animates travel rather than
  teleporting. `Speed` defaults to `5` if omitted (higher = slower, per the
  docstring). Accepts either a target node/coordinate (pathfinds across
  revealed roads via `overworld.any_path`) or an explicit `PointList`
  waypoint chain, which takes priority if both are given. Flags:
  `no_block` (script continues while it walks), `no_follow` (camera
  doesn't pan to track it — the default *does* follow, via
  `game.camera.do_slow_pan`/`set_center`), `disable_after` (fades out and
  clears the entity's position when the move finishes — the cinematic
  "reinforcement walked off-screen" pattern), `no_sound`.
- `overworld_cinematic;[OverworldNID]` (`event_commands.py:3339-3345`,
  `overworld_event_functions.py:19-42`) — switches the background to the
  overworld map itself so events can stage a cutscene there;
  `OverworldNID` defaults to the first overworld in the DB if omitted, or
  logs an error if the DB has no overworlds at all. Also unloads the
  current level's board/boundary from `game`, remembering unit positions
  in `game.level_vars['_prev_pos_<tilemap_nid>']` for restoration.
- `enter_level_from_overworld;LevelNid` (`event_commands.py:3442-3448`) —
  the direct way to start a specific level from an overworld event script
  rather than through the node-click flow.

### 2.5 What happens if you omit fields

- `reveal_overworld_road` before both endpoint nodes are revealed → silent
  no-op, no error, road never appears (§2.2).
- `create_overworld_entity` without `Unit` → silent no-op, no entity
  created (§2.4).
- `set_overworld_position` targeting an unrevealed node → logged error,
  position unchanged.
- `overworld_move_unit` with neither `OverworldLocation` nor `PointList` →
  logged error, no movement.
- `set_overworld_menu_option_visible` never called for a custom option →
  falls back to whatever `NodeMenuEvent.visible` was authored on the node
  itself (`overworld.py:170-174` seeds from the prefab at load).

## 3. Code files

- `app/events/event_commands.py:3339-3448` — all ten overworld commands.
- `app/events/overworld_event_functions.py` (full file, 306 lines) — every
  implementation in §2.2-§2.4.
- `app/engine/objects/overworld/overworld.py:159-175` — automatic party
  entity seeding, node menu-option enabled/visible seeding.
- `app/engine/objects/overworld/overworld_entity.py` (full file) —
  `OverworldEntityObject`, `from_party_prefab` vs. `from_unit_prefab`.
- `app/engine/overworld/overworld_manager.py:19-33,130-208` —
  `enable_node`/`enable_road`/`toggle_menu_option_enabled`/
  `toggle_menu_option_visible`/`add_entity`/`delete_entity`/
  `selected_entity`.
- `app/engine/overworld/overworld_states.py:382-449` —
  `OverworldPartyOptionMenu`, where visible/enabled menu options actually
  get filtered and drawn.
- `app/data/database/overworld_node.py` (full file) — `OverworldNodePrefab`,
  its `menu_options` catalogue.
- `lion_throne.ltproj/game_data/overworlds.json` — this project's node/road
  data (`overworld_nodes`, `map_paths`).
- `lion_throne.ltproj/game_data/parties.json` — the party roster that
  drives automatic entity creation.

## 4. Working example in this repo

Live. Event nid `Global Reveal Overworld`
(`lion_throne.ltproj/game_data/events.json`, trigger `overworld_start`)
reveals every node and every road in the map at once, immediately:
```
reveal_overworld_node;CAPITAL;immediate
reveal_overworld_node;S1;immediate
reveal_overworld_node;S2;immediate
reveal_overworld_node;SHUB;immediate
reveal_overworld_node;S3;immediate
reveal_overworld_node;S4;immediate
reveal_overworld_node;S5;immediate
reveal_overworld_road;CAPITAL;S1;immediate
reveal_overworld_road;S1;S2;immediate
reveal_overworld_road;S2;SHUB;immediate
reveal_overworld_road;S3;S4;immediate
reveal_overworld_road;S4;S5;immediate
reveal_overworld_road;SHUB;S3;immediate
```
Note the node reveals are correctly ordered before the road reveals that
depend on them (§2.2). This project's `overworlds.json` defines all seven
nodes with empty `menu_options: []` on every one, and its single party
`Emberwake` is the only auto-created entity
(`overworld.entities['Emberwake']`). **`create_overworld_entity`,
`overworld_move_unit`, `set_overworld_position`,
`set_overworld_menu_option_enabled/visible`, and `overworld_cinematic` are
never called anywhere in this project's event data** — this project only
ever uses the progressive-reveal half of the system, not the dummy-entity/
custom-menu-option half. The closest analogue for entity movement is the
implicit one: the real `Emberwake` party's `on_node` advances automatically
as `EnterLevelFromOverworld`/node completion moves the player between the
statically-defined nodes.

## 5. Test

`tools/test_overworld_gating.py` exists but only exercises
`req_unit_count`/`req_unit_level` roster-based node gating (already
excluded from this catalogue), not reveal/road/entity/menu-option
mechanics — confirmed by grepping it for `reveal_overworld`,
`create_overworld_entity`, and `menu_option`, all absent. A
`tools/test_overworld_authoring.py` should exist that: asserts a fresh
overworld's `revealed_node_nids` is empty (or matches whatever's
pre-enabled) before `Global Reveal Overworld` fires; runs that event and
asserts all seven node nids and six road pairs are now enabled; calls
`reveal_overworld_road` on two nodes where only one has been revealed and
asserts the road stays disabled (proving the ordering dependency in
§2.2); and calls `create_overworld_entity` with `Unit` omitted, asserting
no new entity appears in `game.overworld_controller.entities` (proving the
silent-no-op in §2.4).
