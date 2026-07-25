#!/usr/bin/env python3
"""Generate visually distinct MONSTER/CREATURE map sprites by programmatically
recolouring existing Lex Talionis map sprites -- no image-generation API involved.

Usage:
    uv run --no-project --python 3.12 --with pillow python tools/make_monster_sprites.py

This script is deterministic and safe to re-run: it always recomputes the
recoloured sprites from the *original* source sprites (never from a
previously generated monster sprite), and it only ever *appends* new,
missing entries to map_sprites.json / classes.json. Re-running it produces
byte-identical output and never touches an existing sprite or data entry.

Transform
---------
Each recipe below performs a deterministic "palette lock" recolour in HSV
space:
  * every pixel that exactly matches the sprite's transparency key colour is
    left completely untouched (byte-for-byte), so the sprite's silhouette /
    transparency continues to work exactly as before.
  * every other pixel has its hue snapped to a single fixed target hue
    (the class's "theme colour"), and its saturation/value scaled by fixed
    factors. Because the *value* (brightness) channel is preserved from the
    source pixel, all of the shading, folds, highlights and shadows painted
    into the original template sprite survive -- only the *colour family*
    changes. This is the classic "palette swap" recolour technique, and it
    is obviously and immediately visually distinct from the source class
    while still clearly being built from the same underlying template.

Sources -> monsters:
  * Fighter    -> Ghoul       (sickly yellow-green, slightly darkened/grimy)
  * Mage       -> Wraith      (pale, desaturated, brightened icy blue-white)
  * Mercenary  -> Hellhound   (deep, saturated crimson red)

Note: "Bishop" has map-sprite/portrait/combat-anim assets in this project
but is *not* an actual playable/enemy class in classes.json (this fangame's
Cleric line promotes into "Oracle", not "Bishop"), so Wraith is instead
modelled on "Mage" -- also anima/light-magic themed and an equally good fit
for a pale, ghostly caster-type monster.
"""
import colorsys
import json
import os
from typing import Tuple

from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_SPRITES_DIR = os.path.join(REPO_ROOT, "lion_throne.ltproj", "resources", "map_sprites")
MAP_SPRITES_JSON = os.path.join(MAP_SPRITES_DIR, "map_sprites.json")
CLASSES_JSON = os.path.join(REPO_ROOT, "lion_throne.ltproj", "game_data", "classes.json")
FACTIONS_JSON = os.path.join(REPO_ROOT, "lion_throne.ltproj", "game_data", "factions.json")

# The LT map-sprite transparency key colour, confirmed by inspecting the
# corner pixels (and dominant colour) of every existing sprite in the repo,
# e.g. Soldier-stand.png: corners are all (128, 160, 128), which is also by
# far the most common colour in the image (the flat background).
TRANSPARENCY_KEY: Tuple[int, int, int] = (128, 160, 128)


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def recolor_pixel(rgb: Tuple[int, int, int], target_hue: float, sat_scale: float,
                   sat_add: float, val_scale: float) -> Tuple[int, int, int]:
    """Palette-lock a single RGB pixel to `target_hue`, preserving its
    original brightness (value) pattern so shading/highlights survive."""
    if rgb == TRANSPARENCY_KEY:
        return rgb
    r, g, b = (c / 255.0 for c in rgb)
    _, s, v = colorsys.rgb_to_hsv(r, g, b)
    new_s = clamp01(s * sat_scale + sat_add)
    new_v = clamp01(v * val_scale)
    nr, ng, nb = colorsys.hsv_to_rgb(target_hue, new_s, new_v)
    out = (round(nr * 255), round(ng * 255), round(nb * 255))
    # Never accidentally produce the transparency key colour from a
    # non-key source pixel -- nudge the blue channel by 1 if we would.
    if out == TRANSPARENCY_KEY:
        out = (out[0], out[1], out[2] - 1 if out[2] > 0 else 1)
    return out


def recolor_image(im: Image.Image, target_hue: float, sat_scale: float,
                   sat_add: float, val_scale: float) -> Image.Image:
    im = im.convert("RGB")
    px = im.load()
    w, h = im.size
    cache = {}
    for y in range(h):
        for x in range(w):
            src = px[x, y]
            if src not in cache:
                cache[src] = recolor_pixel(src, target_hue, sat_scale, sat_add, val_scale)
            px[x, y] = cache[src]
    return im


# hue is expressed as degrees/360 for readability below.
def hue(deg: float) -> float:
    return (deg % 360.0) / 360.0


