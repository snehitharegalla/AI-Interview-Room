"""
Candidate Assessment Lifecycle & Auto-Report Integration Tests.

Validates:
1. Candidate starting interview.
2. Answering questions with zero leakage.
3. Concluding interview automatically generates FinalReport in database.
4. Candidate forbidden from accessing recruiter report endpoint.
5. Recruiter accessing full depth-weighted report with evaluation transcript.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, Interview, FinalReport

client = TestClient(app)


class TestCandidateFlow:

    def test_candidate_complete_lifecycle_and_auto_report(self):
        # 1. Login as Recruiter to create an interview
        rec_login = client.post("/api/auth/demo-login?role=recruiter")
        assert rec_login.status_code == 200
        rec_token = rec_login.json()["access_token"]
        rec_headers = {"Authorization": f"Bearer {rec_token}"}

        # Create interview via wizard
        wizard_payload = {
            "title": "Automated Lifecycle Evaluation",
            "job_role": "Distributed Systems Engineer",
            "experience_level": "Senior",
            "description": "Testing full end-to-end adaptive flow",
            "topics": ["Python Core", "Data Structures"],
            "difficulty": "intermediate",
            "difficulty_range": "all",
            "total_questions": 3,
            "duration_minutes": 20,
            "adaptive_mode": "enabled",
            "allow_followups": True,
            "prevent_repeated": True,
            "question_categories": ["Technical", "Conceptual"],
            "selected_question_ids": [],
            "candidate_name": "Test Candidate EndToEnd",
            "candidate_email": "candidate.e2e@example.com"
        }
        create_resp = client.post("/api/recruiter/interviews", json=wizard_payload, headers=rec_headers)
        assert create_resp.status_code == 200
        created_data = create_resp.json()
        interview_id = created_data["interview_id"]
        assert interview_id is not None

        # 2. Login as Candidate
        cand_login = client.post("/api/auth/demo-login?role=candidate")
        assert cand_login.status_code == 200
        cand_token = cand_login.json()["access_token"]
        cand_headers = {"Authorization": f"Bearer {cand_token}"}

        # 3. Candidate loads interview state (verify zero leakage)
        state_resp = client.get(f"/api/candidate/interview/{interview_id}", headers=cand_headers)
        assert state_resp.status_code == 200
        state = state_resp.json()
        assert "overall_score" not in state
        assert "weighted_score" not in state
        assert "knowledge_profile" not in state
        q1 = state["current_question"]
        assert q1 is not None
        assert "difficulty" not in q1
        assert "target_concept" not in q1
        assert q1["question_number"] == 1

        # 4. Candidate submits answer 1 (Strong)
        ans1_resp = client.post("/api/candidate/interview/answer", json={
            "interview_id": interview_id,
            "question_id": q1["question_id"],
            "candidate_answer": "In Python, functools.wraps updates the wrapper function to look like the wrapped function by copying attributes like __name__, __doc__, and __annotations__. Decorators use closures to wrap execution around target functions."
        }, headers=cand_headers)
        assert ans1_resp.status_code == 200
        ans1_data = ans1_resp.json()
        assert ans1_data["status"] == "in_progress"
        # Zero score leakage
        assert "score" not in ans1_data
        assert "evaluation" not in ans1_data
        assert "adaptive_decision" not in ans1_data
        q2 = ans1_data["next_question"]
        assert q2 is not None
        assert q2["question_number"] == 2
        assert "difficulty" not in q2

        # 5. Candidate submits answer 2 (Partial)
        ans2_resp = client.post("/api/candidate/interview/answer", json={
            "interview_id": interview_id,
            "question_id": q2["question_id"],
            "candidate_answer": "A Least Recently Used (LRU) cache uses a doubly-linked list paired with a hash map to achieve O(1) get and put operations. The map stores node references while the list orders elements by access recency."
        }, headers=cand_headers)
        assert ans2_resp.status_code == 200
        ans2_data = ans2_resp.json()
        assert ans2_data["status"] == "in_progress"
        q3 = ans2_data["next_question"]
        assert q3 is not None
        assert q3["question_number"] == 3

        # 6. Candidate submits answer 3 (Final question)
        ans3_resp = client.post("/api/candidate/interview/answer", json={
            "interview_id": interview_id,
            "question_id": q3["question_id"],
            "candidate_answer": "Consistent hashing maps nodes and keys onto a circular ring using hashes. When a node leaves, only keys mapped to that node are redistributed to its successor, minimizing cache misses across the cluster."
        }, headers=cand_headers)
        assert ans3_resp.status_code == 200
        ans3_data = ans3_resp.json()
        assert ans3_data["status"] == "completed"
        assert ans3_data["next_question"] is None
        # Zero score leakage
        assert "score" not in ans3_data
        assert "evaluation" not in ans3_data

        # 7. Verify FinalReport was automatically created in the database
        db = SessionLocal()
        try:
            report_in_db = db.query(FinalReport).filter(FinalReport.interview_id == interview_id).first()
            assert report_in_db is not None
            assert report_in_db.overall_score > 0
            assert report_in_db.weighted_score > 0
            assert report_in_db.hiring_recommendation in ["Strong Hire", "Hire", "Lean Hire", "Re-evaluate", "No Hire"]
            assert len(report_in_db.transcript) == 3
        finally:
            db.close()

        # 7. Verify candidate is FORBIDDEN from accessing the report API
        cand_rep_resp = client.get(f"/api/interview/{interview_id}/report", headers=cand_headers)
        assert cand_rep_resp.status_code == 403

        # 8. Verify recruiter CAN access the report API
        rec_rep_resp = client.get(f"/api/interview/{interview_id}/report", headers=rec_headers)
        assert rec_rep_resp.status_code == 200
        rec_rep_data = rec_rep_resp.json()
        assert rec_rep_data["candidate_name"] == "Test Candidate EndToEnd"
        assert rec_rep_data["weighted_score"] > 0
        assert len(rec_rep_data["transcript"]) == 3
        assert rec_rep_data["transcript"][0]["score"] > 0
