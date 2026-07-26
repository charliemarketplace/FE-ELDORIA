---
name: configure-convoy-and-storage
description: Turn on the party's shared item convoy/storage (prep, base, and on-map long-range storage), route items straight into a specific party's convoy from an event, and scope storage per-party in a multi-party game via parties.json.
---

## 1. Feature

Every `PartyObject` (`lion_throne.ltproj/game_data/parties.json`) carries a
`convoy` — a shared item pool independent of any one unit's inventory.
Enabling it unlocks a "Storage"/"Items" option in the map item menu, prep
screen, and base, lets shops send overflow purchases to it instead of
failing, and lets events push items into it directly (optionally into a
*named* party's convoy, for multi-party projects). None of this requires
extra data beyond flipping one game_var and, optionally, calling one event
command per item.

## 2. Details

### 2.1 The gate: `_convoy` game_var

Everything convoy-related is gated behind `game.game_vars.get('_convoy')`,
which is `None`/falsy until the `enable_convoy` event command sets it:

```
class EnableConvoy(EventCommand):
    nid = 'enable_convoy'
    keywords = ["Activated"]
    keyword_types = ['Bool']
```
(`app/events/event_commands.py:883-893`) →
`action.do(action.SetGameVar("_convoy", activated))`
(`app/events/event_functions.py:611-612`). There is no DB constant that
turns this on by default and no other code path sets `_convoy` — it is
purely event-authored. Everywhere it's checked:

- `app/engine/general_states.py:1324,1326` — whether the map "hold item →
  Storage" option appears on a unit's item at all (see §2.3).
- `app/engine/general_states.py:1436,1439,1441` — same gate for the
  "Discard" vs. "Storage" choice when the current unit's own inventory item
  menu opens.
- `app/engine/general_states.py:2709,2722` — whether a shop purchase that
  doesn't fit in the buyer's inventory goes to convoy instead of failing
  outright (see `author-shop-and-armoury`).
- `app/engine/prep.py:767` — whether prep's "Optimize All" (auto-equip the
  whole party from convoy) is available at all; if `_convoy` is falsy,
  selecting it shows an `"Convoy not available"` alert banner instead.
- `app/engine/prep.py:847-848` — swaps the prep manage menu's `Use` option
  label for `Items` (the convoy browser) once convoy is on.
- `app/engine/prep.py:853-869` (`get_ignore`) — with convoy off, only
  `Use` (base-item consumption) is ever enabled; with convoy on, `Restock`,
  `Give all`, and `Items` become selectable (each further gated by whether
  there's anything to restock/give/hold).

### 2.2 Reachability in this project — verified unreachable today

`grep`-ing every `_source` line across
`lion_throne.ltproj/game_data/events.json` finds **zero** calls to
`enable_convoy` (and zero `open_convoy` calls, and zero `give_item;Convoy`
calls — see §2.4). `_convoy` is therefore never set, so:
- The prep/base "Items"/convoy-browse option never appears (`Use` is shown
  instead, per `prep.py:847-848`).
- `Optimize All` always shows `"Convoy not available"`.
- A shop purchase with a full inventory always fails outright — it can
  never spill into a convoy that isn't enabled.

This is a fully-built, non-trivial engine system (multi-party scoped,
turnwheel-safe, with its own auto-equip heuristics in `convoy_funcs.py`)
that is present and consumable, but currently switched off by omission —
no event in this project's data calls `enable_convoy;true`. Turning it on
is a one-line addition to any early-game event (e.g. right after
`Global Reveal Overworld` or a chapter-1 intro).

### 2.3 On-map long-range storage vs. adjacency requirement

Even with `_convoy` on, whether "Storage" is offered for a held item
depends on the `long_range_storage` DB constant
(`app/data/database/constants.py:88`, default `True`):
- `long_range_storage = True` → Storage is available from anywhere on the
  map (`general_states.py:1324,1436`).
- `long_range_storage = False` → Storage only appears if
  `SupplyAbility.targets(self.cur_unit)` is true — i.e. the unit must be
  within range of an actual Supply-tagged tile/unit
  (`general_states.py:1326,1441`).
This project's `constants.json` has `long_range_storage: true` (matches the
engine default), so storage would be available anywhere on the map the
moment `_convoy` is turned on.

