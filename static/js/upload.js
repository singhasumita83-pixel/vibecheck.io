// VibeCheck UI — Upload, Repo & Analysis State Management (DESIGN V2)

export class UploadManager {
  constructor(options) {
    this.onAnalysisComplete = options.onAnalysisComplete;
    this.onStartAnalyzing = options.onStartAnalyzing;
    this.onCancel = options.onCancel;
    this.onError = options.onError;

    this.currentMode = 'screenshot'; // 'screenshot' | 'repo'
    this.selectedFile = null;
    this.currentImageSrc = null;
    this.activeJobPollTimer = null;
    this.activeAbortController = null;

    this.initElements();
    this.bindEvents();
  }

  initElements() {
    // Mode Tabs & Panels
    this.tabScreenshot = document.getElementById('tab-mode-screenshot');
    this.tabRepo = document.getElementById('tab-mode-repo');
    this.panelScreenshot = document.getElementById('panel-screenshot');
    this.panelRepo = document.getElementById('panel-repo');

    // Screenshot elements
    this.dropzone = document.getElementById('upload-dropzone');
    this.fileInput = document.getElementById('file-input');
    this.dropzoneEmpty = document.getElementById('dropzone-empty');
    this.dropzonePreview = document.getElementById('dropzone-preview');
    this.previewImg = document.getElementById('preview-image');
    this.previewFilename = document.getElementById('preview-filename');
    this.previewFilesize = document.getElementById('preview-filesize');
    this.changeFileBtn = document.getElementById('btn-change-file');
    this.removeFileBtn = document.getElementById('btn-remove-file');
    this.btnAnalyze = document.getElementById('btn-analyze');
    this.dropzoneError = document.getElementById('dropzone-error');

    // Repo elements
    this.repoUrlInput = document.getElementById('repo-url-input');
    this.repoBranchInput = document.getElementById('repo-branch-input');
    this.repoModelSelect = document.getElementById('repo-model-select');
    this.customModelFields = document.getElementById('custom-model-fields');
    this.customBaseUrl = document.getElementById('custom-base-url');
    this.customModelName = document.getElementById('custom-model-name');
    this.customApiKey = document.getElementById('custom-api-key');
    this.repoError = document.getElementById('repo-error');
    this.btnScanRepo = document.getElementById('btn-scan-repo');

    // Shared inputs
    this.personaSelect = document.getElementById('persona-select');
    this.goalInput = document.getElementById('goal-input');

    // Analyzing screen elements
    this.analyzingScreen = document.getElementById('analyzing-screen');
    this.analyzingThumbnail = document.getElementById('analyzing-thumbnail');
    this.analyzingThumbBox = document.getElementById('analyzing-thumb-box');
    this.stageList = document.getElementById('analysis-stages');
    this.repoProgressCounter = document.getElementById('repo-progress-counter');
    this.filesScannedCount = document.getElementById('files-scanned-count');
    this.cancelAnalysisBtn = document.getElementById('btn-cancel-analysis');
  }

