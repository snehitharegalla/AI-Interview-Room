/**
 * Live AI Interview Room Controller
 */

function initInterviewRoom() {
  // Elements
  const sessionInfoEl = document.getElementById('sessionCandidateInfo') || document.getElementById('sessionRoleInfo');
  const sessionTimerEl = document.getElementById('sessionTimerBadge');
  const sessionShortIdEl = document.getElementById('sessionShortId');
  const activeTopicValEl = document.getElementById('activeTopicVal');
  const activeRoleValEl = document.getElementById('activeRoleVal');
  const activeDifficultyValEl = document.getElementById('activeDifficultyVal');
  const interviewerStatusTextEl = document.getElementById('interviewerStatusText');
  const statusDotEl = document.getElementById('statusDot');

  const questionProgressTextEl = document.getElementById('questionProgressText');
  const progressPercentageTextEl = document.getElementById('progressPercentageText');
  const progressBarFillEl = document.getElementById('progressBarFill');

  const questionBadgeEl = document.getElementById('questionBadge');
  const topicBadgeEl = document.getElementById('topicBadge');
  const difficultyBadgeEl = document.getElementById('difficultyBadge');
  const questionTextEl = document.getElementById('questionText');

  const answerForm = document.getElementById('answerForm');
  const answerInput = document.getElementById('candidateAnswer');
  const charCountEl = document.getElementById('charCount');
  const submitBtn = document.getElementById('submitAnswerBtn');
  const endEarlyBtn = document.getElementById('endInterviewEarlyBtn');

  const evalOverlay = document.getElementById('evalOverlay');
  const evalOverlayMsg = document.getElementById('evalOverlayMessage');

  // Parse Interview ID
  const urlParams = new URLSearchParams(window.location.search);
  let interviewId = urlParams.get('id') || sessionStorage.getItem('interview_id');

  if (!interviewId) {
    alert('No active interview session found. Redirecting to start page.');
    window.location.href = '/';
    return;
  }

  // Session Timer
  let secondsElapsed = 0;
  setInterval(() => {
    secondsElapsed++;
    const mins = String(Math.floor(secondsElapsed / 60)).padStart(2, '0');
    const secs = String(secondsElapsed % 60).padStart(2, '0');
    if (sessionTimerEl) {
      sessionTimerEl.textContent = `⏱️ Time: ${mins}:${secs}`;
    }
  }, 1000);

  // Character Counter
  if (answerInput && charCountEl) {
    answerInput.addEventListener('input', () => {
      const len = answerInput.value.length;
      charCountEl.textContent = `${len} character${len === 1 ? '' : 's'}`;
    });
  }

  // Keyboard shortcut Ctrl + Enter to submit
  if (answerInput && answerForm) {
    answerInput.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        answerForm.dispatchEvent(new Event('submit'));
      }
    });
  }

  let currentQuestionId = null;
  let totalQuestions = 5;

  // Load Session State
  async function loadSessionState() {
    try {
      const token = localStorage.getItem('auth_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

      let resp = await fetch(`/api/interview/${interviewId}`, { headers });
      if (resp.status === 403) {
        resp = await fetch(`/api/candidate/interview/${interviewId}`, { headers });
      }

      if (!resp.ok) {
        throw new Error('Could not load session state.');
      }
      const data = await resp.json();

      if (data.status === 'completed') {
        window.location.href = `/report.html?id=${interviewId}`;
        return;
      }

      totalQuestions = data.total_questions || 5;

      if (sessionShortIdEl) {
        sessionShortIdEl.textContent = `#${interviewId.slice(0, 8)}`;
      }

      if (sessionInfoEl) {
        const exp = data.experience_level ? ` (${data.experience_level})` : '';
        sessionInfoEl.textContent = `${data.candidate_name || 'Candidate'} • ${data.job_role || 'Software Engineer'}${exp}`;
      }

      if (activeRoleValEl && data.job_role) {
        activeRoleValEl.textContent = data.job_role;
      }

      if (data.current_question) {
        renderQuestion(data.current_question, data.current_question_index || 1, totalQuestions);
      }
    } catch (err) {
      console.error(err);
      alert(`Error: ${err.message}`);
    }
  }

  function renderQuestion(q, currentNum, total) {
    if (!q) return;

    currentQuestionId = q.question_id;

    // Progress Bar
    const pct = Math.round(((currentNum) / total) * 100);
    if (questionProgressTextEl) {
      questionProgressTextEl.textContent = `Question ${currentNum} of ${total}`;
    }
    if (progressPercentageTextEl) {
      progressPercentageTextEl.textContent = `${pct}% Complete`;
    }
    if (progressBarFillEl) {
      progressBarFillEl.style.width = `${pct}%`;
    }

    // Badges & Labels
    if (questionBadgeEl) {
      questionBadgeEl.textContent = `Question ${currentNum}`;
    }
    if (topicBadgeEl) {
      topicBadgeEl.textContent = q.topic ? (q.topic.startsWith('Topic') ? q.topic : `Topic: ${q.topic}`) : 'Topic: Technical';
    }
    if (difficultyBadgeEl && q.difficulty) {
      difficultyBadgeEl.textContent = q.difficulty.toUpperCase();
      difficultyBadgeEl.className = `badge-tag badge-${q.difficulty.toLowerCase()}`;
    }

    // Left sidebar status
    if (activeTopicValEl) {
      activeTopicValEl.textContent = q.topic || 'Core Principles';
    }
    if (activeDifficultyValEl && q.difficulty) {
      activeDifficultyValEl.innerHTML = `<span class="badge-tag badge-${q.difficulty.toLowerCase()}">${q.difficulty}</span>`;
    }
    if (interviewerStatusTextEl) {
      interviewerStatusTextEl.textContent = 'Listening to candidate';
    }
    if (statusDotEl) {
      statusDotEl.className = 'status-dot';
    }

    // Question Text
    if (questionTextEl) {
      questionTextEl.textContent = q.question_text || '';
    }

    // Clear answer area
    if (answerInput) {
      answerInput.value = '';
      if (charCountEl) {
        charCountEl.textContent = '0 characters';
      }
      answerInput.focus();
    }
  }

  // Submit Answer
  if (answerForm) {
    answerForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const answer = answerInput ? answerInput.value.trim() : '';
      if (!answer) {
        alert('Please provide an answer before submitting.');
        return;
      }

      // Activate overlay & status animation
      if (evalOverlay) evalOverlay.classList.add('active');
      if (statusDotEl) statusDotEl.className = 'status-dot evaluating';
      if (interviewerStatusTextEl) interviewerStatusTextEl.textContent = 'Evaluating response...';
      if (submitBtn) submitBtn.disabled = true;

      const overlayMessages = [
        'Analyzing answer for correctness and conceptual clarity...',
        'Diagnosing knowledge boundaries and missing concepts...',
        'Updating candidate knowledge profile across tiers...',
        'Formulating the next adaptive technical challenge...'
      ];

      let msgIndex = 0;
      const msgInterval = setInterval(() => {
        msgIndex = (msgIndex + 1) % overlayMessages.length;
        if (evalOverlayMsg) evalOverlayMsg.textContent = overlayMessages[msgIndex];
      }, 1100);

      try {
        const payload = {
          interview_id: interviewId,
          question_id: currentQuestionId,
          candidate_answer: answer
        };

        const token = localStorage.getItem('auth_token');
        const headers = {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };

        const resp = await fetch('/api/interview/answer', {
          method: 'POST',
          headers,
          body: JSON.stringify(payload)
        });

        clearInterval(msgInterval);

        if (!resp.ok) {
          const err = await resp.json();
          throw new Error(err.detail || 'Failed to submit answer.');
        }

        const result = await resp.json();

        // Check if interview completed
        if (result.status === 'completed' || !result.next_question) {
          if (evalOverlayMsg) evalOverlayMsg.textContent = 'Interview complete! Compiling final evaluation report...';
          setTimeout(() => {
            window.location.href = `/report.html?id=${interviewId}`;
          }, 800);
          return;
        }

        // Next Question ready
        setTimeout(() => {
          if (evalOverlay) evalOverlay.classList.remove('active');
          if (submitBtn) submitBtn.disabled = false;
          renderQuestion(
            result.next_question,
            result.next_question.question_number,
            result.total_questions || totalQuestions
          );
        }, 600);

      } catch (err) {
        clearInterval(msgInterval);
        console.error(err);
        alert(`Submission Error: ${err.message}`);
        if (evalOverlay) evalOverlay.classList.remove('active');
        if (submitBtn) submitBtn.disabled = false;
        if (interviewerStatusTextEl) interviewerStatusTextEl.textContent = 'Listening to candidate';
        if (statusDotEl) statusDotEl.className = 'status-dot';
      }
    });
  }

  // End Interview Early
  if (endEarlyBtn) {
    endEarlyBtn.addEventListener('click', () => {
      const confirmEnd = confirm('Are you sure you want to end this interview session early? A final report will be generated for the questions answered so far.');
      if (confirmEnd) {
        window.location.href = `/report.html?id=${interviewId}`;
      }
    });
  }

  // Initial Load
  loadSessionState();
}

// Make sure DOM is fully loaded before initializing
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initInterviewRoom);
} else {
  initInterviewRoom();
}
