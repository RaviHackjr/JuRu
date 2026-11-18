# JuRu in VS Code

The official editor support lives in this repository at `vscode/juru-vscode/`
— finished, tested, and ready to load. Everything below works today without
publishing anything.

## One-time load (2 minutes)

**Download the ready-made `.vsix`** from the
[releases page](https://github.com/RaviHackjr/JuRu/releases) (file
`JuRu-vscode-<version>.vsix`), then:

```bash
code --install-extension JuRu-vscode-1.10.0.vsix
```

**Or build it from this repo:**

```bash
cd vscode/juru-vscode
npx --yes @vscode/vsce package --no-dependencies
code --install-extension juru-vscode-1.10.0.vsix
```

**Or from source:**

```bash
cp -r vscode/juru-vscode ~/.vscode/extensions/
```

Open a `.jr` file → VS Code picks **JuRu** automatically.

## Run your code — four ways, zero configuration

Open any `.jr` file, then run it however you like:

1. the **▶ button** (top-right of the editor),
2. **Ctrl+Alt+J**,
3. right-click in the editor → **JuRu: Run File** (the file tree's
   right-click menu has it too),
4. **JuRu: Run File** from the command palette.

The file runs in a real terminal, so `ask()` works and the output
scrolls normally — the same feel as running `python file.py`.

The interpreter is **found by itself**: plain `juru` on your PATH, or
the exact places the one-step setup puts it (`%LOCALAPPDATA%\Programs\JuRu`
from setup.bat on Windows, `/usr/local/bin` or `~/.local/bin` from
install.sh elsewhere). You never set an interpreter, never pick a
version, never hunt for a path — like a real installer, the setup did
it already.

## The .jr file icon in the Explorer

`.jr` files carry the JuRu ruby in the file tree — the same way Python
files show theirs. It comes from the extension's language icon, so it
works with any icon theme (Seti, Material, ...) without switching
anything. No setting, no click — install the extension and the icon is
there next to every `.jr` file.

- **JuRu: Open REPL** — a live JuRu session in the terminal.
- **juru.interpreterPath** — only for unusual setups: leave it as
  `auto` (the default) and the extension finds the interpreter itself.
  If the interpreter is genuinely missing, you get one friendly dialog
  with a link to the
  [interpreter download](https://github.com/RaviHackjr/JuRu/releases/latest)
  instead of a cryptic shell error.

Using the [Code Runner](https://marketplace.visualstudio.com/items?itemName=formulahendry.code-runner)
extension instead? It runs JuRu with one line in your settings:
`"code-runner.executorMap": { "juru": "juru" }`.

## What you get

- **Colors** — 21 keywords, all 48 builtins, comments (`#`), text, numbers,
  operators; the keyword list is test-enforced against `KEYWORDS`, so
  highlighting and language can never disagree.
- **Snippets** — type `if`, `for`, `forin`, `while`, `func`, `say`, `ask`,
  `import`, `try` and press Tab.
- **Editing** — auto-closing `{ } [ ] ( ) " "`, comment toggle with `#`,
  folding by block.

## Pair it with the language itself

```bash
pip install juru          # after a release (this repo: python3 juru.py works too)
juru --new hello          # starter template
juru hello.jr             # run it
juru repl                 # try ideas live
```

## Publishing to the Marketplace (later step, by design)

1. `npm install -g @vscode/vsce`
2. `vsce login juru-lang` (a publisher account on marketplace.visualstudio.com)
3. `cd vscode/juru-vscode && vsce publish`

Everything needed for that step is already prepared and tested in this repo.
