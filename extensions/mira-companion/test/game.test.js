"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const {
  createProfile,
  currentRhythm,
  lineForState,
  normalizeProfile,
  processEvents,
  profileSummary,
} = require("../src/game");

const NOW = Date.parse("2026-08-11T12:00:00.000Z");

function event(id, name, extra = {}) {
  return {
    id,
    at: new Date(NOW + Number(id.replace(/\D/g, "") || 0) * 1000).toISOString(),
    event: name,
    status: "thinking",
    category: null,
    outcome: "unknown",
    activeSubagents: 0,
    ...extra,
  };
}

test("event ids are idempotent and a completed turn unlocks the first sticker", () => {
  const result = processEvents(
    createProfile(NOW),
    [event("event-1", "Stop"), event("event-1", "Stop")],
    NOW,
  );

  assert.equal(result.profile.counters.turns, 1);
  assert.equal(result.profile.bondXp, 2);
  assert.deepEqual(
    result.profile.badges.map((badge) => badge.id),
    ["hello"],
  );

  const replay = processEvents(result.profile, [event("event-1", "Stop")], NOW);
  assert.equal(replay.changed, false);
  assert.equal(replay.profile.counters.turns, 1);
});

test("automatic bond progress has a daily cap and cannot reward grinding", () => {
  const turns = Array.from({ length: 20 }, (_unused, index) =>
    event(`turn-${index + 1}`, "Stop"),
  );
  let profile = processEvents(createProfile(NOW), turns, NOW).profile;

  assert.equal(profile.daily.automaticXp, 12);
  assert.equal(profile.bondXp, 12);
  assert.equal(profile.counters.turns, 20);
});

test("an explicit test recovery becomes a safe memory and unlocks stickers", () => {
  const result = processEvents(
    createProfile(NOW),
    [
      event("test-1", "PostToolUse", {
        status: "testing",
        category: "test",
        outcome: "failure",
      }),
      event("test-2", "PostToolUse", {
        status: "testing",
        category: "test",
        outcome: "success",
      }),
    ],
    NOW,
  );

  assert.equal(result.profile.counters.testsFailed, 1);
  assert.equal(result.profile.counters.testsPassed, 1);
  assert.equal(result.profile.counters.recoveries, 1);
  assert.ok(result.profile.badges.some((badge) => badge.id === "green-light"));
  assert.ok(result.profile.badges.some((badge) => badge.id === "comeback"));
  assert.ok(
    result.profile.moments.some((moment) => moment.kind === "recovery"),
  );
});

test("a three-agent party is recognized without reading agent content", () => {
  const result = processEvents(
    createProfile(NOW),
    [
      event("agent-1", "SubagentStart", {
        status: "delegating",
        category: "agent",
        activeSubagents: 3,
      }),
    ],
    NOW,
  );
  assert.equal(result.profile.counters.maxSubagents, 3);
  assert.ok(result.profile.badges.some((badge) => badge.id === "party"));
});

test("agentctl lifecycle contributes the same passive team progress", () => {
  const result = processEvents(
    createProfile(NOW),
    [
      event("job-1", "AgentJobStart", {
        status: "typing",
        category: "agent",
        activeSubagents: 1,
        provider: "grok",
        role: "implementer",
      }),
      event("job-2", "AgentJobSucceeded", {
        status: "success",
        category: "agent",
        outcome: "success",
        provider: "grok",
        role: "implementer",
      }),
    ],
    NOW,
  );

  assert.equal(result.profile.counters.delegations, 1);
  assert.equal(result.profile.counters.turns, 1);
  assert.equal(result.profile.bondXp, 3);
  assert.equal(
    lineForState(
      {
        status: "typing",
        revision: 1,
        activeAgents: [{ provider: "grok", role: "implementer" }],
      },
      result.profile,
      "workspace-a",
      NOW,
    ),
    "Grokの実装班が工房で作業中〜",
  );
});

test("profile normalization keeps only bounded game data", () => {
  const profile = normalizeProfile(
    {
      bondXp: 38,
      privatePrompt: "must disappear",
      badges: [
        { id: "hello", unlockedAt: "x".repeat(100) },
        { id: "hello", unlockedAt: "duplicate" },
        { id: "invented", unlockedAt: "never" },
      ],
      moments: [
        {
          id: "m",
          kind: "test",
          at: "now",
          text: "x".repeat(200),
          secret: "drop",
        },
      ],
      seenEventIds: ["e".repeat(200)],
      theme: "not-a-theme",
      themeDate: "2026-08-10",
    },
    NOW,
  );

  assert.equal(profile.privatePrompt, undefined);
  assert.equal(profile.badges.length, 1);
  assert.equal(profile.badges[0].unlockedAt.length, 64);
  assert.equal(profile.moments[0].text.length, 100);
  assert.equal(profile.moments[0].secret, undefined);
  assert.equal(profile.seenEventIds[0].length, 80);
  assert.equal(profile.theme, "curious");
  assert.equal(profile.themeDate, "2026-08-11");
  assert.deepEqual(profileSummary(profile), {
    level: 4,
    title: "作戦会議仲間",
    xp: 38,
    nextLevelXp: 62,
  });
});

test("dialogue is deterministic and rhythm fades instead of punishing absence", () => {
  const profile = createProfile(NOW);
  const state = { status: "typing", revision: 7, recentEvents: [] };
  assert.equal(
    lineForState(state, profile, "workspace-a", NOW),
    lineForState(state, profile, "workspace-a", NOW),
  );

  const withRhythm = processEvents(
    profile,
    [
      event("edit-1", "PreToolUse", { category: "edit" }),
      event("read-2", "PreToolUse", { category: "read" }),
    ],
    NOW,
  ).profile;
  assert.ok(currentRhythm(withRhythm, NOW + 2_000) >= 2);
  assert.equal(currentRhythm(withRhythm, NOW + 30 * 60_000), 0);
});
