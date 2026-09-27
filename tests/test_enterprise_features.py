"""
Enterprise Features & Security Integration Tests.

Tests:
1. Role-based Authentication (Registration, Login, JWT verification).
2. Candidate Zero-Leakage Security (scores and internal AI logic strictly shielded).
3. Recruiter 7-Step Wizard & Dashboard Metrics.
4. Question Bank Search, Filter, CRUD, and Duplication.
5. Recruiter Analytics and Notifications.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestEnterpriseFeatures:

    def test_auth_registration_and_login(self):
        import uuid
        uid = str(uuid.uuid4())[:8]
        rec_email = f"test.recruiter.{uid}@testcorp.com"
        cand_email = f"test.candidate.{uid}@testcorp.com"

        # 1. Register Recruiter
        rec_payload = {
            "full_name": "Test Recruiter",
            "email": rec_email,
            "password": "securepassword123",
            "role": "recruiter",
            "company": "TestCorp Global",
            "title": "Senior Talent Partner"
        }
        res = client.post("/api/auth/register", json=rec_payload)
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["role"] == "recruiter"
        rec_token = data["access_token"]

        # 2. Register Candidate
        cand_payload = {
            "full_name": "Test Candidate",
            "email": cand_email,
            "password": "securepassword123",
            "role": "candidate",
            "job_role": "Backend Engineer",
            "experience_level": "Mid-Level"
        }
        res2 = client.post("/api/auth/register", json=cand_payload)
        assert res2.status_code == 200
        data2 = res2.json()
        assert "access_token" in data2
        assert data2["user"]["role"] == "candidate"

        # 3. Login
        login_res = client.post("/api/auth/login", json={
            "email": rec_email,
            "password": "securepassword123"
        })
        assert login_res.status_code == 200
        assert login_res.json()["user"]["role"] == "recruiter"

    def test_candidate_zero_leakage(self):
        """
        Verify that candidate API responses NEVER leak scores, evaluations,
        difficulty levels, or internal reasoning.
        """
        # Start an interview
        start_payload = {
            "candidate_name": "Security Test Candidate",
            "candidate_email": "security.cand@example.com",
            "job_role": "Systems Engineer",
            "experience_level": "Senior",
            "topics": ["Python", "SQL"],
            "total_questions": 3,
            "starting_difficulty": "intermediate"
        }
        start_res = client.post("/api/interview/start", json=start_payload)
        assert start_res.status_code == 200
        interview_id = start_res.json()["interview_id"]

        # Candidate fetches interview state via candidate route
        cand_res = client.get(f"/api/candidate/interview/{interview_id}")
        assert cand_res.status_code == 200
        cand_data = cand_res.json()

        # Check for ZERO LEAKAGE in candidate view
        q = cand_data.get("current_question", {})
        assert "difficulty" not in q  # Candidate must not see difficulty
        assert "target_concept" not in q
        assert "score" not in cand_data
        assert "evaluation" not in cand_data
        assert "knowledge_profile" not in cand_data

        # Submit answer via candidate endpoint
        ans_payload = {
            "interview_id": interview_id,
            "question_id": q["question_id"],
            "candidate_answer": "In Python, decorators wrap callables and preserve closures in lexical scope."
        }
        ans_res = client.post("/api/candidate/interview/answer", json=ans_payload)
        assert ans_res.status_code == 200
        ans_data = ans_res.json()

        # Verify candidate receives sanitized response
        assert "evaluation" not in ans_data
        assert "score" not in ans_data
        assert "adaptive_decision" not in ans_data
        assert "knowledge_profile" not in ans_data
        if ans_data.get("next_question"):
            nxt = ans_data["next_question"]
            assert "difficulty" not in nxt
            assert "target_concept" not in nxt
            assert "question_text" in nxt

    def test_recruiter_7step_wizard_interview_creation(self):
        """
        Tests interview creation via the multi-step recruiter wizard.
        """
        wizard_payload = {
            "title": "Senior Data & AI Systems Assessment",
            "job_role": "AI Systems Architect",
            "experience_level": "Senior",
            "description": "Comprehensive evaluation covering ML theory and distributed pipelines.",
            "topics": ["Machine Learning", "Python", "Cloud"],
            "difficulty": "advanced",
            "difficulty_range": "all",
            "total_questions": 5,
            "duration_minutes": 45,
            "adaptive_mode": "enabled",
            "allow_followups": True,
            "prevent_repeated": True,
            "question_categories": ["Technical", "Conceptual"],
            "candidate_name": "Wizard Candidate",
            "candidate_email": "wizard.candidate@example.com"
        }

        res = client.post("/api/recruiter/interviews", json=wizard_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "interview_id" in data
        assert data["total_questions"] == 5

    def test_question_bank_crud_and_duplicate(self):
        """
        Tests Question Bank search, filter, creation, update, duplicate, and deletion.
        """
        # 1. Create Question
        new_q = {
            "title": "RAFT Consensus Protocol Mechanics",
            "question_text": "Explain leader election and log replication in the RAFT distributed consensus protocol.",
            "topic": "Distributed Systems",
            "difficulty": "advanced",
            "job_role": "Senior Infrastructure Engineer",
            "question_type": "Technical",
            "target_concept": "Heartbeats, randomized election timeouts, log quorum commitment",
            "expected_key_points": ["Leader election via randomized timeouts", "Quorum majority log write ACK"]
        }
        res = client.post("/api/question-bank", json=new_q)
        assert res.status_code == 201
        created = res.json()
        q_id = created["id"]
        assert created["topic"] == "Distributed Systems"

        # 2. Search & Filter
        filter_res = client.get("/api/question-bank?topic=Distributed%20Systems")
        assert filter_res.status_code == 200
        items = filter_res.json()
        assert any(i["id"] == q_id for i in items)

        # 3. Duplicate Question
        dup_res = client.post(f"/api/question-bank/{q_id}/duplicate")
        assert dup_res.status_code == 200
        dup = dup_res.json()
        assert "(Copy)" in dup["title"]

        # 4. Delete duplicated
        del_res = client.delete(f"/api/question-bank/{dup['id']}")
        assert del_res.status_code == 200

    def test_recruiter_analytics_and_dashboard(self):
        """
        Tests Recruiter dashboard metrics and aggregated analytics endpoints.
        """
        dash_res = client.get("/api/recruiter/dashboard")
        assert dash_res.status_code == 200
        dash = dash_res.json()
        assert "metrics" in dash
        assert "total_candidates" in dash["metrics"]
        assert "recent_interviews" in dash

        analytics_res = client.get("/api/recruiter/analytics")
        assert analytics_res.status_code == 200
        analytics = analytics_res.json()
        assert "summary" in analytics
        assert "topic_performance" in analytics
        assert "difficulty_distribution" in analytics

    def test_candidate_forbidden_from_recruiter_endpoints(self):
        """
        Verify that authenticated candidate users receive HTTP 403 Forbidden
        when attempting to access recruiter-only APIs or reports.
        """
        import uuid
        uid = str(uuid.uuid4())[:8]
        cand_payload = {
            "full_name": "Restricted Candidate",
            "email": f"restricted.{uid}@testcorp.com",
            "password": "password123",
            "role": "candidate",
            "job_role": "Backend Engineer",
            "experience_level": "Mid-Level"
        }
        reg_res = client.post("/api/auth/register", json=cand_payload)
        assert reg_res.status_code == 200
        cand_token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {cand_token}"}

        # Candidate attempting to access Recruiter Dashboard
        dash_res = client.get("/api/recruiter/dashboard", headers=headers)
        assert dash_res.status_code == 403

        # Candidate attempting to access Recruiter Analytics
        analytics_res = client.get("/api/recruiter/analytics", headers=headers)
        assert analytics_res.status_code == 403

        # Candidate attempting to access Candidate Talent Directory
        cand_dir_res = client.get("/api/recruiter/candidates", headers=headers)
        assert cand_dir_res.status_code == 403

        # Candidate attempting to access evaluation report directly
        report_res = client.get("/api/interview/demo-alex-101/report", headers=headers)
        assert report_res.status_code == 403
        assert "Candidates are not permitted" in report_res.json()["detail"]

    def test_question_bank_role_filter_and_update(self):
        """
        Tests question bank updating and job role filtering.
        """
        # 1. Create a specialized question
        q_payload = {
            "title": "PostgreSQL MVCC & Vacuum Optimization",
            "question_text": "Explain how PostgreSQL Multi-Version Concurrency Control handles dead tuples and how autovacuum parameters prevent transaction ID wraparound.",
            "topic": "SQL",
            "difficulty": "advanced",
            "job_role": "Senior Database Engineer",
            "question_type": "Technical",
            "target_concept": "Dead tuples, transaction ID wraparound, autovacuum_vacuum_cost_limit",
            "expected_key_points": ["xmin/xmax tuple headers", "Autovacuum freeze"]
        }
        create_res = client.post("/api/question-bank", json=q_payload)
        assert create_res.status_code == 201
        created = create_res.json()
        q_id = created["id"]

        # 2. Filter by role
        role_res = client.get("/api/question-bank?job_role=Senior%20Database%20Engineer")
        assert role_res.status_code == 200
        role_items = role_res.json()
        assert any(item["id"] == q_id for item in role_items)

        # 3. Update question
        update_payload = {
            "title": "PostgreSQL MVCC & Autovacuum Tuning (Updated)",
            "difficulty": "intermediate"
        }
        update_res = client.put(f"/api/question-bank/{q_id}", json=update_payload)
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["title"] == "PostgreSQL MVCC & Autovacuum Tuning (Updated)"
        assert updated["difficulty"] == "intermediate"
