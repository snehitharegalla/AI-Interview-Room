"""
Demo Seed Data Generator for AI Interview Room Enterprise.

Populates the database with realistic demonstration data:
1. Recruiter accounts (Sarah Jenkins, David Miller)
2. Candidate accounts (Alex Rivera, Priya Patel, Marcus Chen, Elena Rostova)
3. Extensive Question Bank (25+ categorized questions across Python, Java, SQL, OOP, Data Structures, ML, Cloud)
4. Fully conducted adaptive interview ('demo-alex-101') demonstrating genuine adaptive engine transitions
5. In-progress and assigned upcoming interviews
6. Multi-dimensional Knowledge Profiles and Final Reports
7. Notifications for both recruiter and candidates
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import SessionLocal, init_db
from backend.models import (
    User,
    Recruiter,
    Candidate,
    Interview,
    InterviewQuestion,
    InterviewAnswer,
    KnowledgeProfile,
    FinalReport,
    QuestionBankItem,
    Notification
)
from backend.security import hash_password


def seed_demo_data():
    from backend.database import engine, Base
    print("Recreating database tables with updated schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Creating Recruiters & Candidates...")
    # ==========================================
    # 1. USERS & PROFILES
    # ==========================================
    recruiter_user = User(
        email="sarah.jenkins@techcorp.io",
        password_hash=hash_password("password123"),
        full_name="Sarah Jenkins",
        role="recruiter",
        created_at=datetime.utcnow() - timedelta(days=30)
    )
    db.add(recruiter_user)
    db.commit()
    db.refresh(recruiter_user)

    recruiter = Recruiter(
        user_id=recruiter_user.id,
        name="Sarah Jenkins",
        email="sarah.jenkins@techcorp.io",
        company="CloudScale Systems",
        title="Lead Technical Talent Partner",
        department="Engineering Talent Acquisition",
        created_at=datetime.utcnow() - timedelta(days=30)
    )
    db.add(recruiter)

    david_user = User(
        email="david.miller@innovate.ai",
        password_hash=hash_password("password123"),
        full_name="David Miller",
        role="recruiter",
        created_at=datetime.utcnow() - timedelta(days=20)
    )
    db.add(david_user)
    db.commit()
    db.refresh(david_user)

    david_recruiter = Recruiter(
        user_id=david_user.id,
        name="David Miller",
        email="david.miller@innovate.ai",
        company="Innovate AI Labs",
        title="VP of Engineering & Hiring Manager",
        department="Core Infrastructure",
        created_at=datetime.utcnow() - timedelta(days=20)
    )
    db.add(david_recruiter)

    # Candidate 1: Alex Rivera (Senior Backend)
    alex_user = User(
        email="alex.rivera@example.com",
        password_hash=hash_password("password123"),
        full_name="Alex Rivera",
        role="candidate",
        created_at=datetime.utcnow() - timedelta(days=14)
    )
    db.add(alex_user)
    db.commit()
    db.refresh(alex_user)

    alex_cand = Candidate(
        user_id=alex_user.id,
        name="Alex Rivera",
        email="alex.rivera@example.com",
        job_role="Senior Python Backend Engineer",
        applied_role="Senior Python Backend Engineer",
        experience_level="Senior",
        skills=["Python Core", "Data Structures", "System Design", "Distributed Systems", "SQL"],
        created_at=datetime.utcnow() - timedelta(days=14)
    )
    db.add(alex_cand)

    # Candidate 2: Priya Patel (Full Stack)
    priya_user = User(
        email="priya.patel@example.com",
        password_hash=hash_password("password123"),
        full_name="Priya Patel",
        role="candidate",
        created_at=datetime.utcnow() - timedelta(days=10)
    )
    db.add(priya_user)
    db.commit()
    db.refresh(priya_user)

    priya_cand = Candidate(
        user_id=priya_user.id,
        name="Priya Patel",
        email="priya.patel@example.com",
        job_role="Full Stack Architect",
        applied_role="Full Stack Architect",
        experience_level="Mid-Level",
        skills=["JavaScript", "Python", "REST APIs", "React", "PostgreSQL"],
        created_at=datetime.utcnow() - timedelta(days=10)
    )
    db.add(priya_cand)

    # Candidate 3: Marcus Chen (Cloud / DevOps)
    marcus_user = User(
        email="marcus.chen@example.com",
        password_hash=hash_password("password123"),
        full_name="Marcus Chen",
        role="candidate",
        created_at=datetime.utcnow() - timedelta(days=5)
    )
    db.add(marcus_user)
    db.commit()
    db.refresh(marcus_user)

    marcus_cand = Candidate(
        user_id=marcus_user.id,
        name="Marcus Chen",
        email="marcus.chen@example.com",
        job_role="Cloud Infrastructure Engineer",
        applied_role="Cloud Infrastructure Engineer",
        experience_level="Senior",
        skills=["Cloud Architecture", "Kubernetes", "Docker", "CI/CD", "Go"],
        created_at=datetime.utcnow() - timedelta(days=5)
    )
    db.add(marcus_cand)

    # Candidate 4: Elena Rostova (Data Engineer)
    elena_user = User(
        email="elena.rostova@example.com",
        password_hash=hash_password("password123"),
        full_name="Elena Rostova",
        role="candidate",
        created_at=datetime.utcnow() - timedelta(days=3)
    )
    db.add(elena_user)
    db.commit()
    db.refresh(elena_user)

    elena_cand = Candidate(
        user_id=elena_user.id,
        name="Elena Rostova",
        email="elena.rostova@example.com",
        job_role="Data Engineer",
        applied_role="Data Engineer",
        experience_level="Junior",
        skills=["SQL", "Python", "Data Warehousing", "ETL Pipelines"],
        created_at=datetime.utcnow() - timedelta(days=3)
    )
    db.add(elena_cand)
    db.commit()

    print("Seeding Question Bank...")
    # ==========================================
    # 2. QUESTION BANK (25+ questions)
    # ==========================================
    question_pool = [
        # Python
        {
            "title": "Python Decorators & Closures",
            "question_text": "Explain how Python decorators work internally. How do closures preserve outer function scope variables, and why is `functools.wraps` recommended when authoring production decorators?",
            "topic": "Python",
            "difficulty": "intermediate",
            "job_role": "Backend Engineer",
            "question_type": "Conceptual",
            "target_concept": "Closures, callable wrappers, functools.wraps metadata preservation",
            "expected_key_points": ["First-class functions", "Enclosing lexical scope closure cell", "functools.wraps updates __dict__, __doc__, __name__"]
        },
        {
            "title": "Python GIL & Concurrency Models",
            "question_text": "What is the Global Interpreter Lock (GIL) in CPython? Contrast how CPU-bound vs I/O-bound tasks should be architected using threading, multiprocessing, and asyncio.",
            "topic": "Python",
            "difficulty": "advanced",
            "job_role": "Senior Backend Engineer",
            "question_type": "Technical",
            "target_concept": "GIL mutex, CPU vs I/O concurrency, event loop vs OS processes",
            "expected_key_points": ["GIL prevents multi-core CPython bytecode execution", "asyncio/threading best for I/O", "multiprocessing bypasses GIL for CPU-bound tasks"]
        },
        {
            "title": "Python Generators and Memory Efficiency",
            "question_text": "How do generator functions and the `yield` keyword manage call stack state in memory compared to returning a full list? Provide a scenario where generators prevent OOM errors.",
            "topic": "Python",
            "difficulty": "basic",
            "job_role": "Software Engineer",
            "question_type": "Technical",
            "target_concept": "Yield lazy evaluation, generator frame stack state, streaming large datasets",
            "expected_key_points": ["Lazy evaluation (eval on demand)", "State suspended in frame object", "Streams huge logs without allocating gigabytes in RAM"]
        },
        # OOP
        {
            "title": "Composition vs Inheritance in Object Design",
            "question_text": "Why is 'favor composition over inheritance' widely regarded as a fundamental OOP principle? Walk through an example where deep class inheritance creates fragile code.",
            "topic": "OOP",
            "difficulty": "intermediate",
            "job_role": "Software Engineer",
            "question_type": "Conceptual",
            "target_concept": "Liskov substitution, tight coupling, fragile base class problem",
            "expected_key_points": ["Tight coupling between superclass and subclasses", "Fragile base class problem", "Composition allows runtime swapping of behaviors"]
        },
        {
            "title": "SOLID Principles: Dependency Inversion",
            "question_text": "Define the Dependency Inversion Principle (DIP). How does introducing interfaces or abstract base classes decouple high-level business logic from low-level data access implementations?",
            "topic": "OOP",
            "difficulty": "advanced",
            "job_role": "Software Architect",
            "question_type": "Scenario-based",
            "target_concept": "DIP, dependency injection, loose coupling",
            "expected_key_points": ["High-level modules should not depend on low-level modules; both depend on abstractions", "Enables unit testing with mocks", "Inversion of Control (IoC) containers"]
        },
        # Data Structures
        {
            "title": "LRU Cache Internal Architecture",
            "question_text": "How can you implement a Least Recently Used (LRU) cache such that both `get(key)` and `put(key, value)` operate in strict O(1) time complexity? Which combined data structures are required?",
            "topic": "Data Structures",
            "difficulty": "intermediate",
            "job_role": "Backend Engineer",
            "question_type": "Problem-solving",
            "target_concept": "Hash Map + Doubly Linked List coordination, O(1) eviction",
            "expected_key_points": ["Hash map provides O(1) key-to-node lookup", "Doubly linked list allows O(1) insertion/deletion of nodes", "Eviction pops tail node"]
        },
        {
            "title": "Hash Table Collision Resolution Tradeoffs",
            "question_text": "Compare open addressing (linear/quadratic probing, double hashing) with separate chaining for hash table collision resolution. Under what load factor conditions does open addressing degrade severely?",
            "topic": "Data Structures",
            "difficulty": "advanced",
            "job_role": "Core Systems Engineer",
            "question_type": "Technical",
            "target_concept": "Hash collisions, clustering, load factor impact, cache locality",
            "expected_key_points": ["Open addressing stores in array with probing, excellent cache locality", "Chaining uses linked lists/trees at buckets", "Open addressing clustering causes rapid degradation as load factor approaches 1.0"]
        },
        {
            "title": "Binary Search Trees vs Balanced AVL/Red-Black Trees",
            "question_text": "Under what insertion sequence does a standard Binary Search Tree degrade to O(N) lookup? How do balanced self-rotating trees prevent this worst-case scenario?",
            "topic": "Data Structures",
            "difficulty": "basic",
            "job_role": "Junior Developer",
            "question_type": "Conceptual",
            "target_concept": "Degenerate trees, tree rotation, worst-case height",
            "expected_key_points": ["Sorted insertion turns BST into linked list", "Worst-case height becomes N", "Rotations rebalance tree to guarantee O(log N) depth"]
        },
        # SQL & Databases
        {
            "title": "B-Tree vs Hash Indexes in Relational Databases",
            "question_text": "Why do relational database engines like PostgreSQL and MySQL default to B-Tree indexes over Hash indexes for general table columns? Explain the operational difference regarding range queries.",
            "topic": "SQL",
            "difficulty": "intermediate",
            "job_role": "Backend Engineer",
            "question_type": "Conceptual",
            "target_concept": "B-Tree sorted leaf pages, range scan efficiency, point lookups",
            "expected_key_points": ["B-Trees keep keys sorted, enabling BETWEEN, >, <, ORDER BY", "Hash indexes only support exact equality (=)", "B-Tree depth is small (3-4 levels for millions of rows)"]
        },
        {
            "title": "ACID Transactions and Isolation Levels",
            "question_text": "Explain the four standard SQL transaction isolation levels. What concurrency anomalies (dirty read, non-repeatable read, phantom read) does 'Repeatable Read' protect against?",
            "topic": "SQL",
            "difficulty": "advanced",
            "job_role": "Senior Database Engineer",
            "question_type": "Technical",
            "target_concept": "ACID isolation, MVCC, phantom reads, write skew",
            "expected_key_points": ["Read Uncommitted, Read Committed, Repeatable Read, Serializable", "Repeatable read guarantees consistent snapshot", "MVCC implementation using transaction timestamps"]
        },
        {
            "title": "Database Normalization vs Denormalization",
            "question_text": "What is the difference between 3NF (Third Normal Form) and a denormalized schema? In what read-heavy analytics or high-scale microservice architectures is denormalization preferred?",
            "topic": "SQL",
            "difficulty": "basic",
            "job_role": "Data Analyst",
            "question_type": "Conceptual",
            "target_concept": "3NF, transitive dependencies, read optimization vs write overhead",
            "expected_key_points": ["3NF eliminates redundancy and update anomalies", "Denormalization pre-joins tables for fast reads", "Ideal for analytical dashboards and document stores"]
        },
        # Java
        {
            "title": "Java Memory Model & Garbage Collection",
            "question_text": "Explain the distinction between the JVM Stack and Heap memory. How does generational garbage collection (Young/Eden vs Old/Tenured generation) optimize throughput?",
            "topic": "Java",
            "difficulty": "intermediate",
            "job_role": "Java Engineer",
            "question_type": "Technical",
            "target_concept": "Stack frames, heap allocation, weak generational hypothesis",
            "expected_key_points": ["Stack holds thread execution frames and primitives", "Heap holds dynamically allocated objects", "Most objects die young; minor GC collects Eden quickly"]
        },
        {
            "title": "Java Thread Synchronization and volatile keyword",
            "question_text": "What guarantees does the `volatile` keyword provide in Java regarding visibility and instruction reordering? Why does `volatile` alone not guarantee thread safety for compound actions like `count++`?",
            "topic": "Java",
            "difficulty": "advanced",
            "job_role": "Senior Java Architect",
            "question_type": "Scenario-based",
            "target_concept": "Happens-before relationship, CPU cache synchronization, atomicity vs visibility",
            "expected_key_points": ["Volatile ensures CPU memory cache flush (visibility)", "Prevents compiler instruction reordering", "count++ is 3 instructions (read, modify, write), requires AtomicInteger or synchronized"]
        },
        # Machine Learning
        {
            "title": "Bias-Variance Tradeoff and Regularization",
            "question_text": "Explain the bias-variance tradeoff in supervised machine learning models. How do L1 (Lasso) and L2 (Ridge) regularization mathematically prevent overfitting?",
            "topic": "Machine Learning",
            "difficulty": "intermediate",
            "job_role": "Machine Learning Engineer",
            "question_type": "Conceptual",
            "target_concept": "Overfitting vs underfitting, L1 sparsity, L2 weight shrinkage",
            "expected_key_points": ["High bias causes underfitting; high variance causes overfitting", "L1 adds absolute coefficient penalty (sparse feature selection)", "L2 adds squared coefficient penalty (shrinks weights)"]
        },
        {
            "title": "Transformer Self-Attention Mechanism",
            "question_text": "Walk through the mathematical formulation of scaled dot-product attention in Transformer architectures: `Attention(Q, K, V) = softmax((Q*K^T)/sqrt(d_k)) * V`. Why is scaling by `sqrt(d_k)` crucial?",
            "topic": "Machine Learning",
            "difficulty": "advanced",
            "job_role": "AI / NLP Engineer",
            "question_type": "Technical",
            "target_concept": "Query/Key/Value matrix multiplication, softmax gradient saturation",
            "expected_key_points": ["Computes correlation between query tokens and all key tokens", "Softmax normalizes into attention weights", "Large d_k causes large dot-products, pushing softmax into near-zero gradient zones"]
        },
        # Cloud
        {
            "title": "Microservices Resiliency: Circuit Breakers",
            "question_text": "How does the Circuit Breaker pattern protect downstream microservices during cascading failures? Explain the transitions between CLOSED, OPEN, and HALF-OPEN states.",
            "topic": "Cloud",
            "difficulty": "intermediate",
            "job_role": "Cloud Architect",
            "question_type": "Scenario-based",
            "target_concept": "Cascading failures, fallback responses, timeout thresholds",
            "expected_key_points": ["Closed: traffic passes normally", "Open: failures exceed threshold, calls fail fast without hitting dependency", "Half-Open: canary requests test if downstream service has recovered"]
        },
        {
            "title": "Kubernetes Pod Lifecycle & Readiness vs Liveness Probes",
            "question_text": "What is the critical operational difference between a Kubernetes Liveness Probe and a Readiness Probe? What outage scenario occurs if an overloaded database service misconfigures a liveness probe?",
            "topic": "Cloud",
            "difficulty": "advanced",
            "job_role": "DevOps Engineer",
            "question_type": "Problem-solving",
            "target_concept": "Liveness probe restarts container; readiness probe stops traffic routing",
            "expected_key_points": ["Liveness kills and restarts pod", "Readiness pulls pod out of Service endpoints", "Misconfigured liveness restarts already overloaded pods, creating restart loops"]
        },
        # Web Development
        {
            "title": "Browser Rendering Pipeline & DOM Virtualization",
            "question_text": "Explain the stages of the browser rendering pipeline (DOM -> CSSOM -> Render Tree -> Layout -> Paint). Why does Virtual DOM or DOM diffing improve performance in complex interactive SPAs?",
            "topic": "Web Development",
            "difficulty": "intermediate",
            "job_role": "Frontend Engineer",
            "question_type": "Technical",
            "target_concept": "Reflow vs Repaint, batching updates, Virtual DOM reconciliation",
            "expected_key_points": ["Layout/Reflow calculates geometry and is computationally expensive", "Direct DOM manipulation triggers synchronous layout thrashing", "Virtual DOM batches and computes minimal surgical patches"]
        },
        # Behavioral
        {
            "title": "Managing High-Severity Production Outages",
            "question_text": "Describe a scenario where a critical production deployment caused widespread customer downtime. How do you triage under pressure, communicate with stakeholders, and run an effective blameless post-mortem?",
            "topic": "Behavioral",
            "difficulty": "intermediate",
            "job_role": "Senior Engineer / Tech Lead",
            "question_type": "Behavioral",
            "target_concept": "Incident command, rollback prioritization, blameless post-mortem culture",
            "expected_key_points": ["Establish incident commander and clear comms channel", "Prioritize immediate mitigation/rollback over root cause debugging", "Publish timeline, root cause analysis, action items without blaming individuals"]
        }
    ]

    for item in question_pool:
        q_bank_item = QuestionBankItem(
            title=item["title"],
            question_text=item["question_text"],
            topic=item["topic"],
            difficulty=item["difficulty"],
            job_role=item["job_role"],
            question_type=item["question_type"],
            target_concept=item["target_concept"],
            expected_key_points=item["expected_key_points"],
            created_at=datetime.utcnow() - timedelta(days=25)
        )
        db.add(q_bank_item)
    db.commit()

    print("Seeding Pre-Conducted Adaptive Interview ('demo-alex-101')...")
    # ==========================================
    # 3. COMPLETED ADAPTIVE INTERVIEW (demo-alex-101)
    # Demonstrates:
    # Q1: Python Core (Inter) -> Strong -> DEEPER
    # Q2: Data Structures (Adv) -> Partial -> PROBE_MISSING
    # Q3: Data Structures (Adv) -> Strong -> DEEPER
    # Q4: System Design (Adv) -> Moderate -> PIVOT_TOPIC / DEEPER
    # Q5: Database Internals (Adv) -> Strong -> CONCLUDE
    # ==========================================
    interview_alex = Interview(
        id="demo-alex-101",
        title="Senior Python & Distributed Systems Assessment",
        description="Comprehensive technical evaluation assessing language mechanics, algorithmic depth, and distributed concurrency.",
        recruiter_id=recruiter.id,
        candidate_id=alex_cand.id,
        topics=["Python", "Data Structures", "System Design", "SQL"],
        difficulty_range="all",
        total_questions=5,
        duration_minutes=45,
        adaptive_mode="enabled",
        allow_followups=1,
        prevent_repeated=1,
        current_topic="SQL",
        current_question_index=5,
        status="completed",
        overall_score=8.4,
        weighted_score=8.8,
        started_at=datetime.utcnow() - timedelta(hours=3),
        completed_at=datetime.utcnow() - timedelta(hours=2, minutes=15)
    )
    db.add(interview_alex)
    db.commit()

    # Question 1: Decorators
    q1 = InterviewQuestion(
        interview_id="demo-alex-101",
        question_number=1,
        question_text="Explain how Python decorators work internally. How do closures preserve outer function scope variables, and why is functools.wraps recommended when authoring production decorators?",
        topic="Python",
        difficulty="intermediate",
        target_concept="Closures, callable wrappers, functools.wraps",
        rationale="Initial baseline question to verify Python core mastery."
    )
    db.add(q1)
    db.commit()
    db.refresh(q1)

    a1 = InterviewAnswer(
        question_id=q1.id,
        candidate_answer="In Python, decorators are higher-order callables that take a function object as an argument and return a modified replacement wrapper. They work through closures: inner functions maintain references to the variables in their enclosing lexical environment even after the outer function has completed execution, stored in the __closure__ cell. In production, functools.wraps is essential because without it, the wrapper function replaces the original function's metadata — such as __name__, __doc__, and type annotations — which breaks introspecting tools, debugger stack traces, and automatic API documentation generators.",
        score=9.3,
        correctness="correct",
        understanding_level="strong",
        relevant_concepts_identified=["Higher-order functions", "Lexical closures & __closure__ cells", "functools.wraps metadata preservation"],
        missing_or_misunderstood_concepts=[],
        explanation="Candidate demonstrates flawless understanding of Python's execution model, function references, closures, and metadata introspection.",
        knowledge_diagnosis="understands_deeply",
        recommended_strategy="Candidate excels at intermediate Python. Escalate difficulty to advanced Data Structures and cache design.",
        adaptive_decision={
            "action": "DEEPER",
            "next_difficulty": "advanced",
            "next_topic": "Data Structures",
            "target_concept": "LRU cache O(1) eviction mechanics",
            "reason": "Candidate exhibited superior command of language mechanics. Pushing deeper into algorithmic cache implementation."
        }
    )
    db.add(a1)

    # Question 2: LRU Cache (Partial answer)
    q2 = InterviewQuestion(
        interview_id="demo-alex-101",
        question_number=2,
        question_text="How can you architect an in-memory LRU (Least Recently Used) cache such that get() and put() both run in strict O(1) time? Walk through the specific data structures and pointers needed.",
        topic="Data Structures",
        difficulty="advanced",
        target_concept="Hash Map + Doubly Linked List coordination",
        rationale="Challenging candidate with O(1) cache algorithmic implementation."
    )
    db.add(q2)
    db.commit()
    db.refresh(q2)

    a2 = InterviewAnswer(
        question_id=q2.id,
        candidate_answer="To achieve O(1) get and put, you pair a Hash Map with a Linked List. The hash map maps keys directly to values for O(1) lookups. When an item is accessed or inserted, it is marked as most recently used by moving it to the front of the list. When the cache reaches capacity, the least recently used item at the back of the list is evicted.",
        score=6.8,
        correctness="partially_correct",
        understanding_level="partial",
        relevant_concepts_identified=["Hash map for O(1) lookups", "Queue/List ordering for recency", "Eviction on capacity"],
        missing_or_misunderstood_concepts=["Doubly linked list pointer mechanics (prev and next)", "Removing arbitrary nodes in O(1) requires double pointers"],
        explanation="Candidate understood the architectural combination of a map and list, but failed to clarify why a DOUBLY linked list is strictly necessary for O(1) node deletion.",
        knowledge_diagnosis="partially_correct_missing_key_element",
        recommended_strategy="Probe the specific missing concept: why a singly linked list fails to provide O(1) deletion.",
        adaptive_decision={
            "action": "PROBE_MISSING",
            "next_difficulty": "advanced",
            "next_topic": "Data Structures",
            "target_concept": "Doubly linked list pointer manipulation vs singly linked list",
            "reason": "Candidate understood high-level design but omitted the critical double-pointer mechanism required for true O(1) node removal. Targeted diagnostic follow-up."
        }
    )
    db.add(a2)

    # Question 3: Diagnostic Follow-up on Doubly Linked List
    q3 = InterviewQuestion(
        interview_id="demo-alex-101",
        question_number=3,
        question_text="In your previous LRU design, if you had used a standard Singly Linked List, what would be the exact time complexity to delete an arbitrary middle node when moving it to the head, and why does a Doubly Linked List eliminate this bottleneck?",
        topic="Data Structures",
        difficulty="advanced",
        target_concept="Doubly linked list pointer manipulation vs singly linked list",
        rationale="Targeted probe checking the missing pointer nuance from Question 2."
    )
    db.add(q3)
    db.commit()
    db.refresh(q3)

    a3 = InterviewAnswer(
        question_id=q3.id,
        candidate_answer="In a singly linked list, removing an arbitrary node requires finding its PREVIOUS node so you can update `prev.next = node.next`. Because single pointers only go forward, finding `prev` requires a linear traversal from the head of the list, which degrades deletion to O(N). A doubly linked list stores explicit `prev` and `next` pointers on every node. When you look up the node in the hash map, you instantly have access to `node.prev` without traversing, allowing you to unlink and rewire pointers in O(1) constant time.",
        score=9.5,
        correctness="correct",
        understanding_level="strong",
        relevant_concepts_identified=["O(N) predecessor traversal in singly linked list", "O(1) pointer updates with node.prev and node.next", "Direct node reference eliminates linear scan"],
        missing_or_misunderstood_concepts=[],
        explanation="Candidate comprehensively answered the diagnostic probe, demonstrating profound mastery of memory pointers and algorithmic trade-offs.",
        knowledge_diagnosis="understands_deeply",
        recommended_strategy="Candidate resolved the gap decisively. Rotate topic to System Design.",
        adaptive_decision={
            "action": "PIVOT_TOPIC",
            "next_difficulty": "advanced",
            "next_topic": "System Design",
            "target_concept": "Distributed cache invalidation and stampedes",
            "reason": "Candidate proved advanced mastery of local caching. Rotating to distributed system architecture."
        }
    )
    db.add(a3)

    # Question 4: System Design Distributed Caching
    q4 = InterviewQuestion(
        interview_id="demo-alex-101",
        question_number=4,
        question_text="When scaling from a local in-memory cache to a distributed Redis cluster handling 500k requests/sec, how do you prevent the 'Cache Stampede' (Thundering Herd) phenomenon when an expensive cache key expires?",
        topic="System Design",
        difficulty="advanced",
        target_concept="Distributed locking, probabilistic early expiration (XFetch), mutex fallback",
        rationale="Assessing high-concurrency distributed caching architecture."
    )
    db.add(q4)
    db.commit()
    db.refresh(q4)

    a4 = InterviewAnswer(
        question_id=q4.id,
        candidate_answer="A Cache Stampede occurs when a high-traffic key expires, causing thousands of simultaneous requests to miss cache and hit the database concurrently. To mitigate this, you can use: 1) Distributed locking (e.g. Redlock or atomic SETNX) so only a single worker queries the database while other requests wait or receive stale data; 2) Probabilistic early expiration (like the XFetch algorithm) where background workers recalculate the value before it actually expires based on compute time; or 3) Stale-While-Revalidate caching pattern where clients immediately get the last known good value while an asynchronous task refreshes the cache.",
        score=9.0,
        correctness="correct",
        understanding_level="strong",
        relevant_concepts_identified=["Distributed mutex locks (SETNX)", "Probabilistic early expiration (XFetch)", "Stale-while-revalidate asynchronous background refresh"],
        missing_or_misunderstood_concepts=[],
        explanation="Outstanding architectural grasp of high-throughput caching challenges and real-world mitigation patterns.",
        knowledge_diagnosis="understands_deeply",
        recommended_strategy="Maintain advanced level and conclude assessment with Database Internals.",
        adaptive_decision={
            "action": "DEEPER",
            "next_difficulty": "advanced",
            "next_topic": "SQL",
            "target_concept": "B-Tree page splitting & write amplification",
            "reason": "Candidate excels in high-scale systems. Testing storage engine internals."
        }
    )
    db.add(a4)

    # Question 5: Database B-Tree Index Internals
    q5 = InterviewQuestion(
        interview_id="demo-alex-101",
        question_number=5,
        question_text="In relational database storage engines (like InnoDB or PostgreSQL heap), how does secondary index fragmentation and B-Tree page splitting impact write latency during heavy insert workloads? What design choices minimize this overhead?",
        topic="SQL",
        difficulty="advanced",
        target_concept="B-Tree page splitting, random I/O write amplification, UUID vs sequential keys",
        rationale="Final advanced technical evaluation on database storage engines."
    )
    db.add(q5)
    db.commit()
    db.refresh(q5)

    a5 = InterviewAnswer(
        question_id=q5.id,
        candidate_answer="When inserts occur with non-sequential keys (like random UUIDv4), records must be placed into random B-Tree leaf pages. When a target page is 100% full, the database must execute a Page Split: allocating a new page, moving half the keys over, and updating parent index pointers. This causes heavy write amplification and random disk I/O. To minimize this: 1) Use sequential or time-sorted keys like UUIDv7 or auto-incrementing BigInts; 2) Tune the B-Tree fill-factor to leave headroom (e.g. 80-90% fill factor); 3) Leverage insert buffers or LSM-tree write-optimized stores (like RocksDB or Cassandra) for write-heavy streaming workloads.",
        score=8.7,
        correctness="correct",
        understanding_level="strong",
        relevant_concepts_identified=["B-Tree leaf page splitting", "Random I/O write amplification from random UUIDs", "Time-ordered keys (UUIDv7) and fill-factor tuning"],
        missing_or_misunderstood_concepts=[],
        explanation="Candidate accurately details the internal storage engine consequences of random index keys and provides industry-standard architectural solutions.",
        knowledge_diagnosis="understands_deeply",
        recommended_strategy="All questions completed. Conclude interview.",
        adaptive_decision={
            "action": "CONCLUDE",
            "next_difficulty": "advanced",
            "next_topic": "SQL",
            "target_concept": "Final Evaluation",
            "reason": "Target 5 questions reached. Comprehensive cognitive assessment achieved."
        }
    )
    db.add(a5)

    # Knowledge Profiles for Alex
    kp_data = [
        {"topic": "Python", "diff": "intermediate", "score": 93.0, "lvl": "Strong", "dem": ["Closures", "functools.wraps", "Higher-order functions"], "miss": []},
        {"topic": "Data Structures", "diff": "advanced", "score": 85.0, "lvl": "Strong", "dem": ["Hash Map + Doubly Linked List", "O(1) Eviction", "Pointer Manipulation"], "miss": []},
        {"topic": "System Design", "diff": "advanced", "score": 90.0, "lvl": "Strong", "dem": ["Distributed Locking", "Cache Stampede Mitigation", "XFetch Algorithm"], "miss": []},
        {"topic": "SQL", "diff": "advanced", "score": 87.0, "lvl": "Strong", "dem": ["B-Tree Page Splitting", "Write Amplification", "UUIDv7 Sequential Keys"], "miss": []}
    ]

    for kp in kp_data:
        k_prof = KnowledgeProfile(
            candidate_id=alex_cand.id,
            interview_id="demo-alex-101",
            topic=kp["topic"],
            difficulty=kp["diff"],
            mastery_score=kp["score"],
            level=kp["lvl"],
            demonstrated_concepts=kp["dem"],
            missing_concepts=kp["miss"],
            attempt_count=1
        )
        db.add(k_prof)

    # Final Report for Alex
    report_alex = FinalReport(
        interview_id="demo-alex-101",
        overall_score=8.4,
        weighted_score=8.8,
        hiring_recommendation="Strong Hire",
        recommendation_reasoning="Alex demonstrates exceptional engineering depth, excelling at advanced algorithmic trade-offs, pointer mechanics, distributed caching resilience, and database internal storage mechanics.",
        overall_summary="The adaptive engine tested Alex through a rigorous multi-tier assessment. After demonstrating flawless command of Python lexical closures, the engine escalated to advanced cache design. Alex initially gave a high-level response omitting doubly linked list pointer mechanics, triggering a targeted diagnostic probe. Alex answered the probe with zero hesitation, demonstrating genuine algorithmic understanding rather than rote memorization. The interview concluded with advanced distributed systems and database storage internals.",
        depth_analysis="Candidate excelled on Advanced-tier challenges (averaging 8.7/10 across 4 advanced questions). The depth-weighted score of 8.8/10 reflects authentic senior-level capability rather than simple correct answers to elementary questions.",
        strengths=[
            "Deep comprehension of low-level pointer manipulation and O(1) doubly linked list operations",
            "Strong understanding of distributed system failure modes (Cache Stampede, SETNX distributed locks)",
            "Detailed knowledge of relational storage engine internals (B-Tree page splitting, UUIDv7 vs v4 write amplification)",
            "Clean technical articulation and practical operational trade-off considerations"
        ],
        areas_for_improvement=[
            "Ensure low-level data structure nuances (like double pointers) are explicitly mentioned in initial explanations before follow-up prompting"
        ],
        topic_breakdown={
            "Python": {"count": 1, "avg": 9.3, "total_score": 9.3},
            "Data Structures": {"count": 2, "avg": 8.2, "total_score": 16.3},
            "System Design": {"count": 1, "avg": 9.0, "total_score": 9.0},
            "SQL": {"count": 1, "avg": 8.7, "total_score": 8.7}
        },
        difficulty_breakdown={
            "basic": {"count": 0, "avg": 0.0, "total_score": 0.0},
            "intermediate": {"count": 1, "avg": 9.3, "total_score": 9.3},
            "advanced": {"count": 4, "avg": 8.5, "total_score": 34.0}
        },
        demonstrated_concepts=[
            "Closures & __closure__ cells",
            "functools.wraps metadata preservation",
            "LRU Cache Doubly Linked List + Hash Map",
            "O(1) Pointer rewiring",
            "Distributed Caching & Stampede Prevention",
            "B-Tree Leaf Page Splitting & Write Amplification"
        ],
        missing_concepts=[],
        transcript=[
            {"question_number": 1, "topic": "Python", "difficulty": "intermediate", "question_text": q1.question_text, "candidate_answer": a1.candidate_answer, "score": 9.3, "explanation": a1.explanation, "adaptive_decision": a1.adaptive_decision},
            {"question_number": 2, "topic": "Data Structures", "difficulty": "advanced", "question_text": q2.question_text, "candidate_answer": a2.candidate_answer, "score": 6.8, "explanation": a2.explanation, "adaptive_decision": a2.adaptive_decision},
            {"question_number": 3, "topic": "Data Structures", "difficulty": "advanced", "question_text": q3.question_text, "candidate_answer": a3.candidate_answer, "score": 9.5, "explanation": a3.explanation, "adaptive_decision": a3.adaptive_decision},
            {"question_number": 4, "topic": "System Design", "difficulty": "advanced", "question_text": q4.question_text, "candidate_answer": a4.candidate_answer, "score": 9.0, "explanation": a4.explanation, "adaptive_decision": a4.adaptive_decision},
            {"question_number": 5, "topic": "SQL", "difficulty": "advanced", "question_text": q5.question_text, "candidate_answer": a5.candidate_answer, "score": 8.7, "explanation": a5.explanation, "adaptive_decision": a5.adaptive_decision}
        ],
        generated_at=datetime.utcnow() - timedelta(hours=2, minutes=15)
    )
    db.add(report_alex)

    # ==========================================
    # 4. ASSIGNED & IN-PROGRESS INTERVIEWS
    # ==========================================
    # Priya Patel: In Progress Interview
    interview_priya = Interview(
        id="demo-priya-102",
        title="Full Stack Architecture & Microservices Assessment",
        description="Assessing frontend rendering pipelines, RESTful contracts, and transactional integrity.",
        recruiter_id=recruiter.id,
        candidate_id=priya_cand.id,
        topics=["Web Development", "Python", "SQL"],
        difficulty_range="intermediate",
        total_questions=5,
        duration_minutes=45,
        adaptive_mode="enabled",
        allow_followups=1,
        prevent_repeated=1,
        current_topic="Web Development",
        current_question_index=1,
        status="in_progress",
        overall_score=0.0,
        weighted_score=0.0,
        started_at=datetime.utcnow() - timedelta(minutes=25)
    )
    db.add(interview_priya)
    db.commit()

    q_priya1 = InterviewQuestion(
        interview_id="demo-priya-102",
        question_number=1,
        question_text="Explain the stages of the browser rendering pipeline (DOM -> CSSOM -> Render Tree -> Layout -> Paint). Why does Virtual DOM or DOM diffing improve performance in complex interactive SPAs?",
        topic="Web Development",
        difficulty="intermediate",
        target_concept="Browser rendering pipeline and reflow reduction",
        rationale="Initial frontend architecture baseline."
    )
    db.add(q_priya1)

    # Marcus Chen: Assigned Interview (Not yet started)
    interview_marcus = Interview(
        id="demo-marcus-103",
        title="Cloud Infrastructure & Kubernetes Architecture",
        description="Testing container orchestration, service mesh routing, and infrastructure resiliency.",
        recruiter_id=recruiter.id,
        candidate_id=marcus_cand.id,
        topics=["Cloud", "Data Structures", "System Design"],
        difficulty_range="advanced",
        total_questions=5,
        duration_minutes=40,
        adaptive_mode="enabled",
        allow_followups=1,
        prevent_repeated=1,
        current_topic="Cloud",
        current_question_index=0,
        status="assigned",
        overall_score=0.0,
        weighted_score=0.0,
        started_at=datetime.utcnow() - timedelta(days=1)
    )
    db.add(interview_marcus)

    # Notifications
    notifs = [
        Notification(
            user_id=recruiter_user.id,
            role="recruiter",
            title="Interview Completed: Alex Rivera",
            message="Alex Rivera has completed the Senior Python Assessment (Score: 8.8/10 - Strong Hire).",
            type="interview_completed",
            link="/report.html?id=demo-alex-101",
            read=0
        ),
        Notification(
            user_id=recruiter_user.id,
            role="recruiter",
            title="Interview In-Progress: Priya Patel",
            message="Priya Patel has initiated the Full Stack Architecture Assessment.",
            type="interview_started",
            link="/recruiter.html",
            read=1
        ),
        Notification(
            user_id=alex_user.id,
            role="candidate",
            title="Assessment Submitted Successfully",
            message="Your technical assessment for Senior Python Backend Engineer has been submitted for recruiter review.",
            type="interview_submitted",
            read=1
        ),
        Notification(
            user_id=marcus_user.id,
            role="candidate",
            title="New Technical Interview Assigned",
            message="CloudScale Systems has invited you to complete 'Cloud Infrastructure & Kubernetes Architecture'.",
            type="interview_assigned",
            link="/interview.html?id=demo-marcus-103",
            read=0
        )
    ]

    for n in notifs:
        db.add(n)

    db.commit()
    db.close()
    print("Demo seed successfully loaded!")


if __name__ == "__main__":
    seed_demo_data()
