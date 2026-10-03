// VibeCheck UI — Main Application Orchestrator (DESIGN V2: Red Pen)

import { UploadManager } from './upload.js';
import { OverlayManager } from './overlay.js';
import { ReportManager } from './report.js';

class App {
  constructor() {
    this.currentScreen = 'upload';
    this.initTheme();
    this.initElements();
    this.initManagers();
    this.bindGlobalEvents();
    this.renderSampleMarkers();
  }

  // ─── Theme ───

  initTheme() {
    const savedTheme = localStorage.getItem('vibecheck_theme');
    if (savedTheme) {
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }
    this.updateThemeToggleLabel();
  }

  toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('vibecheck_theme', next);
    this.updateThemeToggleLabel();
  }

  updateThemeToggleLabel() {
    const btn = document.getElementById('btn-theme-toggle');
    if (!btn) return;
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    btn.textContent = current === 'dark' ? 'Light' : 'Dark';
    btn.setAttribute('title', `Switch to ${current === 'dark' ? 'light' : 'dark'} mode`);
  }


  // ─── Elements ───

  initElements() {
    this.screenUpload = document.getElementById('upload-screen');
    this.screenAnalyzing = document.getElementById('analyzing-screen');
    this.screenReport = document.getElementById('report-screen');
    this.btnThemeToggle = document.getElementById('btn-theme-toggle');
    this.btnNewCheck = document.getElementById('btn-new-check');
    this.toastEl = document.getElementById('app-toast');
    this.toastMessage = document.getElementById('toast-message');
    this.toastRetryBtn = document.getElementById('btn-toast-retry');

    // Demo menu
    this.demoTrigger = document.getElementById('btn-demo-trigger');
    this.demoMenu = document.getElementById('demo-menu');
    this.btnTryDemo = document.getElementById('btn-try-demo');
    this.btnTryRepoDemo = document.getElementById('btn-try-repo-demo');
  }


  // ─── Managers ───

  initManagers() {
    // Create a dummy overlay container for init; will be replaced on report render
    const dummyContainer = document.createElement('div');
    const dummyImg = document.createElement('img');
    this.overlayManager = new OverlayManager(dummyContainer, dummyImg);
    this.reportManager = new ReportManager(this.overlayManager);

    this.uploadManager = new UploadManager({
      onStartAnalyzing: () => this.showScreen('analyzing'),
      onAnalysisComplete: (result, imageSrc, mode) => {
        this.reportManager.renderReport(result, imageSrc, mode);
        this.showScreen('report');
      },
      onCancel: () => {
        this.showScreen('upload');
      },
      onError: (errMsg) => {
        this.showToast(errMsg, true);
        this.showScreen('upload');
      }
    });
  }


  // ─── Events ───

  bindGlobalEvents() {
    // Theme toggle
    if (this.btnThemeToggle) {
      this.btnThemeToggle.addEventListener('click', () => this.toggleTheme());
    }

    // Demo menu toggle
    if (this.demoTrigger && this.demoMenu) {
      this.demoTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        this.demoMenu.classList.toggle('open');
      });

      // Close on outside click
      document.addEventListener('click', () => {
        this.demoMenu.classList.remove('open');
      });
    }

    // Demo buttons
    if (this.btnTryDemo) {
      this.btnTryDemo.addEventListener('click', () => {
        this.demoMenu.classList.remove('open');
        this.loadDemo();
      });
    }

    if (this.btnTryRepoDemo) {
      this.btnTryRepoDemo.addEventListener('click', () => {
        this.demoMenu.classList.remove('open');
        this.loadRepoDemo();
      });
    }

    // New check
    if (this.btnNewCheck) {
      this.btnNewCheck.addEventListener('click', () => {
        this.uploadManager.clearFile();
        this.reportManager.clear();
        this.btnNewCheck.classList.add('hidden');
        const headerCopy = document.getElementById('btn-header-copy-fix');
        if (headerCopy) headerCopy.classList.add('hidden');
        this.showScreen('upload');
      });
    }

    // Brand logo → home
    const brandLogo = document.querySelector('.brand-logo');
    if (brandLogo) {
      brandLogo.addEventListener('click', () => {
        this.uploadManager.clearFile();
        this.reportManager.clear();
        if (this.btnNewCheck) this.btnNewCheck.classList.add('hidden');
        const headerCopy = document.getElementById('btn-header-copy-fix');
        if (headerCopy) headerCopy.classList.add('hidden');
        this.showScreen('upload');
      });
    }
  }


  // ─── Screen management ───

  showScreen(screenName) {
    this.currentScreen = screenName;
    this.screenUpload.classList.toggle('hidden', screenName !== 'upload');
    this.screenAnalyzing.classList.toggle('hidden', screenName !== 'analyzing');
    this.screenReport.classList.toggle('hidden', screenName !== 'report');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }


  // ─── Sample markers on landing (stamp in once) ───

  renderSampleMarkers() {
    const wrap = document.getElementById('sample-img-wrap');
    if (!wrap) return;

    const sampleFindings = [
      { num: '①', x: 65, y: 25, sev: 'High' },
      { num: '②', x: 40, y: 60, sev: 'High' }
    ];

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    sampleFindings.forEach((f, i) => {
      const el = document.createElement('div');
      el.className = 'marker-pin';
      el.dataset.sev = f.sev;
      el.textContent = (i + 1).toString();
      el.style.position = 'absolute';
      el.style.left = `${f.x}%`;
      el.style.top = `${f.y}%`;
      el.style.pointerEvents = 'none';

      if (!prefersReduced) {
        el.style.opacity = '0';
        setTimeout(() => {
          el.classList.add('stamp-in');
          el.style.opacity = '';
        }, 300 + i * 60);
      }

      wrap.appendChild(el);
    });
  }


  // ─── Demo loading ───

  async loadDemo() {
    this.showScreen('analyzing');

    const demoScreenshotSrc = '/api/demo/screenshot';
    const thumb = document.getElementById('analyzing-thumbnail');
    if (thumb) {
      thumb.src = demoScreenshotSrc;
      thumb.classList.remove('hidden');
    }

    const stages = [
      { id: 'stage-1', text: 'read the screen' },
      { id: 'stage-2', text: 'finding issues' },
      { id: 'stage-3', text: 'verifying' },
      { id: 'stage-4', text: 'writing fixes' }
    ];
    this.uploadManager.resetStages(stages);

    this.uploadManager.advanceStage(0, stages);
    await new Promise(r => setTimeout(r, 120));
    this.uploadManager.advanceStage(1, stages);
    await new Promise(r => setTimeout(r, 150));
    this.uploadManager.advanceStage(2, stages);
    await new Promise(r => setTimeout(r, 150));
    this.uploadManager.advanceStage(3, stages);
    await new Promise(r => setTimeout(r, 120));

    stages.forEach((_, i) => this.uploadManager.markStageComplete(i));

    try {
      const response = await fetch('/api/demo');
      if (!response.ok) throw new Error("Could not fetch demo results.");
      const demoData = await response.json();

      this.reportManager.renderReport(demoData, demoScreenshotSrc, 'screenshot');
      this.showScreen('report');
    } catch (e) {
      this.showToast("Failed to load demo: " + e.message, true);
      this.showScreen('upload');
    }
  }

  async loadRepoDemo() {
    this.showScreen('analyzing');

    const thumb = document.getElementById('analyzing-thumbnail');
    if (thumb) thumb.classList.add('hidden');

    const counter = document.getElementById('repo-progress-counter');
    const filesCount = document.getElementById('files-scanned-count');
    if (counter) counter.classList.remove('hidden');
    if (filesCount) filesCount.textContent = "2 / 2";

    const stages = [
      { id: 'stage-1', text: 'cloning repository' },
      { id: 'stage-2', text: 'scanning UI files' },
      { id: 'stage-3', text: 'reviewing with model' },
      { id: 'stage-4', text: 'synthesizing fixes' },
      { id: 'stage-5', text: 'validating patches' }
    ];
    this.uploadManager.resetStages(stages);

    this.uploadManager.advanceStage(0, stages);
    await new Promise(r => setTimeout(r, 100));
    this.uploadManager.advanceStage(1, stages);
    await new Promise(r => setTimeout(r, 120));
    this.uploadManager.advanceStage(2, stages);
    await new Promise(r => setTimeout(r, 120));
    this.uploadManager.advanceStage(3, stages);
    await new Promise(r => setTimeout(r, 120));
    this.uploadManager.advanceStage(4, stages);
    await new Promise(r => setTimeout(r, 100));

    stages.forEach((_, i) => this.uploadManager.markStageComplete(i));

    try {
      const response = await fetch('/api/demo-repo');
      if (!response.ok) throw new Error("Could not fetch repo demo results.");
      const demoData = await response.json();

      this.reportManager.renderReport(demoData, null, 'repo');
      this.showScreen('report');
    } catch (e) {
      this.showToast("Failed to load repo demo: " + e.message, true);
      this.showScreen('upload');
    }
  }


  // ─── Toast ───

  showToast(message, isRetryable = false) {
    if (!this.toastEl) return;
    this.toastMessage.textContent = message;
    if (this.toastRetryBtn) {
      this.toastRetryBtn.classList.toggle('hidden', !isRetryable);
      this.toastRetryBtn.onclick = () => {
        this.hideToast();
        if (this.uploadManager.currentMode === 'repo') {
          this.uploadManager.startRepoAnalysis();
        } else {
          this.uploadManager.startScreenshotAnalysis();
        }
      };
    }
    this.toastEl.classList.remove('hidden');
    setTimeout(() => this.hideToast(), 6000);
  }

  hideToast() {
    if (this.toastEl) this.toastEl.classList.add('hidden');
  }
}

// Bootstrap
document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});
