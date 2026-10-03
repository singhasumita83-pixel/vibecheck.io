# VibeCheck UI: Model Disclosure & Configuration

VibeCheck UI is built in compliance with the **MLH + DEV Open-Source / Open-Weight AI Track**.
All artificial intelligence evaluations, vision analysis, and issue verification run exclusively on open-weight models or open endpoints. No closed-source proprietary APIs are required.

---

## 1. Supported Open-Weight Models

| Role | Primary Model | Alternative Candidates | License | Grounding Support |
|---|---|---|---|---|
| **Screenshot Vision Analysis** | `qwen2.5-vl:7b` / `gemma-4-26b-a4b-it` | `llama3.2-vision:11b`, `minicpm-v` | Apache 2.0 / Gemma Terms | Native 2D bounding-box coordinates & visual tokens |
| **Screenshot Issue Verifier** | `qwen2.5-vl:7b` / `qwen2.5:7b-instruct` | `mistral-nemo`, `gemma-2-9b-it` | Apache 2.0 | Schema-constrained JSON deduplication & severity ranking |
| **Repo Mode Code Reviewer** | `Qwen2.5-Coder-7B-Instruct` | `DeepSeek-Coder-V2-Lite`, `Llama-3.2-3B` | Apache 2.0 / Open-Weight | Line-level code parsing, heuristic citation & severity |
| **Repo Mode Unified Diff Fixes** | `Qwen2.5-Coder-7B-Instruct` | `DeepSeek-Coder-V2-Lite` | Apache 2.0 | Synthesizes verified unified diffs with git check |
| **Fix Prompt Synthesis** | Deterministic Template Engine | `qwen2.5:7b` | MIT / Apache 2.0 | Standardized tool-agnostic prompt generation |

---

## 2. Serving Environments

### Option A: Local-First Privacy Mode (Ollama)
In local mode, uploaded screenshots and repo code never leave your machine:

1. Install Ollama: [https://ollama.com](https://ollama.com)
2. Pull the vision & code models:
   ```bash
   ollama pull qwen2.5-vl:7b
   ollama pull qwen2.5-coder:7b
   ```
3. Set your environment in `.env`:
   ```env
   LLM_BASE_URL=http://localhost:11434/v1
   LLM_API_KEY=ollama
   VLM_MODEL=qwen2.5-vl:7b
   VERIFIER_MODEL=qwen2.5-vl:7b
   REPO_MODEL=qwen2.5-coder:7b
   COORD_CONVENTION=normalized
   ```

### Option B: Hosted Open-Weight Endpoints
For maximum inference speed without local GPU requirements:
- Use any OpenAI-compatible provider serving open-weight models (e.g. Together AI, Fireworks, Groq, OpenRouter).
- Set in `.env`:
  ```env
  LLM_BASE_URL=https://api.together.xyz/v1
  LLM_API_KEY=your_together_api_key
  VLM_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
  REPO_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct
  ```

### Option C: Google GenAI / Gemma Mode
Supports Gemma open models (`gemma-4-26b-a4b-it`) using the configured `GEMINI_API_KEY`.

### Option D: 100% Offline Local Engine (`USE_LOCAL_ENGINE=true`)
For instant test runs, demonstrations, and test cases without any external API or GPU dependencies:
```env
USE_LOCAL_ENGINE=true
```
Runs deterministic, image-aware heuristics and static source code scanners in ~30ms locally on Python.

---

## 3. Bring-Your-Own Model (BYO) & Security (Repo Mode)

Users can provide their own open-weight endpoint in Repo Mode via the custom model selector:
- `base_url`: OpenAI-compatible endpoint URL
- `model`: Open-weight model identifier
- `api_key`: Optional API key, **held in memory for the job only**, never logged or written to disk.

**SSRF Guardrails:** User-supplied `base_url` values are strictly validated against an allowlist of verified open-weight providers (`api.groq.com`, `openrouter.ai`, `api.together.xyz`, `api.fireworks.ai`, `api.deepinfra.com`) or `localhost` / `127.0.0.1` for local models. Private RFC1918 and internal cloud metadata IP addresses are strictly rejected.

---

## 4. Transparency & Compliance Guarantee

- **No closed-source models**: The pipeline does not require closed proprietary models.
- **Visible Disclosure**: The report footer explicitly communicates the exact model name, license, and execution locality (Local vs Hosted).

