"use strict";

(() => {
  const vscode = acquireVsCodeApi();
  const world = document.getElementById("world");
  const map = document.getElementById("world-map");
  const mira = document.getElementById("mira");
  const sprite = document.getElementById("mira-sprite");
  const companions = document.getElementById("companions");
  const earnedPop = document.getElementById("earned-pop");
  const status = document.getElementById("status");
  const line = document.getElementById("line");
  const session = document.getElementById("session");
  const progress = document.getElementById("progress");
  const announcement = document.getElementById("announcement");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const ambientActions = [
    { x: 27, animation: "research" },
    { x: 34, animation: "idle" },
    { x: 41, animation: "thinking" },
    { x: 48, animation: "ready" },
    { x: 55, animation: "terminal" },
    { x: 63, animation: "testing" },
    { x: 72, animation: "idle" },
  ];

  let assets;
  let snapshot;
  let animationTimer;
  let movementTimer;
  let ambientTimer;
  let popTimer;
  let currentX = Number(vscode.getState()?.x) || 48;
  let ambientState;

  function nextAmbientRandom() {
    let value = ambientState >>> 0;
    value ^= value << 13;
    value ^= value >>> 17;
    value ^= value << 5;
    ambientState = value >>> 0 || 0x6d2b79f5;
    return ambientState / 0x1_0000_0000;
  }

  function clearTimer(name) {
    if (name === "animation" && animationTimer) clearInterval(animationTimer);
    if (name === "movement" && movementTimer) clearTimeout(movementTimer);
    if (name === "ambient" && ambientTimer) clearTimeout(ambientTimer);
    if (name === "pop" && popTimer) clearTimeout(popTimer);
    if (name === "animation") animationTimer = undefined;
    if (name === "movement") movementTimer = undefined;
    if (name === "ambient") ambientTimer = undefined;
    if (name === "pop") popTimer = undefined;
  }

  function motionEnabled() {
    return (
      snapshot?.motion !== "off" &&
      snapshot?.windowFocused !== false &&
      !document.hidden &&
      !reducedMotion.matches
    );
  }

  function animation(name) {
    return assets?.animations?.[name] || assets?.animations?.idle;
  }

  function playAnimation(name) {
    clearTimer("animation");
    const value = animation(name);
    if (!value?.frames?.length) return;
    let index = 0;
    sprite.src = value.frames[0];
    if (!motionEnabled() || value.frames.length < 2) return;
    const cap = snapshot.motion === "full" ? 6 : name === "idle" ? 0.75 : 3;
    const fps = Math.max(0.5, Math.min(cap, Number(value.fps) || 1));
    animationTimer = setInterval(() => {
      index = (index + 1) % value.frames.length;
      sprite.src = value.frames[index];
    }, Math.round(1000 / fps));
  }

  function renderedX() {
    const worldBounds = world.getBoundingClientRect();
    const miraBounds = mira.getBoundingClientRect();
    if (worldBounds.width <= 0) return currentX;
    return (
      ((miraBounds.left + miraBounds.width / 2 - worldBounds.left) /
        worldBounds.width) *
      100
    );
  }

  function moveTo(rawTarget, finalAnimation) {
    if (movementTimer) {
      currentX = renderedX();
      clearTimer("movement");
      world.style.setProperty("--travel-ms", "0ms");
      world.style.setProperty("--mira-x", String(currentX));
      void mira.offsetWidth;
    }
    const target = Math.max(8, Math.min(92, Number(rawTarget) || 48));
    const distance = Math.abs(target - currentX);
    if (!motionEnabled() || distance < 0.75) {
      currentX = target;
      world.style.setProperty("--travel-ms", "0ms");
      world.style.setProperty("--mira-x", String(currentX));
      vscode.setState({ x: currentX });
      playAnimation(finalAnimation);
      return;
    }

    const duration = Math.max(420, Math.min(2300, Math.round(distance * 42)));
    const walking = target > currentX ? "walkRight" : "walkLeft";
    world.style.setProperty("--travel-ms", `${duration}ms`);
    world.style.setProperty("--mira-x", String(currentX));
    void mira.offsetWidth;
    playAnimation(walking);
    world.style.setProperty("--mira-x", String(target));
    currentX = target;
    movementTimer = setTimeout(() => {
      movementTimer = undefined;
      vscode.setState({ x: currentX });
      playAnimation(finalAnimation);
      scheduleAmbient();
    }, duration + 30);
  }

  function renderCompanions() {
    companions.replaceChildren();
    const count = Math.min(4, Number(snapshot?.activeSubagents) || 0);
    for (let index = 0; index < count; index += 1) {
      const definition = assets.companions[index % assets.companions.length];
      const wrapper = document.createElement("span");
      wrapper.className = "companion";
      wrapper.style.left = `${77 + index * 4}%`;
      const image = document.createElement("img");
      image.alt = "";
      image.src =
        snapshot.status === "delegating" ? definition.active : definition.idle;
      wrapper.append(image);
      companions.append(wrapper);
    }
  }

  function renderDecorations() {
    const visible = new Set(snapshot?.decorations || []);
    for (const element of document.querySelectorAll("[data-decoration]")) {
      element.classList.toggle(
        "is-visible",
        visible.has(element.dataset.decoration),
      );
    }
  }

  function hidePop() {
    clearTimer("pop");
    earnedPop.hidden = true;
    earnedPop.textContent = "";
  }

  function renderPop() {
    hidePop();
    const pop = snapshot?.earnedPop;
    if (!pop) return;
    const remaining = Date.parse(pop.expiresAt) - Date.now();
    if (!Number.isFinite(remaining) || remaining <= 0) return;
    earnedPop.textContent = pop.label;
    earnedPop.dataset.popId = pop.id;
    earnedPop.setAttribute("aria-label", `${pop.label}。ミラの節目リアクション`);
    earnedPop.hidden = false;
    popTimer = setTimeout(hidePop, Math.min(remaining, 2_147_483_647));
  }

  function scheduleAmbient() {
    clearTimer("ambient");
    if (snapshot?.status !== "idle" || !motionEnabled()) return;
    const delay = 11_000 + Math.floor(nextAmbientRandom() * 10_000);
    ambientTimer = setTimeout(() => {
      ambientTimer = undefined;
      const candidates = ambientActions.filter(
        (action) => Math.abs(action.x - currentX) >= 5,
      );
      const action =
        candidates[Math.floor(nextAmbientRandom() * candidates.length)];
      moveTo(action.x, action.animation);
    }, delay);
  }

  function renderSnapshot(value) {
    if (!value || !assets) return;
    snapshot = value;
    world.dataset.status = snapshot.status;
    world.dataset.dayPhase = snapshot.dayPhase;
    if (ambientState === undefined) {
      ambientState = Number(snapshot.ambientSeed) >>> 0 || 0x6d2b79f5;
    }
    status.textContent = snapshot.connected
      ? snapshot.label
      : "Codex未接続";
    line.textContent = snapshot.line;
    const activity = snapshot.session || {};
    session.textContent = `調査${activity.research || 0} · 編集${activity.edit || 0} · test${activity.test || 0}`;
    const next = snapshot.progress.nextLevelXp ?? "MAX";
    progress.textContent = `Lv.${snapshot.progress.level} · ${snapshot.progress.xp}/${next} · ✦${snapshot.rhythm}`;
    renderDecorations();
    renderCompanions();
    renderPop();
    clearTimer("ambient");
    moveTo(snapshot.destination, snapshot.status);
    scheduleAmbient();
  }

  earnedPop.addEventListener("click", () => {
    const id = earnedPop.dataset.popId;
    if (!id || !snapshot?.earnedPop || id !== snapshot.earnedPop.id) return;
    hidePop();
    world.classList.add("is-celebrating");
    playAnimation("success");
    announcement.textContent = snapshot.earnedPop.line;
    vscode.postMessage({ type: "ackPop", id });
    setTimeout(() => world.classList.remove("is-celebrating"), 1100);
  });

  window.addEventListener("message", (event) => {
    const message = event.data;
    if (!message || typeof message !== "object") return;
    if (message.type === "hydrate") {
      assets = message.assets;
      map.src = assets.map;
      world.style.setProperty("--mira-x", String(currentX));
      renderSnapshot(message.snapshot);
    }
    if (message.type === "update") renderSnapshot(message.snapshot);
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      clearTimer("animation");
      clearTimer("ambient");
      return;
    }
    if (snapshot) renderSnapshot(snapshot);
  });

  reducedMotion.addEventListener?.("change", () => {
    if (snapshot) renderSnapshot(snapshot);
  });

  vscode.postMessage({ type: "ready" });
})();
