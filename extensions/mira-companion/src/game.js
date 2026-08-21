"use strict";

const PROFILE_SCHEMA_VERSION = 1;
const MAX_MOMENTS = 20;
const MAX_SEEN_EVENTS = 96;
const LEVEL_THRESHOLDS = Object.freeze([
  0, 8, 20, 38, 62, 92, 128, 170, 218, 272, 332, 398, 470, 548, 632, 722, 818,
  920, 1028, 1142,
]);

const THEMES = Object.freeze({
  curious: { label: "好奇心モード", line: "気になるとこ、ひとつ拾ってこ" },
  steady: { label: "じっくりモード", line: "焦らず一個ずつ、でいこ" },
  bold: { label: "大胆モード", line: "小さく試して、当たり引こ" },
  playful: { label: "遊び心モード", line: "面白い方、ちょっと覗こ" },
});

const BADGES = Object.freeze([
  {
    id: "hello",
    title: "はじめまして",
    description: "最初のturnを一緒に完了した",
  },
  {
    id: "detective",
    title: "探偵モード",
    description: "調査eventを10回見届けた",
  },
  {
    id: "builder",
    title: "組み立て上手",
    description: "編集eventを10回見届けた",
  },
  { id: "green-light", title: "青信号", description: "test成功を確認した" },
  { id: "conductor", title: "指揮者", description: "subagentを3回迎えた" },
  {
    id: "comeback",
    title: "立て直し名人",
    description: "test failureからsuccessへ戻した",
  },
  {
    id: "party",
    title: "にぎやか開発部",
    description: "subagentが同時に3人集まった",
  },
  { id: "partner", title: "相棒", description: "bond level 5になった" },
]);

const LINES = Object.freeze({
  idle: [
    "ここいるよ、続きやろ",
    "静かに待機してる〜",
    "次の一手、いつでもどぞ",
    "今の余白もけっこう大事",
  ],
  ready: [
    "今日も一緒にいこ",
    "準備おっけ、始めよ",
    "よし、作戦会議スタート",
    "今日は何見つけよっか",
  ],
  thinking: [
    "いま筋道つないでる",
    "ちょい待ち、形見えてきた",
    "選択肢ならべてるとこ",
    "ここ、ちゃんと考えるね",
  ],
  research: [
    "手がかり拾ってくる",
    "探偵モード入った",
    "根拠あるとこまで見るね",
    "この辺、匂うんだよね",
  ],
  typing: [
    "いま組み立ててる",
    "形にしてる途中〜",
    "差分ちっちゃく綺麗にね",
    "ここ、手を入れてくる",
  ],
  terminal: [
    "工房うごかしてる",
    "コマンド結果みよ",
    "実行して確かめるね",
    "ログ、ちゃんと見てるよ",
  ],
  testing: [
    "青信号か見てくる",
    "答え合わせ中〜",
    "ここ通ればかなり綺麗",
    "テストに聞いてみよ",
  ],
  delegating: [
    "みんなに声かけたよ",
    "分担、いい感じに回すね",
    "仲間の報告待ち〜",
    "こっちは全体見とく",
  ],
  approval: [
    "ここだけ確認ほしい！",
    "進む前に一回見て〜",
    "この判断、相棒に渡すね",
    "確認できたら続けるよ",
  ],
  success: [
    "できた、はい勝ち！",
    "きれいに着地した〜",
    "よし、ひと区切り！",
    "ナイス連携だったね",
  ],
  error: [
    "原因見えたらもう前進",
    "責めずに切り分けよ",
    "ここから立て直せる",
    "大丈夫、事実から見よ",
  ],
});

const PROVIDER_LABELS = Object.freeze({
  codex: "Codex",
  claude: "Claude",
  grok: "Grok",
  unknown: "agent",
});

const ROLE_ACTIVITY_LINES = Object.freeze({
  implementer: "実装班が工房で作業中〜",
  researcher: "調査班が資料庫を探索中〜",
  reviewer: "review班が作戦卓で確認中〜",
  tester: "test班が信号門を確認中〜",
  unknown: "仲間がdockで稼働中〜",
});

function dateKey(nowMs) {
  const value = new Date(nowMs);
  return [
    value.getFullYear(),
    String(value.getMonth() + 1).padStart(2, "0"),
    String(value.getDate()).padStart(2, "0"),
  ].join("-");
}

