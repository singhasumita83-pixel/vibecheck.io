from typing import List, Dict, Tuple
from analyzer.schema import Finding, SummaryCounts, AnalysisSummary

WEIGHTS = {
    "Critical": 25,
    "High": 15,
    "Medium": 8,
    "Low": 3
}

CATEGORIES = [
    "Usability",
    "Visual Hierarchy",
    "Accessibility",
    "Navigation",
    "Content & Copy",
    "Forms & Feedback",
    "Responsive"
]

SEVERITY_ORDER = {
    "Critical": 0,
    "High": 1,
    "Medium": 2,
    "Low": 3
}

def rank_findings(findings: List[Finding]) -> List[Finding]:
    """
    Sorts findings by severity rank (Critical -> High -> Medium -> Low),
    then by confidence descending. Re-indexes ids to f1, f2, ...
    so that ① is always the most important finding.
    """
    sorted_findings = sorted(
        findings,
        key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), -f.confidence)
    )
    
    # Re-assign sequential IDs
    reindexed: List[Finding] = []
    for idx, finding in enumerate(sorted_findings, start=1):
        f_dict = finding.model_dump()
        f_dict["id"] = f"f{idx}"
        reindexed.append(Finding(**f_dict))
        
    return reindexed

def calculate_summary(findings: List[Finding]) -> AnalysisSummary:
    """
    Calculates severity counts and category scores based on findings.
    Category score = 100 - sum(severity weight * confidence), clamped [0, 100].
    """
    counts = SummaryCounts(
        critical=sum(1 for f in findings if f.severity == "Critical"),
        high=sum(1 for f in findings if f.severity == "High"),
        medium=sum(1 for f in findings if f.severity == "Medium"),
        low=sum(1 for f in findings if f.severity == "Low"),
    )
    
    # Calculate score for each category
    scores: Dict[str, int] = {}
    for cat in CATEGORIES:
        cat_findings = [f for f in findings if f.category == cat]
        penalty = sum(WEIGHTS.get(f.severity, 5) * f.confidence for f in cat_findings)
        score = max(0, round(100 - penalty))
        scores[cat] = score
        
    return AnalysisSummary(
        counts=counts,
        scores=scores,
        disclaimer="AI heuristic indicators, not validated UX metrics."
    )
