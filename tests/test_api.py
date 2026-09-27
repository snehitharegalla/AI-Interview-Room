"""
API Integration Tests.

Tests the FastAPI endpoints:
- POST /api/interview/start
- POST /api/interview/answer
- GET /api/interview/{interview_id}
- GET /api/interview/{interview_id}/report
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestInterviewAPI:

    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "provider" in data

    def test_full_adaptive_interview_workflow(self):
        # 1. Start Interview
        start_payload = {
            "candidate_name": "Test User",
            "candidate_email": "test.user@example.com",
            "job_role": "Backend Engineer",
            "experience_level": "Mid-Level",
            "topics": ["Python Core", "Data Structures"],
            "total_questions": 3,
            "starting_difficulty": "intermediate"
        }

        start_resp = client.post("/api/interview/start", json=start_payload)
        assert start_resp.status_code == 200
        session = start_resp.json()
        interview_id = session["interview_id"]
        assert interview_id is not None
        assert session["total_questions"] == 3
        q1 = session["first_question"]
        assert q1["question_number"] == 1
        assert len(q1["question_text"]) > 10

        # 2. Submit Question 1 Answer (Strong)
        ans1_payload = {
            "interview_id": interview_id,
            "question_id": q1["question_id"],
            "candidate_answer": "In Python, decorators are callables taking a function and returning a wrapper. They utilize closures to retain outer scope variables. Using functools.wraps preserves function docstrings, name attributes, and annotations by updating the wrapper's __dict__."
        }
        ans1_resp = client.post("/api/interview/answer", json=ans1_payload)
        assert ans1_resp.status_code == 200
        ans1_data = ans1_resp.json()
        assert ans1_data["status"] == "in_progress"
        assert ans1_data["evaluation"]["score"] >= 7.0
        assert ans1_data["next_question"] is not None

        q2 = ans1_data["next_question"]
        assert q2["question_number"] == 2

        # 3. Submit Question 2 Answer (Partial)
        ans2_payload = {
            "interview_id": interview_id,
            "question_id": q2["question_id"],
            "candidate_answer": "I know generators use yield instead of return to produce items one at a time, saving memory compared to lists. But I'm not totally sure about how send() passes values into generators."
        }
        ans2_resp = client.post("/api/interview/answer", json=ans2_payload)
        assert ans2_resp.status_code == 200
        ans2_data = ans2_resp.json()
        assert ans2_data["status"] == "in_progress"
        q3 = ans2_data["next_question"]
        assert q3["question_number"] == 3

        # 4. Submit Question 3 Answer (Final Question)
        ans3_payload = {
            "interview_id": interview_id,
            "question_id": q3["question_id"],
            "candidate_answer": "Hash tables compute a hash of the key and map it to an array bucket. In worst case with collisions it becomes O(N), but Python handles this with perturbation and open addressing to find alternate slots."
        }
        ans3_resp = client.post("/api/interview/answer", json=ans3_payload)
        assert ans3_resp.status_code == 200
        ans3_data = ans3_resp.json()
        assert ans3_data["status"] == "completed"
        assert ans3_data["next_question"] is None

        # 5. Fetch Interview State
        state_resp = client.get(f"/api/interview/{interview_id}")
        assert state_resp.status_code == 200
        state_data = state_resp.json()
        assert state_data["status"] == "completed"
        assert len(state_data["knowledge_profile"]) > 0

        # 6. Fetch Final Report
        report_resp = client.get(f"/api/interview/{interview_id}/report")
        assert report_resp.status_code == 200
        report_data = report_resp.json()
        assert report_data["candidate_name"] == "Test User"
        assert report_data["overall_score"] > 0
        assert report_data["weighted_score"] > 0
        assert "hiring_recommendation" in report_data
        assert len(report_data["transcript"]) == 3
        assert len(report_data["strengths"]) > 0

    def test_invalid_interview_handling(self):
        # Non-existent interview
        resp = client.get("/api/interview/non-existent-id")
        assert resp.status_code == 404

        # Non-existent report
        resp2 = client.get("/api/interview/non-existent-id/report")
        assert resp2.status_code == 404

    def test_direct_interview_prefix_endpoints(self):
        """Test the exact endpoints specified in the prompt: /interview/start, /interview/answer, etc."""
        start_payload = {
            "candidate_name": "Direct Route Candidate",
            "candidate_email": "direct@example.com",
            "job_role": "Full Stack Engineer",
            "experience_level": "Senior",
            "topics": ["Python Core"],
            "total_questions": 3
        }

        # POST /interview/start
        resp = client.post("/interview/start", json=start_payload)
        assert resp.status_code == 200
        data = resp.json()
        interview_id = data["interview_id"]
        q_id = data["first_question"]["question_id"]

        # GET /interview/{interview_id}
        state_resp = client.get(f"/interview/{interview_id}")
        assert state_resp.status_code == 200

        # POST /interview/answer
        ans_resp = client.post("/interview/answer", json={
            "interview_id": interview_id,
            "question_id": q_id,
            "candidate_answer": "Python uses reference counting along with a cyclic garbage collector to reclaim unreferenced memory."
        })
        assert ans_resp.status_code == 200

        # GET /interview/{interview_id}/report
        rep_resp = client.get(f"/interview/{interview_id}/report")
        assert rep_resp.status_code == 200
        assert rep_resp.json()["candidate_name"] == "Direct Route Candidate"
