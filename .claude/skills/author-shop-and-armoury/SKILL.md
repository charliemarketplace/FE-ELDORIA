---
name: author-shop-and-armoury
description: Author a shop event that lets a unit buy/sell from a designer-picked item list, choose whether it's flavored as a vendor, armoury, or custom shop, and optionally cap per-item stock that's remembered across future visits via a shared ShopId.
---

## 1. Feature

The `shop` event command drops a unit into a self-contained buy/sell menu
built from an arbitrary list of items the designer supplies inline in the
event script — no separate "shop inventory" data object to maintain. A
single command controls what's for sale, how much of it there is, what
flavor text/portrait frames the transaction (vendor vs. armoury vs. a
project-defined custom flavor), and whether stock persists (shared) across
multiple visits to logically "the same" shop. This is how every
non-narrative commerce screen in an LT game is built — town shops, boss
loot vendors, base-camp armouries.

## 2. Details

### 2.1 The `shop` command (`app/events/event_commands.py:2765-2779`)

| Keyword | Required | Type | Default when omitted |
|---|---|---|---|
| `Unit` | yes | Unit | — the unit who "visits" the shop (their gold, inventory space, and tradeable items drive the buy/sell menus) |
| `ItemList` | yes | ItemList (comma-separated item nids) | — |
| `ShopFlavor` | no | `ShopFlavor` (`vendor`/`armory`/anything) | `'armory'` (`app/events/event_functions.py:2893-2896`) |
| `StockList` | no | IntegerList, same order as `ItemList` | `None` → unlimited stock for every item |
| `ShopId` | no | Nid | the event's own nid (`self.nid`), used as the persistence key |

Implementation: `app/events/event_functions.py:2880-2908` (`shop()`). It
stores everything the `shop` state needs into `game.memory` (`shop_id`,
`current_unit`, `shop_items` built via `item_funcs.create_items`,
`shop_flavor`, `shop_stock`) then does `game.state.change('shop')`.

### 2.2 Stock (`StockList`)

- `-1` for an index means unlimited stock for that item (per the command's
  own docstring).
- On each `shop` call, before the state opens, the engine subtracts
  previously-recorded purchases from `StockList`: for each item it checks
  `game_vars['__shop_<ShopId>_<item_nid>']` and, if present, subtracts that
  count from the authored stock number
  (`event_functions.py:2898-2904`). This is what makes stock "remembered
  across shops with the same ShopId" per the command's docstring.
- **Gotcha, verified in code**: the purchase counter is written
  inconsistently with how it's read back. At buy time
  (`app/engine/general_states.py:2714-2715`):
  ```python
  stock_marker = '__shop_%s_%s' % (self.shop_id, item.nid)
  action.do(action.SetGameVar(stock_marker, game.level_vars.get(stock_marker, 0) + 1))
  ```
  it increments from `game.level_vars` (cleared to empty every time a new
  level starts — `app/engine/game_state.py:237`), but `SetGameVar` writes
  into `game.game_vars` (persists across levels,
  `app/engine/action.py:543-550`), and the *read-back* in `shop()` at the
  next visit also checks `game.game_vars` (`event_functions.py:2902`).
  Net effect: because the increment always reads a fresh `0` from
  `level_vars` (which never has the key — nothing ever writes there),
  buying the same item more than once in a single shop visit keeps
  resetting the persisted counter back to `1` instead of accumulating.
  Only the *last* purchase of a session is what's remembered the next time
  that `ShopId` is reopened, so a player who buys 3 of a 3-stock item in one
  visit will find 2 back in stock (`3 - 1`) on a later visit instead of 0.
  This bug is present in the shared engine code, not project-specific data,
  and is unexercised by this project (see §4) since no shop here uses
  `StockList`.
- `self.buy_menu.get_stock()` (`app/engine/menus.py:730-734`) returns `-1`
  (never blocking a purchase) whenever `stock` wasn't passed to the menu at
  all, which is exactly what happens when `StockList` is omitted.

### 2.3 Flavor (`ShopFlavor`)

