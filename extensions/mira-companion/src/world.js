"use strict";

const { currentRhythm, profileSummary } = require("./game");

const DESTINATIONS = Object.freeze({
  idle: 48,
  ready: 48,
  thinking: 41,
  research: 31,
  typing: 52,
  terminal: 56,
  testing: 63,
  delegating: 72,
  approval: 68,
  success: 63,
  error: 60,
});

const IDLE_WAYPOINTS = Object.freeze([27, 34, 41, 48, 55, 63, 72]);
const MOTION_MODES = new Set(["subtle", "full", "off"]);
const POP_LIFETIME_MS = 45_000;

function finiteCount(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.floor(number)) : 0;
}

function boundedText(value, limit = 100) {
  return String(value ?? "")
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .slice(0, limit);
}

function hashText(value) {
  let hash = 2166136261;
  for (const character of String(value)) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function destinationForStatus(status, seed = "workspace", revision = 0) {
  if (status === "idle") {
    const index = hashText(`${seed}:${revision}:idle`) % IDLE_WAYPOINTS.length;
    return IDLE_WAYPOINTS[index];
  }
  return DESTINATIONS[status] ?? DESTINATIONS.idle;
}

function dayPhase(nowMs = Date.now()) {
  const hour = new Date(nowMs).getHours();
  if (hour >= 5 && hour < 10) return "morning";
  if (hour >= 10 && hour < 18) return "day";
  if (hour >= 18 && hour < 22) return "evening";
  return "night";
}

function sessionActivity(stats) {
  const source = stats && typeof stats === "object" ? stats : {};
  return (
    finiteCount(source.research) +
    finiteCount(source.edit) +
    finiteCount(source.shell) +
    finiteCount(source.test) +
    finiteCount(source.delegations)
  );
}

function decorationIds(profile) {
  const counters = profile?.counters || {};
  const summary = profileSummary(profile);
  const decorations = [];
  if ((profile?.badges || []).length >= 1) decorations.push("first-sticker");
  if (finiteCount(counters.turns) >= 5) decorations.push("turn-lanterns");
  if (finiteCount(counters.testsPassed) >= 1) decorations.push("green-signal");
  if (finiteCount(counters.delegations) >= 3) decorations.push("team-pennant");
  if (finiteCount(counters.recoveries) >= 1) decorations.push("comeback-star");
  if (summary.level >= 5) decorations.push("partner-banner");
  return decorations;
}

function latestEvent(events, predicate) {
  return [...(Array.isArray(events) ? events : [])].reverse().find(predicate);
}

function createPop(kind, sourceEvent, label, line, nowMs) {
  const sourceId = boundedText(sourceEvent?.id || `${kind}-${nowMs}`, 80);
  return {
    id: `mira-pop:${kind}:${sourceId}`,
    kind,
    label: boundedText(label, 32),
    line: boundedText(line, 100),
    expiresAt: new Date(nowMs + POP_LIFETIME_MS).toISOString(),
  };
}

function selectEarnedPop({
  freshEvents,
  newBadges,
  sessionStats,
  previousRecoveries,
  profile,
  nowMs = Date.now(),
}) {
  const events = Array.isArray(freshEvents) ? freshEvents : [];
  const sourceEvent = events[events.length - 1];
  const newestBadge = Array.isArray(newBadges)
    ? newBadges[newBadges.length - 1]
    : undefined;
  if (newestBadge && sourceEvent) {
    return createPop(
      "badge",
      sourceEvent,
      "ステッカーを受け取る",
      `「${boundedText(newestBadge.title, 40)}」みつけた！`,
      nowMs,
    );
  }

  const recovered =
    finiteCount(profile?.counters?.recoveries) > finiteCount(previousRecoveries);
  const recoveryEvent = latestEvent(
    events,
    (event) =>
      event.event === "PostToolUse" &&
      event.category === "test" &&
      event.outcome === "success",
  );
  if (recovered && recoveryEvent) {
    return createPop(
      "recovery",
      recoveryEvent,
      "立て直しを祝う",
      "赤から青へ！ きれいに立て直した〜",
      nowMs,
    );
  }

  const completed = latestEvent(
    events,
    (event) => event.event === "Stop" || event.event === "SessionEnd",
  );
  if (completed && sessionActivity(sessionStats) >= 6) {
    return createPop(
      "long-task",
      completed,
      "ひと区切り！",
      "長い作業、ちゃんと着地したね！",
      nowMs,
    );
  }

  const passed = latestEvent(
    events,
    (event) =>
      event.event === "PostToolUse" &&
      event.category === "test" &&
      event.outcome === "success",
  );
  if (passed && sessionActivity(sessionStats) >= 3) {
    return createPop(
      "test-pass",
      passed,
      "青信号を点ける",
      "青信号、きれいに通った！",
      nowMs,
    );
  }
  return null;
}

function sanitizePop(pop, nowMs = Date.now()) {
  if (!pop || typeof pop !== "object") return null;
  const expiresAt = Date.parse(pop.expiresAt);
  if (!Number.isFinite(expiresAt) || expiresAt <= nowMs) return null;
  return {
    id: boundedText(pop.id, 120),
    kind: boundedText(pop.kind, 32),
    label: boundedText(pop.label, 32),
    line: boundedText(pop.line, 100),
    expiresAt: new Date(expiresAt).toISOString(),
  };
}

function sanitizeSession(stats) {
  const source = stats && typeof stats === "object" ? stats : {};
  return {
    research: finiteCount(source.research),
    edit: finiteCount(source.edit),
    shell: finiteCount(source.shell),
    test: finiteCount(source.test),
    testsPassed: finiteCount(source.testsPassed),
    testsFailed: finiteCount(source.testsFailed),
    delegations: finiteCount(source.delegations),
    turns: finiteCount(source.turns),
  };
}

function buildWorldSnapshot({
  state,
  profile,
  sessionStats,
  seed,
  line,
  effectiveStatus,
  motion,
  windowFocused,
  earnedPop,
  nowMs = Date.now(),
}) {
  const status = DESTINATIONS[effectiveStatus]
    ? effectiveStatus
    : state?.status || "idle";
  const summary = profileSummary(profile);
  return {
    schemaVersion: 1,
    revision: finiteCount(state?.revision),
    status,
    label: boundedText(state?.label || "待機中", 32),
    line: boundedText(line, 100),
    destination: destinationForStatus(
      status,
      seed,
      finiteCount(state?.revision),
    ),
    ambientSeed: hashText(`${seed}:ambient`),
    dayPhase: dayPhase(nowMs),
    connected: state?.source !== "extension",
    activeSubagents: Math.min(4, finiteCount(state?.activeSubagents)),
    motion: MOTION_MODES.has(motion) ? motion : "subtle",
    windowFocused: Boolean(windowFocused),
    rhythm: currentRhythm(profile, nowMs),
    progress: {
      level: summary.level,
      title: boundedText(summary.title, 40),
      xp: finiteCount(summary.xp),
      nextLevelXp:
        summary.nextLevelXp === null
          ? null
          : finiteCount(summary.nextLevelXp),
      badges: Math.min(99, (profile?.badges || []).length),
    },
    session: sanitizeSession(sessionStats),
    decorations: decorationIds(profile),
    earnedPop: sanitizePop(earnedPop, nowMs),
  };
}

module.exports = {
  DESTINATIONS,
  IDLE_WAYPOINTS,
  POP_LIFETIME_MS,
  buildWorldSnapshot,
  dayPhase,
  decorationIds,
  destinationForStatus,
  sanitizePop,
  selectEarnedPop,
  sessionActivity,
};
