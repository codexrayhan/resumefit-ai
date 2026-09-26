document.addEventListener('DOMContentLoaded', () => {

  const stateCommandCenter    = document.getElementById('state-command-center');
  const stateIdeCanvas        = document.getElementById('state-ide-canvas');

  const analysisForm          = document.getElementById('analysis-form');
  const dropzoneLabel         = document.getElementById('dropzone-label');
  const fileInput             = document.getElementById('resume-upload');
  const jdInput               = document.getElementById('jd-input');

  const demoModeBtn           = document.getElementById('demo-mode-btn');
  const terminalLoader        = document.getElementById('terminal-loader');
  const terminalOutput        = document.getElementById('terminal-output');
  const resumeContenteditable = document.getElementById('resume-contenteditable');
  const recalcBtn             = document.getElementById('recalc-btn');
  const jdPaneContent         = document.getElementById('jd-pane-content');
  const commitProgressFill    = document.getElementById('commit-progress-fill');
  const drawerTitle           = document.getElementById('drawer-title');

  const scoreElement          = document.getElementById('final-score');
  const header                = document.querySelector('.global-header');
  const cmdKTrigger           = document.querySelector('.cmd-k-trigger');
  const drawerToggle          = document.querySelector('.drawer-toggle');
  const drawerContent         = document.querySelector('.drawer-content');

  // Prevent XSS by escaping special characters
  function escapeHtml(str) {
    return str
      .replace(/&/g,  '&amp;')
      .replace(/</g,  '&lt;')
      .replace(/>/g,  '&gt;')
      .replace(/"/g,  '&quot;')
      .replace(/'/g,  '&#39;');
  }

  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Converts "INFORMATION-TECHNOLOGY" to "Information Technology"
  function formatRoleName(role) {
    return role.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
  }

  function getScoreColor(score) {
    if (score >= 80) return '#16A34A';
    if (score >= 60) return '#2563EB';
    if (score >= 40) return '#D97706';
    return '#DC2626';
  }

  function getRoleColor(confidence) {
    if (confidence >= 80) return '#16A34A';
    if (confidence >= 60) return '#2563EB';
    if (confidence >= 40) return '#D97706';
    return '#DC2626';
  }

  function getSignal(score) {
    if (score >= 80) return { label: 'HIGH_CONFIDENCE', cls: 'signal-high' };
    if (score >= 60) return { label: 'MODERATE',        cls: 'signal-moderate' };
    if (score >= 40) return { label: 'LOW',             cls: 'signal-warning' };
    return               { label: 'CRITICAL_GAP',   cls: 'signal-warning' };
  }

  const analyzeBtn = document.getElementById('analyze-btn');
  const fileCardWrapper = document.getElementById('file-card-wrapper');
  const fileCardName = document.getElementById('file-card-name');
  const fileCardMeta = document.getElementById('file-card-meta');
  const btnRemoveFile = document.getElementById('btn-remove-file');

  // Detect Mac keyboard and update Cmd+K trigger label
  const cmdKeyIcon = document.getElementById('cmd-key-icon');
  const cmdKeyText = document.getElementById('cmd-key-text');
  if (cmdKeyIcon && cmdKeyText && /Mac/.test(navigator.userAgent)) {
    cmdKeyIcon.textContent = '⌘';
    cmdKeyText.textContent = ' K for commands';
  }

  const resetDropzoneUI = () => {
    if (fileInput) fileInput.value = '';
    const dropzoneContent = document.getElementById('dropzone-content');
    if (dropzoneContent) dropzoneContent.style.display = 'flex';
    if (dropzoneLabel) {
      dropzoneLabel.style.backgroundColor = '';
      dropzoneLabel.style.borderColor = '';
      dropzoneLabel.style.borderStyle = '';
      dropzoneLabel.style.padding = '';
    }
    if (fileCardWrapper) {
      fileCardWrapper.style.display = 'none';
    }
  };

  if (btnRemoveFile) {
    btnRemoveFile.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      resetDropzoneUI();
    });
  }

  const showFileErrorModal = () => {
    const container = document.querySelector('.dropzone-container');
    if (!container) return;

    const existing = container.querySelector('.file-error-modal');
    if (existing) existing.remove();

    const errorEl = document.createElement('div');
    errorEl.className = 'file-error-modal';
    errorEl.style.cssText = 'color: #DC2626; font-size: 0.875rem; font-weight: 500; margin-top: 8px; display: flex; align-items: center; gap: 6px;';
    errorEl.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>⚠ Upload Failed. Please try again.</span>
    `;

    container.appendChild(errorEl);

    setTimeout(() => {
      errorEl.style.transition = 'opacity 0.3s ease';
      errorEl.style.opacity = '0';
      setTimeout(() => errorEl.remove(), 300);
    }, 3000);
  };

  const handleFileParse = (file) => {
    if (!file) {
      resetDropzoneUI();
      return;
    }

    const validTypes = ['.pdf', '.docx', '.txt'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

    if (!validTypes.includes(ext)) {
      alert(`Invalid file type. Please upload ${validTypes.join(', ')}.`);
      resetDropzoneUI();
      return;
    }

    const dropzoneContent = document.getElementById('dropzone-content');
    if (dropzoneContent) dropzoneContent.style.display = 'none';
    if (dropzoneLabel) {
      dropzoneLabel.style.backgroundColor = 'var(--bg-surface-hover)';
      dropzoneLabel.style.borderColor = 'transparent';
      dropzoneLabel.style.borderStyle = 'solid';
      dropzoneLabel.style.padding = '16px 24px';
    }
    if (fileCardWrapper) {
      fileCardWrapper.style.display = 'flex';

      if (fileCardName) fileCardName.textContent = file.name;
      if (fileCardMeta) {
        const extName = ext.substring(1).toUpperCase();
        const sizeKB = Math.round(file.size / 1024);
        const sizeStr = sizeKB > 1024 ? (sizeKB / 1024).toFixed(1) + ' MB' : sizeKB + ' KB';
        fileCardMeta.textContent = `${extName} • ${sizeStr}`;
      }
    }

    jdInput.focus();
  };

  const adjustTextareaHeight = (el) => {
    el.style.height = 'auto';
    el.style.height = (el.scrollHeight) + 'px';
  };

  if (jdInput) {
    jdInput.addEventListener('input', function() {
      adjustTextareaHeight(this);
    });

    adjustTextareaHeight(jdInput);
  }

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  if (dropzoneLabel) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
      dropzoneLabel.addEventListener(ev, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(ev => {
      dropzoneLabel.addEventListener(ev, () => {
        dropzoneLabel.style.backgroundColor = 'var(--bg-surface-hover)';
        dropzoneLabel.style.borderColor = 'var(--accent-primary)';
      });
    });

    ['dragleave', 'drop'].forEach(ev => {
      dropzoneLabel.addEventListener(ev, () => {
        if (!fileInput || !fileInput.files.length) {
          dropzoneLabel.style.backgroundColor = '';
          dropzoneLabel.style.borderColor = '';
        }
      });
    });

    dropzoneLabel.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files.length) {
        if (fileInput) fileInput.files = files;
        handleFileParse(files[0]);
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', function () {
      if (this.files.length) {
        handleFileParse(this.files[0]);
      } else {
        resetDropzoneUI();
      }
    });
  }

  async function callAnalyzeAPI() {
    try {
      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('job_description', jdInput.value.trim());

      const response = await fetch('/analyze', { method: 'POST', body: formData });
      const data = await response.json();

      if (data.error) {
        showTerminalError(data.error);
        return null;
      }

      return data;
    } catch (err) {
      showTerminalError(err.message || 'Network error — please try again.');
      return null;
    }
  }

  async function callReanalyzeAPI(resumeText, jdText) {
    try {
      const response = await fetch('/reanalyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText, job_description: jdText })
      });
      const data = await response.json();

      if (data.error) {
        showTerminalError(data.error);
        return null;
      }

      return data;
    } catch (err) {
      showTerminalError(err.message || 'Network error — please try again.');
      return null;
    }
  }

  function showTerminalError(message) {
    if (terminalOutput) {
      const errEl = document.createElement('div');
      errEl.className = 'log-line';
      errEl.style.color = '#DC2626';
      errEl.textContent = '> ERROR: ' + message;
      terminalOutput.insertBefore(errEl, terminalOutput.querySelector('.cursor'));
    }
    setTimeout(() => resetToCommandCenter(), 2500);
  }

  const triggerTerminalLoader = () => {
    if (analysisForm) analysisForm.style.display = 'none';
    if (demoModeBtn)  demoModeBtn.style.display  = 'none';

    const trustSignal = document.querySelector('.trust-signal');
    if (trustSignal) trustSignal.style.display = 'none';

    if (terminalLoader) {
      terminalLoader.style.display = 'block';
      terminalLoader.setAttribute('aria-hidden', 'false');
    }

    const fileName = fileInput.files.length ? fileInput.files[0].name : 'source.pdf';

    const sequence = [
      `> INITIATING SECURE SESSION... [OK]`,
      `> PARSING ${fileName}... [OK]`,
      `> GENERATING semantic_embeddings... [OK]`,
      `> CALCULATING vector_distance... [OK]`
    ];

    terminalOutput.innerHTML = '<span class="cursor"></span>';
    let delay = 0;

    sequence.forEach((line, index) => {
      delay += 400 + Math.random() * 300;
      setTimeout(() => {
        const lineEl = document.createElement('div');
        lineEl.className = 'log-line';
        lineEl.textContent = line;
        if (terminalOutput) {
          terminalOutput.insertBefore(lineEl, terminalOutput.querySelector('.cursor'));
        }

        if (index === sequence.length - 1) {
          setTimeout(async () => {
            const data = await callAnalyzeAPI();
            if (data) transitionToIDE(data);
          }, 800);
        }
      }, delay);
    });
  };

  if (analysisForm) {
    analysisForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const submitBtn  = analysisForm.querySelector('.action-submit');
      const jdText     = jdInput ? jdInput.value.trim() : '';
      const wordCount  = jdText.split(/\s+/).filter(w => w.length > 0).length;

      if (!fileInput || !fileInput.files.length) {
        showFileErrorModal();
        return;
      }

      if (wordCount < 20) {
        alert(`System Error: Insufficient telemetry. Job description requires at least 20 words. (Currently: ${wordCount})`);
        if (jdInput) jdInput.focus();
        return;
      }

      if (submitBtn) {
        submitBtn.innerHTML = `<span class="btn-text">Analyzing context vectors...</span><span class="btn-shortcut">⟳</span>`;
        submitBtn.style.opacity = '0.7';
        submitBtn.disabled = true;
      }

      triggerTerminalLoader();
    });
  }

  if (demoModeBtn) {
    demoModeBtn.addEventListener('click', () => {
      jdInput.value = "We are looking for an expert engineer to design and implement resilient cloud architectures. The ideal candidate will have extensive experience in multi-cloud environments, specifically scaling across AWS and GCP.\n\nRequirements:\n- 5+ years backend development.\n- Deep understanding of Terraform and Infrastructure as Code.\n- Experience with robust observability tools (Datadog, Prometheus).\n- Strong background in ensuring strict compliance standards (SOC2).";

      if (!fileInput.files.length) {
        alert('Demo job description loaded. Please upload your resume file then click Execute Analysis.');
        return;
      }

      analysisForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    });
  }

  const transitionToIDE = (data) => {
    if (!stateCommandCenter) return;

    stateCommandCenter.style.opacity = '0';
    setTimeout(() => {
      stateCommandCenter.style.display = 'none';
      stateCommandCenter.classList.remove('active');

      if (stateIdeCanvas) {
        stateIdeCanvas.style.display = 'flex';
        stateIdeCanvas.setAttribute('aria-hidden', 'false');
        void stateIdeCanvas.offsetWidth;
        stateIdeCanvas.style.animation = 'fadeIn 0.5s ease-out forwards';
      }

      populateResults(data);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 300);
  };

  const populateResults = (data) => {
    const score       = Math.round(data.score);
    const missing     = data.missing_keywords || [];
    const suggestions = data.suggestions      || [];
    const roles       = data.predicted_roles  || [];

    animateScore(score);
    setTimeout(() => {
      if (scoreElement) scoreElement.style.color = getScoreColor(score);
    }, 2100);

    const signal = getSignal(score);
    const rows   = document.querySelectorAll('.telemetry-row');

    if (rows.length >= 4) {
      const matchDd = rows[0].querySelector('dd');
      if (matchDd) { matchDd.textContent = signal.label; matchDd.className = signal.cls; }

      const resWDd = rows[1].querySelector('dd');
      if (resWDd) resWDd.textContent = data.resume_word_count ?? '—';

      const jdWDd = rows[2].querySelector('dd');
      if (jdWDd) jdWDd.textContent = data.jd_word_count ?? '—';

      const gapDd = rows[3].querySelector('dd');
      if (gapDd) {
        gapDd.textContent = String(missing.length).padStart(2, '0');
        gapDd.className   = missing.length > 0 ? 'signal-warning' : 'signal-high';
      }
    }

    const jdPaneMeta = document.querySelector('.jd-pane .pane-meta');
    if (jdPaneMeta) {
      jdPaneMeta.textContent = missing.length + ' Missing Terms Highlighted';
    }
    if (jdPaneContent) {
      jdPaneContent.innerHTML = highlightKeywords(jdInput.value, missing);
    }

    const resumePaneTitle = document.querySelector('.resume-pane .pane-title');
    if (resumePaneTitle && fileInput.files[0]) {
      resumePaneTitle.textContent = fileInput.files[0].name;
    }
    const resumePaneContent = document.getElementById('resume-pane-content');
    if (resumePaneContent) {
      resumePaneContent.innerHTML =
        '<p><em style="color:var(--text-tertiary); font-size: 0.75rem;">' + data.resume_word_count + ' words analyzed...</em></p>' +
        (data.resume_text ? '<p>' + escapeHtml(data.resume_text).replace(/\n/g, '<br>') + '</p>' : '');
    }

    const taskList = document.querySelector('.task-list');
    if (taskList) {
      taskList.innerHTML = '';
      suggestions.slice(0, 5).forEach((suggestion, index) => {
        const priority    = index === 0 ? 'p0' : index <= 2 ? 'p1' : 'p2';
        const priorityLbl = index === 0 ? 'P0' : index <= 2 ? 'P1' : 'P2';

        const li = document.createElement('li');
        li.className = 'task-item';
        li.innerHTML = `
          <label class="task-label">
            <input type="checkbox" class="task-checkbox" aria-label="Mark task complete">
            <span class="custom-checkbox" aria-hidden="true"></span>
            <span class="task-text">
              <span class="priority-badge ${priority}">${priorityLbl}</span>
              ${escapeHtml(suggestion)}
            </span>
          </label>
        `;
        taskList.appendChild(li);
      });

      document.querySelectorAll('.task-checkbox').forEach(cb => {
        cb.addEventListener('change', updateProgress);
      });
    }

    if (drawerTitle) {
      drawerTitle.textContent = 'Analysis Insights (0/' + suggestions.length + ' Tasks Resolved)';
    }
    updateProgress();

    const existingRoles = document.getElementById('predicted-roles-section');
    if (existingRoles) existingRoles.remove();

    if (roles.length > 0) {
      const drawerContentEl = document.querySelector('.drawer-content');
      if (drawerContentEl) {
        const section = document.createElement('div');
        section.id = 'predicted-roles-section';
        section.innerHTML =
          '<div style="margin-top:24px;padding-top:24px;border-top:1px solid var(--border-subtle)">' +
          '<div style="font-size:11px;font-weight:600;color:#52525B;letter-spacing:0.08em;margin-bottom:16px;margin-left:24px;margin-right:24px;">PREDICTED ROLES</div>' +
          '<div style="padding: 0 24px 24px 24px; display: flex; flex-direction: column; gap: 8px;">' +
          roles.map(r => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border: 1px solid #E4E4E7; border-radius: 6px; background-color: #FAFAFA;">
              <span style="color: #0A0A0A; font-weight: 500; font-size: 0.875rem; text-align: left;">${formatRoleName(r.role)}</span>
              <span class="role-pct" style="color: ${getRoleColor(r.confidence)}; font-weight: 500; font-size: 0.875rem; text-align: right;">${Math.round(r.confidence)}%</span>
            </div>
          `).join('') +
          '</div></div>';
        drawerContentEl.appendChild(section);

        if (drawerContent) drawerContent.style.maxHeight = drawerContent.scrollHeight + 'px';
      }
    }
  };

  function highlightKeywords(text, keywords) {
    let escaped = escapeHtml(text);
    keywords.forEach(kw => {
      const regex = new RegExp('(' + escapeRegex(kw) + ')', 'gi');
      escaped = escaped.replace(regex, '<mark class="gap-highlight">$1</mark>');
    });

    return escaped.replace(/\n/g, '<br>');
  }

  const animateScore = (targetScore) => {
    let startTimestamp = null;
    const duration = 2000;

    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);

      // Cubic ease-out deceleration
      const easeOut      = 1 - Math.pow(1 - progress, 3);
      const currentScore = Math.floor(easeOut * targetScore);

      scoreElement.textContent = currentScore;

      if (currentScore < 50) {
        scoreElement.style.color = 'var(--signal-warning)';
      } else {
        scoreElement.style.color = 'var(--text-primary)';
      }

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        scoreElement.textContent = targetScore;
      }
    };

    window.requestAnimationFrame(step);
  };

  if (drawerToggle && drawerContent) {
    drawerToggle.addEventListener('click', () => {
      const isExpanded = drawerToggle.getAttribute('aria-expanded') === 'true';

      if (isExpanded) {
        drawerContent.style.maxHeight = '0px';
        drawerContent.style.opacity   = '0';
        drawerToggle.setAttribute('aria-expanded', 'false');
        drawerToggle.style.transform  = 'rotate(180deg)';
      } else {
        drawerContent.style.maxHeight = drawerContent.scrollHeight + 'px';
        drawerContent.style.opacity   = '1';
        drawerToggle.setAttribute('aria-expanded', 'true');
        drawerToggle.style.transform  = 'rotate(0deg)';
      }

      drawerContent.style.transition = 'max-height 0.3s ease-out, opacity 0.3s ease-out';
      drawerToggle.style.transition  = 'transform 0.3s ease-out';
    });

    drawerContent.style.maxHeight = drawerContent.scrollHeight + 'px';
    drawerContent.style.opacity   = '1';
  }

  const updateProgress = () => {
    const liveCheckboxes = document.querySelectorAll('.task-checkbox');
    if (!liveCheckboxes.length || !commitProgressFill || !drawerTitle) return;

    const total   = liveCheckboxes.length;
    let   checked = 0;
    liveCheckboxes.forEach(cb => { if (cb.checked) checked++; });

    commitProgressFill.style.width = `${(checked / total) * 100}%`;
    drawerTitle.textContent = `Analysis Insights (${checked}/${total} Tasks Resolved)`;
  };

  const resetToCommandCenter = () => {
    if (stateIdeCanvas) {
      stateIdeCanvas.style.display = 'none';
      stateIdeCanvas.setAttribute('aria-hidden', 'true');
    }

    if (stateCommandCenter) {
      stateCommandCenter.style.display = 'flex';
      stateCommandCenter.style.opacity = '1';
      stateCommandCenter.classList.add('active');
    }

    if (analysisForm) {
      analysisForm.reset();
      analysisForm.style.display = 'flex';
    }

    if (fileInput) fileInput.value = '';

    resetDropzoneUI();

    if (demoModeBtn) demoModeBtn.style.display = 'block';

    const trustSignal = document.querySelector('.trust-signal');
    if (trustSignal) trustSignal.style.display = 'flex';

    if (terminalLoader) terminalLoader.style.display = 'none';

    const submitBtn = analysisForm ? analysisForm.querySelector('.action-submit') : null;
    if (submitBtn) {
      submitBtn.disabled      = false;
      submitBtn.style.opacity = '1';
      submitBtn.innerHTML     = `<span class="btn-text">Analyze Resume Match</span><span class="btn-shortcut" aria-hidden="true">↵</span>`;
    }

    if (recalcBtn) {
      recalcBtn.classList.remove('active');
      recalcBtn.textContent = '[ ⟳ Re-calculate ]';
      recalcBtn.disabled    = false;
    }

    document.querySelectorAll('.task-checkbox').forEach(cb => { cb.checked = false; });
    updateProgress();

    const rolesSection = document.getElementById('predicted-roles-section');
    if (rolesSection) rolesSection.remove();

    if (scoreElement) scoreElement.textContent = '0';

    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const newScanBtn = document.querySelector('.btn-primary');
  if (newScanBtn) newScanBtn.addEventListener('click', resetToCommandCenter);

  const initCommandPalette = () => {
    document.body.insertAdjacentHTML('beforeend', `
      <div id="cp-backdrop" class="cp-backdrop" aria-hidden="true">
        <div class="cp-modal">
          <div class="cp-header">
            <input type="text" id="cp-input" placeholder="Search commands or navigate..." autocomplete="off">
          </div>
          <div class="cp-body">
            <ul id="cp-results" class="cp-results"></ul>
          </div>
        </div>
      </div>
    `);

    const cpBackdrop = document.getElementById('cp-backdrop');
    const cpInput    = document.getElementById('cp-input');
    const cpResults  = document.getElementById('cp-results');

    const commands = [
      { id: 'action-new',   label: 'Analyzer / New Scan',     action: () => {
          if (stateIdeCanvas && stateIdeCanvas.style.display !== 'none') {
            resetToCommandCenter();
          } else if (window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
            window.location.href = '/';
          }
        },
        path: '/'
      },
      { id: 'nav-docs',     label: 'Go to Documentation',     action: () => { window.location.href = '/docs'; }, path: '/docs' },
      { id: 'nav-privacy',  label: 'View Privacy Policy',     action: () => { window.location.href = '/privacy'; }, path: '/privacy' },
      { id: 'nav-security', label: 'View Security Policy',    action: () => { window.location.href = '/security'; }, path: '/security' },
      { id: 'nav-terms',    label: 'View Terms of Service',   action: () => { window.location.href = '/terms'; }, path: '/terms' }
    ];

    let selectedIndex = 0;

    const renderResults = (query = '') => {
      cpResults.innerHTML = '';
      const filtered = commands.filter(c => c.label.toLowerCase().includes(query.toLowerCase()));

      if (filtered.length === 0) {
        cpResults.innerHTML = '<li class="cp-result-item" style="justify-content:center;cursor:default">No commands found</li>';
        return;
      }

      if (selectedIndex >= filtered.length) selectedIndex = Math.max(0, filtered.length - 1);

      filtered.forEach((cmd, idx) => {
        const li = document.createElement('li');
        li.className = 'cp-result-item' + (idx === selectedIndex ? ' selected' : '');
        let currentPath = window.location.pathname;
        if (currentPath === '/index.html') currentPath = '/';
        const isCurrent = (cmd.path && currentPath === cmd.path) || (currentPath === '/' && cmd.id === 'action-new');
        if (isCurrent) {
          li.innerHTML = `
            <span class="cp-item-label" style="color: var(--text-primary); font-weight: 500;">${cmd.label}</span>
            <span class="cp-item-current" style="display: flex; align-items: center; gap: 4px; font-size: 0.7rem; font-weight: 600; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em;">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              Active
            </span>
          `;
        } else {
          li.textContent = cmd.label;
        }
        li.addEventListener('mousedown', (e) => {
          e.preventDefault();
        });
        li.addEventListener('click', () => {
          closeCP();
          cmd.action();
        });
        li.addEventListener('mouseenter', () => {
          selectedIndex = idx;
          document.querySelectorAll('.cp-result-item').forEach(el => el.classList.remove('selected'));
          li.classList.add('selected');
        });
        cpResults.appendChild(li);
      });
    };

    const toggleCP = () => {
      const isActive = cpBackdrop.classList.contains('active');
      if (isActive) {
        closeCP();
      } else {
        cpBackdrop.classList.add('active');
        cpBackdrop.setAttribute('aria-hidden', 'false');
        cpInput.value  = '';
        selectedIndex  = 0;
        renderResults();
        setTimeout(() => cpInput.focus(), 50);
      }
    };

    const closeCP = () => {
      cpBackdrop.classList.remove('active');
      cpBackdrop.setAttribute('aria-hidden', 'true');
      cpInput.blur();
    };

    cpBackdrop.addEventListener('click', (e) => { if (e.target === cpBackdrop) closeCP(); });

    cpInput.addEventListener('input', (e) => { selectedIndex = 0; renderResults(e.target.value); });

    cpInput.addEventListener('keydown', (e) => {
      const filtered = commands.filter(c => c.label.toLowerCase().includes(cpInput.value.toLowerCase()));
      if (filtered.length === 0) return;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedIndex = (selectedIndex + 1) % filtered.length;
        updateSelection();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedIndex = (selectedIndex - 1 + filtered.length) % filtered.length;
        updateSelection();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) { closeCP(); filtered[selectedIndex].action(); }
      }
    });

    const updateSelection = () => {
      const items = document.querySelectorAll('.cp-result-item');
      items.forEach((el, idx) => {
        if (idx === selectedIndex) {
          el.classList.add('selected');
          el.scrollIntoView({ block: 'nearest' });
        } else {
          el.classList.remove('selected');
        }
      });
    };

    document.addEventListener('keydown', (e) => {

      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        toggleCP();
      }

      if (e.key === 'Escape') {
        if (cpBackdrop && cpBackdrop.classList.contains('active')) {
          e.preventDefault();
          closeCP();
        } else if (drawerToggle && drawerToggle.getAttribute('aria-expanded') === 'true') {
          e.preventDefault();
          drawerContent.style.maxHeight = '0px';
          drawerContent.style.opacity   = '0';
          drawerToggle.setAttribute('aria-expanded', 'false');
          drawerToggle.style.transform  = 'rotate(180deg)';
        }
      }

      if (e.altKey && e.code === 'KeyN') {
        e.preventDefault();
        if (stateIdeCanvas && stateIdeCanvas.style.display !== 'none') {
          resetToCommandCenter();
        } else if (window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
          window.location.href = '/';
        } else {
          resetToCommandCenter();
        }
      }
    });

    if (cmdKTrigger) cmdKTrigger.addEventListener('click', () => toggleCP());
  };

  initCommandPalette();

  let lastScrollY = window.scrollY;

  window.addEventListener('scroll', () => {
    if (window.innerWidth <= 768 && header) {
      if (window.scrollY > lastScrollY && window.scrollY > 60) {
        header.style.transform  = 'translateY(-100%)';
        header.style.transition = 'transform 0.3s ease';
      } else {
        header.style.transform = 'translateY(0)';
      }
    } else if (header) {
      header.style.transform = 'translateY(0)';
    }
    lastScrollY = window.scrollY;
  }, { passive: true });

  // FAQ accordion for docs page
  document.querySelectorAll('.faq-item').forEach(item => {
    const btn = item.querySelector('.faq-question');
    if (btn) {
      btn.addEventListener('click', () => {
        const isExpanded = btn.getAttribute('aria-expanded') === 'true';
        // Collapse other open FAQ items for single-open accordion behavior
        document.querySelectorAll('.faq-question').forEach(otherBtn => {
          if (otherBtn !== btn) otherBtn.setAttribute('aria-expanded', 'false');
        });
        btn.setAttribute('aria-expanded', !isExpanded);
      });
    }
  });

  // Scrollspy highlights the active sidebar link based on visible section
  const sections  = document.querySelectorAll('.help-section');
  const navLinks  = document.querySelectorAll('.sidenav-link');

  if (sections.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          navLinks.forEach(link => {
            if (link.getAttribute('href') === `#${entry.target.id}`) {
              link.classList.add('active');
            } else {
              link.classList.remove('active');
            }
          });
        }
      });
    }, { rootMargin: '-100px 0px -60% 0px' });

    sections.forEach(section => observer.observe(section));
  }

});

// Exposed globally for onclick attributes in docs.html
window.handleFeedback = function () {
  const container = document.getElementById('feedback-module');
  const text      = document.getElementById('feedback-text');
  const buttons   = document.getElementById('feedback-buttons');

  if (container && text && buttons) {
    container.classList.add('feedback-submitted');
    buttons.style.opacity = '0';
    text.style.opacity    = '0';

    setTimeout(() => {
      buttons.style.display = 'none';
      text.textContent      = 'Thank you for your feedback.';
      text.style.opacity    = '1';
    }, 300);
  }
};