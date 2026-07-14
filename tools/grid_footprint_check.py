#!/usr/bin/env python
"""
grid_footprint_check.py -- render a tile-grid-with-coordinates overlay for an
LT tileset PNG, optionally with a level's region boxes drawn on top, so a
human or agent can see at a glance whether the *art* and the *data* (region
positions/sizes, terrain grid) agree.

This exists because Capital.png shipped with several building sprites drawn
2-3x larger than any sensible single-building footprint (see
.claude/skills/lt-ai-art-generation/SKILL.md, "Structure footprint budget"
section, for the authoring rule this tool is meant to catch violations of).
Re-run this after any map art edit to visually re-verify before moving on --
don't just assert the fix worked, look at the image.

Usage (run with Pillow available, e.g. via uv):
    uv run --no-project --python 3.12 --with pillow python tools/grid_footprint_check.py \\
        --tileset lion_throne.ltproj/resources/tilesets/Capital.png \\
        --tile-size 16 \\
        --level lion_throne.ltproj/game_data/levels.json --level-nid CAPITAL \\
        --out grid_overlay_Capital.png

Only --tileset is required; --tile-size defaults to 16 (LT's standard tile
size). Pass --level/--level-nid to also overlay that level's regions (reads
each region's position/size straight out of levels.json -- no game engine
import needed, this is a standalone, reusable script).

Add --blob-check to print a best-effort list of contiguous non-background
tile blobs whose bounding box exceeds --max-w/--max-h tiles (default 3x3),
as a rough signal for "this sprite may be sprawling past its budget". This
is a heuristic (dominant-background-color classification + flood fill), not
authoritative -- always confirm by looking at the rendered image yourself.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

GRID_COLOR = (255, 0, 0, 255)          # red gridlines, every tile
LABEL_COLOR = (255, 255, 0, 255)       # yellow coordinate labels
REGION_COLOR = (0, 220, 255, 255)      # cyan region boxes
REGION_LABEL_BG = (0, 60, 70, 220)
BLOB_COLOR = (255, 120, 0, 255)        # orange blob-warning boxes


def load_regions(level_path: Path, level_nid: str) -> list[dict]:
    data = json.loads(level_path.read_text(encoding='utf-8'))
    for lvl in data:
        if lvl.get('nid') == level_nid:
            return lvl.get('regions', [])
    raise SystemExit(f"level nid {level_nid!r} not found in {level_path}")


def dominant_tile_color(im: Image.Image, tile_size: int) -> tuple[int, int, int]:
    """Sample every tile's average color and return the modal (rounded)
    color, used as the 'background' reference for blob detection."""
    w, h = im.width // tile_size, im.height // tile_size
    counter: Counter[tuple[int, int, int]] = Counter()
    for ty in range(h):
        for tx in range(w):
            box = (tx * tile_size, ty * tile_size, (tx + 1) * tile_size, (ty + 1) * tile_size)
            tile = im.crop(box)
            avg = tuple(int(c) for c in tile.resize((1, 1), Image.BOX).getpixel((0, 0))[:3])
            # bucket to reduce noise
            bucket = tuple((c // 12) * 12 for c in avg)
            counter[bucket] += 1
    return counter.most_common(1)[0][0]


def find_blobs(im: Image.Image, tile_size: int, bg_color: tuple[int, int, int],
               threshold: int) -> list[tuple[int, int, int, int]]:
    """Classify each tile cell as background/foreground by average-color
    distance to bg_color, flood-fill 4-connected foreground cells, and
    return bounding boxes (x0, y0, x1, y1) in tile coordinates (inclusive)."""
    w, h = im.width // tile_size, im.height // tile_size
    is_fg = [[False] * w for _ in range(h)]
    for ty in range(h):
        for tx in range(w):
            box = (tx * tile_size, ty * tile_size, (tx + 1) * tile_size, (ty + 1) * tile_size)
            tile = im.crop(box)
            avg = tile.resize((1, 1), Image.BOX).getpixel((0, 0))[:3]
            dist = sum(abs(a - b) for a, b in zip(avg, bg_color))
            is_fg[ty][tx] = dist > threshold

    seen = [[False] * w for _ in range(h)]
    blobs = []
    for ty in range(h):
        for tx in range(w):
            if is_fg[ty][tx] and not seen[ty][tx]:
                q = deque([(tx, ty)])
                seen[ty][tx] = True
                cells = []
                while q:
                    cx, cy = q.popleft()
                    cells.append((cx, cy))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and is_fg[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((nx, ny))
                xs = [c[0] for c in cells]
                ys = [c[1] for c in cells]
                blobs.append((min(xs), min(ys), max(xs), max(ys)))
    return blobs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tileset', required=True, help='path to the tileset PNG')
    ap.add_argument('--tile-size', type=int, default=16)
    ap.add_argument('--scale', type=int, default=3, help='upscale factor for the overlay image')
    ap.add_argument('--label-every', type=int, default=2, help='label coordinates every N tiles')
    ap.add_argument('--level', help='path to levels.json, to overlay a level\'s regions')
    ap.add_argument('--level-nid', help='nid of the level within --level to overlay')
    ap.add_argument('--out', default=None, help='output PNG path (default: <tileset-stem>_grid.png next to the tileset)')
    ap.add_argument('--blob-check', action='store_true', help='best-effort: flag contiguous non-background blobs exceeding --max-w/--max-h')
    ap.add_argument('--max-w', type=int, default=3, help='footprint budget width in tiles (default 3, per the skill-doc rule)')
    ap.add_argument('--max-h', type=int, default=3, help='footprint budget height in tiles (default 3)')
    ap.add_argument('--blob-threshold', type=int, default=90, help='color-distance threshold (0-765) for foreground classification')
    args = ap.parse_args()

    tileset_path = Path(args.tileset)
    im = Image.open(tileset_path).convert('RGB')
    ts = args.tile_size
    tiles_w, tiles_h = im.width // ts, im.height // ts
    if im.width % ts or im.height % ts:
        print(f"WARNING: {tileset_path} ({im.width}x{im.height}) is not an exact multiple of tile size {ts}", file=sys.stderr)

    scale = args.scale
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST).convert('RGBA')
    draw = ImageDraw.Draw(big)

    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()

    # Gridlines every tile
    for tx in range(tiles_w + 1):
        x = tx * ts * scale
        draw.line([(x, 0), (x, big.height)], fill=GRID_COLOR, width=1)
    for ty in range(tiles_h + 1):
        y = ty * ts * scale
        draw.line([(0, y), (big.width, y)], fill=GRID_COLOR, width=1)

    # Coordinate labels every --label-every tiles
    for ty in range(0, tiles_h, args.label_every):
        for tx in range(0, tiles_w, args.label_every):
            x = tx * ts * scale + 2
            y = ty * ts * scale + 1
            draw.text((x, y), f"{tx},{ty}", fill=LABEL_COLOR, font=font)

    # Region overlays
    if args.level and args.level_nid:
        regions = load_regions(Path(args.level), args.level_nid)
        for region in regions:
            pos = region.get('position')
            size = region.get('size', [1, 1])
            if not pos:
                continue
            rx0, ry0 = pos
            rw, rh = size
            x0, y0 = rx0 * ts * scale, ry0 * ts * scale
            x1, y1 = (rx0 + rw) * ts * scale, (ry0 + rh) * ts * scale
            draw.rectangle([x0, y0, x1, y1], outline=REGION_COLOR, width=3)
            label = region.get('nid', '?')
            tw = draw.textlength(label, font=font)
            draw.rectangle([x0, y1, x0 + tw + 4, y1 + 14], fill=REGION_LABEL_BG)
            draw.text((x0 + 2, y1 + 1), label, fill=REGION_COLOR, font=font)

    # Best-effort blob check
    if args.blob_check:
        bg = dominant_tile_color(im, ts)
        blobs = find_blobs(im, ts, bg, args.blob_threshold)
        flagged = [b for b in blobs if (b[2] - b[0] + 1) > args.max_w or (b[3] - b[1] + 1) > args.max_h]
        print(f"Background reference color (bucketed): {bg}")
        print(f"Found {len(blobs)} contiguous non-background blob(s); {len(flagged)} exceed the "
              f"{args.max_w}x{args.max_h} footprint budget:")
        for (x0, y0, x1, y1) in flagged:
            w, h = x1 - x0 + 1, y1 - y0 + 1
            print(f"  blob at tiles x={x0}-{x1}, y={y0}-{y1}  ({w}x{h})")
            draw.rectangle([x0 * ts * scale, y0 * ts * scale, (x1 + 1) * ts * scale, (y1 + 1) * ts * scale],
                            outline=BLOB_COLOR, width=2)
        if not flagged:
            print("  (none -- everything fits the budget, or the heuristic missed it; still eyeball the image)")

    out_path = Path(args.out) if args.out else tileset_path.with_name(tileset_path.stem + "_grid.png")
    big.convert('RGB').save(out_path)
    print(f"Wrote {out_path} ({big.width}x{big.height}, {tiles_w}x{tiles_h} tiles at {scale}x)")


if __name__ == '__main__':
    main()
