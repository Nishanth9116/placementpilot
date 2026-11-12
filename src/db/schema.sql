-- PlacementPilot SQLite Database Schema
-- Local-first relational storage with foreign key constraints enabled

PRAGMA foreign_keys = ON;

-- 0. College Academic Departments Table
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1. Students / Candidates Table
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usn TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    branch TEXT NOT NULL,
    department TEXT,
    year_of_study TEXT,
    cgpa REAL NOT NULL CHECK (cgpa >= 0.0 AND cgpa <= 10.0),
    graduation_year INTEGER NOT NULL,
    skills TEXT NOT NULL DEFAULT '[]', -- JSON string array of skills
    resume_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Companies Table
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    website TEXT,
    industry TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Job Drives / Openings Table
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    role_title TEXT NOT NULL,
    job_description TEXT,
    ctc_lpa REAL NOT NULL CHECK (ctc_lpa >= 0.0),
    location TEXT DEFAULT 'On-site',
    min_cgpa REAL DEFAULT 0.0 CHECK (min_cgpa >= 0.0 AND min_cgpa <= 10.0),
    allowed_branches TEXT NOT NULL DEFAULT '[]', -- JSON string array of branches (e.g. ["CSE", "ECE"])
    required_skills TEXT DEFAULT '[]', -- JSON string array of skills
    application_deadline TEXT,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed', 'in_progress')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Placement Applications Table
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'applied' CHECK (status IN ('applied', 'shortlisted', 'oa_cleared', 'interview_scheduled', 'offered', 'rejected', 'withdrawn')),
    current_stage TEXT DEFAULT 'Application Submitted',
    notes TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, job_id)
);

-- 5. Interview Rounds Table
CREATE TABLE IF NOT EXISTS interview_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    round_type TEXT NOT NULL, -- e.g. "Online Assessment", "Technical 1", "Technical 2", "HR"
    scheduled_at TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'cleared', 'failed', 'cancelled')),
    feedback TEXT,
    interviewer_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Question Bank for Placement Prep
CREATE TABLE IF NOT EXISTS question_bank (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL CHECK (category IN ('DSA', 'Core_CS', 'System_Design', 'Database', 'Behavioral_HR', 'Aptitude')),
    topic TEXT NOT NULL,
    question_text TEXT NOT NULL,
    difficulty TEXT DEFAULT 'Medium' CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    solution_guide TEXT,
    company_tags TEXT DEFAULT '[]', -- JSON string array e.g. ["Amazon", "Google"]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Mock Interview Sessions & Logs
CREATE TABLE IF NOT EXISTS mock_interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    score REAL CHECK (score >= 0.0 AND score <= 100.0),
    feedback TEXT,
    transcript TEXT,
    conducted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_students_cgpa ON students(cgpa);
CREATE INDEX IF NOT EXISTS idx_students_branch ON students(branch);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_applications_student ON applications(student_id);
CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_rounds_application ON interview_rounds(application_id);
CREATE INDEX IF NOT EXISTS idx_questions_category ON question_bank(category, difficulty);

