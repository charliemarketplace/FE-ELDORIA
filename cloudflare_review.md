# Cloudflare Deployment Review — Eldoria web build

*Research writeup, 2026-07-15. No Cloudflare resources were created; nothing in the repo was modified. Numbers marked ⚠ should be re-checked against live docs before relying on them.*

*Update, 2026-07-16: implemented. Live manual deploy confirmed at `https://eldoria.carlos-rafael-mercado4.workers.dev`. Cloudflare's native Git integration is now connected to `charliemarketplace/FE-ELDORIA` (`main` branch) with build command `curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH="$HOME/.local/bin:$PATH" && uvx pygbag --ume_block 0 --template lt.tmpl --build .` and deploy command `npx wrangler deploy`. The `.github/workflows/deploy.yml` GitHub Actions workflow remains committed as a manual (`workflow_dispatch`-only) fallback in case the Cloudflare build container can't bootstrap `uv`.*

---

## Summary / Recommendation

**Yes, wrangler + Cloudflare is a good fit — use a Worker with static assets (not classic Pages, not Workers Sites).** The pygbag bundle in `build/web/` is a plain static site (HTML + two archives + favicon; the Python runtime itself comes from the pygame-web CDN), which is exactly what Cloudflare serves for free with no bandwidth metering. As of 2026, Cloudflare's official guidance is that **new projects should use Workers with static assets**; Pages still works and is not being shut down, but new features land on Workers only, and Workers Sites is legacy — skip it. For this project the two are near-identical effort (Workers needs a 7-line config file; Pages needs zero config), so I recommend Workers to avoid ever migrating, with Pages documented below as an equally functional fallback if you prefer the cleaner `eldoria.pages.dev` URL.

Key findings from inspecting the actual build:

1. **`eldoria.apk` is dead weight for a Cloudflare deploy.** Your custom `lt.tmpl` (and the built `index.html`, lines 40–50) only fetches the `.apk` when `location.host` contains `.itch.zone`; on every other host it fetches **`eldoria.tar.gz`** and unpacks it with `tarfile`. So on `*.workers.dev` / `*.pages.dev`, players download only the ~11MB tar.gz — the apk is never requested. Keep the apk in `build/web/` for future itch.io uploads, but it can be excluded from the Cloudflare upload (or left in; it costs upload time, not player load time).
2. **No COOP/COEP headers needed** — and adding them would likely *break* the build (details in Required Headers).
3. **No CI config exists and none is needed.** The repo has no `.github/workflows`, no `wrangler.toml`, no `_headers`/`_redirects` (confirmed), and isn't even a git repo — so git-connected auto-deploys are off the table anyway. Manual `wrangler deploy` from this machine is the right workflow at this scale.
4. **First load for friends will be roughly 30MB total** (11MB game archive + ~20MB Python/pygame runtime from the pygame-web CDN), i.e. ~10–20s to playable on decent broadband, up to a minute on bad 4G. Acceptable for a friends-feedback build; the biggest shrink lever is PNG quantization (details below). Notably, **the web bundle currently ships no audio files at all** — worth knowing before spending effort on "audio bitrate" optimization (there's nothing to optimize) and worth confirming it's intentional.

---

## Deployment

### Recommended: Worker with static assets

One config file at the repo root (`C:\Users\crmer\Documents\DND\LT_Editor\Eldoria\wrangler.jsonc`; a `wrangler.toml` works identically if you prefer TOML):

```jsonc
{
  "name": "eldoria",
  "compatibility_date": "2026-07-01",
  "assets": {
    "directory": "./build/web"
  }
}
```

No `main` / no Worker script means it's an **assets-only Worker**: requests are served straight from the static files without invoking (or billing) any Worker code. Then:

```powershell
npx wrangler login          # one-time browser OAuth (this is the only account-touching step)
npx wrangler deploy         # uploads build/web, prints https://eldoria.<your-subdomain>.workers.dev
```

Repeat deploys just re-run `npx wrangler deploy`; wrangler hashes files and only re-uploads changed ones. `_headers` and `_redirects` files dropped into `build/web/` are honored natively, same syntax as Pages.

Equivalent `wrangler.toml`, if preferred:

```toml
name = "eldoria"
compatibility_date = "2026-07-01"

[assets]
directory = "./build/web"
```

### Alternative: Cloudflare Pages (direct upload)

Zero config file — the entire deployment is:

```powershell
npx wrangler pages deploy build/web --project-name=eldoria
```

First run creates the project and prints `https://eldoria.pages.dev` (plus a unique per-deploy preview URL like `https://<hash>.eldoria.pages.dev`, handy for "try the new build vs the old one" with friends). This works fine and Cloudflare has stated existing Pages projects remain supported with no migration deadline — but since you're starting fresh in 2026, Workers is the maintained path. Pick Pages only if the nicer subdomain matters to you.

**Workers Sites** (the pre-2024 `[site]` config): legacy, deprecated, do not use.

### Optional: exclude the redundant .apk from the upload

Since the apk is never fetched off itch.io, you can halve the upload with a tiny staging step (PowerShell):

```powershell
Remove-Item -Recurse -Force deploy_stage -ErrorAction SilentlyContinue
Copy-Item -Recurse build\web deploy_stage
Remove-Item deploy_stage\eldoria.apk
npx wrangler deploy --assets deploy_stage   # or: wrangler pages deploy deploy_stage --project-name=eldoria
```

Honestly, at 11MB this is optional — leaving the apk in costs a few seconds of upload and nothing at runtime. Do it only if deploy time annoys you.

---

## Required Headers

### COOP/COEP: not needed — and actively risky here

pygbag 0.9.x runs single-threaded asyncio WASM and **does not require SharedArrayBuffer**, which is why pygbag builds officially work on GitHub Pages and itch.io (neither lets you set COOP/COEP). Your build already runs on the plain `localhost:8000` pygbag server, which confirms it.

More importantly: your `index.html` loads its runtime **cross-origin from `https://pygame-web.github.io/cdn/0.9.3/`** (`pythons.js`, `browserfs.min.js`, the CPython/pygame wasm, plus an iframe). If you set `Cross-Origin-Embedder-Policy: require-corp`, every one of those cross-origin loads must carry CORP/CORS headers or the browser blocks them — GitHub Pages does not send `Cross-Origin-Resource-Policy`, so **adding COOP/COEP would very likely break the game's loading**. Leave them off. (⚠ If a future pygbag version adds a threading mode you want, revisit this — you'd then also need `crossorigin` attributes or a self-hosted CDN copy.)

