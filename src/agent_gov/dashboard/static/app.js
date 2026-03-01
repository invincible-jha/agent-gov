/* agent-gov compliance dashboard — vanilla JS + Chart.js */
'use strict';

// ---------------------------------------------------------------------------
// Tab navigation
// ---------------------------------------------------------------------------
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + target).classList.add('active');
    refreshActiveTab(target);
  });
});

function refreshActiveTab(tab) {
  if (tab === 'policies') loadPolicies();
  else if (tab === 'audit') loadAudit();
  else if (tab === 'compliance') loadCompliance();
  else if (tab === 'frameworks') loadFrameworks();
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
function escHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function resultBadge(result) {
  const map = {
    pass: 'badge-pass',
    fail: 'badge-fail',
    skip: 'badge-skip',
  };
  const cls = map[String(result).toLowerCase()] || 'badge-warning';
  return `<span class="badge ${cls}">${escHtml(result)}</span>`;
}

function passRateBar(rate) {
  const pct = Math.round((Number(rate) || 0) * 100);
  const color = pct >= 80 ? 'var(--success)' : pct >= 50 ? 'var(--warning)' : 'var(--danger)';
  return `<div style="display:flex;align-items:center;gap:8px">
    <div style="flex:1;height:6px;background:var(--surface2);border-radius:3px">
      <div style="height:100%;width:${pct}%;background:${color};border-radius:3px"></div>
    </div>
    <span style="color:${color};font-weight:600;min-width:36px">${pct}%</span>
  </div>`;
}

async function apiFetch(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return res.json();
}

function showToast(msg) {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

function setLastRefresh() {
  document.getElementById('last-refresh').textContent =
    'Refreshed ' + new Date().toLocaleTimeString();
}

// ---------------------------------------------------------------------------
// Policy Rules Tab
// ---------------------------------------------------------------------------
async function loadPolicies() {
  try {
    const data = await apiFetch('/api/policies');

    document.getElementById('qs-policies').textContent = data.total_policies || 0;
    document.getElementById('qs-evidence').textContent = data.total_evidence || 0;
    const passRatePct = Math.round((data.global_pass_rate || 0) * 100);
    document.getElementById('qs-passrate').textContent = passRatePct + '%';
    document.getElementById('qs-fails').textContent = data.global_fail_count || 0;

    const tbody = document.getElementById('policies-tbody');
    const policies = data.policies || [];
    if (policies.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No policies evaluated yet.</td></tr>';
      setLastRefresh();
      return;
    }

    tbody.innerHTML = policies.map(p => `
      <tr>
        <td style="font-weight:600;font-family:monospace">${escHtml(p.policy_id)}</td>
        <td>${resultBadge(p.status)}</td>
        <td style="color:var(--success);font-weight:600">${p.pass}</td>
        <td style="color:var(--danger);font-weight:600">${p.fail}</td>
        <td style="color:var(--warning)">${p.skip}</td>
        <td>${p.total}</td>
        <td style="min-width:160px">${passRateBar(p.pass_rate)}</td>
      </tr>
    `).join('');
    setLastRefresh();
  } catch (err) {
    showToast('Error loading policies: ' + err.message);
  }
}

// ---------------------------------------------------------------------------
// Audit Log Tab
// ---------------------------------------------------------------------------
async function loadAudit() {
  try {
    const policy = document.getElementById('audit-policy-filter').value.trim();
    const rule = document.getElementById('audit-rule-filter').value.trim();
    const result = document.getElementById('audit-result-filter').value;

    let url = '/api/audit?limit=200';
    if (policy) url += '&policy_id=' + encodeURIComponent(policy);
    if (rule) url += '&rule_id=' + encodeURIComponent(rule);
    if (result) url += '&result=' + encodeURIComponent(result);

    const data = await apiFetch(url);
    const entries = data.entries || [];
    const tbody = document.getElementById('audit-tbody');

    if (entries.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No audit entries found.</td></tr>';
      setLastRefresh();
      return;
    }

    tbody.innerHTML = entries.slice().reverse().map(e => {
      const contextStr = e.context && Object.keys(e.context).length > 0
        ? JSON.stringify(e.context).slice(0, 60) + (JSON.stringify(e.context).length > 60 ? '…' : '')
        : '-';
      return `
        <tr>
          <td style="white-space:nowrap;font-size:12px">${escHtml(String(e.timestamp || '-').slice(0, 19))}</td>
          <td style="font-family:monospace;font-size:12px">${escHtml(e.policy_id || '-')}</td>
          <td style="font-family:monospace;font-size:12px">${escHtml(e.rule_id || '-')}</td>
          <td>${resultBadge(e.result || '-')}</td>
          <td style="color:var(--text-muted);font-size:12px">${escHtml(contextStr)}</td>
        </tr>
      `;
    }).join('');
    setLastRefresh();
  } catch (err) {
    showToast('Error loading audit log: ' + err.message);
  }
}

// ---------------------------------------------------------------------------
// Compliance Posture Tab — gauge chart
// ---------------------------------------------------------------------------
let gaugeChart = null;

async function loadCompliance() {
  try {
    const data = await apiFetch('/api/compliance');

    // Score — handle different field names from scorer
    const score = Number(
      data.overall_score ?? data.score ?? data.posture_score ?? 0
    );
    const scorePct = Math.round(score * 100);
    const scoreColor = scorePct >= 80 ? '#10b981' : scorePct >= 50 ? '#f59e0b' : '#ef4444';

    document.getElementById('gauge-pct').textContent = scorePct + '%';
    document.getElementById('gauge-pct').style.color = scoreColor;

    // Draw gauge using Chart.js doughnut
    const ctx = document.getElementById('gauge-chart').getContext('2d');
    if (gaugeChart) gaugeChart.destroy();
    gaugeChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [scorePct, 100 - scorePct],
          backgroundColor: [scoreColor, 'rgba(255,255,255,0.08)'],
          borderWidth: 0,
          circumference: 180,
          rotation: -90,
        }],
      },
      options: {
        responsive: false,
        cutout: '75%',
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
      },
    });

    // Details table
    const tbody = document.getElementById('posture-tbody');
    const rows = [
      ['Overall Score', scorePct + '%'],
      ['Total Checks', data.total_checks ?? data.total ?? '-'],
      ['Passing', data.passing ?? data.pass_count ?? '-'],
      ['Failing', data.failing ?? data.fail_count ?? '-'],
      ['Skipped', data.skipped ?? data.skip_count ?? '-'],
      ['Policies Evaluated', Object.keys(data.framework_coverage || {}).length],
    ];
    tbody.innerHTML = rows.map(([k, v]) => `
      <tr>
        <td style="color:var(--text-muted)">${k}</td>
        <td style="font-weight:700">${v}</td>
      </tr>
    `).join('');
    setLastRefresh();
  } catch (err) {
    showToast('Error loading compliance: ' + err.message);
  }
}

