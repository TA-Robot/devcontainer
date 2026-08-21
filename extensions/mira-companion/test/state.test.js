"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { idleState, normalizeState } = require("../src/state");

test("missing and invalid values become idle", () => {
  const missing = normalizeState(null, 0);
  assert.equal(missing.status, "idle");
  assert.equal(missing.label, "未接続");
  assert.equal(missing.source, "extension");
  assert.equal(normalizeState({ status: "unknown" }, 0).status, "idle");
  assert.equal(idleState(0).activeSubagents, 0);
});

test("a valid state keeps only bounded display fields", () => {
  const state = normalizeState(
    {
      status: "delegating",
      message: "仲間を呼んでるよ\u0000" + "x".repeat(200),
      event: "SubagentStart",
      activeSubagents: 2.9,
    },
    0,
  );
  assert.equal(state.status, "delegating");
  assert.equal(state.activeSubagents, 2);
  assert.ok(state.message.length <= 100);
  assert.doesNotMatch(state.message, /\u0000/);
});

test("expired transient state returns to idle", () => {
  const state = normalizeState(
    {
      status: "success",
      message: "完了したよ！",
      expiresAt: "2026-01-01T00:00:00.000Z",
    },
    Date.parse("2026-01-01T00:00:01.000Z"),
  );
  assert.equal(state.status, "idle");
  assert.equal(state.message, "待機中だよ");
});

test("an abandoned active session becomes idle after the bridge TTL", () => {
  const state = normalizeState(
    {
      status: "thinking",
      message: "まだ考えてるよ",
      updatedAt: "2026-08-11T00:00:00.000Z",
      activeSubagents: 3,
      toolCategory: "agent",
    },
    Date.parse("2026-08-11T01:00:00.000Z"),
  );
  assert.equal(state.status, "idle");
  assert.equal(state.message, "待機中だよ");
  assert.equal(state.activeSubagents, 0);
  assert.equal(state.toolCategory, null);
});

test("recent events are bounded and discard every unknown payload field", () => {
  const recentEvents = Array.from({ length: 30 }, (_unused, index) => ({
    id: `event-${index}`,
    at: "2026-08-11T00:00:00Z",
    event: "PostToolUse",
    status: "testing",
    category: index === 29 ? "test" : "private-category",
    outcome: index === 29 ? "failure" : "private-outcome",
    activeSubagents: 2.9,
    session: "hashed-but-not-needed-by-the-extension",
    toolResponse: "must disappear",
    prompt: "must disappear",
  }));
  const state = normalizeState({ status: "testing", recentEvents }, 0);

  assert.equal(state.recentEvents.length, 24);
  assert.equal(state.recentEvents[0].id, "event-6");
  assert.deepEqual(Object.keys(state.recentEvents[0]).sort(), [
    "activeSubagents",
    "at",
    "category",
    "event",
    "id",
    "outcome",
    "status",
  ]);
  assert.equal(state.recentEvents[0].category, null);
  assert.equal(state.recentEvents[0].outcome, "unknown");
  assert.equal(state.recentEvents[0].activeSubagents, 2);
  assert.equal(state.recentEvents[23].category, "test");
  assert.equal(state.recentEvents[23].outcome, "failure");
});
