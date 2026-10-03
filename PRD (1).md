# VibeCheck UI: Product Requirements Document

**Tagline:** Your AI UX tester for vibe-coded apps.
**Type:** Hackathon MVP (6-hour build)
**Status:** Draft v1.1 (updated for the open-source / open-weight AI track)
**Track:** Build an original project that uses open-source or open-weight AI (MLH+DEV)

---

## 1. Problem

Vibe-coding tools (Cursor, Lovable, Bolt, v0, Claude Code) let anyone ship a working app in hours. The result usually *works* but is often hard to *use*: weak hierarchy, low contrast, broken mobile layouts, unclear errors, buried CTAs.

The builders are fast, but they rarely have a designer, a QA team, or real users to test with. They find out about UX problems only after launch.

## 2. Solution

VibeCheck UI takes a live URL or screenshots, evaluates the app the way a real user would, and returns:

1. **Pain points**, each pinned to a spot on the screenshot.
2. **Evidence** for every finding (measured contrast, tap-target size, DOM facts), so findings aren't just LLM opinion.
3. **Fixes** the developer can apply immediately, including a **copy-paste "Fix Prompt"** for their vibe-coding tool.

## 2.1 Track alignment: open-source / open-weight AI

- **Open models only.** All AI inference uses open-weight models: a vision-language model (primary candidate: the Qwen-VL family) for screenshot analysis, and an open text or vision model for verification. No closed-model API anywhere in the pipeline.
- **Model-agnostic.** The app talks to any OpenAI-compatible endpoint, so it runs on a local Ollama install or a hosted open-weight provider by changing environment variables only.
- **Local-first privacy story.** Developers often test unreleased UIs. In local mode, screenshots never leave their machine, which is a real reason to prefer open-weight AI here and not just a checkbox.
- **Visible disclosure.** The report footer and README name the model, its license, and where it ran (local or hosted).
- **Original work.** This is not a thin wrapper around a model. The hybrid pipeline (measured checks + vision model + verifier) and the Fix Prompt export are the original contributions.

## 3. What makes this better than "ask an LLM about my screenshot"

| Upgrade | Why it matters |
|---|---|
| **Hybrid analysis** (deterministic checks + open-weight vision model) | Contrast, tap-target size, missing labels and overflow are *measured*, not guessed. The LLM handles judgment calls (hierarchy, clarity, copy). |
| **Evidence-backed findings** | Each issue carries proof (e.g. "contrast 2.3:1, needs 4.5:1"). Judges and users trust it more. |
| **Verifier pass** | A second LLM pass discards vague, duplicate or unsupported findings, which cuts hallucinations. |
| **Persona + task simulation** | Analysis is framed by a target user and goal ("first-time college student trying to sign up"). |
| **Heuristic grounding** | Findings map to Nielsen's 10 heuristics and WCAG criteria, so they use recognized vocabulary. |
| **Fix Prompt export** | Output is directly usable inside the tool that created the app. This is the signature feature. |
| **Honest scoring** | Category scores are computed from issue counts and severity, and labelled "heuristic indicators", not fake precision. |
| **Open-weight, local-first** | Runs on open models you can host yourself, so unreleased UIs never go to a third-party API. Also qualifies for the open-source AI track. |

## 4. Target users

- **Primary:** solo builders and students shipping vibe-coded apps.
- **Secondary:** hackathon teams, indie hackers, small startups without a designer.

## 5. User stories

1. As a builder, I paste my app URL and get a prioritized list of UX problems in under a minute.
2. As a builder, I see markers on my screenshot so I know exactly *where* each problem is.
3. As a builder, I pick a target persona so feedback fits my real audience.
4. As a builder, I copy a ready-made prompt that tells my AI coding tool how to fix the top issues.
5. As a builder, I re-run the check after fixing and see improvement.

## 6. Scope

### MVP (must ship in 6 hours)
- **M1.** Input: screenshot upload (PNG/JPG) or app URL, plus optional persona and goal.
- **M2.** Vision analysis with an open-weight vision-language model returning schema-constrained JSON (issue, category, severity, location, impact, fix).
- **M3.** Overlay view: numbered markers on the screenshot, click to open the issue card.
- **M4.** Issue cards with severity badge, category, impact, solution, and evidence.
- **M5.** Summary: counts by severity, category heuristic scores, top-5 priority fix plan.
- **M6.** "Copy Fix Prompt" button.
- **M7.** One deliberately bad demo app plus a one-click "Try demo" button.
- **M8.** URL mode: Playwright captures desktop and mobile screenshots and runs measured checks (axe-core contrast and labels, tap-target size, mobile overflow). Measured findings are merged with model findings.
- **M9.** Model transparency: report footer shows model name, license, and where inference ran (local or hosted).
- **M10.** Model-agnostic config: provider and model are swapped through environment variables only.

