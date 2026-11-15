# JuRu for VS Code (official)

Syntax highlighting, snippets, a run button and a REPL for **JuRu** (`.jr`)
— the easy, secure programming language.

> **Prepare-only release** — the extension files are finished and shipped
> in this repository, ready to be packaged. The Marketplace upload is a
> later, separate step (it needs a `vsce` login).

## What you get

| Feature | Details |
|---------|---------|
| Language | `juru`, for every `.jr` file |
| Grammar | full `source.juru` TextMate grammar: 19 keywords, 30 builtins, comments, strings, numbers, operators |
| Snippets | `if`, `elseif`, `for`, `forin`, `while`, `func`, `say`, `ask`, `import` |
| Editing | auto-closing braces/brackets/quotes, comment toggle with `#`, bracket matching, fold by block |
| Run | ▶ button, right-click → **JuRu: Run File**, command palette; runs in a real terminal so `ask()` works |
| REPL | **JuRu: Open REPL** — a live JuRu session in the terminal |
| Setup | `juru.interpreterPath` setting; a missing interpreter gets a dialog with a link to the download |

The grammar's keyword list is **test-enforced** to match the language's
`KEYWORDS` exactly — highlighting can never drift from the language.

## How to load it (from this repo, no publish needed)

### Option A — VSIX (recommended)

```bash
cd vscode/juru-vscode
npx --yes @vscode/vsce package --no-dependencies
code --install-extension juru-vscode-1.5.0.vsix
```

### Option B — run from source

```bash
mkdir -p ~/.vscode/extensions && cp -r vscode/juru-vscode ~/.vscode/extensions/
code .
```

Either way, open any `.jr` file and pick **JuRu** as the language
(bottom-right corner), or just let the `.jr` extension map it for you.

## Running code

Press the ▶ button in the editor's top-right corner (or
**JuRu: Run File** from the right-click menu / command palette). The
extension looks for the interpreter at the `juru.interpreterPath` setting
(default `juru`, i.e. on your PATH — get the download from the
[releases page](https://github.com/RaviHackjr/JuRu/releases/latest)). If
it cannot find the interpreter, you get a friendly dialog with the
download link and a shortcut to the setting.

## Files in this folder

```
vscode/juru-vscode/
├── package.json                 the extension manifest
├── extension.js                 the run button + REPL commands
├── language-configuration.json  comments, brackets, folding rules
├── syntaxes/juru.tmLanguage.json  the TextMate grammar
├── snippets/juru.json           the snippets
├── LICENSE                      MIT (packaged into the .vsix)
└── README.md                    this file
```
