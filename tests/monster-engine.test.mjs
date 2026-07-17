import test from "node:test";
import assert from "node:assert/strict";
import MonsterEngine from "../public/static/js/monster-engine.js";

// ---------------------------------------------------------------------------
// levelProgressFromPoints / levelFromPoints
// ---------------------------------------------------------------------------

test("levelUpRequirement matches (3 + level*2) * 10", () => {
  assert.equal(MonsterEngine.levelUpRequirement(1), 50);
  assert.equal(MonsterEngine.levelUpRequirement(2), 70);
  assert.equal(MonsterEngine.levelUpRequirement(3), 90);
  assert.equal(MonsterEngine.levelUpRequirement(9), 210);
});

test("levelProgressFromPoints at 0 points is level 1 with 0 progress", () => {
  const progress = MonsterEngine.levelProgressFromPoints(0);
  assert.equal(progress.level, 1);
  assert.equal(progress.pointsIntoLevel, 0);
  assert.equal(progress.pointsNeededForNext, 50);
});

test("levelProgressFromPoints just below the level-2 boundary stays level 1", () => {
  const progress = MonsterEngine.levelProgressFromPoints(49);
  assert.equal(progress.level, 1);
  assert.equal(progress.pointsIntoLevel, 49);
});

test("levelProgressFromPoints exactly at the level-2 boundary (50) becomes level 2", () => {
  const progress = MonsterEngine.levelProgressFromPoints(50);
  assert.equal(progress.level, 2);
  assert.equal(progress.pointsIntoLevel, 0);
  assert.equal(progress.pointsNeededForNext, 70);
});

test("levelProgressFromPoints exactly at the level-3 boundary (120) becomes level 3", () => {
  // req(1)=50, req(2)=70 -> cumulative 120
  const progress = MonsterEngine.levelProgressFromPoints(120);
  assert.equal(progress.level, 3);
  assert.equal(progress.pointsIntoLevel, 0);
});

test("levelProgressFromPoints exactly at the level-6 boundary (450) becomes level 6", () => {
  // cumulative req(1..5) = 50+70+90+110+130 = 450
  assert.equal(MonsterEngine.levelFromPoints(450), 6);
  assert.equal(MonsterEngine.levelFromPoints(449), 5);
});

test("levelProgressFromPoints exactly at the level-10 boundary (1170) becomes level 10", () => {
  // cumulative req(1..9) = 1170
  assert.equal(MonsterEngine.levelFromPoints(1170), 10);
  assert.equal(MonsterEngine.levelFromPoints(1169), 9);
});

test("levelProgressFromPoints with partial progress into a level", () => {
  // level 3 requires 120 cumulative, level 4 requires 90 more (210 cumulative)
  const progress = MonsterEngine.levelProgressFromPoints(150);
  assert.equal(progress.level, 3);
  assert.equal(progress.pointsIntoLevel, 30);
  assert.equal(progress.pointsNeededForNext, 90);
});

// ---------------------------------------------------------------------------
// comboMultiplier
// ---------------------------------------------------------------------------

test("comboMultiplier breakpoints", () => {
  assert.equal(MonsterEngine.comboMultiplier(2), 1.0);
  assert.equal(MonsterEngine.comboMultiplier(3), 2.0);
  assert.equal(MonsterEngine.comboMultiplier(5), 2.0);
  assert.equal(MonsterEngine.comboMultiplier(6), 3.5);
  assert.equal(MonsterEngine.comboMultiplier(9), 3.5);
  assert.equal(MonsterEngine.comboMultiplier(10), 5.0);
  assert.equal(MonsterEngine.comboMultiplier(15), 5.0);
});

// ---------------------------------------------------------------------------
// evaluateTap
// ---------------------------------------------------------------------------

