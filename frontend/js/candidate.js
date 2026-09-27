/**
 * Candidate Portal Controller.
 * Manages dashboard state, assigned assessments, and start/resume actions.
 */

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

async function loadCandidateDashboard() {
  const token = localStorage.getItem('auth_token');
  const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

  try {
    const res = await fetch('/api/candidate/dashboard', { headers });
    if (res.status === 401 || res.status === 403) {
      // Auto demo login as Alex Rivera if not logged in
      const demoRes = await fetch('/api/auth/demo-login?role=candidate', { method: 'POST' });
      const demoData = await demoRes.json();
      localStorage.setItem('auth_token', demoData.access_token);
      localStorage.setItem('user_role', demoData.user.role);
      localStorage.setItem('user_name', demoData.user.full_name);
      return loadCandidateDashboard();
    }

    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.error('Error fetching candidate dashboard:', err);
    showToast('Failed to load candidate dashboard.', 'error');
  }
}

function renderDashboard(data) {
  // Update Candidate Name
  const nameBadge = document.getElementById('candidateNameBadge');
  if (nameBadge && data.candidate) {
    nameBadge.textContent = `${data.candidate.name} (${data.candidate.job_role})`;
  }

  // Update KPI counters
  const assigned = data.assigned_interviews || [];
  const inProgress = data.in_progress_interviews || [];
  const completed = data.completed_interviews || [];

  document.getElementById('kpiAssignedCount').textContent = assigned.length;
  document.getElementById('kpiInProgressCount').textContent = inProgress.length;
  document.getElementById('kpiCompletedCount').textContent = completed.length;

  // Active / Assigned Table
  const activeTableBody = document.getElementById('activeInterviewsTableBody');
  const allActive = [...inProgress, ...assigned];

  if (allActive.length === 0) {
    activeTableBody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 36px;">
          <div style="font-size: 28px; margin-bottom: 8px;">🎉</div>
          <div>No pending assessments! You are completely up to date.</div>
        </td>
      </tr>
    `;
  } else {
    activeTableBody.innerHTML = allActive.map(item => `
      <tr>
        <td>
          <div style="font-weight: 600; color: var(--text-primary);">${item.title}</div>
          <div style="font-size: 12px; color: var(--text-muted);">${item.id}</div>
        </td>
        <td>${item.job_role}</td>
        <td>${item.current_question_index > 0 ? `Q${item.current_question_index} of ${item.total_questions}` : `${item.total_questions} Questions`}</td>
        <td>${item.duration_minutes} mins</td>
        <td>
          <span class="status-badge ${item.status}">
            ● ${item.status === 'in_progress' ? 'In Progress' : 'Assigned'}
          </span>
        </td>
        <td>
          <button class="btn ${item.status === 'in_progress' ? 'btn-secondary' : 'btn-primary'}" 
                  style="padding: 8px 16px; font-size: 13px;"
                  onclick="launchInterview('${item.id}')">
            ${item.status === 'in_progress' ? 'Resume Assessment ➔' : 'Start Assessment ➔'}
          </button>
        </td>
      </tr>
    `).join('');
  }

  // Completed Table (Strictly NO scores displayed!)
  const completedTableBody = document.getElementById('completedInterviewsTableBody');
  if (completed.length === 0) {
    completedTableBody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 36px;">
          No completed assessments found.
        </td>
      </tr>
    `;
  } else {
    completedTableBody.innerHTML = completed.map(item => `
      <tr>
        <td>
          <div style="font-weight: 600; color: var(--text-primary);">${item.title}</div>
          <div style="font-size: 12px; color: var(--text-muted);">${item.id}</div>
        </td>
        <td>${item.job_role}</td>
        <td>${item.completed_at ? new Date(item.completed_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'Recently'}</td>
        <td>
          <span class="status-badge completed">
            ● Completed
          </span>
        </td>
        <td>
          <span style="font-size: 13px; color: var(--color-basic); display: flex; align-items: center; gap: 6px;">
            <span>✓</span> Responses delivered to Hiring Team
          </span>
        </td>
      </tr>
    `).join('');
  }

  // Notifications
  renderNotifications(data.notifications || []);
}

function renderNotifications(notifs) {
  const badge = document.getElementById('notifBadgeCount');
  const list = document.getElementById('notifsList');
  const unreadCount = notifs.filter(n => !n.read).length;
  if (badge) badge.textContent = unreadCount;

  if (!list) return;
  if (notifs.length === 0) {
    list.innerHTML = `<div style="padding: 16px; text-align: center; color: var(--text-muted); font-size: 13px;">No new notifications.</div>`;
    return;
  }

  list.innerHTML = notifs.map(n => `
    <div class="notif-item ${n.read ? '' : 'unread'}">
      <div style="font-weight: 600; margin-bottom: 2px;">${n.title}</div>
      <div style="color: var(--text-secondary); font-size: 12px;">${n.message}</div>
      <div style="color: var(--text-muted); font-size: 10px; margin-top: 4px;">${new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
    </div>
  `).join('');
}

function launchInterview(interviewId) {
  window.location.href = `/interview.html?id=${interviewId}`;
}

async function markAllNotificationsRead(e) {
  if (e) e.preventDefault();
  const token = localStorage.getItem('auth_token');
  try {
    await fetch('/api/notifications/read-all', {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    const badge = document.getElementById('notifBadgeCount');
    if (badge) badge.textContent = '0';
    document.querySelectorAll('.notif-item').forEach(el => el.classList.remove('unread'));
    showToast('All notifications marked as read', 'success');
  } catch (err) {
    console.error('Failed to mark notifications read', err);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadCandidateDashboard();

  const btnLogout = document.getElementById('btnLogout');
  if (btnLogout) {
    btnLogout.addEventListener('click', () => {
      localStorage.clear();
      window.location.href = '/';
    });
  }

  const notifsToggle = document.getElementById('btnNotifsToggle');
  const notifDropdown = document.getElementById('notifDropdown');
  if (notifsToggle && notifDropdown) {
    notifsToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      notifDropdown.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
      if (!notifDropdown.contains(e.target) && e.target !== notifsToggle) {
        notifDropdown.classList.remove('active');
      }
    });
  }
});
