/** Peptide Guide Web — SPA на данных из бота */

const FAV_KEY = "peptide_guide_favs";

let data = null;
let favorites = loadFavs();

const $ = (sel) => document.querySelector(sel);
const content = $("#content");
const breadcrumbs = $("#breadcrumbs");
const searchInput = $("#searchInput");

// --- Favorites (localStorage) ---

function loadFavs() {
  try {
    return new Set(JSON.parse(localStorage.getItem(FAV_KEY) || "[]"));
  } catch {
    return new Set();
  }
}

function saveFavs() {
  localStorage.setItem(FAV_KEY, JSON.stringify([...favorites]));
}

function toggleFav(id) {
  if (favorites.has(id)) favorites.delete(id);
  else favorites.add(id);
  saveFavs();
}

function isFav(id) {
  return favorites.has(id);
}

// --- Router ---

function parseRoute() {
  const hash = location.hash.slice(1) || "/";
  const parts = hash.split("/").filter(Boolean);
  return parts;
}

function navigate(parts, push = true) {
  const hash = parts.length ? "#/" + parts.join("/") : "#/";
  if (push && location.hash !== hash) location.hash = hash;
  else render(parts);
}

function render(parts) {
  if (!data) return;

  updateNavActive(parts);
  renderBreadcrumbs(parts);

  const [view, ...rest] = parts.length ? parts : ["home"];

  switch (view) {
    case "home":
      renderHome();
      break;
    case "cat":
      renderCategory(rest[0], rest[1]);
      break;
    case "sub":
      renderSubstance(rest[0], rest[1], rest[2]);
      break;
    case "all":
      renderAll(rest[0]);
      break;
    case "favorites":
      renderFavorites();
      break;
    case "disclaimer":
      renderDisclaimer();
      break;
    case "search":
      renderSearch(rest.join("/"));
      break;
    default:
      renderHome();
  }

  closeSidebar();
}

function updateNavActive(parts) {
  const view = parts[0] || "home";
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.route === view);
  });
}

function renderBreadcrumbs(parts) {
  const crumbs = [{ label: "Главная", route: [] }];

  if (!parts.length || parts[0] === "home") {
    breadcrumbs.innerHTML = `<span>Главная</span>`;
    return;
  }

  const [view, ...rest] = parts;

  if (view === "cat" && rest[0]) {
    const cat = data.categories[rest[0]];
    if (cat) {
      crumbs.push({ label: cat.title, route: ["cat", rest[0]] });
      if (rest[1] && data.stackLevels[rest[1]]) {
        crumbs.push({
          label: data.stackLevels[rest[1]].title,
          route: ["cat", rest[0], rest[1]],
        });
      }
    }
  } else if (view === "sub" && rest[0]) {
    const sub = data.substances[rest[0]];
    if (sub) crumbs.push({ label: sub.name, route: ["sub", rest[0]] });
    if (rest[1] === "form" && rest[2] && sub?.forms?.[rest[2]]) {
      crumbs.push({
        label: sub.forms[rest[2]].title,
        route: ["sub", rest[0], "form", rest[2]],
      });
    }
  } else if (view === "all") {
    crumbs.push({ label: "Все A–Z", route: ["all"] });
  } else if (view === "favorites") {
    crumbs.push({ label: "Избранное", route: ["favorites"] });
  } else if (view === "disclaimer") {
    crumbs.push({ label: "О базе", route: ["disclaimer"] });
  } else if (view === "search") {
    crumbs.push({ label: `Поиск: ${decodeURIComponent(rest.join("/"))}`, route: parts });
  }

  breadcrumbs.innerHTML = crumbs
    .map((c, i) => {
      const isLast = i === crumbs.length - 1;
      const link = isLast
        ? `<span>${esc(c.label)}</span>`
        : `<a href="#/${c.route.join("/")}">${esc(c.label)}</a>`;
      const sep = isLast ? "" : `<span class="sep">›</span>`;
      return link + sep;
    })
    .join("");
}

// --- Views ---

function renderHome() {
  const cats = Object.entries(data.categories);
  content.innerHTML = `
    <div class="hero">
      <h1>Личная база по пептидам и препам</h1>
      <p>Те же заметки, что в Telegram-боте — но с нормальным поиском, избранным и навигацией по разделам.</p>
      <div class="stats">
        <div class="stat"><strong>${data.meta.substanceCount}</strong> веществ</div>
        <div class="stat"><strong>${data.meta.categoryCount}</strong> разделов</div>
        <div class="stat"><strong>${favorites.size}</strong> в избранном</div>
      </div>
    </div>
    <div class="grid">
      ${cats
        .map(([id, cat]) => `
          <button class="card-btn" data-cat="${id}">
            <span class="title">${esc(cat.title)}</span>
            <span class="desc">${esc(cat.desc || "")}</span>
            <span class="count">${cat.items.length} записей →</span>
          </button>
        `)
        .join("")}
    </div>
  `;

  content.querySelectorAll("[data-cat]").forEach((btn) => {
    btn.addEventListener("click", () => navigate(["cat", btn.dataset.cat]));
  });
}

