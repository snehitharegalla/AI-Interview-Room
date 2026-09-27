/**
 * Recruiter Hub & 7-Step Wizard Controller.
 */

let currentStep = 1;
const totalWizardSteps = 7;
let allQuestionBankItems = [];
let allCandidatesList = [];

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  const icon = type === 'error' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function getAuthHeaders() {
  const token = localStorage.getItem('auth_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Navigation between sidebar views
function switchRecruiterView(viewId, clickedEl = null) {
  document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
  const target = document.getElementById(`view-${viewId}`);
  if (target) target.classList.add('active');

  document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));
  if (clickedEl) {
    clickedEl.classList.add('active');
  } else {
    const link = document.querySelector(`.sidebar-link[onclick*="${viewId}"]`);
    if (link) link.classList.add('active');
  }

  const titleMap = {
    'dashboard': 'Recruiter Hub / Dashboard',
    'interviews': 'Recruiter Hub / Interview Management',
    'candidates': 'Recruiter Hub / Candidate Directory',
    'question-bank': 'Recruiter Hub / Question Bank',
    'reports': 'Recruiter Hub / Evaluation Reports',
    'analytics': 'Recruiter Hub / Analytics & Insights',
    'settings': 'Recruiter Hub / Settings'
  };
  const titleEl = document.getElementById('breadcrumbTitle');
  if (titleEl && titleMap[viewId]) titleEl.textContent = titleMap[viewId];

  if (viewId === 'dashboard') loadDashboard();
  else if (viewId === 'interviews') loadInterviews();
  else if (viewId === 'candidates') loadCandidates();
  else if (viewId === 'question-bank') loadQuestionBank();
  else if (viewId === 'reports') loadReports();
  else if (viewId === 'analytics') loadAnalytics();
}

// -------------------------------------------------------------
// DASHBOARD
// -------------------------------------------------------------
async function loadDashboard() {
  try {
    const res = await fetch('/api/recruiter/dashboard', { headers: getAuthHeaders() });
    if (res.status === 401 || res.status === 403) {
      // Auto demo login as Sarah Jenkins
      const demoRes = await fetch('/api/auth/demo-login?role=recruiter', { method: 'POST' });
      const demoData = await demoRes.json();
      localStorage.setItem('auth_token', demoData.access_token);
      localStorage.setItem('user_role', demoData.user.role);
      localStorage.setItem('user_name', demoData.user.full_name);
      return loadDashboard();
    }
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.error(err);
    showToast('Failed to load dashboard metrics.', 'error');
  }
}

function renderDashboard(data) {
  const m = data.metrics || {};
  document.getElementById('kpiTotalCandidates').textContent = m.total_candidates || 0;
  document.getElementById('kpiActiveInterviews').textContent = m.active_interviews || 0;
  document.getElementById('kpiCompletedInterviews').textContent = m.completed_interviews || 0;
  document.getElementById('kpiAverageScore').innerHTML = `${m.average_score || 0.0} <span style="font-size: 16px; color: var(--text-muted);">/ 10</span>`;

  const tbody = document.getElementById('recentInterviewsTableBody');
  const recents = data.recent_interviews || [];

  if (recents.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 30px;">No interviews scheduled yet. Click "+ Create Interview" to launch your first session.</td></tr>`;
    return;
  }

  tbody.innerHTML = recents.map(r => `
    <tr>
      <td>
        <div style="font-weight: 600;">${r.candidate_name}</div>
        <div style="font-size: 12px; color: var(--text-muted);">${r.candidate_email}</div>
      </td>
      <td>
        <div style="font-weight: 500;">${r.title}</div>
        <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">${r.id}</div>
      </td>
      <td>${r.job_role}</td>
      <td>
        <span class="status-badge ${r.status}">
          ● ${r.status === 'completed' ? 'Completed' : r.status === 'in_progress' ? 'In Progress' : 'Assigned'}
        </span>
      </td>
      <td>
        ${r.status === 'completed' ? `<span style="font-weight: 700; color: var(--color-basic); font-size: 15px;">${r.weighted_score}/10</span>` : '<span style="color: var(--text-muted);">-</span>'}
      </td>
      <td style="font-size: 13px; color: var(--text-secondary);">${r.started_at}</td>
      <td>
        ${r.report_url ? `<a href="${r.report_url}" class="btn btn-secondary btn-sm" style="font-size: 12px; padding: 6px 12px;">View Report ➔</a>` : `<span style="font-size: 12px; color: var(--text-muted);">In Progress</span>`}
      </td>
    </tr>
  `).join('');
}

