/* ==========================================================================
   Dev Vault — portal behaviour
   No framework, no bundler, no dependencies. Served exactly as committed.

   The single data source is catalog/index.json, fetched at runtime. This file
   never embeds resource data, so the catalog stays the only source of truth.
   ========================================================================== */
(function () {
  "use strict";

  var TYPES = [
    "skills", "snippets", "configurations", "templates",
    "prompts", "workflows", "references"
  ];

  var TYPE_LABEL = {
    skills: "Skill",
    snippets: "Snippet",
    configurations: "Configuration",
    templates: "Template",
    prompts: "Prompt",
    workflows: "Workflow",
    references: "Reference"
  };

  /* Absolute URL of the site root, so project base paths (/dev-vault/) and
     local previews both resolve the same way. */
  var BASE = new URL(".", window.location.href).href;

  var state = {
    all: [],
    query: "",
    type: "all",
    status: "idle", // idle | loading | ready | error
    error: null,
    version: null
  };

  var el = {};

  function $(id) {
    return document.getElementById(id);
  }

  function norm(value) {
    return String(value == null ? "" : value).toLowerCase();
  }

  /* ---------- Rendering helpers ---------- */

  function text(tag, className, content) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (content != null) node.textContent = content;
    return node;
  }

  function resourceURL(resource) {
    var path = norm(resource.path);
    return BASE + path;
  }

  function statusBadge(status) {
    var badge = text("span", "badge badge-" + norm(status), status);
    return badge;
  }

  function buildCard(resource) {
    var card = document.createElement("article");
    card.className = "res-card";

    var top = text("div", "res-top");
    var name = text("h3", "res-name");
    var link = document.createElement("a");
    link.href = resourceURL(resource);
    link.textContent = resource.name || resource.id;
    name.appendChild(link);
    top.appendChild(name);
    top.appendChild(text("span", "badge badge-type", TYPE_LABEL[resource.type] || resource.type));
    top.appendChild(statusBadge(resource.status));
    card.appendChild(top);

    card.appendChild(text("p", "res-desc", resource.description));

    var meta = text("div", "res-meta");
    var langs = Array.isArray(resource.language) ? resource.language : [];
    if (langs.length) {
      meta.appendChild(text("span", "", langs.join(" · ")));
    }
    if (resource.version) {
      meta.appendChild(text("span", "", "v" + resource.version));
    }
    var compat = Array.isArray(resource.compatibility) ? resource.compatibility : [];
    if (compat.length) {
      meta.appendChild(text("span", "", compat.join(" · ")));
    }
    if (meta.childNodes.length) card.appendChild(meta);

    return card;
  }

  function statePanel(options) {
    var panel = document.createElement("div");
    panel.className = "state" + (options.isError ? " is-error" : "");

    var icon = text("span", "state-icon");
    icon.setAttribute("aria-hidden", "true");
    icon.innerHTML = options.isError
      ? '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 8v5M12 16.5v.01"/><circle cx="12" cy="12" r="9"/></svg>'
      : '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M4 12h16M4 17h10"/></svg>';
    panel.appendChild(icon);

    panel.appendChild(text("p", "state-title", options.title));

    if (options.body) {
      var body = text("p", "state-body");
      body.innerHTML = options.body;
      panel.appendChild(body);
    }

    if (options.links && options.links.length) {
      var actions = text("div", "state-actions");
      options.links.forEach(function (item) {
        var anchor = document.createElement("a");
        anchor.className = "btn";
        anchor.href = item.href;
        anchor.textContent = item.label;
        actions.appendChild(anchor);
      });
      panel.appendChild(actions);
    }

    return panel;
  }

  /* ---------- Filtering ---------- */

  function matchesQuery(resource, query) {
    if (!query) return true;

    var haystack = [
      resource.id, resource.name, resource.description, resource.type,
      resource.status, resource.version, resource.license
    ];

    ["language", "technologies", "use_cases", "compatibility", "dependencies"].forEach(function (key) {
      var value = resource[key];
      if (Array.isArray(value)) haystack = haystack.concat(value);
    });

    var hay = norm(haystack.join(" \u0001 "));
    /* Every whitespace-separated term must appear somewhere in the entry. */
    return query.split(/\s+/).every(function (term) {
      return hay.indexOf(term) !== -1;
    });
  }

  function visibleResources() {
    var query = norm(state.query).trim();
    return state.all.filter(function (resource) {
      if (state.type !== "all" && resource.type !== state.type) return false;
      return matchesQuery(resource, query);
    });
  }

  /* ---------- Sections ---------- */

  function renderStats() {
    var total = state.all.length;
    var counts = {};
    TYPES.forEach(function (type) { counts[type] = 0; });
    var languages = {};

    state.all.forEach(function (resource) {
      if (counts[resource.type] != null) counts[resource.type] += 1;
      (Array.isArray(resource.language) ? resource.language : []).forEach(function (lang) {
        if (norm(lang) !== "n/a") languages[norm(lang)] = true;
      });
    });

    var populated = TYPES.filter(function (type) { return counts[type] > 0; }).length;
    var stable = state.all.filter(function (r) { return r.status === "stable"; }).length;

    var figures = [
      { value: total, label: total === 1 ? "Resource" : "Resources" },
      { value: populated, label: "Types populated" },
      { value: stable, label: "Marked stable" },
      { value: Object.keys(languages).length, label: "Languages" }
    ];

    el.stats.innerHTML = "";
    el.stats.setAttribute("aria-busy", "false");

    figures.forEach(function (figure) {
      var wrap = text("div", "stat");
      var value = text("span", "stat-value", String(figure.value));
      if (figure.value === 0) value.classList.add("is-empty");
      wrap.appendChild(value);
      wrap.appendChild(text("span", "stat-label", figure.label));
      el.stats.appendChild(wrap);
    });

    TYPES.forEach(function (type) {
      var badge = document.querySelector('[data-count-for="' + type + '"]');
      if (badge) badge.textContent = String(counts[type]);
    });

    if (total === 0) {
      el.statsNote.innerHTML =
        'The catalog is currently <strong>empty</strong> — <code>catalog/index.json</code> ' +
        'contains <code>"resources": []</code>. Zero means zero; no placeholders are shown. ' +
        'See <a href="' + BASE + 'docs/ROADMAP.md">Phase 1</a> for what arrives first.';
    } else {
      el.statsNote.innerHTML =
        "Every figure above was read live from <code>catalog/index.json</code> at page load. " +
        "Nothing is hard-coded.";
    }

    if (el.footerVersion) {
      el.footerVersion.textContent = state.version == null ? "—" : String(state.version);
    }
  }

  function renderResults() {
    var results = visibleResources();
    el.grid.innerHTML = "";

    var total = state.all.length;
    var meta;

    if (total === 0) {
      meta = "No resources in the catalog yet.";
    } else if (results.length === 0) {
      meta = "No matches — 0 of " + total + (total === 1 ? " resource" : " resources");
    } else {
      meta = "Showing " + results.length + " of " + total +
        (total === 1 ? " resource" : " resources");
    }
    el.resultMeta.textContent = meta;

    if (results.length === 0) {
      if (total === 0) {
        el.grid.appendChild(statePanel({
          title: "The catalog is empty — and that is the honest state",
          body:
            "No resources have been added yet, so there is nothing to search. " +
            "The catalog ships with <code>\"resources\": []</code> by design: a new vault " +
            "should not display invented content to look complete.",
          links: [
            { href: BASE + "docs/RESOURCE_STANDARD.md", label: "How to add the first resource" },
            { href: BASE + "catalog/index.json", label: "Read catalog/index.json" }
          ]
        }));
      } else {
        el.grid.appendChild(statePanel({
          title: "No resources match those filters",
          body:
            "Nothing in the catalog matches this search and type combination. " +
            "Try a broader term, or clear the filters.",
          links: [{ href: "#catalog", label: "Clear filters" }]
        }));
        var clearLink = el.grid.querySelector(".state-actions a");
        if (clearLink) {
          clearLink.addEventListener("click", function (event) {
            event.preventDefault();
            resetFilters();
            el.search.focus();
          });
        }
      }
      return;
    }

    var frag = document.createDocumentFragment();
    results.forEach(function (resource) { frag.appendChild(buildCard(resource)); });
    el.grid.appendChild(frag);
  }

  function renderFeatured() {
    if (!el.featuredGrid) return;
    el.featuredGrid.innerHTML = "";

    if (state.all.length === 0) {
      el.featuredGrid.appendChild(statePanel({
        title: "Nothing to feature yet",
        body:
          "Featured entries are promoted from the catalog by lifecycle status " +
          "(<code>stable</code> first, then <code>experimental</code>). With an empty " +
          "catalog this section stays empty rather than inventing a showcase."
      }));
      return;
    }

    var order = { stable: 0, experimental: 1, deprecated: 2, archived: 3 };
    var featured = state.all
      .slice()
      .sort(function (a, b) {
        var rankA = order[a.status] == null ? 9 : order[a.status];
        var rankB = order[b.status] == null ? 9 : order[b.status];
        if (rankA !== rankB) return rankA - rankB;
        return String(a.name || a.id).localeCompare(String(b.name || b.id));
      })
      .slice(0, 3);

    var frag = document.createDocumentFragment();
    featured.forEach(function (resource) { frag.appendChild(buildCard(resource)); });
    el.featuredGrid.appendChild(frag);
  }

  function syncFilterUI() {
    el.filters.forEach(function (chip) {
      var active = chip.dataset.type === state.type;
      chip.classList.toggle("is-active", active);
      chip.setAttribute("aria-pressed", active ? "true" : "false");
    });
    document.querySelectorAll(".cat-card").forEach(function (card) {
      card.classList.toggle("is-active", card.dataset.type === state.type);
    });
  }

  function resetFilters() {
    state.query = "";
    state.type = "all";
    el.search.value = "";
    el.clear.hidden = true;
    syncFilterUI();
    renderResults();
  }

  /* ---------- Data ---------- */

  function renderError(message) {
    state.status = "error";
    state.error = message;
    el.stats.setAttribute("aria-busy", "false");
    el.stats.innerHTML =
      '<div class="stat"><span class="stat-value is-empty">—</span><span class="stat-label">Catalog unavailable</span></div>' +
      '<div class="stat"><span class="stat-value is-empty">—</span><span class="stat-label">Not loaded</span></div>' +
      '<div class="stat"><span class="stat-value is-empty">—</span><span class="stat-label">Not loaded</span></div>' +
      '<div class="stat"><span class="stat-value is-empty">—</span><span class="stat-label">Not loaded</span></div>';
    el.statsNote.innerHTML =
      "Statistics are unavailable because the catalog could not be read. " +
      "No numbers are guessed.";

    el.resultMeta.textContent = "Catalog unavailable";
    el.grid.innerHTML = "";
    el.grid.appendChild(statePanel({
      isError: true,
      title: "Could not load catalog/index.json",
      body:
        "The page fetches the catalog directly from the repository. If you are running " +
        "this file from disk rather than a web server, the browser will block the request. " +
        "Serve the folder over HTTP, or read the catalog straight from GitHub.<br><br>" +
        "<span class=\"sr-only\">Error detail:</span><code>" +
        String(message).replace(/[<>&]/g, "") + "</code>",
      links: [
        {
          href: "https://raw.githubusercontent.com/shaonkabir8/dev-vault/main/catalog/index.json",
          label: "Read catalog on raw.githubusercontent.com"
        },
        {
          href: "https://github.com/shaonkabir8/dev-vault/blob/main/catalog/index.json",
          label: "View on GitHub"
        }
      ]
    }));

    if (el.featuredGrid) {
      el.featuredGrid.innerHTML = "";
      el.featuredGrid.appendChild(statePanel({
        isError: true,
        title: "Featured resources unavailable",
        body: "This section depends on the same catalog that failed to load."
      }));
    }
  }

  function load() {
    state.status = "loading";

    var url = BASE + "catalog/index.json";

    fetch(url, { cache: "no-cache", headers: { Accept: "application/json" } })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("HTTP " + response.status + " for " + url);
        }
        return response.json();
      })
      .then(function (catalog) {
        if (!catalog || !Array.isArray(catalog.resources)) {
          throw new Error("catalog/index.json has no resources array");
        }
        state.all = catalog.resources;
        state.version = catalog.version;
        state.status = "ready";

        renderStats();
        renderResults();
        renderFeatured();
        syncFilterUI();
      })
      .catch(function (error) {
        state.all = [];
        renderError(error && error.message ? error.message : "Unknown error");
      });
  }

  /* ---------- Theme ---------- */

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    var isDark = theme === "dark";
    el.themeToggle.setAttribute(
      "aria-label",
      isDark ? "Switch to light theme" : "Switch to dark theme"
    );
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", isDark ? "#08090c" : "#fbfbfd");
  }

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function initTheme() {
    applyTheme(currentTheme());

    el.themeToggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem("dev-vault-theme", next);
      } catch (e) {
        /* Persistence unavailable — the in-memory theme still applies. */
      }
    });
  }

  /* ---------- Navigation ---------- */

  function initNav() {
    el.navToggle.addEventListener("click", function () {
      var open = el.nav.classList.toggle("is-open");
      el.navToggle.setAttribute("aria-expanded", open ? "true" : "false");
      el.navToggle.setAttribute("aria-label", open ? "Close navigation menu" : "Open navigation menu");
    });

    el.nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        el.nav.classList.remove("is-open");
        el.navToggle.setAttribute("aria-expanded", "false");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && el.nav.classList.contains("is-open")) {
        el.nav.classList.remove("is-open");
        el.navToggle.setAttribute("aria-expanded", "false");
        el.navToggle.focus();
      }
    });
  }

  /* ---------- Search ---------- */

  function initSearch() {
    el.search.addEventListener("input", function () {
      state.query = el.search.value;
      el.clear.hidden = el.search.value.length === 0;
      renderResults();
    });

    el.clear.addEventListener("click", function () {
      el.search.value = "";
      state.query = "";
      el.clear.hidden = true;
      el.search.focus();
      renderResults();
    });

    el.filters.forEach(function (chip) {
      chip.addEventListener("click", function () {
        state.type = chip.dataset.type;
        syncFilterUI();
        renderResults();
      });
    });

    document.querySelectorAll(".cat-card").forEach(function (card) {
      card.addEventListener("click", function () {
        state.type = card.dataset.type;
        syncFilterUI();
        renderResults();
        document.getElementById("catalog").scrollIntoView({ behavior: "smooth", block: "start" });
        window.setTimeout(function () { el.search.focus(); }, 260);
      });
    });

    document.addEventListener("keydown", function (event) {
      var target = event.target;
      var typing = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);

      if (event.key === "/" && !typing && !event.metaKey && !event.ctrlKey && !event.altKey) {
        event.preventDefault();
        el.search.focus();
        el.search.select();
        return;
      }

      if (event.key === "Escape" && typing && target === el.search && el.search.value) {
        el.search.value = "";
        state.query = "";
        el.clear.hidden = true;
        renderResults();
      }
    });
  }

  /* ---------- Copy to clipboard ---------- */

  function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(value);
    }
    return new Promise(function (resolve, reject) {
      var area = document.createElement("textarea");
      area.value = value;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.top = "-1000px";
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try {
        ok = document.execCommand("copy");
      } catch (e) {
        ok = false;
      }
      document.body.removeChild(area);
      ok ? resolve() : reject(new Error("copy command rejected"));
    });
  }

  function flash(button, label, isError) {
    var target = button.querySelector(".copy-label");
    if (!target) return;
    var original = target.textContent;
    button.classList.remove("is-done", "is-fail");
    button.classList.add(isError ? "is-fail" : "is-done");
    target.textContent = label;
    window.setTimeout(function () {
      button.classList.remove("is-done", "is-fail");
      target.textContent = original;
    }, 1600);
  }

  function initCopy() {
    document.querySelectorAll(".copy-btn").forEach(function (button) {
      var path = button.dataset.path;
      var literal = button.dataset.copy;
      var value = literal != null ? literal : BASE + path;

      if (path) button.title = value;

      button.addEventListener("click", function () {
        copyText(value)
          .then(function () { flash(button, "Copied"); })
          .catch(function () { flash(button, "Failed", true); });
      });
    });
  }

  /* ---------- Boot ---------- */

  function init() {
    el.stats = $("stats");
    el.statsNote = $("stats-note");
    el.grid = $("resource-grid");
    el.featuredGrid = $("featured-grid");
    el.resultMeta = $("result-meta");
    el.search = $("search-input");
    el.clear = $("search-clear");
    el.nav = $("site-nav");
    el.navToggle = $("nav-toggle");
    el.themeToggle = $("theme-toggle");
    el.footerVersion = $("footer-catalog-version");

    el.filters = Array.prototype.slice.call(document.querySelectorAll(".chip[data-type]"));

    var year = $("year");
    if (year) year.textContent = String(new Date().getFullYear());

    initTheme();
    initNav();
    initSearch();
    initCopy();
    syncFilterUI();
    load();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
