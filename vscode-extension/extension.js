"use strict";

const vscode = require("vscode");

const VIEW_TYPE = "myliner.sidebar";
const VIEW_COMMANDS = {
  "myliner.addLine": "addLine",
  "myliner.removeLine": "removeLine",
  "myliner.speedUp": "speedUp",
  "myliner.speedDown": "speedDown",
};

/** Provide the Myliner Webview inside the Explorer view. */
class MylinerViewProvider {
  /** Store extension state until VS Code resolves the Webview. */
  constructor(extensionUri) {
    this.extensionUri = extensionUri;
    this.view = undefined;
    this.ready = false;
    this.pendingCommands = [];
  }

  /** Initialize a newly resolved Myliner Webview. */
  resolveWebviewView(webviewView) {
    this.view = webviewView;
    this.ready = false;
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.extensionUri, "media")],
    };
    webviewView.webview.html = this.getHtml(webviewView.webview);
    webviewView.webview.onDidReceiveMessage((message) => {
      if (message.type !== "ready") {
        return;
      }

      this.ready = true;
      for (const command of this.pendingCommands) {
        void webviewView.webview.postMessage({ command });
      }
      this.pendingCommands = [];
    });
    webviewView.onDidDispose(() => {
      if (this.view === webviewView) {
        this.view = undefined;
        this.ready = false;
      }
    });
  }

  /** Reveal the Myliner view in the Explorer. */
  async showView() {
    await vscode.commands.executeCommand(`${VIEW_TYPE}.focus`);
  }

  /** Send a command after the Webview has reported that it is ready. */
  async runViewCommand(command) {
    await this.showView();
    if (!this.view) {
      vscode.window.showWarningMessage("The Myliner view could not be opened.");
      return;
    }

    if (!this.ready) {
      this.pendingCommands.push(command);
      return;
    }

    await this.view.webview.postMessage({ command });
  }

  /** Build the isolated HTML document hosted by the Webview. */
  getHtml(webview) {
    const nonce = getNonce();
    const componentScriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "myliner-web.js"),
    );

    return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta
      http-equiv="Content-Security-Policy"
      content="default-src 'none'; img-src ${webview.cspSource} https:; style-src ${
        webview.cspSource
      } 'unsafe-inline'; script-src ${webview.cspSource} 'nonce-${nonce}';"
    />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      html,
      body {
        width: 100%;
        height: 100%;
        margin: 0;
        overflow: hidden;
        background: var(--vscode-sideBar-background, transparent);
      }

      myliner-overlay {
        display: block;
        width: 100vw;
        height: 100vh;
      }
    </style>
    <script type="module" nonce="${nonce}" src="${componentScriptUri}"></script>
  </head>
  <body>
    <myliner-overlay
      active
      keyboard-controls="false"
      click-to-stop="false"
      frameless
      transparent-background
      lines="2"
      history="150"
      speed="10"
      thickness="1"
      offset-min="1"
      offset-max="10"
      overlay-width="100vw"
      overlay-height="100vh"
      overlay-left="50vw"
      overlay-top="50vh"
    ></myliner-overlay>
    <script nonce="${nonce}">
      const overlay = document.querySelector("myliner-overlay");
      const vscodeApi = acquireVsCodeApi();

      customElements.whenDefined("myliner-overlay").then(() => {
        vscodeApi.postMessage({ type: "ready" });
      });

      window.addEventListener("message", (event) => {
        switch (event.data.command) {
          case "addLine":
            overlay.addLine();
            break;
          case "removeLine":
            overlay.removeLine();
            break;
          case "speedUp":
            overlay.speedUp();
            break;
          case "speedDown":
            overlay.speedDown();
            break;
          default:
            break;
        }
      });
    </script>
  </body>
</html>`;
  }
}

/** Register the Explorer view and its menu commands. */
function activate(context) {
  const provider = new MylinerViewProvider(context.extensionUri);
  const viewCommands = Object.entries(VIEW_COMMANDS).map(([commandId, message]) =>
    vscode.commands.registerCommand(commandId, () => provider.runViewCommand(message)),
  );

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(VIEW_TYPE, provider, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
    vscode.commands.registerCommand("myliner.showPanel", () => provider.showView()),
    ...viewCommands,
  );
}

/** Leave deactivation to VS Code's disposable cleanup. */
function deactivate() {}

/** Create a nonce for the Webview Content Security Policy. */
function getNonce() {
  const possibleCharacters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let text = "";

  for (let index = 0; index < 32; index += 1) {
    text += possibleCharacters.charAt(Math.floor(Math.random() * possibleCharacters.length));
  }

  return text;
}

module.exports = {
  activate,
  deactivate,
};
