"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createProfile } = require("../src/game");
const {
  buildWorldSnapshot,
  dayPhase,
  decorationIds,
  destinationForStatus,
  selectEarnedPop,
  sessionActivity,
} = require("../src/world");

const NOW = Date.parse("2026-08-12T12:00:00.000Z");

function event(id, name, extra = {}) {
  return {
    id,
    at: new Date(NOW).toISOString(),
    event: name,
    status: "success",
    category: null,
    outcome: "unknown",
    activeSubagents: 0,
    ...extra,
  };
}

test("work states have stable geographic destinations", () => {
  assert.equal(destinationForStatus("research", "workspace", 1), 31);
  assert.equal(destinationForStatus("typing", "workspace", 1), 52);
  assert.equal(destinationForStatus("testing", "workspace", 1), 63);
  assert.equal(destinationForStatus("delegating", "workspace", 1), 72);
  assert.equal(
    destinationForStatus("idle", "workspace", 9),
    destinationForStatus("idle", "workspace", 9),
  );
});

test("local time changes atmosphere without network state", () => {
  const atHour = (hour) => {
    const value = new Date(NOW);
    value.setHours(hour, 0, 0, 0);
    return value.getTime();
  };
  assert.equal(dayPhase(atHour(7)), "morning");
  assert.equal(dayPhase(atHour(13)), "day");
  assert.equal(dayPhase(atHour(19)), "evening");
  assert.equal(dayPhase(atHour(23)), "night");
});

test("the map grows from automatic work progress only", () => {
  const profile = createProfile(NOW);
  profile.badges.push({ id: "hello", unlockedAt: "now" });
  profile.counters.turns = 5;
  profile.counters.testsPassed = 1;
  profile.counters.delegations = 3;
  profile.counters.recoveries = 1;
  profile.bondXp = 62;

  assert.deepEqual(decorationIds(profile), [
    "first-sticker",
    "turn-lanterns",
    "green-signal",
    "team-pennant",
    "comeback-star",
    "partner-banner",
  ]);
});

test("one-click reactions are earned at real breakpoints, not always present", () => {
  const profile = createProfile(NOW);
  const completed = event("stop-1", "Stop");
  const shortStats = { research: 2, edit: 2, shell: 1 };
  const longStats = { ...shortStats, test: 1 };

  assert.equal(sessionActivity(shortStats), 5);
  assert.equal(
    selectEarnedPop({
      freshEvents: [completed],
      newBadges: [],
      sessionStats: shortStats,
      previousRecoveries: 0,
      profile,
      nowMs: NOW,
    }),
    null,
  );

  const pop = selectEarnedPop({
    freshEvents: [completed],
    newBadges: [],
    sessionStats: longStats,
    previousRecoveries: 0,
    profile,
    nowMs: NOW,
  });
  assert.equal(pop.kind, "long-task");
  assert.equal(pop.label, "ひと区切り！");
  assert.equal(Date.parse(pop.expiresAt) - NOW, 45_000);
});

test("test failure never asks the user for a companion interaction", () => {
  const profile = createProfile(NOW);
  const pop = selectEarnedPop({
    freshEvents: [
      event("test-red", "PostToolUse", {
        category: "test",
        outcome: "failure",
      }),
    ],
    newBadges: [],
    sessionStats: { research: 3, edit: 3, test: 1 },
    previousRecoveries: 0,
    profile,
    nowMs: NOW,
  });
  assert.equal(pop, null);
});

test("world snapshots expose activity metadata but no prompt or code payload", () => {
  const profile = createProfile(NOW);
  const snapshot = buildWorldSnapshot({
    state: {
      revision: 4,
      status: "typing",
      label: "実装中",
      source: "codex",
      activeSubagents: 9,
      activeAgents: [
        {
          id: "agent-1",
          provider: "grok",
          role: "implementer",
          status: "typing",
          prompt: "must disappear",
        },
        {
          id: "agent-2",
          provider: "private-provider",
          role: "private-role",
          status: "private-status",
        },
      ],
      providerCounts: { codex: 1, claude: 2, grok: 3, private: 99 },
      prompt: "must disappear",
    },
    profile,
    sessionStats: { edit: 2, privateSource: "must disappear" },
    seed: "workspace",
    line: "形にしてる途中〜",
    effectiveStatus: "typing",
    motion: "subtle",
    windowFocused: true,
    earnedPop: null,
    nowMs: NOW,
  });

  assert.equal(snapshot.destination, 52);
  assert.equal(typeof snapshot.ambientSeed, "number");
  assert.match(snapshot.dayPhase, /^(morning|day|evening|night)$/);
  assert.equal(snapshot.activeSubagents, 4);
  assert.deepEqual(snapshot.activeAgents, [
    {
      id: "agent-1",
      provider: "grok",
      role: "implementer",
      status: "typing",
    },
    {
      id: "agent-2",
      provider: "unknown",
      role: "unknown",
      status: "thinking",
    },
  ]);
  assert.deepEqual(snapshot.providerCounts, { codex: 1, claude: 2, grok: 3 });
  assert.equal(snapshot.prompt, undefined);
  assert.equal(snapshot.activeAgents[0].prompt, undefined);
  assert.equal(snapshot.session.privateSource, undefined);
  assert.deepEqual(Object.keys(snapshot.session).sort(), [
    "delegations",
    "edit",
    "research",
    "shell",
    "test",
    "testsFailed",
    "testsPassed",
    "turns",
  ]);
});
