# Electronics Design — experimental

This independent app wraps the upstream [designElectronics](https://github.com/rORrEtboLt/designElectronics) browser editor. Its MIT-licensed code provides breadboard, schematic, PCB, simulation, an autorouter and Gerber export. It is an alternative to the separate tscircuit PCB investigation, not a tscircuit frontend. The included example opens in PCB view; it is not a manufacture-ready circuit. Inspect design rules and fabrication output independently before making a board.

**Storage:** Open `.dez` projects with **Open from My files** or from Files; upload from your computer in Files first. **Save project** captures the current design directly to My files on this device and starts server synchronization. The embedded editor's Ctrl+S uses the same path; Ctrl+Shift+S chooses a new path, then use Save project. Save conflicts and existing files require attention rather than silently overwriting them. If you edit or start another design during a save, the later work remains unsaved. The window warns before discarding changes, conservatively including some interactions that may not modify the design. Native exports such as Gerbers wait in the **Exports** section until saved to My files or discarded. Use **Import part** (or the editor’s File → Import Part) to choose a `.dezpart` or supported part JSON from My files. It appears under Custom in the editor; imported parts that are not placed in the design remain temporary to that editor window. Placed part definitions are included in saved designs. The GitHub account and version-history interface is disabled pending a desktop-integrated replacement.

Projects and captured outputs are limited to 128 MiB; large projects need substantial browser and WebAssembly memory, and that maximum is not validated on every device. The embedded editor is trusted same-origin code, not a security sandbox. Simulation is an aid to design, not proof that hardware is safe or will work.

## Build and licensing

This experimental integration uses a **locally rebuilt** WebAssembly binary, not the upstream Pages binary. The app code is MIT licensed. Its bundled notices cover the upstream fonts, SDL3, SDL_ttf, FreeType, HarfBuzz, PlutoSVG, PlutoVG, Emscripten and the upstream vendored encoders. SDL_ttf's vendored build used FreeType, HarfBuzz and PlutoSVG; FreeType's external zlib, bzip2, PNG and Brotli support were disabled by its build configuration. More information and original license texts are under `licenses/`.

The source revisions below are pinned for this local build. The SDL and SDL_ttf versions were selected as the last branch revisions before upstream's published build; the local build used the exact revisions listed, rather than relying on upstream's moving-branch artifact:

- designElectronics: `4d9cb373bd06afb2d99b1548e6c3a0c86992bd56`
- SDL3: `7e03137ea0a22d1a754426b4dc305e46f58a1a08`
- SDL_ttf: `1f759d81f0b9662558d916655f05942e038d6c57`
- SDL_ttf submodules: FreeType `535d2993d2cab67cc8b270132b1b1bcb62f269aa`, HarfBuzz `950d232cdcd29e2e83a2099307e5624a8f1aa937`, PlutoSVG `96e115bc0f837dbccf260a05ad23978b6b54f731`, PlutoVG `a6e0d682d08a5e993694ad82a23e5d45e831f315` (their nested submodules are pinned by those Git trees).
- Emscripten SDK 5.0.7: `6cd98e86d7749ff98b82b7f2ae78eb4f01942788`.

From SIMPLIFIED, a clean source checkout can be prepared as follows. Build dependencies and generated WebAssembly live under `.build/`, outside Git:

```sh
git clone https://github.com/rORrEtboLt/designElectronics.git .build/design-electronics-upstream
git -C .build/design-electronics-upstream checkout --detach 4d9cb373bd06afb2d99b1548e6c3a0c86992bd56
git clone https://github.com/libsdl-org/SDL.git .build/design-electronics-upstream/external/SDL
git -C .build/design-electronics-upstream/external/SDL checkout --detach 7e03137ea0a22d1a754426b4dc305e46f58a1a08
git clone https://github.com/libsdl-org/SDL_ttf.git .build/design-electronics-upstream/external/SDL_ttf
git -C .build/design-electronics-upstream/external/SDL_ttf checkout --detach 1f759d81f0b9662558d916655f05942e038d6c57
git -C .build/design-electronics-upstream/external/SDL_ttf submodule update --init --recursive
git clone https://github.com/emscripten-core/emsdk.git .build/electronics-emsdk
.build/electronics-emsdk/emsdk install 5.0.7
.build/electronics-emsdk/emsdk activate 5.0.7
source .build/electronics-emsdk/emsdk_env.sh
python3 apps/system/electronics-design/prepare_source.py
emcmake cmake -S .build/design-electronics-upstream -B .build/design-electronics-rebuilt -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build .build/design-electronics-rebuilt --parallel 4
python3 apps/system/electronics-design/prepare.py
../active-system/.venv/bin/python active-system/scripts/build-public-apps.py --output .build/electronics-design-source-test --apps electronics-design --node ../active-system/.build/tools/node-v24.22.1-linux-x64/bin/node
```

`prepare_source.py` checks pinned upstream source hashes before applying the open/save, change tracking, and third-party-account patches. `prepare.py` checks the actual local output against the reviewed build hashes: JS `4d6c5602fbd164465144b9edf223cdb8b7b6bac57eca99905dd81d56359d2c22`, WASM `1fb748273aeed5f3b74d0993ec9381548b341704f4c75f05ff60928078d2a693`, and data `b47f7a58ff1e8768885267b349018d60932c535938a301c0f3b6a2b0c5f8a7ed`. A different output requires review before updating those pins; bit-for-bit reproducibility on another machine has not been established. This successful build used four workers and finished without memory or disk failures.

## Tests

The durable tests are `tests/electronics-design-browser.test.mjs` (mock host, real WebAssembly editor) and `tests/electronics-design-desktop.test.mjs` (registered account and real disk sync). They exercise part import and invalid-part recovery, direct save, edits during save, unsaved-change prompts, invalid input, and reopen; the browser test places an imported part and verifies its embedded definition after reopening. the account test also checks a stale session and a new design created while saving. The phone test simulates keyboard interaction; physical touch has not been tested. The registered-account test launches the app programmatically to exercise its file workflow.

Start an isolated preview with the built bundle on port 18164 and a disposable Chromium with remote debugging on port 19255, then run:

```sh
../active-system/.venv/bin/python -B active-system/scripts/run-simplified-local.py --port 18164 --isolated --browser-relay --apps-bundle .build/electronics-design-source-test
```

In another shell:

```sh
../active-system/.build/tools/node-v24.22.1-linux-x64/bin/node tests/electronics-design-desktop.test.mjs
CODI_PHONE=1 ../active-system/.build/tools/node-v24.22.1-linux-x64/bin/node tests/electronics-design-desktop.test.mjs
CODI_LARGE=1 ../active-system/.build/tools/node-v24.22.1-linux-x64/bin/node tests/electronics-design-desktop.test.mjs
```

The large case round-trips a valid design with 9 MiB of notes; it does not establish that 128 MiB projects work on every device. Those tests create isolated test accounts and inspect the local preview's account directory. Use disposable accounts only; the test removes its named test files but does not delete the account. `CODI_TEST_URL`, `CODI_BROWSER_URL`, and `CODI_TEST_ACCOUNT_DIR` override the defaults. The MIT upstream LED-with-battery example under `tests/fixtures/electronics-design/` is used solely as test data.