function finiteCount(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.floor(number)) : 0;
}

function boundedText(value, limit) {
  return String(value ?? "")
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .slice(0, limit);
}

function defaultCounters() {
  return {
    sessions: 0,
    prompts: 0,
    turns: 0,
    read: 0,
    edit: 0,
    shell: 0,
    test: 0,
    testsPassed: 0,
    testsFailed: 0,
    delegations: 0,
    approvals: 0,
    recoveries: 0,
    maxSubagents: 0,
  };
}

function createProfile(nowMs = Date.now()) {
  return {
    schemaVersion: PROFILE_SCHEMA_VERSION,
    bondXp: 0,
    counters: defaultCounters(),
    badges: [],
    moments: [],
    seenEventIds: [],
    lastTestOutcome: "unknown",
    rhythm: { value: 0, lastAt: 0, lastCategory: null },
    daily: {
      date: dateKey(nowMs),
      automaticXp: 0,
    },
    theme: "curious",
    themeDate: dateKey(nowMs),
  };
}

function normalizeProfile(value, nowMs = Date.now()) {
  const profile = createProfile(nowMs);
  if (!value || typeof value !== "object" || Array.isArray(value))
    return profile;
  profile.bondXp = finiteCount(value.bondXp);
  const counters =
    value.counters && typeof value.counters === "object" ? value.counters : {};
  for (const key of Object.keys(profile.counters))
    profile.counters[key] = finiteCount(counters[key]);
  const badgeIds = new Set();
  profile.badges = Array.isArray(value.badges)
    ? value.badges
        .filter((badge) => {
          if (
            !badge ||
            badgeIds.has(badge.id) ||
            !BADGES.some((definition) => definition.id === badge.id)
          ) {
            return false;
          }
          badgeIds.add(badge.id);
          return true;
        })
        .map((badge) => ({
          id: badge.id,
          unlockedAt: boundedText(badge.unlockedAt, 64),
        }))
    : [];
  profile.moments = Array.isArray(value.moments)
    ? value.moments
        .filter((moment) => moment && typeof moment.text === "string")
        .slice(-MAX_MOMENTS)
        .map((moment) => ({
          id: boundedText(moment.id, 80),
          at: boundedText(moment.at, 64),
          kind: boundedText(moment.kind || "moment", 32),
          text: boundedText(moment.text, 100),
        }))
    : [];
  profile.seenEventIds = Array.isArray(value.seenEventIds)
    ? value.seenEventIds
        .map((id) => boundedText(id, 80))
        .filter(Boolean)
        .slice(-MAX_SEEN_EVENTS)
    : [];
  profile.lastTestOutcome = ["success", "failure", "unknown"].includes(
    value.lastTestOutcome,
  )
    ? value.lastTestOutcome
    : "unknown";
  if (value.rhythm && typeof value.rhythm === "object") {
    profile.rhythm.value = Math.min(9, finiteCount(value.rhythm.value));
    profile.rhythm.lastAt = finiteCount(value.rhythm.lastAt);
    profile.rhythm.lastCategory =
      typeof value.rhythm.lastCategory === "string"
        ? value.rhythm.lastCategory
        : null;
  }
  if (value.daily && typeof value.daily === "object") {
    profile.daily = {
      date: String(value.daily.date || dateKey(nowMs)),
      automaticXp: finiteCount(value.daily.automaticXp),
    };
  }
  const themeDate = boundedText(value.themeDate || dateKey(nowMs), 10);
  profile.theme =
    themeDate === dateKey(nowMs) && Object.hasOwn(THEMES, value.theme)
      ? value.theme
      : "curious";
  profile.themeDate = dateKey(nowMs);
  resetDaily(profile, nowMs);
  return profile;
}

function cloneProfile(profile, nowMs = Date.now()) {
  return normalizeProfile(JSON.parse(JSON.stringify(profile)), nowMs);
}

function resetDaily(profile, nowMs) {
  const today = dateKey(nowMs);
  if (profile.daily.date !== today) {
    profile.daily = {
      date: today,
      automaticXp: 0,
    };
  }
}

function awardXp(profile, amount, nowMs) {
  resetDaily(profile, nowMs);
  const available = Math.max(0, 12 - profile.daily.automaticXp);
  const awarded = Math.min(Math.max(0, amount), available);
  profile.daily.automaticXp += awarded;
  profile.bondXp += awarded;
  return awarded;
}