### MIME types: defaults are fine

Cloudflare assigns `Content-Type` by extension. It doesn't matter much here because the archive is fetched via JavaScript `fetch()` (pygbag's `platform.fopen`), which ignores content-type — `tarfile`/`zipfile` parse the raw bytes.

**The one real gotcha to verify: `Content-Encoding` on `eldoria.tar.gz`.** Some static hosts serve `.gz` files with `Content-Encoding: gzip`, causing the browser to transparently *decompress* the body — then `tarfile.open(mode="r:gz")` fails on what is now a plain tar. Cloudflare should serve it as `application/gzip` with no content-encoding (gzip archives aren't on its compressible-types list), but confirm after the first deploy:

```powershell
curl -sI https://eldoria.<subdomain>.workers.dev/eldoria.tar.gz | findstr /i "content-"
```

You want to see `content-length: ~10.9M` and **no** `content-encoding` header (or the symptom in-browser would be an immediate tarfile traceback in the loading console). ⚠ I could not verify Cloudflare's exact current behavior for `.tar.gz` from docs — this 30-second check is the insurance.

### Suggested `_headers` file (optional, not required to launch)

Drop into the deployed folder (see the caveat below about pygbag rebuilds):

```
/*
  X-Content-Type-Options: nosniff

/eldoria.tar.gz
  Cache-Control: public, max-age=3600, must-revalidate
```

Caveat: pygbag regenerates `build/web/` on every build and may drop extra files you placed there. Keep the master copy somewhere like `web_extra\_headers` and copy it in post-build:

```powershell
Copy-Item web_extra\_headers build\web\_headers
```

---

## Local Testing Workflow

Your iteration loop becomes:

```powershell
# 1. Rebuild the web bundle (your existing, confirmed-working command)
uvx pygbag --ume_block 0 --template lt.tmpl --build .

# 2. Preview against Cloudflare's actual local runtime (workerd), same asset/header/
#    _headers behavior as production, on http://localhost:8787
npx wrangler dev
#    (Pages variant: npx wrangler pages dev build/web)

# 3. When it looks right:
npx wrangler deploy
```

Notes:

- `wrangler dev` runs the real edge runtime locally, so `_headers` rules and asset serving behave like production — a meaningfully better preview than pygbag's ad hoc `--serve` server (which injects its own headers, including COOP/COEP ones production won't have).
- `--build` in step 1: plain `uvx pygbag .` starts its own test server after building; use pygbag's build-only flag (⚠ check `uvx pygbag --help`; it's `--build` in current versions) so it doesn't squat on a port when you only want the artifacts.
- One thing local preview can't fully replicate: the pygame-web CDN fetches still go to the real internet in both cases, so no difference there.
- Per your usual testing preference: after the first real deploy, the best QA is simply sending yourself the `workers.dev` link and playing a chapter — the deploy is byte-identical static serving, so if it boots and loads a save, it works.