test("evaluateTap: first tap of a session is always valid with combo 1", () => {
  const now = 1_000_000;
  const result = MonsterEngine.evaluateTap({ lastTapAt: null, comboCount: 0, now });
  assert.equal(result.isValid, true);
  assert.equal(result.comboCount, 1);
  assert.equal(result.comboSecondsRemaining, 30);
  assert.equal(result.grantedPoints, 10); // floor(10 * 1.0)
});

test("evaluateTap: tap faster than 1.8s is invalid and does not change combo", () => {
  const lastTapAt = 1_000_000;
  const now = lastTapAt + 1000; // 1s later -> too fast
  const result = MonsterEngine.evaluateTap({ lastTapAt, comboCount: 4, now });
  assert.equal(result.isValid, false);
  assert.equal(result.comboCount, 4); // unchanged
  assert.equal(result.grantedPoints, 0);
  assert.equal(result.comboSecondsRemaining, 29); // max(0, 30 - 1)
});

test("evaluateTap: tap between 1.8s and 30s continues the combo", () => {
  const lastTapAt = 1_000_000;
  const now = lastTapAt + 5000; // 5s later -> valid continue
  const result = MonsterEngine.evaluateTap({ lastTapAt, comboCount: 2, now });
  assert.equal(result.isValid, true);
  assert.equal(result.comboCount, 3);
  assert.equal(result.comboSecondsRemaining, 30);
  assert.equal(result.grantedPoints, Math.floor(10 * MonsterEngine.comboMultiplier(3)));
});

test("evaluateTap: tap after more than 30s resets combo to 1", () => {
  const lastTapAt = 1_000_000;
  const now = lastTapAt + 31_000; // 31s later -> timeout reset
  const result = MonsterEngine.evaluateTap({ lastTapAt, comboCount: 9, now });
  assert.equal(result.isValid, true);
  assert.equal(result.comboCount, 1);
  assert.equal(result.comboSecondsRemaining, 30);
  assert.equal(result.grantedPoints, 10);
});

test("evaluateTap: exact boundary at 1.8s is valid (not too-fast)", () => {
  const lastTapAt = 1_000_000;
  const now = lastTapAt + 1800;
  const result = MonsterEngine.evaluateTap({ lastTapAt, comboCount: 1, now });
  assert.equal(result.isValid, true);
  assert.equal(result.comboCount, 2);
});

test("evaluateTap: exact boundary at 30s continues (not a reset)", () => {
  const lastTapAt = 1_000_000;
  const now = lastTapAt + 30_000;
  const result = MonsterEngine.evaluateTap({ lastTapAt, comboCount: 5, now });
  assert.equal(result.isValid, true);
  assert.equal(result.comboCount, 6);
});

test("evaluateTap accepts Date objects for lastTapAt/now", () => {
  const lastTapAt = new Date(2026, 0, 1, 12, 0, 0);
  const now = new Date(2026, 0, 1, 12, 0, 5); // 5s later
  const result = MonsterEngine.evaluateTap({ lastTapAt, comboCount: 0, now });
  assert.equal(result.isValid, true);
  assert.equal(result.comboCount, 1);
});

// ---------------------------------------------------------------------------
// applyFeeding / evolution chain
// ---------------------------------------------------------------------------