  bindEvents() {
    // Mode Switcher Tabs
    if (this.tabScreenshot) {
      this.tabScreenshot.addEventListener('click', () => this.switchMode('screenshot'));
    }
    if (this.tabRepo) {
      this.tabRepo.addEventListener('click', () => this.switchMode('repo'));
    }

    // Custom model dropdown toggle
    if (this.repoModelSelect) {
      this.repoModelSelect.addEventListener('change', () => {
        if (this.customModelFields) {
          this.customModelFields.classList.toggle('hidden', this.repoModelSelect.value !== 'custom');
        }
      });
    }

    // Repo scan button
    if (this.btnScanRepo) {
      this.btnScanRepo.addEventListener('click', () => this.startRepoAnalysis());
    }

    // Dropzone click & Change button
    if (this.dropzone) {
      this.dropzone.addEventListener('click', (e) => {
        // If clicking remove button, don't open file picker
        if (e.target === this.removeFileBtn || e.target.closest('#btn-remove-file')) {
          return;
        }
        if (this.fileInput) {
          this.fileInput.value = '';
          this.fileInput.click();
        }
      });

      this.dropzone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          if (this.fileInput) {
            this.fileInput.value = '';
            this.fileInput.click();
          }
        }
      });

      // Drag and Drop
      ['dragenter', 'dragover'].forEach(eventName => {
        this.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.dropzone.classList.add('dragover');
        });
      });

      ['dragleave', 'drop'].forEach(eventName => {
        this.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.dropzone.classList.remove('dragover');
        });
      });

      this.dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
          this.handleFile(dt.files[0]);
        }
      });
    }

    if (this.changeFileBtn) {
      this.changeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (this.fileInput) {
          this.fileInput.value = '';
          this.fileInput.click();
        }
      });
    }

    if (this.cancelAnalysisBtn) {
      this.cancelAnalysisBtn.addEventListener('click', () => {
        this.cancelAnalysis();
      });
    }

    // Clipboard paste support
    document.addEventListener('paste', (e) => {
      if (this.currentMode !== 'screenshot') return;
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault();
          const file = item.getAsFile();
          if (file) this.handleFile(file);
          break;
        }
      }
    });

    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          this.handleFile(e.target.files[0]);
        }
      });
    }

    if (this.removeFileBtn) {
      this.removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.clearFile();
      });
    }

    if (this.btnAnalyze) {
      this.btnAnalyze.addEventListener('click', () => {
        this.startScreenshotAnalysis();
      });
    }
  }

  switchMode(mode) {
    this.currentMode = mode;
    if (this.tabScreenshot && this.tabRepo) {
      this.tabScreenshot.classList.toggle('active', mode === 'screenshot');
      this.tabScreenshot.setAttribute('aria-selected', mode === 'screenshot');
      this.tabRepo.classList.toggle('active', mode === 'repo');
      this.tabRepo.setAttribute('aria-selected', mode === 'repo');
    }
    if (this.panelScreenshot && this.panelRepo) {
      this.panelScreenshot.classList.toggle('hidden', mode !== 'screenshot');
      this.panelRepo.classList.toggle('hidden', mode !== 'repo');
    }
    this.clearError();
  }

  handleFile(file) {
    this.clearError();

    if (!file.type.match(/^image\/(png|jpeg|webp)$/)) {
      this.showError("Please upload a PNG or JPG image.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      this.showError("File size exceeds 5 MB limit.");
      return;
    }

    this.selectedFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
      this.currentImageSrc = e.target.result;
      if (this.previewImg) this.previewImg.src = this.currentImageSrc;
      if (this.previewFilename) this.previewFilename.textContent = file.name;
      if (this.previewFilesize) {
        const kb = (file.size / 1024).toFixed(1);
        this.previewFilesize.textContent = `${kb} KB`;
      }
      if (this.dropzoneEmpty) this.dropzoneEmpty.classList.add('hidden');
      if (this.dropzonePreview) this.dropzonePreview.classList.remove('hidden');
      if (this.btnAnalyze) this.btnAnalyze.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  clearFile() {
    this.selectedFile = null;
    this.currentImageSrc = null;
    if (this.fileInput) this.fileInput.value = "";
    if (this.previewImg) this.previewImg.src = "";
    if (this.dropzoneEmpty) this.dropzoneEmpty.classList.remove('hidden');
    if (this.dropzonePreview) this.dropzonePreview.classList.add('hidden');
    if (this.btnAnalyze) this.btnAnalyze.disabled = true;
    if (this.analyzingThumbnail) {
      this.analyzingThumbnail.src = "";
      this.analyzingThumbnail.classList.add('hidden');
    }
    this.clearError();
  }

  cancelAnalysis() {
    if (this.activeAbortController) {
      try {
        this.activeAbortController.abort();
      } catch (e) {}
      this.activeAbortController = null;
    }
    if (this.activeJobPollTimer) {
      clearInterval(this.activeJobPollTimer);
      this.activeJobPollTimer = null;
    }
    if (this.onCancel) {
      this.onCancel();
    }
  }

  showError(message) {
    if (this.dropzoneError) {
      this.dropzoneError.textContent = message;
      this.dropzoneError.classList.remove('hidden');
    }
    if (this.dropzone) {
      this.dropzone.classList.add('has-error');
    }
  }

  clearError() {
    if (this.dropzoneError) {
      this.dropzoneError.textContent = "";
      this.dropzoneError.classList.add('hidden');
    }
    if (this.dropzone) {
      this.dropzone.classList.remove('has-error');
    }
  }

  async startScreenshotAnalysis() {
    if (!this.selectedFile) return;

    this.activeAbortController = new AbortController();
    const signal = this.activeAbortController.signal;

    if (this.repoProgressCounter) this.repoProgressCounter.classList.add('hidden');

    if (this.analyzingThumbnail && this.currentImageSrc) {
      this.analyzingThumbnail.src = this.currentImageSrc;
      this.analyzingThumbnail.classList.remove('hidden');
    }

    const stages = [
      { id: 'stage-1', text: 'read the screen' },
      { id: 'stage-2', text: 'finding issues' },
      { id: 'stage-3', text: 'verifying' },
      { id: 'stage-4', text: 'writing fixes' }
    ];

    this.resetStages(stages);
    this.advanceStage(0, stages);

    if (this.onStartAnalyzing) {
      this.onStartAnalyzing();
    }

    const formData = new FormData();
    formData.append('image', this.selectedFile);
    formData.append('persona', this.personaSelect ? this.personaSelect.value : '');
    formData.append('goal', this.goalInput ? this.goalInput.value : '');

    try {
      const stageTimer1 = setTimeout(() => this.advanceStage(1, stages), 400);
      const stageTimer2 = setTimeout(() => this.advanceStage(2, stages), 1200);
      const stageTimer3 = setTimeout(() => this.advanceStage(3, stages), 2200);

      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
        signal: signal
      });

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);

      stages.forEach((_, i) => this.markStageComplete(i));

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || "Analysis request failed.");
      }

      const result = await response.json();
      setTimeout(() => {
        if (this.onAnalysisComplete) {
          this.onAnalysisComplete(result, this.currentImageSrc, 'screenshot');
        }
      }, 400);

    } catch (err) {
      if (err.name === 'AbortError') {
        console.log("[UploadManager] Analysis aborted by user.");
        return;
      }
      console.error("[UploadManager] Analysis error:", err);
      if (this.onError) {
        this.onError(err.message || "Failed to analyze screenshot.");
      }
    } finally {
      this.activeAbortController = null;
    }
  }

  async startRepoAnalysis(customRepoUrl = null) {
    const repoUrl = (customRepoUrl || (this.repoUrlInput ? this.repoUrlInput.value : '')).trim();
    if (!repoUrl) {
      this.showRepoError("Please enter a public GitHub repository URL.");
      return;
    }
    if (!repoUrl.startsWith("https://github.com/")) {
      this.showRepoError("Only public GitHub repositories (https://github.com/owner/repo) are supported.");
      return;
    }

    this.clearRepoError();

    const branch = this.repoBranchInput ? this.repoBranchInput.value.trim() : '';
    const persona = this.personaSelect ? this.personaSelect.value : '';
    const goal = this.goalInput ? this.goalInput.value : '';

    let modelConf = null;
    if (this.repoModelSelect && this.repoModelSelect.value === 'custom') {
      const baseUrl = this.customBaseUrl ? this.customBaseUrl.value.trim() : '';
      const modelName = this.customModelName ? this.customModelName.value.trim() : '';
      const apiKey = this.customApiKey ? this.customApiKey.value.trim() : '';
      if (!baseUrl) {
        this.showRepoError("Base URL is required when using a custom model endpoint.");
        return;
      }
      modelConf = { base_url: baseUrl, model: modelName || "custom-model", api_key: apiKey };
    }

    if (this.onStartAnalyzing) {
      this.onStartAnalyzing();
    }

    if (this.repoProgressCounter) this.repoProgressCounter.classList.remove('hidden');
    if (this.filesScannedCount) this.filesScannedCount.textContent = "0";

    // Show repo name instead of thumbnail
    if (this.analyzingThumbnail) {
      this.analyzingThumbnail.classList.add('hidden');
    }

    const repoStages = [
      { id: 'stage-1', text: 'cloning repository' },
      { id: 'stage-2', text: 'scanning UI files' },
      { id: 'stage-3', text: 'reviewing with model' },
      { id: 'stage-4', text: 'synthesizing fixes' },
      { id: 'stage-5', text: 'validating patches' }
    ];

    this.resetStages(repoStages);
    this.advanceStage(0, repoStages);

    try {
      const payload = {
        repo_url: repoUrl,
        branch: branch,
        persona: persona,
        goal: goal,
        model: modelConf
      };

      const response = await fetch('/api/analyze-repo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || "Failed to initialize repository analysis.");
      }

      const { job_id } = await response.json();
      this.pollRepoJob(job_id, repoStages);

    } catch (err) {
      console.error("[UploadManager] Repo analysis start error:", err);
      if (this.onError) {
        this.onError(err.message || "Failed to start repository analysis.");
      }
    }
  }

  pollRepoJob(jobId, repoStages) {
    if (this.activeJobPollTimer) clearInterval(this.activeJobPollTimer);

    const stageMap = {
      'cloning': 0,
      'scanning': 1,
      'reviewing': 2,
      'fixing': 3,
      'validating': 4,
      'done': 5
    };

    this.activeJobPollTimer = setInterval(async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) {
          clearInterval(this.activeJobPollTimer);
          throw new Error("Lost connection to background analysis job.");
        }

        const job = await res.json();

        if (job.files_scanned && this.filesScannedCount) {
          this.filesScannedCount.textContent = `${job.files_scanned}${job.total_files ? ' / ' + job.total_files : ''}`;
        }

        const currentIdx = stageMap[job.stage] !== undefined ? stageMap[job.stage] : 0;
        if (currentIdx < repoStages.length) {
          this.advanceStage(currentIdx, repoStages);
        }

        if (job.status === 'done') {
          clearInterval(this.activeJobPollTimer);
          repoStages.forEach((_, i) => this.markStageComplete(i));

          setTimeout(() => {
            if (this.onAnalysisComplete) {
              this.onAnalysisComplete(job.result, null, 'repo');
            }
          }, 400);

        } else if (job.status === 'failed') {
          clearInterval(this.activeJobPollTimer);
          throw new Error(job.error || "Repository analysis failed.");
        }

      } catch (err) {
        clearInterval(this.activeJobPollTimer);
        console.error("[UploadManager] Poll error:", err);
        if (this.onError) {
          this.onError(err.message);
        }
      }
    }, 450);
  }

  showRepoError(msg) {
    if (this.repoError) {
      this.repoError.textContent = msg;
      this.repoError.classList.remove('hidden');
    }
  }

  clearRepoError() {
    if (this.repoError) {
      this.repoError.textContent = "";
      this.repoError.classList.add('hidden');
    }
  }

  // Stage rendering: plain mono checklist, no spinners
  resetStages(stages) {
    if (!this.stageList) return;
    this.stageList.innerHTML = stages.map((s) => `
      <div id="${s.id}" class="stage-line">
        <span class="stage-icon"> </span>
        <span class="stage-label">${s.text}</span>
      </div>
    `).join('');
  }

  advanceStage(stageIdx, stages) {
    for (let i = 0; i < stageIdx; i++) {
      this.markStageComplete(i);
    }
    const current = document.getElementById(stages[stageIdx]?.id);
    if (current) {
      current.classList.add('current');
      current.classList.remove('done');
      const icon = current.querySelector('.stage-icon');
      if (icon) icon.textContent = '…';
    }
  }

  markStageComplete(stageIdx) {
    const el = document.getElementById(`stage-${stageIdx + 1}`);
    if (el) {
      el.classList.remove('current');
      el.classList.add('done');
      const icon = el.querySelector('.stage-icon');
      if (icon) icon.textContent = '✓';
    }
  }
}
