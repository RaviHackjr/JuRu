# JuRu in VS Code

The official editor support lives in this repository at `vscode/juru-vscode/`
— finished, tested, and ready to load. Everything below works today without
publishing anything.

## One-time load (2 minutes)

**Download the ready-made `.vsix`** from the
[releases page](https://github.com/RaviHackjr/JuRu/releases) (file
`JuRu-vscode-<version>.vsix`), then:

```bash
code --install-extension JuRu-vscode-1.5.0.vsix
```

**Or build it from this repo:**

```bash
cd vscode/juru-vscode
npx --yes @vscode/vsce package --no-dependencies
code --install-extension juru-vscode-1.5.0.vsix
```

**Or from source:**

```bash
cp -r vscode/juru-vscode ~/.vscode/extensions/
```

Open a `.jr` file → VS Code picks **JuRu** automatically.

## Run your code — the play button

Open any `.jr` file and press the **▶ button** (top-right of the editor),
or right-click → **JuRu: Run File**, or run **JuRu: Run File** from the
command palette. The file runs in a real terminal, so `ask()` works and
the REPL-style output scrolls normally.

- **JuRu: Open REPL** — a live JuRu session in the terminal.
- **juru.interpreterPath** — where the extension looks for the
  interpreter. The default, `juru`, expects it on your PATH; put the full
  path there if you keep `juru.exe` somewhere else. When the interpreter
  is missing, you get a dialog with a link to the
  [interpreter download](https://github.com/RaviHackjr/JuRu/releases/latest)
  instead of a cryptic shell error.

Using the [Code Runner](https://marketplace.visualstudio.com/items?itemName=formulahendry.code-runner)
extension instead? It runs JuRu with one line in your settings:
`"code-runner.executorMap": { "juru": "juru" }`.

## What you get

- **Colors** — 19 keywords, all 30 builtins, comments (`#`), text, numbers,
  operators; the keyword list is test-enforced against `KEYWORDS`, so
  highlighting and language can never disagree.
- **Snippets** — type `if`, `for`, `forin`, `while`, `func`, `say`, `ask`,
  `import` and press Tab.
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