function levelForXp(xp) {
  let level = 1;
  for (let index = 0; index < LEVEL_THRESHOLDS.length; index += 1) {
    if (xp >= LEVEL_THRESHOLDS[index]) level = index + 1;
  }
  return level;
}

function titleForLevel(level) {
  if (level >= 17) return "伝説の開発部";
  if (level >= 13) return "最強開発部";
  if (level >= 9) return "名コンビ";
  if (level >= 5) return "相棒";
  if (level >= 3) return "作戦会議仲間";
  return "顔見知り";
}

function profileSummary(profile) {
  const level = levelForXp(profile.bondXp);
  return {
    level,
    title: titleForLevel(level),
    xp: profile.bondXp,
    nextLevelXp: LEVEL_THRESHOLDS[level] ?? null,
  };
}

function addMoment(profile, event, kind, text) {
  const id = `${event.id || Date.now()}:${kind}`;
  if (profile.moments.some((moment) => moment.id === id)) return;
  profile.moments.push({
    id,
    at: event.at || new Date().toISOString(),
    kind,
    text,
  });
  profile.moments = profile.moments.slice(-MAX_MOMENTS);
}

function updateRhythm(profile, category, atMs) {
  const elapsed = Math.max(0, atMs - profile.rhythm.lastAt);
  const decay = profile.rhythm.lastAt ? Math.floor(elapsed / 120_000) : 0;
  profile.rhythm.value = Math.max(0, profile.rhythm.value - decay);
  profile.rhythm.value = Math.min(
    9,
    profile.rhythm.value +
      (profile.rhythm.lastCategory && profile.rhythm.lastCategory !== category
        ? 2
        : 1),
  );
  profile.rhythm.lastAt = atMs;
  profile.rhythm.lastCategory = category;
}

function currentRhythm(profile, nowMs = Date.now()) {
  if (!profile.rhythm.lastAt) return 0;
  return Math.max(
    0,
    profile.rhythm.value -
      Math.floor((nowMs - profile.rhythm.lastAt) / 120_000),
  );
}

function shouldAwardCategory(count) {
  return [1, 5, 15, 30].includes(count);
}

function badgeSatisfied(id, profile) {
  const counters = profile.counters;
  if (id === "hello") return counters.turns >= 1;
  if (id === "detective") return counters.read >= 10;
  if (id === "builder") return counters.edit >= 10;
  if (id === "green-light") return counters.testsPassed >= 1;
  if (id === "conductor") return counters.delegations >= 3;
  if (id === "comeback") return counters.recoveries >= 1;
  if (id === "party") return counters.maxSubagents >= 3;
  if (id === "partner") return levelForXp(profile.bondXp) >= 5;
  return false;
}

function unlockBadges(profile, event) {
  const unlocked = new Set(profile.badges.map((badge) => badge.id));
  const newBadges = [];
  for (const definition of BADGES) {
    if (
      !unlocked.has(definition.id) &&
      badgeSatisfied(definition.id, profile)
    ) {
      const badge = {
        id: definition.id,
        unlockedAt: event.at || new Date().toISOString(),
      };
      profile.badges.push(badge);
      newBadges.push(definition);
      addMoment(
        profile,
        event,
        "badge",
        `ステッカー「${definition.title}」を見つけた`,
      );
    }
  }
  return newBadges;
}

