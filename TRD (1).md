# VibeCheck UI: Technical Requirements Document

**Companion to:** PRD.md
**Target:** 6-hour hackathon MVP, with a clear path to stretch features.
**Track constraint:** all AI inference uses open-source or open-weight models (MLH+DEV open-source AI track).

---

## 1. Architecture overview

```text
Browser (HTML/CSS/JS)
   │  POST /api/analyze  (image, persona, goal)
   ▼
Flask API
   ├─ [URL mode] capture()     Playwright: desktop + mobile screenshots
   ├─ validate_upload()        size, type, resize to MAX_IMAGE_PX
   ├─ [URL mode] measured_checks()   axe-core + DOM metrics
   ├─ pass_1_analyze()         open-weight VLM → candidate findings (JSON)
   ├─ pass_2_verify()          open model → keep / merge / drop, adjust severity
   ├─ score_and_rank()         deterministic Python
   └─ build_fix_prompt()       LLM or template → plain-text prompt
   ▼
JSON response → frontend renders overlay, cards, summary
```

Design principle: **model for judgment, code for measurement and math.** Every model is open-weight and reached through one OpenAI-compatible client, so the provider (local or hosted) is a configuration choice.

## 2. Tech stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Vanilla HTML/CSS/JS + Tailwind (CDN) | No build step, fast to iterate |
| Backend | Python 3.11 + Flask | Simple, team already knows it |
| AI | Open-weight vision-language model (Qwen-VL family primary candidate) | Meets the open-source AI track; strong UI understanding and box grounding |
| Serving | Ollama (local) or a hosted open-weight endpoint | Local privacy mode plus fast live demo |
| Model client | OpenAI-compatible client library, pointed at the endpoints above | One code path for local and hosted; the library is only a client, the models are open |
| Image handling | Pillow | Resize and normalize uploads |
| Validation | Pydantic | Enforce the finding schema |
| URL mode | Playwright (Python), axe-core | URL capture and measured checks (now in MVP, with a scope guard) |
| Hosting | Flask app local or on Render/Railway; models on local Ollama and a hosted open-weight endpoint | Speed for the demo with a local fallback |

## 2.1 Open-weight model strategy

### Roles

| Role | Primary choice | Alternatives | Notes |
|---|---|---|---|
| Vision analysis (Pass 1) | Qwen-VL family (Qwen2.5-VL or newer); 7B-class locally, larger when hosted | Gemma 3 vision, Llama vision models, Pixtral, InternVL, MiniCPM-V | Native bounding-box grounding is the reason it leads |
| Verifier (Pass 2) | Same VLM when box tightening matters; a text-only open model for dedupe, merge and severity only | Any strong open instruct model | Text-only is cheaper and faster |
| Fix Prompt | Deterministic template first | Optional open text model to polish wording | Template is the fallback so this never fails |

Exact model tags depend on what Ollama and your hosting provider currently offer. In hour 1, run two candidates on the demo screenshot and choose by JSON validity rate, marker accuracy and number of wrong findings. Record the choice in `MODELS.md`.

### Serving modes

| Mode | Setup | Use |
|---|---|---|
| Local | `ollama pull <vlm-tag>`, endpoint `http://localhost:11434/v1` | Privacy demo, offline fallback |
| Hosted | OpenAI-compatible endpoint from a provider serving open-weight models (Together, Fireworks, Groq, OpenRouter, Hugging Face Inference) | Live demo speed |

Both modes use the same `llm_client.py`; only `LLM_BASE_URL`, `LLM_API_KEY` and model names change.

