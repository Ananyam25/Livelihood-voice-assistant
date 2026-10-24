/* =============================================================
   app.js – Livelihood Voice Assistant
   Voice recording, image upload, API calls, TTS, UI rendering
   ============================================================= */

"use strict";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const API_BASE = window.location.origin;

// Avatar emojis keyed by occupation category
const AVATARS = {
  carpenter : "🪚",
  wood      : "🪵",
  weav      : "🧵",
  loom      : "🧶",
  hvac      : "❄️",
  ac        : "🌀",
  refriger  : "🧊",
  electr    : "⚡",
  construct : "🏗️",
  default   : "👷",
};

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const micBtn       = document.getElementById("mic-btn");
const micIcon      = document.getElementById("mic-icon");
const stopIcon     = document.getElementById("stop-icon");
const micStatus    = document.getElementById("mic-status");
const dropzone     = document.getElementById("image-dropzone");
const fileInput    = document.getElementById("file-input");
const imagePreview = document.getElementById("image-preview");
const previewImg   = document.getElementById("preview-img");
const textInput    = document.getElementById("text-input");
const analyseBtn   = document.getElementById("analyse-btn");
const loadingOverlay = document.getElementById("loading-overlay");
const resultsSection = document.getElementById("results-section");
const toast        = document.getElementById("toast");
const newAnalysisBtn = document.getElementById("new-analysis-btn");

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let isRecording     = false;
let recognition     = null;
let transcript      = "";
let selectedFile    = null;
let toastTimer      = null;
let currentAnalysis = null;

// ---------------------------------------------------------------------------
// TTS helper
// ---------------------------------------------------------------------------
const TTS = {
  speaking: false,
  speak(text, btn) {
    if (!window.speechSynthesis) return;
    if (this.speaking) {
      speechSynthesis.cancel();
      this.speaking = false;
      if (btn) btn.textContent = "▶ Read Aloud";
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.92;
    utterance.pitch = 1.05;
    // Prefer a female, Indian-accent voice if available
    const voices = speechSynthesis.getVoices();
    const preferred = voices.find(v => /india|hindi|en-IN/i.test(v.lang + v.name));
    if (preferred) utterance.voice = preferred;
    utterance.onstart = () => {
      this.speaking = true;
      if (btn) btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2"/></svg> Stop`;
    };
    utterance.onend = utterance.onerror = () => {
      this.speaking = false;
      if (btn) btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg> Read Aloud`;
    };
    speechSynthesis.speak(utterance);
  }
};

// Attach TTS buttons
document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-tts]");
  if (!btn) return;
  const targetId = btn.dataset.tts;
  const el = document.getElementById(targetId);
  if (!el) return;
  TTS.speak(el.textContent.trim(), btn);
});

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function showToast(message, type = "info") {
  toast.textContent = message;
  toast.className   = `show ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.className = ""; }, 4500);
}

// ---------------------------------------------------------------------------
// Voice Recording (Web Speech API)
// ---------------------------------------------------------------------------
function initRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const r = new SpeechRecognition();
  r.continuous      = true;
  r.interimResults  = true;
  r.lang            = "hi-IN"; // Start with Hindi; browser often auto-detects

  r.onstart = () => {
    isRecording  = true;
    transcript   = "";
    micStatus.textContent = "🔴 Recording… speak now in any language";
    micStatus.classList.add("active");
    micBtn.classList.add("recording");
    micBtn.setAttribute("aria-pressed", "true");
    micBtn.setAttribute("aria-label", "Stop recording");
    micIcon.style.display = "none";
    stopIcon.style.display = "block";
  };

  r.onresult = (event) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const res = event.results[i];
      if (res.isFinal) {
        transcript += res[0].transcript + " ";
      } else {
        interim = res[0].transcript;
      }
    }
    micStatus.textContent = `🎙 ${(transcript + interim).slice(-80)}…`;
    // Mirror into textarea for user visibility
    textInput.value = (transcript + interim).trim();
  };

  r.onerror = (event) => {
    if (event.error === "not-allowed") {
      showToast("Microphone permission denied. Please allow mic access.", "error");
    } else if (event.error !== "aborted") {
      showToast(`Voice error: ${event.error}`, "error");
    }
    stopRecording();
  };

  r.onend = () => {
    if (isRecording) {
      // Restart for continuous recording
      try { r.start(); } catch (_) { stopRecording(); }
    }
  };

  return r;
}

