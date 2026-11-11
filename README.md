# PlacementPilot 🎓✈️

**PlacementPilot** is a production-grade, local-first AI placement preparation and campus recruitment platform. It integrates a local **SQLite** relational database, the official **Model Context Protocol (MCP) Python SDK (`mcp==2.3.0`)**, and a **Modern Dark Navy & Blue SaaS Web Dashboard**.

All candidate profiles, academic records, campus recruitment drives, interview stages, and preparation question banks remain securely on your local system — **zero Google Cloud or remote cloud databases**.

---

## 🌟 Key Capabilities & Features

### 1. Modern Professional SaaS Web Dashboard
- **Dark Navy & Blue Design System:** Built with deep space tones (`#060913`, `#0c1322`), electric blue accents (`#3b82f6`), glassmorphic panels, and accessible typography.
- **Responsive Layout:** Collapsible sidebar navigation, live student profile selector in the top bar, real-time metrics, and native `<dialog>` modals with background blur.

### 2. Candidate Dashboard & Analytics
- Live KPI cards tracking **Total Applications**, **Interviews Scheduled**, **Job Offers Secured**, and **Active Campus Drives**.
- Active student profile card with branch, GPA, declared skill tags, and placement conversion stats.
- Featured recruitment drives table with 1-click application submission.

### 3. Application Pipeline Workflow
- Structured state machine managing candidate progress across:
  `applied` ➔ `shortlisted` ➔ `oa_cleared` ➔ `interview_scheduled` ➔ `offered` / `rejected` / `withdrawn`.
- Enforces strict transition rules (e.g., failed interviews automatically move applications to `rejected`).
- Visual history modal showing round-by-round chronological evaluation notes.

### 4. Company & Campus Drive Management
- Full CRUD operations for hiring organizations and job postings.
- Declarative cutoffs for minimum CGPA, eligible degree branches (e.g. `CSE`, `ISE`, `ECE`), and compensation packages (CTC in LPA).
- Instant AI Job Analysis modal summarizing drive competitiveness and preparation roadmaps.

### 5. Upcoming Interview Calendar & Scheduling
- Agenda view of upcoming technical assessments and interviews.
- Interactive **"Record Outcome"** modal allowing coordinators to mark rounds as `cleared` or `failed` with qualitative interview feedback.

### 6. Candidate Profile & Skills Management
- Edit candidate details (Roll No / USN, college email, branch, CGPA, graduation year).
- Dynamic technical skills tagging system (add/remove skills with tag chips).
- Integrated placement readiness metrics and offers log.

### 7. AI Skill Gap Diagnostics
- Select any student and target recruitment drive to instantly evaluate eligibility.
- Visual skill overlap breakdown: computes skill match percentage, matched skills chips, and missing skill gaps.
- Curated study questions automatically recommended for the diagnosed gaps.

### 8. Interview Preparation & Mock Evaluator
- Filterable question bank by category (*DSA*, *Core CS*, *System Design*, *Database*, *Behavioral HR*, *Aptitude*).
- Solution strategy toggle for self-paced learning.
- Interactive Mock Interview evaluation form to record session topics, scores, and track candidate readiness ratings.

### 9. Post-Interview Follow-Up Email Generator
- Select an active application and completed interview round.
- Generates a polished, professional thank-you email following corporate etiquette, tailored to the topics discussed.
- Includes a 1-click **Copy to Clipboard** utility.

### 10. Official MCP Python SDK (`mcp==2.3.0`)
- **8 MCP Tools:** `register_student`, `add_job_opening`, `check_job_eligibility`, `apply_for_job`, `schedule_interview`, `update_interview_outcome`, `get_student_placement_summary`, `get_interview_prep_plan`.
- **4 MCP Resources:** `placement://students/{id}/profile`, `placement://students/{id}/applications`, `placement://students/{id}/skills`, `placement://jobs/active`.
- **3 MCP Prompts:** `interview_preparation`, `job_analysis`, `follow_up_email`.

---

## 🏗️ Architecture & Directory Layout