function renderCategory(catId, levelId) {
  const cat = data.categories[catId];
  if (!cat) {
    content.innerHTML = `<div class="empty">Раздел не найден</div>`;
    return;
  }

  if (cat.hub === "stack_levels" && !levelId) {
    content.innerHTML = `
      <div class="section-head">
        <h2>${esc(cat.title)}</h2>
        <p>${esc(cat.desc)}</p>
      </div>
      <div class="level-grid">
        ${Object.entries(data.stackLevels)
          .map(
            ([lid, lvl]) => `
          <button class="level-pill ${lid}" data-level="${lid}">
            <div class="title">${esc(lvl.title)}</div>
            <div class="desc">${esc(lvl.desc)} · ${lvl.items.length} связок</div>
          </button>
        `
          )
          .join("")}
      </div>
    `;
    content.querySelectorAll("[data-level]").forEach((btn) => {
      btn.addEventListener("click", () =>
        navigate(["cat", catId, btn.dataset.level])
      );
    });
    return;
  }

  const items =
    levelId && data.stackLevels[levelId]
      ? data.stackLevels[levelId].items
      : cat.items;

  const title =
    levelId && data.stackLevels[levelId]
      ? data.stackLevels[levelId].title
      : cat.title;

  const desc =
    levelId && data.stackLevels[levelId]
      ? data.stackLevels[levelId].desc
      : cat.desc;

  content.innerHTML = `
    <div class="section-head">
      <h2>${esc(title)}</h2>
      <p>${esc(desc || "")}</p>
    </div>
    <div class="item-list">
      ${items
        .map((sid) => itemRow(sid))
        .filter(Boolean)
        .join("")}
    </div>
  `;

  bindItemRows();
}

function renderSubstance(sid, formMode, formId) {
  const sub = data.substances[sid];
  if (!sub) {
    content.innerHTML = `<div class="empty">Запись не найдена</div>`;
    return;
  }

  const hasForms = sub.forms && Object.keys(sub.forms).length > 0;
  const activeForm = formId || (hasForms ? Object.keys(sub.forms)[0] : null);

  let cardHtml = "";
  let formTabs = "";

  if (hasForms) {
    formTabs = `
      <div class="form-tabs">
        ${Object.entries(sub.forms)
          .map(
            ([fid, f]) => `
          <button class="form-tab ${fid === activeForm ? "active" : ""}" data-form="${fid}">
            ${esc(f.title)}
          </button>
        `
          )
          .join("")}
      </div>
    `;
    cardHtml = sub.forms[activeForm]?.card || "";
  } else {
    cardHtml = sub.card || "";
  }

  const components =
    sub.components?.length > 0
      ? `
    <div class="components">
      <h3>Компоненты связки</h3>
      <div class="comp-chips">
        ${sub.components
          .map((cid) => {
            const c = data.substances[cid];
            return c
              ? `<span class="chip" data-sub="${cid}">${esc(c.name)}</span>`
              : "";
          })
          .join("")}
      </div>
    </div>
  `
      : "";

  const favClass = isFav(sid) ? "fav-active" : "";

  content.innerHTML = `
    <div class="detail-card">
      ${formTabs}
      <div class="card-html">${cardHtml}</div>
      ${components}
      <div class="detail-actions">
        <button class="btn ${favClass}" id="favBtn">${isFav(sid) ? "★ В избранном" : "☆ В избранное"}</button>
        <button class="btn" id="backBtn">← Назад</button>
      </div>
    </div>
  `;

  content.querySelectorAll(".form-tab").forEach((tab) => {
    tab.addEventListener("click", () =>
      navigate(["sub", sid, "form", tab.dataset.form], true)
    );
  });

  content.querySelectorAll(".chip[data-sub]").forEach((chip) => {
    chip.addEventListener("click", () => navigate(["sub", chip.dataset.sub]));
  });

  $("#favBtn").addEventListener("click", () => {
    toggleFav(sid);
    renderSubstance(sid, formMode, activeForm);
  });

  $("#backBtn").addEventListener("click", () => history.back());
}

function renderAll(pageStr) {
  const page = parseInt(pageStr || "0", 10) || 0;
  const PAGE = 30;
  const sorted = Object.values(data.substances).sort((a, b) =>
    a.name.localeCompare(b.name, "ru")
  );
  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE));
  const p = Math.min(Math.max(0, page), totalPages - 1);
  const slice = sorted.slice(p * PAGE, (p + 1) * PAGE);

  content.innerHTML = `
    <div class="section-head">
      <h2>📋 Все вещества A–Z</h2>
      <p>${sorted.length} записей · страница ${p + 1} из ${totalPages}</p>
    </div>
    <div class="item-list">
      ${slice.map((s) => itemRow(s.id)).join("")}
    </div>
    <div class="detail-actions" style="margin-top:1rem;border:none;padding:0">
      ${p > 0 ? `<button class="btn" id="prevPage">← Назад</button>` : ""}
      ${p < totalPages - 1 ? `<button class="btn primary" id="nextPage">Дальше →</button>` : ""}
    </div>
  `;

  bindItemRows();
  $("#prevPage")?.addEventListener("click", () => navigate(["all", String(p - 1)]));
  $("#nextPage")?.addEventListener("click", () => navigate(["all", String(p + 1)]));
}

