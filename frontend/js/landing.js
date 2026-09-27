/**
 * Landing Page & Authentication Controller.
 */

let currentAuthRole = 'recruiter';
let currentAuthMode = 'login';

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

function openAuthModal(role = 'recruiter', mode = 'login') {
  const modal = document.getElementById('authModal');
  if (modal) {
    modal.classList.add('active');
    setAuthRole(role);
    switchAuthTab(mode);
  }
}

function closeAuthModal() {
  const modal = document.getElementById('authModal');
  if (modal) modal.classList.remove('active');
}

function setAuthRole(role) {
  currentAuthRole = role;
  const recBtn = document.getElementById('roleRecruiterBtn');
  const candBtn = document.getElementById('roleCandidateBtn');
  const recFields = document.getElementById('recruiterFields');
  const candFields = document.getElementById('candidateFields');
  const emailInput = document.getElementById('loginEmail');

  if (role === 'recruiter') {
    recBtn.className = 'btn btn-primary';
    candBtn.className = 'btn btn-secondary';
    if (recFields) recFields.style.display = 'block';
    if (candFields) candFields.style.display = 'none';
    if (emailInput && !emailInput.value) emailInput.value = 'sarah.jenkins@techcorp.io';
  } else {
    recBtn.className = 'btn btn-secondary';
    candBtn.className = 'btn btn-primary';
    if (recFields) recFields.style.display = 'none';
    if (candFields) candFields.style.display = 'block';
    if (emailInput && !emailInput.value) emailInput.value = 'alex.rivera@example.com';
  }
}

function switchAuthTab(mode) {
  currentAuthMode = mode;
  const tabLogin = document.getElementById('tabLogin');
  const tabRegister = document.getElementById('tabRegister');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const modalTitle = document.getElementById('authModalTitle');

  if (mode === 'login') {
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
    loginForm.style.display = 'block';
    registerForm.style.display = 'none';
    modalTitle.textContent = 'Sign In to AI Interview Room';
  } else {
    tabRegister.classList.add('active');
    tabLogin.classList.remove('active');
    registerForm.style.display = 'block';
    loginForm.style.display = 'none';
    modalTitle.textContent = 'Create New Account';
  }
}

async function quickDemoLogin(role) {
  try {
    const res = await fetch(`/api/auth/demo-login?role=${role}`, {
      method: 'POST'
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user_role', data.user.role);
      localStorage.setItem('user_name', data.user.full_name);
      localStorage.setItem('user_email', data.user.email);
      showToast(`Welcome back, ${data.user.full_name}! Redirecting...`, 'success');
      setTimeout(() => {
        if (role === 'recruiter') {
          window.location.href = '/recruiter.html';
        } else {
          window.location.href = '/candidate-dashboard.html';
        }
      }, 700);
    } else {
      showToast(data.detail || 'Demo login failed', 'error');
    }
  } catch (err) {
    showToast('Failed to connect to authentication service.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Modal triggers
  const btnOpen = document.getElementById('btnOpenLoginModal');
  const btnClose = document.getElementById('btnCloseAuthModal');
  const modal = document.getElementById('authModal');
  const heroRec = document.getElementById('heroRecruiterBtn');
  const heroCand = document.getElementById('heroCandidateBtn');
  const quickRec = document.getElementById('btnQuickDemoRecruiter');

  if (btnOpen) btnOpen.addEventListener('click', () => openAuthModal(currentAuthRole, 'login'));
  if (btnClose) btnClose.addEventListener('click', closeAuthModal);
  if (heroRec) heroRec.addEventListener('click', () => quickDemoLogin('recruiter'));
  if (heroCand) heroCand.addEventListener('click', () => quickDemoLogin('candidate'));
  if (quickRec) quickRec.addEventListener('click', () => quickDemoLogin('recruiter'));

  // Close modal on click outside
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeAuthModal();
    });
  }

  // Forgot password
  const forgotBtn = document.getElementById('btnForgotPassword');
  if (forgotBtn) {
    forgotBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value;
      if (!email) {
        showToast('Please enter your email address first.', 'error');
        return;
      }
      showToast(`Password reset link dispatched to ${email}`, 'success');
    });
  }

  // Login Form Submission
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value;
      const password = document.getElementById('loginPassword').value;
      const submitBtn = document.getElementById('loginSubmitBtn');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Signing in...';

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, role: currentAuthRole })
        });
        const data = await res.json();
        if (res.ok) {
          localStorage.setItem('auth_token', data.access_token);
          localStorage.setItem('user_role', data.user.role);
          localStorage.setItem('user_name', data.user.full_name);
          localStorage.setItem('user_email', data.user.email);
          showToast('Authentication successful!', 'success');
          setTimeout(() => {
            if (data.user.role === 'recruiter') {
              window.location.href = '/recruiter.html';
            } else {
              window.location.href = '/candidate-dashboard.html';
            }
          }, 600);
        } else {
          showToast(data.detail || 'Login failed', 'error');
          submitBtn.disabled = false;
          submitBtn.textContent = 'Sign In to Portal';
        }
      } catch (err) {
        showToast('Connection error with server.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign In to Portal';
      }
    });
  }

  // Register Form Submission
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fullName = document.getElementById('regFullName').value;
      const email = document.getElementById('regEmail').value;
      const password = document.getElementById('regPassword').value;
      const company = document.getElementById('regCompany').value;
      const title = document.getElementById('regTitle').value;
      const jobRole = document.getElementById('regJobRole').value;
      const expLevel = document.getElementById('regExpLevel').value;

      const payload = {
        full_name: fullName,
        email: email,
        password: password,
        role: currentAuthRole,
        company: company,
        title: title,
        job_role: jobRole,
        experience_level: expLevel
      };

      const submitBtn = document.getElementById('registerSubmitBtn');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Creating account...';

      try {
        const res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
          localStorage.setItem('auth_token', data.access_token);
          localStorage.setItem('user_role', data.user.role);
          localStorage.setItem('user_name', data.user.full_name);
          localStorage.setItem('user_email', data.user.email);
          showToast('Account created successfully!', 'success');
          setTimeout(() => {
            if (data.user.role === 'recruiter') {
              window.location.href = '/recruiter.html';
            } else {
              window.location.href = '/candidate-dashboard.html';
            }
          }, 600);
        } else {
          showToast(data.detail || 'Registration failed', 'error');
          submitBtn.disabled = false;
          submitBtn.textContent = 'Create Account';
        }
      } catch (err) {
        showToast('Server connection failed.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Account';
      }
    });
  }

  // Handle direct navigation to /login, hash #login or query parameters
  const urlParams = new URLSearchParams(window.location.search);
  const path = window.location.pathname.toLowerCase();
  const hash = window.location.hash.toLowerCase();
  const reqRole = urlParams.get('role') || 'recruiter';
  const reqMode = hash === '#register' || urlParams.get('auth') === 'register' ? 'register' : 'login';

  if (path.includes('/login') || hash === '#login' || hash === '#register' || urlParams.has('auth') || urlParams.has('role')) {
    openAuthModal(reqRole, reqMode);
  }
});

