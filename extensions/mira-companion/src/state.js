"use strict";

const STATES = new Set([
  "idle",
  "ready",
  "thinking",
  "research",
  "typing",
  "terminal",
  "testing",
  "delegating",
  "approval",
  "success",
  "error",
]);

const LABELS = Object.freeze({
  idle: "待機中",
  ready: "準備完了",
  thinking: "思考中",
  research: "調査中",
  typing: "実装中",
  terminal: "実行中",
  testing: "検証中",
  delegating: "委譲中",
  approval: "確認待ち",
  success: "完了",
  error: "エラー",
});

const DEFAULT_MESSAGES = Object.freeze({
  idle: "待機中だよ",
  ready: "準備できたよ",
  thinking: "方針を考えてるよ",
  research: "調べもの中だよ",
  typing: "実装してるよ",
  terminal: "コマンドを実行中だよ",
  testing: "テストで確認中だよ",
  delegating: "みんなにお願いしてるよ",
  approval: "確認を待ってるよ",
  success: "完了したよ！",
  error: "うまくいかなかったみたい",
});

const EVENT_CATEGORIES = new Set([
  "agent",
  "approval",
  "edit",
  "planning",
  "read",
  "shell",
  "test",
  "tool",
]);

const OUTCOMES = new Set(["success", "failure", "unknown"]);
const AGENT_PROVIDERS = new Set(["codex", "claude", "grok", "unknown"]);
const AGENT_ROLES = new Set([
  "implementer",
  "researcher",
  "reviewer",
  "tester",
  "unknown",
]);
const ACTIVE_STATE_TTL_MS = 60 * 60 * 1000;

function finiteInteger(value, fallback = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return fallback;
  }
  return Math.max(0, Math.floor(number));
}

function cleanText(value, limit) {
  return String(value ?? "")
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .slice(0, limit);
}

function idleState(nowMs = Date.now()) {
  return {
    schemaVersion: 1,
    revision: 0,
    updatedAt: new Date(nowMs).toISOString(),
    status: "idle",
    label: "未接続",
    message: "activity連携を待ってるよ",
    event: "StateFileMissing",
    toolCategory: null,
    activeSubagents: 0,
    activeAgents: [],
    providerCounts: { codex: 0, claude: 0, grok: 0 },
    expiresAt: null,
    source: "extension",
    recentEvents: [],
  };
}

function normalizeEvent(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  const status = STATES.has(value.status) ? value.status : "thinking";
  const category = EVENT_CATEGORIES.has(value.category) ? value.category : null;
  const outcome = OUTCOMES.has(value.outcome) ? value.outcome : "unknown";
  return {
    id: cleanText(value.id, 80),
    at: cleanText(value.at, 64),
    event: cleanText(value.event || "Unknown", 80),
    status,
    category,
    outcome,
    activeSubagents: finiteInteger(value.activeSubagents),
    provider: AGENT_PROVIDERS.has(value.provider)
      ? value.provider
      : "unknown",
    role: AGENT_ROLES.has(value.role) ? value.role : "unknown",
  };
}

function normalizeAgent(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return {
    id: cleanText(value.id, 32),
    provider: AGENT_PROVIDERS.has(value.provider)
      ? value.provider
      : "unknown",
    role: AGENT_ROLES.has(value.role) ? value.role : "unknown",
    status: STATES.has(value.status) ? value.status : "thinking",
  };
}

function normalizeProviderCounts(value) {
  const source = value && typeof value === "object" ? value : {};
  return {
    codex: Math.min(99, finiteInteger(source.codex)),
    claude: Math.min(99, finiteInteger(source.claude)),
    grok: Math.min(99, finiteInteger(source.grok)),
  };
}

function normalizeState(value, nowMs = Date.now()) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return idleState(nowMs);
  }

  let status = STATES.has(value.status) ? value.status : "idle";
  const updatedAtText = cleanText(
    value.updatedAt || new Date(nowMs).toISOString(),
    64,
  );
  const updatedAt = Date.parse(updatedAtText);
  const expiresAt = value.expiresAt ? Date.parse(value.expiresAt) : Number.NaN;
  const expired = Number.isFinite(expiresAt) && expiresAt <= nowMs;
  const stale =
    status !== "idle" &&
    Number.isFinite(updatedAt) &&
    updatedAt + ACTIVE_STATE_TTL_MS <= nowMs;
  if (expired || stale) {
    status = "idle";
  }

  const recentEvents = Array.isArray(value.recentEvents)
    ? value.recentEvents.map(normalizeEvent).filter(Boolean).slice(-24)
    : [];
  const activeAgents =
    status !== "idle" && Array.isArray(value.activeAgents)
      ? value.activeAgents.map(normalizeAgent).filter(Boolean).slice(0, 8)
      : [];
  const providerCounts =
    status === "idle"
      ? { codex: 0, claude: 0, grok: 0 }
      : normalizeProviderCounts(value.providerCounts);

  return {
    schemaVersion: 1,
    revision: finiteInteger(value.revision),
    updatedAt: updatedAtText,
    status,
    label: LABELS[status],
    message:
      status === value.status && cleanText(value.message, 100)
        ? cleanText(value.message, 100)
        : DEFAULT_MESSAGES[status],
    event: cleanText(value.event || "Unknown", 80),
    toolCategory:
      status !== "idle" && value.toolCategory
        ? cleanText(value.toolCategory, 40)
        : null,
    activeSubagents:
      status === "idle" ? 0 : finiteInteger(value.activeSubagents),
    activeAgents,
    providerCounts,
    expiresAt:
      Number.isFinite(expiresAt) && !expired && !stale
        ? new Date(expiresAt).toISOString()
        : null,
    source: cleanText(value.source || "unknown", 40),
    recentEvents,
  };
}

module.exports = {
  DEFAULT_MESSAGES,
  LABELS,
  STATES,
  idleState,
  normalizeAgent,
  normalizeEvent,
  normalizeState,
};