test("applyFeeding: all-apple chain evolves baby -> child(draup) -> mature(flare_drag) -> final(prometheus)", () => {
  let state = MonsterEngine.createInitialMonsterState();
  assert.equal(MonsterEngine.assetFamily(state), "baby/baby");

  // Cross level 3 (needs 120 cumulative points) purely on apples.
  let result = MonsterEngine.applyFeeding(state, "apple", 120);
  state = result.state;
  assert.equal(result.leveledUp, true);
  assert.equal(result.evolved, true);
  assert.equal(state.level, 3);
  assert.equal(state.evolutionStage, 1);
  assert.equal(state.baseFood, "apple");
  assert.equal(state.evolutionType, "draup");
  assert.equal(state.lastEvolutionLevel, 3);
  assert.ok(state.obtainedMonsters.includes("child/draup"));
  assert.equal(MonsterEngine.assetFamily(state), "child/draup");
  assert.equal(MonsterEngine.displayName(state), MonsterEngine.MONSTER_LABELS.draup);

  // Cross level 6 (needs 450 cumulative points total) still on apples.
  result = MonsterEngine.applyFeeding(state, "apple", 330);
  state = result.state;
  assert.equal(state.level, 6);
  assert.equal(state.evolutionStage, 2);
  assert.equal(state.evolutionType, "flare_drag");
  assert.equal(state.evolutionFoodFamily, "apple");
  assert.equal(state.lastEvolutionLevel, 6);
  assert.ok(state.obtainedMonsters.includes("mature/flare_drag"));
  assert.equal(MonsterEngine.assetFamily(state), "mature/flare_drag");

  // Cross level 10 (needs 1170 cumulative points total) still on apples.
  result = MonsterEngine.applyFeeding(state, "apple", 720);
  state = result.state;
  assert.equal(state.level, 10);
  assert.equal(state.evolutionStage, 3);
  assert.equal(state.evolutionType, "prometheus");
  assert.equal(state.lastEvolutionLevel, 10);
  assert.ok(state.obtainedMonsters.includes("final/prometheus"));
  assert.equal(MonsterEngine.assetFamily(state), "final/prometheus");
  assert.equal(MonsterEngine.displayName(state), MonsterEngine.MONSTER_LABELS.prometheus);
});

test("applyFeeding: representative sample of stage-1->2 and stage-2->3 routes", () => {
  // carrot -> carrot: bolt_garo, then bolt_garo final: raiden_volf
  let state = MonsterEngine.createInitialMonsterState();
  state = MonsterEngine.applyFeeding(state, "carrot", 120).state;
  assert.equal(state.evolutionType, "garoron");
  state = MonsterEngine.applyFeeding(state, "carrot", 330).state;
  assert.equal(state.evolutionType, "bolt_garo");
  state = MonsterEngine.applyFeeding(state, "carrot", 720).state;
  assert.equal(state.evolutionType, "raiden_volf");

  // fish -> broccoli: coral_guard, then coral_guard final: okeanos
  state = MonsterEngine.createInitialMonsterState();
  state = MonsterEngine.applyFeeding(state, "fish", 120).state;
  assert.equal(state.evolutionType, "fishul");
  state = MonsterEngine.applyFeeding(state, "broccoli", 330).state;
  assert.equal(state.evolutionType, "coral_guard");
  state = MonsterEngine.applyFeeding(state, "broccoli", 720).state;
  assert.equal(state.evolutionType, "okeanos");

  // broccoli -> apple: burn_golem, then burn_golem final: titan_magma
  state = MonsterEngine.createInitialMonsterState();
  state = MonsterEngine.applyFeeding(state, "broccoli", 120).state;
  assert.equal(state.evolutionType, "kororon");
  state = MonsterEngine.applyFeeding(state, "apple", 330).state;
  assert.equal(state.evolutionType, "burn_golem");
  state = MonsterEngine.applyFeeding(state, "apple", 720).state;
  assert.equal(state.evolutionType, "titan_magma");
});

