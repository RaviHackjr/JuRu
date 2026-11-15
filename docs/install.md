# Install JuRu

Three ways to get the interpreter. Pick one — the download needs no Python
at all.

## 1. Download the interpreter (any OS)

From the [releases page](https://github.com/RaviHackjr/JuRu/releases)
pick the file for your system:

| File | For |
|------|-----|
| `JuRu-<version>-windows-x64.zip` | Windows 10 / 11, 64-bit |
| `JuRu-<version>-linux-x64.zip` | Linux, 64-bit |
| `JuRu-<version>-macos-arm64.zip` | Macs with Apple Silicon |

Unzip it. You get one file — `juru.exe` on Windows, `juru` elsewhere —
and an INSTALL.txt with the same steps as below.

### Make `juru` runnable everywhere

The interpreter is a single program. Either run it with its full path, or
put its folder on your PATH:

- **Windows** — move `juru.exe` to a folder such as `C:\juru`, add that
  folder to PATH (Settings → search "environment variables" → edit the
  user PATH), then open a new terminal.
- **macOS / Linux** — `sudo mv juru /usr/local/bin/` (or move it into
  `~/.local/bin` if that is on your PATH). `chmod +x juru` if needed.
- **macOS first-run note** — the binary is not code-signed, so Gatekeeper
  may ask once: right-click `juru` → Open, or allow it under System
  Settings → Privacy & Security.

### Verify and write your first program

```bash
juru --version                 # JuRu <version>

echo 'say("hello JuRu!")' > hello.jr
juru hello.jr                  # hello JuRu!

juru                           # bare command → the live REPL
juru --new mygame guessing_game
juru mygame.jr                 # a ready-made game to make yours
```

## 2. pip install (needs Python 3.9+)

```bash
pip install juru
juru --version
juru hello.jr
```

Same interpreter, delivered as a package. The wheel also carries the
five `--new` templates.

## 3. From a clone (development)

```bash
git clone https://github.com/RaviHackjr/JuRu.git
cd JuRu
python3 juru.py examples/demo.jr
python3 repl.py
python3 test_ultimate.py       # the full test suite
```

The root launchers are thin wrappers around the `src/juru/` package —
nothing to install, everything runs in place.

## Building the interpreter yourself

The release binaries are built with PyInstaller from one spec file:

```bash
python3 -m pip install pyinstaller
python3 -m PyInstaller juru.spec      # → dist/juru  (or dist/juru.exe)
```

The templates for `--new` ride along automatically; `juru.spec` and
`packaging/juru_entry.py` are the only build files. Pushing a `v*` tag
builds the same binaries on GitHub's runners and attaches them to the
release.

## Next step: VS Code

Install the extension and press ▶ to run the open file —
see [vscode.md](vscode.md).