### Structured output
Use schema-constrained decoding where the backend supports it (Ollama `format` with a JSON schema, vLLM guided JSON, or a provider's `response_format`). Where it doesn't, fall back to prompt-only JSON plus the Pydantic retry in section 6. Small open models need this more than large closed ones.

### Coordinate handling
Grounding conventions differ between model versions (absolute pixels in the resized image versus a 0 to 1000 relative scale). Check the model card, set `COORD_CONVENTION`, and convert in one function, `to_normalized(box, convention, img_w, img_h)`, with a unit test. All downstream code uses normalized 0 to 1 coordinates only.

### Transparency and licensing
Read each model's license before the demo. The report footer shows model name, license and where it ran. `MODELS.md` lists the same plus versions.

## 3. Repository layout

```text
vibecheck-ui/
├─ app.py                 Flask entry, routes
├─ analyzer/
│  ├─ pipeline.py         orchestrates passes
│  ├─ llm_client.py       OpenAI-compatible client, constrained JSON, fallback
│  ├─ capture.py          [URL mode] Playwright screenshots
│  ├─ measured.py         [URL mode] axe-core + DOM checks
│  ├─ coords.py           to_normalized() + tests
│  ├─ prompts.py          system + user prompt templates
│  ├─ schema.py           Pydantic models
│  ├─ scoring.py          score + rank
│  └─ fixprompt.py        Fix Prompt builder
├─ static/
│  ├─ css/ js/ img/
│  └─ demo/               bad-app screenshot + cached result.json
├─ templates/index.html
├─ MODELS.md              models used, versions, licenses, local/hosted setup
├─ requirements.txt
├─ .env.example           API key placeholder
└─ README.md
```

## 4. API specification

### `POST /api/analyze`

`multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `image` | file | yes, unless `url` is given | PNG/JPG, ≤ 5 MB |
| `persona` | string | no | e.g. "first-time college student" |
| `goal` | string | no | e.g. "create an account" |
| `viewport` | string | no | `desktop` or `mobile` hint |
| `url` | string | no | URL mode: if present, `image` is optional and measured checks run |

**200 response**

```json
{
  "run_id": "uuid",
  "model": { "name": "<model-tag>", "license": "<license>", "served_by": "local|hosted" },
  "image": { "width": 1440, "height": 900 },
  "summary": {
    "counts": { "critical": 1, "high": 4, "medium": 7, "low": 3 },
    "scores": {
      "Usability": 68, "Visual Hierarchy": 61, "Accessibility": 54,
      "Navigation": 72, "Forms & Feedback": 66
    },
    "disclaimer": "AI heuristic indicators, not validated UX metrics."
  },
  "findings": [ /* Finding[] */ ],
  "fix_plan": [
    { "priority": 1, "title": "Increase CTA prominence", "finding_ids": ["f1", "f4"] }
  ],
  "fix_prompt": "Improve this app's UI. 1) ..."
}
```

**Errors:** `400` bad input, `413` too large, `422` model returned invalid output after retry, `502` upstream AI failure, each as `{ "error": "message", "retryable": true|false }`.

### `GET /api/demo`
Returns the cached demo result instantly (demo-day safety net).

## 5. Finding schema

```json
{
  "id": "f1",
  "title": "Primary CTA lacks visual prominence",
  "category": "Visual Hierarchy",
  "severity": "High",
  "confidence": 0.82,
  "heuristic": "Nielsen #4 Consistency and standards",
  "location": { "x": 0.42, "y": 0.71, "w": 0.18, "h": 0.07 },
  "problem": "The Submit button uses the same gray as secondary actions.",
  "impact": "New users may hesitate or miss the next step.",
  "solution": "Use a filled high-contrast primary style and place it directly below the form.",
  "evidence": "Button fill and page background are similar in luminance.",
  "source": "llm"
}
```

Rules:
- `location` is normalized to image size (0 to 1). `x,y` is the top-left corner of the box.
- `severity` ∈ {Critical, High, Medium, Low}.
- `source` ∈ {`llm`, `measured`}. Measured findings (stretch) always include numeric evidence.
- Findings with `confidence < 0.5` are dropped.

## 6. AI pipeline

### Pass 1: Analyze
- Input: resized image, persona, goal, taxonomy, schema.
- System prompt sets role: *senior UX auditor evaluating from the perspective of the given persona*.
- Required: cite a heuristic, give a bounding box, give concrete evidence visible in the image, no generic advice.
- Output: JSON array only. Target 8 to 15 candidates. Small open models over-produce and drift, so keep the prompt short, the schema explicit, and include one worked example of a good finding.

### Pass 2: Verify
- Input: image + candidate JSON.
- Task: remove vague, duplicate or unsupported items; merge overlapping ones; correct severity; tighten boxes; keep the original schema.
- This single pass is the biggest quality gain per hour spent.
- A text-only verifier can dedupe, merge and re-rank but cannot tighten boxes; use the VLM when box accuracy matters.
- In URL mode, measured findings are passed in as ground truth the verifier must not drop.

### Fix prompt
Built from the top 5 to 7 findings using a template:

```text
You are improving the UI of an existing app. Make these changes without
breaking functionality:
1. [title]: [solution]  (where: [plain-language location])
...
Keep the current tech stack and component structure. After changes,
list what you changed.
```

### Robustness
- Prefer schema-constrained decoding (section 2.1); otherwise ask for JSON only and strip code fences before parsing.
- Validate with Pydantic; on failure, retry once with the validation error appended.
- Temperature low (≈0.2) for consistency.
- Timeout 60s per call (hosted) or 120s (local); return `502` with `retryable: true` on failure.
- Provider fallback: if the hosted endpoint fails, retry once on local Ollama if available; for the demo screenshot only, fall back to `/api/demo`.
- Open VLMs have their own visual-token budgets: keep the image cap configurable (`MAX_IMAGE_PX`, default 1568) and lower it for local runs.

## 7. Scoring logic (`scoring.py`)

```python
WEIGHTS = {"Critical": 25, "High": 15, "Medium": 8, "Low": 3}

def category_score(findings):
    penalty = sum(WEIGHTS[f.severity] * f.confidence for f in findings)
    return max(0, round(100 - penalty))
```

Sort order: severity rank, then confidence descending.

## 8. Measured checks (`measured_checks`), in MVP for URL mode

Run in Playwright against a URL:
- **axe-core** injection for WCAG violations (contrast, labels, alt text, ARIA).
- **Tap targets:** flag interactive elements smaller than 44×44 CSS px on a 390px viewport.
- **Overflow:** `document.documentElement.scrollWidth > innerWidth` at mobile width.
- **Contrast:** computed from element color and background where axe can't resolve it.
- Convert each result to a Finding with `source: "measured"` and pixel boxes normalized to the screenshot.
- Merge with LLM findings; if both flag the same region, keep one and mark it "confirmed by measurement" (confidence boost).

Scope guard: if this is not working by the end of hour 4, ship screenshot-only mode and make this the first post-hackathon item. Measured checks need a live DOM, so they never run on uploaded screenshots.

## 9. Frontend requirements

- Single page with three states: **Upload → Analyzing → Report**.
- Overlay: image container with `position: relative`; markers absolutely positioned using percentage `left/top` from normalized coordinates, so it scales responsively.
- Marker click: opens/scrolls to the issue card and highlights the box.
- Severity filter chips and category filter.
- "Copy Fix Prompt" uses `navigator.clipboard` with a fallback textarea.
- No framework required; keep JS in modules (`upload.js`, `report.js`, `overlay.js`).
- Input screen has two tabs: screenshot upload and URL field.
- Report footer shows model name, license, and where inference ran (local or hosted).

## 10. Security and privacy

- API key only in environment variables, never sent to the client.
- Validate MIME type server-side by inspecting the image with Pillow, not only the extension.
- Cap upload size and dimensions; resize before sending to the model.
- Do not persist uploads; process in memory and discard. In local mode nothing leaves the machine; say so in the UI.
- Rate limit `/api/analyze` (e.g. 10/min per IP with Flask-Limiter) to protect API credits.
- Warn users not to upload screenshots containing real personal data.
- URL mode: allow only http(s), block private and internal IP ranges (SSRF), set a navigation timeout, and run Playwright with no credentials or saved sessions.

## 11. Performance targets

| Step | Budget |
|---|---|
| Upload + resize | < 1 s |
| Pass 1 | 12 to 20 s |
| Pass 2 | 8 to 15 s |
| Total | < 45 s |

Budgets assume hosted open-weight inference. A 7B-class VLM on a laptop can take 1 to 3 minutes, so use local mode for the privacy demo with a cached result ready and run the live demo on hosted inference.

Mitigation: stream progress stages to the UI (SSE or polling), and keep a cached demo result.

## 12. Testing

- **Schema tests:** feed malformed model output, confirm retry and clean error.
- **Scoring tests:** known findings give expected scores.
- **Coordinate test:** unit-test `to_normalized` with known boxes for each supported convention.
- **Model bake-off (hour 1):** run two candidate open models on the demo screenshot; compare JSON validity, marker accuracy and wrong findings; record the winner in `MODELS.md`.
- **Manual QA:** 3 screenshots (bad app, decent app, mobile layout); check markers land correctly.
- **Dry run:** full demo three times on the venue network, offline fallback via `/api/demo`.

## 13. Build plan mapped to 6 hours

| Hour | Deliverable |
|---|---|
| 1 | Flask skeleton, upload UI, demo screenshot, **model bake-off (Ollama or hosted), pick the model** |
| 2 | `llm_client` + `/api/analyze` Pass 1 with constrained JSON; coordinate normalization |
| 3 | Pydantic validation, Pass 2 verifier, scoring |
| 4 | Report UI, cards, overlay markers; **URL mode (capture + axe-core), scope-guarded** |
| 5 | Fix plan, Fix Prompt, model footer, `MODELS.md`, cached demo |
| 6 | Polish, error states, rehearsal, README, slides |

Suggested split for a team: one person on backend pipeline, one on frontend report/overlay, one on demo app, prompts and slides.

## 14. Environment

```text
LLM_BASE_URL=http://localhost:11434/v1   # Ollama, or a hosted open-weight endpoint
LLM_API_KEY=ollama                       # real key when hosted; any string for Ollama
VLM_MODEL=<vision model tag>             # chosen in the hour-1 bake-off
VERIFIER_MODEL=<model tag>               # may equal VLM_MODEL
COORD_CONVENTION=<abs_pixels|rel_1000>   # per the model card
MAX_UPLOAD_MB=5
MAX_IMAGE_PX=1568
```

`requirements.txt`: `flask`, `pillow`, `pydantic`, `python-dotenv`, `flask-limiter`, `openai` (client library only, used against Ollama or any OpenAI-compatible open-weight host), `playwright` (URL mode).

Local setup: install Ollama, then `ollama pull <vlm-tag>`.

## 15. Track compliance checklist

- No closed-model API calls anywhere in the code; search the repo for other providers' SDKs and keys before submitting.
- `MODELS.md` and README name each model, version, license, and how to run it locally and hosted.
- Public repo with an open-source license (MIT or Apache-2.0).
- Report footer shows the model in use; the demo shows it too.
- Confirm the track's exact rules and submission requirements on the hackathon page.
