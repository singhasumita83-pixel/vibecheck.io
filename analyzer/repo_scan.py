import re
from typing import List, Dict, Optional, Tuple
from analyzer.schema import Finding, CodeLocation

def calculate_contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates WCAG relative luminance contrast ratio between two hex colors."""
    def hex_to_rgb(h: str) -> Tuple[float, float, float]:
        h = h.lstrip('#')
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        if len(h) != 6:
            return 0.5, 0.5, 0.5
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return r, g, b

    def luminance(r: float, g: float, b: float) -> float:
        a = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
        return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

    try:
        l1 = luminance(*hex_to_rgb(hex1))
        l2 = luminance(*hex_to_rgb(hex2))
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return round((lighter + 0.05) / (darker + 0.05), 2)
    except Exception:
        return 4.5

class RepoScanner:
    def __init__(self):
        pass

    def scan_file(self, rel_path: str, content: str) -> List[Finding]:
        """Runs rule-based static AST/Regex scans against a single file content."""
        findings: List[Finding] = []
        lines = content.splitlines()
        ext = rel_path.lower().split('.')[-1]

        # 1. HTML / JSX specific checks
        if ext in ("html", "jsx", "tsx", "vue", "svelte"):
            findings.extend(self._scan_markup(rel_path, lines, content))

        # 2. CSS / Styling specific checks
        if ext in ("css", "scss", "sass", "html", "vue", "svelte"):
            findings.extend(self._scan_styles(rel_path, lines))

        return findings

    def _scan_markup(self, rel_path: str, lines: List[str], full_content: str) -> List[Finding]:
        findings = []

        # Rule 1: <img> without alt attribute
        img_pattern = re.compile(r"<img\b([^>]*?)(/?)>", re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            for match in img_pattern.finditer(line):
                attrs = match.group(1)
                if not re.search(r'\balt\s*=', attrs, re.IGNORECASE):
                    findings.append(Finding(
                        id=f"static_img_alt_{i}",
                        title="Image missing required alt text",
                        category="Accessibility",
                        severity="High",
                        confidence=0.95,
                        heuristic="WCAG 2.1 AA 1.1.1 Non-text Content",
                        code_location=CodeLocation(file=rel_path, line_start=i, line_end=i),
                        snippet=match.group(0),
                        problem="The <img> element is missing an alt attribute.",
                        impact="Screen reader users will not understand the context or purpose of this graphic.",
                        solution="Add a concise, descriptive alt attribute (e.g. alt=\"Company logo\").",
                        evidence="No alt attribute found on <img> tag.",
                        source="static"
                    ))

        # Rule 2: <input> without label, aria-label, or id
        input_pattern = re.compile(r"<input\b([^>]*?)(/?)>", re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            for match in input_pattern.finditer(line):
                attrs = match.group(1)
                input_type = re.search(r'type\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
                t_val = input_type.group(1).lower() if input_type else "text"
                if t_val in ("hidden", "submit", "button", "reset"):
                    continue

                has_aria_label = re.search(r'\baria-label(ledby)?\s*=', attrs, re.IGNORECASE)
                has_id = re.search(r'\bid\s*=', attrs, re.IGNORECASE)
                if not has_aria_label and not has_id:
                    findings.append(Finding(
                        id=f"static_input_label_{i}",
                        title="Form input lacks accessible label or id",
                        category="Forms & Feedback",
                        severity="High",
                        confidence=0.90,
                        heuristic="WCAG 2.1 AA 3.3.2 Labels or Instructions",
                        code_location=CodeLocation(file=rel_path, line_start=i, line_end=i),
                        snippet=match.group(0),
                        problem="The <input> field does not specify an aria-label or an id associated with a <label>.",
                        impact="Assistive technologies cannot announce the expected input for this field.",
                        solution="Link an explicit <label for=\"id\"> or add aria-label=\"Description\".",
                        evidence=f"Missing label pairing on input (type='{t_val}').",
                        source="static"
                    ))

        # Rule 3: Clickable div/span without role="button" or keyboard handler
        clickable_div_pattern = re.compile(r"<(div|span)\b([^>]*?)(onClick|onclick)\s*=", re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            match = clickable_div_pattern.search(line)
            if match:
                tag = match.group(1)
                attrs = match.group(2)
                has_role = re.search(r'\brole\s*=\s*["\']button["\']', attrs, re.IGNORECASE)
                has_key_handler = re.search(r'\bonkey(down|up|press)\s*=', line, re.IGNORECASE)
                if not has_role or not has_key_handler:
                    findings.append(Finding(
                        id=f"static_clickable_div_{i}",
                        title=f"Non-semantic clickable <{tag}> without keyboard accessibility",
                        category="Accessibility",
                        severity="High",
                        confidence=0.88,
                        heuristic="WCAG 2.1 AA 2.1.1 Keyboard",
                        code_location=CodeLocation(file=rel_path, line_start=i, line_end=i),
                        snippet=line.strip()[:100],
                        problem=f"A generic <{tag}> has an onClick handler without role='button' or keyboard listeners.",
                        impact="Keyboard-only users and screen readers cannot navigate or activate this action.",
                        solution=f"Replace <{tag}> with a native <button>, or add role=\"button\" and onKeyDown handlers.",
                        evidence="onClick on non-interactive element without complete ARIA keyboard handlers.",
                        source="static"
                    ))

        # Rule 4: Missing <meta name="viewport"> or missing lang on <html> in entry documents
        if rel_path.endswith("index.html") or "<html" in full_content:
            for i, line in enumerate(lines[:30], start=1):
                if "<html" in line and not re.search(r'\blang\s*=', line, re.IGNORECASE):
                    findings.append(Finding(
                        id=f"static_html_lang_{i}",
                        title="<html> tag missing lang attribute",
                        category="Accessibility",
                        severity="Medium",
                        confidence=0.96,
                        heuristic="WCAG 2.1 AA 3.1.1 Language of Page",
                        code_location=CodeLocation(file=rel_path, line_start=i, line_end=i),
                        snippet=line.strip(),
                        problem="The root <html> element does not specify a language attribute.",
                        impact="Screen readers cannot determine correct pronunciation rules and speech synthesis.",
                        solution="Add lang=\"en\" (or appropriate language code) to the <html> opening tag.",
                        evidence="<html tag found without lang attribute.",
                        source="static"
                    ))
            if "<head" in full_content and not re.search(r'<meta\s+name=["\']viewport["\']', full_content, re.IGNORECASE):
                findings.append(Finding(
                    id=f"static_meta_viewport_1",
                    title="Missing responsive viewport meta tag",
                    category="Responsive",
                    severity="Critical",
                    confidence=0.98,
                    heuristic="Responsive Web Standards",
                    code_location=CodeLocation(file=rel_path, line_start=1, line_end=5),
                    snippet="<head>...</head>",
                    problem="The document <head> does not define a responsive viewport meta tag.",
                    impact="Mobile browsers will render the desktop layout scaled down, causing severe readability issues.",
                    solution="Include <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"> in <head>.",
                    evidence="No viewport meta tag found in document head.",
                    source="static"
                ))

        # Rule 5: Vague button copy ("Click here", "Submit", "More")
        vague_btn_pattern = re.compile(r"<button\b[^>]*>\s*(Click here|Submit|More|Button|Read More)\s*</button>", re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            match = vague_btn_pattern.search(line)
            if match:
                btn_text = match.group(1)
                findings.append(Finding(
                    id=f"static_vague_button_{i}",
                    title=f"Ambiguous action copy: '{btn_text}'",
                    category="Content & Copy",
                    severity="Medium",
                    confidence=0.82,
                    heuristic="Nielsen #2 Match Between System and the Real World",
                    code_location=CodeLocation(file=rel_path, line_start=i, line_end=i),
                    snippet=match.group(0),
                    problem=f"The button label '{btn_text}' lacks context about what happens next.",
                    impact="Users hesitate when submitting forms or exploring sections.",
                    solution=f"Replace '{btn_text}' with an explicit action (e.g. 'Create Account', 'Send Message', 'Save Changes').",
                    evidence=f"Generic text '{btn_text}' used as entire button content.",
                    source="static"
                ))

        return findings

    def _scan_styles(self, rel_path: str, lines: List[str]) -> List[Finding]:
        findings = []

        # Rule 6: outline: none / outline: 0 without replacement focus ring
        outline_none_pattern = re.compile(r"\boutline\s*:\s*(none|0)\b", re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            if outline_none_pattern.search(line):
                # Check if :focus-visible or replacement box-shadow is present on same line
                if not re.search(r"(box-shadow|border|focus-visible)", line, re.IGNORECASE):
                    findings.append(Finding(
                        id=f"static_outline_none_{i}",
                        title="Focus outline removed without replacement",
                        category="Accessibility",
                        severity="High",
                        confidence=0.89,
                        heuristic="WCAG 2.1 AA 2.4.7 Focus Visible",
                        code_location=CodeLocation(file=rel_path, line_start=i, line_end=i),
                        snippet=line.strip(),
                        problem="CSS declares 'outline: none' or 'outline: 0' removing native focus indicators.",
                        impact="Keyboard navigation becomes impossible as users cannot visually track focused controls.",
                        solution="Provide an accessible custom focus ring (e.g. outline: 2px solid var(--primary); outline-offset: 2px).",
                        evidence="outline: none detected without replacement focus style.",
                        source="static"
                    ))

        # Rule 7: Fixed container pixel widths (>800px) causing mobile overflow
        fixed_width_pattern = re.compile(r"\bwidth\s*:\s*([8-9]\d\d|1\d\d\d)px\b", re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            match = fixed_width_pattern.search(line)
            if match:
                width_val = match.group(1)
                findings.append(Finding(
                    id=f"static_fixed_width_{i}",
                    title=f"Hardcoded fixed container width: {width_val}px",
                    category="Responsive",
                    severity="Medium",
                    confidence=0.85,
                    heuristic="Nielsen #1 Visibility of System Status",
                    code_location=CodeLocation(file=rel_path, line_start=i, line_end=i),
                    snippet=line.strip(),
                    problem=f"Hardcoded fixed width of {width_val}px will overflow screens on viewports narrower than this value.",
                    impact="Induces horizontal layout scrolling and clips content on mobile devices.",
                    solution=f"Use max-width: {width_val}px; width: 100%; instead of rigid pixel widths.",
                    evidence=f"Fixed width constraint of {width_val}px without fluid container fallback.",
                    source="static"
                ))

        # Rule 8: Tiny font sizes (<12px)
        tiny_font_pattern = re.compile(r"\bfont-size\s*:\s*([1-9]|1[0-1])px\b", re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            match = tiny_font_pattern.search(line)
            if match:
                size_val = match.group(1)
                findings.append(Finding(
                    id=f"static_tiny_font_{i}",
                    title=f"Sub-minimum font size: {size_val}px",
                    category="Usability",
                    severity="Medium",
                    confidence=0.88,
                    heuristic="WCAG 2.1 AA 1.4.4 Resize Text",
                    code_location=CodeLocation(file=rel_path, line_start=i, line_end=i),
                    snippet=line.strip(),
                    problem=f"Text font size is set to {size_val}px, below the recommended 12px minimum.",
                    impact="Severely impairs readability for users with low vision or on mobile screens.",
                    solution="Increase base font size to at least 12px (or 14px for body content).",
                    evidence=f"font-size declared as {size_val}px.",
                    source="static"
                ))

        # Rule 9: Low-contrast CSS color pairs (e.g. color: #b8b8b8 on #f7f7f7)
        color_pair_pattern = re.compile(r"color\s*:\s*(#[0-9a-fA-F]{3,6}).*?background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})")
        for i, line in enumerate(lines, start=1):
            match = color_pair_pattern.search(line)
            if match:
                fg, bg = match.group(1), match.group(2)
                ratio = calculate_contrast_ratio(fg, bg)
                if ratio < 4.5:
                    findings.append(Finding(
                        id=f"static_low_contrast_{i}",
                        title=f"Low CSS color contrast ratio: {ratio}:1",
                        category="Accessibility",
                        severity="Critical" if ratio < 3.0 else "High",
                        confidence=0.94,
                        heuristic="WCAG 2.1 AA 1.4.3 Contrast (Minimum)",
                        code_location=CodeLocation(file=rel_path, line_start=i, line_end=i),
                        snippet=line.strip(),
                        problem=f"Foreground color {fg} on background {bg} provides only {ratio}:1 contrast ratio.",
                        impact="Users with low vision cannot distinguish text from the surface.",
                        solution=f"Adjust colors to meet the minimum WCAG 4.5:1 ratio requirement.",
                        evidence=f"Measured ratio {ratio}:1 fails 4.5:1 AA threshold.",
                        source="static"
                    ))

        return findings

    def scan_files(self, file_list: List[Dict[str, any]]) -> List[Finding]:
        """Scans a list of files and aggregates all findings."""
        all_findings = []
        for file_info in file_list:
            abs_path = file_info["abs_path"]
            rel_path = file_info["rel_path"]
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                file_findings = self.scan_file(rel_path, content)
                all_findings.extend(file_findings)
            except Exception as e:
                print(f"[RepoScanner] Error reading {rel_path}: {e}")
                continue
        return all_findings