function processEvents(inputProfile, events, nowMs = Date.now()) {
  const profile = cloneProfile(inputProfile, nowMs);
  const seen = new Set(profile.seenEventIds);
  const queued = new Set();
  const newBadges = [];
  const ordered = Array.isArray(events)
    ? [...events]
        .filter((event) => {
          if (!event || !event.id || seen.has(event.id) || queued.has(event.id))
            return false;
          queued.add(event.id);
          return true;
        })
        .sort((a, b) => String(a.at).localeCompare(String(b.at)))
    : [];

  for (const event of ordered) {
    const atMs = Number.isFinite(Date.parse(event.at))
      ? Date.parse(event.at)
      : nowMs;
    resetDaily(profile, atMs);
    seen.add(event.id);
    profile.counters.maxSubagents = Math.max(
      profile.counters.maxSubagents,
      finiteCount(event.activeSubagents),
    );

    if (event.event === "SessionStart") profile.counters.sessions += 1;
    if (event.event === "UserPromptSubmit") profile.counters.prompts += 1;
    if (event.event === "PermissionRequest") profile.counters.approvals += 1;
    if (["SubagentStart", "AgentJobStart"].includes(event.event)) {
      profile.counters.delegations += 1;
      awardXp(profile, 1, atMs);
      addMoment(profile, event, "delegation", "仲間がteamへ加わった");
    }
    if (["Stop", "AgentJobSucceeded"].includes(event.event)) {
      profile.counters.turns += 1;
      awardXp(profile, 2, atMs);
      addMoment(profile, event, "complete", "ひとつのturnを一緒に完了した");
    }

    if (
      event.event === "PreToolUse" &&
      ["read", "edit", "shell", "test"].includes(event.category)
    ) {
      profile.counters[event.category] += 1;
      updateRhythm(profile, event.category, atMs);
      if (shouldAwardCategory(profile.counters[event.category]))
        awardXp(profile, 1, atMs);
    }

    if (
      event.event === "PostToolUse" &&
      event.category === "test" &&
      event.outcome !== "unknown"
    ) {
      if (event.outcome === "success") {
        profile.counters.testsPassed += 1;
        awardXp(profile, 2, atMs);
        addMoment(profile, event, "test-pass", "testが青信号になった");
        if (profile.lastTestOutcome === "failure") {
          profile.counters.recoveries += 1;
          addMoment(profile, event, "recovery", "赤から青へ立て直した");
        }
      } else {
        profile.counters.testsFailed += 1;
        addMoment(profile, event, "test-fail", "testから手がかりを受け取った");
      }
      profile.lastTestOutcome = event.outcome;
    }

    newBadges.push(...unlockBadges(profile, event));
  }

  profile.seenEventIds = [...seen].slice(-MAX_SEEN_EVENTS);
  return { profile, changed: ordered.length > 0, newBadges };
}

function hashText(value) {
  let hash = 2166136261;
  for (const character of String(value)) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function pick(values, seed) {
  return values[hashText(seed) % values.length];
}

function lineForState(
  state,
  profile,
  seed = "workspace",
  nowMs = Date.now(),
) {
  const activeAgents = Array.isArray(state.activeAgents)
    ? state.activeAgents
    : [];
  if (activeAgents.length > 1) {
    return `agentが${activeAgents.length}人、並行で動いてるよ`;
  }
  if (activeAgents.length === 1) {
    const agent = activeAgents[0];
    const provider = PROVIDER_LABELS[agent.provider] || PROVIDER_LABELS.unknown;
    const activity =
      ROLE_ACTIVITY_LINES[agent.role] || ROLE_ACTIVITY_LINES.unknown;
    return `${provider}の${activity}`;
  }
  const hour = new Date(nowMs).getHours();
  if (state.status === "ready") {
    if (hour < 6) return "夜ふかし部だ。無理はなしね";
    if (hour < 11) return "おはよ、今日も一緒にいこ";
    if (hour >= 22) return "遅い時間だし、丁寧にね";
  }
  const latestTest = [...(state.recentEvents || [])]
    .reverse()
    .find(
      (event) =>
        event.event === "PostToolUse" &&
        event.category === "test" &&
        event.outcome !== "unknown",
    );
  if (state.status === "testing" && latestTest?.outcome === "failure")
    return "赤は失敗じゃなくて手がかり";
  if (state.status === "testing" && latestTest?.outcome === "success")
    return "青信号、きれいに通った！";

  const hourBucket = Math.floor(nowMs / 3_600_000);
  if (
    state.status === "idle" &&
    hashText(`${seed}:${hourBucket}:rare`) % 97 === 0
  ) {
    return "えっ、今ちょっとだけ踊ってたの見た？";
  }
  return pick(
    LINES[state.status] || LINES.idle,
    `${seed}:${state.status}:${state.revision}:${dateKey(nowMs)}`,
  );
}

function dailyTheme(profile) {
  return THEMES[profile.theme] || THEMES.curious;
}

function badgeDefinition(id) {
  return BADGES.find((badge) => badge.id === id);
}

module.exports = {
  BADGES,
  THEMES,
  badgeDefinition,
  createProfile,
  currentRhythm,
  dailyTheme,
  dateKey,
  levelForXp,
  lineForState,
  normalizeProfile,
  processEvents,
  profileSummary,
  titleForLevel,
};
