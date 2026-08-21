"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const vscode = require("vscode");
const {
  lineForState,
  normalizeProfile,
  processEvents,
} = require("./game");
const { LABELS, idleState, normalizeState } = require("./state");
const {
  buildWorldSnapshot,
  sanitizePop,
  selectEarnedPop,
} = require("./world");
const { MiraWorldViewProvider, VIEW_TYPE } = require("./world-view");

const PROFILE_KEY = "mira.profile.v1";
const WORLD_OPENED_KEY = "mira.world.opened.v2";
const WORLD_RUNTIME_MARKER = "world-opened-v3";
const MOTION_MODES = new Set(["auto", "subtle", "full", "off"]);
const STATUS_ICONS = Object.freeze({
  idle: "mira-idle-1",
  ready: "mira-ready",
  thinking: "mira-thinking",
  research: "mira-research-1",
  typing: "mira-typing-1",
  terminal: "mira-terminal-1",
  testing: "mira-testing-1",
  delegating: "mira-delegating-1",
  approval: "mira-approval",
  success: "mira-success",
  error: "mira-error",
});

function configuredStatePath() {
  const configured = vscode.workspace
    .getConfiguration("miraCompanion")
    .get("stateFile", "")
    .trim();
  if (configured)
    return path.resolve(configured.replace(/^~(?=$|\/)/, os.homedir()));
  const explicitDirectory = process.env.MIRA_COMPANION_STATE_DIR;
  if (explicitDirectory) return path.join(explicitDirectory, "state.json");
  const xdgState =
    process.env.XDG_STATE_HOME || path.join(os.homedir(), ".local", "state");
  return path.join(xdgState, "mira-companion", "state.json");
}

function readState(statePath) {
  try {
    return normalizeState(JSON.parse(fs.readFileSync(statePath, "utf8")));
  } catch (_error) {
    return idleState();
  }
}

class MiraStateStore {
  constructor(statePath) {
    this.statePath = statePath;
    this.current = readState(statePath);
    this.emitter = new vscode.EventEmitter();
    this.onDidChange = this.emitter.event;
    this.fileWatcher = undefined;
    this.poller = undefined;
    this.expiryTimer = undefined;
    this.lastSignature = "";
    this.start();
  }

  start() {
    this.stopWatchers();
    const directory = path.dirname(this.statePath);
    try {
      fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
      this.fileWatcher = fs.watch(
        directory,
        { persistent: false },
        (_event, filename) => {
          if (
            !filename ||
            filename.toString() === path.basename(this.statePath)
          ) {
            this.refresh(true);
          }
        },
      );
      this.fileWatcher.on("error", () => {});
    } catch (_error) {
      this.fileWatcher = undefined;
    }
    this.poller = setInterval(() => this.refresh(), 1000);
    this.poller.unref?.();
    this.refresh(true);
  }

  refresh(force = false) {
    let signature = "missing";
    try {
      const stat = fs.statSync(this.statePath);
      signature = `${stat.mtimeMs}:${stat.size}`;
    } catch (_error) {
      // Missing state means disconnected idle.
    }
    const expiredLocally =
      this.current.expiresAt &&
      Date.parse(this.current.expiresAt) <= Date.now();
    if (!force && signature === this.lastSignature && !expiredLocally) return;
    this.lastSignature = signature;
    this.current = readState(this.statePath);
    this.scheduleExpiry();
    this.emitter.fire(this.current);
  }

  scheduleExpiry() {
    if (this.expiryTimer) clearTimeout(this.expiryTimer);
    this.expiryTimer = undefined;
    if (!this.current.expiresAt) return;
    const delay = Date.parse(this.current.expiresAt) - Date.now();
    if (delay > 0) {
      this.expiryTimer = setTimeout(
        () => this.refresh(true),
        Math.min(delay + 25, 2_147_483_647),
      );
      this.expiryTimer.unref?.();
    }
  }

  setPath(statePath) {
    if (statePath === this.statePath) return;
    this.statePath = statePath;
    this.lastSignature = "";
    this.start();
  }

