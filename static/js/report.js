// VibeCheck UI — Report Screen Management (DESIGN V2: Red Pen)

// Severity marks: shape + word (section 4 of DESIGN V2)
const SEVERITY_MARKS = {
  Critical: { mark: '■', cls: 'sev-mark-critical' },
  High:     { mark: '●', cls: 'sev-mark-high' },
  Medium:   { mark: '◐', cls: 'sev-mark-medium' },
  Low:      { mark: '○', cls: 'sev-mark-low' }
};

export class ReportManager {
  constructor(overlayManager) {
    this.overlay = overlayManager;
    this.currentData = null;
    this.previousData = null;   // Feature 4: kept for Re-check
    this.currentMode = 'screenshot';
    this.activeFilter = { severity: 'all', category: 'all' };
    this.activeFileFilter = 'all';
    this.expandedCards = new Set();
    this.selectedFixIds = new Set();

    // Restore previous result from sessionStorage (Feature 4)
    try {
      const stored = sessionStorage.getItem('vibecheck_previous_result');
      if (stored) this.previousData = JSON.parse(stored);
    } catch (_) {}

    this.initElements();
    this.bindEvents();
  }

  initElements() {
    this.reportScreen = document.getElementById('report-screen');
    this.summaryCountsEl = document.getElementById('summary-counts');
    this.scoresContainerEl = document.getElementById('scores-container');
    this.reportLayoutEl = document.getElementById('report-layout');
    this.fixPromptTextEl = document.getElementById('fix-prompt-text');
    this.copyPromptBtn = document.getElementById('btn-copy-prompt');
    this.headerCopyBtn = document.getElementById('btn-header-copy-fix');
    this.headerDownloadBtn = document.getElementById('btn-header-download-report');
    this.downloadReportBtn = document.getElementById('btn-download-report');
    this.modelInfoFooter = document.getElementById('model-info-footer');
    this.fixPromptSection = document.getElementById('fix-prompt-section');
    // Ignored header placeholder
    this.ignoredHeaderEl = document.getElementById('ignored-header');
  }

