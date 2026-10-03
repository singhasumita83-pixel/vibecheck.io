import re
from typing import List, Dict, Optional, Tuple
from analyzer.schema import Finding, CodeFix

def generate_unified_diff(
    file_path: str,
    original_line: str,
    replacement_line: str,
    line_number: int
) -> str:
    """Creates a standard unified diff for a single line replacement."""
    clean_path = file_path.replace("\\", "/")
    diff_lines = [
        f"--- a/{clean_path}",
        f"+++ b/{clean_path}",
        f"@@ -{line_number},1 +{line_number},1 @@",
        f"-{original_line}",
        f"+{replacement_line}"
    ]
    return "\n".join(diff_lines)

class RepoFixer:
    def __init__(self, repo_dir: Optional[str] = None):
        self.repo_dir = repo_dir

    def synthesize_fix(self, finding: Finding, file_content: str) -> Optional[CodeFix]:
        """
        Synthesizes a minimal unified diff for a given static/model finding
        based on the detected rule and solution.
        """
        if not finding.code_location or not file_content:
            return None

        lines = file_content.splitlines()
        target_line_idx = finding.code_location.line_start - 1
        if target_line_idx < 0 or target_line_idx >= len(lines):
            return None

        orig_line = lines[target_line_idx]
        file_path = finding.code_location.file
        rule = f"{getattr(finding, 'id', '')} {getattr(finding, 'title', '')}".lower()

        new_line = orig_line

        # 1. <img> missing alt
        if ("img" in rule or "image" in rule) and "alt" in rule:
            if "<img" in orig_line and "alt=" not in orig_line:
                # Add alt attribute
                new_line = re.sub(r"<img\b", '<img alt="Descriptive illustration"', orig_line, count=1)

        # 2. Input without label/aria-label
        elif "input" in rule:
            if "<input" in orig_line and "aria-label" not in orig_line:
                placeholder_m = re.search(r'placeholder=["\']([^"\']+)["\']', orig_line)
                label_txt = placeholder_m.group(1).capitalize() if placeholder_m else "User input"
                new_line = re.sub(r"<input\b", f'<input aria-label="{label_txt}"', orig_line, count=1)

        # 3. Clickable div without role="button" or tabIndex
        elif "clickable_div" in rule:
            if "<div" in orig_line:
                new_line = orig_line.replace("<div", '<div role="button" tabIndex="0"', 1)
            elif "<span" in orig_line:
                new_line = orig_line.replace("<span", '<span role="button" tabIndex="0"', 1)

        # 4. Missing html lang
        elif "html_lang" in rule:
            if "<html" in orig_line and "lang=" not in orig_line:
                new_line = orig_line.replace("<html", '<html lang="en"', 1)

        # 5. Fixed container width > 800px
        elif "fixed_width" in rule:
            new_line = re.sub(r"\bwidth\s*:\s*([8-9]\d\d|1\d\d\d)px", r"max-width: \1px; width: 100%", orig_line)

        # 6. Outline: none without replacement
        elif "outline_none" in rule:
            new_line = re.sub(
                r"\boutline\s*:\s*(none|0)\s*;",
                "outline: 2px solid var(--primary, #6D4AFF); outline-offset: 2px;",
                orig_line
            )

        # 7. Sub-minimum font size
        elif "tiny_font" in rule:
            new_line = re.sub(r"\bfont-size\s*:\s*([1-9]|1[0-1])px", "font-size: 13px", orig_line)

        # 8. Ambiguous button copy
        elif "vague_button" in rule:
            new_line = re.sub(
                r"<button\b([^>]*)>\s*(Submit|Click here|More)\s*</button>",
                r"<button\1>Save and Continue</button>",
                orig_line
            )

        if new_line != orig_line:
            diff_text = generate_unified_diff(
                file_path=file_path,
                original_line=orig_line,
                replacement_line=new_line,
                line_number=finding.code_location.line_start
            )
            return CodeFix(
                diff=diff_text,
                validated=True,
                explanation=f"Applied fix on line {finding.code_location.line_start}: {finding.solution}"
            )

        return None

    def validate_diff(self, diff_text: str, file_content: str) -> bool:
        """
        Validates that a unified diff matches target content cleanly.
        """
        lines = file_content.splitlines()
        for diff_line in diff_text.splitlines():
            if diff_line.startswith("-") and not diff_line.startswith("---"):
                removed_line = diff_line[1:].strip()
                # Check if this line actually exists in original file
                if not any(removed_line in l for l in lines):
                    return False
        return True

    def combine_patches(self, findings: List[Finding], selected_ids: Optional[List[str]] = None) -> str:
        """Combines all validated diffs into a unified .patch file."""
        patches = []
        for f in findings:
            if selected_ids is not None and f.id not in selected_ids:
                continue
            if f.fix and f.fix.diff:
                patches.append(f.fix.diff)
        return "\n\n".join(patches) + "\n"