test("applyFeeding: balance branch triggers FOOD_BALANCE evolution (child) when foods are fed evenly", () => {
  let state = MonsterEngine.createInitialMonsterState();

  // Feed one of each food type; none crosses level 3 until the last call.
  let result = MonsterEngine.applyFeeding(state, "apple", 0);
  state = result.state;
  assert.equal(state.evolutionStage, 0);

  result = MonsterEngine.applyFeeding(state, "carrot", 0);
  state = result.state;
  assert.equal(state.evolutionStage, 0);

  result = MonsterEngine.applyFeeding(state, "fish", 0);
  state = result.state;
  assert.equal(state.evolutionStage, 0);

  // Final feed of broccoli pushes points to exactly the level-3 boundary (120)
  // while stageFoodCounts sit at {apple:1, carrot:1, fish:1, broccoli:1}.
  result = MonsterEngine.applyFeeding(state, "broccoli", 120);
  state = result.state;

  assert.equal(result.evolved, true);
  assert.equal(state.level, 3);
  assert.equal(state.evolutionStage, 1);
  assert.equal(state.baseFood, "balance");
  assert.equal(state.evolutionType, MonsterEngine.CHILD_BY_FOOD.balance);
  assert.equal(state.evolutionType, "lumina");
  assert.ok(state.obtainedMonsters.includes("child/lumina"));
});

test("applyFeeding: balance branch also applies at the mature (stage 1->2) transition", () => {
  let state = MonsterEngine.createInitialMonsterState();
  // Get to child stage quickly and cleanly on straight apples first.
  state = MonsterEngine.applyFeeding(state, "apple", 120).state;
  assert.equal(state.evolutionStage, 1);
  assert.equal(state.baseFood, "apple");

  // Now feed one of each food type again during the child stage; last call
  // crosses level 6 (needs 330 more points -> cumulative 450) with an even
  // stageFoodCounts spread -> triggers "balance" for the second food family.
  state = MonsterEngine.applyFeeding(state, "apple", 0).state;
  state = MonsterEngine.applyFeeding(state, "carrot", 0).state;
  state = MonsterEngine.applyFeeding(state, "fish", 0).state;
  const result = MonsterEngine.applyFeeding(state, "broccoli", 330);
  state = result.state;

  assert.equal(state.level, 6);
  assert.equal(state.evolutionStage, 2);
  assert.equal(state.evolutionFoodFamily, "balance");
  assert.equal(state.evolutionType, MonsterEngine.MATURE_BY_FOODS["apple:balance"]);
  assert.equal(state.evolutionType, "shine_drag");
});

test("createInitialMonsterState returns the documented fresh baby shape", () => {
  const state = MonsterEngine.createInitialMonsterState();
  assert.deepEqual(state, {
    level: 1,
    growthPoints: 0,
    evolutionStage: 0,
    evolutionType: "baby",
    baseFood: null,
    evolutionFoodFamily: null,
    stageFoodCounts: { apple: 0, carrot: 0, fish: 0, broccoli: 0 },
    stageRecentFoods: [],
    lastEvolutionLevel: 0,
    obtainedMonsters: ["baby/baby"],
    lifetimeEatCount: 0,
    hallOfFame: [],
    lastGraduationPromptLevel: 0
  });
});

test("applyFeeding does not mutate the input state", () => {
  const state = MonsterEngine.createInitialMonsterState();
  const snapshot = JSON.stringify(state);
  MonsterEngine.applyFeeding(state, "apple", 120);
  assert.equal(JSON.stringify(state), snapshot);
});

// ---------------------------------------------------------------------------
// loadState / saveState (localStorage persistence, using a minimal in-memory shim)
// ---------------------------------------------------------------------------

test("loadState returns a fresh state when nothing is stored", () => {
  global.localStorage = {
    store: {},
    getItem(key) { return Object.prototype.hasOwnProperty.call(this.store, key) ? this.store[key] : null; },
    setItem(key, value) { this.store[key] = String(value); }
  };
  delete global.localStorage.store[MonsterEngine.STORAGE_KEY];

  const state = MonsterEngine.loadState();
  assert.deepEqual(state, MonsterEngine.createInitialMonsterState());
  delete global.localStorage;
});

test("saveState then loadState round-trips a state", () => {
  global.localStorage = {
    store: {},
    getItem(key) { return Object.prototype.hasOwnProperty.call(this.store, key) ? this.store[key] : null; },
    setItem(key, value) { this.store[key] = String(value); }
  };

  let state = MonsterEngine.createInitialMonsterState();
  state = MonsterEngine.applyFeeding(state, "apple", 120).state;

  MonsterEngine.saveState(state);
  const loaded = MonsterEngine.loadState();
  assert.deepEqual(loaded, state);

  delete global.localStorage;
});

