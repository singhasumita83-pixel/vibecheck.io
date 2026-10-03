# VibeCheck UI 🔍

> **Your AI UX tester for vibe-coded apps.**  
> Find friction before your users do. Get measured, evidence-backed fixes and copy-paste prompts for Cursor, Lovable, Bolt, v0, and Claude Code.

[![Track](https://img.shields.io/badge/Track-Open--Weight%20AI-6D4AFF)](MODELS.md)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## ⚡ The Problem

Vibe-coding tools let anyone ship working web apps in a weekend. But while the app *works*, it's often hard to *use*:
- Low contrast text that fails WCAG accessibility
- Buried or weakly styled primary CTAs
- Confusing navigation without active anchors
- Vague error states ("Invalid")
- Tiny, unclickable icon touch targets

Builders rarely have a design or QA team to critique their screens before launch.

## 🚀 The Solution: VibeCheck UI

VibeCheck UI evaluates your user interface the way a real user would:
1. **Interactive Visual Markers**: Every issue is pinned directly to its spot on the screenshot with normalized coordinates.
2. **Evidence-Backed Critiques**: Findings cite measured contrast, element sizes, and recognized Nielsen UX & WCAG heuristics.
3. **Honest Scoring**: Category scores are computed from issue counts and severity weights, clearly labeled as *"AI heuristic indicators"*.
4. **Fix Prompt Export**: Generates a prioritized, ready-to-paste prompt for your vibe-coding tool to fix all identified flaws in one go.
5. **Open-Weight & Local-First**: Built with open-weight models (Qwen-VL, Gemma) ensuring unreleased UIs remain private.

---

## 🛠 Quickstart

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/your-username/vibecheck-ui.git
cd vibecheck-ui
py -m pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

To run with **Google Gemma / GenAI**:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

To run with **Local Ollama** (offline, private):
```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
VLM_MODEL=qwen2.5-vl:7b
```

### 3. Run the Server

```bash
py app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser!

---

## 🎯 Testing the Planted Flaws Demo

Click the **"⚡ Try Demo"** button on the top right. It instantly loads the intentionally flawed sample dashboard ([/demo](http://127.0.0.1:5000/demo)) showcasing all 7 planted UX errors:
- Low-contrast gray-on-gray notice text (Accessibility)
- Faded primary CTA styled like secondary (Visual Hierarchy)
- 22px micro-buttons (Usability)
- Vague 'Invalid' banner (Forms & Feedback)
- 9-item flat navigation with cryptic 3-letter codes (Navigation)
- Dense wall of text without typography structure (Content & Copy)
- Fixed-width table causing mobile overflow (Responsive)

---

## 🐙 Feature: Repo Mode (GitHub Link → Code Findings → Unified Diffs)

Repo Mode closes the loop: **Screenshot mode** highlights *what's wrong on screen*; **Repo mode** pins *which file and line* and *how to change it* with verified unified diffs.

```text
POST /api/analyze-repo {repo_url, branch?, persona?, goal?, model?}
   ▼
Async Job Created → Client polls GET /api/jobs/<job_id>
   ▼
1. ingest      Validate github.com URL → shallow single-branch clone (read-only)
2. select      Select UI files (.html, .css, .jsx, .tsx, .vue, .svelte), max 25 files, 60KB cap
3. scan        10 static rules → candidates with file + line + snippet (no model cost)
4. review      Open-weight model evaluates code chunks → confirms, categorizes & rates
5. fix         Synthesizes minimal unified diff per confirmed finding
6. validate    Validates that diff applies cleanly against clean repo clone
7. verify      Deduplicates, scores, generates prioritized fix plan
8. package     Calculates category scores, exports .patch or .zip bundle
   ▼
Temp directory deleted immediately. Nothing persisted. Zero repo code execution.
```

### Repo Mode Highlights:
- **Zero Code Execution**: Static read-only analysis only. Never installs packages, executes build scripts, or runs unit tests.
- **Unified Diff Viewer**: Side-by-side or unified diff views with syntax-highlighted additions and removals.
- **Clean Git Patch**: Select desired fixes via checkboxes and download a `.patch` file apply-able via `git apply`.
- **Zip Bundle Export**: Download all selected fixes, fix prompt, and summary in a `.zip` archive.
- **Instant Demo**: Click **"⚡ Try Repo Demo"** to inspect precomputed results for a flawed sample repository in under 1 second.
- **BYO Model & SSRF Guardrails**: Supports custom open-weight endpoints (Groq, Together AI, OpenRouter, local Ollama) with strict hostname validation. Keys are held in memory for the job duration only.

---

## 🏗 Architecture & Tech Stack

```text
Browser (HTML5, Tailwind CDN, Vanilla JS)
   │  POST /api/analyze        │  POST /api/analyze-repo
   ▼                           ▼
Flask Core API            Async Job Worker (Background Thread)
   ├─ Vision Pipeline          ├─ RepoIngest (Shallow clone, UI file filtering)
   ├─ Image Calibration        ├─ RepoScanner (10 static heuristics)
   ├─ Mathematical Scoring     ├─ RepoFixer (Unified diff synthesis & validation)
   └─ Fix Prompt Generator     └─ RepoReviewer (Open-weight model code audit)
   ▼                           ▼
Interactive Annotations   File Tree + Diff Viewer + .patch / .zip Export
```

---

## 🧪 Testing Suite

Run all automated unit tests and probe suites:

```bash
# 1. Discover all unit tests (schemas, scoring, scanner, diffs, jobs API)
py -m unittest discover tests

# 2. Run API and analysis engine smoke tests
py test_app.py

# 3. Run Dynamic Operational Probe (DOP) on all screens & tabs
py run_dop.py
```

---

## 📜 License
MIT License. See [MODELS.md](MODELS.md) for open-weight model licenses and disclosures.

