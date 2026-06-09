const state = {
  accounts: [],
  followups: [],
  insights: null,
};

const els = {
  status: document.querySelector("#status"),
  refreshButton: document.querySelector("#refreshButton"),
  categoryFilter: document.querySelector("#categoryFilter"),
  totalAccounts: document.querySelector("#totalAccounts"),
  hotLeads: document.querySelector("#hotLeads"),
  highFollowups: document.querySelector("#highFollowups"),
  totalCalls: document.querySelector("#totalCalls"),
  leadRows: document.querySelector("#leadRows"),
  followupList: document.querySelector("#followupList"),
  positiveCalls: document.querySelector("#positiveCalls"),
  neutralCalls: document.querySelector("#neutralCalls"),
  negativeCalls: document.querySelector("#negativeCalls"),
  positiveBar: document.querySelector("#positiveBar"),
  neutralBar: document.querySelector("#neutralBar"),
  negativeBar: document.querySelector("#negativeBar"),
  insightList: document.querySelector("#insightList"),
};

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${path} failed: ${response.status} ${detail}`);
  }
  return response.json();
}

async function loadDashboard() {
  setStatus("Loading dashboard data...");
  els.refreshButton.disabled = true;

  try {
    const [accounts, followups, insights] = await Promise.all([
      fetchJson("/api/v1/analytics/accounts?limit=100"),
      fetchJson("/api/v1/analytics/follow-ups?limit=6"),
      fetchJson("/api/v1/analytics/call-insights"),
    ]);

    state.accounts = accounts.items || [];
    state.followups = followups.items || [];
    state.insights = insights;

    render();
    setStatus(`Loaded ${state.accounts.length} accounts from the CRM analytics API.`);
  } catch (error) {
    console.error(error);
    setStatus(error.message || "Unable to load dashboard data.", true);
  } finally {
    els.refreshButton.disabled = false;
  }
}

function render() {
  renderKpis();
  renderLeadRows();
  renderFollowups();
  renderCallInsights();
}

function renderKpis() {
  els.totalAccounts.textContent = state.accounts.length.toString();
  els.hotLeads.textContent = state.accounts.filter((item) => item.lead_score.category === "Hot").length.toString();
  els.highFollowups.textContent = state.accounts.filter((item) => item.follow_up.priority === "High").length.toString();
  els.totalCalls.textContent = (state.insights?.total_calls || 0).toString();
}

function renderLeadRows() {
  const category = els.categoryFilter.value;
  const rows = state.accounts
    .filter((item) => !category || item.lead_score.category === category)
    .sort((a, b) => b.lead_score.score - a.lead_score.score)
    .slice(0, 25);

  els.leadRows.innerHTML = rows
    .map((item) => {
      const why = item.lead_score.explanations?.[0] || "Score uses available CRM signals";
      return `
        <tr>
          <td>
            <strong>${escapeHtml(item.account_name || "Unnamed account")}</strong>
            <div class="card-note">${escapeHtml(item.account_status || "No status")}</div>
          </td>
          <td>${escapeHtml(item.industry || "Unknown")}</td>
          <td class="score">${item.lead_score.score}</td>
          <td><span class="pill ${item.lead_score.category}">${item.lead_score.category}</span></td>
          <td>${escapeHtml(why)}</td>
        </tr>
      `;
    })
    .join("");

  if (!rows.length) {
    els.leadRows.innerHTML = `<tr><td colspan="5">No leads match this filter.</td></tr>`;
  }
}

function renderFollowups() {
  const items = state.followups.slice(0, 6);
  els.followupList.innerHTML = items
    .map((item) => {
      return `
        <article class="followup-card">
          <header>
            <h3>${escapeHtml(item.account_name || "Unnamed account")}</h3>
            <span class="pill priority ${item.follow_up.priority}">${item.follow_up.priority}</span>
          </header>
          <p>${escapeHtml(item.follow_up.suggested_action)}</p>
          <p class="card-note">${escapeHtml(item.follow_up.recommended_time)}</p>
        </article>
      `;
    })
    .join("");

  if (!items.length) {
    els.followupList.innerHTML = `<p class="card-note">No follow-up recommendations yet.</p>`;
  }
}

function renderCallInsights() {
  const insights = state.insights || {};
  const positive = insights.positive_calls || 0;
  const neutral = insights.neutral_calls || 0;
  const negative = insights.negative_calls || 0;
  const total = Math.max(positive + neutral + negative, 1);

  els.positiveCalls.textContent = positive.toString();
  els.neutralCalls.textContent = neutral.toString();
  els.negativeCalls.textContent = negative.toString();
  els.positiveBar.style.width = `${Math.round((positive / total) * 100)}%`;
  els.neutralBar.style.width = `${Math.round((neutral / total) * 100)}%`;
  els.negativeBar.style.width = `${Math.round((negative / total) * 100)}%`;

  const insightItems = insights.insights || [];
  els.insightList.innerHTML = insightItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function setStatus(message, isError = false) {
  els.status.textContent = message;
  els.status.classList.toggle("error", isError);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

els.refreshButton.addEventListener("click", loadDashboard);
els.categoryFilter.addEventListener("change", renderLeadRows);
loadDashboard();