**Priority if time slips:** M1 to M7 and M9 first, then M10, then M8. Screenshot-only mode is a complete product on its own.

### Stretch (only if time remains)
- **S1.** Side-by-side model comparison: run two open models on the same screenshot and show the difference.
- **S3.** Before/after comparison of two runs.
- **S4.** Guided journey test (sign up / find product) with step-by-step screenshots.
- **S5.** PDF/Markdown report export.

### Out of scope
Accounts and auth, saved history in a database, real user analytics, scientifically validated UX scores, native mobile app analysis.

## 7. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | Accept PNG/JPG up to 5 MB; reject others with a clear message. |
| FR-2 | Show an image preview before analysis. |
| FR-3 | Return findings as validated JSON; invalid output triggers one automatic retry. |
| FR-4 | Every finding includes: `id`, `title`, `category`, `severity`, `location`, `problem`, `impact`, `solution`, `confidence`, `heuristic`. |
| FR-5 | Location uses normalized coordinates (0 to 1) so markers scale with the image. |
| FR-6 | Findings are sorted by severity, then confidence. |
| FR-7 | Fix Prompt covers the top issues and is plain text, tool-agnostic. |
| FR-8 | Loading state with progress stages (Reading UI, Finding issues, Verifying, Writing fixes). |
| FR-9 | Graceful failure: API error shows a retry button, never a blank page. |
| FR-10 | Provider and model are set only through environment variables; swapping models needs no code change. |
| FR-11 | Report footer shows model name, license, and where inference ran (local or hosted). |
| FR-12 | URL mode: measured findings carry numeric evidence and are tagged `source: measured`. |

## 8. Issue taxonomy

**Categories:** Usability, Visual Hierarchy, Accessibility, Navigation, Content & Copy, Forms & Feedback, Responsive.

**Severity:**

| Level | Meaning |
|---|---|
| Critical | Blocks a core task or excludes users |
| High | Causes major confusion or drop-off |
| Medium | Noticeable friction |
| Low | Polish |

## 9. Scoring (honest version)

Category score = `100 − Σ(severity weight × confidence)`, clamped to 0 to 100.
Weights: Critical 25, High 15, Medium 8, Low 3.
Displayed with the label **"AI heuristic indicator, not a validated UX metric."**

## 10. Success metrics (demo day)

- Analysis completes in **under 45 seconds** on hosted open-weight inference (local mode may take longer).
- The full pipeline runs with **open-weight models only**, shown both locally (Ollama) and through a hosted open-weight endpoint.
- Demo app yields **at least 10 relevant findings** with **zero obviously wrong ones**.
- Every marker lands on or near the correct UI element.
- The Fix Prompt, pasted into a coding tool, visibly improves the demo app (shown live or in a prepared before/after).

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Marker positions are inaccurate | Ask for coarse regions, snap to a grid, offer measured DOM boxes in stretch S2. |
| LLM invents issues | Verifier pass, confidence filter (drop below 0.5), evidence field. |
| API latency or rate limits | Pre-computed cached result for the demo app as a fallback. |
| Scope creep | MVP list is frozen; stretch items only after M1 to M7 work end to end. |
| Generic feedback | Persona and goal injected into the prompt; heuristics required per finding. |
| Open model is weaker than closed models at grounding and strict JSON | Schema-constrained decoding, verifier pass, measured checks as ground truth, a model with native box grounding (Qwen-VL), and an early model bake-off on the demo app. |
| Local inference too slow or too large for team laptops | Hosted open-weight endpoint for the live demo, local mode as the privacy story, cached demo result as fallback. |
| Model license limits the intended use | Read the license on the model card before the demo and display it in the UI. |

## 12. Demo script (3 minutes)

1. **Hook (20s):** "We all vibe-code now. Nobody tests the vibes." Show the bad app. Mention that the whole pipeline runs on open-weight models.
2. **Run (30s):** Upload, pick persona "first-time college student", click Analyze.
3. **Wow (60s):** Overlay appears; click 3 markers and read problem, impact and fix with evidence.
4. **Payoff (45s):** Click "Copy Fix Prompt", paste into the coding tool, show the improved app.
5. **Close (25s):** Re-run, show issue counts drop. Point at the footer (model name, license, running locally). Roadmap: guided journeys, CI integration.

## 13. Roadmap after the hackathon

Browser extension, GitHub Action that comments UX findings on PRs, multi-page journey testing, history and trends, team sharing.

## 14. Submission checklist (track)

- Public repository with an open-source license (MIT or Apache-2.0).
- README states which open-weight models are used, their licenses, and exact steps to run locally and hosted.
- `MODELS.md` lists models, versions, licenses and where they were run.
- No closed-model API calls anywhere in the code (search the repo before submitting).
- Demo video or live demo shows the model name and the open-weight pipeline running.
- Confirm the track's exact rules and submission requirements on the hackathon page.