`ShopState.start()` (`app/engine/general_states.py:2569-2613`) uses the
flavor string to key into `SPRITES` for a `<flavor>_portrait` and into
`DB.translations` for `<flavor>_opener` / `<flavor>_buy` / `<flavor>_back` /
`<flavor>_leave` / `<flavor>_buy_again` / `<flavor>_convoy` /
`<flavor>_no_stock` / `<flavor>_no_money` / `<flavor>_max_inventory` /
`<flavor>_sell_again` / `<flavor>_again` / `<flavor>_no_value`. If a given
`<flavor>_X` translation key doesn't exist, `apply_flavor()`
(lines 2579-2583) falls back to the generic `shop_X` key instead — so a
custom flavor only needs to override the lines it actually wants to
customize; everything else silently falls back to the stock `shop_*`
copy. The portrait sprite itself has no such fallback: `SPRITES.get('%s_portrait' % flavor)` returns whatever that lookup yields (including `None`
if the sprite sheet doesn't exist for that flavor).

Because `shop()` always assigns *some* string to `game.memory['shop_flavor']`
(defaulting to `'armory'` when the keyword is omitted), `ShopState`'s
`if self.flavor:` branch (line 2585) is always taken in practice — the
`else` branch (hardcoded `armory_*`/`shop_*` messages, lines 2599-2612) is
effectively dead code reachable only if something else sets
`game.memory['shop_flavor']` to a falsy value directly.

### 2.4 Buy/sell mechanics (`ShopState`, `app/engine/general_states.py:2569-2842`)

- Opens with `opening_message`, then a `Buy`/`Sell` choice
  (`Sell` only enabled if the visiting unit has any
  `item_funcs.get_all_tradeable_items`).
- **Buy** (lines 2701-2738): computes `item_funcs.buy_price(unit, item)`,
  blocks the purchase (with a flavored failure message) if gold is
  insufficient, stock is `0`, or the unit's inventory is full **and**
  `_convoy` isn't on (see `configure-convoy-and-storage`) — if `_convoy` is
  on and the buyer's inventory is full, the purchased item is routed
  straight into the party convoy instead of failing.
- **Sell** (lines 2740-2759): uses `item_funcs.sell_price`; an item with no
  sell value (`sell_price` returns falsy) shows the `no_value_message`
  instead of completing.
- Every successful trade calls `action.HasTraded(unit)`; closing the shop
  afterward marks the unit as having attacked (`action.HasAttacked`,
  lines 2764-2765/2773-2774) — i.e. visiting a shop spends the unit's turn
  exactly like an attack does, once a trade has happened.
- `RepairShopState` (`app/engine/general_states.py:2844+`) is a
  `ShopState` subclass with its own `start()` for the repair-shop variant;
  gated separately by the `repair_shop` DB constant and `_repair_shop`
  game_var (`enable_repair_shop` event command,
  `app/events/event_commands.py:895-906`).

### 2.5 What happens if you omit fields

- Omit `ShopFlavor` → `'armory'`.
- Omit `StockList` → unlimited stock, `get_stock()` always `-1`.
- Omit `ShopId` → keyed off the event's own nid, so two different `shop`
  calls inside the *same* event (unlikely) would collide, but two calls in
  two different events never do unless you explicitly pass a shared
  `ShopId`.
- Omit `Unit` or pass a nid that doesn't resolve → `shop()` logs
  `"shop: Must have a unit visit the shop!"` and returns without changing
  state (`event_functions.py:2882-2884`) — no crash, shop just never opens.

## 3. Code files

- `app/events/event_commands.py:2765-2779` — the `Shop` command definition.
- `app/events/event_functions.py:2880-2908` — `shop()`, item creation,
  stock-carryover math, `game.memory` staging.
- `app/events/event_validators.py:676-683` — `ShopFlavor` validator
  (`"defaults to armory"`, valid options `vendor`/`armory`).
- `app/engine/general_states.py:2569-2842` — `ShopState` (buy/sell UI,
  flavor-to-translation-key mapping, stock decrement bug at 2714-2716).
- `app/engine/general_states.py:2844+` — `RepairShopState`.
- `app/engine/menus.py:712-745` — the `Shop` menu widget (`get_stock`,
  `decrement_stock`).
- `app/events/event_commands.py:895-906` — `EnableRepairShop`.

## 4. Working example in this repo

Live. Event nid `CAPITAL Vendor` (`lion_throne.ltproj/game_data/events.json`,
level `CAPITAL`) runs:
```
transition;Close
shop;{unit};Vulnerary,Potion,Fire,Heal;vendor
transition;Open
```
— explicit `vendor` flavor, no `StockList` (unlimited), no `ShopId`
(defaults to the event's own nid). Five other shop calls exist in this
project (e.g. one selling `Steel Sword,Steel Lance,Steel Axe,EMB_CinderVial`
and one omitting `ShopFlavor` entirely to get the default `armory` look),
but **none of the six live shops in this project use `StockList` or
`ShopId`** — the persistence bug in §2.2 is real, verified engine
behaviour, but unexercised by this project's own data.

## 5. Test

`tools/test_capital_completion.py:275-317` already exercises part of this:
it parses the `CAPITAL Vendor` event's `shop;` line, replicates the real
buy-path (`item_funcs.buy_price` → `action.GainMoney` → `action.GiveItem`)
against the actual `Vulnerary` item and asserts the price matches the
authored `items.json` value (`300`) and that gold/inventory move by exactly
that amount. It does **not** drive `ShopState` itself, and does not cover
`ShopFlavor` (vendor vs. armory message/portrait differences), `StockList`
carryover across visits, or the `Sell` path. A `tools/test_shop_stock.py`
should exist that: calls `shop()` with a `StockList` of `[1]` and a fixed
`ShopId`, buys the item via `ShopState.take_input`, closes the shop, calls
`shop()` again with the same `ShopId`/`ItemList`, and asserts the reopened
stock is `0` (the correct behaviour) rather than `1` (today's buggy carry
value) — proving or disproving the level_vars/game_vars mismatch in
§2.2 end-to-end.