function startRecording() {
  if (!recognition) {
    recognition = initRecognition();
  }
  if (!recognition) {
    // Fallback: simulate recording state visually
    isRecording = true;
    micBtn.classList.add("recording");
    micBtn.setAttribute("aria-pressed", "true");
    micStatus.textContent = "🎙 Simulated recording (no mic API)…";
    micStatus.classList.add("active");
    micIcon.style.display = "none";
    stopIcon.style.display = "block";
    showToast("Voice recording not supported in this browser. Use text input.", "error");
    return;
  }
  try {
    recognition.start();
  } catch (err) {
    showToast("Could not start recording. Try again.", "error");
  }
}

function stopRecording() {
  isRecording = false;
  if (recognition) {
    try { recognition.stop(); } catch (_) {}
  }
  micBtn.classList.remove("recording");
  micBtn.setAttribute("aria-pressed", "false");
  micBtn.setAttribute("aria-label", "Start voice recording – click to speak your work experience");
  micStatus.classList.remove("active");
  micIcon.style.display = "block";
  stopIcon.style.display = "none";

  if (transcript.trim()) {
    micStatus.textContent = `✅ Recorded (${transcript.trim().split(" ").length} words). Tap again to re-record.`;
    showToast("Voice captured! Click 'Analyse My Experience' to continue.", "success");
  } else {
    micStatus.textContent = "Tap microphone and describe your work experience";
  }
}

micBtn.addEventListener("click", () => {
  if (isRecording) stopRecording();
  else              startRecording();
});

micBtn.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    micBtn.click();
  }
});

// ---------------------------------------------------------------------------
// Image Upload
// ---------------------------------------------------------------------------
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault(); dropzone.classList.add("drag-over");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault(); dropzone.classList.remove("drag-over");
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  if (!file.type.startsWith("image/")) {
    showToast("Please upload an image file (JPG, PNG, WEBP).", "error");
    return;
  }
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src        = e.target.result;
    imagePreview.style.display = "block";
  };
  reader.readAsDataURL(file);
  showToast(`Image "${file.name}" ready!`, "success");
}

// ---------------------------------------------------------------------------
// Core Analysis
// ---------------------------------------------------------------------------
async function runAnalysis(formData) {
  loadingOverlay.classList.add("active");
  analyseBtn.disabled = true;
  resultsSection.classList.remove("visible");

  try {
    const response = await fetch(`${API_BASE}/api/analyse`, {
      method: "POST",
      body  : formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(err.detail || `Server error ${response.status}`);
    }

    const data = await response.json();
    if (!data.success) throw new Error("Analysis returned unsuccessful.");

    currentAnalysis = data;
    renderResults(data);

    resultsSection.classList.add("visible");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    showToast("Analysis complete! See your profile below.", "success");

  } catch (err) {
    console.error("Analysis error:", err);
    showToast(`Error: ${err.message}`, "error");
  } finally {
    loadingOverlay.classList.remove("active");
    analyseBtn.disabled = false;
  }
}

async function runDemo(profileType) {
  loadingOverlay.classList.add("active");
  analyseBtn.disabled = true;
  resultsSection.classList.remove("visible");

  try {
    const response = await fetch(`${API_BASE}/api/demo?profile_type=${profileType}`);
    if (!response.ok) throw new Error(`Server error ${response.status}`);
    const data = await response.json();
    if (!data.success) throw new Error("Demo failed.");

    currentAnalysis = data;
    renderResults(data);

    resultsSection.classList.add("visible");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    showToast("Demo profile loaded!", "success");

  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  } finally {
    loadingOverlay.classList.remove("active");
    analyseBtn.disabled = false;
  }
}

// Main button
analyseBtn.addEventListener("click", () => {
  const txt = textInput.value.trim();
  const trans = transcript.trim();

  if (!txt && !trans && !selectedFile) {
    showToast("Please speak, type, or upload a photo first.", "error");
    return;
  }

  const fd = new FormData();
  if (trans) fd.append("transcript", trans);
  if (txt)   fd.append("text_input",  txt);
  if (selectedFile) fd.append("image", selectedFile);

  runAnalysis(fd);
});

// Demo buttons
document.querySelectorAll(".demo-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const profile = btn.dataset.profile;
    runDemo(profile);
  });
});

