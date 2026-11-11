/**
 * PlacementPilot Frontend Application Controller
 * Handles SPA navigation, REST API interactions, dynamic DOM rendering, and modals.
 */

// Global State
const state = {
  currentView: "dashboard",
  activeStudentId: null,
  students: [],
  companies: [],
  jobs: [],
  applications: [],
  upcomingInterviews: [],
  profileSkills: [],
};

// =============================================================================
// Initialization & Navigation
// =============================================================================

document.addEventListener("DOMContentLoaded", async () => {
  setupNavigation();
  setupGlobalActions();
  setupProfileSkillTags();
  await refreshInitialData();
});

function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      const view = item.getAttribute("data-view");
      navigateTo(view);
    });
  });
}

function navigateTo(viewName) {
  state.currentView = viewName;

  // Update navigation items
  document.querySelectorAll(".nav-item").forEach((item) => {
    if (item.getAttribute("data-view") === viewName) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Update view sections
  document.querySelectorAll(".view-section").forEach((sec) => {
    sec.classList.remove("active");
  });
  const activeSec = document.getElementById(`view-${viewName}`);
  if (activeSec) activeSec.classList.add("active");

  // Update title
  const titles = {
    dashboard: "Dashboard Overview",
    applications: "Application Pipeline Management",
    calendar: "Upcoming Interview Calendar",
    companies: "Campus Drives & Companies",
    profile: "Student Profile & Competencies",
    skillgap: "AI Skill Gap Diagnostics",
    prep: "Interview Preparation & Questions",
    email: "Follow-up Email Generator",
  };
  const titleEl = document.getElementById("page-title");
  if (titleEl) titleEl.innerText = titles[viewName] || "PlacementPilot";

  // Trigger view data refresh
  loadViewData(viewName);
}

async function refreshInitialData() {
  await Promise.all([
    loadStudents(),
    loadCompanies(),
    loadJobs(),
  ]);
  loadViewData(state.currentView);
}

function loadViewData(viewName) {
  switch (viewName) {
    case "dashboard":
      loadDashboard();
      break;
    case "applications":
      loadApplications();
      break;
    case "calendar":
      loadCalendar();
      break;
    case "companies":
      loadJobsView();
      break;
    case "profile":
      loadProfileView();
      break;
    case "skillgap":
      initSkillGapView();
      break;
    case "prep":
      loadQuestions();
      initMockForm();
      break;
    case "email":
      initEmailView();
      break;
  }
}

// =============================================================================
// API Service Wrappers
// =============================================================================

async function apiRequest(endpoint, options = {}) {
  try {
    const res = await fetch(endpoint, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json.error || `HTTP error ${res.status}`);
    }
    return json.data;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    showToast(err.message, "error");
    throw err;
  }
}

// =============================================================================
// Students & Global State
// =============================================================================

async function loadStudents() {
  try {
    const students = await apiRequest("/api/students");
    state.students = students;

    const select = document.getElementById("global-student-select");
    const gapSelect = document.getElementById("gap-student-select");
    const applySelect = document.getElementById("apply-student");
    const mockSelect = document.getElementById("mock-student-id");

    const optionsHtml = students.map((s) => 
      `<option value="${s.id}">${s.name} (${s.branch} • ${s.cgpa.toFixed(2)})</option>`
    ).join("");

    if (select) {
      select.innerHTML = optionsHtml;
      if (!state.activeStudentId && students.length > 0) {
        state.activeStudentId = students[0].id;
      }
      if (state.activeStudentId) {
        select.value = state.activeStudentId;
      }
    }

    if (gapSelect) gapSelect.innerHTML = optionsHtml;
    if (applySelect) applySelect.innerHTML = optionsHtml;
    if (mockSelect) mockSelect.innerHTML = optionsHtml;
  } catch (err) {
    console.error("Failed to load students:", err);
  }
}

function setupGlobalActions() {
  const globalSelect = document.getElementById("global-student-select");
  if (globalSelect) {
    globalSelect.addEventListener("change", (e) => {
      state.activeStudentId = parseInt(e.target.value);
      showToast(`Active candidate switched.`, "info");
      loadViewData(state.currentView);
    });
  }

  const quickApplyBtn = document.getElementById("btn-quick-apply");
  if (quickApplyBtn) {
    quickApplyBtn.addEventListener("click", () => openApplyModal());
  }

  const quickAddJobBtn = document.getElementById("btn-quick-add-job");
  if (quickAddJobBtn) {
    quickAddJobBtn.addEventListener("click", () => openAddJobModal());
  }

  // Modals form submissions
  setupModalForms();
}

// =============================================================================
// View 1: Dashboard
// =============================================================================

async function loadDashboard() {
  try {
    const overview = await apiRequest("/api/overview");
    document.getElementById("stat-total-apps").innerText = overview.total_applications;
    document.getElementById("stat-interviews").innerText = overview.upcoming_interviews;
    document.getElementById("stat-offers").innerText = overview.offers_extended;
    document.getElementById("stat-active-drives").innerText = overview.active_jobs;

    // Featured Drives
    const drivesBody = document.getElementById("dashboard-drives-body");
    const jobs = await apiRequest("/api/jobs?status=open");
    state.jobs = jobs;

    if (!jobs || jobs.length === 0) {
      drivesBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">No active drives right now.</td></tr>`;
    } else {
      drivesBody.innerHTML = jobs.slice(0, 5).map((j) => `
        <tr>
          <td><strong>${escapeHtml(j.company_name)}</strong></td>
          <td>${escapeHtml(j.role_title)}</td>
          <td><span style="color: var(--accent-emerald); font-weight: 600;">₹${j.ctc_lpa} LPA</span></td>
          <td>${j.min_cgpa.toFixed(1)}</td>
          <td>${formatBranches(j.allowed_branches)}</td>
          <td>
            <button class="btn btn-primary btn-sm" onclick="quickApply(${j.id})">Apply</button>
          </td>
        </tr>
      `).join("");
    }

    // Active Student Snapshot
    renderDashboardStudentCard();
  } catch (err) {
    console.error("Dashboard load failed:", err);
  }
}

async function renderDashboardStudentCard() {
  const container = document.getElementById("dashboard-student-card");
  if (!container) return;

  if (!state.activeStudentId) {
    container.innerHTML = `<p style="color: var(--text-muted);">No student selected.</p>`;
    return;
  }

  try {
    const student = await apiRequest(`/api/students/${state.activeStudentId}`);
    const summary = await apiRequest(`/api/students/${state.activeStudentId}/summary`);

    container.innerHTML = `
      <div style="margin-bottom: 1rem;">
        <h3 style="font-size: 1.15rem; color: #fff;">${escapeHtml(student.name)}</h3>
        <p style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(student.usn)} • ${escapeHtml(student.branch)} • CGPA: <strong>${student.cgpa.toFixed(2)}</strong></p>
      </div>

      <div style="display: flex; gap: 0.75rem; margin-bottom: 1rem;">
        <div style="background: rgba(0,0,0,0.25); padding: 0.5rem 0.75rem; border-radius: var(--radius-sm); flex: 1;">
          <div style="font-size: 0.7rem; color: var(--text-dim);">APPLIED</div>
          <div style="font-size: 1.25rem; font-weight: 700;">${summary.total_applications}</div>
        </div>
        <div style="background: rgba(0,0,0,0.25); padding: 0.5rem 0.75rem; border-radius: var(--radius-sm); flex: 1;">
          <div style="font-size: 0.7rem; color: var(--text-dim);">INTERVIEWS</div>
          <div style="font-size: 1.25rem; font-weight: 700; color: var(--accent-purple);">${summary.upcoming_interviews_count}</div>
        </div>
        <div style="background: rgba(0,0,0,0.25); padding: 0.5rem 0.75rem; border-radius: var(--radius-sm); flex: 1;">
          <div style="font-size: 0.7rem; color: var(--text-dim);">OFFERS</div>
          <div style="font-size: 1.25rem; font-weight: 700; color: var(--accent-emerald);">${summary.offers_count}</div>
        </div>
      </div>

      <div>
        <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-muted); margin-bottom: 0.35rem;">SKILLS:</div>
        <div class="tag-container">
          ${(student.skills || []).map(s => `<span class="tag-chip">${escapeHtml(s)}</span>`).join("") || '<span style="color: var(--text-dim); font-size: 0.75rem;">No skills declared</span>'}
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<p style="color: var(--accent-rose); font-size: 0.85rem;">Failed to load candidate snapshot.</p>`;
  }
}

// =============================================================================
// View 2: Applications
// =============================================================================

async function loadApplications() {
  const filter = document.getElementById("filter-app-status");
  const status = filter ? filter.value : "";
  const tableBody = document.getElementById("applications-table-body");
  if (!tableBody) return;

  try {
    const url = status ? `/api/applications?status=${status}` : "/api/applications";
    const apps = await apiRequest(url);
    state.applications = apps;

    if (!apps || apps.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">No applications found.</td></tr>`;
      return;
    }

    tableBody.innerHTML = apps.map((app) => `
      <tr>
        <td>
          <strong>${escapeHtml(app.student_name)}</strong>
          <div style="font-size: 0.75rem; color: var(--text-dim);">${escapeHtml(app.student_usn)} • ${escapeHtml(app.student_branch)}</div>
        </td>
        <td>
          <strong>${escapeHtml(app.company_name)}</strong>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(app.role_title)}</div>
        </td>
        <td><span style="color: var(--accent-emerald); font-weight: 600;">₹${app.ctc_lpa} LPA</span></td>
        <td><span class="badge badge-${app.status}">${app.status.replace("_", " ")}</span></td>
        <td><span style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(app.current_stage || "In Review")}</span></td>
        <td>
          <div style="display: flex; gap: 0.35rem;">
            <button class="btn btn-secondary btn-sm" onclick="openScheduleRoundModal(${app.id})">+ Schedule</button>
            <button class="btn btn-secondary btn-sm" onclick="viewRoundsHistory(${app.id})">History</button>
          </div>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--accent-rose);">Failed to load applications.</td></tr>`;
  }
}

// =============================================================================
// View 3: Companies & Job Drives
// =============================================================================

async function loadCompanies() {
  try {
    const comps = await apiRequest("/api/companies");
    state.companies = comps;
  } catch (err) {
    console.error("Failed to load companies:", err);
  }
}

async function loadJobs() {
  try {
    const jobs = await apiRequest("/api/jobs");
    state.jobs = jobs;

    const gapSelect = document.getElementById("gap-job-select");
    const applySelect = document.getElementById("apply-job");
    const optionsHtml = jobs.map((j) =>
      `<option value="${j.id}">${j.company_name} - ${j.role_title} (₹${j.ctc_lpa} LPA)</option>`
    ).join("");

    if (gapSelect) gapSelect.innerHTML = optionsHtml;
    if (applySelect) applySelect.innerHTML = optionsHtml;
  } catch (err) {
    console.error("Failed to load jobs:", err);
  }
}

async function loadJobsView() {
  const tableBody = document.getElementById("jobs-table-body");
  if (!tableBody) return;

  try {
    const jobs = await apiRequest("/api/jobs");
    state.jobs = jobs;

    if (!jobs || jobs.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim);">No job drives registered.</td></tr>`;
      return;
    }

    tableBody.innerHTML = jobs.map((job) => `
      <tr>
        <td><strong>${escapeHtml(job.company_name)}</strong></td>
        <td>${escapeHtml(job.role_title)}</td>
        <td><span style="color: var(--accent-emerald); font-weight: 600;">₹${job.ctc_lpa} LPA</span></td>
        <td>
          <div>Min CGPA: <strong>${job.min_cgpa.toFixed(1)}</strong></div>
          <div style="font-size: 0.75rem; color: var(--text-dim);">${formatBranches(job.allowed_branches)}</div>
        </td>
        <td>
          <div class="tag-container">
            ${(job.required_skills || []).slice(0, 3).map(s => `<span class="tag-chip">${escapeHtml(s)}</span>`).join("")}
            ${(job.required_skills || []).length > 3 ? `<span class="tag-chip">+${job.required_skills.length - 3}</span>` : ""}
          </div>
        </td>
        <td><span class="badge badge-${job.status}">${job.status}</span></td>
        <td>
          <div style="display: flex; gap: 0.35rem;">
            <button class="btn btn-primary btn-sm" onclick="quickApply(${job.id})">Apply</button>
            <button class="btn btn-secondary btn-sm" onclick="viewJobAnalysis(${job.id}, '${escapeHtml(job.role_title)}')">AI Analysis</button>
            <button class="btn btn-danger btn-sm" onclick="deleteJob(${job.id})">Delete</button>
          </div>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--accent-rose);">Failed to load job drives.</td></tr>`;
  }
}

// =============================================================================
// View 4: Interview Calendar & Schedules
// =============================================================================

async function loadCalendar() {
  const container = document.getElementById("calendar-list");
  const countBadge = document.getElementById("calendar-count-badge");
  if (!container) return;

  try {
    const upcoming = await apiRequest("/api/interviews/upcoming");
    state.upcomingInterviews = upcoming;

    if (countBadge) countBadge.innerText = `${upcoming.length} Pending`;

    if (!upcoming || upcoming.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">No upcoming interviews scheduled. Schedule one from the Applications page!</p>`;
      return;
    }

    container.innerHTML = upcoming.map((item) => `
      <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center; border-left: 4px solid var(--accent-purple);">
        <div>
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
            <span class="badge badge-interview_scheduled">Round ${item.round_number}: ${escapeHtml(item.round_type)}</span>
            <span style="font-size: 0.8rem; color: var(--text-dim);">${item.scheduled_at || 'Date to be finalized'}</span>
          </div>
          <h4 style="font-size: 1.05rem; margin-bottom: 0.2rem;">${escapeHtml(item.student_name)} • ${escapeHtml(item.role_title)}</h4>
          <p style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(item.company_name)} | ${escapeHtml(item.interviewer_notes || "No special instructions")}</p>
        </div>
        <div>
          <button class="btn btn-primary btn-sm" onclick="openRecordOutcomeModal(${item.id})">Record Outcome</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<p style="color: var(--accent-rose);">Failed to load upcoming interviews.</p>`;
  }
}

// =============================================================================
// View 5: Student Profile & Skills
// =============================================================================

async function loadProfileView() {
  if (!state.activeStudentId) return;

  try {
    const student = await apiRequest(`/api/students/${state.activeStudentId}`);
    document.getElementById("prof-id").value = student.id;
    document.getElementById("prof-usn").value = student.usn;
    document.getElementById("prof-name").value = student.name;
    document.getElementById("prof-email").value = student.email;
    document.getElementById("prof-branch").value = student.branch;
    document.getElementById("prof-cgpa").value = student.cgpa;
    document.getElementById("prof-year").value = student.graduation_year;
    document.getElementById("prof-resume").value = student.resume_path || "";

    state.profileSkills = [...(student.skills || [])];
    renderProfileSkillChips();

    // Load readiness metrics
    const summary = await apiRequest(`/api/students/${state.activeStudentId}/summary`);
    const readinessContainer = document.getElementById("profile-readiness-stats");
    if (readinessContainer) {
      readinessContainer.innerHTML = `
        <div class="metrics-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 1.5rem;">
          <div class="metric-card">
            <div class="metric-label">Applications</div>
            <div class="metric-value" style="font-size: 1.5rem;">${summary.total_applications}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Offers</div>
            <div class="metric-value" style="font-size: 1.5rem; color: var(--accent-emerald);">${summary.offers_count}</div>
          </div>
        </div>

        <h4 style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.5rem;">Recent Offers</h4>
        ${summary.offers.length > 0 ? summary.offers.map(o => `
          <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 0.75rem; border-radius: var(--radius-sm); margin-bottom: 0.5rem;">
            <strong>${escapeHtml(o.company_name)}</strong> — ${escapeHtml(o.role_title)}
            <div style="color: var(--accent-emerald); font-weight: 700;">₹${o.ctc_lpa} LPA</div>
          </div>
        `).join("") : '<p style="font-size: 0.8rem; color: var(--text-dim);">No offers secured yet. Keep preparing!</p>'}
      `;
    }
  } catch (err) {
    console.error("Profile view load error:", err);
  }
}

function setupProfileSkillTags() {
  const input = document.getElementById("skill-input");
  const addBtn = document.getElementById("btn-add-skill");

  function addCurrentSkill() {
    if (!input) return;
    const val = input.value.trim();
    if (val && !state.profileSkills.includes(val)) {
      state.profileSkills.push(val);
      input.value = "";
      renderProfileSkillChips();
    }
  }

  if (addBtn) addBtn.addEventListener("click", addCurrentSkill);
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        addCurrentSkill();
      }
    });
  }

  // Profile Form Save
  const form = document.getElementById("student-profile-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const payload = {
          usn: document.getElementById("prof-usn").value.trim(),
          name: document.getElementById("prof-name").value.trim(),
          email: document.getElementById("prof-email").value.trim(),
          branch: document.getElementById("prof-branch").value,
          cgpa: parseFloat(document.getElementById("prof-cgpa").value),
          graduation_year: parseInt(document.getElementById("prof-year").value),
          skills: state.profileSkills,
          resume_path: document.getElementById("prof-resume").value.trim() || null,
        };

        const res = await apiRequest("/api/students", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        showToast(`Profile for ${res.student.name} saved successfully!`, "success");
        await loadStudents();
        state.activeStudentId = res.student.id;
        loadProfileView();
      } catch (err) {
        // Error already toasted by apiRequest
      }
    });
  }
}

