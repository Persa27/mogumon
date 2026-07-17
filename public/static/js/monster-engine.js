/*
 * MonsterEngine — dependency-free port of the original Python server game logic
 * (formerly src/app.py) so the game can run entirely client-side against
 * localStorage on a static (Vercel) deployment.
 *
 * Works both as a plain <script> tag (attaches to window.MonsterEngine) and as
 * a CommonJS module (module.exports = MonsterEngine) for Node-based tests.
 *
 * Date/time convention: anywhere a "now" or "lastTapAt" value is accepted, you
 * may pass either a JS Date object or an epoch-millisecond number — both are
 * normalized to epoch-ms internally.
 */
(function (root) {
  "use strict";

  var FOOD_TYPES = ["apple", "carrot", "fish", "broccoli"];
  var FOOD_BALANCE = "balance";
  var COMBO_CONTINUE_SECONDS = 30;
  var COMBO_TOO_FAST_SECONDS = 1.8;
  var BASE_EVOLUTION_LEVEL = 3;
  var FIRST_EVOLUTION_LEVEL = 6;
  var SECOND_EVOLUTION_LEVEL = 10;
  var FOOD_PRIORITY = ["apple", "carrot", "fish", "broccoli"];

  // ---- Phase 6: Lv10+ "post-graduation" growth (see docs/phase6/post-lv10-design-v1.md) ----
  var GRADUATION_MIN_LEVEL = 10;
  var GRADUATION_PROMPT_INTERVAL = 5;
  var SCALE_CAP = 50;

  var CHILD_BY_FOOD = {
    apple: "draup",
    carrot: "garoron",
    fish: "fishul",
    broccoli: "kororon",
    balance: "lumina"
  };

  // Keyed by `${baseFood}:${secondFood}` since JS object keys can't be tuples.
  var MATURE_BY_FOODS = {
    "apple:apple": "flare_drag", "apple:carrot": "bolt_drag", "apple:fish": "frost_drag",
    "apple:broccoli": "magma_rock", "apple:balance": "shine_drag",
    "carrot:apple": "burst_garo", "carrot:carrot": "bolt_garo", "carrot:fish": "aqua_garo",
    "carrot:broccoli": "terra_garo", "carrot:balance": "holy_garo",
    "fish:apple": "steam_fin", "fish:carrot": "plasma_fin", "fish:fish": "glacies",
    "fish:broccoli": "coral_guard", "fish:balance": "angel_fin",
    "broccoli:apple": "burn_golem", "broccoli:carrot": "pulse_rock", "broccoli:fish": "splash_terra",
    "broccoli:broccoli": "forest_guard", "broccoli:balance": "rune_golem",
    "balance:apple": "flare_eterna", "balance:carrot": "bolt_eterna", "balance:fish": "crystal_eterna",
    "balance:broccoli": "leaf_eterna", "balance:balance": "eterna"
  };

  var FINAL_BY_FOODS = {
    "apple:apple": "prometheus", "apple:carrot": "indra_drag", "apple:fish": "agniva",
    "apple:broccoli": "gaia_drag", "apple:balance": "sol_dragnir",
    "carrot:apple": "ifrit_leo", "carrot:carrot": "raiden_volf", "carrot:fish": "kelpie_volt",
    "carrot:broccoli": "yggdra_beast", "carrot:balance": "sirius_star",
    "fish:apple": "levia_burn", "fish:carrot": "thunder_kaiser", "fish:fish": "poseidram",
    "fish:broccoli": "okeanos", "fish:balance": "seraph_aqua",
    "broccoli:apple": "titan_magma", "broccoli:carrot": "thor_terra", "broccoli:fish": "neptune_rock",
    "broccoli:broccoli": "yggdrasil", "broccoli:balance": "chronos_terra",
    "balance:apple": "phoenix", "balance:carrot": "astral_rai", "balance:fish": "diamond_halo",
    "balance:broccoli": "eden_spirit", "balance:balance": "zeus_omega"
  };

  var MONSTER_LABELS = {
    baby: "ベビー",
    draup: "ドラップ", garoron: "ガロロン", fishul: "フィシュル", kororon: "コロロン", lumina: "ルミナ",
    flare_drag: "フレアドラグ", bolt_drag: "ボルトドラグ", frost_drag: "フロストドラグ",
    magma_rock: "マグマロック", shine_drag: "シャインドラグ", burst_garo: "バーストガロ",
    bolt_garo: "ボルトガロ", aqua_garo: "アクアガロ", terra_garo: "テラガロ", holy_garo: "ホーリーガロ",
    steam_fin: "スチームフィン", plasma_fin: "プラズマフィン", glacies: "グラキエス",
    coral_guard: "コーラルガルド", angel_fin: "エンゼルフィン", burn_golem: "バーンゴレム",
    pulse_rock: "パルスロック", splash_terra: "スプラッシュテラ", forest_guard: "フォレストガルド",
    rune_golem: "ルーンゴーレム", flare_eterna: "フレアエテルナ", bolt_eterna: "ボルトエテルナ",
    crystal_eterna: "クリスタルエテルナ", leaf_eterna: "リーフエテルナ", eterna: "エテルナ",
    prometheus: "プロメテウス", indra_drag: "インドラ・ドラグ", agniva: "アグニヴァ",
    gaia_drag: "ガイアドラグ", sol_dragnir: "ソル・ドラグニル", ifrit_leo: "イフリート・レオ",
    raiden_volf: "ライデンヴォルフ", kelpie_volt: "ケルピーヴォルト", yggdra_beast: "ユグドラビースト",
    sirius_star: "シリウス・スター", levia_burn: "レヴィア・バーン", thunder_kaiser: "サンダーカイザー",
    poseidram: "ポセイドラム", okeanos: "オケアノス", seraph_aqua: "セラフィ・アクア",
    titan_magma: "タイタン・マグマ", thor_terra: "トール・テラ", neptune_rock: "ネプチュン・ロック",
    yggdrasil: "ユグドラシル", chronos_terra: "クロノス・テラ", phoenix: "フェニックス",
    astral_rai: "アストラル・ライ", diamond_halo: "ダイアモンド・ハロー", eden_spirit: "エデン・スピリット",
    zeus_omega: "ゼウス・オメガ"
  };

  var STORAGE_KEY = "mgu_monster_state_v1";

  function levelUpRequirement(level) {
    return (3 + level * 2) * 10;
  }

  function levelProgressFromPoints(points) {
    var level = 1;
    var remaining = points;
    while (remaining >= levelUpRequirement(level)) {
      remaining -= levelUpRequirement(level);
      level += 1;
    }
    return {
      level: level,
      pointsIntoLevel: remaining,
      pointsNeededForNext: levelUpRequirement(level)
    };
  }

  function levelFromPoints(points) {
    return levelProgressFromPoints(points).level;
  }

  function comboMultiplier(combo) {
    if (combo >= 10) return 5.0;
    if (combo >= 6) return 3.5;
    if (combo >= 3) return 2.0;
    return 1.0;
  }

  function foodRatio(counts, foodType) {
    var total = 0;
    var keys = Object.keys(counts);
    for (var i = 0; i < keys.length; i++) {
      total += counts[keys[i]];
    }
    if (total <= 0) return 0.0;
    var value = Object.prototype.hasOwnProperty.call(counts, foodType) ? counts[foodType] : 0;
    return value / total;
  }

  function countOccurrences(arr, value) {
    var count = 0;
    for (var i = 0; i < arr.length; i++) {
      if (arr[i] === value) count++;
    }
    return count;
  }

  function dominantFood(counts, recentFoods) {
    var foods = Object.keys(counts);
    var highest = 0;
    for (var i = 0; i < foods.length; i++) {
      if (counts[foods[i]] > highest) highest = counts[foods[i]];
    }
    var tied = [];
    for (var j = 0; j < foods.length; j++) {
      if (counts[foods[j]] === highest) tied.push(foods[j]);
    }
    if (tied.length === 0) return FOOD_PRIORITY[0];
    if (tied.length === 1) return tied[0];

    var recentCounts = {};
    var recentHighest = 0;
    for (var k = 0; k < tied.length; k++) {
      var c = countOccurrences(recentFoods, tied[k]);
      recentCounts[tied[k]] = c;
      if (c > recentHighest) recentHighest = c;
    }
    var recentTied = [];
    for (var m = 0; m < tied.length; m++) {
      if (recentCounts[tied[m]] === recentHighest) recentTied.push(tied[m]);
    }
    for (var p = 0; p < FOOD_PRIORITY.length; p++) {
      if (recentTied.indexOf(FOOD_PRIORITY[p]) !== -1) return FOOD_PRIORITY[p];
    }
    return recentTied[0];
  }

  function foodsOverThreshold(counts, threshold) {
    var total = 0;
    for (var i = 0; i < FOOD_TYPES.length; i++) {
      if (foodRatio(counts, FOOD_TYPES[i]) >= threshold) total++;
    }
    return total;
  }

  function dominantFoodWithBalance(counts, recentFoods) {
    var mainFood = dominantFood(counts, recentFoods);
    if (foodRatio(counts, mainFood) < 0.45 && foodsOverThreshold(counts, 0.15) >= 3) {
      return FOOD_BALANCE;
    }
    return mainFood;
  }

  function freshFoodCounts() {
    var counts = {};
    for (var i = 0; i < FOOD_TYPES.length; i++) counts[FOOD_TYPES[i]] = 0;
    return counts;
  }

  function recordFoodChoice(monsterState, foodType) {
    monsterState.stageFoodCounts[foodType] = (monsterState.stageFoodCounts[foodType] || 0) + 1;
    monsterState.stageRecentFoods.push(foodType);
    if (monsterState.stageRecentFoods.length > 3) {
      monsterState.stageRecentFoods = monsterState.stageRecentFoods.slice(-3);
    }
  }

  function resetStageFoodHistory(monsterState) {
    monsterState.stageFoodCounts = freshFoodCounts();
    monsterState.stageRecentFoods = [];
  }

  function applyEvolutionIfNeeded(monsterState) {
    var evolved = false;

    if (monsterState.evolutionStage === 0 && monsterState.level >= BASE_EVOLUTION_LEVEL &&
        monsterState.lastEvolutionLevel < BASE_EVOLUTION_LEVEL) {
      var childFood = dominantFoodWithBalance(monsterState.stageFoodCounts, monsterState.stageRecentFoods);
      monsterState.baseFood = childFood;
      monsterState.evolutionType = CHILD_BY_FOOD[childFood];
      monsterState.evolutionStage = 1;
      monsterState.lastEvolutionLevel = BASE_EVOLUTION_LEVEL;
      resetStageFoodHistory(monsterState);
      var childKey = "child/" + monsterState.evolutionType;
      if (monsterState.obtainedMonsters.indexOf(childKey) === -1) {
        monsterState.obtainedMonsters.push(childKey);
      }
      evolved = true;
    }

    if (monsterState.evolutionStage === 1 && monsterState.level >= FIRST_EVOLUTION_LEVEL &&
        monsterState.lastEvolutionLevel < FIRST_EVOLUTION_LEVEL) {
      var secondFood = dominantFoodWithBalance(monsterState.stageFoodCounts, monsterState.stageRecentFoods);
      var matureKey = monsterState.baseFood + ":" + secondFood;
      var matureName = Object.prototype.hasOwnProperty.call(MATURE_BY_FOODS, matureKey)
        ? MATURE_BY_FOODS[matureKey]
        : "flare_drag";
      monsterState.evolutionFoodFamily = secondFood;
      monsterState.evolutionType = matureName;
      monsterState.evolutionStage = 2;
      monsterState.lastEvolutionLevel = FIRST_EVOLUTION_LEVEL;
      resetStageFoodHistory(monsterState);
      var matureObtainedKey = "mature/" + matureName;
      if (monsterState.obtainedMonsters.indexOf(matureObtainedKey) === -1) {
        monsterState.obtainedMonsters.push(matureObtainedKey);
      }
      evolved = true;
    }

    if (monsterState.evolutionStage === 2 && monsterState.level >= SECOND_EVOLUTION_LEVEL &&
        monsterState.lastEvolutionLevel < SECOND_EVOLUTION_LEVEL) {
      var finalKey = monsterState.baseFood + ":" + monsterState.evolutionFoodFamily;
      var finalName = Object.prototype.hasOwnProperty.call(FINAL_BY_FOODS, finalKey)
        ? FINAL_BY_FOODS[finalKey]
        : "prometheus";
      monsterState.evolutionType = finalName;
      monsterState.evolutionStage = 3;
      monsterState.lastEvolutionLevel = SECOND_EVOLUTION_LEVEL;
      resetStageFoodHistory(monsterState);
      var finalObtainedKey = "final/" + finalName;
      if (monsterState.obtainedMonsters.indexOf(finalObtainedKey) === -1) {
        monsterState.obtainedMonsters.push(finalObtainedKey);
      }
      evolved = true;
    }

    return evolved;
  }

  function toMillis(value) {
    if (value === null || value === undefined) return null;
    if (value instanceof Date) return value.getTime();
    return value;
  }

  // ---- Phase 6: Lv10+ sizing / graduation helpers ----

  function sizeForLevel(level) {
    if (typeof level !== "number" || level < GRADUATION_MIN_LEVEL) return null;
    return 2.0 * Math.pow(1.2, level - GRADUATION_MIN_LEVEL);
  }

  function formatSize(meters) {
    if (typeof meters !== "number" || isNaN(meters)) return "";
    if (meters >= 1000) {
      return (meters / 1000).toFixed(1) + "km";
    }
    return meters.toFixed(1) + "m";
  }

  function cssScaleForLevel(level) {
    if (typeof level !== "number" || level <= GRADUATION_MIN_LEVEL) return 1;
    return Math.min(SCALE_CAP, Math.pow(1.15, level - GRADUATION_MIN_LEVEL));
  }

  function canGraduate(state) {
    return !!state && state.evolutionStage === 3 && state.level >= GRADUATION_MIN_LEVEL;
  }

  // Highest "prompt-worthy" level threshold reached so far: 10, then every
  // GRADUATION_PROMPT_INTERVAL levels after that (15, 20, 25, ...).
  function graduationThresholdForLevel(level) {
    if (typeof level !== "number" || level < GRADUATION_MIN_LEVEL) return null;
    var steps = Math.floor((level - GRADUATION_MIN_LEVEL) / GRADUATION_PROMPT_INTERVAL);
    return GRADUATION_MIN_LEVEL + steps * GRADUATION_PROMPT_INTERVAL;
  }

  function shouldShowGraduationPrompt(state) {
    if (!canGraduate(state)) return false;
    var threshold = graduationThresholdForLevel(state.level);
    if (threshold === null) return false;
    var lastPrompted = typeof state.lastGraduationPromptLevel === "number" ? state.lastGraduationPromptLevel : 0;
    return threshold > lastPrompted;
  }

  function markGraduationPrompted(state) {
    var next = cloneState(state);
    var threshold = graduationThresholdForLevel(state.level);
    if (threshold !== null) {
      next.lastGraduationPromptLevel = threshold;
    }
    return next;
  }

  function graduate(state, now) {
    var record = {
      monsterKey: assetFamily(state),
      displayName: displayName(state),
      finalLevel: state.level,
      sizeMeters: sizeForLevel(state.level),
      eatCount: typeof state.lifetimeEatCount === "number" ? state.lifetimeEatCount : 0,
      graduatedAt: toMillis(now === undefined ? Date.now() : now)
    };

    var next = createInitialMonsterState();
    next.obtainedMonsters = state.obtainedMonsters ? state.obtainedMonsters.slice() : next.obtainedMonsters;
    next.hallOfFame = (Array.isArray(state.hallOfFame) ? state.hallOfFame.slice() : []).concat([record]);

    return next;
  }

  function evaluateTap(options) {
    var lastTapAt = toMillis(options.lastTapAt);
    var previousCombo = options.comboCount || 0;
    var now = toMillis(options.now);

    if (lastTapAt === null) {
      return {
        isValid: true,
        comboCount: 1,
        comboSecondsRemaining: COMBO_CONTINUE_SECONDS,
        grantedPoints: Math.floor(10 * comboMultiplier(1))
      };
    }

    var diffSeconds = (now - lastTapAt) / 1000;

    if (diffSeconds < COMBO_TOO_FAST_SECONDS) {
      return {
        isValid: false,
        comboCount: previousCombo,
        comboSecondsRemaining: Math.max(0, COMBO_CONTINUE_SECONDS - diffSeconds),
        grantedPoints: 0
      };
    }

    if (diffSeconds <= COMBO_CONTINUE_SECONDS) {
      var newCombo = previousCombo + 1;
      return {
        isValid: true,
        comboCount: newCombo,
        comboSecondsRemaining: COMBO_CONTINUE_SECONDS,
        grantedPoints: Math.floor(10 * comboMultiplier(newCombo))
      };
    }

    return {
      isValid: true,
      comboCount: 1,
      comboSecondsRemaining: COMBO_CONTINUE_SECONDS,
      grantedPoints: Math.floor(10 * comboMultiplier(1))
    };
  }

  function createInitialMonsterState() {
    return {
      level: 1,
      growthPoints: 0,
      evolutionStage: 0,
      evolutionType: "baby",
      baseFood: null,
      evolutionFoodFamily: null,
      stageFoodCounts: freshFoodCounts(),
      stageRecentFoods: [],
      lastEvolutionLevel: 0,
      obtainedMonsters: ["baby/baby"],
      lifetimeEatCount: 0,
      hallOfFame: [],
      lastGraduationPromptLevel: 0
    };
  }

  function cloneState(state) {
    return {
      level: state.level,
      growthPoints: state.growthPoints,
      evolutionStage: state.evolutionStage,
      evolutionType: state.evolutionType,
      baseFood: state.baseFood,
      evolutionFoodFamily: state.evolutionFoodFamily,
      stageFoodCounts: {
        apple: state.stageFoodCounts.apple || 0,
        carrot: state.stageFoodCounts.carrot || 0,
        fish: state.stageFoodCounts.fish || 0,
        broccoli: state.stageFoodCounts.broccoli || 0
      },
      stageRecentFoods: state.stageRecentFoods.slice(),
      lastEvolutionLevel: state.lastEvolutionLevel,
      obtainedMonsters: state.obtainedMonsters.slice(),
      lifetimeEatCount: typeof state.lifetimeEatCount === "number" ? state.lifetimeEatCount : 0,
      hallOfFame: Array.isArray(state.hallOfFame) ? state.hallOfFame.slice() : [],
      lastGraduationPromptLevel: typeof state.lastGraduationPromptLevel === "number" ? state.lastGraduationPromptLevel : 0
    };
  }

  function applyFeeding(state, foodType, grantedPoints) {
    var next = cloneState(state);
    var previousLevel = next.level;

    next.growthPoints += grantedPoints;
    next.level = levelFromPoints(next.growthPoints);
    next.lifetimeEatCount = (typeof next.lifetimeEatCount === "number" ? next.lifetimeEatCount : 0) + 1;

    recordFoodChoice(next, foodType);

    var evolved = applyEvolutionIfNeeded(next);

    return {
      state: next,
      leveledUp: next.level > previousLevel,
      evolved: evolved
    };
  }

  function assetFamily(state) {
    if (state.evolutionStage === 0) return "baby/baby";
    var stagePrefix = state.evolutionStage === 1 ? "child" : (state.evolutionStage === 2 ? "mature" : "final");
    return stagePrefix + "/" + state.evolutionType;
  }

  function displayName(state) {
    var family = assetFamily(state);
    var parts = family.split("/");
    var baseName = parts[parts.length - 1];
    return Object.prototype.hasOwnProperty.call(MONSTER_LABELS, baseName) ? MONSTER_LABELS[baseName] : baseName;
  }

  function normalizeMonsterState(raw) {
    var initial = createInitialMonsterState();
    if (!raw || typeof raw !== "object") return initial;

    var normalized = {
      level: typeof raw.level === "number" ? raw.level : initial.level,
      growthPoints: typeof raw.growthPoints === "number" ? raw.growthPoints : initial.growthPoints,
      evolutionStage: typeof raw.evolutionStage === "number" ? raw.evolutionStage : initial.evolutionStage,
      evolutionType: typeof raw.evolutionType === "string" ? raw.evolutionType : initial.evolutionType,
      baseFood: raw.baseFood !== undefined ? raw.baseFood : initial.baseFood,
      evolutionFoodFamily: raw.evolutionFoodFamily !== undefined ? raw.evolutionFoodFamily : initial.evolutionFoodFamily,
      stageFoodCounts: freshFoodCounts(),
      stageRecentFoods: Array.isArray(raw.stageRecentFoods) ? raw.stageRecentFoods.slice(-3) : initial.stageRecentFoods,
      lastEvolutionLevel: typeof raw.lastEvolutionLevel === "number" ? raw.lastEvolutionLevel : initial.lastEvolutionLevel,
      obtainedMonsters: Array.isArray(raw.obtainedMonsters) && raw.obtainedMonsters.length > 0
        ? raw.obtainedMonsters.slice()
        : initial.obtainedMonsters.slice(),
      lifetimeEatCount: typeof raw.lifetimeEatCount === "number" ? raw.lifetimeEatCount : initial.lifetimeEatCount,
      hallOfFame: Array.isArray(raw.hallOfFame) ? raw.hallOfFame.slice() : initial.hallOfFame.slice(),
      lastGraduationPromptLevel: typeof raw.lastGraduationPromptLevel === "number"
        ? raw.lastGraduationPromptLevel
        : initial.lastGraduationPromptLevel
    };

    if (raw.stageFoodCounts && typeof raw.stageFoodCounts === "object") {
      for (var i = 0; i < FOOD_TYPES.length; i++) {
        var f = FOOD_TYPES[i];
        normalized.stageFoodCounts[f] = typeof raw.stageFoodCounts[f] === "number" ? raw.stageFoodCounts[f] : 0;
      }
    }

    return normalized;
  }

  function loadState() {
    try {
      var raw = root.localStorage ? root.localStorage.getItem(STORAGE_KEY) : null;
      if (!raw) return createInitialMonsterState();
      var parsed = JSON.parse(raw);
      return normalizeMonsterState(parsed);
    } catch (err) {
      return createInitialMonsterState();
    }
  }

  function saveState(state) {
    if (root.localStorage) {
      root.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }
  }

  var MonsterEngine = {
    FOOD_TYPES: FOOD_TYPES,
    FOOD_BALANCE: FOOD_BALANCE,
    COMBO_CONTINUE_SECONDS: COMBO_CONTINUE_SECONDS,
    COMBO_TOO_FAST_SECONDS: COMBO_TOO_FAST_SECONDS,
    BASE_EVOLUTION_LEVEL: BASE_EVOLUTION_LEVEL,
    FIRST_EVOLUTION_LEVEL: FIRST_EVOLUTION_LEVEL,
    SECOND_EVOLUTION_LEVEL: SECOND_EVOLUTION_LEVEL,
    FOOD_PRIORITY: FOOD_PRIORITY,
    GRADUATION_MIN_LEVEL: GRADUATION_MIN_LEVEL,
    GRADUATION_PROMPT_INTERVAL: GRADUATION_PROMPT_INTERVAL,
    SCALE_CAP: SCALE_CAP,
    CHILD_BY_FOOD: CHILD_BY_FOOD,
    MATURE_BY_FOODS: MATURE_BY_FOODS,
    FINAL_BY_FOODS: FINAL_BY_FOODS,
    MONSTER_LABELS: MONSTER_LABELS,
    STORAGE_KEY: STORAGE_KEY,

    levelUpRequirement: levelUpRequirement,
    levelProgressFromPoints: levelProgressFromPoints,
    levelFromPoints: levelFromPoints,
    comboMultiplier: comboMultiplier,
    foodRatio: foodRatio,
    dominantFood: dominantFood,
    foodsOverThreshold: foodsOverThreshold,
    dominantFoodWithBalance: dominantFoodWithBalance,
    recordFoodChoice: recordFoodChoice,
    resetStageFoodHistory: resetStageFoodHistory,
    applyEvolutionIfNeeded: applyEvolutionIfNeeded,
    evaluateTap: evaluateTap,
    createInitialMonsterState: createInitialMonsterState,
    applyFeeding: applyFeeding,
    assetFamily: assetFamily,
    displayName: displayName,
    loadState: loadState,
    saveState: saveState,

    sizeForLevel: sizeForLevel,
    formatSize: formatSize,
    cssScaleForLevel: cssScaleForLevel,
    canGraduate: canGraduate,
    graduationThresholdForLevel: graduationThresholdForLevel,
    shouldShowGraduationPrompt: shouldShowGraduationPrompt,
    markGraduationPrompted: markGraduationPrompted,
    graduate: graduate
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = MonsterEngine;
  }
  if (typeof window !== "undefined") {
    window.MonsterEngine = MonsterEngine;
  }
})(typeof window !== "undefined" ? window : global);