// New analysis button
newAnalysisBtn.addEventListener("click", () => {
  resultsSection.classList.remove("visible");
  transcript   = "";
  selectedFile = null;
  textInput.value = "";
  imagePreview.style.display = "none";
  previewImg.src = "";
  fileInput.value = "";
  micStatus.textContent = "Tap microphone and describe your work experience";
  window.scrollTo({ top: 0, behavior: "smooth" });
});

// ---------------------------------------------------------------------------
// Results rendering
// ---------------------------------------------------------------------------
function getAvatar(occupation) {
  const occ = (occupation || "").toLowerCase();
  for (const [key, emoji] of Object.entries(AVATARS)) {
    if (key !== "default" && occ.includes(key)) return emoji;
  }
  return AVATARS.default;
}

function makeBadge(text, type, dot = true) {
  const span = document.createElement("span");
  span.className = `badge badge-${type}`;
  span.setAttribute("role", "listitem");
  if (dot) {
    const d = document.createElement("span");
    d.className = "badge-dot";
    d.setAttribute("aria-hidden", "true");
    span.appendChild(d);
  }
  span.appendChild(document.createTextNode(
    text.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase())
  ));
  return span;
}

function animateGauge(score) {
  const circumference = 314; // 2π × 50
  const offset = circumference - (score / 100) * circumference;
  const fg = document.getElementById("gauge-fg");
  const num = document.getElementById("gauge-num");

  // Animate stroke
  fg.style.strokeDashoffset = offset;

  // Animate number
  let current = 0;
  const step = score / 60;
  const interval = setInterval(() => {
    current = Math.min(current + step, score);
    num.textContent = Math.round(current);
    if (current >= score) clearInterval(interval);
  }, 16);
}

function animateBar(fillEl, valEl, pct) {
  // Trigger CSS transition
  setTimeout(() => { fillEl.style.width = `${pct}%`; }, 50);
  let current = 0;
  const step = pct / 40;
  const interval = setInterval(() => {
    current = Math.min(current + step, pct);
    valEl.textContent = `${Math.round(current)}%`;
    if (current >= pct) clearInterval(interval);
  }, 16);
}