// -------------------------------------------------------------
// INTERVIEWS LIST
// -------------------------------------------------------------
async function loadInterviews() {
  const status = document.getElementById('interviewStatusFilter').value;
  const search = document.getElementById('interviewSearchInput').value;

  try {
    const url = `/api/recruiter/interviews?status=${status}&search=${encodeURIComponent(search)}`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    const items = await res.json();
    const tbody = document.getElementById('allInterviewsTableBody');

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 36px;">No matching interviews found.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(r => `
      <tr>
        <td>
          <div style="font-weight: 600;">${r.candidate_name}</div>
          <div style="font-size: 12px; color: var(--text-muted);">${r.candidate_email}</div>
        </td>
        <td>
          <div style="font-weight: 500;">${r.title}</div>
          <div style="font-size: 11px; color: var(--accent-secondary); margin-top: 2px;">Topics: ${(r.topics || []).join(', ')}</div>
        </td>
        <td>${r.total_questions} Questions</td>
        <td>
          <span class="status-badge ${r.status}">● ${r.status}</span>
        </td>
        <td>
          ${r.status === 'completed' ? `<strong style="color: var(--color-basic); font-size: 15px;">${r.weighted_score}</strong>` : '-'}
        </td>
        <td style="font-size: 13px; color: var(--text-secondary);">${r.started_at}</td>
        <td>
          ${r.report_url ? `<a href="${r.report_url}" class="btn btn-secondary btn-sm" style="font-size: 12px; padding: 6px 12px;">Full Report ➔</a>` : `<span style="font-size: 12px; color: var(--text-muted);">Active Session</span>`}
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// CANDIDATES DIRECTORY
// -------------------------------------------------------------
async function loadCandidates() {
  const search = document.getElementById('candidateSearchInput').value;
  try {
    const url = `/api/recruiter/candidates?search=${encodeURIComponent(search)}`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    const items = await res.json();
    allCandidatesList = items;
    const tbody = document.getElementById('candidatesTableBody');

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 36px;">No candidate profiles found.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(c => `
      <tr>
        <td>
          <div style="font-weight: 600;">${c.name}</div>
          <div style="font-size: 12px; color: var(--text-muted);">${c.email}</div>
        </td>
        <td>${c.applied_role || c.job_role}</td>
        <td><span class="badge-tag">${c.experience_level}</span></td>
        <td><span class="status-badge ${c.status}">● ${c.status}</span></td>
        <td>
          ${c.latest_score !== null ? `<strong style="color: var(--color-basic); font-size: 15px;">${c.latest_score}/10</strong>` : '<span style="color: var(--text-muted);">-</span>'}
        </td>
        <td style="font-size: 13px; color: var(--text-secondary);">${c.interview_date}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="viewCandidateProfile(${c.id})" style="font-size: 12px; padding: 6px 12px;">
            Cognitive Profile ➔
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

// Candidate Profile Modal with Knowledge Map
async function viewCandidateProfile(candidateId) {
  try {
    const res = await fetch(`/api/recruiter/candidate/${candidateId}`, { headers: getAuthHeaders() });
    const data = await res.json();
    const c = data.candidate;

    document.getElementById('candModalName').textContent = `${c.name} — Technical Profile`;
    document.getElementById('candModalRole').textContent = `${c.job_role} • ${c.experience_level} • ${c.email}`;

    const body = document.getElementById('candModalBody');
    const kp = data.knowledge_profile || [];
    const strengths = data.strengths || [];
    const areas = data.areas_for_improvement || [];

    body.innerHTML = `
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 24px;">
        <div>
          <h4 style="font-size: 15px; margin-bottom: 12px;">Verified Cognitive Knowledge Profile</h4>
          ${kp.length === 0 ? '<p style="color: var(--text-muted); font-size: 13px;">No assessment attempts completed yet.</p>' : ''}
          <div style="display: flex; flex-direction: column; gap: 14px;">
            ${kp.map(k => `
              <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-glass); border-radius: 12px; padding: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <span style="font-weight: 600; font-size: 14px;">${k.topic}</span>
                  <span class="badge-tag badge-${k.level.toLowerCase() === 'strong' ? 'basic' : k.level.toLowerCase() === 'moderate' ? 'intermediate' : 'advanced'}">
                    ${k.level} (${k.mastery_score}%)
                  </span>
                </div>
                <div class="meter-bar">
                  <div class="meter-fill-intermediate" style="width: ${k.mastery_score}%;"></div>
                </div>
                ${k.demonstrated_concepts.length > 0 ? `
                  <div style="margin-top: 10px; font-size: 12px;">
                    <span style="color: var(--color-basic); font-weight: 600;">Demonstrated:</span>
                    <span style="color: var(--text-secondary);">${k.demonstrated_concepts.join(', ')}</span>
                  </div>
                ` : ''}
                ${k.missing_concepts.length > 0 ? `
                  <div style="margin-top: 4px; font-size: 12px;">
                    <span style="color: var(--color-danger); font-weight: 600;">Areas to Probe:</span>
                    <span style="color: var(--text-secondary);">${k.missing_concepts.join(', ')}</span>
                  </div>
                ` : ''}
              </div>
            `).join('')}
          </div>
        </div>

        <div>
          <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-glass); border-radius: 12px; padding: 18px; margin-bottom: 18px;">
            <h4 style="font-size: 14px; margin-bottom: 10px; color: var(--color-basic);">Top Strengths</h4>
            ${strengths.length === 0 ? '<p style="color: var(--text-muted); font-size: 12px;">None identified yet.</p>' : ''}
            <ul style="padding-left: 18px; font-size: 12px; color: var(--text-secondary); line-height: 1.6;">
              ${strengths.map(s => `<li>${s}</li>`).join('')}
            </ul>
          </div>

          <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-glass); border-radius: 12px; padding: 18px;">
            <h4 style="font-size: 14px; margin-bottom: 10px; color: var(--color-danger);">Areas for Improvement</h4>
            ${areas.length === 0 ? '<p style="color: var(--text-muted); font-size: 12px;">None recorded.</p>' : ''}
            <ul style="padding-left: 18px; font-size: 12px; color: var(--text-secondary); line-height: 1.6;">
              ${areas.map(a => `<li>${a}</li>`).join('')}
            </ul>
          </div>
        </div>
      </div>

      <div>
        <h4 style="font-size: 15px; margin-bottom: 10px;">Interview History</h4>
        <table class="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Score</th>
              <th>Date</th>
              <th>Report</th>
            </tr>
          </thead>
          <tbody>
            ${(data.interview_history || []).map(h => `
              <tr>
                <td>${h.title}</td>
                <td><span class="status-badge ${h.status}">● ${h.status}</span></td>
                <td><strong>${h.weighted_score > 0 ? `${h.weighted_score}/10` : '-'}</strong></td>
                <td>${h.started_at}</td>
                <td>
                  ${h.report_url ? `<a href="${h.report_url}" class="btn btn-secondary btn-sm" style="font-size: 11px; padding: 4px 10px;">Open Report</a>` : '-'}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('candidateProfileModal').classList.add('active');
  } catch (err) {
    console.error(err);
    showToast('Could not load candidate profile.', 'error');
  }
}

function closeCandidateProfileModal() {
  document.getElementById('candidateProfileModal').classList.remove('active');
}

// -------------------------------------------------------------
// -------------------------------------------------------------
// QUESTION BANK
// -------------------------------------------------------------
async function loadQuestionBank() {
  const search = document.getElementById('qBankSearch').value;
  const topic = document.getElementById('qBankTopicFilter').value;
  const difficulty = document.getElementById('qBankDifficultyFilter').value;
  const qType = document.getElementById('qBankTypeFilter').value;
  const roleEl = document.getElementById('qBankRoleFilter');
  const role = roleEl ? roleEl.value : 'all';

  try {
    const url = `/api/question-bank?search=${encodeURIComponent(search)}&topic=${topic}&difficulty=${difficulty}&question_type=${qType}&job_role=${encodeURIComponent(role)}`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    const items = await res.json();
    allQuestionBankItems = items;
    const container = document.getElementById('qBankItemsContainer');

    if (items.length === 0) {
      container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📚</div><div class="empty-state-title">No questions found</div><div class="empty-state-text">Adjust filters or create a new question for the bank.</div></div>`;
      return;
    }

    container.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 16px;">
        ${items.map(item => `
          <div class="glass-card" style="padding: 20px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                <h4 style="font-size: 15px; font-weight: 600; line-height: 1.3;">${item.title}</h4>
                <div style="display: flex; gap: 6px; flex-shrink: 0;">
                  <span class="badge-tag badge-${item.difficulty}">${item.difficulty}</span>
                  <span class="badge-tag">${item.question_type}</span>
                </div>
              </div>
              <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">
                ${item.question_text}
              </p>
              ${item.target_concept ? `
                <div style="font-size: 11px; color: var(--accent-secondary); margin-bottom: 8px;">
                  🎯 <strong>Target Concept:</strong> ${item.target_concept}
                </div>
              ` : ''}
              <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">
                👤 <strong>Role:</strong> ${item.job_role || 'General Software Engineer'}
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid var(--border-glass); margin-top: 8px; flex-wrap: wrap; gap: 8px;">
              <span style="font-size: 12px; color: var(--text-muted);">Topic: <strong>${item.topic}</strong></span>
              <div style="display: flex; gap: 6px;">
                <button class="btn btn-secondary btn-sm" onclick="openPreviewQuestionModal(${item.id})" title="Preview question" style="padding: 4px 8px; font-size: 11px;">👁️ Preview</button>
                <button class="btn btn-secondary btn-sm" onclick="openEditQuestionModal(${item.id})" title="Edit question" style="padding: 4px 8px; font-size: 11px;">✏️ Edit</button>
                <button class="btn btn-secondary btn-sm" onclick="duplicateQuestion(${item.id})" title="Duplicate question" style="padding: 4px 8px; font-size: 11px;">📋 Duplicate</button>
                <button class="btn btn-secondary btn-sm" onclick="deleteQuestion(${item.id})" title="Delete question" style="padding: 4px 8px; font-size: 11px; color: var(--color-danger);">🗑️</button>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    console.error(err);
  }
}

function openAddQuestionModal() {
  document.getElementById('addQuestionModal').classList.add('active');
}

function closeAddQuestionModal() {
  document.getElementById('addQuestionModal').classList.remove('active');
}

function openPreviewQuestionModal(id) {
  const item = allQuestionBankItems.find(q => q.id === id);
  if (!item) {
    fetch(`/api/question-bank/${id}`, { headers: getAuthHeaders() })
      .then(r => r.json())
      .then(populateAndShowPreview)
      .catch(() => showToast('Could not load question details.', 'error'));
    return;
  }
  populateAndShowPreview(item);
}

function populateAndShowPreview(item) {
  document.getElementById('prevQBadgeType').textContent = item.question_type || 'Technical';
  document.getElementById('prevQTitle').textContent = item.title;
  document.getElementById('prevQTopic').textContent = `Topic: ${item.topic}`;
  document.getElementById('prevQDifficulty').textContent = `Difficulty: ${item.difficulty.toUpperCase()}`;
  document.getElementById('prevQRole').textContent = `Target: ${item.job_role || 'Software Engineer'}`;
  document.getElementById('prevQText').textContent = item.question_text;

  const conceptBox = document.getElementById('prevQTargetConceptBox');
  if (item.target_concept) {
    conceptBox.style.display = 'block';
    document.getElementById('prevQTargetConcept').textContent = item.target_concept;
  } else {
    conceptBox.style.display = 'none';
  }

  const keyPointsList = document.getElementById('prevQKeyPointsList');
  const points = item.expected_key_points || [];
  if (points.length > 0) {
    document.getElementById('prevQKeyPointsBox').style.display = 'block';
    keyPointsList.innerHTML = points.map(p => `<li>${p}</li>`).join('');
  } else {
    keyPointsList.innerHTML = `<li>Core mechanism explanation</li><li>Operational and runtime tradeoffs</li>`;
  }

  document.getElementById('previewQuestionModal').classList.add('active');
}

function closePreviewQuestionModal() {
  document.getElementById('previewQuestionModal').classList.remove('active');
}

function openEditQuestionModal(id) {
  const item = allQuestionBankItems.find(q => q.id === id);
  if (!item) return;

  document.getElementById('editQId').value = item.id;
  document.getElementById('editQTitle').value = item.title;
  document.getElementById('editQText').value = item.question_text;
  document.getElementById('editQTopic').value = item.topic;
  document.getElementById('editQDifficulty').value = item.difficulty;
  document.getElementById('editQType').value = item.question_type || 'Technical';
  document.getElementById('editQJobRole').value = item.job_role || 'Software Engineer';
  document.getElementById('editQTargetConcept').value = item.target_concept || '';

  document.getElementById('editQuestionModal').classList.add('active');
}

function closeEditQuestionModal() {
  document.getElementById('editQuestionModal').classList.remove('active');
}

async function handleSaveEditQuestion(e) {
  e.preventDefault();
  const id = document.getElementById('editQId').value;
  const btn = document.getElementById('btnSaveEditQuestion');
  btn.disabled = true;
  btn.textContent = 'Saving...';

  const payload = {
    title: document.getElementById('editQTitle').value.trim(),
    question_text: document.getElementById('editQText').value.trim(),
    topic: document.getElementById('editQTopic').value.trim(),
    difficulty: document.getElementById('editQDifficulty').value,
    question_type: document.getElementById('editQType').value,
    job_role: document.getElementById('editQJobRole').value.trim(),
    target_concept: document.getElementById('editQTargetConcept').value.trim()
  };

  try {
    const res = await fetch(`/api/question-bank/${id}`, {
      method: 'PUT',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast('Question updated successfully!', 'success');
      closeEditQuestionModal();
      loadQuestionBank();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Failed to update question.', 'error');
    }
  } catch (err) {
    showToast('Failed to connect to server.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Save Changes';
  }
}

function previewWizardStarterQuestion() {
  const sel = document.getElementById('wzStarterQuestion');
  if (!sel || !sel.value) return;
  if (sel.value === 'auto') {
    showToast('Auto-Generate mode: The AI will generate a tailored benchmark question based on candidate profile and selected topics.', 'info');
    return;
  }
  openPreviewQuestionModal(parseInt(sel.value));
}

async function testAiConnection() {
  const resSpan = document.getElementById('aiTestResult');
  const btn = document.getElementById('btnTestAiConnection');
  btn.disabled = true;
  btn.textContent = 'Testing...';
  resSpan.textContent = '';

  const t0 = performance.now();
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    const t1 = performance.now();
    const ms = Math.round(t1 - t0);
    if (res.ok) {
      resSpan.textContent = `✓ Connected: ${data.provider.toUpperCase()} Engine (${ms}ms latency)`;
      resSpan.style.color = 'var(--color-basic)';
      document.getElementById('settingsAiProvider').textContent = `● ${data.provider.toUpperCase()} Active`;
      showToast(`AI Engine connectivity verified (${ms}ms)`, 'success');
    } else {
      resSpan.textContent = '⚠️ Service degraded';
      resSpan.style.color = 'var(--color-warning)';
    }
  } catch (err) {
    resSpan.textContent = '✕ Connection failed';
    resSpan.style.color = 'var(--color-danger)';
  } finally {
    btn.disabled = false;
    btn.textContent = '⚡ Test Engine Health & Latency';
  }
}

async function duplicateQuestion(id) {
  try {
    const res = await fetch(`/api/question-bank/${id}/duplicate`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (res.ok) {
      showToast('Question duplicated successfully!', 'success');
      loadQuestionBank();
    }
  } catch (err) {
    showToast('Failed to duplicate question.', 'error');
  }
}

async function deleteQuestion(id) {
  if (!confirm('Are you sure you want to remove this question from the bank?')) return;
  try {
    const res = await fetch(`/api/question-bank/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (res.ok) {
      showToast('Question deleted.', 'info');
      loadQuestionBank();
    }
  } catch (err) {
    showToast('Delete failed.', 'error');
  }
}

// -------------------------------------------------------------
// REPORTS DIRECTORY
// -------------------------------------------------------------
async function loadReports() {
  try {
    const res = await fetch('/api/recruiter/interviews?status=completed', { headers: getAuthHeaders() });
    const items = await res.json();
    const tbody = document.getElementById('reportsTableBody');

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 36px;">No evaluation reports generated yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(r => `
      <tr>
        <td>
          <div style="font-weight: 600;">${r.candidate_name}</div>
          <div style="font-size: 12px; color: var(--text-muted);">${r.job_role}</div>
        </td>
        <td>
          <div style="font-weight: 500;">${r.title}</div>
          <div style="font-size: 11px; color: var(--text-muted);">${r.id}</div>
        </td>
        <td>
          <span class="badge-tag badge-basic">Candidate Evaluated</span>
        </td>
        <td style="font-size: 14px;">${r.weighted_score}/10</td>
        <td>
          <strong style="color: var(--color-basic); font-size: 16px;">${r.weighted_score}/10</strong>
        </td>
        <td style="font-size: 13px; color: var(--text-secondary);">${r.completed_at || r.started_at}</td>
        <td>
          <a href="${r.report_url}" class="btn btn-primary btn-sm" style="font-size: 12px; padding: 6px 14px;">
            Open Report ➔
          </a>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// ANALYTICS
// -------------------------------------------------------------
async function loadAnalytics() {
  try {
    const res = await fetch('/api/recruiter/analytics', { headers: getAuthHeaders() });
    const data = await res.json();
    const s = data.summary || {};

    document.getElementById('analyticsCompletionRate').textContent = `${s.completion_rate || 0}%`;
    document.getElementById('analyticsEvaluatedCount').textContent = s.completed_interviews || 0;
    document.getElementById('analyticsAvgDepthScore').textContent = `${s.average_score || 0.0} / 10`;

    // Topic performance bars
    const topicContainer = document.getElementById('analyticsTopicBars');
    const topics = data.topic_performance || [];
    if (topics.length === 0) {
      topicContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 13px;">No completed interviews to display topic distributions.</p>`;
    } else {
      topicContainer.innerHTML = topics.map(t => `
        <div style="margin-bottom: 14px;">
          <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 500; margin-bottom: 4px;">
            <span>${t.topic}</span>
            <span style="color: var(--color-intermediate); font-weight: 600;">${t.average_score}/10 (${t.sample_count} evals)</span>
          </div>
          <div class="meter-bar">
            <div class="meter-fill-intermediate" style="width: ${t.average_score * 10}%;"></div>
          </div>
        </div>
      `).join('');
    }

    // Difficulty distribution bars
    const diffContainer = document.getElementById('analyticsDifficultyBars');
    const diff = data.difficulty_distribution || {};
    const totalDiff = (diff.basic || 0) + (diff.intermediate || 0) + (diff.advanced || 0) || 1;

    diffContainer.innerHTML = `
      <div style="margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 500; margin-bottom: 4px;">
          <span>Basic / Fundamentals</span>
          <span style="color: var(--color-basic); font-weight: 600;">${diff.basic || 0} questions</span>
        </div>
        <div class="meter-bar">
          <div class="meter-fill-basic" style="width: ${((diff.basic || 0) / totalDiff) * 100}%;"></div>
        </div>
      </div>
      <div style="margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 500; margin-bottom: 4px;">
          <span>Intermediate</span>
          <span style="color: var(--color-intermediate); font-weight: 600;">${diff.intermediate || 0} questions</span>
        </div>
        <div class="meter-bar">
          <div class="meter-fill-intermediate" style="width: ${((diff.intermediate || 0) / totalDiff) * 100}%;"></div>
        </div>
      </div>
      <div style="margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 500; margin-bottom: 4px;">
          <span>Advanced Architectural</span>
          <span style="color: var(--color-advanced); font-weight: 600;">${diff.advanced || 0} questions</span>
        </div>
        <div class="meter-bar">
          <div class="meter-fill-advanced" style="width: ${((diff.advanced || 0) / totalDiff) * 100}%;"></div>
        </div>
      </div>
    `;
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// 7-STEP INTERVIEW CREATION WIZARD LOGIC
// -------------------------------------------------------------
function openWizardModal() {
  currentStep = 1;
  updateWizardUI();
  populateWizardCandidates();
  populateWizardQuestions();
  document.getElementById('wizardModal').classList.add('active');
}

function closeWizardModal() {
  document.getElementById('wizardModal').classList.remove('active');
}

function updateWizardUI() {
  // Update step indicators
  for (let i = 1; i <= totalWizardSteps; i++) {
    const indicator = document.getElementById(`wizardStepIndicator-${i}`);
    const content = document.getElementById(`wizardStep-${i}`);
    if (indicator) {
      indicator.className = i === currentStep ? 'step-item active' : i < currentStep ? 'step-item completed' : 'step-item';
    }
    if (content) {
      content.className = i === currentStep ? 'step-content active' : 'step-content';
    }
  }

  // Buttons
  const prevBtn = document.getElementById('wzPrevBtn');
  const nextBtn = document.getElementById('wzNextBtn');

  if (prevBtn) prevBtn.style.display = currentStep > 1 ? 'inline-block' : 'none';
  if (nextBtn) {
    nextBtn.textContent = currentStep === totalWizardSteps ? 'Launch Interview 🚀' : 'Next Step ➔';
  }

  if (currentStep === totalWizardSteps) {
    compileWizardReview();
  }
}

function wizardNextStep() {
  // Validate current step
  if (currentStep === 1) {
    const title = document.getElementById('wzTitle').value.trim();
    const role = document.getElementById('wzJobRole').value.trim();
    if (!title || !role) {
      showToast('Please provide an interview title and job role.', 'error');
      return;
    }
  } else if (currentStep === 2) {
    const selectedTopics = getSelectedTopics();
    if (selectedTopics.length === 0) {
      showToast('Please select at least one technical topic.', 'error');
      return;
    }
  } else if (currentStep === totalWizardSteps) {
    submitWizardInterview();
    return;
  }

  currentStep++;
  updateWizardUI();
}

function wizardPrevStep() {
  if (currentStep > 1) {
    currentStep--;
    updateWizardUI();
  }
}

function getSelectedTopics() {
  const chips = document.querySelectorAll('#wzTopicsContainer .topic-chip.active');
  return Array.from(chips).map(c => c.getAttribute('data-topic'));
}

function addCustomWizardTopic() {
  const input = document.getElementById('wzCustomTopicInput');
  const topic = input.value.trim();
  if (!topic) return;

  const container = document.getElementById('wzTopicsContainer');
  const chip = document.createElement('div');
  chip.className = 'topic-chip active';
  chip.setAttribute('data-topic', topic);
  chip.textContent = topic;
  chip.addEventListener('click', () => chip.classList.toggle('active'));
  container.appendChild(chip);

  input.value = '';
}

function populateWizardCandidates() {
  const select = document.getElementById('wzSelectExistingCandidate');
  if (!select) return;
  fetch('/api/recruiter/candidates', { headers: getAuthHeaders() })
    .then(res => res.json())
    .then(candidates => {
      select.innerHTML = '<option value="">-- Or enter new candidate below --</option>' +
        candidates.map(c => `<option value="${c.id}" data-name="${c.name}" data-email="${c.email}" data-role="${c.job_role}">${c.name} (${c.job_role})</option>`).join('');
    });

  select.addEventListener('change', () => {
    const selectedOption = select.options[select.selectedIndex];
    if (selectedOption.value) {
      document.getElementById('wzCandidateName').value = selectedOption.getAttribute('data-name');
      document.getElementById('wzCandidateEmail').value = selectedOption.getAttribute('data-email');
    }
  });
}

function populateWizardQuestions() {
  const select = document.getElementById('wzStarterQuestion');
  if (!select) return;
  fetch('/api/question-bank', { headers: getAuthHeaders() })
    .then(res => res.json())
    .then(questions => {
      select.innerHTML = '<option value="auto">Auto-Generate Baseline with AI (Recommended)</option>' +
        questions.map(q => `<option value="${q.id}">[${q.topic} - ${q.difficulty}] ${q.title}</option>`).join('');
    });
}

function compileWizardReview() {
  document.getElementById('revTitle').textContent = document.getElementById('wzTitle').value || 'Adaptive Technical Assessment';
  document.getElementById('revRole').textContent = document.getElementById('wzJobRole').value || 'Software Engineer';
  document.getElementById('revExp').textContent = document.getElementById('wzExpLevel').value;
  document.getElementById('revTopics').textContent = getSelectedTopics().join(', ');
  document.getElementById('revDifficulty').textContent = `${document.getElementById('wzDifficulty').value.toUpperCase()} (${document.getElementById('wzDifficultyRange').value})`;
  document.getElementById('revQuestions').textContent = `${document.getElementById('wzTotalQuestions').value} Questions (${document.getElementById('wzDuration').value} Minutes)`;

  const candName = document.getElementById('wzCandidateName').value.trim() || 'Assigned Candidate';
  const candEmail = document.getElementById('wzCandidateEmail').value.trim() || 'candidate@example.com';
  document.getElementById('revCandidate').textContent = `${candName} (${candEmail})`;
}

async function submitWizardInterview() {
  const nextBtn = document.getElementById('wzNextBtn');
  nextBtn.disabled = true;
  nextBtn.textContent = 'Generating & Initializing...';

  const categories = Array.from(document.querySelectorAll('.wz-cat-check:checked')).map(c => c.value);
  const starterQVal = document.getElementById('wzStarterQuestion').value;
  const selectedQIds = starterQVal !== 'auto' ? [parseInt(starterQVal)] : [];

  const payload = {
    title: document.getElementById('wzTitle').value.trim(),
    job_role: document.getElementById('wzJobRole').value.trim(),
    experience_level: document.getElementById('wzExpLevel').value,
    description: document.getElementById('wzDescription').value.trim(),
    topics: getSelectedTopics(),
    difficulty: document.getElementById('wzDifficulty').value,
    difficulty_range: document.getElementById('wzDifficultyRange').value,
    total_questions: parseInt(document.getElementById('wzTotalQuestions').value),
    duration_minutes: parseInt(document.getElementById('wzDuration').value),
    adaptive_mode: document.getElementById('wzAdaptiveMode').checked ? 'enabled' : 'disabled',
    allow_followups: document.getElementById('wzAllowFollowups').checked,
    prevent_repeated: document.getElementById('wzPreventRepeated').checked,
    question_categories: categories.length > 0 ? categories : ['Technical', 'Conceptual'],
    selected_question_ids: selectedQIds,
    candidate_name: document.getElementById('wzCandidateName').value.trim() || 'New Candidate',
    candidate_email: document.getElementById('wzCandidateEmail').value.trim() || 'candidate@example.com'
  };

  try {
    const res = await fetch('/api/recruiter/interviews', {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
      showToast('Interview successfully created and assigned to candidate!', 'success');
      closeWizardModal();
      loadDashboard();
      loadInterviews();
    } else {
      showToast(data.detail || 'Failed to create interview.', 'error');
    }
  } catch (err) {
    showToast('Failed to create interview.', 'error');
  } finally {
    nextBtn.disabled = false;
    nextBtn.textContent = 'Next Step ➔';
  }
}

// -------------------------------------------------------------
// NOTIFICATIONS
// -------------------------------------------------------------
async function loadRecruiterNotifications() {
  try {
    const res = await fetch('/api/notifications?role=recruiter', { headers: getAuthHeaders() });
    const notifs = await res.json();
    const badge = document.getElementById('recNotifBadge');
    const list = document.getElementById('recNotifsList');

    const unread = notifs.filter(n => !n.read).length;
    if (badge) badge.textContent = unread;

    if (!list) return;
    if (notifs.length === 0) {
      list.innerHTML = `<div style="padding: 16px; text-align: center; color: var(--text-muted); font-size: 13px;">No notifications.</div>`;
      return;
    }

    list.innerHTML = notifs.map(n => `
      <a href="${n.link || '#'}" class="notif-item ${n.read ? '' : 'unread'}">
        <div style="font-weight: 600; margin-bottom: 2px;">${n.title}</div>
        <div style="color: var(--text-secondary); font-size: 12px;">${n.message}</div>
        <div style="color: var(--text-muted); font-size: 10px; margin-top: 4px;">${new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
      </a>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

async function markAllNotificationsRead(e) {
  if (e) e.preventDefault();
  try {
    await fetch('/api/notifications/read-all?role=recruiter', { method: 'POST', headers: getAuthHeaders() });
    document.getElementById('recNotifBadge').textContent = '0';
    document.querySelectorAll('.notif-item').forEach(el => el.classList.remove('unread'));
    showToast('Notifications marked as read.', 'success');
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// INITIALIZATION
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  loadRecruiterNotifications();

  // Check health for settings
  fetch('/api/health')
    .then(r => r.json())
    .then(h => {
      const el = document.getElementById('settingsAiProvider');
      if (el) el.textContent = `Active (${h.provider})`;
    });

  // Launch wizard trigger
  const launchBtn = document.getElementById('btnLaunchWizard');
  if (launchBtn) launchBtn.addEventListener('click', openWizardModal);

  // Logout trigger
  const logoutBtn = document.getElementById('btnRecruiterLogout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      localStorage.clear();
      window.location.href = '/';
    });
  }

  // Notif Bell dropdown
  const notifToggle = document.getElementById('btnRecNotifsToggle');
  const notifDropdown = document.getElementById('recNotifDropdown');
  if (notifToggle && notifDropdown) {
    notifToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      notifDropdown.classList.toggle('active');
    });
    document.addEventListener('click', (e) => {
      if (!notifDropdown.contains(e.target) && e.target !== notifToggle) {
        notifDropdown.classList.remove('active');
      }
    });
  }

  // Filter input listeners
  const intSearch = document.getElementById('interviewSearchInput');
  const intFilter = document.getElementById('interviewStatusFilter');
  if (intSearch) intSearch.addEventListener('input', loadInterviews);
  if (intFilter) intFilter.addEventListener('change', loadInterviews);

  const candSearch = document.getElementById('candidateSearchInput');
  if (candSearch) candSearch.addEventListener('input', loadCandidates);

  const qbSearch = document.getElementById('qBankSearch');
  const qbTopic = document.getElementById('qBankTopicFilter');
  const qbDiff = document.getElementById('qBankDifficultyFilter');
  const qbType = document.getElementById('qBankTypeFilter');
  const qbRole = document.getElementById('qBankRoleFilter');
  if (qbSearch) qbSearch.addEventListener('input', loadQuestionBank);
  if (qbTopic) qbTopic.addEventListener('change', loadQuestionBank);
  if (qbDiff) qbDiff.addEventListener('change', loadQuestionBank);
  if (qbType) qbType.addEventListener('change', loadQuestionBank);
  if (qbRole) qbRole.addEventListener('change', loadQuestionBank);

  // Topic chip click listeners in wizard
  document.querySelectorAll('#wzTopicsContainer .topic-chip').forEach(chip => {
    chip.addEventListener('click', () => chip.classList.toggle('active'));
  });

  // Add Question form
  const addQForm = document.getElementById('addQuestionForm');
  if (addQForm) {
    addQForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        title: document.getElementById('qTitle').value.trim(),
        question_text: document.getElementById('qText').value.trim(),
        topic: document.getElementById('qTopic').value.trim(),
        difficulty: document.getElementById('qDifficulty').value,
        question_type: document.getElementById('qType').value,
        job_role: document.getElementById('qJobRole').value.trim(),
        target_concept: document.getElementById('qTargetConcept').value.trim()
      };

      try {
        const res = await fetch('/api/question-bank', {
          method: 'POST',
          headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          showToast('Question added to bank!', 'success');
          closeAddQuestionModal();
          loadQuestionBank();
          addQForm.reset();
        } else {
          showToast('Failed to save question.', 'error');
        }
      } catch (err) {
        showToast('Connection error.', 'error');
      }
    });
  }
});
