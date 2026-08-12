/*
 * Sport-agnostic Story viewer.
 *
 * Loads a Story JSON (produced by the builder) and renders its pages as a
 * tap-through "Stories" experience. It knows nothing about soccer or any
 * specific teams - it just renders cover / highlight / info pages, so it works
 * unchanged for any sport the builder supports.
 */
(function () {
  "use strict";

  // The builder writes /out/story.json and images live under /assets, both at
  // the repo root (this file lives in /preview). Depending on how the site is
  // served we may be one level under the root or at it, so we try a few
  // candidate locations. Override explicitly with ?story=<url>.
  var params = new URLSearchParams(location.search);
  var override = params.get("story");
  var STORY_CANDIDATES = override
    ? [override]
    : ["../out/story.json", "out/story.json", "/out/story.json", "./story.json"];
  // Asset prefix is chosen to match whichever story URL succeeds.
  var ASSET_PREFIX = "../";
  var SLIDE_MS = 6000;

  var el = {
    stage: document.getElementById("stage"),
    progress: document.getElementById("progress"),
    counter: document.getElementById("counter"),
    title: document.getElementById("storyTitle"),
    loading: document.getElementById("loading"),
    playPause: document.getElementById("playPause"),
    tapPrev: document.getElementById("tapPrev"),
    tapNext: document.getElementById("tapNext"),
    phone: document.getElementById("phone"),
    status: document.getElementById("status"),
  };

  var state = { pages: [], index: 0, timer: null, start: 0, elapsed: 0, paused: false };

  init();

  function init() {
    wireControls();
    loadStory(0);
  }

  function loadStory(i) {
    if (i >= STORY_CANDIDATES.length) {
      return showError(new Error("Story not found. Tried: " + STORY_CANDIDATES.join(", ")));
    }
    var url = STORY_CANDIDATES[i];
    fetch(url, { cache: "no-store" })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        // Resolve asset paths relative to the story file's directory.
        ASSET_PREFIX = url.slice(0, url.lastIndexOf("/") + 1).replace(/out\/$/, "");
        return r.json();
      })
      .then(start)
      .catch(function () { loadStory(i + 1); });
  }

  function start(story) {
    state.pages = story.pages || [];
    if (!state.pages.length) return showError(new Error("Story has no pages."));
    el.title.textContent = story.title || "Story";
    el.loading.remove();
    buildProgress();
    go(0);
  }

  function buildProgress() {
    el.progress.innerHTML = "";
    state.pages.forEach(function () {
      var seg = document.createElement("div");
      seg.className = "seg";
      seg.innerHTML = "<i></i>";
      el.progress.appendChild(seg);
    });
  }

  function go(i) {
    if (i < 0 || i >= state.pages.length) return;
    state.index = i;
    var page = state.pages[i];
    render(page);
    updateProgressMarks();
    el.counter.textContent = i + 1 + " / " + state.pages.length;
    announce(i, page);
    restartTimer();
  }

  function announce(i, page) {
    if (!el.status) return;
    var label = page.headline || (page.type || "page");
    el.status.textContent = "Page " + (i + 1) + " of " + state.pages.length + ": " + label;
  }

  function next() { state.index < state.pages.length - 1 ? go(state.index + 1) : stopTimer(true); }
  function prev() { if (state.index > 0) go(state.index - 1); }

  function render(page) {
    var node = document.createElement("div");
    node.className = "page " + (page.type || "highlight");

    if (page.type !== "info") {
      var bg = document.createElement("div");
      bg.className = "bg";
      if (page.image) applyImage(bg, ASSET_PREFIX + page.image);
      node.appendChild(bg);
      var scrim = document.createElement("div");
      scrim.className = "scrim";
      node.appendChild(scrim);
    } else {
      var solid = document.createElement("div");
      solid.className = "bg";
      node.appendChild(solid);
    }

    var content = document.createElement("div");
    content.className = "content";

    if (page.type === "cover") {
      content.appendChild(h1(page.headline));
      if (page.subheadline) content.appendChild(div("sub", page.subheadline));
    } else if (page.type === "info") {
      renderInfo(content, page);
    } else {
      if (typeof page.minute === "number") {
        content.appendChild(badge("minute", page.minute + "'"));
      }
      content.appendChild(h1(page.headline));
      if (page.caption) content.appendChild(div("caption", page.caption));
      if (page.explanation) content.appendChild(div("explain", page.explanation));
    }

    node.appendChild(content);
    el.stage.innerHTML = "";
    el.stage.appendChild(node);
  }

  // Info page: a full-time scoreboard + home-vs-away stat comparison when the
  // structured fields are present; otherwise a simple text panel.
  function renderInfo(content, page) {
    content.appendChild(div("kicker", page.headline || "Summary"));

    if (page.home_team && page.away_team && typeof page.home_score === "number") {
      var board = document.createElement("div");
      board.className = "scoreboard";
      board.appendChild(teamCol(page.home_code || page.home_team, page.home_team));
      var score = document.createElement("div");
      score.className = "score";
      score.textContent = page.home_score + " – " + page.away_score;
      board.appendChild(score);
      board.appendChild(teamCol(page.away_code || page.away_team, page.away_team));
      content.appendChild(board);
    }

    if (Array.isArray(page.stats) && page.stats.length) {
      var table = document.createElement("div");
      table.className = "stats";
      page.stats.forEach(function (row) {
        table.appendChild(statRow(row));
      });
      content.appendChild(table);
    } else if (page.body) {
      content.appendChild(div("body", page.body));
    }
  }

  function teamCol(code, name) {
    var col = document.createElement("div");
    col.className = "team";
    col.innerHTML = "<span class='code'>" + escapeHtml(code) + "</span>";
    return col;
  }

  function statRow(row) {
    var home = Number(row.home) || 0;
    var away = Number(row.away) || 0;
    var total = home + away;
    var hPct = total ? Math.round((home / total) * 100) : 50;
    var wrap = document.createElement("div");
    wrap.className = "stat";
    wrap.innerHTML =
      "<div class='stat-top'><span>" + home + "</span>" +
      "<span class='stat-label'>" + escapeHtml(row.label) + "</span>" +
      "<span>" + away + "</span></div>" +
      "<div class='bar'><i style='width:" + hPct + "%'></i></div>";
    return wrap;
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>\"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function applyImage(node, url) {
    var img = new Image();
    img.onload = function () { node.style.backgroundImage = "url('" + url + "')"; };
    img.onerror = function () {
      node.style.backgroundImage = "url('" + ASSET_PREFIX + "assets/placeholder.png')";
    };
    img.src = url;
  }

  // --- progress / autoplay ------------------------------------------------
  function updateProgressMarks() {
    var segs = el.progress.children;
    for (var i = 0; i < segs.length; i++) {
      var done = i < state.index;
      segs[i].classList.toggle("done", done);
      // Set the fill explicitly: an inline width from tick() would otherwise
      // override the .done CSS and leave a skipped bar stuck mid-fill.
      segs[i].querySelector("i").style.width = done ? "100%" : "0%";
      segs[i].setAttribute("aria-current", i === state.index ? "true" : "false");
    }
  }

  function restartTimer() {
    stopTimer(false);
    state.start = performance.now();
    state.elapsed = 0;
    if (!state.paused) tick();
  }

  function tick() {
    state.timer = requestAnimationFrame(function (now) {
      var pct = Math.min(((now - state.start + state.elapsed) / SLIDE_MS) * 100, 100);
      var cur = el.progress.children[state.index];
      if (cur) cur.querySelector("i").style.width = pct + "%";
      if (pct >= 100) return next();
      tick();
    });
  }

  function stopTimer(fillCurrent) {
    if (state.timer) cancelAnimationFrame(state.timer);
    state.timer = null;
    if (fillCurrent) {
      var cur = el.progress.children[state.index];
      if (cur) cur.querySelector("i").style.width = "100%";
    }
  }

  function setPaused(paused) {
    state.paused = paused;
    el.playPause.textContent = paused ? "►" : "❚❚";
    el.playPause.setAttribute("aria-label", paused ? "Play" : "Pause");
    if (paused) {
      state.elapsed += performance.now() - state.start;
      stopTimer(false);
    } else {
      state.start = performance.now();
      tick();
    }
  }

  // --- controls -----------------------------------------------------------
  function wireControls() {
    el.tapNext.addEventListener("click", next);
    el.tapPrev.addEventListener("click", prev);
    el.playPause.addEventListener("click", function () { setPaused(!state.paused); });

    document.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") prev();
      else if (e.key === "Home") { e.preventDefault(); go(0); }
      else if (e.key === "End") { e.preventDefault(); go(state.pages.length - 1); }
      else if (e.key === " ") { e.preventDefault(); setPaused(!state.paused); }
    });

    // Press-and-hold anywhere to pause.
    var holdPause = function () { if (!state.paused) setPaused(true); };
    var holdResume = function () { if (state.paused) setPaused(false); };
    el.phone.addEventListener("mousedown", holdPause);
    el.phone.addEventListener("mouseup", holdResume);
    el.phone.addEventListener("touchstart", holdPause, { passive: true });
    el.phone.addEventListener("touchend", holdResume);
  }

  // --- helpers ------------------------------------------------------------
  function h1(text) { var n = document.createElement("h1"); n.textContent = text || ""; return n; }
  function div(cls, text) { var n = document.createElement("div"); n.className = cls; n.textContent = text || ""; return n; }
  function badge(cls, text) {
    var n = document.createElement("span");
    n.className = "badge " + cls;
    n.textContent = text;
    return n;
  }

  function showError(err) {
    var box = document.createElement("div");
    box.className = "error";
    box.innerHTML =
      "Could not load the story.<br><br><code>" + (err && err.message ? err.message : err) +
      "</code><br><br>Run the builder, then serve from the repo root:<br>" +
      "<code>python -m http.server</code><br>and open <code>/preview/</code>.";
    el.stage.innerHTML = "";
    el.stage.appendChild(box);
  }
})();
