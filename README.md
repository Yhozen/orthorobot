# Ortho Robot

A Lua/LÖVE perspective puzzle game by Maurice Guégan / Stabyourself.net.
The desktop source targets **LÖVE 11.5** (`love .`). All game assets and 16 levels
are included; no backend is required. See `LICENSE.txt` for credits and license.

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

## Verification status

The Python packaging test, four Node launcher/persistence tests, and Lua save tests
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
python3 scripts/runtime-version-check.py
```

The runtime version check substitutes a tiny diagnostic game in browser requests;
it never modifies the deployment files. Gameplay checks use the real game archive.
Browser test screenshots should be visually reviewed alongside assertions.

Native `love .`, Firefox/Safari, live CI, and hosting-provider deployment have not
been exercised in this environment. The static game is intended for desktop mouse
and keyboard; no touch-control rewrite was made. Nothing is automatically deployed.
