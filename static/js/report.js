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
    this.currentMode = 'screenshot';
    this.activeFilter = { severity: 'all', category: 'all' };
    this.activeFileFilter = 'all';
    this.expandedCards = new Set();
    this.selectedFixIds = new Set();

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
    this.modelInfoFooter = document.getElementById('model-info-footer');
    this.fixPromptSection = document.getElementById('fix-prompt-section');
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

    // Overlay marker → finding card sync
    this.overlay.onSelect((id, shouldScroll) => {
      this.highlightCard(id, shouldScroll);
    });

    // Esc clears selection
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.clearSelection();
      }
    });
  }

  renderReport(data, imageSrc, mode = 'screenshot') {
    this.currentData = data;
    this.currentMode = (data.mode === 'repo' || mode === 'repo') ? 'repo' : 'screenshot';
    this.expandedCards.clear();
    this.activeFilter = { severity: 'all', category: 'all' };
    this.activeFileFilter = 'all';

    const isRepo = this.currentMode === 'repo';

    // Show header actions
    const btnNewCheck = document.getElementById('btn-new-check');
    const btnHeaderCopy = document.getElementById('btn-header-copy-fix');
    if (btnNewCheck) btnNewCheck.classList.remove('hidden');
    if (btnHeaderCopy) btnHeaderCopy.classList.remove('hidden');

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

    this.summaryCountsEl.innerHTML = `
      <span class="summary-total">${total} issues</span>
      <span class="summary-breakdown">
        <span class="summary-item"><span class="sev-mark sev-mark-critical">${SEVERITY_MARKS.Critical.mark}</span> ${counts.critical} critical</span>
        <span class="summary-item"><span class="sev-mark sev-mark-high">${SEVERITY_MARKS.High.mark}</span> ${counts.high} high</span>
        <span class="summary-item"><span class="sev-mark sev-mark-medium">${SEVERITY_MARKS.Medium.mark}</span> ${counts.medium} medium</span>
        <span class="summary-item"><span class="sev-mark sev-mark-low">${SEVERITY_MARKS.Low.mark}</span> ${counts.low} low</span>
        ${verifiedLabel}
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

    const filtered = this.currentData.findings.filter(f => {
      const matchSev = this.activeFilter.severity === 'all' || f.severity === this.activeFilter.severity;
      let matchFile = true;
      if (isRepo && this.activeFileFilter !== 'all') {
        matchFile = f.code_location && f.code_location.file === this.activeFileFilter;
      }
      return matchSev && matchFile;
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
          <button id="btn-copy-prompt" type="button" class="copy-btn">Copy</button>
        </div>
        <pre id="fix-prompt-text" class="fix-prompt-box font-mono">${this.escapeHtml(prompt || '')}</pre>
      </div>
    `;

    // Re-bind copy button
    const copyBtn = document.getElementById('btn-copy-prompt');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => this.copyPrompt());
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

    const downloadUrl = `/api/jobs/${jobId}/patch?ids=${encodeURIComponent(ids)}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `vibecheck-${jobId}.patch`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
    if (this.summaryCountsEl) this.summaryCountsEl.innerHTML = '';
    if (this.scoresContainerEl) this.scoresContainerEl.innerHTML = '';
    if (this.reportLayoutEl) this.reportLayoutEl.innerHTML = '';
    if (this.fixPromptSection) this.fixPromptSection.innerHTML = '';
    if (this.modelInfoFooter) this.modelInfoFooter.innerHTML = '';
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