  stopWatchers() {
    this.fileWatcher?.close();
    this.fileWatcher = undefined;
    if (this.poller) clearInterval(this.poller);
    if (this.expiryTimer) clearTimeout(this.expiryTimer);
    this.poller = undefined;
    this.expiryTimer = undefined;
  }

  dispose() {
    this.stopWatchers();
    this.emitter.dispose();
  }
}

function findAssetRoot(context) {
  const packaged = path.join(context.extensionPath, "assets");
  if (fs.existsSync(path.join(packaged, "manifest.json"))) return packaged;
  const repositoryAssets = path.resolve(
    context.extensionPath,
    "..",
    "..",
    "assets",
    "mira",
  );
  if (fs.existsSync(path.join(repositoryAssets, "manifest.json"))) {
    return repositoryAssets;
  }
  throw new Error(
    "Mira assets were not found in the extension package or repository.",
  );
}

function workspaceSeed() {
  const identity =
    (vscode.workspace.workspaceFolders || [])
      .map((folder) => folder.uri.toString())
      .join("|") || "no-workspace";
  return crypto
    .createHash("sha256")
    .update(identity)
    .digest("hex")
    .slice(0, 16);
}

function worldRuntimeMarkerPath(context) {
  const storagePath = context.globalStorageUri?.fsPath;
  return storagePath ? path.join(storagePath, WORLD_RUNTIME_MARKER) : undefined;
}

function hasWorldRuntimeMarker(context) {
  const markerPath = worldRuntimeMarkerPath(context);
  return Boolean(markerPath && fs.existsSync(markerPath));
}

function markWorldRuntimeOpened(context) {
  const markerPath = worldRuntimeMarkerPath(context);
  if (!markerPath) return false;
  fs.mkdirSync(path.dirname(markerPath), { recursive: true, mode: 0o700 });
  fs.writeFileSync(markerPath, "opened\n", { encoding: "utf8", mode: 0o600 });
  return true;
}

function shouldAutoOpenWorld(context, autoOpen) {
  if (!autoOpen) return false;
  const workspaceOpened = context.workspaceState.get(WORLD_OPENED_KEY, false);
  return !workspaceOpened || !hasWorldRuntimeMarker(context);
}

function emptySessionStats() {
  return {
    research: 0,
    edit: 0,
    shell: 0,
    test: 0,
    testsPassed: 0,
    testsFailed: 0,
    delegations: 0,
    turns: 0,
  };
}

class MiraCompanion {
  constructor(context, store, worldProvider) {
    this.context = context;
    this.store = store;
    this.worldProvider = worldProvider;
    this.seed = workspaceSeed();
    this.profile = normalizeProfile(context.globalState.get(PROFILE_KEY));
    this.sessionStats = emptySessionStats();
    this.state = store.current;
    this.line = lineForState(this.state, this.profile, this.seed);
    this.reaction = undefined;
    this.reactionTimer = undefined;
    this.earnedPop = undefined;
    this.popTimer = undefined;
    this.windowFocused = vscode.window.state.focused;
    this.persistPromise = Promise.resolve();

    this.statusBar = vscode.window.createStatusBarItem(
      "miraCompanion.status",
      vscode.StatusBarAlignment.Right,
      50,
    );
    this.statusBar.name = "Mira World";
    this.statusBar.command = "miraCompanion.openWorld";

    this.stateSubscription = store.onDidChange((state) =>
      this.consumeState(state),
    );
    this.configurationSubscription = vscode.workspace.onDidChangeConfiguration(
      (event) => {
        if (event.affectsConfiguration("miraCompanion.stateFile")) {
          store.setPath(configuredStatePath());
        }
        if (
          event.affectsConfiguration("miraCompanion") ||
          event.affectsConfiguration("workbench.reduceMotion")
        ) {
          this.render();
        }
      },
    );
    this.windowSubscription = vscode.window.onDidChangeWindowState((state) => {
      this.windowFocused = state.focused;
      this.render();
    });

    this.consumeState(this.state);
  }

