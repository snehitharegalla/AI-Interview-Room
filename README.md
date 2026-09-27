# AI Interview Room ⚡

> **Adaptive Technical Interview Platform powered by Generative AI & Deterministic Cognitive Profiling**

AI Interview Room is a technical interview platform that conducts **truly adaptive** interviews. Rather than following a static list of questions or applying naive rules (e.g. "wrong = easy / correct = hard"), the system continuously analyzes the candidate's actual conceptual understanding, constructs a live multi-dimensional knowledge profile, and dynamically orchestrates the interview strategy.

---

## 🌟 Key Differentiating Features

### 1. True Conceptual Understanding
The AI doesn't just score answers 0–10; it categorizes candidate responses across four distinct knowledge states:
- **Understands Deeply**: Strong mastery of both concepts and operational tradeoffs.
- **Knows Basics but Lacks Advanced Depth**: Accurately explains fundamentals but struggles with internals or edge cases.
- **Understands Concept but Missed Specific Nuance**: Misunderstood a particular question or boundary condition despite underlying grasp.
- **Partially Correct Answer**: Grasped the high-level purpose while omitting a specific required mechanism.

### 2. Real-Time Diagnostic Probing
- **On a Strong Answer**: Pushes deeper into architecture, scalability, and edge cases (`DEEPER`).
- **On a Partial Answer**: Pinpoints the exact missing concept and generates a targeted follow-up question testing that specific gap (`PROBE_MISSING`).
- **On an Incorrect Answer**: **Does NOT immediately reduce difficulty.** First issues a targeted diagnostic question to explore foundational mechanics (`DIAGNOSTIC`). Only after gathering repeated evidence is difficulty adjusted (`EASIER`) or topic rotated (`PIVOT_TOPIC`).

### 3. Depth-Weighted Scoring & Fair Hiring Signals
Candidates cannot artificially inflate their final evaluation score simply by answering many elementary questions correctly. The final report calculates:
- **Raw Average**: Arithmetic mean of question scores.
- **Depth-Weighted Score**: Weighted by difficulty tier (Basic: `1.0x`, Intermediate: `1.5x`, Advanced: `2.2x`).
- **Hiring Signals**: Objective recommendations (`Strong Hire`, `Hire`, `Lean Hire`, `Re-evaluate`, `No Hire`) backed by strategic hiring reasoning.

### 4. Zero-Leakage Candidate Experience
Candidate sees a clean, professional, focused interview room with an animated AI Interviewer persona, progress indicators, timers, and code-friendly inputs. All internal scores, prompts, and adaptive directives are safely isolated on the backend.

---

## 🏗️ Project Architecture

```
AI_Interview_Room/
│
├── backend/
│   ├── main.py                  # FastAPI app entry point & static file routing
│   ├── database.py              # SQLite engine & session management
│   ├── models.py                # SQLAlchemy models (Candidate, Interview, Question, Answer, etc.)
│   ├── schemas.py               # Pydantic validation schemas
│   ├── routes/
│   │   ├── interview.py         # Start session, submit answer, get live state
│   │   └── report.py            # Generate & retrieve depth-weighted final reports
│   ├── services/
│   │   ├── ai_service.py        # Configurable GenAI provider (Gemini, OpenAI, Mock)
│   │   ├── evaluator.py         # Structured JSON answer evaluation & normalization
│   │   └── adaptive_engine.py   # Adaptive interview decision tree & knowledge profile manager
│   ├── prompts/
│   │   ├── question_prompt.txt   # Prompt template for adaptive questions
│   │   ├── evaluation_prompt.txt # Prompt template for multi-dimensional evaluation
│   │   └── report_prompt.txt     # Prompt template for executive hiring report
│   └── seed_demo.py             # Script to load demo interview data for instant testing
│
├── frontend/
│   ├── index.html               # Candidate setup & interview configuration page
│   ├── interview.html           # Live interactive AI interview room
│   ├── report.html              # Comprehensive performance & knowledge profile report
│   ├── css/
│   │   └── style.css            # Modern, dark-mode glassmorphic design system
│   └── js/
│       ├── start.js             # Onboarding validation & session initialization
│       ├── interview.js         # Adaptive Q&A loop, timers, transitions, keyboard shortcuts
│       └── report.js            # Score meters, topic radar, transcript viewer, print/export
│
├── tests/
│   ├── test_adaptive_engine.py  # Unit tests covering all 7 mandatory adaptive scenarios
│   └── test_api.py              # Integration tests for FastAPI endpoints
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started Locally

### Prerequisites
- Python 3.10+ installed

### 1. Install Dependencies
In PowerShell or terminal:
```powershell
python -m pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Default `.env` configuration:
```ini
AI_PROVIDER=mock      # "mock" runs locally with zero API keys required!
                      # Change to "gemini" or "openai" when using live keys.

GEMINI_API_KEY=       # Your Google Gemini API Key (optional)
OPENAI_API_KEY=       # Your OpenAI API Key (optional)
AI_MODEL=gemini-1.5-flash
PORT=8000
```
> **Note**: If `AI_PROVIDER=gemini` is selected but no key is set, the system automatically falls back to the intelligent Mock provider so the application runs seamlessly out-of-the-box!

### 3. Seed Demo Data (Optional)
To instantly inspect a pre-conducted adaptive interview report:
```powershell
python -m backend.seed_demo
```
This seeds sample candidate **Alex Rivera** (`demo-alex-101`) demonstrating how the adaptive engine escalated through Python decorators, handled LRU cache eviction gaps with focused diagnostic probes, and evaluated distributed system caching.

### 4. Start the Application Server
Run the FastAPI development server:
```powershell
python -m uvicorn backend.main:app --reload --port 8000
```
Once started, open your browser and navigate to:
👉 **`http://127.0.0.1:8000/`**

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:
```powershell
python -m pytest tests/ -v
```

### Tested Scenarios:
1. **Strong candidate answer**: Engine probes deeper / escalates difficulty.
2. **Partial candidate answer**: Engine pinpoints missing concept and probes that specific topic.
3. **Completely wrong answer**: Engine triggers diagnostic probe without prematurely reducing difficulty.
4. **Repeated weak answers**: Engine gathers repeated evidence and steps down difficulty or pivots topic.
5. **Basic correct vs. Advanced struggling**: Verifies that depth-weighted scoring and knowledge profiling accurately differentiate fundamentals from advanced mastery.
6. **Avoiding repeated questions**: Ensures previously asked questions are excluded from future prompts.
7. **Moving to a new topic**: Graceful topic rotation when sufficient evidence is gathered.
8. **End-to-end API workflows**: Complete start -> submit answers -> get report pipeline.

---

## 📋 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/interview/start` | Register candidate, select topics, generate initial question |
| `POST` | `/api/interview/answer` | Evaluate candidate answer, update profile, run adaptive engine, return next question |
| `GET` | `/api/interview/{id}` | Get current interview status and knowledge profile |
| `GET` | `/api/interview/{id}/report` | Compile and retrieve depth-weighted final evaluation report |
| `GET` | `/api/health` | Service health status and active AI provider |

---

## 🎨 Design & Accessibility
- **Glassmorphic Obsidian Theme**: Deep obsidian `#0a0d14` background with ambient indigo and cyan radial glows.
- **Animated Interviewer**: Live audio wave / pulse avatar indicating AI listening vs evaluating state.
- **Shortcuts**: `Ctrl + Enter` to submit answers immediately.
- **Exporting**: Click **Print / PDF** on the report page for a printer-friendly executive summary.