// ---------------------------------------------------------------------------
// Framework Coverage Tab
// ---------------------------------------------------------------------------
let frameworkBarChart = null;

async function loadFrameworks() {
  try {
    const data = await apiFetch('/api/compliance');
    const coverage = data.framework_coverage || {};
    const frameworks = Object.keys(coverage);

    const tbody = document.getElementById('framework-tbody');
    if (frameworks.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No framework data available.</td></tr>';
      setLastRefresh();
      return;
    }

    tbody.innerHTML = frameworks.map(fw => {
      const info = coverage[fw] || {};
      const pct = Number(info.coverage_pct || 0);
      const barWidth = Math.round(pct * 0.8); // max 80px
      const color = pct >= 80 ? 'var(--success)' : pct >= 50 ? 'var(--warning)' : 'var(--danger)';
      const status = pct >= 80 ? 'pass' : pct >= 50 ? 'skip' : 'fail';
      return `
        <tr>
          <td style="font-weight:600;font-family:monospace">${escHtml(fw)}</td>
          <td style="text-align:center">${info.total || 0}</td>
          <td style="text-align:center;color:var(--success);font-weight:600">${info.pass || 0}</td>
          <td style="text-align:center">
            <div style="display:flex;align-items:center;gap:8px;justify-content:center">
              <div style="height:6px;width:${barWidth}px;background:${color};border-radius:3px"></div>
              <span style="color:${color};font-weight:600">${pct}%</span>
            </div>
          </td>
          <td style="text-align:center">${resultBadge(status)}</td>
        </tr>
      `;
    }).join('');

    // Bar chart
    const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text').trim();
    const mutedColor = getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim();
    const coverageValues = frameworks.map(fw => Number((coverage[fw] || {}).coverage_pct || 0));
    const bgColors = coverageValues.map(v =>
      v >= 80 ? 'rgba(16,185,129,0.7)' : v >= 50 ? 'rgba(245,158,11,0.7)' : 'rgba(239,68,68,0.7)'
    );

    const ctx = document.getElementById('framework-bar-chart').getContext('2d');
    if (frameworkBarChart) frameworkBarChart.destroy();
    frameworkBarChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: frameworks,
        datasets: [{
          label: 'Coverage %',
          data: coverageValues,
          backgroundColor: bgColors,
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: textColor } } },
        scales: {
          x: {
            ticks: { color: mutedColor },
            grid: { color: 'rgba(255,255,255,0.05)' },
          },
          y: {
            min: 0,
            max: 100,
            ticks: { color: mutedColor, callback: v => v + '%' },
            grid: { color: 'rgba(255,255,255,0.05)' },
          },
        },
      },
    });
    setLastRefresh();
  } catch (err) {
    showToast('Error loading frameworks: ' + err.message);
  }
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
loadPolicies();
setInterval(() => {
  const active = document.querySelector('.tab-btn.active');
  if (active) refreshActiveTab(active.dataset.tab);
}, 30000);