function renderResults(data) {
  const { skill_profile: profile, analysis } = data;

  // ── Readiness gauge ──────────────────────────────────────
  const rs = analysis.readiness_score || 0;
  animateGauge(rs);
  document.getElementById("readiness-text").textContent =
    `You are ${rs >= 75 ? "highly" : rs >= 50 ? "moderately" : "partially"} ready ` +
    `for top matching roles. Complete the recommended courses to boost your score.`;

  // ── Profile ──────────────────────────────────────────────
  document.getElementById("profile-avatar").textContent = getAvatar(profile.occupation);
  document.getElementById("profile-name").textContent       = profile.name || "Skilled Worker";
  document.getElementById("profile-occupation").textContent = profile.occupation || "—";
  document.getElementById("profile-experience").textContent =
    `${profile.years_experience || 0} years of experience · ${profile.input_type || "text"} input`;

  const confPct = Math.round((profile.confidence_score || 0) * 100);
  const confFill = document.getElementById("confidence-fill");
  const confVal  = document.getElementById("confidence-val");
  const confMeter = document.getElementById("confidence-meter");
  confMeter.setAttribute("aria-valuenow", confPct);
  animateBar(confFill, confVal, confPct);

  document.getElementById("profile-summary").textContent = profile.raw_summary || "—";

  // Skills badges
  const skillsEl = document.getElementById("skills-badges");
  skillsEl.innerHTML = "";
  (profile.skills || []).forEach(s => skillsEl.appendChild(makeBadge(s, "skill")));

  // Tools badges
  const toolsEl = document.getElementById("tools-badges");
  toolsEl.innerHTML = "";
  (profile.tools_detected || []).forEach(t => toolsEl.appendChild(makeBadge(t, "tool")));

  // Level + language badges
  const levelEl = document.getElementById("level-badges");
  levelEl.innerHTML = "";
  if (profile.experience_level) levelEl.appendChild(makeBadge(profile.experience_level, "level", false));
  if (profile.language_detected) levelEl.appendChild(makeBadge("🌐 " + profile.language_detected, "lang", false));

  // ── Pathway timeline ─────────────────────────────────────
  const pw = analysis.pathway;

  // Step 1 – Current
  const skills = (pw.current?.skills || []).slice(0, 4).join(", ");
  document.getElementById("step-current-detail").textContent =
    `${pw.current?.level || ""} · ${skills || "Many skills"}`;

  // Step 2 – Gap
  const gaps = (pw.gap?.skills || []).slice(0, 3).join(", ");
  document.getElementById("step-gap-detail").textContent =
    gaps ? `Add: ${gaps}` : "You're nearly there!";

  // Step 3 – Target
  const target = pw.target || {};
  document.getElementById("step-target-title").textContent = target.job_title || "Top Opportunity";
  document.getElementById("step-target-detail").textContent =
    `${target.salary_range || ""} · ${target.employer || ""} · ${target.match_score || 0}% match`;

  // TTS pathway text
  document.getElementById("pathway-tts-text").textContent =
    `Your career pathway: Step 1 – Your current skills include ${skills}. ` +
    `Step 2 – You need to develop: ${gaps || "no major gaps"}. ` +
    `Step 3 – Your target role is ${target.job_title} at ${target.employer}, ` +
    `paying ${target.salary_range}, with a ${target.match_score}% match score.`;

  // ── Skill Gaps ────────────────────────────────────────────
  const gapEl = document.getElementById("gap-badges");
  gapEl.innerHTML = "";
  const gaps_ = analysis.skill_gaps || [];
  if (gaps_.length === 0) {
    gapEl.innerHTML = '<span class="badge badge-skill"><span class="badge-dot" aria-hidden="true"></span>No critical gaps! You\'re ready to apply.</span>';
  } else {
    gaps_.forEach(g => gapEl.appendChild(makeBadge(g, "gap")));
  }

  // ── Jobs ──────────────────────────────────────────────────
  const jobsGrid = document.getElementById("jobs-grid");
  jobsGrid.innerHTML = "";
  (analysis.matched_jobs || []).forEach((job, idx) => {
    const card = document.createElement("article");
    card.className = "job-card";
    card.setAttribute("role", "listitem");
    card.setAttribute("aria-label", `Job opportunity: ${job.title}`);

    const matchColor = job.match_score >= 70 ? "var(--clr-success)" : job.match_score >= 50 ? "var(--clr-gold)" : "var(--clr-error)";

    card.innerHTML = `
      <div class="job-match-badge" style="background:${matchColor === "var(--clr-success)" ? "linear-gradient(135deg,#22d3a0,#059669)" : matchColor === "var(--clr-gold)" ? "linear-gradient(135deg,#fbbf24,#d97706)" : "linear-gradient(135deg,#f87171,#dc2626)"}; color:#000">
        ${job.match_score}% Match
      </div>
      <div class="job-title">${escHtml(job.title)}</div>
      <div class="job-employer">🏢 ${escHtml(job.employer)}</div>
      <div class="job-salary">💰 ${escHtml(job.salary_range_inr)}</div>
      <div class="job-meta">
        <span class="job-meta-chip">📍 ${escHtml(job.location)}</span>
        <span class="job-meta-chip">📋 ${escHtml(job.type)}</span>
        <span class="job-meta-chip">👥 ${job.openings} opening${job.openings !== 1 ? "s" : ""}</span>
      </div>
      ${job.description ? `<p style="font-size:0.85rem; color:var(--clr-muted); line-height:1.6">${escHtml(job.description.slice(0,140))}…</p>` : ""}
      <div class="badge-area" style="margin-top:0.5rem">
        ${(job.matched_skills || []).slice(0,4).map(s => `<span class="badge badge-skill" style="font-size:0.72rem"><span class="badge-dot" aria-hidden="true"></span>${escHtml(s)}</span>`).join("")}
      </div>
    `;
    jobsGrid.appendChild(card);
  });

  // ── Courses ───────────────────────────────────────────────
  const coursesGrid = document.getElementById("courses-grid");
  coursesGrid.innerHTML = "";
  (analysis.recommended_courses || []).forEach(course => {
    const card = document.createElement("article");
    card.className = "course-card";
    card.setAttribute("role", "listitem");
    card.setAttribute("aria-label", `Course: ${course.title}`);

    const isFree = (course.cost || "").toLowerCase() === "free";
    card.innerHTML = `
      <div class="course-platform">${escHtml(course.platform || "Online")}</div>
      <h3 class="course-title">${escHtml(course.title)}</h3>
      <p class="course-desc">${escHtml(course.description || "")}</p>
      <div class="course-footer">
        <div>
          <div class="course-meta">⏱ ${course.duration_hours || "?"} hours · ${escHtml(course.format || "")}</div>
          <div class="course-meta">${(course.language || []).join(", ")}</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:0.4rem">
          <span class="course-cost ${isFree ? "" : "paid"}">${isFree ? "🎁 Free" : "💳 " + escHtml(course.cost)}</span>
          ${course.certificate ? '<span style="font-size:0.75rem; color:var(--clr-gold)">🏅 Certificate</span>' : ""}
        </div>
      </div>
      ${course.url ? `<a href="${escHtml(course.url)}" target="_blank" rel="noopener" class="course-link" style="margin-top:0.75rem">Enrol Now →</a>` : ""}
    `;
    coursesGrid.appendChild(card);
  });
}

