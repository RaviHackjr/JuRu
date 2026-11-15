# JuRu for VS Code (official)

Syntax highlighting, snippets and friendly editing for **JuRu** (`.jr`)
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

## Files in this folder

```
vscode/juru-vscode/
├── package.json                 the extension manifest
├── language-configuration.json  comments, brackets, folding rules
├── syntaxes/juru.tmLanguage.json  the TextMate grammar
├── snippets/juru.json           the snippets
└── README.md                    this file
```
