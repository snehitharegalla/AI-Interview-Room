"""
AI Service Provider Module.

Provides an abstraction layer supporting:
1. Google Gemini (via google-genai)
2. OpenAI (via openai client)
3. Intelligent Mock/Demo Provider (instant local zero-config testing & bulletproof fallback)
"""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

AI_PROVIDER = os.getenv("AI_PROVIDER", "mock").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "")


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Safely extracts and parses a JSON object from text that may contain
    markdown formatting, code fences, or surrounding conversational text.
    """
    if not text:
        return {}

    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Extract JSON inside ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find first { and last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to parse JSON from response text: %s", text[:200])
    return {}


class MockAIService:
    """
    Intelligent simulated AI service for local offline demos and automated test suites.
    Responds dynamically according to the candidate's answers and adaptive directives.
    """

    @staticmethod
    def evaluate_answer(
        question_text: str,
        candidate_answer: str,
        topic: str,
        difficulty: str,
        target_concept: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dynamically analyzes candidate's answer based on length, keywords, and quality markers.
        """
        ans = candidate_answer.strip().lower()

        # Check for empty / non-substantive answers
        if len(ans) < 10 or ans in ["i don't know", "idk", "no idea", "pass", "skip"]:
            return {
                "score": 1.5,
                "correctness": "incorrect",
                "understanding_level": "weak",
                "relevant_concepts_identified": [],
                "missing_or_misunderstood_concepts": [
                    target_concept or f"Fundamental concepts of {topic}",
                    "Implementation principles",
                    "Core definitions"
                ],
                "explanation": f"The candidate was unable to provide a substantive explanation for the {topic} question. Foundational comprehension appears unproven.",
                "knowledge_diagnosis": "does_not_understand_concept",
                "recommended_strategy": f"Ask a basic diagnostic question to probe whether they possess rudimentary {topic} familiarity."
            }

        # Check for weak or confused answers
        weak_indicators = ["wrong", "not sure", "maybe", "confused", "guess", "i think it does the opposite"]
        if any(w in ans for w in weak_indicators) and len(ans) < 60:
            return {
                "score": 3.0,
                "correctness": "incorrect",
                "understanding_level": "weak",
                "relevant_concepts_identified": ["High-level terminology"],
                "missing_or_misunderstood_concepts": [
                    target_concept or "Memory & Execution model",
                    "Operational mechanics"
                ],
                "explanation": "The candidate mentioned surface terminology but displayed misconceptions regarding core mechanics.",
                "knowledge_diagnosis": "does_not_understand_concept",
                "recommended_strategy": "Ask a diagnostic question on the underlying mechanism before adjusting difficulty."
            }

        # Check for partial answers (has some substance but misses nuances or specific concepts)
        if len(ans) < 120 or "part" in ans or "basic" in ans or "simple" in ans:
            concept_name = target_concept or f"Underlying nuances in {topic}"
            return {
                "score": 6.5,
                "correctness": "partially_correct",
                "understanding_level": "partial",
                "relevant_concepts_identified": [
                    "High-level purpose and usage",
                    "Standard syntax and behavior"
                ],
                "missing_or_misunderstood_concepts": [
                    concept_name,
                    "Edge case handling / internal tradeoffs"
                ],
                "explanation": "The candidate understands the practical high-level purpose, but omitted internal tradeoffs and specific edge-case handling.",
                "knowledge_diagnosis": "partially_correct_missing_key_element",
                "recommended_strategy": f"Ask a targeted follow-up probing the specific missing concept: {concept_name}."
            }

        # Strong answer (detailed, articulate, well-explained)
        return {
            "score": 9.0,
            "correctness": "correct",
            "understanding_level": "strong",
            "relevant_concepts_identified": [
                f"{topic} core architectural patterns",
                target_concept or "Underlying data structure & complexity",
                "Efficiency & runtime tradeoffs",
                "Production safety & edge cases"
            ],
            "missing_or_misunderstood_concepts": [],
            "explanation": f"The candidate provided a comprehensive, technically sound answer. They articulated both conceptual definitions and practical performance implications.",
            "knowledge_diagnosis": "understands_deeply",
            "recommended_strategy": f"Escalate difficulty or explore advanced architectural edge cases in {topic}."
        }

    @staticmethod
    def generate_question(
        job_role: str,
        experience_level: str,
        topic: str,
        target_difficulty: str,
        adaptive_action: str,
        target_concept: str,
        adaptive_reason: str,
        previous_questions: List[str]
    ) -> Dict[str, Any]:
        """
        Generates realistic questions strictly aligned to the adaptive directive.
        """
        # Tailored bank of questions mapped by normalized topic and difficulty
        target_diff = (target_difficulty or "intermediate").lower()
        if target_diff not in ["basic", "intermediate", "advanced"]:
            target_diff = "intermediate"

        # Topic normalization
        t_lower = (topic or "").lower()
        norm_topic = "Python Core"
        if "data structure" in t_lower or "algorithm" in t_lower:
            norm_topic = "Data Structures"
        elif "system design" in t_lower or "architecture" in t_lower or "distributed" in t_lower:
            norm_topic = "System Design"
        elif "sql" in t_lower or "database" in t_lower or "postgres" in t_lower:
            norm_topic = "SQL"
        elif "cloud" in t_lower or "kubernetes" in t_lower or "aws" in t_lower or "docker" in t_lower or "devops" in t_lower:
            norm_topic = "Cloud"
        elif "java" in t_lower or "spring" in t_lower:
            norm_topic = "Java"
        elif "machine learning" in t_lower or " ai" in t_lower or "deep learning" in t_lower or "ml" in t_lower:
            norm_topic = "Machine Learning"
        elif "oop" in t_lower or "object-oriented" in t_lower:
            norm_topic = "OOP"
        elif "python" in t_lower:
            norm_topic = "Python Core"
        else:
            norm_topic = topic or "General Technical"

        questions_pool = {
            ("Python Core", "basic"): [
                ("Explain the difference between mutable and immutable types in Python, and how they behave when passed into functions.", "Mutability & Function Passing"),
                ("How does Python handle memory management and garbage collection with reference counting?", "Memory Management & Ref Counting"),
                ("What is the difference between a list and a tuple in Python, and when would you choose one over the other?", "Data Structures: List vs Tuple")
            ],
            ("Python Core", "intermediate"): [
                ("How do Python decorators work under the hood? Explain how `@functools.wraps` preserves metadata.", "Decorators & Closures"),
                ("Explain how Python generators and `yield` work with memory efficiency, and compare with list comprehensions.", "Generators & Iterators"),
                ("Explain the Global Interpreter Lock (GIL) in CPython and how it impacts multithreaded CPU-bound vs IO-bound programs.", "CPython GIL & Concurrency")
            ],
            ("Python Core", "advanced"): [
                ("How does Python's metaclass mechanism (`type` vs `class`) operate, and how would you implement an automated registry pattern using `__init_subclass__`?", "Metaprogramming & __init_subclass__"),
                ("Discuss asyncio's event loop architecture: how does it multiplex coroutines, tasks, and future callbacks without OS-level context switching overhead?", "Asyncio Architecture & Event Loops"),
                ("How does Python implement hash collision resolution in dictionaries (open addressing with perturbation)? Explain the impact of resizing and load factor.", "Dictionary Hash Collision & Internals")
            ],
            ("Data Structures", "basic"): [
                ("What is the average and worst-case time complexity of lookup in a Hash Table, and what causes the worst case?", "Hash Table Lookup Complexity"),
                ("Explain the difference between an Array and a Linked List in terms of memory layout and access time.", "Array vs Linked List Memory Layout"),
                ("Explain the concept of a Stack and a Queue, and describe how each handles element insertion and removal.", "Stacks & Queues")
            ],
            ("Data Structures", "intermediate"): [
                ("How does a Binary Search Tree maintain ordering, and what self-balancing strategies (like AVL or Red-Black trees) prevent O(N) degradation?", "Self-Balancing Binary Search Trees"),
                ("Explain how a LRU (Least Recently Used) cache is implemented with O(1) get and put operations using a Doubly Linked List and Hash Map.", "LRU Cache Data Structure Design"),
                ("Explain how a Min/Max Heap is structured in array representation and how heapify operations run in O(log N).", "Heap Architecture & Heapify")
            ],
            ("Data Structures", "advanced"): [
                ("How would you design a distributed rate limiter or consistent hashing ring that handles server node joins and leaves with minimal key relocation?", "Consistent Hashing & Distributed Ring"),
                ("Explain how B-Trees and LSM (Log-Structured Merge) Trees differ in write amplification, read latency, and suitability for SSD storage engines.", "B-Trees vs LSM Trees Storage Engines"),
                ("Explain how Trie structures enable prefix searching and autocomplete, and analyze memory optimization using Radix trees.", "Tries & Radix Trees")
            ],
            ("System Design", "basic"): [
                ("What is the role of a Load Balancer in client-server architecture, and how do Layer 4 vs Layer 7 load balancers differ?", "Load Balancing L4 vs L7"),
                ("Explain the concept of database indexing: why does adding an index accelerate read queries while impacting write throughput?", "Database Indexing Foundations")
            ],
            ("System Design", "intermediate"): [
                ("Explain how horizontal scaling differs from vertical scaling, and how database read replicas assist in handling read-heavy workloads.", "Horizontal Scaling & Read Replicas"),
                ("How would you design an idempotent payment processing API to prevent double-charging during network timeouts?", "API Idempotency & Payment Gateways"),
                ("Explain the differences between Cache-Aside, Write-Through, and Write-Behind caching strategies.", "Caching Strategies")
            ],
            ("System Design", "advanced"): [
                ("Design a distributed message broker ensuring at-least-once delivery with partition ordering and consumer group rebalancing under node failure.", "Distributed Message Broker Partitioning"),
                ("How would you design a geo-distributed caching tier maintaining eventual consistency with write-through or write-behind invalidation?", "Distributed Cache Invalidation & Consistency"),
                ("Explain how consensus algorithms (such as Raft or Paxos) elect leaders and maintain state machine replication under network partitions.", "Distributed Consensus & Raft")
            ],
            ("SQL", "basic"): [
                ("Explain the differences between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with practical query examples.", "SQL Joins"),
                ("What is the difference between WHERE and HAVING clauses in SQL aggregations?", "SQL Filtering & Grouping")
            ],
            ("SQL", "intermediate"): [
                ("Explain SQL transaction isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) and the concurrency anomalies they prevent.", "Transaction Isolation Levels"),
                ("How do database indexes (B-Tree vs Hash) work in SQL engines, and how do you interpret an EXPLAIN query execution plan?", "Query Optimization & EXPLAIN Plans")
            ],
            ("SQL", "advanced"): [
                ("Explain PostgreSQL Multi-Version Concurrency Control (MVCC) mechanics, dead tuple accumulation, and autovacuum tuning under heavy write loads.", "PostgreSQL MVCC & Autovacuum"),
                ("How would you design database sharding across multiple geographic nodes, handling cross-shard queries and two-phase commit overhead?", "Database Sharding & 2PC")
            ],
            ("Cloud", "basic"): [
                ("What is the core difference between monolithic and containerized microservice architectures?", "Containers & Microservices"),
                ("Explain the role of Docker containers and how they isolate processes compared to Virtual Machines.", "Docker Containerization")
            ],
            ("Cloud", "intermediate"): [
                ("How do Kubernetes Pods, Deployments, and Services interact to manage container lifecycle and traffic routing?", "Kubernetes Core Components"),
                ("Explain Infrastructure as Code (IaC) principles and how declarative state management in Terraform works.", "Infrastructure as Code & Terraform")
            ],
            ("Cloud", "advanced"): [
                ("How would you architect a multi-region active-active cloud deployment on Kubernetes with global traffic routing and cross-region database replication?", "Multi-Region Cloud Architecture"),
                ("Explain how Kubernetes Horizontal Pod Autoscaler (HPA) and cluster autoscaling handle sudden traffic spikes with custom Prometheus metrics.", "Kubernetes Autoscaling & Metrics")
            ],
            ("Java", "basic"): [
                ("Explain the difference between JDK, JRE, and JVM in the Java ecosystem.", "JVM Architecture"),
                ("What is the difference between `==` and `.equals()` in Java, especially when comparing String objects?", "Java Object Equality")
            ],
            ("Java", "intermediate"): [
                ("Explain Java's Garbage Collection mechanisms (e.g. G1GC, ZGC) and the roles of Young Generation vs Old Generation heap space.", "JVM Garbage Collection"),
                ("How does Java's `ConcurrentHashMap` achieve thread-safety without locking the entire table?", "Java Concurrent Collections")
            ],
            ("Java", "advanced"): [
                ("Discuss Java Virtual Threads (Project Loom) architecture and how lightweight user-mode threads differ from OS platform threads.", "Virtual Threads & Concurrency"),
                ("Explain Java memory model (JMM), happens-before relationship, and the operational semantics of `volatile` and `AtomicReference`.", "Java Memory Model & Volatile")
            ],
            ("Machine Learning", "basic"): [
                ("Explain the difference between supervised, unsupervised, and reinforcement learning.", "ML Paradigms"),
                ("What is the bias-variance tradeoff in machine learning, and how does it relate to overfitting and underfitting?", "Bias-Variance Tradeoff")
            ],
            ("Machine Learning", "intermediate"): [
                ("Explain how gradient descent and backpropagation optimize neural network weights during training.", "Backpropagation & Optimization"),
                ("How do precision, recall, F1-score, and ROC-AUC differ, and when would you prioritize recall over precision?", "ML Evaluation Metrics")
            ],
            ("Machine Learning", "advanced"): [
                ("Explain the self-attention mechanism in Transformer architectures and how multi-head attention computes context vectors.", "Transformer Self-Attention"),
                ("How would you design an end-to-end real-time ML feature store and model inference pipeline with low latency and drift detection?", "MLOps & Feature Stores")
            ],
            ("OOP", "basic"): [
                ("Explain the four fundamental principles of Object-Oriented Programming: Encapsulation, Abstraction, Inheritance, and Polymorphism.", "OOP Core Principles"),
                ("What is the difference between an abstract class and an interface?", "Abstract Classes vs Interfaces")
            ],
            ("OOP", "intermediate"): [
                ("Explain the SOLID design principles with concrete architectural examples.", "SOLID Principles"),
                ("How does the Factory pattern differ from the Dependency Injection pattern in modern software architecture?", "Design Patterns: Factory & DI")
            ],
            ("OOP", "advanced"): [
                ("How do you design a flexible event-driven architecture utilizing the Observer pattern and Domain-Driven Design (DDD) aggregate roots?", "DDD & Event-Driven Patterns"),
                ("Discuss the tradeoffs between deep class inheritance hierarchies vs object composition (Composition over Inheritance).", "Composition vs Inheritance")
            ]
        }

        # Select matching question from pool
        key = (norm_topic, target_diff)
        candidates = questions_pool.get(key)
        if not candidates:
            # Fallback by normalized topic
            candidates = [q for k, q in questions_pool.items() if k[0] == norm_topic]
            if candidates:
                candidates = candidates[0]
        if not candidates:
            # Fallback to general topic
            clean_concept = target_concept if (target_concept and target_concept != "None") else f"core principles of {topic}"
            candidates = [
                (f"Could you explain your approach to handling {clean_concept} in {topic} for a {experience_level} {job_role}?", clean_concept),
                (f"In {topic}, what are the primary architectural tradeoffs when implementing {clean_concept}?", clean_concept)
            ]

        # Filter out questions already asked
        unused = [q for q in candidates if q[0] not in previous_questions]
        selected = unused[0] if unused else candidates[0]

        # If adaptive action is diagnostic or probe missing, format specifically
        q_text, concept = selected
        concept_label = target_concept if (target_concept and target_concept != "None") else concept
        if adaptive_action == "DIAGNOSTIC":
            q_text = f"To explore the underlying mechanism: {q_text}"
        elif adaptive_action == "PROBE_MISSING":
            q_text = f"Specifically focusing on {concept_label}: {q_text}"

        return {
            "question_text": q_text,
            "topic": topic,
            "difficulty": target_diff,
            "target_concept": concept_label,
            "rationale": adaptive_reason or f"Fulfilling adaptive action {adaptive_action} on {topic}."
        }

    @staticmethod
    def generate_report(
        candidate_name: str,
        job_role: str,
        experience_level: str,
        overall_score: float,
        weighted_score: float,
        diff_data: Dict[str, Any],
        topic_data: Dict[str, Any],
        demonstrated_concepts: List[str],
        missing_concepts: List[str]
    ) -> Dict[str, Any]:
        """
        Generates simulated executive hiring evaluation report.
        """
        if weighted_score >= 8.0:
            rec = "Strong Hire"
            reasoning = f"{candidate_name} showed consistent depth across intermediate and advanced scenarios, demonstrating robust problem-solving and clean conceptual reasoning."
        elif weighted_score >= 6.5:
            rec = "Hire"
            reasoning = f"Demonstrated solid competence across core topics with good foundational mastery and ability to reason through intermediate problems."
        elif weighted_score >= 4.5:
            rec = "Lean Hire"
            reasoning = "Strong on fundamentals but exhibited knowledge gaps when probed on advanced internals and edge case handling."
        else:
            rec = "No Hire"
            reasoning = "Struggled with foundational concepts and was unable to resolve diagnostic probes across key subject areas."

        return {
            "overall_summary": f"Technical evaluation for {candidate_name} interviewing for {job_role} ({experience_level}). The candidate demonstrated a weighted score of {weighted_score}/10. They exhibited strong foundational knowledge in key areas while highlighting specific development opportunities in advanced internals.",
            "strengths": demonstrated_concepts[:4] if demonstrated_concepts else [
                "Clear verbal articulation of concepts",
                "Solid foundational understanding",
                "Structured reasoning approach"
            ],
            "areas_for_improvement": missing_concepts[:3] if missing_concepts else [
                "Deep dive into runtime internal mechanics",
                "High-scale concurrency and edge case optimizations"
            ],
            "depth_analysis": f"Candidate achieved {diff_data.get('basic', {}).get('avg', 0)}/10 in basic questions, {diff_data.get('intermediate', {}).get('avg', 0)}/10 in intermediate questions, and {diff_data.get('advanced', {}).get('avg', 0)}/10 in advanced challenges. In accordance with depth-weighted scoring, high marks on foundational questions are balanced against performance on complex edge cases.",
            "hiring_recommendation": rec,
            "recommendation_reasoning": reasoning
        }


