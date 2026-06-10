const state = {
  accounts: [],
  followups: [],
  insights: null,
  selectedAccountId: null,
};

const els = {
  status: document.querySelector("#status"),
  refreshButton: document.querySelector("#refreshButton"),
  categoryFilter: document.querySelector("#categoryFilter"),
  totalAccounts: document.querySelector("#totalAccounts"),
  hotLeads: document.querySelector("#hotLeads"),
  highFollowups: document.querySelector("#highFollowups"),
  totalCalls: document.querySelector("#totalCalls"),
  leadCards: document.querySelector("#leadCards"),
  leadDetails: document.querySelector("#leadDetails"),
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
    state.selectedAccountId = state.accounts[0]?.account_id || null;

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
  renderLeadCards();
  renderLeadDetails();
  renderFollowups();
  renderCallInsights();
}

function renderKpis() {
  els.totalAccounts.textContent = state.accounts.length.toString();
  els.hotLeads.textContent = state.accounts.filter((item) => item.lead_score.category === "Hot").length.toString();
  els.highFollowups.textContent = state.accounts.filter((item) => item.follow_up.priority === "High").length.toString();
  els.totalCalls.textContent = (state.insights?.total_calls || 0).toString();
}

function renderLeadCards() {
  const category = els.categoryFilter.value;
  const rows = state.accounts
    .filter((item) => !category || item.lead_score.category === category)
    .sort((a, b) => b.lead_score.score - a.lead_score.score)
    .slice(0, 25);

  if (rows.length && !rows.some((item) => item.account_id === state.selectedAccountId)) {
    state.selectedAccountId = rows[0].account_id;
  }

  els.leadCards.innerHTML = rows
    .map((item) => {
      const why = item.lead_score.explanations?.[0] || "Score uses available CRM signals";
      const isSelected = item.account_id === state.selectedAccountId;
      return `
        <button class="lead-card ${isSelected ? "selected" : ""}" type="button" data-account-id="${escapeHtml(item.account_id)}">
          <span class="lead-card-top">
            <span>
              <strong>${escapeHtml(item.account_name || "Unnamed account")}</strong>
              <small>${escapeHtml(item.industry || "Unknown industry")} · ${escapeHtml(item.account_status || "No status")}</small>
            </span>
            <span class="score-badge ${item.lead_score.category}">${item.lead_score.score}</span>
          </span>
          <span class="lead-card-bottom">
            <span class="pill ${item.lead_score.category}">${item.lead_score.category}</span>
            <span>${escapeHtml(why)}</span>
          </span>
        </button>
      `;
    })
    .join("");

  if (!rows.length) {
    els.leadCards.innerHTML = `<div class="empty-state">No leads match this filter.</div>`;
    state.selectedAccountId = null;
  }

  els.leadCards.querySelectorAll(".lead-card").forEach((card) => {
    card.addEventListener("click", () => {
      state.selectedAccountId = card.dataset.accountId;
      renderLeadCards();
      renderLeadDetails();
    });
  });
}

function renderLeadDetails() {
  const item = state.accounts.find((account) => account.account_id === state.selectedAccountId);
  if (!item) {
    els.leadDetails.innerHTML = `<div class="empty-state">Select a lead card to view score factors.</div>`;
    return;
  }

  const metrics = item.metrics || {};
  const factors = scoreFactors(metrics);
  const comment = scoreComment(item);
  const maxFactorValue = Math.max(...factors.map((factor) => factor.value), 1);

  els.leadDetails.innerHTML = `
    <div class="detail-header">
      <div>
        <span class="eyebrow">Lead score details</span>
        <h3>${escapeHtml(item.account_name || "Unnamed account")}</h3>
      </div>
      <span class="score-ring ${item.lead_score.category}">${item.lead_score.score}</span>
    </div>

    <div class="score-comment ${item.lead_score.category}">
      <strong>${escapeHtml(comment.title)}</strong>
      <p>${escapeHtml(comment.body)}</p>
    </div>

    <div class="factor-grid">
      ${factors
        .map((factor) => {
          const width = Math.max(4, Math.round((factor.value / maxFactorValue) * 100));
          return `
            <div class="factor-row">
              <div>
                <span>${escapeHtml(factor.label)}</span>
                <strong>${escapeHtml(factor.display)}</strong>
              </div>
              <div class="factor-track"><span style="width: ${width}%"></span></div>
            </div>
          `;
        })
        .join("")}
    </div>

    <div class="explanation-block">
      <h4>Why this score</h4>
      <ul>
        ${(item.lead_score.explanations || ["Score uses available CRM signals"])
          .map((reason) => `<li>${escapeHtml(reason)}</li>`)
          .join("")}
      </ul>
    </div>

    <div class="explanation-block">
      <h4>Recommended action</h4>
      <p>${escapeHtml(item.follow_up.suggested_action)} · ${escapeHtml(item.follow_up.recommended_time)}</p>
      <ul>
        ${(item.follow_up.reasons || [])
          .map((reason) => `<li>${escapeHtml(reason)}</li>`)
          .join("")}
      </ul>
    </div>
  `;
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

function scoreFactors(metrics) {
  return [
    {
      label: "Total calls",
      value: metrics.total_calls || 0,
      display: `${metrics.total_calls || 0}`,
    },
    {
      label: "Average call duration",
      value: metrics.average_call_duration || 0,
      display: `${formatNumber(metrics.average_call_duration)} min`,
    },
    {
      label: "Sentiment score",
      value: Math.round(((metrics.average_sentiment || 0) + 1) * 50),
      display: formatNumber(metrics.average_sentiment),
    },
    {
      label: "Opportunities",
      value: metrics.opportunities_count || 0,
      display: `${metrics.opportunities_count || 0}`,
    },
    {
      label: "Recent activities",
      value: metrics.recent_activities_count || 0,
      display: `${metrics.recent_activities_count || 0}`,
    },
    {
      label: "Untouched days",
      value: metrics.untouched_since_days || 0,
      display: `${metrics.untouched_since_days || 0} days`,
    },
    {
      label: "Average call rating",
      value: metrics.average_call_rating || 0,
      display: `${formatNumber(metrics.average_call_rating)} / 5`,
    },
    {
      label: "Ticket count",
      value: metrics.ticket_count || 0,
      display: `${metrics.ticket_count || 0}`,
    },
  ];
}

function scoreComment(item) {
  const score = item.lead_score.score || 0;
  const category = item.lead_score.category;
  const untouched = item.metrics?.untouched_since_days || 0;
  const opportunities = item.metrics?.opportunities_count || 0;

  if (category === "Hot") {
    return {
      title: "Sales-ready lead",
      body:
        opportunities > 0
          ? "This account has strong conversion signals and linked opportunity activity. Prioritize it for a decisive next step."
          : "This account is highly engaged. Move quickly while momentum is still visible.",
    };
  }
  if (category === "Warm") {
    return {
      title: "Needs focused nurturing",
      body:
        untouched >= 14
          ? "The score is moderate, but inactivity is pulling it down. A timely follow-up can recover momentum."
          : "The account has useful signals, but not enough urgency yet. Validate need, budget, and timing.",
    };
  }
  return {
    title: "Low-priority or risk lead",
    body:
      score < 25
        ? "Signals are weak right now. Keep this in a light-touch nurture path unless new activity appears."
        : "This lead needs more engagement before it deserves sales priority.",
  };
}

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isInteger(number) ? number.toString() : number.toFixed(2);
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
els.categoryFilter.addEventListener("change", () => {
  renderLeadCards();
  renderLeadDetails();
});
loadDashboard();
