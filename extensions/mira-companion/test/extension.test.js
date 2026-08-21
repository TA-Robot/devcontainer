"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const Module = require("node:module");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

function disposable(dispose = () => {}) {
  return { dispose };
}

class EventEmitter {
  constructor() {
    this.listeners = new Set();
    this.event = (listener) => {
      this.listeners.add(listener);
      return disposable(() => this.listeners.delete(listener));
    };
  }

  fire(value) {
    for (const listener of this.listeners) listener(value);
  }

  dispose() {
    this.listeners.clear();
  }
}

test("activation contributes one bottom world and only a tiny status toggle", async () => {
  const stateDirectory = fs.mkdtempSync(
    path.join(os.tmpdir(), "mira-extension-test-"),
  );
  const originalDirectory = process.env.MIRA_COMPANION_STATE_DIR;
  process.env.MIRA_COMPANION_STATE_DIR = stateDirectory;
  const statusItems = [];
  const commands = new Map();
  const executedCommands = [];
  const providers = [];

  const vscode = {
    EventEmitter,
    StatusBarAlignment: { Right: 2 },
    Uri: {
      file(value) {
        return {
          fsPath: value,
          toString: () => `file://${value}`,
        };
      },
    },
    commands: {
      registerCommand(id, handler) {
        commands.set(id, handler);
        return disposable();
      },
      async executeCommand(id) {
        executedCommands.push(id);
      },
    },
    window: {
      state: { focused: true },
      createStatusBarItem(id, alignment, priority) {
        const item = {
          id,
          alignment,
          priority,
          visible: false,
          show() {
            this.visible = true;
          },
          hide() {
            this.visible = false;
          },
          dispose() {
            this.visible = false;
          },
        };
        statusItems.push(item);
        return item;
      },
      onDidChangeWindowState: () => disposable(),
      registerWebviewViewProvider(viewType, provider, options) {
        providers.push({ viewType, provider, options });
        return disposable();
      },
    },
    workspace: {
      workspaceFolders: [
        { uri: { toString: () => "file:///workspace/mira-test" } },
      ],
      getConfiguration(section) {
        return {
          get(key, fallback) {
            if (section === "miraCompanion" && key === "autoOpen") {
              return false;
            }
            return fallback;
          },
        };
      },
      onDidChangeConfiguration: () => disposable(),
    },
  };

  const originalLoad = Module._load;
  Module._load = function patchedLoad(request, parent, isMain) {
    if (request === "vscode") return vscode;
    return originalLoad.call(this, request, parent, isMain);
  };

  const context = {
    extensionPath: path.resolve(__dirname, ".."),
    globalState: {
      get: () => undefined,
      update: async () => undefined,
    },
    workspaceState: {
      get: (_key, fallback) => fallback,
      update: async () => undefined,
    },
    subscriptions: [],
  };

  try {
    const {
      activate,
      markWorldRuntimeOpened,
      shouldAutoOpenWorld,
    } = require("../src/extension");
    activate(context);

    const runtimeStorage = path.join(stateDirectory, "extension-storage");
    const previouslyOpenedContext = {
      globalStorageUri: { fsPath: runtimeStorage },
      workspaceState: { get: () => true },
    };
    assert.equal(shouldAutoOpenWorld(previouslyOpenedContext, true), true);
    assert.equal(markWorldRuntimeOpened(previouslyOpenedContext), true);
    assert.equal(shouldAutoOpenWorld(previouslyOpenedContext, true), false);
    assert.equal(
      fs.statSync(path.join(runtimeStorage, "world-opened-v3")).mode & 0o777,
      0o600,
    );
    assert.equal(
      shouldAutoOpenWorld(
        {
          globalStorageUri: { fsPath: runtimeStorage },
          workspaceState: { get: () => false },
        },
        true,
      ),
      true,
    );
    assert.equal(shouldAutoOpenWorld(previouslyOpenedContext, false), false);

    assert.equal(statusItems.length, 1);
    assert.equal(statusItems[0].id, "miraCompanion.status");
    assert.equal(statusItems[0].visible, true);
    assert.equal(statusItems[0].text, "$(mira-idle-1)");
    assert.match(statusItems[0].tooltip, /Mira World/);
    assert.equal(statusItems[0].command, "miraCompanion.openWorld");
    assert.deepEqual([...commands.keys()], ["miraCompanion.openWorld"]);

    assert.equal(providers.length, 1);
    assert.equal(providers[0].viewType, "miraCompanion.world");
    assert.deepEqual(providers[0].options, {
      webviewOptions: { retainContextWhenHidden: true },
    });

    let receiveMessage;
    const posted = [];
    const webview = {
      cspSource: "webview-resource:",
      options: undefined,
      html: "",
      asWebviewUri(uri) {
        return { toString: () => `webview://${uri.fsPath}` };
      },
      onDidReceiveMessage(listener) {
        receiveMessage = listener;
        return disposable();
      },
      async postMessage(message) {
        posted.push(message);
        return true;
      },
    };
    const view = {
      webview,
      onDidDispose: () => disposable(),
    };
    providers[0].provider.resolveWebviewView(view);

    assert.equal(webview.options.enableScripts, true);
    assert.equal(webview.options.localResourceRoots.length, 2);
    assert.match(webview.html, /world-runtime\.js/);
    assert.match(webview.html, /id="earned-pop"/);
    assert.doesNotMatch(webview.html, /ハイタッチ|なでる|Mira Deck/);

    receiveMessage({ type: "ready" });
    assert.equal(posted.length, 1);
    assert.equal(posted[0].type, "hydrate");
    assert.match(posted[0].assets.map, /worlds\/workshop\.png$/);
    assert.equal(posted[0].assets.animations.walkRight.frames.length, 4);
    assert.equal(posted[0].snapshot.connected, false);

    await commands.get("miraCompanion.openWorld")();
    assert.deepEqual(executedCommands, ["miraCompanion.world.focus"]);
  } finally {
    for (const subscription of [...context.subscriptions].reverse()) {
      subscription.dispose?.();
    }
    Module._load = originalLoad;
    if (originalDirectory === undefined) {
      delete process.env.MIRA_COMPANION_STATE_DIR;
    } else {
      process.env.MIRA_COMPANION_STATE_DIR = originalDirectory;
    }
    fs.rmSync(stateDirectory, { recursive: true, force: true });
  }
});