test("loadState tolerates malformed JSON by returning a fresh state", () => {
  global.localStorage = {
    store: {},
    getItem() { return "{not valid json"; },
    setItem() {}
  };
  const state = MonsterEngine.loadState();
  assert.deepEqual(state, MonsterEngine.createInitialMonsterState());
  delete global.localStorage;
});

test("loadState normalizes a partial/legacy saved object without crashing", () => {
  global.localStorage = {
    store: {},
    getItem() { return JSON.stringify({ level: 4, growthPoints: 200 }); },
    setItem() {}
  };
  const state = MonsterEngine.loadState();
  assert.equal(state.level, 4);
  assert.equal(state.growthPoints, 200);
  assert.deepEqual(state.stageFoodCounts, { apple: 0, carrot: 0, fish: 0, broccoli: 0 });
  assert.deepEqual(state.obtainedMonsters, ["baby/baby"]);
  assert.equal(state.lifetimeEatCount, 0);
  assert.deepEqual(state.hallOfFame, []);
  assert.equal(state.lastGraduationPromptLevel, 0);
  delete global.localStorage;
});

// ---------------------------------------------------------------------------
// normalizeMonsterState backward compatibility for Phase 6 fields
// ---------------------------------------------------------------------------

test("normalizeMonsterState backfills lifetimeEatCount/hallOfFame/lastGraduationPromptLevel for legacy saves", () => {
  global.localStorage = {
    store: {},
    getItem() {
      // Legacy saved shape from before Phase 6 — none of the new fields exist.
      return JSON.stringify({
        level: 12,
        growthPoints: 5000,
        evolutionStage: 3,
        evolutionType: "prometheus",
        baseFood: "apple",
        evolutionFoodFamily: "apple",
        stageFoodCounts: { apple: 3, carrot: 0, fish: 0, broccoli: 0 },
        stageRecentFoods: ["apple"],
        lastEvolutionLevel: 10,
        obtainedMonsters: ["baby/baby", "child/draup", "mature/flare_drag", "final/prometheus"]
      });
    },
    setItem() {}
  };
  const state = MonsterEngine.loadState();
  assert.equal(state.level, 12);
  assert.equal(state.lifetimeEatCount, 0);
  assert.deepEqual(state.hallOfFame, []);
  assert.equal(state.lastGraduationPromptLevel, 0);
  delete global.localStorage;
});

test("normalizeMonsterState preserves existing Phase 6 fields when already present", () => {
  const raw = {
    level: 20,
    growthPoints: 9000,
    evolutionStage: 3,
    evolutionType: "prometheus",
    baseFood: "apple",
    evolutionFoodFamily: "apple",
    stageFoodCounts: { apple: 1, carrot: 0, fish: 0, broccoli: 0 },
    stageRecentFoods: ["apple"],
    lastEvolutionLevel: 10,
    obtainedMonsters: ["baby/baby"],
    lifetimeEatCount: 42,
    hallOfFame: [{ monsterKey: "final/prometheus", displayName: "プロメテウス", finalLevel: 15, sizeMeters: 5, eatCount: 30, graduatedAt: 123 }],
    lastGraduationPromptLevel: 15
  };
  global.localStorage = {
    store: {},
    getItem() { return JSON.stringify(raw); },
    setItem() {}
  };
  const state = MonsterEngine.loadState();
  assert.equal(state.lifetimeEatCount, 42);
  assert.deepEqual(state.hallOfFame, raw.hallOfFame);
  assert.equal(state.lastGraduationPromptLevel, 15);
  delete global.localStorage;
});

