from typing import List, Tuple
from analyzer.schema import Finding, FixPlanItem

def get_location_description(x: float, y: float) -> str:
    """Returns a natural language description of where on the screen the element is located."""
    vertical = "top" if y < 0.33 else ("middle" if y < 0.66 else "bottom")
    horizontal = "left" if x < 0.33 else ("center" if x < 0.66 else "right")
    
    if vertical == "middle" and horizontal == "center":
        return "center of page"
    return f"{vertical} {horizontal}"

def build_fix_plan(findings: List[Finding], max_items: int = 5) -> List[FixPlanItem]:
    """Generates the prioritized fix plan items from ranked findings."""
    fix_plan: List[FixPlanItem] = []
    top_findings = findings[:max_items]
    
    for idx, f in enumerate(top_findings, start=1):
        fix_plan.append(
            FixPlanItem(
                priority=idx,
                title=f"{f.title} ({f.category})",
                finding_ids=[f.id]
            )
        )
    return fix_plan

def build_fix_prompt(findings: List[Finding], persona: str = "", goal: str = "", max_findings: int = 7) -> str:
    """
    Constructs a plain-text prompt tailored for AI coding tools (Cursor, Lovable, Bolt, v0, Claude Code).
    """
    top_findings = findings[:max_findings]
    
    context_lines = []
    if persona:
        context_lines.append(f"- Target User Persona: {persona}")
    if goal:
        context_lines.append(f"- User Goal: {goal}")
    context_str = "\n".join(context_lines)
    if context_str:
        context_str = f"Context for changes:\n{context_str}\n\n"

    items_text = []
    for idx, f in enumerate(top_findings, start=1):
        loc_desc = get_location_description(f.location.x, f.location.y)
        items_text.append(
            f"{idx}. [{f.severity.upper()}] {f.title}\n"
            f"   - Problem: {f.problem}\n"
            f"   - Fix: {f.solution}\n"
            f"   - Target Area: approx. {loc_desc} (x: {int(f.location.x * 100)}%, y: {int(f.location.y * 100)}%)\n"
            f"   - Heuristic / Guideline: {f.heuristic}"
        )

    findings_block = "\n\n".join(items_text)

    prompt = (
        "You are improving the UI/UX of this existing application. "
        "Apply the following prioritized fixes without breaking any existing functionality, layout flow, or business logic.\n\n"
        f"{context_str}"
        "PRIORITIZED FIXES:\n"
        f"{findings_block}\n\n"
        "GUIDELINES FOR THE FIXES:\n"
        "- Maintain WCAG AA compliance (ensure text contrast is at least 4.5:1 for body and 3:1 for large headers).\n"
        "- Ensure interactive touch/click targets are at least 44x44px.\n"
        "- Use consistent typography hierarchy, spacing scale, and clear state styling (hover/focus/disabled/active).\n"
        "- Keep the existing technology stack and component architecture intact.\n"
        "- Once finished, summarize the exact code modifications made."
    )
    return prompt
