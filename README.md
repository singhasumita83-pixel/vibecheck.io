# VibeCheck

> **Your app works. Does it make sense?**  
> Upload a screenshot or a GitHub repo. VibeCheck marks what a first-time user would trip over, says why, and writes the fix.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-vibecheck--io.vercel.app-E5391C?style=flat-square)](https://vibecheck-io.vercel.app)
[![Track](https://img.shields.io/badge/AI-Open--Weights-14130F?style=flat-square)](MODELS.md)
[![License](https://img.shields.io/badge/License-MIT-5F5B50?style=flat-square)](LICENSE)

---

## 🖋 Concept: The Senior Designer's Red Pen

VibeCheck is built like a proof sheet a senior designer has marked up: warm paper, black ink, one red pen.

- **One accent color (`#E5391C`)**: Used exclusively for critical and high severity markings and primary actions.
- **Asymmetric, typographic layout**: Left-aligned, editorial typography with *Instrument Serif*, *Instrument Sans*, and *JetBrains Mono*.
- **Shape + word severity**: Critical (■), High (●), Medium (◐), and Low (○). Color is never the sole indicator.
- **Evidence in monospace**: Specific ratios, pixel measurements, file paths, and model names formatted like receipts.

---

## ⚡ Features

### 1. Screenshot Mode (The Proof Sheet)
- **Live Annotated Overlay**: Numbered stamp-in pins placed directly over visual friction points.
- **Synchronized Margin Notes**: Clicking a pin scrolls and highlights its corresponding finding; selecting a card draws an active red bounding box over the element.
- **Honest Indicators**: Category scores (Usability, Visual Hierarchy, Accessibility, Forms) with thin metric bars, clearly noted as *AI heuristic indicators*.
- **One-Click Fix Prompt**: Clean monospace prompt ready to hand to coding tools (Cursor, Lovable, Bolt, v0, Claude Code).

### 2. Repo Mode (GitHub Link → Code Diff Fixes)
- **Zero Code Execution**: Shallow, read-only clone of public GitHub repositories. Never executes build scripts, installs packages, or runs untrusted code.
- **Smart UI Selection**: Automatically selects and prioritizes UI source files (`.html`, `.css`, `.jsx`, `.tsx`, `.vue`, `.svelte`), capping at 25 files.
- **Unified Diff Engine**: Produces real git diffs with `+` and `-` annotations and line numbers.
- **Verified Patches**: Validates that patches apply cleanly and allows exporting custom selections as `.patch` files or bundled `.zip` archives.

---

## 🌐 Live Deployment

VibeCheck is deployed serverless on Vercel:
**[https://vibecheck-io.vercel.app](https://vibecheck-io.vercel.app)**

---

## 🛠 Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/singhasumita83-pixel/vibecheck.io.git
cd vibecheck.io
```

### 2. Install Dependencies
```bash
py -m pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your model keys:
```env
# Google GenAI / Gemini API key
GEMINI_API_KEY=your_api_key_here
USE_LOCAL_ENGINE=false

# Or local Ollama (100% offline & private)
# LLM_BASE_URL=http://localhost:11434/v1
# LLM_API_KEY=ollama
# VLM_MODEL=qwen2.5-vl:7b
```

### 4. Run the Application
```bash
py app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 🚀 Deploying to Vercel

VibeCheck is pre-configured for Vercel Serverless deployment using `vercel.json` and `api/index.py`:

1. Import `singhasumita83-pixel/vibecheck.io` on [Vercel](https://vercel.com/new).
2. Set Environment Variables:
   - `GEMINI_API_KEY`: your API key
   - `USE_LOCAL_ENGINE`: `false`
3. Click **Deploy**.

---

## 🖥 Command-Line Interface (CLI)

VibeCheck ships a standalone CLI that calls the analyzer pipeline directly — no web server needed.

```bash
# Audit a screenshot and print a table
py cli.py ui.png

# Fail CI if any High or above issues are found
py cli.py ui.png --fail-on high

# Write a Markdown report
py cli.py ui.png --md report.md

# Get raw JSON for piping
py cli.py ui.png --json | jq .summary

# With persona / goal context
py cli.py checkout.png --persona "first-time buyer" --goal "complete purchase" --fail-on high
```

**Exit codes**

| Code | Meaning |
|------|---------|
| `0`  | Analysis succeeded, no findings above threshold |
| `1`  | Analysis succeeded, findings at/above `--fail-on` threshold |
| `2`  | Input error (file not found, invalid image) |
| `3`  | Unreachable model endpoint |

---

## 🔄 Re-check After Fixing (Before/After Delta)

After receiving a report in the UI, click **"⟳ Re-check after fixing"** in the summary bar. Upload your improved screenshot — VibeCheck will:

1. Run a fresh analysis on the new screenshot.
2. Match findings between runs (IoU > 0.3 on bounding boxes or title Jaccard > 0.5).
3. Show an **improvement banner**: `7 of 12 fixed, 2 new, 5 remaining`.
4. Display per-category score changes: `Accessibility 54 → 78 (+24)`.
5. Show contrast measurement deltas for matched findings: `2.3:1 → 4.8:1`.

---

## ⚙️ Use in CI (GitHub Actions)

VibeCheck integrates into your pull request workflow via `.github/workflows/vibecheck.yml`.

### Setup

1. **Add a screenshot** at `docs/ui-screenshot.png` (or configure a different path via the `VIBECHECK_SCREENSHOT` repository variable).

2. **Set repository secrets** in *Settings → Secrets and variables → Actions*:
   - `LLM_BASE_URL` – Base URL of your hosted open-weight model endpoint (e.g. `https://api.together.xyz/v1`)
   - `LLM_API_KEY` – API key for the endpoint

   > **Note:** A hosted open-weight endpoint is required for CI because the model runs server-side. Free-tier providers like [Together AI](https://www.together.ai/) and [Groq](https://groq.com/) work well with `Qwen2-VL-72B-Instruct`.

3. **Set optional repository variables** in *Settings → Secrets and variables → Variables*:
   - `VLM_MODEL` – Vision model (default: `Qwen/Qwen2-VL-72B-Instruct`)
   - `VERIFIER_MODEL` – Verifier model (default: `Qwen/Qwen2.5-72B-Instruct`)
   - `VIBECHECK_SCREENSHOT` – Screenshot path (default: `docs/ui-screenshot.png`)
   - `VIBECHECK_FAIL_ON` – Severity threshold (default: `high`)

### What happens on each PR

- Checks out the repo and installs dependencies.
- Skips with a notice if the screenshot is missing.
- Runs `cli.py` and writes a Markdown report.
- Publishes the report to the **GitHub Step Summary** (visible in the Actions run).
- Uploads the report as a downloadable artifact.
- **Fails the job** only if findings at or above the threshold are found.

---

## 🔒 Security & Privacy

- **Read-Only Clones**: Shallow clones (`--depth 1`, `--no-recurse-submodules`) executed in disposable temporary directories.
- **Immediate Cleanup**: Cloned repositories and temporary files are wiped from disk immediately after scanning.
- **Zero Secret Retention**: Secrets and API tokens are never saved or committed.

---

## 📜 License
MIT License. See [MODELS.md](MODELS.md) for open-weight model disclosures.
