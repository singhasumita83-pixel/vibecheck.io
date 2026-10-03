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

## 🔒 Security & Privacy

- **Read-Only Clones**: Shallow clones (`--depth 1`, `--no-recurse-submodules`) executed in disposable temporary directories.
- **Immediate Cleanup**: Cloned repositories and temporary files are wiped from disk immediately after scanning.
- **Zero Secret Retention**: Secrets and API tokens are never saved or committed.

---

## 📜 License
MIT License. See [MODELS.md](MODELS.md) for open-weight model disclosures.