```
placementpilot/
│
├── config/
│   ├── __init__.py
│   └── settings.py               # Local settings (SQLite file path, server metadata)
│
├── data/
│   ├── .gitkeep
│   └── placementpilot.db         # Local SQLite database (WAL mode, Foreign Keys ON)
│
├── src/
│   ├── db/                       # SQLite Persistence Layer
│   │   ├── connection.py         # Connection manager & row factory
│   │   ├── schema.sql            # DDL definitions (students, companies, jobs, applications, rounds, questions)
│   │   ├── init_db.py            # Database initialization and sample seed runner
│   │   └── repositories/         # Isolated SQL query objects (students, companies, applications, questions)
│   │
│   ├── services/                 # Domain Business Logic
│   │   ├── eligibility.py        # CGPA, branch, and skill match evaluation algorithms
│   │   ├── tracker.py            # Application pipeline state machine & funnel analytics
│   │   └── prep.py               # Skill gap analysis & mock interview evaluation
│   │
│   ├── mcp_server/               # Official MCP Python SDK Server
│   │   ├── server.py             # MCPServer STDIO runner
│   │   ├── tools/                # 8 MCP Tools (students, jobs, applications, prep)
│   │   ├── resources/            # 4 MCP Resources (profiles, applications, skills, active jobs)
│   │   └── prompts/              # 3 Reusable MCP Prompts (interview prep, job analysis, follow-up email)
│   │
│   └── web/                      # Frontend Dashboard & REST API
│       ├── app.py                # Starlette application & static file server
│       ├── api.py                # REST API endpoints
│       └── static/
│           ├── index.html        # Modern SaaS responsive SPA
│           ├── css/style.css     # Professional Dark Navy & Blue CSS Design System
│           └── js/app.js         # Reactive SPA controller
│
├── tests/                        # 50 Automated Unit & Integration Tests
│   ├── test_db.py                # Database & Repository CRUD tests (10 tests)
│   ├── test_services.py          # Eligibility & Tracker domain service tests (9 tests)
│   ├── test_mcp_server.py        # MCP Server tool, resource, and prompt tests (18 tests)
│   ├── test_api.py               # Web REST API integration tests (6 tests)
│   └── test_ui_contract.py       # Frontend view, modal & button contract tests (7 tests)
│
├── scripts/
│   └── demo_client.py            # End-to-end smoke test verifying MCP tools, resources & prompts
│
├── mcp_client_config.json        # Turnkey configuration for Claude Desktop / Antigravity / Cursor
├── pyproject.toml                # Project packaging configuration
├── requirements.txt              # Pinned Python dependencies
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Environment Preparation
```bash
# Clone or open the placementpilot workspace
cd placementpilot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize and Seed Local Database
```bash
python -m src.db.init_db
```
Populates `data/placementpilot.db` with sample students, companies, job drives, active applications, scheduled interview rounds, and curated interview questions.

### 3. Launch the Web Dashboard
```bash
python -m src.web.app
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser to access the complete PlacementPilot dashboard.

### 4. Run the MCP Server (for AI Assistants)
```bash
python -m src.mcp_server.server
```

### 5. Run the MCP Client Smoke Test
```bash
python scripts/demo_client.py
```

---

## 🔌 Connecting to MCP Clients (Claude Desktop / Antigravity / Cursor)

Add the configuration snippet from `mcp_client_config.json` to your client configuration file:

**Claude Desktop Configuration (`claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "placementpilot": {
      "command": "D:\\placementpilot\\.venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "D:\\placementpilot",
      "env": {
        "DATABASE_PATH": "D:\\placementpilot\\data\\placementpilot.db"
      }
    }
  }
}
```

---

## 🧪 Automated Test Suite

Run the full automated test suite (50 tests covering SQLite CRUD, business services, MCP endpoints, REST API, and frontend contracts):

```bash
pytest -v
```

---

## 📤 Preparing and Pushing to GitHub

The repository is configured with a strict `.gitignore` that safely excludes all virtual environments (`.venv`), cache files (`__pycache__`, `.pytest_cache`, `.uv_*`), and local database binaries (`data/*.db`).

To push PlacementPilot to GitHub:

```bash
# 1. Initialize git
git init

# 2. Add files
git add .

# 3. Create initial commit
git commit -m "Initial commit: PlacementPilot local AI placement platform"

# 4. Set branch to main
git branch -M main

# 5. Link your GitHub repository
git remote add origin https://github.com/<your-username>/PlacementPilot.git

# 6. Push to GitHub
git push -u origin main
```