  consumeState(state) {
    const nowMs = Date.now();
    const previouslySeen = new Set(this.profile.seenEventIds);
    const previousRecoveries = this.profile.counters.recoveries;
    const freshEvents = (state.recentEvents || []).filter(
      (event) => event.id && !previouslySeen.has(event.id),
    );
    this.updateSessionStats(freshEvents);
    const result = processEvents(this.profile, state.recentEvents || [], nowMs);
    this.profile = result.profile;
    this.state = state;
    this.line = lineForState(state, this.profile, this.seed, nowMs);
    if (result.changed) this.persistProfile();

    const earnedPop = selectEarnedPop({
      freshEvents,
      newBadges: result.newBadges,
      sessionStats: this.sessionStats,
      previousRecoveries,
      profile: this.profile,
      nowMs,
    });
    if (earnedPop) this.setEarnedPop(earnedPop, nowMs);

    const latestTest = [...freshEvents]
      .reverse()
      .find(
        (event) =>
          event.event === "PostToolUse" &&
          event.category === "test" &&
          event.outcome !== "unknown",
      );
    if (latestTest && state.status !== "approval") {
      if (latestTest.outcome === "failure") {
        this.setReaction("赤は失敗じゃなくて手がかり", "error", 3400);
      } else {
        this.setReaction("青信号、きれいに通った！", "success", 3000);
      }
      return;
    }
    const latestAgentTerminal = [...freshEvents]
      .reverse()
      .find((event) =>
        [
          "AgentJobSucceeded",
          "AgentJobFailed",
          "AgentJobOrphaned",
        ].includes(event.event),
      );
    if (latestAgentTerminal && state.status !== "approval") {
      if (latestAgentTerminal.outcome === "success") {
        this.setReaction("agent job、きれいに着地した〜", "success", 3200);
      } else {
        this.setReaction("agent jobを切り分け直してるよ", "error", 3600);
      }
      return;
    }
    this.render(nowMs);
  }

  updateSessionStats(events) {
    for (const event of events) {
      if (event.event === "SessionStart") {
        this.sessionStats = emptySessionStats();
      }
      if (event.event === "PreToolUse") {
        if (event.category === "read") this.sessionStats.research += 1;
        if (event.category === "edit") this.sessionStats.edit += 1;
        if (event.category === "shell") this.sessionStats.shell += 1;
        if (event.category === "test") this.sessionStats.test += 1;
      }
      if (event.event === "PostToolUse" && event.category === "test") {
        if (event.outcome === "success") this.sessionStats.testsPassed += 1;
        if (event.outcome === "failure") this.sessionStats.testsFailed += 1;
      }
      if (["SubagentStart", "AgentJobStart"].includes(event.event))
        this.sessionStats.delegations += 1;
      if (["Stop", "AgentJobSucceeded"].includes(event.event))
        this.sessionStats.turns += 1;
    }
  }

  persistProfile() {
    const snapshot = JSON.parse(JSON.stringify(this.profile));
    this.persistPromise = this.persistPromise
      .then(() => this.context.globalState.update(PROFILE_KEY, snapshot))
      .catch(() => {});
  }

  motionMode() {
    const configured = vscode.workspace
      .getConfiguration("miraCompanion")
      .get("motion", "auto");
    if (!MOTION_MODES.has(configured)) return "subtle";
    if (configured !== "auto") return configured;
    const reduceMotion = vscode.workspace
      .getConfiguration("workbench")
      .get("reduceMotion", "auto");
    return reduceMotion === "on" ? "off" : "subtle";
  }

  effectiveStatus() {
    if (this.state.status === "approval") return "approval";
    return this.reaction?.status || this.state.status;
  }

  effectiveLine() {
    if (this.state.status === "approval") return this.line;
    return this.reaction?.line || this.line;
  }

  setReaction(line, status = "success", duration = 3000) {
    if (this.reactionTimer) clearTimeout(this.reactionTimer);
    this.reaction = { line, status };
    this.reactionTimer = setTimeout(() => {
      this.reaction = undefined;
      this.reactionTimer = undefined;
      this.line = lineForState(this.state, this.profile, this.seed);
      this.render();
    }, duration);
    this.reactionTimer.unref?.();
    this.render();
  }