### 2.4 Event-side access

| Command | File:line | What it does |
|---|---|---|
| `enable_convoy;Activated` | `event_commands.py:883-893` | Toggles `_convoy` |
| `open_convoy;GlobalUnit[;include_other_units]` | `event_commands.py:1662-1675` | Immediately opens the convoy-browsing screen (`supply_items` state) for that unit, regardless of whether `_convoy` is set — this is a direct entry point independent of the prep/base menu gating. `include_other_units` also folds in items currently held by other party units, not just what's already in `party.convoy` (`event_functions.py:1572-1583`). |
| `give_item;convoy;Item[;Party]` | `event_commands.py:1582-1599` | `GlobalUnitOrConvoy` accepts the literal string `convoy` (case-insensitive) to route a freshly-created item straight into a party's convoy instead of a unit's inventory; the optional `Party` keyword targets a *specific* party's convoy by nid — this is the multi-party hook (`event_functions.py:1399,1403-1404,1445-1450`, `action.PutItemInConvoy(item, party)`). Omit `Party` and it goes to whatever `game.get_party(None)`/the current party resolves to. |
| `remove_item;convoy;Item[;Party]` | mirrors `give_item` | Removes an item from a (specific) party's convoy. |

### 2.5 Underlying actions (turnwheel-safe) — `app/engine/action.py`

- `PutItemInConvoy(item, party_nid=None)` (1193-1207) — un-owns the item
  and appends it to `game.get_party(party_nid).convoy`; reverse pops it
  back to its original owner.
- `TakeItemFromConvoy(unit, item, party_nid=None)` (1210-1227) — moves an
  item from a party's convoy into a unit's inventory.
- `RemoveItemFromConvoy(item, party_nid=None)` (1229-1241) — deletes an
  item from convoy outright (no owner to restore to).
- `TradeItemWithConvoy(unit, convoy_item, unit_item)` (1266-1285) — swaps
  one of a unit's items for one sitting in convoy in a single reversible
  step, preserving the unit's item-slot index. Always targets
  `game.party` (the *current* party), not an arbitrary `party_nid`.

### 2.6 Auto-management helpers — `app/engine/convoy_funcs.py` (full file)

- `can_restock(item)` / `restock(item)` / `restock_convoy()` (5-36) —
  finds other copies of the same item nid sitting in convoy with fewer
  uses remaining and consolidates uses onto the highest-durability copy,
  discarding the exhausted ones. Always operates on `game.party.convoy`
  (current party only).
- `optimize_all()` (38-86) — stores every storeable item every fielded/
  rescued unit is carrying, restocks, then redistributes weapons/spells/
  healing items from convoy back out to units by a fixed heuristic (rank,
  remaining uses, inventory space). This is what prep's `Optimize All`
  calls (§2.1).
- `optimize(unit)` (89-130) — the single-unit version (used by the
  per-unit `Optimize`/`Repair` prep option).
- `trade_items(convoy_item, unit_item, unit)` (141-148) — used by the
  interactive convoy-trade UI; routes to `TradeItem` (unit-to-unit) instead
  of `TradeItemWithConvoy` if the convoy item happens to still have an
  `owner_nid` (i.e. it's not actually convoy-owned, an edge case from
  mixed unit/convoy trade menus).

### 2.7 `convoy_on_death` constant — malformed but effectively-on default

