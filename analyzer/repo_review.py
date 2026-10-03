import os
from typing import List, Dict, Optional, Tuple
from analyzer.schema import Finding, CodeFix, CodeLocation, AnalysisSummary, FixPlanItem
from analyzer.repo_scan import RepoScanner
from analyzer.repo_fix import RepoFixer
from analyzer.scoring import calculate_summary, rank_findings

class RepoReviewer:
    def __init__(self, llm_client=None):
        self.scanner = RepoScanner()
        self.fixer = RepoFixer()
        self.llm_client = llm_client

    def review_repository(
        self,
        file_list: List[Dict[str, any]],
        persona: str = "",
        goal: str = ""
    ) -> Tuple[List[Finding], AnalysisSummary, List[FixPlanItem], str]:
        """
        Executes static scan + model review pass over selected UI files,
        generates unified diff fixes, scores the findings, and builds the fix plan.
        """
        all_findings: List[Finding] = []
        files_by_path = {}

        # 1. Static Scan pass
        for file_info in file_list:
            abs_p = file_info["abs_path"]
            rel_p = file_info["rel_path"]
            try:
                with open(abs_p, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                files_by_path[rel_p] = content
                file_findings = self.scanner.scan_file(rel_p, content)
                all_findings.extend(file_findings)
            except Exception as e:
                print(f"[RepoReviewer] Error reading {rel_p}: {e}")

        # 2. Fix generation pass
        for finding in all_findings:
            if finding.code_location and finding.code_location.file in files_by_path:
                content = files_by_path[finding.code_location.file]
                fix = self.fixer.synthesize_fix(finding, content)
                if fix:
                    finding.fix = fix

        # 3. Ranking and ID assignment (r1, r2...)
        ranked = self._rank_repo_findings(all_findings)

        # 4. Scoring & verified fixes count
        summary = calculate_summary(ranked)
        verified_count = sum(1 for f in ranked if f.fix and f.fix.validated)
        summary.verified_fixes = verified_count

        # 5. Fix plan items
        fix_plan = []
        for idx, f in enumerate(ranked[:5], start=1):
            fix_plan.append(
                FixPlanItem(
                    priority=idx,
                    title=f"{f.title} ({f.code_location.file}:{f.code_location.line_start if f.code_location else '1'})",
                    finding_ids=[f.id]
                )
            )

        # 6. Plain-text fix prompt for coding tool
        fix_prompt_lines = [
            "You are fixing UI and accessibility issues identified in this codebase.",
            f"Context: Persona='{persona or 'Developer'}', Goal='{goal or 'Accessibility & Polish'}'.\n",
            "PRIORITIZED CODE FIXES:"
        ]
        for idx, f in enumerate(ranked[:7], start=1):
            loc_str = f"{f.code_location.file}:{f.code_location.line_start}" if f.code_location else "UI"
            fix_prompt_lines.append(
                f"{idx}. [{f.severity.upper()}] {f.title} in {loc_str}\n"
                f"   - Problem: {f.problem}\n"
                f"   - Fix: {f.solution}\n"
                f"   - Heuristic: {f.heuristic}"
            )
        fix_prompt = "\n\n".join(fix_prompt_lines)

        return ranked, summary, fix_plan, fix_prompt

    def _rank_repo_findings(self, findings: List[Finding]) -> List[Finding]:
        SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        sorted_findings = sorted(
            findings,
            key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), -f.confidence)
        )
        reindexed = []
        for idx, f in enumerate(sorted_findings, start=1):
            f_dict = f.model_dump()
            f_dict["id"] = f"r{idx}"
            reindexed.append(Finding(**f_dict))
        return reindexed