// ---------------------------------------------------------------------------
// sizeForLevel / formatSize / cssScaleForLevel
// ---------------------------------------------------------------------------

test("sizeForLevel is null/undefined-ish below Lv10", () => {
  assert.equal(MonsterEngine.sizeForLevel(1), null);
  assert.equal(MonsterEngine.sizeForLevel(9), null);
});

test("sizeForLevel follows 2.0 * 1.2^(level-10)", () => {
  assert.equal(MonsterEngine.sizeForLevel(10), 2.0);
  assert.ok(Math.abs(MonsterEngine.sizeForLevel(15) - 4.97664) < 1e-3);
  assert.ok(Math.abs(MonsterEngine.sizeForLevel(20) - 12.3835) < 1e-2);
});

test("formatSize renders meters under 1000, kilometers at/above 1000", () => {
  assert.equal(MonsterEngine.formatSize(5), "5.0m");
  assert.equal(MonsterEngine.formatSize(999), "999.0m");
  assert.equal(MonsterEngine.formatSize(1000), "1.0km");
  assert.equal(MonsterEngine.formatSize(2900), "2.9km");
});

test("cssScaleForLevel is 1 at/below Lv10 and grows with a cap", () => {
  assert.equal(MonsterEngine.cssScaleForLevel(1), 1);
  assert.equal(MonsterEngine.cssScaleForLevel(10), 1);
  assert.ok(MonsterEngine.cssScaleForLevel(11) > 1);
  assert.equal(MonsterEngine.cssScaleForLevel(500), MonsterEngine.SCALE_CAP);
});

// ---------------------------------------------------------------------------
// canGraduate / shouldShowGraduationPrompt / markGraduationPrompted
// ---------------------------------------------------------------------------

test("canGraduate requires final evolution stage and Lv10+", () => {
  const state = MonsterEngine.createInitialMonsterState();
  assert.equal(MonsterEngine.canGraduate(state), false);

  const notFinal = Object.assign({}, state, { evolutionStage: 2, level: 12 });
  assert.equal(MonsterEngine.canGraduate(notFinal), false);

  const tooLow = Object.assign({}, state, { evolutionStage: 3, level: 9 });
  assert.equal(MonsterEngine.canGraduate(tooLow), false);

  const ready = Object.assign({}, state, { evolutionStage: 3, level: 10 });
  assert.equal(MonsterEngine.canGraduate(ready), true);
});

test("shouldShowGraduationPrompt: true on first reaching Lv10", () => {
  const state = Object.assign(MonsterEngine.createInitialMonsterState(), { evolutionStage: 3, level: 10 });
  assert.equal(MonsterEngine.shouldShowGraduationPrompt(state), true);
});

test("shouldShowGraduationPrompt: false at Lv14 (no new 5-level threshold reached)", () => {
  const state = Object.assign(MonsterEngine.createInitialMonsterState(), {
    evolutionStage: 3, level: 14, lastGraduationPromptLevel: 10
  });
  assert.equal(MonsterEngine.shouldShowGraduationPrompt(state), false);
});

test("shouldShowGraduationPrompt: true at Lv15 after Lv10 was already prompted", () => {
  const state = Object.assign(MonsterEngine.createInitialMonsterState(), {
    evolutionStage: 3, level: 15, lastGraduationPromptLevel: 10
  });
  assert.equal(MonsterEngine.shouldShowGraduationPrompt(state), true);
});

test("markGraduationPrompted records the threshold and shouldShowGraduationPrompt becomes false", () => {
  let state = Object.assign(MonsterEngine.createInitialMonsterState(), { evolutionStage: 3, level: 15, lastGraduationPromptLevel: 10 });
  assert.equal(MonsterEngine.shouldShowGraduationPrompt(state), true);
  state = MonsterEngine.markGraduationPrompted(state);
  assert.equal(state.lastGraduationPromptLevel, 15);
  assert.equal(MonsterEngine.shouldShowGraduationPrompt(state), false);
});

