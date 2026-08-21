"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vscode = require("vscode");

const VIEW_TYPE = "miraCompanion.world";

function escapeAttribute(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

class MiraWorldViewProvider {
  constructor(context, assetRoot, onAcknowledgePop) {
    this.context = context;
    this.assetRoot = assetRoot;
    this.onAcknowledgePop = onAcknowledgePop;
    this.snapshot = undefined;
    this.view = undefined;
    this.messageSubscription = undefined;
    this.viewDisposeSubscription = undefined;
    this.manifest = JSON.parse(
      fs.readFileSync(path.join(assetRoot, "manifest.json"), "utf8"),
    );
  }

  resolveWebviewView(view) {
    this.disposeViewSubscriptions();
    this.view = view;
    const mediaRoot = path.join(this.context.extensionPath, "media");
    view.webview.options = {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.file(this.assetRoot),
        vscode.Uri.file(mediaRoot),
      ],
    };
    this.messageSubscription = view.webview.onDidReceiveMessage((message) => {
      if (!message || typeof message !== "object") return;
      if (message.type === "ready") this.postHydrate();
      if (message.type === "ackPop" && typeof message.id === "string") {
        this.onAcknowledgePop?.(message.id.slice(0, 120));
      }
    });
    view.webview.html = this.html(view.webview, mediaRoot);
    this.viewDisposeSubscription = view.onDidDispose?.(() => {
      this.disposeViewSubscriptions();
      this.view = undefined;
    });
  }

  update(snapshot) {
    this.snapshot = snapshot;
    void this.view?.webview.postMessage({ type: "update", snapshot });
  }

  postHydrate() {
    if (!this.view) return;
    void this.view.webview.postMessage({
      type: "hydrate",
      assets: this.assetCatalog(this.view.webview),
      snapshot: this.snapshot,
    });
  }

  assetCatalog(webview) {
    const uri = (relative) =>
      webview
        .asWebviewUri(vscode.Uri.file(path.join(this.assetRoot, relative)))
        .toString();
    const animation = (setName, animationName) => {
      const value = this.manifest.sets[setName].animations[animationName];
      return { frames: value.frames.map(uri), fps: value.fps };
    };
    const pose = (setName, poseName) => ({
      frames: [uri(this.manifest.sets[setName].poses[poseName])],
      fps: 1,
    });
    const companions = Object.entries(this.manifest.sets.companions.roles).map(
      ([role, frames]) => ({
        role,
        idle: uri(frames.idle),
        active: uri(frames.active),
        done: uri(frames.done),
      }),
    );
    return {
      map: uri(this.manifest.worlds.workshop.background),
      animations: {
        idle: animation("core-motion", "idle"),
        walkRight: animation("core-motion", "walk-right"),
        walkLeft: animation("core-motion", "walk-left"),
        ready: pose("status-emotions", "ready"),
        thinking: pose("status-emotions", "thinking"),
        research: animation("work-actions", "research"),
        typing: animation("work-actions", "typing"),
        terminal: animation("work-actions", "terminal"),
        testing: animation("work-actions", "testing"),
        delegating: {
          frames: [
            "delegate-one",
            "delegate-two",
            "delegate-dispatch",
            "delegate-watch",
          ].map((name) => uri(this.manifest.sets.orchestration.poses[name])),
          fps: 4,
        },
        approval: pose("status-emotions", "approval"),
        success: pose("orchestration", "complete"),
        error: pose("status-emotions", "error"),
      },
      companions,
    };
  }

  html(webview, mediaRoot) {
    const nonce = crypto.randomBytes(18).toString("base64url");
    const styleUri = webview.asWebviewUri(
      vscode.Uri.file(path.join(mediaRoot, "world.css")),
    );
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.file(path.join(mediaRoot, "world-runtime.js")),
    );
    const csp = [
      "default-src 'none'",
      `img-src ${webview.cspSource}`,
      `style-src ${webview.cspSource}`,
      `script-src 'nonce-${nonce}'`,
    ].join("; ");
    return `<!doctype html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="${escapeAttribute(csp)}">
  <link rel="stylesheet" href="${escapeAttribute(styleUri)}">
  <title>Mira World</title>
</head>
<body>
  <main id="world" class="world" aria-label="ミラの開発ワールド">
    <img id="world-map" class="world__map" alt="" aria-hidden="true">
    <div class="world__shade" aria-hidden="true"></div>
    <div id="decorations" class="decorations" aria-hidden="true">
      <i data-decoration="first-sticker" class="decoration decoration--sticker"></i>
      <i data-decoration="turn-lanterns" class="decoration decoration--lanterns"></i>
      <i data-decoration="green-signal" class="decoration decoration--signal"></i>
      <i data-decoration="team-pennant" class="decoration decoration--pennant"></i>
      <i data-decoration="comeback-star" class="decoration decoration--star"></i>
      <i data-decoration="partner-banner" class="decoration decoration--banner"></i>
    </div>
    <div id="companions" class="companions" aria-hidden="true"></div>
    <div id="mira" class="mira" aria-hidden="true"><img id="mira-sprite" alt=""></div>
    <button id="earned-pop" class="earned-pop" type="button" hidden></button>
    <div class="hud">
      <span id="status" class="hud__status">準備中</span>
      <span id="line" class="hud__line"></span>
      <span id="session" class="hud__session"></span>
      <span id="progress" class="hud__progress"></span>
    </div>
    <span id="announcement" class="sr-only" aria-live="polite"></span>
  </main>
  <script nonce="${nonce}" src="${escapeAttribute(scriptUri)}"></script>
</body>
</html>`;
  }

  disposeViewSubscriptions() {
    this.messageSubscription?.dispose();
    this.viewDisposeSubscription?.dispose();
    this.messageSubscription = undefined;
    this.viewDisposeSubscription = undefined;
  }

  dispose() {
    this.disposeViewSubscriptions();
    this.view = undefined;
  }
}

module.exports = { MiraWorldViewProvider, VIEW_TYPE };