function renderFavorites() {
  const ids = [...favorites].filter((id) => data.substances[id]);

  if (!ids.length) {
    content.innerHTML = `
      <div class="empty">
        <p>Избранное пустое.</p>
        <p>Открой любую карточку и нажми «☆ В избранное».</p>
      </div>
    `;
    return;
  }

  content.innerHTML = `
    <div class="section-head">
      <h2>⭐ Избранное</h2>
      <p>${ids.length} записей</p>
    </div>
    <div class="item-list">
      ${ids.map((sid) => itemRow(sid)).join("")}
    </div>
  `;
  bindItemRows();
}

function renderDisclaimer() {
  content.innerHTML = `
    <div class="detail-card">
      <div class="card-html">${data.disclaimer}</div>
    </div>
  `;
}

async function renderSearch(query) {
  const q = decodeURIComponent(query || "").trim();
  if (!q) {
    content.innerHTML = `<div class="empty">Введи запрос в поиск</div>`;
    return;
  }

  const results = searchLocal(q);

  if (!results.length) {
    content.innerHTML = `
      <div class="empty">По запросу «${esc(q)}» ничего не нашлось.</div>
    `;
    return;
  }

  content.innerHTML = `
    <div class="section-head">
      <h2>🔍 Поиск</h2>
      <p>«${esc(q)}» — ${results.length} результатов</p>
    </div>
    <div class="item-list search-results">
      ${results.map((s) => itemRow(s.id)).join("")}
    </div>
  `;
  bindItemRows();
}

function normalizeQuery(q) {
  return q.toLowerCase().replace(/ё/g, "е").trim();
}

function stripHtml(text) {
  return (text || "").replace(/<[^>]+>/g, " ").replace(/\n/g, " ");
}

function substanceSearchText(sub) {
  const parts = [sub.name || "", ...(sub.tags || [])];
  if (sub.card) parts.push(stripHtml(sub.card));
  if (sub.forms) {
    for (const f of Object.values(sub.forms)) {
      parts.push(f.title || "");
      parts.push(stripHtml(f.card));
    }
  }
  return normalizeQuery(parts.join(" "));
}

function searchLocal(query, limit = 30) {
  const nq = normalizeQuery(query);
  if (!nq || !data?.substances) return [];

  const results = [];
  for (const sub of Object.values(data.substances)) {
    if (substanceSearchText(sub).includes(nq)) {
      results.push(sub);
      if (results.length >= limit) break;
    }
  }
  return results;
}

async function loadData() {
  try {
    const res = await fetch("/api/data");
    if (res.ok) return await res.json();
  } catch {
    /* static hosting — без сервера */
  }
  const res = await fetch("/data.json");
  if (!res.ok) throw new Error("data.json not found");
  return await res.json();
}

// --- Helpers ---

function itemRow(sid) {
  const s = data.substances[sid];
  if (!s) return "";
  const tags = (s.tags || [])
    .slice(0, 3)
    .map((t) => `<span class="tag">${esc(t)}</span>`)
    .join("");
  const star = isFav(sid) ? "★ " : "";
  return `
    <div class="item-row" data-sub="${sid}">
      <span class="name">${star}${esc(s.name)}</span>
      <span class="tags">${tags}</span>
    </div>
  `;
}

function bindItemRows() {
  content.querySelectorAll(".item-row[data-sub]").forEach((row) => {
    row.addEventListener("click", () => navigate(["sub", row.dataset.sub]));
  });
}

function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildSidebarCats() {
  const wrap = $("#sidebarCats");
  wrap.innerHTML = Object.entries(data.categories)
    .map(
      ([id, cat]) =>
        `<button class="cat-link" data-cat="${id}">${esc(cat.title)}</button>`
    )
    .join("");

  wrap.querySelectorAll(".cat-link").forEach((btn) => {
    btn.addEventListener("click", () => navigate(["cat", btn.dataset.cat]));
  });
}

function closeSidebar() {
  $("#sidebar").classList.remove("open");
  $("#overlay").classList.remove("open");
}

// --- Init ---

async function init() {
  try {
    data = await loadData();
    buildSidebarCats();
    render(parseRoute());
  } catch (e) {
    content.innerHTML = `<div class="empty">Не удалось загрузить базу. Запусти <code>python web/server.py</code> или <code>python web/export_static.py</code></div>`;
    console.error(e);
  }
}

window.addEventListener("hashchange", () => render(parseRoute()));

document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.addEventListener("click", () => navigate([btn.dataset.route]));
});

$("#menuBtn").addEventListener("click", () => {
  $("#sidebar").classList.toggle("open");
  $("#overlay").classList.toggle("open");
});

$("#overlay").addEventListener("click", closeSidebar);

let searchTimer;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  const q = searchInput.value.trim();
  if (!q) return;
  searchTimer = setTimeout(() => {
    navigate(["search", encodeURIComponent(q)]);
  }, 300);
});

searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    const q = searchInput.value.trim();
    if (q) navigate(["search", encodeURIComponent(q)]);
  }
});

init();