test("shouldShowGraduationPrompt: true again at Lv20 after Lv15 was prompted", () => {
  let state = Object.assign(MonsterEngine.createInitialMonsterState(), { evolutionStage: 3, level: 15, lastGraduationPromptLevel: 10 });
  state = MonsterEngine.markGraduationPrompted(state);
  assert.equal(MonsterEngine.shouldShowGraduationPrompt(state), false);

  const atTwenty = Object.assign({}, state, { level: 20 });
  assert.equal(MonsterEngine.shouldShowGraduationPrompt(atTwenty), true);
});

// ---------------------------------------------------------------------------
// graduate
// ---------------------------------------------------------------------------

test("graduate records a hall-of-fame entry and resets to a fresh baby", () => {
  let state = MonsterEngine.createInitialMonsterState();
  state = MonsterEngine.applyFeeding(state, "apple", 120).state; // -> child
  state = MonsterEngine.applyFeeding(state, "apple", 330).state; // -> mature
  state = MonsterEngine.applyFeeding(state, "apple", 720).state; // -> final, Lv10
  assert.equal(state.level, 10);
  assert.equal(MonsterEngine.canGraduate(state), true);

  const before = state.lifetimeEatCount;
  const result = MonsterEngine.graduate(state, 1_700_000_000_000);

  // Hall of fame record content
  assert.equal(result.hallOfFame.length, 1);
  const record = result.hallOfFame[0];
  assert.equal(record.monsterKey, "final/prometheus");
  assert.equal(record.displayName, MonsterEngine.MONSTER_LABELS.prometheus);
  assert.equal(record.finalLevel, 10);
  assert.equal(record.sizeMeters, MonsterEngine.sizeForLevel(10));
  assert.equal(record.eatCount, before);
  assert.equal(record.graduatedAt, 1_700_000_000_000);

  // obtainedMonsters carried over from the graduated individual
  assert.deepEqual(result.obtainedMonsters, state.obtainedMonsters);

  // New generation resets to a fresh Lv1 baby
  assert.equal(result.level, 1);
  assert.equal(result.growthPoints, 0);
  assert.equal(result.evolutionStage, 0);
  assert.equal(result.evolutionType, "baby");
  assert.equal(result.lifetimeEatCount, 0);
  assert.equal(result.lastGraduationPromptLevel, 0);
});

test("graduate accepts a Date for `now` just like other engine date params", () => {
  let state = MonsterEngine.createInitialMonsterState();
  state = MonsterEngine.applyFeeding(state, "apple", 120).state;
  state = MonsterEngine.applyFeeding(state, "apple", 330).state;
  state = MonsterEngine.applyFeeding(state, "apple", 720).state;
  const now = new Date(2026, 0, 1, 12, 0, 0);
  const result = MonsterEngine.graduate(state, now);
  assert.equal(result.hallOfFame[0].graduatedAt, now.getTime());
});

test("graduate accumulates multiple generations into hallOfFame across repeated graduations", () => {
  let state = MonsterEngine.createInitialMonsterState();
  state = MonsterEngine.applyFeeding(state, "apple", 120).state;
  state = MonsterEngine.applyFeeding(state, "apple", 330).state;
  state = MonsterEngine.applyFeeding(state, "apple", 720).state;
  state = MonsterEngine.graduate(state, 1000);

  state = MonsterEngine.applyFeeding(state, "carrot", 120).state;
  state = MonsterEngine.applyFeeding(state, "carrot", 330).state;
  state = MonsterEngine.applyFeeding(state, "carrot", 720).state;
  state = MonsterEngine.graduate(state, 2000);

  assert.equal(state.hallOfFame.length, 2);
  assert.equal(state.hallOfFame[0].monsterKey, "final/prometheus");
  assert.equal(state.hallOfFame[1].monsterKey, "final/raiden_volf");
});
