"""Database initialization and comprehensive sample seeding script for PlacementPilot."""

import json
import logging
from pathlib import Path
from typing import Optional

from config.settings import settings
from src.db.connection import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def migrate_database(conn) -> None:
    """Safely apply schema migrations to preserve existing database records."""
    cursor = conn.cursor()

    # 1. Ensure departments table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT UNIQUE NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Check and add columns to students table if not existing
    cursor.execute("PRAGMA table_info(students);")
    columns = [col[1] for col in cursor.fetchall()]
    if "phone" not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN phone TEXT;")
    if "department" not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN department TEXT;")
    if "year_of_study" not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN year_of_study TEXT;")

    # 3. Backfill department from branch if empty
    cursor.execute("UPDATE students SET department = branch WHERE department IS NULL OR department = '';")

    # 4. Seed default academic departments if empty
    cursor.execute("SELECT COUNT(*) FROM departments;")
    if cursor.fetchone()[0] == 0:
        default_depts = [
            ("CSE", "Computer Science"),
            ("IT", "Information Technology"),
            ("MCA", "Computer Applications"),
            ("COMMERCE", "Commerce"),
            ("BBA", "Business Administration"),
            ("MATH", "Mathematics"),
            ("PHYSICS", "Physics"),
            ("CHEMISTRY", "Chemistry"),
            ("OTHER", "Other"),
        ]
        cursor.executemany("INSERT OR IGNORE INTO departments (code, name) VALUES (?, ?);", default_depts)

    conn.commit()


def initialize_database(db_path: Optional[Path] = None) -> None:
    """Execute DDL statements from schema.sql to create all required tables and indexes."""
    target_path = db_path or settings.DATABASE_PATH
    logger.info("Initializing SQLite database at: %s", target_path)

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db_connection(target_path) as conn:
        conn.executescript(schema_sql)
        migrate_database(conn)

    logger.info("Database schema initialized and verified successfully.")