RECIPES = [
    {
        "source": "Fighter",
        "new_class": "Ghoul",
        "name": "Ghoul",
        "desc": "A rotting reanimated corpse, driven only by hunger for the living.",
        "target_hue": hue(100),   # sickly yellow-green
        "sat_scale": 1.0,
        "sat_add": 0.18,
        "val_scale": 0.90,        # slightly darker / grimier
    },
    {
        "source": "Mage",
        "new_class": "Wraith",
        "name": "Wraith",
        "desc": "A restless, half-corporeal spirit that drains warmth from the air around it.",
        "target_hue": hue(200),   # icy blue
        "sat_scale": 0.45,        # washed out / ghostly
        "sat_add": 0.0,
        "val_scale": 1.20,        # brightened, pale
    },
    {
        "source": "Mercenary",
        "new_class": "Hellhound",
        "name": "Hellhound",
        "desc": "A hulking, fire-scarred beast that hunts in the wake of dark magic.",
        "target_hue": hue(355),   # deep crimson red
        "sat_scale": 1.25,
        "sat_add": 0.12,
        "val_scale": 0.80,        # deep, dark red
    },
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def make_class_entry(recipe, source_class):
    """Build a new tier-1, no-promotion class entry modelled on its source
    class, per the shape used by every other tier-1 class in classes.json."""
    entry = json.loads(json.dumps(source_class))  # deep copy
    entry["nid"] = recipe["new_class"]
    entry["name"] = recipe["name"]
    entry["desc"] = recipe["desc"]
    entry["tier"] = 1
    entry["promotes_from"] = None
    entry["turns_into"] = []  # monsters have no promotion path
    tags = set(entry.get("tags", []))
    tags.add("Monster")
    entry["tags"] = sorted(tags)
    entry["max_level"] = 10
    # Modelled on the source class's stat spread, with a small monstrous
    # bump to HP/DEF and a slight trim to LCK, to read as a feral creature
    # rather than a re-skinned human soldier.
    entry["bases"] = dict(source_class["bases"])
    entry["bases"]["HP"] = entry["bases"]["HP"] + 2
    entry["bases"]["DEF"] = entry["bases"]["DEF"] + 1
    entry["bases"]["LCK"] = max(0, entry["bases"]["LCK"] - 1)
    entry["growths"] = dict(source_class["growths"])
    entry["growths"]["HP"] = min(200, entry["growths"]["HP"] + 15)
    entry["growths"]["LCK"] = max(0, entry["growths"]["LCK"] - 15)
    entry["growth_bonus"] = dict(source_class["growth_bonus"])
    entry["promotion"] = dict(source_class["promotion"])
    entry["max_stats"] = dict(source_class["max_stats"])
    entry["learned_skills"] = [list(pair) for pair in source_class["learned_skills"]]
    entry["wexp_gain"] = json.loads(json.dumps(source_class["wexp_gain"]))
    # No new portrait/combat-anim assets were generated (image-generation
    # APIs are explicitly out of scope), so reuse the source class's
    # existing, already-valid icon/combat-anim references.
    entry["icon_nid"] = source_class["icon_nid"]
    entry["icon_index"] = list(source_class["icon_index"])
    entry["map_sprite_nid"] = recipe["new_class"]
    entry["combat_anim_nid"] = source_class["combat_anim_nid"]
    entry["fields"] = list(source_class.get("fields", []))
    return entry


def main():
    print("== make_monster_sprites.py ==")
    map_sprites = load_json(MAP_SPRITES_JSON)
    classes = load_json(CLASSES_JSON)
    factions = load_json(FACTIONS_JSON)

    classes_by_nid = {c["nid"]: c for c in classes}
    map_sprites_original = list(map_sprites)  # preserved verbatim, appended-to only

    generated_sprites = []
    generated_classes = []

    for recipe in RECIPES:
        source = recipe["source"]
        new_class = recipe["new_class"]

        if source not in classes_by_nid:
            raise SystemExit(f"Source class {source!r} not found in classes.json")

        for suffix in ("stand", "move"):
            src_path = os.path.join(MAP_SPRITES_DIR, f"{source}-{suffix}.png")
            dst_path = os.path.join(MAP_SPRITES_DIR, f"{new_class}-{suffix}.png")
            if not os.path.exists(src_path):
                raise SystemExit(f"Missing source sprite {src_path}")

            src_im = Image.open(src_path)
            out_im = recolor_image(src_im, recipe["target_hue"], recipe["sat_scale"],
                                    recipe["sat_add"], recipe["val_scale"])
            out_im.save(dst_path)
            print(f"  wrote {os.path.relpath(dst_path, REPO_ROOT)} "
                  f"({out_im.size[0]}x{out_im.size[1]}, from {source}-{suffix}.png)")

        if new_class not in map_sprites:
            map_sprites.append(new_class)
            generated_sprites.append(new_class)
        else:
            print(f"  map_sprites.json already registers {new_class!r}; leaving as-is")

        if new_class not in classes_by_nid:
            new_entry = make_class_entry(recipe, classes_by_nid[source])
            classes.append(new_entry)
            classes_by_nid[new_class] = new_entry
            generated_classes.append(new_class)
        else:
            print(f"  classes.json already has class {new_class!r}; leaving as-is")

    # map_sprites.json: every original entry must be preserved exactly, in
    # order, with only new entries appended.
    assert map_sprites[:len(map_sprites_original)] == map_sprites_original, \
        "existing map_sprites.json entries were not preserved verbatim"
    save_json(MAP_SPRITES_JSON, map_sprites)
    save_json(CLASSES_JSON, classes)

    # factions.json: a "Monster" faction is required. One already exists in
    # this project (nid "Monster", icon "MonsterEmblem") -- append-only means
    # we must not duplicate/modify it, so we only add it if it is missing.
    faction_nids = {f["nid"] for f in factions}
    if "Monster" not in faction_nids:
        factions.append({
            "nid": "Monster",
            "name": "Monster",
            "desc": "A grotesque creature created by magic and born in darkness.",
            "icon_nid": "MonsterEmblem",
            "icon_index": [0, 0],
        })
        save_json(FACTIONS_JSON, factions)
        print("  appended 'Monster' faction to factions.json")
    else:
        print("  'Monster' faction already present in factions.json; left untouched")

    print(f"Generated/verified {len(RECIPES)} monster classes: "
          f"{[r['new_class'] for r in RECIPES]}")
    print(f"Newly appended sprites: {generated_sprites}")
    print(f"Newly appended classes: {generated_classes}")


if __name__ == "__main__":
    main()