---

## File Size & Load Time

### What's actually in the bundle (measured)

| File | Size | Fetched by players on Cloudflare? |
|---|---|---|
| `build/web/eldoria.tar.gz` | 10.96 MB | **Yes** — the only big download from your origin |
| `build/web/eldoria.apk` | 11.38 MB | **No** — itch.zone-only code path |
| `build/web/index.html` | 19.5 KB | Yes |
| `build/web/favicon.png` | 18 KB | Yes |
| pygame-web CDN runtime (pythons.js, CPython 3.12 wasm, pygame, browserfs) | ~22 MB uncompressed (measured from `build/web-cache/`; largest blobs 13.4 MB + 6.7 MB) | Yes, from `pygame-web.github.io`, not your origin; some of it is served compressed on the wire |

Inside `eldoria.tar.gz` (23.2 MB uncompressed → 11 MB gzipped, 1,312 files): **10.0 MB PNG** (818 files), **8.9 MB JSON** (53 files — combat_anims.json alone is 2.3 MB), **4.1 MB Python** (400 files), and — notably — **zero audio files**. The 18 MB `lion_throne.ltproj` source folder includes music that evidently isn't being packed into the web build. Confirm that's intentional (music disabled on web?) before anyone burns time on OGG bitrate tuning — as shipped, there is nothing to tune.

### Cloudflare limits (all comfortably clear)

- Max **25 MiB per file** — your biggest file is 11.4 MB. Even a future 2× asset growth fits. (⚠ per-file limit is the one to watch if the tar.gz ever approaches 25 MB.)
- Max **20,000 files per deployment** on free plans (Pages paid plans got 100,000 in Jan 2026) — you have 4 files.
- Storage is free; static asset **requests and bandwidth are free and unmetered on the free plan** for both Workers assets and Pages.

### Realistic first-load expectations

Total first-visit transfer ≈ **~30 MB** (11 MB tar.gz + roughly 15–20 MB CDN runtime on the wire), then tar extraction into the in-memory FS + WASM compile + Python startup:

- **Good home broadband (100+ Mbps):** ~3–6 s download, call it **10–20 s to the "click to start" prompt**. Fine.
- **Mediocre broadband / strong 4G (~20 Mbps):** ~15–20 s download, **25–40 s to playable**.
- **Weak 4G / bad hotel Wi-Fi (~5 Mbps):** ~50 s download, **about a minute-plus**. Tell friends on phones to be patient the first time.

Set expectations in the message you send friends ("first load is ~30 MB, then it's cached") and you'll preempt 90% of "is it broken?" pings — the progress bar in your template already helps.

### Repeat visits / caching

- The **pygame-web CDN runtime** is the same for every pygbag game and caches in the browser (GitHub Pages serves it with short max-age but ETags, so revisits revalidate with cheap 304s rather than re-downloading ~20 MB).
- **Your tar.gz**: Cloudflare serves assets with ETags; default browser caching revalidates rather than blind-re-downloading, so a friend's second session re-fetches the 11 MB only after you actually deploy a new build — which is exactly the behavior you want given the filename never changes (don't set a long `max-age` on it, or friends will get stale builds). The `max-age=3600` in the sample `_headers` above is a reasonable middle ground. ⚠ Verify the exact default `cache-control` header with the same `curl -I` check after first deploy.
- Cloudflare auto-applies **brotli/gzip on serve for compressible types** (HTML/JS/CSS/wasm) — that helps your 19 KB index.html trivially and does nothing for the tar.gz, which is already gzip-compressed and correctly excluded from recompression.

### Size-reduction levers, ranked by payoff

