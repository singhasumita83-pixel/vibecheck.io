# VibeCheck UI: DESIGN.md

Design system and screen specs. Intended to be handed directly to a developer or a vibe-coding tool.

---

## 1. Design principles

1. **Clarity over decoration.** The product critiques UI, so its own UI must be exemplary.
2. **The screenshot is the hero.** The report always keeps the user's UI visible.
3. **Severity is scannable.** Color plus icon plus label, never color alone.
4. **Every finding answers three questions:** What's wrong? Why does it matter? How do I fix it?
5. **Fast feedback.** Always show progress; never leave a blank screen.

## 2. Brand

- **Name:** VibeCheck UI
- **Voice:** friendly, direct, a little playful, never condescending.
- **Example copy:** "Let's vibe check your UI." / "Found 12 things worth fixing." / "Nice. Nothing critical here."

## 3. Color tokens

### Light and dark both supported

```css
:root {
  --bg:            #F8FAFC;
  --surface:       #FFFFFF;
  --surface-2:     #F1F5F9;
  --border:        #E2E8F0;
  --text:          #0F172A;
  --text-muted:    #475569;
  --primary:       #6D4AFF;   /* brand violet */
  --primary-hover: #5A38E6;
  --primary-ink:   #FFFFFF;

  --sev-critical:  #DC2626;
  --sev-high:      #EA580C;
  --sev-medium:    #CA8A04;
  --sev-low:       #2563EB;
  --success:       #16A34A;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg:         #0B1020;
    --surface:    #131A2E;
    --surface-2:  #1B2440;
    --border:     #2A3558;
    --text:       #F1F5F9;
    --text-muted: #A5B0CC;
    --primary:    #8B6DFF;
    --primary-hover: #A08AFF;
  }
}
```

**Contrast rule:** all text on its background must meet WCAG AA (4.5:1 body, 3:1 large text). Verify the severity colors against the surface in both themes.

## 4. Typography

| Role | Font | Size / Weight |
|---|---|---|
| Display | Inter (fallback system-ui) | 40/48, 700 |
| H1 | Inter | 28/36, 700 |
| H2 | Inter | 20/28, 600 |
| Body | Inter | 16/24, 400 |
| Small / meta | Inter | 13/20, 500 |
| Code / prompt | JetBrains Mono (fallback ui-monospace) | 14/22, 400 |

## 5. Spacing, radius, elevation

- **Spacing scale:** 4, 8, 12, 16, 24, 32, 48, 64 px.
- **Radius:** 8 (inputs, chips), 12 (cards), 16 (large panels), 999 (pills).
- **Shadows:** `0 1px 2px rgba(15,23,42,.06)` (card), `0 8px 24px rgba(15,23,42,.12)` (popover).
- **Layout:** max content width 1200px; 12-column grid on desktop, single column under 768px.

## 6. Severity system

| Severity | Color | Icon | Badge text |
|---|---|---|---|
| Critical | `--sev-critical` | ⛔ | CRITICAL |
| High | `--sev-high` | 🔴 | HIGH |
| Medium | `--sev-medium` | 🟡 | MEDIUM |
| Low | `--sev-low` | 🔵 | LOW |

Badges always show icon + text. Marker numbers use the severity color as background with white text.

## 7. Components

### 7.1 Button
- **Primary:** filled `--primary`, white text, 48px tall, 12px radius, 600 weight.
- **Secondary:** transparent, 1px border, text color.
- **States:** hover (darker fill), focus (2px outline offset 2px), disabled (50% opacity, not-allowed cursor), loading (spinner replaces label, width unchanged).
- Minimum tap target 44×44px.

### 7.2 Upload dropzone
- Dashed 2px border, 16px radius, 240px min height.
- Icon, "Drop a screenshot or click to upload", helper "PNG or JPG, up to 5 MB".
- States: idle, drag-over (primary border and tinted background), error (red border + message), filled (thumbnail + remove button).
- Keyboard accessible: focusable, Enter/Space opens the file picker.

### 7.3 Persona selector
- Select with presets: *First-time user, College student, Busy professional, Older adult, Mobile-first user*, plus "Custom".
- Optional goal text field: "What should the user accomplish?"

### 7.4 Pain-point marker
- 28px circle, severity color fill, white bold number, white 2px ring, soft shadow.
- Hover: scale 1.15. Active: ring in `--primary`, bounding box outline appears on the screenshot.
- Positioned with percentage coordinates; clamped inside the image bounds.

### 7.5 Issue card
```text
┌──────────────────────────────────────────────┐
│ ① [HIGH]  Visual Hierarchy        conf. 82%  │
│ Primary CTA lacks visual prominence          │
│ ─────────────────────────────────────────    │
│ Problem   The Submit button matches ...      │
│ Impact    New users may hesitate ...         │
│ Fix       Use a filled primary style ...     │
│ Evidence  Button and background similar ...  │
│ Heuristic Nielsen #4                         │
└──────────────────────────────────────────────┘
```
- Collapsed state shows number, badge, category, title. Expanded shows all fields.
- Selected card has a primary-colored left border and syncs with its marker.

### 7.6 Score ring / bar
- Category bars with label, 0 to 100 value, color thresholds (≥80 green, 60 to 79 amber, <60 red).
- Always followed by the caption: *"AI heuristic indicator, not a validated UX metric."*