function renderProfileSkillChips() {
  const container = document.getElementById("profile-skills-chips");
  if (!container) return;
  container.innerHTML = state.profileSkills.map((skill, index) => `
    <span class="tag-chip">
      ${escapeHtml(skill)}
      <span class="tag-remove" onclick="removeSkill(${index})">&times;</span>
    </span>
  `).join("");
}

function removeSkill(index) {
  state.profileSkills.splice(index, 1);
  renderProfileSkillChips();
}

function resetStudentForm() {
  document.getElementById("prof-id").value = "";
  document.getElementById("prof-usn").value = "";
  document.getElementById("prof-name").value = "";
  document.getElementById("prof-email").value = "";
  document.getElementById("prof-cgpa").value = "";
  document.getElementById("prof-resume").value = "";
  state.profileSkills = [];
  renderProfileSkillChips();
  showToast("Candidate form reset for new entry.", "info");
}

// =============================================================================
// View 6: AI Skill Gap Analysis
// =============================================================================

function initSkillGapView() {
  const btn = document.getElementById("btn-run-skillgap");
  if (btn) {
    btn.onclick = async () => {
      const studentId = document.getElementById("gap-student-select").value;
      const jobId = document.getElementById("gap-job-select").value;

      if (!studentId || !jobId) {
        showToast("Please select both a student and a job drive.", "error");
        return;
      }

      try {
        btn.disabled = true;
        btn.innerText = "Analyzing...";

        const gapData = await apiRequest(`/api/prep/skill-gap?student_id=${studentId}&job_id=${jobId}`);
        const eligData = await apiRequest(`/api/prep/eligibility?student_id=${studentId}&job_id=${jobId}`);

        document.getElementById("skillgap-results").style.display = "block";

        // Render Eligibility
        const eligCard = document.getElementById("gap-eligibility-card");
        eligCard.innerHTML = `
          <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; color: ${eligData.is_eligible ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">
            ${eligData.is_eligible ? '✅ ELIGIBLE TO APPLY' : '❌ NOT ELIGIBLE'}
          </div>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">
            CGPA Requirement: ${eligData.student_cgpa.toFixed(2)} / ${eligData.required_cgpa.toFixed(2)} 
            (${eligData.cgpa_satisfied ? 'Passed' : 'Cutoff Not Met'})
          </p>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">
            Branch Requirement: ${eligData.student_branch} 
            (${eligData.branch_satisfied ? 'Eligible' : 'Branch Restricted'})
          </p>
          ${eligData.disqualification_reasons.length > 0 ? `
            <div style="background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); padding: 0.5rem; border-radius: var(--radius-sm); font-size: 0.8rem; color: #fca5a5;">
              ${eligData.disqualification_reasons.join("<br>")}
            </div>
          ` : ''}
        `;

        // Render Skills
        const skillsCard = document.getElementById("gap-skills-card");
        skillsCard.innerHTML = `
          <div style="margin-bottom: 0.75rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.35rem;">
              <span>Skill Match Score</span>
              <strong style="color: var(--accent-cyan);">${gapData.skill_match_percentage}%</strong>
            </div>
            <div style="background: rgba(255,255,255,0.06); height: 8px; border-radius: 9999px; overflow: hidden;">
              <div style="background: linear-gradient(to right, var(--accent-blue), var(--accent-cyan)); height: 100%; width: ${gapData.skill_match_percentage}%;"></div>
            </div>
          </div>

          <div style="margin-bottom: 0.5rem;">
            <div style="font-size: 0.75rem; color: var(--accent-emerald); font-weight: 600; margin-bottom: 0.25rem;">MATCHED SKILLS:</div>
            <div class="tag-container">
              ${(gapData.matched_skills || []).map(s => `<span class="tag-chip" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border-color: rgba(16, 185, 129, 0.3);">${escapeHtml(s)}</span>`).join("") || '<span style="color: var(--text-dim); font-size: 0.75rem;">None</span>'}
            </div>
          </div>

          <div>
            <div style="font-size: 0.75rem; color: var(--accent-rose); font-weight: 600; margin-bottom: 0.25rem;">MISSING SKILL GAPS:</div>
            <div class="tag-container">
              ${(gapData.missing_skills || []).map(s => `<span class="tag-chip" style="background: rgba(244, 63, 94, 0.15); color: #fb7185; border-color: rgba(244, 63, 94, 0.3);">${escapeHtml(s)}</span>`).join("") || '<span style="color: var(--accent-emerald); font-size: 0.75rem;">No skill gaps detected!</span>'}
            </div>
          </div>
        `;

        // Render Questions
        const qList = document.getElementById("gap-questions-list");
        if (gapData.recommended_questions.length === 0) {
          qList.innerHTML = `<p style="color: var(--text-muted); font-size: 0.85rem;">No questions specifically tagged for this profile gap.</p>`;
        } else {
          qList.innerHTML = gapData.recommended_questions.map((q) => `
            <div style="background: var(--bg-card); border: 1px solid var(--border-subtle); padding: 1rem; border-radius: var(--radius-sm); margin-bottom: 0.75rem;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                <span class="badge badge-shortlisted">${q.category} • ${escapeHtml(q.topic)}</span>
                <span style="font-size: 0.75rem; color: var(--accent-amber); font-weight: 600;">${q.difficulty}</span>
              </div>
              <p style="font-size: 0.9rem; margin-bottom: 0.5rem;">${escapeHtml(q.question_text)}</p>
              ${q.solution_guide ? `
                <details style="font-size: 0.8rem; color: var(--text-muted); cursor: pointer;">
                  <summary style="color: var(--accent-blue);">View Solution Strategy</summary>
                  <p style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(0,0,0,0.2); border-radius: var(--radius-sm);">${escapeHtml(q.solution_guide)}</p>
                </details>
              ` : ''}
            </div>
          `).join("");
        }

        showToast("Skill gap diagnostics completed.", "success");
      } catch (err) {
        // Error already handled
      } finally {
        btn.disabled = false;
        btn.innerText = "⚡ Run Diagnostic";
      }
    };
  }
}

// =============================================================================
// View 7: Interview Prep & Mock Logging
// =============================================================================

async function loadQuestions() {
  const container = document.getElementById("questions-container");
  const filter = document.getElementById("filter-q-category");
  const cat = filter ? filter.value : "";
  if (!container) return;

  try {
    const url = cat ? `/api/prep/questions?category=${cat}` : "/api/prep/questions";
    const questions = await apiRequest(url);

    if (!questions || questions.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted);">No questions found in this category.</p>`;
      return;
    }

    container.innerHTML = questions.map((q) => `
      <div class="panel" style="background: var(--bg-surface); padding: 1rem; margin-bottom: 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <span class="badge badge-applied">${q.category} • ${escapeHtml(q.topic)}</span>
          <span style="font-size: 0.75rem; color: var(--accent-amber); font-weight: 600;">${q.difficulty}</span>
        </div>
        <p style="font-size: 0.95rem; margin-bottom: 0.5rem; font-weight: 500;">${escapeHtml(q.question_text)}</p>
        ${q.solution_guide ? `
          <details style="font-size: 0.8rem; color: var(--text-muted); cursor: pointer;">
            <summary style="color: var(--accent-blue);">View Solution Guide</summary>
            <p style="margin-top: 0.5rem; padding: 0.75rem; background: rgba(0,0,0,0.25); border-radius: var(--radius-sm);">${escapeHtml(q.solution_guide)}</p>
          </details>
        ` : ''}
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<p style="color: var(--accent-rose);">Failed to load questions.</p>`;
  }
}

function initMockForm() {
  const form = document.getElementById("mock-interview-form");
  const catFilter = document.getElementById("filter-q-category");

  if (catFilter) {
    catFilter.onchange = () => loadQuestions();
  }

  if (form) {
    form.onsubmit = async (e) => {
      e.preventDefault();
      try {
        const payload = {
          student_id: parseInt(document.getElementById("mock-student-id").value),
          topic: document.getElementById("mock-topic").value.trim(),
          score: parseFloat(document.getElementById("mock-score").value),
          feedback: document.getElementById("mock-feedback").value.trim(),
        };

        const res = await apiRequest("/api/prep/mock-interview", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        showToast(`Mock recorded! Average Score: ${res.average_score} (${res.readiness_verdict})`, "success");
        form.reset();
      } catch (err) {
        // Handled
      }
    };
  }
}

// =============================================================================
// View 8: Follow-up Email Generator
// =============================================================================

async function initEmailView() {
  const appSelect = document.getElementById("email-app-select");
  const roundSelect = document.getElementById("email-round-select");
  const generateBtn = document.getElementById("btn-generate-email");
  const copyBtn = document.getElementById("btn-copy-email");

  try {
    const apps = await apiRequest("/api/applications");
    if (!appSelect) return;

    appSelect.innerHTML = apps.map((a) => 
      `<option value="${a.id}">${a.student_name} ➔ ${a.company_name} (${a.role_title})</option>`
    ).join("");

    async function loadRoundsForApp(appId) {
      if (!appId) return;
      const rounds = await apiRequest(`/api/applications/${appId}/rounds`);
      if (roundSelect) {
        if (rounds.length === 0) {
          roundSelect.innerHTML = `<option value="">No rounds scheduled for this application</option>`;
        } else {
          roundSelect.innerHTML = rounds.map((r) =>
            `<option value="${r.id}">Round ${r.round_number}: ${r.round_type} (${r.status})</option>`
          ).join("");
        }
      }
    }

    if (apps.length > 0) {
      loadRoundsForApp(apps[0].id);
    }

    appSelect.onchange = () => loadRoundsForApp(appSelect.value);

    if (generateBtn) {
      generateBtn.onclick = async () => {
        const appId = appSelect.value;
        const roundId = roundSelect.value;

        if (!appId || !roundId) {
          showToast("Please select an application and a round.", "error");
          return;
        }

        try {
          generateBtn.disabled = true;
          generateBtn.innerText = "Drafting...";

          const emailData = await apiRequest("/api/generator/follow-up-email", {
            method: "POST",
            body: JSON.stringify({ application_id: parseInt(appId), round_id: parseInt(roundId) }),
          });

          document.getElementById("email-output-container").style.display = "block";
          document.getElementById("email-subject").value = emailData.draft_subject;
          document.getElementById("email-body").value = emailData.draft_body;
          showToast("Email draft generated successfully!", "success");
        } catch (err) {
          // Handled
        } finally {
          generateBtn.disabled = false;
          generateBtn.innerText = "✨ Generate Email";
        }
      };
    }

    if (copyBtn) {
      copyBtn.onclick = () => {
        const bodyText = document.getElementById("email-body").value;
        navigator.clipboard.writeText(bodyText);
        showToast("Email copied to clipboard!", "success");
      };
    }
  } catch (err) {
    console.error("Init email view failed:", err);
  }
}

// =============================================================================
// Modals & Dynamic Form Actions
// =============================================================================

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.showModal();
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.close();
}

function openApplyModal(jobId = null) {
  openModal("modal-apply");
  if (jobId) {
    const select = document.getElementById("apply-job");
    if (select) select.value = jobId;
  }
  if (state.activeStudentId) {
    const studentSelect = document.getElementById("apply-student");
    if (studentSelect) studentSelect.value = state.activeStudentId;
  }
}

function quickApply(jobId) {
  openApplyModal(jobId);
}

function openAddJobModal() {
  openModal("modal-add-job");
}

function openAddCompanyModal() {
  openModal("modal-add-comp");
}

function openScheduleRoundModal(appId) {
  document.getElementById("sched-app-id").value = appId;
  openModal("modal-schedule-round");
}

function openRecordOutcomeModal(roundId) {
  document.getElementById("outcome-round-id").value = roundId;
  openModal("modal-record-outcome");
}

async function viewRoundsHistory(appId) {
  openModal("modal-view-rounds");
  const content = document.getElementById("rounds-timeline-content");
  content.innerHTML = `<p style="color: var(--text-muted);">Loading round history...</p>`;

  try {
    const rounds = await apiRequest(`/api/applications/${appId}/rounds`);
    if (!rounds || rounds.length === 0) {
      content.innerHTML = `<p style="color: var(--text-dim);">No interview rounds scheduled yet.</p>`;
      return;
    }

    content.innerHTML = rounds.map((r) => `
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); padding: 0.85rem; border-radius: var(--radius-sm); margin-bottom: 0.75rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
          <strong>Round ${r.round_number}: ${escapeHtml(r.round_type)}</strong>
          <span class="badge badge-${r.status}">${r.status}</span>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 0.5rem;">Scheduled: ${r.scheduled_at || 'Pending schedule'}</div>
        ${r.feedback ? `<div style="font-size: 0.85rem; color: var(--text-main); background: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px;"><strong>Feedback:</strong> ${escapeHtml(r.feedback)}</div>` : ''}
      </div>
    `).join("");
  } catch (err) {
    content.innerHTML = `<p style="color: var(--accent-rose);">Failed to load history.</p>`;
  }
}

async function viewJobAnalysis(jobId, roleTitle) {
  openModal("modal-job-analysis");
  document.getElementById("analysis-job-title").innerText = `AI Analysis: ${roleTitle}`;
  const content = document.getElementById("analysis-content");
  content.innerText = "Analyzing role requirements and benchmark criteria with AI...";

  try {
    const data = await apiRequest(`/api/jobs/${jobId}/analysis`, { method: "POST" });
    content.innerText = data.prompt;
  } catch (err) {
    content.innerText = "Failed to load job analysis.";
  }
}

async function deleteJob(jobId) {
  if (!confirm("Are you sure you want to delete this job drive? Associated applications will be deleted.")) return;
  try {
    await apiRequest(`/api/jobs/${jobId}`, { method: "DELETE" });
    showToast("Job drive deleted.", "info");
    loadJobsView();
    loadJobs();
  } catch (err) {
    // Handled
  }
}

function setupModalForms() {
  // Apply Form
  const applyForm = document.getElementById("form-apply");
  if (applyForm) {
    applyForm.onsubmit = async (e) => {
      e.preventDefault();
      try {
        const payload = {
          student_id: parseInt(document.getElementById("apply-student").value),
          job_id: parseInt(document.getElementById("apply-job").value),
          notes: document.getElementById("apply-notes").value.trim(),
          enforce_eligibility: document.getElementById("apply-enforce").checked,
        };

        await apiRequest("/api/applications", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        showToast("Application submitted successfully!", "success");
        closeModal("modal-apply");
        loadDashboard();
        loadApplications();
      } catch (err) {
        // Handled
      }
    };
  }

  // Add Job Form
  const jobForm = document.getElementById("form-add-job");
  if (jobForm) {
    jobForm.onsubmit = async (e) => {
      e.preventDefault();
      try {
        const branches = document.getElementById("job-branches").value.split(",").map(s => s.trim()).filter(Boolean);
        const skills = document.getElementById("job-skills").value.split(",").map(s => s.trim()).filter(Boolean);

        const payload = {
          company_name: document.getElementById("job-comp-name").value.trim(),
          role_title: document.getElementById("job-role").value.trim(),
          ctc_lpa: parseFloat(document.getElementById("job-ctc").value),
          min_cgpa: parseFloat(document.getElementById("job-cgpa").value) || 0.0,
          allowed_branches: branches,
          required_skills: skills,
          location: document.getElementById("job-location").value.trim(),
          application_deadline: document.getElementById("job-deadline").value || null,
          job_description: document.getElementById("job-desc").value.trim(),
        };

        await apiRequest("/api/jobs", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        showToast("Job drive created successfully!", "success");
        closeModal("modal-add-job");
        await loadJobs();
        loadJobsView();
        loadDashboard();
      } catch (err) {
        // Handled
      }
    };
  }

  // Add Company Form
  const compForm = document.getElementById("form-add-comp");
  if (compForm) {
    compForm.onsubmit = async (e) => {
      e.preventDefault();
      try {
        const payload = {
          name: document.getElementById("comp-name").value.trim(),
          website: document.getElementById("comp-web").value.trim(),
          industry: document.getElementById("comp-ind").value.trim(),
          description: document.getElementById("comp-desc").value.trim(),
        };

        await apiRequest("/api/companies", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        showToast("Company registered successfully!", "success");
        closeModal("modal-add-comp");
        await loadCompanies();
      } catch (err) {
        // Handled
      }
    };
  }

  // Schedule Round Form
  const schedForm = document.getElementById("form-schedule-round");
  if (schedForm) {
    schedForm.onsubmit = async (e) => {
      e.preventDefault();
      try {
        const appId = document.getElementById("sched-app-id").value;
        const payload = {
          round_type: document.getElementById("sched-type").value,
          scheduled_at: document.getElementById("sched-date").value || null,
          interviewer_notes: document.getElementById("sched-notes").value.trim(),
        };

        await apiRequest(`/api/applications/${appId}/rounds`, {
          method: "POST",
          body: JSON.stringify(payload),
        });

        showToast("Interview round scheduled!", "success");
        closeModal("modal-schedule-round");
        loadApplications();
        loadCalendar();
        loadDashboard();
      } catch (err) {
        // Handled
      }
    };
  }

  // Record Outcome Form
  const outcomeForm = document.getElementById("form-record-outcome");
  if (outcomeForm) {
    outcomeForm.onsubmit = async (e) => {
      e.preventDefault();
      try {
        const roundId = document.getElementById("outcome-round-id").value;
        const payload = {
          status: document.getElementById("outcome-status").value,
          feedback: document.getElementById("outcome-feedback").value.trim(),
        };

        await apiRequest(`/api/rounds/${roundId}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });

        showToast("Interview outcome recorded!", "success");
        closeModal("modal-record-outcome");
        loadCalendar();
        loadApplications();
        loadDashboard();
      } catch (err) {
        // Handled
      }
    };
  }
}

// =============================================================================
// Toast Notification Utility
// =============================================================================

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ')}</span> <div>${escapeHtml(message)}</div>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Helpers
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatBranches(branches) {
  if (!branches || branches.length === 0) return "All Branches";
  return branches.join(", ");
}

