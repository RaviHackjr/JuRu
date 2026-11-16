# Install JuRu

Three ways to get the interpreter. Pick one — the download needs no
Python at all, and its setup script does everything for you.

## 1. Download the interpreter (any OS)

From the [releases page](https://github.com/RaviHackjr/JuRu/releases)
pick the file for your system:

| File | For |
|------|-----|
| `JuRu-<version>-windows-x64.zip` | Windows 10 / 11, 64-bit |
| `JuRu-<version>-linux-x64.zip` | Linux, 64-bit |
| `JuRu-<version>-macos-arm64.zip` | Macs with Apple Silicon |

Unzip it. Inside: the interpreter (`juru.exe` on Windows, `juru`
elsewhere), the one-step setup script, and an INSTALL.txt with the same
steps as below.

### Windows — double-click setup.bat

One step, exactly like a real installer (no admin rights):

1. Double-click **setup.bat** in the unzipped folder.
2. Open a NEW terminal.
3. `juru --version`

setup.bat copies `juru.exe` to `%LOCALAPPDATA%\Programs\JuRu` (the same
place Python's per-user install uses), adds it to your PATH, and gives
`.jr` files the JuRu icon in Explorer — double-clicking a `.jr` file
runs it, like `.py` files. If the `.jr` icon does not show at once,
press F5 in Explorer.

### macOS / Linux — sh install.sh

```bash
sh install.sh
```

It copies `juru` to `/usr/local/bin` (directly, or with sudo), falls
back to `~/.local/bin` when that is not possible, and tells you if one
PATH line remains. Reopen the terminal and run `juru --version`.

macOS note: the binary is not code-signed, so the first run may ask for
permission — right-click `juru` → Open, or allow it under System
Settings → Privacy & Security. One-time only.

### Verify and write your first program

```bash
juru --version                 # JuRu <version>

echo 'say("hello JuRu!")' > hello.jr
juru hello.jr                  # hello JuRu!

juru                           # bare command → the live REPL
juru --new mygame starter      # a ready-made program to make yours
juru mygame.jr
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
python3 -m pip install pyinstaller .
python3 -m PyInstaller juru.spec      # → dist/juru  (or dist/juru.exe)
```

The templates for `--new` ride along automatically, and the Windows exe
carries the JuRu icon (`logo/juru_icon.ico`). `juru.spec` and
`packaging/juru_entry.py` are the only build files. Pushing a `v*` tag
builds the same binaries on GitHub's runners and attaches them to the
release.

## Next step: VS Code

Install the extension and press ▶ to run the open file — the extension
finds the interpreter by itself, so there is nothing to configure. See
[vscode.md](vscode.md).