def seed_sample_data(db_path: Optional[Path] = None, clear_existing: bool = False) -> None:
    """Seed comprehensive sample data for students, companies, job drives, and interview prep."""
    target_path = db_path or settings.DATABASE_PATH
    logger.info("Seeding comprehensive sample data into: %s", target_path)

    with get_db_connection(target_path) as conn:
        cursor = conn.cursor()

        if clear_existing:
            cursor.execute("DELETE FROM mock_interviews;")
            cursor.execute("DELETE FROM interview_rounds;")
            cursor.execute("DELETE FROM applications;")
            cursor.execute("DELETE FROM question_bank;")
            cursor.execute("DELETE FROM jobs;")
            cursor.execute("DELETE FROM companies;")
            cursor.execute("DELETE FROM students;")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('students', 'companies', 'jobs', 'applications', 'interview_rounds', 'question_bank', 'mock_interviews');")

        # 1. Seed Students
        cursor.execute("SELECT COUNT(*) FROM students;")
        if cursor.fetchone()[0] == 0:
            sample_students = [
                (
                    "1PI21CS001",
                    "Aarav Sharma",
                    "aarav.sharma@example.edu",
                    "+91 98765 00001",
                    "CSE",
                    "Computer Science",
                    "4th Year",
                    8.90,
                    2025,
                    json.dumps(["Python", "C++", "Data Structures", "SQL", "Docker", "Algorithms"]),
                    "/resumes/1PI21CS001_Aarav.pdf",
                ),
                (
                    "1PI21EC045",
                    "Priya Patel",
                    "priya.patel@example.edu",
                    "+91 98765 00002",
                    "ECE",
                    "Electronics & Communication",
                    "4th Year",
                    7.80,
                    2025,
                    json.dumps(["C++", "Embedded Systems", "Verilog", "Python", "Microcontrollers"]),
                    "/resumes/1PI21EC045_Priya.pdf",
                ),
                (
                    "1PI21IS088",
                    "Rohan Verma",
                    "rohan.verma@example.edu",
                    "+91 98765 00003",
                    "ISE",
                    "Information Technology",
                    "4th Year",
                    8.20,
                    2025,
                    json.dumps(["Java", "Spring Boot", "React", "PostgreSQL", "Docker"]),
                    "/resumes/1PI21IS088_Rohan.pdf",
                ),
                (
                    "1PI21CS042",
                    "Ananya Gupta",
                    "ananya.gupta@example.edu",
                    "+91 98765 00004",
                    "CSE",
                    "Computer Science",
                    "4th Year",
                    9.45,
                    2025,
                    json.dumps(["Python", "Go", "Distributed Systems", "Kubernetes", "SQL", "Algorithms"]),
                    "/resumes/1PI21CS042_Ananya.pdf",
                ),
                (
                    "1PI21ME033",
                    "Vikram Singh",
                    "vikram.singh@example.edu",
                    "+91 98765 00005",
                    "MECH",
                    "Mechanical Engineering",
                    "4th Year",
                    7.20,
                    2025,
                    json.dumps(["CAD", "SolidWorks", "Python", "MATLAB"]),
                    "/resumes/1PI21ME033_Vikram.pdf",
                ),
                (
                    "1PI21IS019",
                    "Sneha Kulkarni",
                    "sneha.kulkarni@example.edu",
                    "+91 98765 00006",
                    "ISE",
                    "Information Technology",
                    "4th Year",
                    8.65,
                    2025,
                    json.dumps(["Python", "Machine Learning", "FastAPI", "SQL", "Pandas"]),
                    "/resumes/1PI21IS019_Sneha.pdf",
                ),
                (
                    "1PI21CM012",
                    "Rahul Nair",
                    "rahul.nair@example.edu",
                    "+91 98765 00007",
                    "COMMERCE",
                    "Commerce",
                    "3rd Year",
                    8.40,
                    2025,
                    json.dumps(["Financial Modeling", "Accounting", "Excel", "Auditing", "Taxation", "PowerBI"]),
                    "/resumes/1PI21CM012_Rahul.pdf",
                ),
                (
                    "1PI21BA024",
                    "Divya Krishnan",
                    "divya.krishnan@example.edu",
                    "+91 98765 00008",
                    "BBA",
                    "Business Administration",
                    "3rd Year",
                    8.15,
                    2025,
                    json.dumps(["Business Strategy", "Marketing", "Operations", "Market Research", "Negotiation"]),
                    "/resumes/1PI21BA024_Divya.pdf",
                ),
                (
                    "1PI21MA009",
                    "Siddharth Roy",
                    "siddharth.roy@example.edu",
                    "+91 98765 00009",
                    "MATH",
                    "Mathematics",
                    "4th Year",
                    9.10,
                    2025,
                    json.dumps(["Probability", "Statistics", "Linear Algebra", "Python", "Data Analysis", "Calculus"]),
                    "/resumes/1PI21MA009_Siddharth.pdf",
                ),
                (
                    "1PI21PH015",
                    "Anjali Verma",
                    "anjali.verma@example.edu",
                    "+91 98765 00010",
                    "PHYSICS",
                    "Physics",
                    "4th Year",
                    8.50,
                    2025,
                    json.dumps(["Computational Physics", "Data Analysis", "Python", "MATLAB", "Research"]),
                    "/resumes/1PI21PH015_Anjali.pdf",
                ),
            ]
            cursor.executemany(
                """
                INSERT INTO students (
                    usn, name, email, phone, branch, department, year_of_study,
                    cgpa, graduation_year, skills, resume_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                sample_students,
            )
            logger.info("Inserted %d sample students.", len(sample_students))

        # 2. Seed Companies
        cursor.execute("SELECT COUNT(*) FROM companies;")
        if cursor.fetchone()[0] == 0:
            sample_companies = [
                ("Google", "https://careers.google.com", "Technology", "Global tech leader in search, cloud platforms, and generative AI."),
                ("Microsoft", "https://careers.microsoft.com", "Technology", "Empowering individuals and organizations globally through intelligent cloud."),
                ("Amazon", "https://amazon.jobs", "E-commerce & Cloud", "Pioneering e-commerce, cloud infrastructure with AWS, and logistics."),
                ("Stripe", "https://stripe.com/jobs", "Fintech & Payments", "Financial infrastructure for the internet, powering millions of businesses."),
                ("Databricks", "https://databricks.com/company/careers", "Data & AI", "The data and AI company, pioneering the lakehouse architecture."),
                ("Oracle", "https://www.oracle.com/careers", "Enterprise Software", "Cloud applications and database platform services."),
                ("Deloitte Consulting", "https://www2.deloitte.com/careers", "Management Consulting", "Global leader in professional consulting, strategy, and business operations."),
                ("KPMG Advisory", "https://kpmg.com/careers", "Financial & Advisory", "Audit, tax, and risk advisory services across global corporate sectors."),
            ]
            cursor.executemany(
                """
                INSERT INTO companies (name, website, industry, description)
                VALUES (?, ?, ?, ?);
                """,
                sample_companies,
            )
            logger.info("Inserted %d sample companies.", len(sample_companies))

        # 3. Seed Jobs
        cursor.execute("SELECT COUNT(*) FROM jobs;")
        if cursor.fetchone()[0] == 0:
            sample_jobs = [
                (
                    1, # Google
                    "Associate Software Engineer",
                    "Build distributed backend services, high-throughput pipelines, and scalable APIs.",
                    28.5,
                    "Bangalore / Hyderabad",
                    8.0,
                    json.dumps(["CSE", "ISE"]),
                    json.dumps(["Data Structures", "Algorithms", "System Design", "Python", "C++"]),
                    "2026-12-15",
                    "open",
                ),
                (
                    2, # Microsoft
                    "Software Engineer - Cloud & AI",
                    "Develop intelligent Azure infrastructure and enterprise developer tools.",
                    24.0,
                    "Bangalore",
                    7.5,
                    json.dumps(["CSE", "ISE", "ECE"]),
                    json.dumps(["C++", "Java", "Python", "SQL", "Cloud Concepts"]),
                    "2026-11-30",
                    "open",
                ),
                (
                    3, # Amazon
                    "SDE-1",
                    "Design and implement high-availability e-commerce and logistics services.",
                    22.0,
                    "Hyderabad",
                    7.0,
                    json.dumps(["CSE", "ISE", "ECE"]),
                    json.dumps(["Java", "OOP", "Data Structures", "SQL"]),
                    "2026-12-01",
                    "open",
                ),
                (
                    4, # Stripe
                    "Software Engineer - Payments Core",
                    "Design fault-tolerant payment ledgers, dispute routing, and international banking APIs.",
                    32.0,
                    "Bangalore",
                    8.5,
                    json.dumps(["CSE", "ISE"]),
                    json.dumps(["Python", "Go", "Distributed Systems", "SQL", "APIs"]),
                    "2026-12-20",
                    "open",
                ),
                (
                    5, # Databricks
                    "Lakehouse Platform Engineer",
                    "Scale unified data processing engines and serverless Spark runtime components.",
                    38.0,
                    "Bangalore",
                    8.5,
                    json.dumps(["CSE", "ISE"]),
                    json.dumps(["Distributed Systems", "C++", "Python", "Algorithms", "SQL"]),
                    "2026-12-31",
                    "open",
                ),
                (
                    6, # Oracle
                    "Cloud Infrastructure Associate",
                    "Build autonomous database infrastructure and enterprise networking services.",
                    18.0,
                    "Bangalore",
                    7.0,
                    json.dumps(["CSE", "ISE", "ECE", "EEE"]),
                    json.dumps(["Java", "Linux", "Networking", "SQL"]),
                    "2026-11-25",
                    "open",
                ),
                (
                    7, # Deloitte Consulting (Open to ALL Departments)
                    "Associate Business & Technology Analyst",
                    "Drive cross-functional client operations, market analysis, process automation, and business intelligence.",
                    14.5,
                    "Bangalore / Mumbai / Gurgaon",
                    6.5,
                    json.dumps(["ALL"]), # All Departments Allowed!
                    json.dumps(["Communication", "Problem Solving", "Excel", "Data Analysis", "SQL"]),
                    "2026-12-28",
                    "open",
                ),
                (
                    8, # KPMG Advisory (Commerce, BBA, Math)
                    "Financial & Risk Advisory Analyst",
                    "Perform statutory risk assessment, financial data audit, regulatory reporting, and portfolio diagnostics.",
                    11.0,
                    "Mumbai / Bangalore",
                    7.0,
                    json.dumps(["Commerce", "Business Administration", "Mathematics"]),
                    json.dumps(["Financial Analysis", "Accounting", "Excel", "Auditing", "Reporting"]),
                    "2026-12-18",
                    "open",
                ),
            ]
            cursor.executemany(
                """
                INSERT INTO jobs (company_id, role_title, job_description, ctc_lpa, location, min_cgpa, allowed_branches, required_skills, application_deadline, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                sample_jobs,
            )
            logger.info("Inserted %d sample job postings.", len(sample_jobs))

        # 4. Seed Applications & Rounds
        cursor.execute("SELECT COUNT(*) FROM applications;")
        if cursor.fetchone()[0] == 0:
            sample_applications = [
                # Aarav (id 1)
                (1, 1, "interview_scheduled", "Technical Round 2: System Architecture", "Top score in online coding assessment."),
                (1, 2, "oa_cleared", "Awaiting Technical Round 1 Schedule", "100% test cases cleared in HackerRank test."),
                # Priya (id 2)
                (2, 3, "applied", "Application Submitted", "Eligible candidate based on CGPA and branch."),
                # Rohan (id 3)
                (3, 3, "interview_scheduled", "Managerial & Fitment Round", "Cleared OA and technical round."),
                (3, 5, "rejected", "Rejected in Round 1", "Did not meet distributed systems concurrency criteria."),
                # Ananya (id 4)
                (4, 4, "offered", "Offer Accepted (₹32.0 LPA)", "Outstanding performance in all 4 interview rounds."),
                (4, 1, "offered", "Offer Received (₹28.5 LPA)", "Extended job offer after executive review."),
                # Vikram (id 5)
                (5, 6, "applied", "Application Submitted", "Eligible candidate under Oracle campus drive."),
            ]
            cursor.executemany(
                """
                INSERT INTO applications (student_id, job_id, status, current_stage, notes)
                VALUES (?, ?, ?, ?, ?);
                """,
                sample_applications,
            )
            logger.info("Inserted %d sample applications.", len(sample_applications))

            # Sample interview rounds
            sample_rounds = [
                # App 1 (Aarav to Google)
                (1, 1, "Online Assessment", "2026-10-15 10:00", "cleared", "Solved both DP and Graph problems cleanly.", "Fast execution."),
                (1, 2, "Technical Round 1", "2026-10-25 14:00", "cleared", "Strong DSA fundamentals, lucid complexity analysis.", "Good communication."),
                (1, 3, "Technical Round 2", "2026-11-20 11:00", "pending", None, "Focus on distributed caching and concurrency."),
                # App 4 (Rohan to Amazon)
                (4, 1, "Online Assessment", "2026-10-18 11:00", "cleared", "Score: 95/100 on coding test.", "Good code modularity."),
                (4, 2, "Technical Round 1", "2026-10-30 15:00", "cleared", "Solid OOP design and database modeling.", "Cleared with high rating."),
                (4, 3, "Managerial & Fitment Round", "2026-11-22 16:00", "pending", None, "Amazon Leadership Principles evaluation."),
                # App 5 (Rohan to Databricks)
                (5, 1, "Technical Round 1", "2026-10-10 10:00", "failed", "Struggled with consensus protocols and Raft.", "Encouraged to reapply."),
                # App 6 (Ananya to Stripe)
                (6, 1, "Online Assessment", "2026-09-15 10:00", "cleared", "Perfect score in under 25 minutes.", "Senior engineer review recommended."),
                (6, 2, "Technical Round 1", "2026-09-22 14:00", "cleared", "Exceptional systems design knowledge.", "Clear explanations."),
                (6, 3, "Technical Round 2", "2026-10-01 11:00", "cleared", "Flawless API idempotency design.", "Ready for hire."),
                (6, 4, "Executive Bar Raiser", "2026-10-12 16:00", "cleared", "High cultural fit and leadership maturity.", "Offer approved."),
            ]
            cursor.executemany(
                """
                INSERT INTO interview_rounds (application_id, round_number, round_type, scheduled_at, status, feedback, interviewer_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                sample_rounds,
            )
            logger.info("Inserted %d sample interview rounds.", len(sample_rounds))

        # 5. Seed Question Bank
        cursor.execute("SELECT COUNT(*) FROM question_bank;")
        if cursor.fetchone()[0] == 0:
            sample_questions = [
                (
                    "DSA",
                    "Binary Search & Two Pointers",
                    "Search in Rotated Sorted Array: Given array nums sorted in ascending order (with distinct values) and rotated at an unknown pivot index, find the target value index in O(log n) time.",
                    "Medium",
                    "Identify which half is strictly sorted by comparing nums[mid] with nums[low]. Then decide whether target lies in the sorted half or the other half.",
                    json.dumps(["Google", "Amazon", "Microsoft", "Stripe"]),
                ),
                (
                    "DSA",
                    "Dynamic Programming",
                    "Longest Increasing Subsequence: Given an integer array nums, return the length of the longest strictly increasing subsequence.",
                    "Medium",
                    "Can be solved in O(N^2) using 1D DP array, or optimized to O(N log N) using binary search with patience sorting.",
                    json.dumps(["Google", "Microsoft", "Databricks"]),
                ),
                (
                    "DSA",
                    "Graph Algorithms",
                    "Course Schedule II: Find a valid topological ordering of courses given prerequisite dependencies, or detect a cycle.",
                    "Medium",
                    "Use Kahn's algorithm (indegree tracking with BFS) or DFS cycle detection with visited states (0=unvisited, 1=visiting, 2=visited).",
                    json.dumps(["Google", "Amazon", "Databricks"]),
                ),
                (
                    "Core_CS",
                    "Operating Systems",
                    "Explain the difference between a Process and a Thread. How does the OS handle context switching between them?",
                    "Medium",
                    "A process has its own address space, memory, and resources. Threads share memory within the same process. Context switching threads is faster due to shared virtual memory.",
                    json.dumps(["Amazon", "Microsoft", "Oracle"]),
                ),
                (
                    "Core_CS",
                    "Computer Networks",
                    "Explain the TCP 3-Way Handshake and 4-Way Termination. Why does TIME_WAIT state exist?",
                    "Medium",
                    "SYN -> SYN-ACK -> ACK. TIME_WAIT ensures remote host received the final ACK and prevents old packets from being confused with new connection incarnations.",
                    json.dumps(["Stripe", "Google", "Oracle"]),
                ),
                (
                    "System_Design",
                    "Distributed Caching",
                    "Design a Distributed Cache like Redis or Memcached with cache eviction policies (LRU/LFU) and consistent hashing.",
                    "Hard",
                    "Use consistent hashing with virtual nodes for partitioning. Combine a doubly linked list with a hash map for O(1) LRU eviction. Implement write-through or write-back strategies.",
                    json.dumps(["Google", "Amazon", "Stripe", "Databricks"]),
                ),
                (
                    "Database",
                    "Indexing & Query Optimization",
                    "What is the difference between a Clustered Index and a Non-Clustered Index in relational databases?",
                    "Medium",
                    "A clustered index defines physical order of data in the table (only 1 per table). A non-clustered index creates a separate pointer structure to row locations.",
                    json.dumps(["Amazon", "Oracle", "Microsoft"]),
                ),
                (
                    "Database",
                    "Transactions & Isolation Levels",
                    "Compare ACID isolation levels: Read Uncommitted, Read Committed, Repeatable Read, and Serializable. What anomalies do they prevent?",
                    "Medium",
                    "Dirty Read, Non-repeatable Read, Phantom Read. Serializable prevents all anomalies via 2PL or SSI (Serializable Snapshot Isolation).",
                    json.dumps(["Stripe", "Oracle", "Databricks"]),
                ),
                (
                    "Behavioral_HR",
                    "Conflict Resolution",
                    "Describe a situation where you had a disagreement with a team member on a technical decision. How did you resolve it?",
                    "Medium",
                    "Use the STAR method (Situation, Task, Action, Result). Highlight listening, data-driven trade-off analysis, empathy, and collective team goals.",
                    json.dumps(["Amazon", "Google", "Microsoft"]),
                ),
                (
                    "Aptitude",
                    "Probability & Combinatorics",
                    "Two fair 6-sided dice are rolled. What is the probability that the sum of the dice is at least 9 given that at least one die shows a 5?",
                    "Easy",
                    "Pairs with at least one 5: 11 outcomes. Favorable outcomes (sum >= 9): (5,4), (5,5), (5,6), (4,5), (6,5). Total favorable = 5. Probability = 5/11.",
                    json.dumps(["Amazon", "Oracle", "Infosys"]),
                ),
            ]
            cursor.executemany(
                """
                INSERT INTO question_bank (category, topic, question_text, difficulty, solution_guide, company_tags)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                sample_questions,
            )
            logger.info("Inserted %d sample prep questions.", len(sample_questions))

        # 6. Seed Mock Interviews
        cursor.execute("SELECT COUNT(*) FROM mock_interviews;")
        if cursor.fetchone()[0] == 0:
            sample_mocks = [
                (1, "Dynamic Programming & Trees", 92.0, "Great algorithmic clarity and edge-case handling.", "Interviewer: Find the maximum path sum in a binary tree..."),
                (1, "System Design Basics", 85.0, "Good grasp of horizontal scaling and load balancers.", "Interviewer: Design a URL shortening service..."),
                (3, "OOP & Java Design Patterns", 78.0, "Solid on inheritance; brush up on Factory and Strategy patterns.", "Interviewer: Explain dependency injection..."),
                (4, "Distributed Systems & Concurrency", 96.0, "Phenomenal explanation of Raft and two-phase commit.", "Interviewer: How does distributed locking work in Redis?"),
            ]
            cursor.executemany(
                """
                INSERT INTO mock_interviews (student_id, topic, score, feedback, transcript)
                VALUES (?, ?, ?, ?, ?);
                """,
                sample_mocks,
            )
            logger.info("Inserted %d sample mock interview logs.", len(sample_mocks))

    logger.info("Sample seeding completed successfully.")


if __name__ == "__main__":
    initialize_database()
    seed_sample_data(clear_existing=True)
