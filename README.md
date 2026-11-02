# Ortho Robot

A Lua/LÖVE perspective puzzle game by Maurice Guégan / Stabyourself.net.
The desktop source targets **LÖVE 11.5** (`love .`). All game assets and 16 levels
are included; no backend is required. See `LICENSE.txt` for credits and license.

Play at **https://orthorobot.rccpr.tech**.

## Static web build

Requires Node.js 22+, npm and Python 3:

```sh
npm ci --ignore-scripts
npm test
npm run build
npm run serve
```

Open http://127.0.0.1:8080 and click Play. Upload the **contents of `dist/`** to a
static host such as GitHub Pages, Netlify, Vercel or itch.io. Keep the files together;
relative asset URLs support subdirectories. Serve `.wasm` as `application/wasm`.
Use HTTP(S), not `file://`. `vercel.json` specifies the build and output directory.
The web workflow builds and uploads artifacts only; it does not publish a site.

The pinned `love.js@11.4.1` compatibility build avoids SharedArrayBuffer and
cross-origin isolation requirements. This npm version is a packaging version;
the bundled engine reports **LÖVE 11.4.0 (Mysterious Mysteries)**. The actual web
build has been tested in Chromium; the desktop source continues to target 11.5.
Compatibility-mode audio has upstream limitations. The launcher requires a user
gesture before starting, reports load failures, and offers fullscreen.

Desktop controls: arrows/WASD move, mouse drag changes perspective, Escape pauses.
See the in-game Help page for the puzzle rules.

## Alchemy deployment

`infra/alchemy.run.ts` deploys the built `dist/` directory as Cloudflare Worker
static assets at `orthorobot.rccpr.tech`. Deployment dependencies are separate from
the game build and require Node.js 24.11.1+ (or Bun). Set `CLOUDFLARE_ACCOUNT_ID`
and `CLOUDFLARE_API_TOKEN` in your environment, then run from the repository root:

```sh
npm ci --ignore-scripts
npm test && npm run build
npm --prefix infra ci --ignore-scripts
CI=1 npm --prefix infra run deploy
```

`npm --prefix infra run plan` previews updates. Alchemy stores deployment state
remotely in the isolated `alchemy-state-store-orthorobot` Worker so another checkout
can update the same deployment. Credentials and local state are excluded from Git.
Deployments are manual; the web workflow continues to build artifacts only.

## Packaging and saves

`scripts/package.py` creates `build/orthorobot.love` from an allowlist of game
source, images, fonts, maps, sounds and the game license. Sorted paths, fixed ZIP
timestamps and permissions make the archive reproducible. It excludes tooling,
repository metadata, dependencies and local saves.

`scripts/finish-build.cjs` adds the launcher and licenses, uses an asset-content
hash for the preload cache, and patches the pinned runtime's IndexedDB startup
handling. Its reviewed markers fail closed on unexpected runtime changes.
Storage failures must allow session-only play. Successful storage hydration enables
queued flushes every two seconds and on page hide. Sudden tab/browser termination
can still lose recent progress. Saves belong to the browser and site origin;
clearing site data clears progress. Malformed save records are ignored safely.
One tab owns the save filesystem at a time using Web Locks. Additional tabs wait
before loading the game, then read the latest save when the owner closes. Browsers
without Web Locks allow session-only play, without writing shared storage.

## Verification status

The Python packaging test, eight Node launcher/persistence tests, and Lua save tests
pass. Run the Lua checks with `luatex --luaonly tests/save.lua` (or `lua tests/save.lua`).

The actual static output was tested under `/dist/` in Chromium 154: menu, level
selection, movement, perspective, pause, restart, completion, return, saved unlocks
and sound preferences after reload, nonzero audio samples after the start gesture,
denied IndexedDB, fullscreen aspect ratio, and failed asset recovery. Screenshots
and machine-readable reports are in the delivered evidence archive.

To repeat browser checks with Python Playwright and system Chromium installed:

```sh
# Serve the repository in a separate terminal (checks use the /dist/ subpath).
python3 -m http.server 8080 --bind 127.0.0.1
python3 scripts/browser-check.py
python3 scripts/browser-edge-check.py
python3 scripts/browser-storage-check.py
python3 scripts/runtime-version-check.py
```

The runtime version check substitutes a tiny diagnostic game in browser requests;
it never modifies the deployment files. Gameplay checks use the real game archive.
Browser test screenshots should be visually reviewed alongside assertions.

The storage regression also runs against the live site with
`GAME_URL=https://orthorobot.rccpr.tech/ python3 scripts/browser-storage-check.py`.
It completes level 1, checks that a second tab waits, and verifies that ownership
transfer preserves the save and unlocks level 2. Missing Web Locks are also tested.

Native `love .` and Firefox/Safari have not been exercised in this environment.
The static game is intended for desktop mouse and keyboard; no touch-control
rewrite was made. Nothing is automatically deployed.
