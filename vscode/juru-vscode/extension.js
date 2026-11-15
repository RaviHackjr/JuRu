// JuRu for Visual Studio Code — highlighting, snippets and the run button.
//
// Three commands:
//   juru.runFile   the ▶ button and "JuRu: Run File" — runs the open .jr file
//   juru.openRepl  "JuRu: Open REPL" — a live JuRu session in the terminal
//
// The interpreter is looked up once per run: the juru.interpreterPath
// setting (default: `juru` on the PATH). If it is missing, you get a
// friendly dialog with a link to the interpreter download instead of a
// cryptic shell error.
const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");

const RELEASES_URL = "https://github.com/RaviHackjr/JuRu/releases/latest";
const SETTING_ID = "juru.interpreterPath";

function interpreterCommand() {
  return vscode.workspace.getConfiguration("juru").get("interpreterPath", "juru");
}

// Wrap values with spaces so the terminal sees them as one word.
function quoted(value) {
  return /\s/.test(value) ? '"' + value + '"' : value;
}

// A quick `juru --version` — this is how "not installed" shows itself.
function interpreterAvailable() {
  return new Promise((resolve) => {
    const probe = cp.spawn(interpreterCommand(), ["--version"], { windowsHide: true });
    probe.on("error", () => resolve(false));
    probe.on("close", (code) => resolve(code === 0));
  });
}

async function ensureInterpreter() {
  if (await interpreterAvailable()) {
    return true;
  }
  const pick = await vscode.window.showErrorMessage(
    "The JuRu interpreter was not found (" + interpreterCommand() + "). " +
    "Download it from the Releases page, or point juru.interpreterPath at it.",
    "Download the interpreter",
    "Open settings"
  );
  if (pick === "Download the interpreter") {
    vscode.env.openExternal(vscode.Uri.parse(RELEASES_URL));
  } else if (pick === "Open settings") {
    vscode.commands.executeCommand("workbench.action.openSettings", SETTING_ID);
  }
  return false;
}

function runInTerminal(command, cwd) {
  const terminal = vscode.window.createTerminal({ name: "JuRu", cwd: cwd });
  terminal.sendText(command, true);
  terminal.show();
}

async function runFile() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== "juru") {
    vscode.window.showInformationMessage("Open a JuRu file (.jr) and press the play button to run it.");
    return;
  }
  if (editor.document.isDirty) {
    await editor.document.save();
  }
  if (!(await ensureInterpreter())) {
    return;
  }
  const file = editor.document.fileName;
  const command = quoted(interpreterCommand()) + " " + quoted(file);
  runInTerminal(command, path.dirname(file));
}

async function openRepl() {
  if (!(await ensureInterpreter())) {
    return;
  }
  const folders = vscode.workspace.workspaceFolders;
  const cwd = folders ? folders[0].uri.fsPath : undefined;
  runInTerminal(quoted(interpreterCommand()) + " repl", cwd);
}

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand("juru.runFile", runFile),
    vscode.commands.registerCommand("juru.openRepl", openRepl)
  );
}

function deactivate() {}

module.exports = {
  activate: activate,
  deactivate: deactivate,
};
