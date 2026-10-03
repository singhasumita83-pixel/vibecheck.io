# VibeCheck

> **Your app works. Does it make sense?**  
> Upload a screenshot or a GitHub repo URL. VibeCheck finds what a first-time user would trip over, explains why, and writes the fix — powered entirely by open-weight models.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-vibecheck--io.vercel.app-E5391C?style=flat-square)](https://vibecheck-io.vercel.app)
[![Model](https://img.shields.io/badge/AI-Open--Weight%20Only-14130F?style=flat-square)](MODELS.md)
[![Tests](https://img.shields.io/badge/Tests-42%20passing-22c55e?style=flat-square)](#-testing)
[![License](https://img.shields.io/badge/License-MIT-5F5B50?style=flat-square)](LICENSE)

---

## What is VibeCheck?

VibeCheck is an AI-powered UX auditor. It looks at your UI the way a senior designer would: methodically, critically, and with specific recommendations.

- **Screenshot mode** — Upload any screenshot. Get numbered annotation pins overlaid on the image, margin-note–style finding cards, measured WCAG contrast ratios, and a one-click fix prompt for coding tools.
- **Repo mode** — Paste a GitHub URL. VibeCheck shallow-clones it, reads your UI source files, and produces real unified diffs you can apply with `git apply`.
- **CLI** — Run the auditor locally in a terminal or inside GitHub Actions, with structured table output and a configurable exit code.
- **Re-check delta** — After fixing issues, upload the improved screenshot. VibeCheck compares the two runs and shows you exactly what was fixed, what's new, and how category scores changed.

---

## 🖋 Design Philosophy: The Senior Designer's Red Pen

VibeCheck is styled like a proof sheet that's been marked up — warm paper, black ink, one red pen.

| Design choice | Rationale |
|---|---|
| One accent color `#E5391C` | Used only for critical/high issues and primary actions — so red always means *look here* |
| Shape + word severity | ■ Critical · ● High · ◐ Medium · ○ Low — color is never the only indicator |
| Editorial typography | *Instrument Serif* for headings, *Instrument Sans* for body, *JetBrains Mono* for evidence |
| Evidence in monospace | Ratios, line numbers, file paths formatted like receipts — proof over opinion |

---

## ⚡ Features

### 1 · Screenshot Mode — Annotated Proof Sheet

- **Live overlay pins** — Numbered stamps placed directly over friction points on the image
- **Synchronized finding cards** — Click a pin → card highlights; click a card → pin pulses with a red bounding box
- **Measured WCAG contrast** — Sampled pixel colors, actual `2.3:1` ratio, suggested accessible color
- **Honest scoring** — Category scores (Usability, Accessibility, Visual Hierarchy, Navigation, Forms…) shown with a thin bar and marked *AI heuristic indicators*
- **One-click fix prompt** — Ready to hand to Cursor, Lovable, Bolt, v0, or Claude Code
- **Markdown report export** — Download a full `.md` report of every finding

### 2 · Repo Mode — GitHub Link → Code Diff

- **Zero code execution** — Shallow `--depth 1` read-only clone; never runs build scripts
- **Smart file selection** — Prioritizes `.html`, `.css`, `.jsx`, `.tsx`, `.vue`, `.svelte`, capped at 25 files
- **Real git diffs** — `+`/`-` annotations, line numbers, `@@` hunks
- **Verified patches** — Validates that patches apply cleanly; export as `.patch` or `.zip`
- **File tree panel** — Click any file to filter findings to that file

### 3 · Dismiss / Ignore List

- Mark any finding as **"Not an issue"** — it disappears from the list and the overlay
- Dismissed IDs are stored in `localStorage` so they persist across page loads
- Ignored count shown in the summary bar; click to see the list

### 4 · Re-check After Fixing — Before/After Delta

After receiving a report, click **"⟳ Re-check after fixing"** in the summary bar:

1. A file picker opens — upload your improved screenshot
2. VibeCheck runs a fresh analysis on the new image
3. Findings are matched between runs (IoU > 0.3 on bounding boxes **or** title Jaccard > 0.5 on tokens)
4. An **improvement banner** appears at the top of the new report:

   ```
   ✅ 7 of 12 fixed, 2 new, 5 remaining
   Accessibility: 54 → 78 (+24)   Visual Hierarchy: 61 → 61 (0)
   ```

5. Contrast deltas shown for matched findings: `2.3:1 → 4.8:1`

### 5 · CLI + GitHub Actions

Run VibeCheck without a web server — directly from the terminal or inside CI.

---

## 🖥 Command-Line Interface

```bash
# Audit a screenshot and print a compact table
python cli.py ui.png

# Exit 1 if any High or above findings are found
python cli.py ui.png --fail-on high

# Write a Markdown report to disk
python cli.py ui.png --md report.md

# Pipe raw JSON
python cli.py ui.png --json | jq .summary

# Add persona and goal context
python cli.py checkout.png --persona "first-time buyer" --goal "complete purchase" --fail-on high
```

**Output example**

```
#     Sev       Category              Title                                         Location
----  --------  --------------------  --------------------------------------------  ----------------------------
1     ■ Critical  Accessibility         CTA button contrast ratio 2.3:1               x=48% y=61%
2     ● High    Visual Hierarchy      No clear focal point above the fold            x=50% y=30%
3     ◐ Medium  Forms & Feedback      Password field lacks visible requirements      x=50% y=72%

3 issues  ■ 1 critical  ● 1 high  ◐ 1 medium  ○ 0 low
Scores  Accessibility: 48  ·  Visual Hierarchy: 67  ·  Forms & Feedback: 72
```

**Exit codes**

| Code | Meaning |
|------|---------|
| `0` | Success, no findings above threshold |
| `1` | Findings at or above `--fail-on` severity found |
| `2` | Input error (file missing, invalid image) |
| `3` | Model endpoint unreachable |

**Environment variables** (or `.env` file):

| Variable | Description |
|---|---|
| `LLM_BASE_URL` | Base URL of OpenAI-compatible endpoint |
| `LLM_API_KEY` | API key |
| `VLM_MODEL` | Vision model name |
| `VERIFIER_MODEL` | Critique/verifier model name |

---

## ⚙️ Use in CI — GitHub Actions

VibeCheck runs on every pull request via `.github/workflows/vibecheck.yml`.

### Quick setup

**1. Add a screenshot** to your repo at `docs/ui-screenshot.png`

**2. Set repository secrets** *(Settings → Secrets and variables → Actions)*

| Secret | Value |
|---|---|
| `LLM_BASE_URL` | e.g. `https://api.together.xyz/v1` |
| `LLM_API_KEY` | API key for your endpoint |

> **A hosted open-weight endpoint is required for CI.** Free-tier providers that work well:
> - [Together AI](https://www.together.ai/) — `Qwen/Qwen2-VL-72B-Instruct`
> - [Groq](https://groq.com/) — fast inference, generous free tier

**3. Set optional repository variables** *(Settings → Secrets and variables → Variables)*

| Variable | Default |
|---|---|
| `VLM_MODEL` | `Qwen/Qwen2-VL-72B-Instruct` |
| `VERIFIER_MODEL` | `Qwen/Qwen2.5-72B-Instruct` |
| `VIBECHECK_SCREENSHOT` | `docs/ui-screenshot.png` |
| `VIBECHECK_FAIL_ON` | `high` |

### What happens on each PR

```
✓ Checkout repo
✓ Set up Python 3.11
✓ Install requirements
✓ Run VibeCheck audit  →  vibecheck-report.md
✓ Publish report to GitHub Step Summary
✓ Upload report as artifact
✗ Fail job  (only if findings ≥ VIBECHECK_FAIL_ON)
```

If the screenshot is not present the step prints a notice and skips gracefully — no false failures.

---

## 🛠 Local Setup

### 1 · Clone

```bash
git clone https://github.com/singhasumita83-pixel/vibecheck.io.git
cd vibecheck.io
```

### 2 · Install dependencies

```bash
pip install -r requirements.txt
```

### 3 · Configure environment

```bash
cp .env.example .env
```

```env
# Hosted open-weight endpoint (Together AI, Groq, Fireworks, DeepInfra…)
LLM_BASE_URL=https://api.together.xyz/v1
LLM_API_KEY=your_key_here
VLM_MODEL=Qwen/Qwen2-VL-72B-Instruct
VERIFIER_MODEL=Qwen/Qwen2.5-72B-Instruct

# --- OR local Ollama (100% offline) ---
# LLM_BASE_URL=http://localhost:11434/v1
# LLM_API_KEY=ollama
# VLM_MODEL=qwen2.5-vl:7b
```

### 4 · Run

```bash
python app.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific suites
python -m pytest tests/test_compare.py    # matching engine + delta logic (23 tests)
python -m pytest tests/test_cli.py        # CLI arg parsing + exit codes (19 tests)
python -m pytest tests/test_contrast.py  # WCAG contrast measurement
```

**42 tests, all passing.** Tests use only the stdlib + pytest — no network calls, no real images.

---

## 🚀 Deploying to Vercel

VibeCheck is pre-configured for Vercel Serverless via `vercel.json` and `api/index.py`:

1. Import `singhasumita83-pixel/vibecheck.io` on [Vercel](https://vercel.com/new)
2. Add environment variables (`LLM_BASE_URL`, `LLM_API_KEY`, `VLM_MODEL`, `VERIFIER_MODEL`)
3. Click **Deploy**

Live: **[https://vibecheck-io.vercel.app](https://vibecheck-io.vercel.app)**

---

## 🔒 Security & Privacy

| Concern | How it's handled |
|---|---|
| Repo code execution | Never — shallow clone, read-only, no `npm install` / build |
| Uploaded images | Held in memory only; never written to disk |
| Secrets | Never logged or committed; loaded from env at runtime |
| SSRF | Model base URLs validated against an allowlist |
| Rate limiting | 10 requests/minute per IP via Flask-Limiter |

---

## 📁 Project Structure

```
vibecheck.io/
├── app.py                   # Flask app + all API routes
├── cli.py                   # Command-line interface (Feature 5)
├── analyzer/
│   ├── pipeline.py          # Screenshot analysis pipeline
│   ├── compare.py           # Before/after delta engine (Feature 4)
│   ├── contrast.py          # WCAG 2.1 contrast measurement (Feature 2)
│   ├── report_md.py         # Markdown report builder (Feature 1)
│   ├── repo_scan.py         # Repo mode: static UI analysis
│   ├── repo_fix.py          # Repo mode: diff generation
│   ├── repo_ingest.py       # GitHub clone + file selection
│   ├── llm_client.py        # OpenAI-compatible LLM wrapper
│   ├── scoring.py           # Category scoring + severity ranking
│   └── schema.py            # Pydantic models
├── static/
│   ├── js/
│   │   ├── app.js           # Main app state machine
│   │   └── report.js        # Report rendering + interactions
│   └── css/
├── templates/index.html     # Single-page app shell
├── tests/                   # 42 unit tests
├── .github/workflows/
│   └── vibecheck.yml        # GitHub Actions CI workflow (Feature 5)
└── vercel.json              # Vercel serverless config
```

---

## 📜 License

MIT License. See [MODELS.md](MODELS.md) for open-weight model attribution and licenses.