### 7.7 Filter chips
- Severity and category toggles, multi-select, show counts: "High (4)".

### 7.8 Fix Prompt panel
- Monospace block, max height 320px with scroll, **Copy** button top-right.
- On copy: button changes to "Copied ✓" for 2 seconds.

### 7.9 Toasts and errors
- Bottom-center toast, auto-dismiss in 5s, with Retry action for failed analysis.

## 8. Screens

### 8.1 Landing / Upload
```text
┌────────────────────────────────────────────────────┐
│ ◆ VibeCheck UI                       [Try demo]    │
│                                                    │
│      Your AI UX tester for vibe-coded apps         │
│  Find friction before your users do. Get fixes     │
│  you can paste straight into your AI coding tool.  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │          Drop a screenshot here              │  │
│  └──────────────────────────────────────────────┘  │
│  Persona [ College student ▾ ]                     │
│  Goal    [ Create an account            ]          │
│                                                    │
│            [   Analyze my UI   ]                   │
└────────────────────────────────────────────────────┘
```

### 8.2 Analyzing
- Centered progress card with four stages and live check marks: *Reading your UI → Finding issues → Verifying findings → Writing fixes*.
- Screenshot thumbnail with a subtle scanning-line animation (respect `prefers-reduced-motion`).

### 8.3 Report (core screen)
```text
┌─────────────────────────────────────────────────────────────┐
│ ◆ VibeCheck UI                      [New check] [Copy Fix ▸]│
├─────────────────────────────────────────────────────────────┤
│ Summary:  ⛔1  🔴4  🟡7  🔵3      Scores: Usab 68 · Hier 61  │
├───────────────────────────────┬─────────────────────────────┤
│                               │ Filters: [High 4][Medium 7] │
│   SCREENSHOT + MARKERS        │ ┌─ ① HIGH  Title ────────┐  │
│   ① ② ③ …                     │ ├─ ② MED   Title ────────┤  │
│                               │ └─ ③ LOW   Title ────────┘  │
│                               │                             │
├───────────────────────────────┴─────────────────────────────┤
│ Fix Plan:  1 Navigation · 2 CTA · 3 Mobile · 4 Errors · 5 …│
│ Fix Prompt  [ monospace block ........................ ][Copy]│
└─────────────────────────────────────────────────────────────┘
```
- Desktop: two columns (screenshot 60%, cards 40%), both independently scrollable with the screenshot sticky.
- Mobile: summary → screenshot (with markers) → cards → fix plan → prompt.

### 8.4 Empty and error states
- **No issues found:** celebratory but honest message, suggest checking mobile.
- **API failure:** "We couldn't finish the check." with Retry and "Use demo result".
- **Bad file:** inline error under the dropzone.

## 9. Interaction details

- Click marker → highlight card, scroll it into view, draw bounding box.
- Click card → pulse its marker for 600ms.
- Keyboard: Tab moves through markers and cards in numeric order; Enter toggles expansion; Esc clears selection.
- Marker numbering follows severity order, so ① is always the most important.
- Animations 150 to 250ms ease-out; disable under `prefers-reduced-motion`.

## 10. Responsive behavior

| Breakpoint | Layout |
|---|---|
| ≥ 1024px | Two-column report |
| 768 to 1023px | Stacked, screenshot full width, cards below |
| < 768px | Single column, larger tap targets, filters in a horizontal scroll row |

## 11. Accessibility checklist (the app must pass its own test)

- Contrast AA in light and dark themes.
- Visible focus rings on every interactive element.
- Markers and cards have `aria-label`s ("Issue 1, High: Primary CTA lacks prominence").
- Severity never conveyed by color alone.
- Dropzone usable by keyboard and screen reader.
- Live region announces analysis progress and completion.
- Tap targets ≥ 44px.
- No horizontal scrolling at 320px width.

## 12. Demo app (the intentionally bad app)

Build a small dashboard with these planted flaws, one per category, so VibeCheck has clear targets:

| Flaw | Category |
|---|---|
| Gray-on-gray low-contrast text | Accessibility |
| Tiny 24px icon-only buttons | Usability |
| Primary CTA styled like secondary | Visual Hierarchy |
| 9-item flat nav with unclear labels | Navigation |
| Form with 3 unnecessary fields and vague error "Invalid" | Forms & Feedback |
| Wall of text, no headings | Content & Copy |
| Fixed-width table overflowing on mobile | Responsive |

Keep a screenshot and a precomputed `result.json` in `static/demo/`.

## 13. Assets

- Logo: simple checkmark inside a speech-bubble or magnifier, violet on light, white on dark.
- Icons: Lucide (consistent 1.75px stroke).
- Fonts: Inter and JetBrains Mono via Google Fonts, with system fallbacks.

## 14. Handoff prompt (paste into your AI coding tool)

```text
Build the VibeCheck UI frontend using vanilla HTML, CSS and JS with Tailwind CDN.
Follow DESIGN.md exactly: color tokens, typography, components and the three screens
(Upload, Analyzing, Report). Report screen has a screenshot with absolutely positioned
numbered severity markers (percentage coordinates), a synced list of expandable issue
cards, severity/category filter chips, category score bars with the disclaimer caption,
a fix plan list, and a Fix Prompt panel with a Copy button. Support light and dark
themes, keyboard navigation, and prefers-reduced-motion. Consume the JSON contract
from TRD.md (POST /api/analyze, GET /api/demo).
```
