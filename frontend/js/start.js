/**
 * Candidate Onboarding & Setup Script
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('interviewSetupForm');
  const startBtn = document.getElementById('startBtn');
  const autofillBtn = document.getElementById('quickAutofillBtn');
  const topicsContainer = document.getElementById('topicsContainer');

  // Interactive Topic Chips Toggle
  topicsContainer.addEventListener('click', (e) => {
    const chip = e.target.closest('.topic-chip');
    if (!chip) return;

    // Toggle active state
    chip.classList.toggle('active');

    // Ensure at least one chip remains selected
    const activeChips = topicsContainer.querySelectorAll('.topic-chip.active');
    if (activeChips.length === 0) {
      chip.classList.add('active');
    }
  });

  // Quick Autofill Demo
  autofillBtn.addEventListener('click', () => {
    document.getElementById('candidateName').value = 'Priya Sharma';
    document.getElementById('candidateEmail').value = 'priya.sharma@example.com';
    document.getElementById('jobRole').value = 'Senior Python Engineer';
    document.getElementById('experienceLevel').value = 'Senior';
    document.getElementById('totalQuestions').value = '5';
    document.getElementById('startingDifficulty').value = 'auto';

    // Set topic chips
    document.querySelectorAll('.topic-chip').forEach((chip) => {
      const topic = chip.dataset.topic;
      if (['Python Core', 'Data Structures', 'System Design'].includes(topic)) {
        chip.classList.add('active');
      } else {
        chip.classList.remove('active');
      }
    });
  });

  // Form Submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('candidateName').value.trim();
    const email = document.getElementById('candidateEmail').value.trim();
    const role = document.getElementById('jobRole').value.trim();
    const experience = document.getElementById('experienceLevel').value;
    const totalQuestions = parseInt(document.getElementById('totalQuestions').value, 10);
    const difficultyChoice = document.getElementById('startingDifficulty').value;

    const selectedTopics = Array.from(
      topicsContainer.querySelectorAll('.topic-chip.active')
    ).map((chip) => chip.dataset.topic);

    if (selectedTopics.length === 0) {
      alert('Please select at least one technical topic.');
      return;
    }

    // Set loading state
    startBtn.disabled = true;
    startBtn.innerHTML = `<span>Initializing Adaptive Engine...</span><div class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></div>`;

    try {
      const payload = {
        candidate_name: name,
        candidate_email: email,
        job_role: role,
        experience_level: experience,
        topics: selectedTopics,
        total_questions: totalQuestions,
        starting_difficulty: difficultyChoice === 'auto' ? null : difficultyChoice
      };

      const response = await fetch('/api/interview/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to initialize interview.');
      }

      const session = await response.json();

      // Save metadata in sessionStorage
      sessionStorage.setItem('interview_id', session.interview_id);
      sessionStorage.setItem('candidate_name', session.candidate_name);
      sessionStorage.setItem('job_role', session.job_role);
      sessionStorage.setItem('total_questions', session.total_questions);

      // Redirect to interview room
      window.location.href = `/interview.html?id=${session.interview_id}`;
    } catch (err) {
      console.error(err);
      alert(`Error: ${err.message}`);
      startBtn.disabled = false;
      startBtn.innerHTML = `<span>Begin Technical Interview</span><span>➔</span>`;
    }
  });
});