class AIService:
    """
    Main GenAI service dispatcher.
    """

    def __init__(self):
        self.provider = AI_PROVIDER
        self.gemini_key = GEMINI_API_KEY
        self.openai_key = OPENAI_API_KEY
        self.mock = MockAIService()

        # Check if provider should fall back to mock
        if self.provider == "gemini" and not self.gemini_key:
            logger.info("GEMINI_API_KEY not set. Falling back to Mock AI Service.")
            self.provider = "mock"
        elif self.provider == "openai" and not self.openai_key:
            logger.info("OPENAI_API_KEY not set. Falling back to Mock AI Service.")
            self.provider = "mock"

    async def evaluate_answer(
        self,
        job_role: str,
        experience_level: str,
        topic: str,
        difficulty: str,
        target_concept: str,
        question_text: str,
        candidate_answer: str
    ) -> Dict[str, Any]:
        """
        Submits candidate answer for multi-dimensional evaluation.
        """
        # If mock mode, return mock evaluation
        if self.provider == "mock":
            return self.mock.evaluate_answer(
                question_text, candidate_answer, topic, difficulty, target_concept
            )

        # Build prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "evaluation_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        prompt = template.format(
            job_role=job_role,
            experience_level=experience_level,
            topic=topic,
            difficulty=difficulty,
            target_concept=target_concept or topic,
            question_text=question_text,
            candidate_answer=candidate_answer
        )

        try:
            if self.provider == "gemini":
                raw_response = await self._call_gemini(prompt)
            elif self.provider == "openai":
                raw_response = await self._call_openai(prompt)
            else:
                raw_response = ""

            parsed = extract_json_from_text(raw_response)
            if parsed and "score" in parsed and "understanding_level" in parsed:
                return parsed
        except Exception as e:
            logger.error("Error in AI evaluation call: %s", str(e))

        # Safe fallback
        return self.mock.evaluate_answer(question_text, candidate_answer, topic, difficulty, target_concept)

    async def generate_next_question(
        self,
        job_role: str,
        experience_level: str,
        topic: str,
        target_difficulty: str,
        adaptive_action: str,
        target_concept: str,
        adaptive_reason: str,
        previous_questions: List[str],
        candidate_profile_summary: str = ""
    ) -> Dict[str, Any]:
        """
        Generates the next question strictly conforming to adaptive requirements.
        """
        if self.provider == "mock":
            return self.mock.generate_question(
                job_role, experience_level, topic, target_difficulty,
                adaptive_action, target_concept, adaptive_reason, previous_questions
            )

        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "question_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        prev_q_str = "\n".join(f"- {q}" for q in previous_questions) if previous_questions else "None yet."
        prompt = template.format(
            job_role=job_role,
            experience_level=experience_level,
            topic=topic,
            target_difficulty=target_difficulty,
            adaptive_action=adaptive_action,
            target_concept=target_concept,
            adaptive_reason=adaptive_reason,
            candidate_profile_summary=candidate_profile_summary or "Candidate session underway.",
            previous_questions=prev_q_str
        )

        try:
            if self.provider == "gemini":
                raw_response = await self._call_gemini(prompt)
            elif self.provider == "openai":
                raw_response = await self._call_openai(prompt)
            else:
                raw_response = ""

            parsed = extract_json_from_text(raw_response)
            if parsed and "question_text" in parsed:
                return parsed
        except Exception as e:
            logger.error("Error generating question: %s", str(e))

        return self.mock.generate_question(
            job_role, experience_level, topic, target_difficulty,
            adaptive_action, target_concept, adaptive_reason, previous_questions
        )

    async def generate_final_report(
        self,
        candidate_name: str,
        job_role: str,
        experience_level: str,
        topics: List[str],
        total_questions: int,
        raw_score: float,
        weighted_score: float,
        diff_data: Dict[str, Any],
        topic_data: Dict[str, Any],
        demonstrated_concepts: List[str],
        missing_concepts: List[str],
        transcript_str: str
    ) -> Dict[str, Any]:
        """
        Generates final AI hiring report.
        """
        if self.provider == "mock":
            return self.mock.generate_report(
                candidate_name, job_role, experience_level, raw_score, weighted_score,
                diff_data, topic_data, demonstrated_concepts, missing_concepts
            )

        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "report_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        prompt = template.format(
            candidate_name=candidate_name,
            job_role=job_role,
            experience_level=experience_level,
            topics=", ".join(topics),
            total_questions=total_questions,
            raw_score=raw_score,
            weighted_score=weighted_score,
            basic_score=diff_data.get("basic", {}).get("avg", 0),
            intermediate_score=diff_data.get("intermediate", {}).get("avg", 0),
            advanced_score=diff_data.get("advanced", {}).get("avg", 0),
            demonstrated_concepts=", ".join(demonstrated_concepts) if demonstrated_concepts else "None recorded",
            missing_concepts=", ".join(missing_concepts) if missing_concepts else "None recorded",
            transcript=transcript_str
        )

        try:
            if self.provider == "gemini":
                raw_response = await self._call_gemini(prompt)
            elif self.provider == "openai":
                raw_response = await self._call_openai(prompt)
            else:
                raw_response = ""

            parsed = extract_json_from_text(raw_response)
            if parsed and "overall_summary" in parsed:
                return parsed
        except Exception as e:
            logger.error("Error generating final report: %s", str(e))

        return self.mock.generate_report(
            candidate_name, job_role, experience_level, raw_score, weighted_score,
            diff_data, topic_data, demonstrated_concepts, missing_concepts
        )

    async def _call_gemini(self, prompt: str) -> str:
        """Calls Google Gemini API using google-genai."""
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_key)
            model_name = AI_MODEL if AI_MODEL else "gemini-1.5-flash"
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text or ""
        except ImportError:
            # Try alternate import
            import google.generativeai as gai
            gai.configure(api_key=self.gemini_key)
            model = gai.GenerativeModel(AI_MODEL or "gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text or ""

    async def _call_openai(self, prompt: str) -> str:
        """Calls OpenAI API using openai client."""
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_key)
        model_name = AI_MODEL if AI_MODEL else "gpt-4o-mini"
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content or ""


# Global singleton instance
ai_service = AIService()