  setEarnedPop(pop, nowMs = Date.now()) {
    const sanitized = sanitizePop(pop, nowMs);
    if (!sanitized || this.earnedPop?.id === sanitized.id) return;
    if (this.popTimer) clearTimeout(this.popTimer);
    this.earnedPop = sanitized;
    const delay = Date.parse(sanitized.expiresAt) - nowMs;
    this.popTimer = setTimeout(() => {
      this.earnedPop = undefined;
      this.popTimer = undefined;
      this.render();
    }, Math.max(1, Math.min(delay + 25, 2_147_483_647)));
    this.popTimer.unref?.();
  }

  acknowledgePop(id) {
    if (!this.earnedPop || this.earnedPop.id !== id) return;
    const line = this.earnedPop.line;
    if (this.popTimer) clearTimeout(this.popTimer);
    this.earnedPop = undefined;
    this.popTimer = undefined;
    this.setReaction(line, "success", 3800);
  }

  render(nowMs = Date.now()) {
    const status = this.effectiveStatus();
    const showStatusBar = vscode.workspace
      .getConfiguration("miraCompanion")
      .get("statusBar", true);
    if (showStatusBar) {
      const icon = STATUS_ICONS[status] || STATUS_ICONS.idle;
      this.statusBar.text = `$(${icon})`;
      this.statusBar.tooltip = `Mira World — ${LABELS[status] || this.state.label}\nクリックでbottom worldを開く`;
      this.statusBar.accessibilityInformation = {
        label: `ミラ、${LABELS[status] || this.state.label}。Mira Worldを開く`,
        role: "button",
      };
      this.statusBar.show();
    } else {
      this.statusBar.hide();
    }

    const effectiveState = {
      ...this.state,
      label: LABELS[status] || this.state.label,
    };
    this.worldProvider.update(
      buildWorldSnapshot({
        state: effectiveState,
        profile: this.profile,
        sessionStats: this.sessionStats,
        seed: this.seed,
        line: this.effectiveLine(),
        effectiveStatus: status,
        motion: this.motionMode(),
        windowFocused: this.windowFocused,
        earnedPop: this.earnedPop,
        nowMs,
      }),
    );
  }

  async openWorld() {
    await vscode.commands.executeCommand(`${VIEW_TYPE}.focus`);
  }

  maybeOpenWorld() {
    const autoOpen = vscode.workspace
      .getConfiguration("miraCompanion")
      .get("autoOpen", true);
    if (!shouldAutoOpenWorld(this.context, autoOpen)) return;
    const timer = setTimeout(async () => {
      try {
        await this.openWorld();
        await this.context.workspaceState.update(WORLD_OPENED_KEY, true);
        markWorldRuntimeOpened(this.context);
      } catch (_error) {
        // The status-bar toggle remains available if the panel cannot be focused.
      }
    }, 650);
    timer.unref?.();
    this.context.subscriptions.push({ dispose: () => clearTimeout(timer) });
  }

  dispose() {
    if (this.reactionTimer) clearTimeout(this.reactionTimer);
    if (this.popTimer) clearTimeout(this.popTimer);
    this.stateSubscription.dispose();
    this.configurationSubscription.dispose();
    this.windowSubscription.dispose();
    this.statusBar.dispose();
  }
}

function activate(context) {
  const store = new MiraStateStore(configuredStatePath());
  const assetRoot = findAssetRoot(context);
  let companion;
  const worldProvider = new MiraWorldViewProvider(
    context,
    assetRoot,
    (id) => companion?.acknowledgePop(id),
  );
  const viewRegistration = vscode.window.registerWebviewViewProvider(
    VIEW_TYPE,
    worldProvider,
    { webviewOptions: { retainContextWhenHidden: true } },
  );
  companion = new MiraCompanion(context, store, worldProvider);
  const openWorldCommand = vscode.commands.registerCommand(
    "miraCompanion.openWorld",
    () => companion.openWorld(),
  );
  context.subscriptions.push(
    store,
    worldProvider,
    viewRegistration,
    companion,
    openWorldCommand,
  );
  companion.maybeOpenWorld();
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
  markWorldRuntimeOpened,
  shouldAutoOpenWorld,
};