`app/data/database/constants.py:121`:
```python
Constant('convoy_on_death', "Items held by dead player units are sent to convoy", ConstantType.BOOL, ConstantTag.OTHER),
```
This call is missing its `default_value` positional argument — `Constant.__init__` is `(nid, name, attr, default_value=False, tag=ConstantTag.OTHER)`, so `ConstantTag.OTHER` (a truthy `str` enum member) lands in the `default_value` slot instead of an explicit `True`/`False`, and `tag` falls back to its own keyword default (also `ConstantTag.OTHER`). The single consumer,
`app/engine/game_state.py:749` (`elif DB.constants.value('convoy_on_death'):`), only checks truthiness, so this happens to behave as "on by default" — but it is not a real boolean default, and any code that ever compared it with `== True` would get `False`. This project's `constants.json` pins it explicitly to `true` (line 215-217), so the ambiguity doesn't affect this project's build either way. The `give_and_take` constant one line below (`constants.py:122`, consumed at `app/engine/abilities.py:204`) has the identical malformed call.

### 2.8 Multi-party scoping

`PartyObject` (`app/engine/objects/party.py`, full file) stores `convoy`
as a plain list of `ItemObject`s per party; `game.get_party(nid)` resolves
which party's convoy an action touches. This project's
`lion_throne.ltproj/game_data/parties.json` defines exactly one party
(`Emberwake`, led by `Rowan`), so the `Party`/`party_nid` scoping in §2.4/
§2.5 is unexercised here — a project with two simultaneous parties (e.g. a
split-route chapter) would author a second entry in `parties.json` and use
`Party` on `give_item`/`remove_item` to keep their stashes separate.

## 3. Code files

- `app/events/event_commands.py:883-893` (`EnableConvoy`),
  `1662-1675` (`OpenConvoy`), `1582-1599` (`GiveItem`'s `convoy` target).
- `app/events/event_functions.py:611-612` (`enable_convoy`),
  `1572-1583` (`open_convoy`), `1399-1450` (`give_item`).
- `app/engine/action.py:1193-1286` — `PutItemInConvoy`/
  `TakeItemFromConvoy`/`RemoveItemFromConvoy`/`TradeItemWithConvoy`.
- `app/engine/convoy_funcs.py` (full file) — restock/optimize heuristics.
- `app/engine/objects/party.py` (full file) — `PartyObject.convoy`.
- `app/engine/general_states.py:1324-1326,1436-1441,2701-2738` — map/shop
  gating on `_convoy`.
- `app/engine/prep.py:740-869` — prep manage menu gating.
- `app/data/database/constants.py:88` (`long_range_storage`), `:121-122`
  (`convoy_on_death`, `give_and_take`).
- `lion_throne.ltproj/game_data/parties.json` — this project's single
  `PartyObject`.

## 4. Working example in this repo

**Not reachable as currently authored.** No event in
`lion_throne.ltproj/game_data/events.json` calls `enable_convoy`,
`open_convoy`, or `give_item;convoy`, and `parties.json` has a single party.
The closest analogue is the shop's fallback path
(`app/engine/general_states.py:2709,2722`,
`author-shop-and-armoury`) which *would* route an over-full purchase into
convoy the moment `_convoy` is set true — that's the one place convoy
plumbing is already wired into this project's live shop code, just
currently dead because the gate is never flipped.

## 5. Test

No `tools/test_*.py` references `_convoy`, `enable_convoy`,
`PutItemInConvoy`, or `convoy_funcs` (checked all files under `tools/`). A
`tools/test_convoy_access.py` should exist that: (1) asserts `_convoy` is
falsy and the prep manage menu's `Items` option is `ignore`d by default;
(2) calls `action.do(action.SetGameVar('_convoy', True))` and re-derives
`PrepManageSelectState.get_ignore()`, asserting `Items` becomes selectable;
(3) does `action.do(action.PutItemInConvoy(item))` on a real item and
asserts it appears in `game.party.convoy` and no longer has an owner, then
reverses the action and asserts it's back on the original unit; (4) creates
a second `PartyObject` in memory, calls `action.PutItemInConvoy(item, other_party_nid)`, and asserts the item lands in *that* party's convoy, not
`game.party`'s — proving the multi-party scoping actually isolates the two
stashes.