// ---------------------------------------------------------------------------
// HTML escaping
// ---------------------------------------------------------------------------
function escHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------------
// Load stats on startup
// ---------------------------------------------------------------------------
async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/api/db/stats`);
    if (!res.ok) return;
    const stats = await res.json();

    const workerEl = document.getElementById("stat-workers");
    const jobsEl   = document.getElementById("stat-jobs");
    const stateEl  = document.getElementById("stat-states");

    if (workerEl && stats.workers_registered) {
      workerEl.textContent = (stats.workers_registered / 1000).toFixed(0) + "K+";
    }
    if (jobsEl && stats.jobs_matched) {
      jobsEl.textContent = (stats.jobs_matched / 1000).toFixed(0) + "K+";
    }
    if (stateEl && stats.states_covered) {
      stateEl.textContent = stats.states_covered;
    }
  } catch (_) {
    // silently fail
  }
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
  loadStats();

  // Pre-warm voices list for TTS
  if (window.speechSynthesis) {
    speechSynthesis.getVoices();
    speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
  }

  // Keyboard shortcut: Space to toggle mic when not in a text field
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space" && document.activeElement === document.body) {
      e.preventDefault();
      micBtn.click();
    }
  });

  console.log(
    "%c🎙 Livelihood Assistant\n%cPowered by Gemma 4 – Built for informal workers of India 🇮🇳",
    "color:#6c63ff; font-size:18px; font-weight:bold;",
    "color:#8892a4; font-size:13px;"
  );
});
