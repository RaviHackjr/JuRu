// JuRu for Visual Studio Code — highlighting, snippets and the run button.
//
// Three commands:
//   juru.runFile   the ▶ button, Ctrl+Alt+J, "JuRu: Run File" — runs the
//                  open .jr file in a real terminal (so ask() works)
//   juru.openRepl  "JuRu: Open REPL" — a live JuRu session in the terminal
//
// The interpreter is found by itself, like a real installer set it up:
// the juru.interpreterPath setting (only if you changed it from `auto`),
// plain `juru` on the PATH, then the one-step-setup location that
// setup.bat (Windows) and install.sh (macOS/Linux) create. Nothing to
// configure, ever. If nothing is found you get one friendly dialog with
// the download link — never a cryptic shell error.
const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const os = require("os");

const RELEASES_URL = "https://github.com/RaviHackjr/JuRu/releases/latest";
const SETTING_ID = "juru.interpreterPath";

// Where the interpreter can live. setup.bat copies juru.exe to
// %LOCALAPPDATA%\Programs\JuRu; install.sh uses /usr/local/bin or
// ~/.local/bin — the same places Python's own installers use.
function candidatePaths() {
  const candidates = [];
  const setting = vscode.workspace.getConfiguration("juru").get("interpreterPath", "auto");
  if (setting && setting !== "auto") {
    candidates.push(setting);            // an explicit setting always wins
  }
  candidates.push("juru");               // plain `juru` on the PATH
  if (process.platform === "win32") {
    if (process.env.LOCALAPPDATA) {
      candidates.push(path.join(process.env.LOCALAPPDATA, "Programs", "JuRu", "juru.exe"));
    }
  } else {
    candidates.push("/usr/local/bin/juru");
    candidates.push(path.join(os.homedir(), ".local", "bin", "juru"));
  }
  return candidates;
}

// A quick `--version` probe — this is how "this one works" announces itself.
function interpreterAvailable(command) {
  return new Promise((resolve) => {
    const probe = cp.spawn(command, ["--version"], { windowsHide: true });
    probe.on("error", () => resolve(null));
    probe.on("close", (code) => resolve(code === 0 ? command : null));
  });
}

let found = null;                        // remembered for the whole session

async function findInterpreter() {
  if (found) {
    return found;
  }
  for (const candidate of candidatePaths()) {
    const works = await interpreterAvailable(candidate);
    if (works) {
      found = works;
      return works;
    }
  }
  return null;
}

// The interpreter or null — after one friendly dialog on the null path.
async function ensureInterpreter() {
  const command = await findInterpreter();
  if (command) {
    return command;
  }
  const pick = await vscode.window.showErrorMessage(
    "The JuRu interpreter was not found. Windows: run setup.bat from the " +
    "downloaded zip — it installs everything (PATH + .jr icons) in one " +
    "step. Or download the interpreter from the Releases page.",
    "Download the interpreter",
    "Open settings"
  );
  if (pick === "Download the interpreter") {
    vscode.env.openExternal(vscode.Uri.parse(RELEASES_URL));
  } else if (pick === "Open settings") {
    vscode.commands.executeCommand("workbench.action.openSettings", SETTING_ID);
  }
  return null;
}

// Wrap values with spaces so the terminal sees them as one word.
function quoted(value) {
  return /\s/.test(value) ? '"' + value + '"' : value;
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
  const command = await ensureInterpreter();
  if (!command) {
    return;
  }
  const file = editor.document.fileName;
  runInTerminal(quoted(command) + " " + quoted(file), path.dirname(file));
}

async function openRepl() {
  const command = await ensureInterpreter();
  if (!command) {
    return;
  }
  const folders = vscode.workspace.workspaceFolders;
  const cwd = folders ? folders[0].uri.fsPath : undefined;
  runInTerminal(quoted(command) + " repl", cwd);
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