1. **PNG quantization** (biggest lever): 10 MB of the payload is 818 PNGs, and PNG does not compress further inside gzip. Pixel-art sprites/tilesets quantize to indexed color nearly losslessly — running `oxipng -o4 --strip all` (lossless, maybe −15–25%) or `pngquant` (lossy-but-invisible on pixel art, often −40–60%) over `lion_throne.ltproj/resources/` before the next pygbag build could plausibly cut 3–5 MB off the archive. Do this on a copy first; verify palettes survive (LT's combat palette system recolors sprites, so test one combat animation after quantizing).
2. **Drop `eldoria.apk` from the upload** — no player-facing effect, halves deploy upload. Already covered above.
3. **JSON (8.9 MB)**: already compresses ~4:1 inside the gzip archive; minifying it buys little. Not worth touching.
4. **pygbag flags**: pygbag has no brotli/zopfli archive option as of 0.9.x (⚠ check `uvx pygbag --help` for anything new); the tar.gz is already gzip. No free win here.
5. **Audio**: nothing shipped, nothing to shrink (but see the "is that intentional?" flag above — if you *add* music later, 64–96 kbps OGG is the web-build sweet spot and will quickly become the dominant weight).

---

## Sharing With Friends

- **Free URL, no auth, no install**: `https://eldoria.<your-subdomain>.workers.dev` (or `https://eldoria.pages.dev`). Send the link; it works in any modern desktop browser. Mobile browsers technically work but a tactics game at 1280×720 with keyboard controls won't be a great phone experience — your controls card even documents keyboard bindings, so pitch it as a desktop link.
- **No meaningful limits at friend-group scale**: static asset serving is free and unmetered — a dozen friends re-downloading 30 MB is statistically zero. The Workers free plan's 100k requests/day cap applies only to Worker *code* invocations, which an assets-only Worker never makes.
- **Preview/versioned URLs**: both platforms give per-deploy preview URLs, so you can send "stable" vs "this week's build" links separately if useful for feedback rounds.
- **Custom domain (optional)**: either platform attaches one for free if you ever buy `eldoria.whatever`; purely cosmetic, skip for now.
- **Saves are per-browser**: your template persists saves to `localStorage` and has export/import buttons — worth telling friends explicitly ("saves live in your browser; use the 💾 button to back them up"), since clearing site data nukes their campaign.
- One soft caveat: the game hard-depends on `pygame-web.github.io` (a GitHub Pages CDN) staying up and keeping the `0.9.3` folder around. It's been stable for years, but it's a dependency you don't control — if you ever want the build fully self-contained, the CDN files can be copied into your deploy and the `cdn:` URL in `lt.tmpl` pointed at a relative path. Not worth doing today.

---

## CI / Automation (optional — recommendation: skip it)

**Skip GitHub Actions for now.** Concretely:

- The Eldoria folder **is not currently a git repo**, so git-triggered CI doesn't even have a trigger; you'd be building automation before the thing it automates exists.
- The full loop is two commands (`uvx pygbag --ume_block 0 --template lt.tmpl --build .` then `npx wrangler deploy`) and takes under a minute from the dev machine. For a solo project deploying "when there's something to show friends," CI adds a GitHub repo, an API-token secret (`CLOUDFLARE_API_TOKEN`), and a pygbag-in-CI environment to debug — all cost, no benefit at this cadence.
- If you later put the project on GitHub and find yourself deploying after every push, the standard recipe is `cloudflare/wrangler-action@v3` running `wrangler deploy` with an API token scoped to Workers — a 20-line workflow. Cross that bridge then.

If you want *local* one-command convenience today, a `deploy.ps1` that chains pygbag build → copy `_headers` → `wrangler deploy` is the right amount of automation.

---

## Double-check before relying on (recap of ⚠ flags)

1. `content-encoding` behavior on `.tar.gz` after first deploy (`curl -I` check) — the one thing that could actually break the game.
2. Current limits pages: [Workers static assets](https://developers.cloudflare.com/workers/static-assets/) and [Pages limits](https://developers.cloudflare.com/pages/platform/limits/) — 25 MiB/file and 20k files were current as of this writeup.
3. `uvx pygbag --help` for the exact build-only flag and any new archive-compression options.
4. Whether pygbag rebuilds wipe an added `_headers` file from `build/web/` (copy it in post-build regardless).
5. Whether the missing audio in the web bundle is intentional.