  bindEvents() {
    if (this.copyPromptBtn) {
      this.copyPromptBtn.addEventListener('click', () => this.copyPrompt());
    }
    if (this.headerCopyBtn) {
      this.headerCopyBtn.addEventListener('click', () => {
        const section = document.getElementById('fix-prompt-section');
        if (section) section.scrollIntoView({ behavior: 'smooth' });
      });
    }
    if (this.headerDownloadBtn) {
      this.headerDownloadBtn.addEventListener('click', () => this.downloadReport());
    }
    if (this.downloadReportBtn) {
      this.downloadReportBtn.addEventListener('click', () => this.downloadReport());
    }

    // Overlay marker → finding card sync
    this.overlay.onSelect((id, shouldScroll) => {
      this.highlightCard(id, shouldScroll);
    });

    // Add ignored header button
    this.initIgnoredHeader();

    // Esc clears selection
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.clearSelection();
      }
    });
  }

  renderReport(data, imageSrc, mode = 'screenshot') {
    // Feature 4: save previous before overwriting
    if (this.currentData) {
      this.previousData = this.currentData;
      try {
        sessionStorage.setItem('vibecheck_previous_result', JSON.stringify(this.previousData));
      } catch (_) {}
    }

    this.currentData = data;
    this.currentMode = (data.mode === 'repo' || mode === 'repo') ? 'repo' : 'screenshot';
    this.expandedCards.clear();
    this.activeFilter = { severity: 'all', category: 'all' };
    this.activeFileFilter = 'all';

    const isRepo = this.currentMode === 'repo';

    // Show header actions
    const btnNewCheck = document.getElementById('btn-new-check');
    const btnHeaderCopy = document.getElementById('btn-header-copy-fix');
    const btnHeaderDownload = document.getElementById('btn-header-download-report');
    if (btnNewCheck) btnNewCheck.classList.remove('hidden');
    if (btnHeaderCopy) btnHeaderCopy.classList.remove('hidden');
    if (btnHeaderDownload) btnHeaderDownload.classList.remove('hidden');

    // Init selected fix IDs for repo mode
    this.selectedFixIds.clear();
    if (data.findings) {
      data.findings.forEach(f => {
        if (f.fix && f.fix.validated) {
          this.selectedFixIds.add(f.id);
        }
      });
    }

    // Auto-expand first card
    if (data.findings && data.findings.length > 0) {
      this.expandedCards.add(data.findings[0].id);
    }

    // Render summary
    this.renderSummaryCounts(data.summary.counts, isRepo, data.summary.verified_fixes, data.repo_info);

    // Render scores
    this.renderScores(data.summary.scores, data.summary.disclaimer);

    // Build report layout
    if (isRepo) {
      this.renderRepoLayout(data, imageSrc);
    } else {
      this.renderScreenshotLayout(data, imageSrc);
    }

    // Render fix prompt
    this.renderFixPrompt(data.fix_prompt, data.fix_plan);

    // Render model footer
    this.renderModelInfo(data.model);

    // Feature 4: show Re-check button if there is a previous result
    this._renderRecheckButton();
  }


  // ─── Summary (typographic line) ───

  renderSummaryCounts(counts, isRepo, verifiedFixes, repoInfo) {
    if (!this.summaryCountsEl) return;

    const total = (counts.critical || 0) + (counts.high || 0) + (counts.medium || 0) + (counts.low || 0);

    let repoLabel = '';
    if (isRepo && repoInfo) {
      repoLabel = `<span style="margin-left:12px; font-family:var(--font-mono); font-size:13px; color:var(--ink-2);">${this.escapeHtml(repoInfo.url || '')} @ ${this.escapeHtml(repoInfo.branch || 'main')}</span>`;
    }

    let verifiedLabel = '';
    if (isRepo && verifiedFixes !== undefined) {
      verifiedLabel = `<span class="summary-item" style="margin-left:12px;"><span class="sev-mark" style="color:var(--ok);">✓</span> ${verifiedFixes} fixes verified</span>`;
    }

    // Ignored count UI
    const ignoredCount = this.getIgnoredIds().length;
    const ignoredLabel = `<span id="ignored-header" class="summary-item" style="margin-left:12px; cursor:pointer;" title="Show ignored issues">🗑️ ${ignoredCount} ignored</span>`;

    this.summaryCountsEl.innerHTML = `
      <span class="summary-total">${total} issues</span>
      <span class="summary-breakdown">
        <span class="summary-item"><span class="sev-mark sev-mark-critical">${SEVERITY_MARKS.Critical.mark}</span> ${counts.critical} critical</span>
        <span class="summary-item"><span class="sev-mark sev-mark-high">${SEVERITY_MARKS.High.mark}</span> ${counts.high} high</span>
        <span class="summary-item"><span class="sev-mark sev-mark-medium">${SEVERITY_MARKS.Medium.mark}</span> ${counts.medium} medium</span>
        <span class="summary-item"><span class="sev-mark sev-mark-low">${SEVERITY_MARKS.Low.mark}</span> ${counts.low} low</span>
        ${verifiedLabel}
        ${ignoredLabel}
      </span>
      ${repoLabel}
    `;
  }


  // ─── Scores (plain numbers + thin bar) ───

  renderScores(scores, disclaimer) {
    if (!this.scoresContainerEl) return;
    const entries = Object.entries(scores || {});
    if (entries.length === 0) {
      this.scoresContainerEl.innerHTML = '';
      return;
    }

    let html = '<div class="scores-row">';
    entries.forEach(([cat, score]) => {
      let barClass = '';
      if (score < 60) barClass = ' poor';
      else if (score < 80) barClass = ' warn';

      html += `
        <div class="score-item">
          <span class="score-name">${cat}</span>
          <span class="score-value">${score}</span>
          <div class="score-bar"><div class="score-bar-fill${barClass}" style="width:${score}%;"></div></div>
        </div>
      `;
    });
    html += '</div>';
    html += `<p class="scores-disclaimer">(AI heuristic indicators, not validated UX metrics)</p>`;

    this.scoresContainerEl.innerHTML = html;
  }


  // ─── Screenshot Mode Layout ───

  renderScreenshotLayout(data, imageSrc) {
    if (!this.reportLayoutEl) return;

    this.reportLayoutEl.className = 'report-grid';
    this.reportLayoutEl.innerHTML = `
      <div class="screenshot-col" id="col-screenshot">
        <div class="screenshot-wrap" id="overlay-container">
          <img id="report-screenshot" src="${imageSrc || ''}" alt="Audited screenshot" style="width:100%; display:block;">
        </div>
      </div>
      <div class="findings-col" id="col-findings">
        <div id="filter-bar" class="filter-bar"></div>
        <div id="issue-cards-list"></div>
      </div>
    `;

    // Re-init overlay with new container
    const overlayContainer = document.getElementById('overlay-container');
    const reportImg = document.getElementById('report-screenshot');
    this.overlay.container = overlayContainer;
    this.overlay.img = reportImg;

    // Render filters
    this.renderFilters(data.findings);

    // Render cards
    this.renderCards(data.findings);

    // Render overlay markers
    this.overlay.render(data.findings);
    if (data.findings && data.findings.length > 0) {
      const firstId = data.findings[0].id;
      this.highlightCard(firstId, false);
      this.overlay.select(firstId);
    }
  }


  // ─── Repo Mode Layout ───

  renderRepoLayout(data) {
    if (!this.reportLayoutEl) return;

    this.reportLayoutEl.className = '';
    this.reportLayoutEl.innerHTML = `
      <div class="repo-report-grid">
        <div class="repo-tree-panel" id="repo-tree-panel">
          <div id="file-tree-container" class="file-tree"></div>
        </div>
        <div class="repo-findings-panel" id="col-findings">
          <div id="filter-bar" class="filter-bar" style="padding-left:16px; padding-right:16px;"></div>
          <div id="issue-cards-list" style="padding: 0 16px;"></div>
        </div>
      </div>
      <div class="repo-footer" id="repo-footer">
        <span id="repo-selected-count" class="repo-footer-count"></span>
        <button id="btn-download-patch" type="button" class="btn btn-primary" style="padding:8px 20px; min-height:40px; font-size:14px;">Download .patch</button>
      </div>
    `;

    // File tree
    this.renderFileTree(data);

    // Filters
    this.renderFilters(data.findings);

    // Cards
    this.renderCards(data.findings);

    // Update selection counter
    this.updatePatchSelectionCounter();

    // Download button
    const btnDownload = document.getElementById('btn-download-patch');
    if (btnDownload) {
      btnDownload.addEventListener('click', () => this.downloadPatch());
    }
  }


  // ─── File Tree (text list, no icons) ───

  renderFileTree(data) {
    const container = document.getElementById('file-tree-container');
    if (!container) return;

    const scannedFiles = (data.repo_info && data.repo_info.scanned_files) || [];

    const fileIssueCounts = {};
    (data.findings || []).forEach(f => {
      const fn = f.code_location ? f.code_location.file : 'other';
      fileIssueCounts[fn] = (fileIssueCounts[fn] || 0) + 1;
    });

    let html = `
      <div class="file-tree-item ${this.activeFileFilter === 'all' ? 'active' : ''}" data-file="all">
        <span class="file-tree-name">All files</span>
        <span class="file-tree-count">${data.findings ? data.findings.length : 0}</span>
      </div>
    `;

    scannedFiles.forEach(fileName => {
      const count = fileIssueCounts[fileName] || 0;
      const isActive = this.activeFileFilter === fileName;
      html += `
        <div class="file-tree-item file-tree-indent ${isActive ? 'active' : ''}" data-file="${this.escapeHtml(fileName)}">
          <span class="file-tree-name">${this.escapeHtml(fileName)}</span>
          <span class="file-tree-count">${count}</span>
        </div>
      `;
    });

    container.innerHTML = html;

    container.querySelectorAll('.file-tree-item').forEach(item => {
      item.addEventListener('click', () => {
        this.activeFileFilter = item.dataset.file;
        this.renderFileTree(this.currentData);
        this.applyFilters();
      });
    });
  }


  // ─── Filters (text toggles) ───

  renderFilters(findings) {
    const filterBar = document.getElementById('filter-bar');
    if (!filterBar) return;

    const severities = ['all', 'Critical', 'High', 'Medium', 'Low'];

    let html = '';
    severities.forEach((sev, i) => {
      const count = sev === 'all'
        ? findings.length
        : findings.filter(f => f.severity === sev).length;
      const label = sev === 'all' ? `All (${count})` : `${sev} (${count})`;
      const activeClass = this.activeFilter.severity === sev ? 'active' : '';
      if (i > 0) html += `<span class="filter-separator">·</span>`;
      html += `<button type="button" class="filter-toggle ${activeClass}" data-sev="${sev}">${label}</button>`;
    });

    filterBar.innerHTML = html;

    filterBar.querySelectorAll('.filter-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        this.activeFilter.severity = btn.dataset.sev;
        this.renderFilters(this.currentData.findings);
        this.applyFilters();
      });
    });
  }


  applyFilters() {
    if (!this.currentData) return;
    const isRepo = this.currentMode === 'repo';

    const ignoredSet = new Set(this.getIgnoredIds());
    const filtered = this.currentData.findings.filter(f => {
      const matchSev = this.activeFilter.severity === 'all' || f.severity === this.activeFilter.severity;
      let matchFile = true;
      if (isRepo && this.activeFileFilter !== 'all') {
        matchFile = f.code_location && f.code_location.file === this.activeFileFilter;
      }
      const notIgnored = !ignoredSet.has(f.id);
      return matchSev && matchFile && notIgnored;
    });

    this.renderCards(filtered);
    if (!isRepo) {
      this.overlay.render(filtered);
    }
  }


  // ─── Finding Cards (margin note style) ───

  renderCards(findings) {
    const container = document.getElementById('issue-cards-list');
    if (!container) return;
    const isRepo = this.currentMode === 'repo';

    if (findings.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <p>Nothing matches these filters.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = findings.map((f, idx) => {
      const isExpanded = this.expandedCards.has(f.id);
      const sevInfo = SEVERITY_MARKS[f.severity] || { mark: '•', cls: '' };

      let codeLocHtml = '';
      if (f.code_location) {
        codeLocHtml = `<span class="code-loc">${this.escapeHtml(f.code_location.file)} : ${f.code_location.line_start}</span>`;
      }

      // Diff / fix for repo mode
      let fixHtml = '';
            // Add dismiss button for each finding
            const isIgnored = this.isFindingIgnored(f.id);
            if (isIgnored) {
              // Skip rendering this finding entirely
              return '';
            }
            // Dismiss button HTML (shown in repo mode fixes area)
            const dismissButton = `<button class="dismiss-btn" data-id="${f.id}" title="Mark as not an issue">Dismiss</button>`;
            // Re‑check button HTML (re‑measure contrast)
            const recheckButton = `<button class="recheck-btn" data-id="${f.id}" title="Re‑check contrast">Re‑check</button>`;
            // Append dismiss and re‑check buttons to fixHtml for both repo and screenshot modes
            fixHtml += dismissButton + recheckButton;
            // Attach dismiss handler if not already attached
            // We'll delegate event handling in a later pass; for now ensure button exists.
            
      if (isRepo) {
        if (f.fix && f.fix.diff) {
          const isSelected = this.selectedFixIds.has(f.id);
          const diffFormatted = this.formatDiff(f.fix.diff);

          fixHtml = `
            <div style="margin-top:12px; padding-top:10px; border-top:1px solid var(--rule);">
              <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
                <span class="verified-tag">✓ patch applies cleanly</span>
                <label class="fix-checkbox-label">
                  <input type="checkbox" class="fix-checkbox" data-id="${f.id}" ${isSelected ? 'checked' : ''}>
                  include
                </label>
              </div>
              ${diffFormatted}
            </div>
          `;
        } else {
          fixHtml = `
            <div style="margin-top:10px; padding-top:8px; border-top:1px solid var(--rule);">
              <span class="type-mono-sm" style="font-style:italic;">Manual fix suggested</span>
            </div>
          `;
        }
      }

      return `
        <div class="finding-note ${this.expandedCards.has(f.id) ? '' : ''}" id="card-${f.id}" data-id="${f.id}" tabindex="0" role="article" aria-label="Issue ${idx + 1}, ${f.severity}: ${f.title}">
          <div class="finding-header">
            <span class="finding-number">${idx + 1}</span>
            <span class="finding-sev-mark ${sevInfo.cls}">${sevInfo.mark}</span>
            <span class="finding-sev-word">${f.severity}</span>
            <span class="finding-category-sep">·</span>
            <span class="finding-category">${this.escapeHtml(f.category)}</span>
          </div>

          <div class="finding-title">${this.escapeHtml(f.title)}</div>
          ${codeLocHtml}

          <div class="finding-details ${isExpanded ? 'expanded' : ''}" id="details-${f.id}">
            <div class="finding-body-label">Why</div>
            <div class="finding-body-text">${this.escapeHtml(f.problem || f.impact || '')}</div>

            <div class="finding-body-label">Fix</div>
            <div class="finding-body-text">${this.escapeHtml(f.solution || '')}</div>

            <div class="finding-evidence">${this.escapeHtml(f.evidence || '')}</div>

            ${f.snippet ? `
              <div style="margin-top:8px;">
                <pre class="type-evidence" style="padding:8px; background:var(--paper-2); border:1px solid var(--rule); overflow-x:auto;">${this.escapeHtml(f.snippet)}</pre>
              </div>
            ` : ''}

            ${fixHtml}
          </div>

          <button type="button" class="finding-toggle btn-toggle">${isExpanded ? 'Collapse' : 'Details'}</button>
        </div>
      `;
    }).join('');

    // Event listeners
    container.querySelectorAll('.finding-note').forEach(card => {
      const id = card.dataset.id;

      card.addEventListener('click', (e) => {
        // Dismiss button handling
        if (e.target.closest('.dismiss-btn')) {
          e.stopPropagation();
          const btn = e.target.closest('.dismiss-btn');
          const ignoreId = btn.dataset.id;
          const ignored = this.getIgnoredIds();
          if (!ignored.includes(ignoreId)) {
            ignored.push(ignoreId);
            this.setIgnoredIds(ignored);
            this.updateIgnoredHeader();
          }
          // Hide card
          const cardEl = document.getElementById(`card-${ignoreId}`);
          if (cardEl) cardEl.style.display = 'none';
          // Remove marker in screenshot mode
          if (!isRepo) {
            this.overlay.removeMarker(ignoreId);
          }
          this.applyFilters();
          return;
        }
        if (e.target.closest('.fix-checkbox')) {
          e.stopPropagation();
          const checkbox = e.target.closest('.fix-checkbox');
          if (checkbox.checked) {
            this.selectedFixIds.add(id);
          } else {
            this.selectedFixIds.delete(id);
          }
          this.updatePatchSelectionCounter();
          return;
        }

        if (e.target.closest('.btn-toggle')) {
          e.stopPropagation();
          this.toggleCard(id);
        } else {
          this.highlightCard(id, false);
          if (!isRepo) {
            this.overlay.pulse(id);
          }
        }
      });

      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.target.closest('.fix-checkbox')) {
          e.preventDefault();
          this.toggleCard(id);
          this.highlightCard(id, false);
          if (!isRepo) {
            this.overlay.pulse(id);
          }
        }
      });
    });
  }


  // ─── Feature 4: Re-check after fixing ────────────────────────────────────

  _renderRecheckButton() {
    // Remove any existing recheck banner/button from previous renders
    ['vibecheck-recheck-btn', 'vibecheck-delta-banner'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.remove();
    });

    const summaryEl = document.getElementById('summary-counts');
    if (!summaryEl) return;

    const btn = document.createElement('button');
    btn.id = 'vibecheck-recheck-btn';
    btn.type = 'button';
    btn.textContent = '⟳ Re-check after fixing';
    btn.style.cssText = [
      'margin-left:16px', 'padding:4px 12px', 'font-size:12px',
      'border:1px solid var(--rule)', 'border-radius:4px',
      'background:var(--paper-2)', 'color:var(--ink-1)',
      'cursor:pointer', 'vertical-align:middle',
    ].join(';');
    btn.title = 'Upload an improved screenshot (or re-run repo scan) and compare results';
    btn.addEventListener('click', () => this._triggerRecheck());
    summaryEl.appendChild(btn);
  }

  async _triggerRecheck() {
    if (!this.currentData) return;
    // Open a hidden file picker and re-run analysis on the new screenshot
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/png,image/jpeg,image/webp';
    input.style.display = 'none';
    document.body.appendChild(input);
    input.addEventListener('change', async () => {
      const file = input.files && input.files[0];
      document.body.removeChild(input);
      if (!file) return;

      const btn = document.getElementById('vibecheck-recheck-btn');
      if (btn) { btn.textContent = '⟳ Analysing…'; btn.disabled = true; }

      try {
        const formData = new FormData();
        formData.append('screenshot', file);
        // Preserve persona / goal if stored in current result (best-effort)
        const resp = await fetch('/api/analyze', { method: 'POST', body: formData });
        if (!resp.ok) throw new Error(`Server error ${resp.status}`);
        const afterResult = await resp.json();

        // Call /api/compare
        const cmpResp = await fetch('/api/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ before: this.currentData, after: afterResult }),
        });
        if (!cmpResp.ok) throw new Error(`Compare error ${cmpResp.status}`);
        const delta = await cmpResp.json();

        // Render the new report then overlay the improvement banner
        this.renderReport(afterResult, URL.createObjectURL(file));
        this._renderDeltaBanner(delta);
      } catch (err) {
        console.error('Re-check failed:', err);
        alert('Re-check failed: ' + err.message);
        if (btn) { btn.textContent = '⟳ Re-check after fixing'; btn.disabled = false; }
      }
    });
    input.click();
  }

  _renderDeltaBanner(delta) {
    const summaryEl = document.getElementById('summary-counts');
    if (!summaryEl) return;

    const { counts = {}, score_deltas = {}, contrast_deltas = [] } = delta;
    const { fixed = 0, new: newCount = 0, remaining = 0, total_before = 0 } = counts;

    // Score delta pills
    const scorePills = Object.entries(score_deltas)
      .filter(([, v]) => v.delta !== 0)
      .map(([cat, v]) => {
        const sign = v.delta > 0 ? '+' : '';
        const color = v.delta > 0 ? 'var(--ok, #22c55e)' : 'var(--err, #ef4444)';
        return `<span style="margin-left:8px; color:${color}; font-size:12px;">${this.escapeHtml(cat)}: ${v.before}→${v.after} (${sign}${v.delta})</span>`;
      }).join('');

    // Contrast delta items
    const contrastItems = contrast_deltas.map(cd =>
      `<li style="font-size:12px; color:var(--ink-2);">${this.escapeHtml(cd.title)}: ${cd.before_ratio}:1 → ${cd.after_ratio}:1</li>`
    ).join('');

    const banner = document.createElement('div');
    banner.id = 'vibecheck-delta-banner';
    banner.style.cssText = [
      'margin:12px 0', 'padding:12px 16px',
      'border-left:3px solid var(--ok, #22c55e)',
      'background:var(--paper-2)', 'border-radius:4px',
    ].join(';');
    banner.innerHTML = `
      <div style="font-weight:600; font-size:14px; margin-bottom:4px;">
        ✅ ${fixed} of ${total_before} fixed, ${newCount} new, ${remaining} remaining
      </div>
      <div>${scorePills}</div>
      ${contrastItems ? `<ul style="margin:6px 0 0 0; padding-left:18px;">${contrastItems}</ul>` : ''}
    `;

    // Insert before the first child of the scores container or after summaryEl
    const scoresEl = this.scoresContainerEl;
    if (scoresEl && scoresEl.parentNode) {
      scoresEl.parentNode.insertBefore(banner, scoresEl);
    } else {
      summaryEl.parentNode && summaryEl.parentNode.insertBefore(banner, summaryEl.nextSibling);
    }
  }


  // ─── Diff formatting (real diff, no rounded containers) ───

  formatDiff(diffText) {
    if (!diffText) return '';
    const lines = diffText.split('\n');
    return `
      <div class="diff-viewer">
        <div class="diff-header">
          <span>diff</span>
          <span>git apply format</span>
        </div>
        ${lines.map(line => {
          let cls = 'diff-line';
          if (line.startsWith('---') || line.startsWith('+++')) cls += ' diff-header-file';
          else if (line.startsWith('@@')) cls += ' diff-line-hunk';
          else if (line.startsWith('-')) cls += ' diff-line-del';
          else if (line.startsWith('+')) cls += ' diff-line-add';
          return `<div class="${cls}">${this.escapeHtml(line)}</div>`;
        }).join('')}
      </div>
    `;
  }


  // ─── Fix Prompt ───

  renderFixPrompt(prompt, fixPlan) {
    // Fix plan
    const section = document.getElementById('fix-prompt-section');
    if (!section) return;

    let planHtml = '';
    if (fixPlan && fixPlan.length > 0) {
      planHtml = `
        <div style="margin-bottom:16px;">
          <span class="type-label" style="display:block; margin-bottom:8px;">Fix plan</span>
          <div class="fix-plan-list">
            ${fixPlan.map(item => `
              <div class="fix-plan-item">
                <span class="fix-plan-num">${item.priority}</span>
                <span class="fix-plan-title">${this.escapeHtml(item.title)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    section.innerHTML = `
      ${planHtml}
      <div>
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
          <span class="fix-prompt-label">Hand this to your coding tool</span>
          <div style="display:flex; gap:12px; align-items:center;">
            <button id="btn-download-report" type="button" class="btn-text" style="font-size:12px; color:var(--ink-2); text-decoration:underline;">Download report (.md)</button>
            <button id="btn-copy-prompt" type="button" class="copy-btn">Copy</button>
          </div>
        </div>
        <pre id="fix-prompt-text" class="fix-prompt-box font-mono">${this.escapeHtml(prompt || '')}</pre>
      </div>
    `;

    // Re-bind buttons
    const copyBtn = document.getElementById('btn-copy-prompt');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => this.copyPrompt());
    }
    const dlBtn = document.getElementById('btn-download-report');
    if (dlBtn) {
      dlBtn.addEventListener('click', () => this.downloadReport());
    }
  }


  // ─── Model info ───

  renderModelInfo(model) {
    if (!this.modelInfoFooter || !model) return;
    this.modelInfoFooter.innerHTML = `
      Model: <strong>${this.escapeHtml(model.name)}</strong> · ${this.escapeHtml(model.license || 'open weights')} · ${(model.served_by || 'local').toLowerCase()}
    `;
  }


  // ─── Patch selection ───

  updatePatchSelectionCounter() {
    const countEl = document.getElementById('repo-selected-count');
    if (!countEl) return;

    const verifiedCount = (this.currentData && this.currentData.findings)
      ? this.currentData.findings.filter(f => f.fix && f.fix.validated).length
      : 0;

    countEl.textContent = `${this.selectedFixIds.size} selected`;
  }

  downloadPatch() {
    if (!this.currentData) return;
    const jobId = this.currentData.run_id || 'demo-repo-vibecheck';
    const ids = Array.from(this.selectedFixIds).join(',');

    if (this.selectedFixIds.size === 0) {
      alert("Select at least one fix to include in the patch.");
      return;
    }

  // ─── Ignored Issues Management ───

  // Retrieve list of ignored finding IDs from localStorage
  getIgnoredIds() {
    try {
      const stored = localStorage.getItem('vibecheck_ignored_ids');
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error('Failed to parse ignored IDs:', e);
      return [];
    }
  }

  // Persist ignored IDs to localStorage
  setIgnoredIds(ids) {
    try {
      localStorage.setItem('vibecheck_ignored_ids', JSON.stringify(ids));
    } catch (e) {
      console.error('Failed to store ignored IDs:', e);
    }
  }

  // Check if a finding is ignored
  isFindingIgnored(id) {
    const ignored = this.getIgnoredIds();
    return ignored.includes(id);
  }

  // Initialize the ignored header click behavior
  initIgnoredHeader() {
    const ignoredHeader = document.getElementById('ignored-header');
    if (!ignoredHeader) return;
    ignoredHeader.addEventListener('click', () => {
      // Toggle display of ignored findings list (simple alert for now)
      const ignored = this.getIgnoredIds();
      if (ignored.length === 0) {
        alert('No ignored issues.');
        return;
      }
      alert('Ignored issue IDs: ' + ignored.join(', '));
    });
    // Ensure header reflects current ignored count
    this.updateIgnoredHeader();
  }

  // Update the ignored count in the UI
  updateIgnoredHeader() {
    const ignoredCount = this.getIgnoredIds().length;
    const ignoredLabel = document.getElementById('ignored-header');
    if (ignoredLabel) {
      ignoredLabel.innerHTML = `🗑️ ${ignoredCount} ignored`;
    }
  }

    const downloadUrl = `/api/jobs/${jobId}/patch?ids=${encodeURIComponent(ids)}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `vibecheck-${jobId}.patch`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    // Also update ignored count UI after any patch operation
    this.updateIgnoredHeader();
  }

  async downloadReport() {
    if (!this.currentData) return;
    try {
      const resp = await fetch('/api/report.md', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.currentData)
      });
      if (!resp.ok) {
        throw new Error(`Server returned ${resp.status}`);
      }
      const text = await resp.text();
      const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const runId = this.currentData.run_id || 'report';
      a.download = `vibecheck-${runId}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download report:', err);
      alert('Failed to download report: ' + err.message);
    }
  }


  // ─── Card interaction ───

  toggleCard(id) {
    if (this.expandedCards.has(id)) {
      this.expandedCards.delete(id);
    } else {
      this.expandedCards.add(id);
    }
    const details = document.getElementById(`details-${id}`);
    const card = document.getElementById(`card-${id}`);
    const isExpanded = this.expandedCards.has(id);

    if (details) details.classList.toggle('expanded', isExpanded);
    if (card) {
      const btn = card.querySelector('.btn-toggle');
      if (btn) btn.textContent = isExpanded ? 'Collapse' : 'Details';
    }
  }

  highlightCard(id, shouldScroll) {
    document.querySelectorAll('.finding-note').forEach(c => {
      c.classList.toggle('active', c.dataset.id === id);
    });

    if (shouldScroll) {
      const target = document.getElementById(`card-${id}`);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }

  clearSelection() {
    this.overlay.clear();
    document.querySelectorAll('.finding-note').forEach(c => c.classList.remove('active'));
  }

  clear() {
    this.currentData = null;
    this.overlay.clear();
    const btnHeaderDownload = document.getElementById('btn-header-download-report');
    if (btnHeaderDownload) btnHeaderDownload.classList.add('hidden');
    // Reset ignored list UI
    this.updateIgnoredHeader();
    if (this.summaryCountsEl) this.summaryCountsEl.innerHTML = '';
    if (this.scoresContainerEl) this.scoresContainerEl.innerHTML = '';
    if (this.reportLayoutEl) this.reportLayoutEl.innerHTML = '';
    if (this.fixPromptSection) this.fixPromptSection.innerHTML = '';
    if (this.modelInfoFooter) this.modelInfoFooter.innerHTML = '';
    // Clear ignored UI count
    this.updateIgnoredHeader();
  }

  copyPrompt() {
    const textEl = document.getElementById('fix-prompt-text');
    const text = textEl ? textEl.textContent : "";
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
      const btn = document.getElementById('btn-copy-prompt');
      if (btn) {
        btn.textContent = 'Copied';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = 'Copy';
          btn.classList.remove('copied');
        }, 2000);
      }
    }).catch(err => {
      console.error("Clipboard copy failed:", err);
    });
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}
