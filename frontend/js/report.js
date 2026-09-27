/**
 * Final Evaluation Report Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const interviewId = urlParams.get('id') || sessionStorage.getItem('interview_id');

  if (!interviewId) {
    alert('No interview ID specified. Redirecting to start page.');
    window.location.href = '/';
    return;
  }

  // Elements
  const candidateTitleEl = document.getElementById('candidateTitle');
  const candidateMetadataEl = document.getElementById('candidateMetadata');
  const hiringSignalContainer = document.getElementById('hiringSignalContainer');

  const weightedScoreValEl = document.getElementById('weightedScoreVal');
  const rawScoreValEl = document.getElementById('rawScoreVal');
  const executiveSummaryTextEl = document.getElementById('executiveSummaryText');
  const hiringReasoningTextEl = document.getElementById('hiringReasoningText');

  const basicScoreTextEl = document.getElementById('basicScoreText');
  const basicMeterFillEl = document.getElementById('basicMeterFill');
  const interScoreTextEl = document.getElementById('interScoreText');
  const interMeterFillEl = document.getElementById('interMeterFill');
  const advScoreTextEl = document.getElementById('advScoreText');
  const advMeterFillEl = document.getElementById('advMeterFill');
  const depthAnalysisTextEl = document.getElementById('depthAnalysisText');

  const topicsBreakdownContainer = document.getElementById('topicsBreakdownContainer');
  const strengthsListEl = document.getElementById('strengthsList');
  const improvementsListEl = document.getElementById('improvementsList');
  const demonstratedConceptsCloudEl = document.getElementById('demonstratedConceptsCloud');
  const missingConceptsCloudEl = document.getElementById('missingConceptsCloud');
  const transcriptListEl = document.getElementById('transcriptList');

  try {
    const resp = await fetch(`/api/interview/${interviewId}/report`);
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Failed to fetch interview report.');
    }

    const report = await resp.json();

    // 1. Candidate Details
    candidateTitleEl.textContent = `${report.candidate_name}`;
    const dateFormatted = new Date(report.generated_at).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric'
    });
    candidateMetadataEl.textContent = `${report.job_role} • Experience: ${report.experience_level} • Evaluated on ${dateFormatted} • ID: #${report.interview_id}`;

    // 2. Hiring Signal
    const recClassMap = {
      'Strong Hire': 'rec-strong-hire',
      'Hire': 'rec-hire',
      'Lean Hire': 'rec-lean-hire',
      'Re-evaluate': 'rec-re-evaluate',
      'No Hire': 'rec-no-hire'
    };
    const recClass = recClassMap[report.hiring_recommendation] || 'rec-hire';
    hiringSignalContainer.innerHTML = `
      <span class="recommendation-badge ${recClass}">
        ${report.hiring_recommendation}
      </span>
    `;

    // 3. Scores & Summary
    weightedScoreValEl.textContent = report.weighted_score.toFixed(1);
    rawScoreValEl.textContent = report.overall_score.toFixed(1);
    executiveSummaryTextEl.textContent = report.overall_summary || 'No summary provided.';
    hiringReasoningTextEl.textContent = report.recommendation_reasoning || 'No specific reasoning recorded.';

    // 4. Difficulty Mastery Tiers
    const diffBreakdown = report.difficulty_breakdown || {};
    const basicAvg = diffBreakdown.basic ? (diffBreakdown.basic.avg * 10) : 0;
    const interAvg = diffBreakdown.intermediate ? (diffBreakdown.intermediate.avg * 10) : 0;
    const advAvg = diffBreakdown.advanced ? (diffBreakdown.advanced.avg * 10) : 0;

    basicScoreTextEl.textContent = `${basicAvg.toFixed(0)}%`;
    basicMeterFillEl.style.width = `${basicAvg}%`;

    interScoreTextEl.textContent = `${interAvg.toFixed(0)}%`;
    interMeterFillEl.style.width = `${interAvg}%`;

    advScoreTextEl.textContent = `${advAvg.toFixed(0)}%`;
    advMeterFillEl.style.width = `${advAvg}%`;

    depthAnalysisTextEl.textContent = report.depth_analysis || '';

    // 5. Topic Breakdown
    const topicBreakdown = report.topic_breakdown || {};
    topicsBreakdownContainer.innerHTML = '';
    const topicEntries = Object.entries(topicBreakdown);

    if (topicEntries.length === 0) {
      topicsBreakdownContainer.innerHTML = `<div style="font-size: 13px; color: var(--text-muted);">No topic data recorded.</div>`;
    } else {
      topicEntries.forEach(([topicName, data]) => {
        const avg = data.avg || 0;
        const count = data.count || 1;
        const pct = Math.round((avg / 10) * 100);

        const row = document.createElement('div');
        row.style.background = 'rgba(0, 0, 0, 0.2)';
        row.style.borderRadius = '10px';
        row.style.padding = '10px 14px';
        row.style.display = 'flex';
        row.style.justifyContent = 'space-between';
        row.style.alignItems = 'center';

        row.innerHTML = `
          <div>
            <div style="font-weight: 600; font-size: 14px;">${topicName}</div>
            <div style="font-size: 11px; color: var(--text-muted);">${count} question${count === 1 ? '' : 's'} evaluated</div>
          </div>
          <div style="text-align: right;">
            <div style="font-weight: 700; font-size: 14px; color: #38bdf8;">${avg.toFixed(1)} / 10</div>
            <div style="font-size: 11px; color: var(--text-secondary);">${pct}% mastery</div>
          </div>
        `;
        topicsBreakdownContainer.appendChild(row);
      });
    }

    // 6. Strengths & Improvements
    strengthsListEl.innerHTML = '';
    (report.strengths || []).forEach((item) => {
      const li = document.createElement('li');
      li.textContent = item;
      strengthsListEl.appendChild(li);
    });

    improvementsListEl.innerHTML = '';
    (report.areas_for_improvement || []).forEach((item) => {
      const li = document.createElement('li');
      li.textContent = item;
      improvementsListEl.appendChild(li);
    });

    // 7. Demonstrated vs Missing Concepts
    demonstratedConceptsCloudEl.innerHTML = '';
    const demList = report.demonstrated_concepts || [];
    if (demList.length === 0) {
      demonstratedConceptsCloudEl.innerHTML = `<span style="font-size: 12px; color: var(--text-muted);">No demonstrated concepts recorded.</span>`;
    } else {
      demList.forEach((c) => {
        const tag = document.createElement('span');
        tag.className = 'concept-tag concept-demonstrated';
        tag.innerHTML = `✓ ${c}`;
        demonstratedConceptsCloudEl.appendChild(tag);
      });
    }

    missingConceptsCloudEl.innerHTML = '';
    const missList = report.missing_concepts || [];
    if (missList.length === 0) {
      missingConceptsCloudEl.innerHTML = `<span style="font-size: 12px; color: var(--text-muted);">No unconfirmed concepts detected.</span>`;
    } else {
      missList.forEach((c) => {
        const tag = document.createElement('span');
        tag.className = 'concept-tag concept-missing';
        tag.innerHTML = `⚠ ${c}`;
        missingConceptsCloudEl.appendChild(tag);
      });
    }

    // 8. Transcript & Adaptive Traces
    transcriptListEl.innerHTML = '';
    const transcript = report.transcript || [];

    transcript.forEach((item, idx) => {
      const card = document.createElement('div');
      card.className = 'transcript-item';

      const decision = item.adaptive_decision || {};
      const actionBadge = decision.action
        ? `<span class="badge-tag badge-adaptive">${decision.action}</span>`
        : '';

      card.innerHTML = `
        <div class="transcript-header" onclick="this.parentElement.classList.toggle('open')">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-weight: 700; font-size: 14px;">Q${item.question_number}</span>
            <span class="badge-tag badge-${item.difficulty.toLowerCase()}">${item.difficulty}</span>
            <span style="font-size: 13px; color: var(--text-secondary);">${item.topic}</span>
          </div>
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-weight: 700; font-size: 14px; color: #a5b4fc;">Score: ${item.score}/10</span>
            ${actionBadge}
            <span class="arrow-icon" style="font-size: 14px;">▼</span>
          </div>
        </div>
        <div class="transcript-body">
          <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 8px;">
            ${item.question_text}
          </div>
          <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">Candidate Response:</div>
          <div class="transcript-answer-box">${escapeHtml(item.candidate_answer || 'No response')}</div>
          
          <div style="margin-top: 10px; font-size: 13px; color: var(--text-secondary);">
            <strong>Evaluator Analysis:</strong> ${item.explanation || 'N/A'}
          </div>

          ${decision.reason ? `
            <div class="adaptive-decision-box">
              <strong style="color: #c7d2fe;">Adaptive Engine Decision:</strong> ${decision.reason}
              <div style="margin-top: 4px; font-size: 12px; color: var(--text-muted);">
                Target Concept: <em>${decision.target_concept || 'N/A'}</em> | Next Tier: <strong>${decision.next_difficulty || item.difficulty}</strong>
              </div>
            </div>
          ` : ''}
        </div>
      `;

      // Open first item by default
      if (idx === 0) {
        card.classList.add('open');
      }

      transcriptListEl.appendChild(card);
    });

  } catch (err) {
    console.error(err);
    alert(`Error loading report: ${err.message}`);
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
});
