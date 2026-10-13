/**
 * TypeRead Web Engine & Application Controller
 * High-Performance Client-Side Keystroke Evaluator, Universal Book Ingestion (PDF, EPUB, TXT),
 * Virtual Keyboard & Finger Guide, and Lenient Typing Engine.
 */

// Default documents in library
const DEFAULT_DOCUMENTS = [
  {
    id: "doc-tale-of-two-cities",
    title: "A Tale of Two Cities",
    author: "Charles Dickens",
    format: "TXT",
    chapters: [
      {
        id: "c1",
        title: "Chapter 1: The Period",
        text: "It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness, it was the epoch of belief, it was the epoch of incredulity, it was the season of light, it was the season of darkness, it was the spring of hope, it was the winter of despair."
      },
      {
        id: "c2",
        title: "Chapter 2: The Mail",
        text: "It was the Dover road that lay, on a Friday night late in November, before the first of the persons with whom this history has business. The Dover mail was lumbering up Shooter's Hill, as the guard walked beside it."
      }
    ]
  },
  {
    id: "doc-atomic-habits",
    title: "Atomic Habits (Excerpt)",
    author: "James Clear",
    format: "TXT",
    chapters: [
      {
        id: "c1",
        title: "Chapter 1: The Surprising Power of Tiny Habits",
        text: "Changes that seem small and unimportant at first will compound into remarkable results if you are willing to stick with them for years. We all deal with setbacks, but in the long run, the quality of our lives often depends on the quality of our habits."
      }
    ]
  },
  {
    id: "doc-art-of-war",
    title: "The Art of War",
    author: "Sun Tzu",
    format: "TXT",
    chapters: [
      {
        id: "c1",
        title: "Chapter 1: Laying Plans",
        text: "The art of war is of vital importance to the State. It is a matter of life and death, a road either to safety or to ruin. Hence it is a subject of inquiry which can on no account be neglected."
      }
    ]
  }
];

// App State
let appState = {
  documents: [],
  currentDocId: null,
  currentChapterId: null,
  session: {
    status: 'idle', // idle, active, paused, finished
    currentIndex: 0,
    startTime: null,
    totalSeconds: 0,
    keystrokes: [], // { expected, typed, correct, skipped, timestamp }
    errorsCount: 0,
    errorHandlingMode: 'allow', // 'allow' or 'strict'
  },
  settings: {
    theme: 'dark',
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: '15px',
    caretStyle: 'block',
    errorHandling: 'allow',
    soundEnabled: true,
    showVirtualKeyboard: true,
    keyAnimations: true,
    showFingerGuide: true,
    ignoreCase: true,
    lenientPunctuation: true
  },
  analytics: {
    totalPracticeSeconds: 0,
    totalCharactersTyped: 0,
    totalSessions: 0,
    totalErrors: 0,
    weakKeys: {}
  }
};

// Punctuation set for lenient typing mode
const PUNCTUATION_SET = new Set([
  ',', '.', ';', ':', '!', '?', '-', '—', '–', '\'', '"', '`',
  '“', '”', '‘', '’', '(', ')', '[', ']', '{', '}', '/', '\\',
  '_', '~', '*', '«', '»', '…'
]);

// Web Audio API for subtle mechanical keyclicks
let audioCtx = null;
function playKeySound(isError = false) {
  if (!appState.settings.soundEnabled) return;

  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    
    if (isError) {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(140, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.08);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.08);
    } else {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(580 + Math.random() * 80, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.025, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.03);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.03);
    }
  } catch (e) {
    // Ignore audio failures if browser blocks autoplay
  }
}

// ============================================================
// Virtual Keyboard & Touch-Typing Finger Model
// ============================================================
const FINGER_MAP = {
  // Left Pinky
  '`': 'left-pinky', '~': 'left-pinky', '1': 'left-pinky', '!': 'left-pinky',
  'q': 'left-pinky', 'a': 'left-pinky', 'z': 'left-pinky', 'tab': 'left-pinky',
  'caps': 'left-pinky', 'shift-left': 'left-pinky',

  // Left Ring
  '2': 'left-ring', '@': 'left-ring', 'w': 'left-ring', 's': 'left-ring', 'x': 'left-ring',

  // Left Middle
  '3': 'left-middle', '#': 'left-middle', 'e': 'left-middle', 'd': 'left-middle', 'c': 'left-middle',

  // Left Index
  '4': 'left-index', '$': 'left-index', '5': 'left-index', '%': 'left-index',
  'r': 'left-index', 't': 'left-index', 'f': 'left-index', 'g': 'left-index',
  'v': 'left-index', 'b': 'left-index',

  // Thumbs
  ' ': 'thumb',

  // Right Index
  '6': 'right-index', '^': 'right-index', '7': 'right-index', '&': 'right-index',
  'y': 'right-index', 'u': 'right-index', 'h': 'right-index', 'j': 'right-index',
  'n': 'right-index', 'm': 'right-index',

  // Right Middle
  '8': 'right-middle', '*': 'right-middle', 'i': 'right-middle', 'k': 'right-middle',
  ',': 'right-middle', '<': 'right-middle',

  // Right Ring
  '9': 'right-ring', '(': 'right-ring', 'o': 'right-ring', 'l': 'right-ring',
  '.': 'right-ring', '>': 'right-ring',

  // Right Pinky
  '0': 'right-pinky', ')': 'right-pinky', '-': 'right-pinky', '_': 'right-pinky',
  '=': 'right-pinky', '+': 'right-pinky', 'p': 'right-pinky', '[': 'right-pinky',
  '{': 'right-pinky', ']': 'right-pinky', '}': 'right-pinky', '\\': 'right-pinky',
  '|': 'right-pinky', ';': 'right-pinky', ':': 'right-pinky', "'": 'right-pinky',
  '"': 'right-pinky', '/': 'right-pinky', '?': 'right-pinky', 'enter': 'right-pinky',
  'backspace': 'right-pinky', 'shift-right': 'right-pinky'
};

const FINGER_INFO = {
  'left-pinky': { name: 'Left Pinky', label: 'L·Pinky', hand: 'Left Hand' },
  'left-ring': { name: 'Left Ring', label: 'L·Ring', hand: 'Left Hand' },
  'left-middle': { name: 'Left Middle', label: 'L·Mid', hand: 'Left Hand' },
  'left-index': { name: 'Left Index', label: 'L·Index', hand: 'Left Hand' },
  'thumb': { name: 'Thumb (Space)', label: 'Thumb', hand: 'Both Hands' },
  'right-index': { name: 'Right Index', label: 'R·Index', hand: 'Right Hand' },
  'right-middle': { name: 'Right Middle', label: 'R·Mid', hand: 'Right Hand' },
  'right-ring': { name: 'Right Ring', label: 'R·Ring', hand: 'Right Hand' },
  'right-pinky': { name: 'Right Pinky', label: 'R·Pinky', hand: 'Right Hand' },
};

const KEYBOARD_LAYOUT = [
  [
    { key: '`', sub: '~' }, { key: '1', sub: '!' }, { key: '2', sub: '@' }, { key: '3', sub: '#' },
    { key: '4', sub: '$' }, { key: '5', sub: '%' }, { key: '6', sub: '^' }, { key: '7', sub: '&' },
    { key: '8', sub: '*' }, { key: '9', sub: '(' }, { key: '0', sub: ')' }, { key: '-', sub: '_' },
    { key: '=', sub: '+' }, { key: 'Backspace', class: 'key-backspace' }
  ],
  [
    { key: 'Tab', class: 'key-tab' }, { key: 'q' }, { key: 'w' }, { key: 'e' }, { key: 'r' },
    { key: 't' }, { key: 'y' }, { key: 'u' }, { key: 'i' }, { key: 'o' }, { key: 'p' },
    { key: '[', sub: '{' }, { key: ']', sub: '}' }, { key: '\\', sub: '|' }
  ],
  [
    { key: 'Caps', class: 'key-caps' }, { key: 'a' }, { key: 's' }, { key: 'd' }, { key: 'f' },
    { key: 'g' }, { key: 'h' }, { key: 'j' }, { key: 'k' }, { key: 'l' },
    { key: ';', sub: ':' }, { key: "'", sub: '"' }, { key: 'Enter', class: 'key-enter' }
  ],
  [
    { key: 'Shift', class: 'key-shift' }, { key: 'z' }, { key: 'x' }, { key: 'c' }, { key: 'v' },
    { key: 'b' }, { key: 'n' }, { key: 'm' }, { key: ',', sub: '<' }, { key: '.', sub: '>' },
    { key: '/', sub: '?' }, { key: 'Shift', class: 'key-shift' }
  ],
  [
    { key: 'Space', val: ' ', class: 'key-space' }
  ]
];

// Build DOM for Virtual Keyboard
function buildVirtualKeyboard() {
  const container = document.getElementById('keyboardGrid');
  if (!container) return;
  container.innerHTML = '';

  KEYBOARD_LAYOUT.forEach(row => {
    const rowEl = document.createElement('div');
    rowEl.className = 'keyboard-row';

    row.forEach(item => {
      const keyEl = document.createElement('div');
      const charVal = item.val !== undefined ? item.val : item.key.toLowerCase();
      const finger = FINGER_MAP[charVal] || FINGER_MAP[item.key.toLowerCase()] || 'thumb';

      keyEl.className = `key ${item.class || ''} finger-${finger}`;
      keyEl.dataset.key = charVal;
      if (item.sub) keyEl.dataset.sub = item.sub;

      if (item.sub) {
        keyEl.innerHTML = `<span class="key-sub">${escapeHtml(item.sub)}</span><span>${escapeHtml(item.key.toUpperCase())}</span>`;
      } else {
        keyEl.innerHTML = `<span>${escapeHtml(item.key.toUpperCase())}</span>`;
      }

      rowEl.appendChild(keyEl);
    });

    container.appendChild(rowEl);
  });
}

// Update Target Key & Active Finger on the Virtual Keyboard
function updateVirtualKeyboardTarget(expectedChar) {
  if (!appState.settings.showVirtualKeyboard) return;

  // Clear previous target
  document.querySelectorAll('.key.target-key').forEach(el => el.classList.remove('target-key'));
  document.querySelectorAll('.finger-pill.active-finger').forEach(el => el.classList.remove('active-finger'));

  if (!expectedChar) return;

  const charLower = expectedChar.toLowerCase();
  const fingerKey = FINGER_MAP[charLower] || FINGER_MAP[expectedChar] || 'thumb';
  const info = FINGER_INFO[fingerKey] || { name: 'Index Finger', label: 'Index', hand: 'Touch Guide' };

  // Update target preview text & badge
  const previewBadge = document.getElementById('fingerGuideBadge');
  const previewText = document.getElementById('targetKeyPreview');
  const leniencyTag = document.getElementById('leniencyIndicator');

  const displayKey = expectedChar === ' ' ? 'SPACE' : expectedChar.toUpperCase();
  if (previewBadge) previewBadge.textContent = info.name;
  if (previewText) previewText.innerHTML = `Target Key: <strong>${escapeHtml(displayKey)}</strong>`;

  if (leniencyTag) {
    if (appState.settings.lenientPunctuation && PUNCTUATION_SET.has(expectedChar)) {
      leniencyTag.textContent = "Space Skips Punctuation";
      leniencyTag.style.display = "inline-block";
    } else if (appState.settings.ignoreCase && expectedChar !== charLower) {
      leniencyTag.textContent = "Case-Insensitive";
      leniencyTag.style.display = "inline-block";
    } else {
      leniencyTag.style.display = "none";
    }
  }

  // Highlight finger in hands diagram
  if (appState.settings.showFingerGuide) {
    document.querySelectorAll(`.finger-pill[data-finger="${fingerKey}"]`).forEach(el => {
      el.classList.add('active-finger');
    });
  }

  // Highlight key on keyboard
  let targetKeyEl = null;
  if (expectedChar === ' ') {
    targetKeyEl = document.querySelector('.key[data-key=" "]');
  } else {
    targetKeyEl = document.querySelector(`.key[data-key="${charLower}"]`);
    if (!targetKeyEl) {
      targetKeyEl = document.querySelector(`.key[data-sub="${expectedChar}"]`);
    }
  }

  if (targetKeyEl) {
    targetKeyEl.classList.add('target-key');
  }
}

// Animate Key on Press
function animateKeyPressed(key) {
  if (!appState.settings.showVirtualKeyboard || !appState.settings.keyAnimations) return;

  const charLower = key.toLowerCase();
  let keyEl = document.querySelector(`.key[data-key="${charLower}"]`);
  if (!keyEl && key === ' ') keyEl = document.querySelector('.key[data-key=" "]');
  if (!keyEl) keyEl = document.querySelector(`.key[data-sub="${key}"]`);

  if (keyEl) {
    keyEl.classList.add('key-pressed');
    setTimeout(() => {
      keyEl.classList.remove('key-pressed');
    }, 110);
  }
}

// ============================================================
// State Management & Storage
// ============================================================
function loadPersistedState() {
  try {
    const savedDocs = localStorage.getItem('typeread_docs');
    appState.documents = savedDocs ? JSON.parse(savedDocs) : DEFAULT_DOCUMENTS;

    const savedSettings = localStorage.getItem('typeread_settings');
    if (savedSettings) {
      appState.settings = { ...appState.settings, ...JSON.parse(savedSettings) };
    }

    const savedAnalytics = localStorage.getItem('typeread_analytics');
    if (savedAnalytics) {
      appState.analytics = { ...appState.analytics, ...JSON.parse(savedAnalytics) };
    }
  } catch (e) {
    console.error("Failed to load local storage:", e);
    appState.documents = DEFAULT_DOCUMENTS;
  }

  // Set default current document
  if (!appState.currentDocId && appState.documents.length > 0) {
    appState.currentDocId = appState.documents[0].id;
    appState.currentChapterId = appState.documents[0].chapters[0].id;
  }
}

function persistState() {
  try {
    localStorage.setItem('typeread_docs', JSON.stringify(appState.documents));
    localStorage.setItem('typeread_settings', JSON.stringify(appState.settings));
    localStorage.setItem('typeread_analytics', JSON.stringify(appState.analytics));
  } catch (e) {
    console.error("Failed to persist state:", e);
  }
}

// Theme & Settings applicator
function applySettings() {
  const s = appState.settings;
  document.documentElement.setAttribute('data-theme', s.theme);
  document.documentElement.style.setProperty('--font-family', s.fontFamily);
  document.documentElement.style.setProperty('--font-size', s.fontSize);

  const caretEl = document.querySelector('.caret');
  if (caretEl) {
    caretEl.className = 'caret ' + s.caretStyle;
  }

  // Form inputs sync
  const elTheme = document.getElementById('settingTheme');
  if (elTheme) elTheme.value = s.theme;

  const elFont = document.getElementById('settingFont');
  if (elFont) elFont.value = s.fontFamily;

  const elFontSize = document.getElementById('settingFontSize');
  if (elFontSize) elFontSize.value = s.fontSize;

  const elCaret = document.getElementById('settingCaret');
  if (elCaret) elCaret.value = s.caretStyle;

  const elErrorMode = document.getElementById('settingErrorMode');
  if (elErrorMode) elErrorMode.value = s.errorHandling;

  // Toggles
  const elSound = document.getElementById('settingSound');
  if (elSound) elSound.checked = s.soundEnabled;

  const elShowKb = document.getElementById('settingShowKeyboard');
  if (elShowKb) elShowKb.checked = s.showVirtualKeyboard;

  const elKeyAnim = document.getElementById('settingKeyAnimations');
  if (elKeyAnim) elKeyAnim.checked = s.keyAnimations;

  const elFingerGuide = document.getElementById('settingFingerGuide');
  if (elFingerGuide) elFingerGuide.checked = s.showFingerGuide;

  const elIgnoreCase = document.getElementById('settingIgnoreCase');
  if (elIgnoreCase) elIgnoreCase.checked = s.ignoreCase;

  const elLenientPunct = document.getElementById('settingLenientPunctuation');
  if (elLenientPunct) elLenientPunct.checked = s.lenientPunctuation;

  // Virtual keyboard container visibility & animation class
  const kbContainer = document.getElementById('virtualKeyboardContainer');
  const fingerBar = document.getElementById('fingerGuideBar');
  const btnToggleKb = document.getElementById('btnToggleKeyboard');

  if (kbContainer) {
    if (s.showVirtualKeyboard) {
      kbContainer.classList.remove('keyboard-hidden');
    } else {
      kbContainer.classList.add('keyboard-hidden');
    }

    if (s.keyAnimations) {
      kbContainer.classList.remove('no-animations');
    } else {
      kbContainer.classList.add('no-animations');
    }
  }

  if (fingerBar) {
    if (s.showFingerGuide) {
      fingerBar.classList.remove('finger-hidden');
    } else {
      fingerBar.classList.add('finger-hidden');
    }
  }

  const btnToggleKbText = document.getElementById('btnToggleKeyboardText');
  if (btnToggleKbText) {
    btnToggleKbText.textContent = s.showVirtualKeyboard ? 'Keyboard: ON' : 'Keyboard: OFF';
  } else if (btnToggleKb) {
    btnToggleKb.textContent = s.showVirtualKeyboard ? 'Keyboard: ON' : 'Keyboard: OFF';
  }
}

// Get current active passage text
function getCurrentChapter() {
  const doc = appState.documents.find(d => d.id === appState.currentDocId);
  if (!doc) return null;
  const chapter = doc.chapters.find(c => c.id === appState.currentChapterId) || doc.chapters[0];
  return { doc, chapter };
}

// Switch view
function switchView(viewName) {
  document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));

  const targetView = document.getElementById(`view${viewName.charAt(0).toUpperCase() + viewName.slice(1)}`);
  if (targetView) targetView.classList.add('active');

  const targetNavBtn = document.querySelector(`.nav-btn[data-view="${viewName}"]`);
  if (targetNavBtn) targetNavBtn.classList.add('active');

  if (viewName === 'practice') {
    renderPracticeView();
    const canvas = document.getElementById('typingCanvasBox');
    if (canvas) canvas.focus();
  } else if (viewName === 'stats') {
    renderStatsDashboard();
  } else if (viewName === 'library') {
    renderLibraryView();
  } else if (viewName === 'home') {
    renderHomeView();
  }
}

// Render Home Screen
function renderHomeView() {
  const current = getCurrentChapter();
  if (current) {
    document.getElementById('heroDocTitle').textContent = current.doc.title;
    document.getElementById('heroChapterInfo').textContent = `${current.chapter.title} • ${current.doc.chapters.length} chapters`;
  }

  const grid = document.getElementById('recentDocsGrid');
  grid.innerHTML = '';
  appState.documents.slice(0, 6).forEach(doc => {
    const card = document.createElement('div');
    card.className = 'doc-card';
    const fmt = doc.format || 'TXT';
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div class="doc-card-title">${escapeHtml(doc.title)}</div>
        <span class="doc-format-badge ${fmt.toLowerCase()}">${fmt}</span>
      </div>
      <div class="doc-card-meta">
        <span>${doc.author || 'Author'}</span>
        <span>${doc.chapters.length} chapter${doc.chapters.length > 1 ? 's' : ''}</span>
      </div>
    `;
    card.onclick = () => {
      appState.currentDocId = doc.id;
      appState.currentChapterId = doc.chapters[0].id;
      resetPracticeSession();
      switchView('practice');
    };
    grid.appendChild(card);
  });
}

// Render Library View
function renderLibraryView() {
  const grid = document.getElementById('libraryDocsGrid');
  grid.innerHTML = '';
  appState.documents.forEach(doc => {
    const card = document.createElement('div');
    card.className = 'doc-card';
    const fmt = doc.format || 'TXT';
    const totalChars = doc.chapters.reduce((acc, c) => acc + c.text.length, 0);

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div class="doc-card-title">${escapeHtml(doc.title)}</div>
        <span class="doc-format-badge ${fmt.toLowerCase()}">${fmt}</span>
      </div>
      <div class="doc-card-meta" style="margin-bottom:12px;">
        <span>${doc.author || 'Imported'}</span>
        <span>${doc.chapters.length} chapters • ${totalChars.toLocaleString()} chars</span>
      </div>
      <button class="btn-primary" style="width:100%; font-size:0.85rem; padding:6px 12px;">Start Typing ➔</button>
    `;
    card.onclick = () => {
      appState.currentDocId = doc.id;
      appState.currentChapterId = doc.chapters[0].id;
      resetPracticeSession();
      switchView('practice');
    };
    grid.appendChild(card);
  });
}

// Render Chapter Navigation Tree
function renderChapterTree() {
  const current = getCurrentChapter();
  if (!current) return;

  document.getElementById('practiceDocHeading').textContent = current.doc.title;
  const list = document.getElementById('chapterTreeList');
  list.innerHTML = '';

  current.doc.chapters.forEach((ch, idx) => {
    const li = document.createElement('li');
    li.className = `chapter-item ${ch.id === current.chapter.id ? 'active' : ''}`;
    li.innerHTML = `<span>#${idx + 1}</span> <span>${escapeHtml(ch.title)}</span>`;
    li.onclick = () => {
      appState.currentChapterId = ch.id;
      resetPracticeSession();
      renderPracticeView();
      document.getElementById('typingCanvasBox').focus();
    };
    list.appendChild(li);
  });
}

// Reset typing session for the current chapter
function resetPracticeSession() {
  appState.session = {
    status: 'idle',
    currentIndex: 0,
    startTime: null,
    totalSeconds: 0,
    keystrokes: [],
    errorsCount: 0,
    errorHandlingMode: appState.settings.errorHandling,
  };
  updateMetricsDisplay();
}

// Render Practice View (Dual Synchronized Stream)
function renderPracticeView() {
  const current = getCurrentChapter();
  if (!current) return;

  document.getElementById('headerDocTitle').textContent = `${current.doc.title} — ${current.chapter.title}`;
  renderChapterTree();

  const sourceText = current.chapter.text;
  const currentIndex = appState.session.currentIndex;

  // 1. Render Upper Source Reader Stream
  const sourceEl = document.getElementById('sourceStream');
  const completedPart = escapeHtml(sourceText.slice(0, currentIndex));
  const currentChar = currentIndex < sourceText.length ? escapeHtml(sourceText[currentIndex]) : '';
  const remainingPart = currentIndex + 1 <= sourceText.length ? escapeHtml(sourceText.slice(currentIndex + 1)) : '';

  sourceEl.innerHTML = `
    <span class="completed-text">${completedPart}</span><span class="current-char">${currentChar || ' '}</span><span>${remainingPart}</span>
  `;

  // 2. Render Lower Typing Canvas Stream
  const typingEl = document.getElementById('typingStream');
  let renderedTypedHtml = '';

  for (let i = 0; i < currentIndex; i++) {
    const stroke = appState.session.keystrokes[i];
    const char = sourceText[i];
    if (stroke && (stroke.correct || stroke.skipped)) {
      renderedTypedHtml += `<span class="char-correct">${escapeHtml(char)}</span>`;
    } else {
      renderedTypedHtml += `<span class="char-incorrect">${escapeHtml(char)}</span>`;
    }
  }

  const caretHtml = `<span class="caret ${appState.settings.caretStyle}"></span>`;
  const untypedPart = escapeHtml(sourceText.slice(currentIndex));

  typingEl.innerHTML = `${renderedTypedHtml}${caretHtml}<span class="char-pending">${untypedPart}</span>`;

  // Update Virtual Keyboard Target
  const nextChar = currentIndex < sourceText.length ? sourceText[currentIndex] : null;
  updateVirtualKeyboardTarget(nextChar);

  updateMetricsDisplay();
}

// Metric computations
function updateMetricsDisplay() {
  const current = getCurrentChapter();
  if (!current) return;

  const totalLen = current.chapter.text.length;
  const idx = appState.session.currentIndex;
  const errors = appState.session.errorsCount;

  // Progress
  const pct = totalLen > 0 ? Math.min(100, Math.round((idx / totalLen) * 100)) : 0;
  document.getElementById('progressBarFill').style.width = `${pct}%`;
  document.getElementById('progressPctText').textContent = `${pct}% COMPLETE`;

  // Accuracy
  const totalTyped = appState.session.keystrokes.length;
  const accuracy = totalTyped > 0 
    ? Math.max(0, ((totalTyped - errors) / totalTyped) * 100).toFixed(1)
    : '100.0';
  document.getElementById('metricAcc').textContent = `${accuracy}%`;

  // Errors
  document.getElementById('metricErrors').textContent = errors;

  // WPM
  let wpm = 0;
  if (appState.session.startTime && idx > 0) {
    const elapsedMinutes = (Date.now() - appState.session.startTime) / 60000;
    if (elapsedMinutes > 0.05) {
      const words = (idx / 5);
      wpm = Math.max(0, Math.round(words / elapsedMinutes));
    }
  }
  document.getElementById('metricWpm').textContent = wpm;
}

// ============================================================
// Keystroke Hot Path Evaluator with Case & Punctuation Leniency
// ============================================================
function handleKeystroke(key) {
  const current = getCurrentChapter();
  if (!current) return;

  const text = current.chapter.text;
  let idx = appState.session.currentIndex;

  // If already at end
  if (idx >= text.length) return;

  // Handle Backspace
  if (key === 'Backspace') {
    if (idx > 0) {
      appState.session.currentIndex--;
      appState.session.keystrokes.pop();
      renderPracticeView();
    }
    animateKeyPressed('Backspace');
    return;
  }

  // Ignore non-printable keys
  if (key.length !== 1) return;

  // Start timer on first keystroke
  if (appState.session.status !== 'active') {
    appState.session.status = 'active';
    appState.session.startTime = Date.now();
  }

  const expectedChar = text[idx];

  // ------------------------------------------------------------------
  // Rule 1: Lenient Punctuation (Space skips punctuation without errors)
  // ------------------------------------------------------------------
  if (appState.settings.lenientPunctuation) {
    if (PUNCTUATION_SET.has(expectedChar)) {
      // User pressed space on punctuation: skip punctuation gracefully!
      if (key === ' ') {
        // Record skipped punctuation mark
        appState.session.keystrokes.push({
          expected: expectedChar,
          typed: ' ',
          correct: true,
          skipped: true,
          timestamp: Date.now()
        });
        appState.session.currentIndex++;
        idx = appState.session.currentIndex;

        // Skip any additional consecutive punctuation marks
        while (idx < text.length && PUNCTUATION_SET.has(text[idx])) {
          appState.session.keystrokes.push({
            expected: text[idx],
            typed: ' ',
            correct: true,
            skipped: true,
            timestamp: Date.now()
          });
          appState.session.currentIndex++;
          idx = appState.session.currentIndex;
        }

        // If immediately followed by a space, consume the space that the user typed!
        if (idx < text.length && text[idx] === ' ') {
          appState.session.keystrokes.push({
            expected: ' ',
            typed: ' ',
            correct: true,
            skipped: false,
            timestamp: Date.now()
          });
          appState.session.currentIndex++;
        }

        playKeySound(false);
        animateKeyPressed('Space');
        renderPracticeView();

        if (appState.session.currentIndex >= text.length) {
          finishSession();
        }
        return;
      }

      // If user typed the next word letter directly (e.g. typing 's' on apostrophe in "it's" or 'w' on quote in '"word"')
      if (idx + 1 < text.length) {
        const nextChar = text[idx + 1];
        const isNextMatch = (key === nextChar) || 
          (appState.settings.ignoreCase && key.toLowerCase() === nextChar.toLowerCase());

        if (isNextMatch) {
          // Auto-skip the punctuation
          appState.session.keystrokes.push({
            expected: expectedChar,
            typed: key,
            correct: true,
            skipped: true,
            timestamp: Date.now()
          });
          // Accept the letter
          appState.session.keystrokes.push({
            expected: nextChar,
            typed: key,
            correct: true,
            skipped: false,
            timestamp: Date.now()
          });
          appState.session.currentIndex += 2;
          playKeySound(false);
          animateKeyPressed(key);
          renderPracticeView();

          if (appState.session.currentIndex >= text.length) {
            finishSession();
          }
          return;
        }
      }
    }
  }

  // ------------------------------------------------------------------
  // Rule 2: Case Leniency & Character Evaluation
  // ------------------------------------------------------------------
  let isCorrect = false;
  if (appState.settings.ignoreCase) {
    // If ignoreCase is active: lowercase and uppercase match equally!
    isCorrect = (key === expectedChar) || (key.toLowerCase() === expectedChar.toLowerCase());
  } else {
    isCorrect = (key === expectedChar);
  }

  // Audio feedback
  playKeySound(!isCorrect);
  animateKeyPressed(key);

  // Error handling modes
  if (!isCorrect) {
    appState.session.errorsCount++;
    const keyLower = expectedChar.toLowerCase();
    if (!appState.analytics.weakKeys[keyLower]) {
      appState.analytics.weakKeys[keyLower] = { errors: 0, total: 0 };
    }
    appState.analytics.weakKeys[keyLower].errors++;

    if (appState.settings.errorHandling === 'strict') {
      // In strict mode: do not advance until correct key is pressed
      renderPracticeView();
      return;
    }
  }

  // Update total key occurrence
  const keyLower = expectedChar.toLowerCase();
  if (!appState.analytics.weakKeys[keyLower]) {
    appState.analytics.weakKeys[keyLower] = { errors: 0, total: 0 };
  }
  appState.analytics.weakKeys[keyLower].total++;

  // Save keystroke
  appState.session.keystrokes.push({
    expected: expectedChar,
    typed: key,
    correct: isCorrect,
    timestamp: Date.now()
  });

  // Advance cursor
  appState.session.currentIndex++;
  renderPracticeView();

  // Check completion
  if (appState.session.currentIndex >= text.length) {
    finishSession();
  }
}

// Session finished
function finishSession() {
  appState.session.status = 'finished';
  const elapsedSecs = Math.max(1, Math.round((Date.now() - appState.session.startTime) / 1000));
  
  appState.analytics.totalSessions++;
  appState.analytics.totalPracticeSeconds += elapsedSecs;
  appState.analytics.totalCharactersTyped += appState.session.currentIndex;
  appState.analytics.totalErrors += appState.session.errorsCount;
  persistState();

  const current = getCurrentChapter();
  const accText = document.getElementById('metricAcc').textContent;
  const wpmText = document.getElementById('metricWpm').textContent;

  const completionModal = document.getElementById('completionModal');
  if (completionModal) {
    const titleEl = document.getElementById('completionTitle');
    const subtitleEl = document.getElementById('completionSubtitle');
    if (titleEl) titleEl.textContent = current ? `${current.chapter.title}` : 'Chapter Completed';
    if (subtitleEl) subtitleEl.textContent = current ? `From "${current.doc.title}"` : 'Great session!';
    
    document.getElementById('completionWpm').textContent = wpmText;
    document.getElementById('completionAcc').textContent = accText;
    document.getElementById('completionTime').textContent = `${elapsedSecs}s`;
    completionModal.classList.add('active');
  } else {
    alert(`Chapter Completed!\nAccuracy: ${accText}\nSpeed: ${wpmText} WPM`);
  }
}

// Render Stats
function renderStatsDashboard() {
  const an = appState.analytics;
  const avgWpm = an.totalPracticeSeconds > 0 
    ? Math.round((an.totalCharactersTyped / 5) / (an.totalPracticeSeconds / 60))
    : 0;
  const totalTyped = an.totalCharactersTyped + an.totalErrors;
  const acc = totalTyped > 0 
    ? ((an.totalCharactersTyped / totalTyped) * 100).toFixed(1)
    : '100.0';

  document.getElementById('statAvgWpm').textContent = avgWpm;
  document.getElementById('statAccuracy').textContent = `${acc}%`;
  document.getElementById('statPracticeTime').textContent = `${Math.round(an.totalPracticeSeconds / 60)}m`;
  document.getElementById('statCharsTyped').textContent = an.totalCharactersTyped;
  document.getElementById('statSessions').textContent = an.totalSessions;

  // Weak key table
  const tbody = document.getElementById('weakKeysTableBody');
  tbody.innerHTML = '';

  const weakEntries = Object.entries(an.weakKeys)
    .filter(([_, data]) => data.errors > 0)
    .sort((a, b) => (b[1].errors / b[1].total) - (a[1].errors / a[1].total));

  if (weakEntries.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:20px;">No errors recorded yet. Great typing!</td></tr>`;
    return;
  }

  weakEntries.forEach(([char, data]) => {
    const errorRate = ((data.errors / data.total) * 100).toFixed(1);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${escapeHtml(char.toUpperCase())}</strong></td>
      <td style="color:var(--incorrect);">${data.errors}</td>
      <td>${data.total}</td>
      <td>${errorRate}%</td>
    `;
    tbody.appendChild(tr);
  });
}

// Targeted Drill Generator
function generateTargetedDrill() {
  const weakEntries = Object.entries(appState.analytics.weakKeys)
    .filter(([_, data]) => data.errors > 0)
    .sort((a, b) => b[1].errors - a[1].errors)
    .slice(0, 5)
    .map(([char]) => char);

  if (weakEntries.length === 0) {
    alert("No weak keys detected yet! Continue practicing to identify problem keys.");
    return;
  }

  const keysStr = weakEntries.join('').toUpperCase();
  const drillText = `Targeted drill practice for problem keys [${keysStr}]: ` + 
    Array.from({ length: 18 }, () => {
      let word = '';
      for (let i = 0; i < 4; i++) {
        word += weakEntries[Math.floor(Math.random() * weakEntries.length)];
      }
      return word;
    }).join(' ') + '.';

  const newDoc = {
    id: `drill-${Date.now()}`,
    title: `Targeted Drill: [${keysStr}]`,
    author: "TypeRead AI Engine",
    format: "TXT",
    chapters: [
      {
        id: "c1",
        title: "Targeted Keystroke Drill",
        text: drillText
      }
    ]
  };

  appState.documents.unshift(newDoc);
  appState.currentDocId = newDoc.id;
  appState.currentChapterId = newDoc.chapters[0].id;
  persistState();
  resetPracticeSession();
  switchView('practice');
}

// ============================================================
// Universal Client-Side Book Ingestion Engine (PDF, EPUB, TXT)
// ============================================================

function cleanBookText(text) {
  if (!text) return '';
  return text
    .replace(/\r\n|\r/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

// Split plain text into chapters via regex heuristic
function splitTextIntoChapters(text) {
  const pattern = /(?:^|(?:\r?\n){2,})(?:#+\s*)?((?:chapter|part|book|section|act)\s+[0-9ivxlcdm]+[^\n]*|[A-Z0-9\s]{4,45})(?:\r?\n)+/gi;
  let matches = [];
  let match;
  while ((match = pattern.exec(text)) !== null) {
    matches.push({ title: cleanBookText(match[1]), start: match.index, end: pattern.lastIndex });
  }

  if (matches.length >= 2) {
    const chapters = [];
    for (let i = 0; i < matches.length; i++) {
      const chTitle = matches[i].title;
      const startPos = matches[i].end;
      const endPos = (i + 1 < matches.length) ? matches[i + 1].start : text.length;
      const chText = cleanBookText(text.slice(startPos, endPos));
      if (chText.length >= 30) {
        chapters.push({
          id: `c${chapters.length + 1}`,
          title: chTitle,
          text: chText
        });
      }
    }
    if (chapters.length > 0) return chapters;
  }

  // Fallback: Segment by ~1,200 words into manageable sections
  const words = text.split(/\s+/);
  const chunkSize = 1100;
  const chapters = [];
  for (let i = 0; i < words.length; i += chunkSize) {
    const chunk = words.slice(i, i + chunkSize).join(' ');
    chapters.push({
      id: `c${chapters.length + 1}`,
      title: `Section ${chapters.length + 1}`,
      text: chunk
    });
  }

  return chapters.length > 0 ? chapters : [{
    id: "c1",
    title: "Section 1",
    text: text
  }];
}

// PDF Extraction using PDF.js
async function extractPdfBook(file, onProgress) {
  if (!window.pdfjsLib) {
    throw new Error("PDF.js library is not loaded.");
  }

  onProgress("Reading PDF binary data...", 15);
  const arrayBuffer = await file.arrayBuffer();
  
  onProgress("Initializing PDF document...", 30);
  const pdf = await window.pdfjsLib.getDocument({ data: arrayBuffer }).promise;
  const numPages = pdf.numPages;

  let title = file.name.replace(/\.[^/.]+$/, "");
  let author = "PDF Document";

  try {
    const meta = await pdf.getMetadata();
    if (meta && meta.info) {
      if (meta.info.Title && meta.info.Title.trim()) title = meta.info.Title.trim();
      if (meta.info.Author && meta.info.Author.trim()) author = meta.info.Author.trim();
    }
  } catch (e) {
    // Ignore metadata failure
  }

  // Attempt to extract PDF Outline (TOC)
  onProgress("Checking table of contents / bookmarks...", 45);
  let outline = null;
  try {
    outline = await pdf.getOutline();
  } catch (e) {
    outline = null;
  }

  let chapters = [];

  // Extract all pages text
  const pagesText = [];
  for (let p = 1; p <= numPages; p++) {
    const pct = Math.round(45 + (p / numPages) * 45);
    onProgress(`Extracting page ${p} of ${numPages}...`, pct);
    const page = await pdf.getPage(p);
    const textContent = await page.getTextContent();
    const pageStrings = textContent.items.map(item => item.str);
    pagesText.push(pageStrings.join(' '));
  }

  // If outline exists with chapters
  if (outline && outline.length > 0) {
    onProgress("Structuring chapters from outline...", 95);
    const resolvedOutline = [];

    for (const item of outline) {
      let pageIndex = -1;
      try {
        if (typeof item.dest === 'string') {
          const dest = await pdf.getDestination(item.dest);
          if (dest) {
            const pageRef = dest[0];
            pageIndex = await pdf.getPageIndex(pageRef);
          }
        } else if (Array.isArray(item.dest)) {
          const pageRef = item.dest[0];
          pageIndex = await pdf.getPageIndex(pageRef);
        }
      } catch (err) {}

      if (pageIndex >= 0 && pageIndex < numPages) {
        resolvedOutline.push({ title: item.title.trim(), page: pageIndex });
      }
    }

    // Sort outline by page
    resolvedOutline.sort((a, b) => a.page - b.page);

    for (let i = 0; i < resolvedOutline.length; i++) {
      const startPage = resolvedOutline[i].page;
      const endPage = (i + 1 < resolvedOutline.length) ? resolvedOutline[i + 1].page : numPages;
      const chText = cleanBookText(pagesText.slice(startPage, endPage).join('\n\n'));

      if (chText.length >= 30) {
        chapters.push({
          id: `c${chapters.length + 1}`,
          title: resolvedOutline[i].title,
          text: chText
        });
      }
    }
  }

  // Fallback: If no outline or empty chapters, run regex heuristic across joined text
  if (chapters.length === 0) {
    onProgress("Auto-detecting chapters and headings...", 95);
    const fullText = cleanBookText(pagesText.join('\n\n'));
    chapters = splitTextIntoChapters(fullText);
  }

  return {
    id: `doc-${Date.now()}`,
    title: title,
    author: author,
    format: "PDF",
    chapters: chapters
  };
}

// EPUB Extraction using JSZip
async function extractEpubBook(file, onProgress) {
  if (!window.JSZip) {
    throw new Error("JSZip library is not loaded.");
  }

  onProgress("Reading EPUB container...", 20);
  const zip = await window.JSZip.loadAsync(file);

  // 1. Locate container.xml
  const containerXml = await zip.file("META-INF/container.xml")?.async("string");
  if (!containerXml) throw new Error("Invalid EPUB: Missing META-INF/container.xml");

  const opfMatch = containerXml.match(/full-path=["']([^"']+)["']/i);
  if (!opfMatch) throw new Error("Cannot locate OPF file inside EPUB container.");
  const opfPath = opfMatch[1];
  const opfDir = opfPath.includes('/') ? opfPath.substring(0, opfPath.lastIndexOf('/')) : '';

  onProgress("Parsing EPUB metadata and spine...", 40);
  const opfText = await zip.file(opfPath)?.async("string");
  if (!opfText) throw new Error("Could not read OPF file.");

  const parser = new DOMParser();
  const opfDoc = parser.parseFromString(opfText, "application/xml");

  // Metadata
  let title = opfDoc.querySelector("title")?.textContent?.trim() || file.name.replace(/\.[^/.]+$/, "");
  let author = opfDoc.querySelector("creator")?.textContent?.trim() || "EPUB Author";

  // Manifest items
  const manifest = {};
  opfDoc.querySelectorAll("manifest item").forEach(item => {
    manifest[item.getAttribute("id")] = item.getAttribute("href");
  });

  // Spine items
  const spineIds = [];
  opfDoc.querySelectorAll("spine itemref").forEach(ref => {
    spineIds.push(ref.getAttribute("idref"));
  });

  // Table of Contents map
  const tocTitles = {};
  const ncxItem = Object.entries(manifest).find(([k, v]) => v.toLowerCase().endsWith(".ncx") || k.toLowerCase().includes("toc"));
  if (ncxItem) {
    const ncxPath = opfDir ? `${opfDir}/${ncxItem[1]}` : ncxItem[1];
    const ncxText = await zip.file(ncxPath)?.async("string");
    if (ncxText) {
      const ncxDoc = parser.parseFromString(ncxText, "application/xml");
      ncxDoc.querySelectorAll("navPoint").forEach(np => {
        const text = np.querySelector("text")?.textContent?.trim();
        const src = np.querySelector("content")?.getAttribute("src")?.split('#')[0];
        if (text && src) {
          const filename = src.split('/').pop();
          tocTitles[filename] = text;
        }
      });
    }
  }

  // Extract chapters from spine
  const chapters = [];
  for (let i = 0; i < spineIds.length; i++) {
    const pct = Math.round(40 + (i / spineIds.length) * 55);
    onProgress(`Extracting chapter ${i + 1} of ${spineIds.length}...`, pct);

    const href = manifest[spineIds[i]];
    if (!href) continue;

    const fullHref = opfDir ? `${opfDir}/${href}` : href;
    const xhtmlText = await zip.file(fullHref)?.async("string");
    if (!xhtmlText) continue;

    const doc = parser.parseFromString(xhtmlText, "text/html");
    doc.querySelectorAll("script, style, nav").forEach(el => el.remove());

    const cleanText = cleanBookText(doc.body?.textContent || "");
    if (cleanText.length < 50) continue; // Skip title/cover/blank leaves

    const filename = href.split('/').pop();
    let chTitle = tocTitles[filename];
    if (!chTitle) {
      const heading = doc.querySelector("h1, h2, h3")?.textContent?.trim();
      if (heading && heading.length <= 70) chTitle = heading;
    }
    if (!chTitle) chTitle = `Chapter ${chapters.length + 1}`;

    chapters.push({
      id: `c${chapters.length + 1}`,
      title: chTitle,
      text: cleanText
    });
  }

  return {
    id: `doc-${Date.now()}`,
    title: title,
    author: author,
    format: "EPUB",
    chapters: chapters.length > 0 ? chapters : [{ id: "c1", title: "Chapter 1", text: "No text found in EPUB." }]
  };
}

// Plain Text & Markdown Extraction
async function extractTextBook(file, onProgress) {
  onProgress("Reading text file...", 40);
  const rawText = await file.text();
  onProgress("Segmenting text into chapters...", 80);

  const cleaned = cleanBookText(rawText);
  const title = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, ' ');
  const chapters = splitTextIntoChapters(cleaned);

  return {
    id: `doc-${Date.now()}`,
    title: title,
    author: "Imported Text",
    format: "TXT",
    chapters: chapters
  };
}

// Central Book Processing Dispatcher
async function processUploadedBook(file) {
  if (!file) return;

  const modal = document.getElementById('parsingModal');
  const spinner = document.getElementById('parsingSpinner');
  const fileNameEl = document.getElementById('parsingFileName');
  const statusEl = document.getElementById('parsingStatusText');
  const progressBar = document.getElementById('parsingProgressBar');
  const percentEl = document.getElementById('parsingPercent');

  fileNameEl.textContent = file.name;
  statusEl.textContent = "Beginning book extraction...";
  progressBar.style.width = "10%";
  percentEl.textContent = "10%";
  modal.classList.add('active');

  const onProgress = (msg, pct) => {
    statusEl.textContent = msg;
    progressBar.style.width = `${pct}%`;
    percentEl.textContent = `${pct}%`;
  };

  try {
    const ext = file.name.split('.').pop().toLowerCase();
    let doc = null;

    if (ext === 'pdf') {
      doc = await extractPdfBook(file, onProgress);
    } else if (ext === 'epub') {
      doc = await extractEpubBook(file, onProgress);
    } else {
      doc = await extractTextBook(file, onProgress);
    }

    onProgress(`Successfully sorted ${doc.chapters.length} chapters!`, 100);

    setTimeout(() => {
      modal.classList.remove('active');

      // Add to Library
      appState.documents.unshift(doc);
      appState.currentDocId = doc.id;
      appState.currentChapterId = doc.chapters[0].id;

      persistState();
      resetPracticeSession();
      switchView('practice');

      // Notification
      setTimeout(() => {
        alert(`📖 "${doc.title}" successfully indexed!\nExtracted ${doc.chapters.length} chapters. Select any chapter on the left sidebar to start typing.`);
      }, 100);
    }, 400);

  } catch (err) {
    console.error("Book parsing error:", err);
    statusEl.textContent = `Error: ${err.message}`;
    progressBar.style.backgroundColor = "var(--incorrect)";
    setTimeout(() => {
      modal.classList.remove('active');
      alert(`Could not process book "${file.name}": ${err.message}`);
    }, 1500);
  }
}

// Helper: Escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ============================================================
// Initialization & Event Listeners
// ============================================================
window.addEventListener('DOMContentLoaded', () => {
  loadPersistedState();
  buildVirtualKeyboard();
  applySettings();
  renderHomeView();

  // Navigation tab clicks
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      switchView(btn.getAttribute('data-view'));
    });
  });

  // Hero resume
  document.getElementById('btnHeroContinue').addEventListener('click', () => {
    switchView('practice');
  });

  // Upload book triggers
  const fileInput = document.getElementById('fileUploadInput');

  document.getElementById('btnHeroImport').addEventListener('click', () => {
    fileInput.click();
  });

  document.getElementById('btnUploadFile').addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      processUploadedBook(file);
      fileInput.value = ''; // Reset input
    }
  });

  // Drag and Drop zones
  const setupDropzone = (el) => {
    if (!el) return;
    el.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
      el.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        el.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      el.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        el.classList.remove('dragover');
      });
    });

    el.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        processUploadedBook(files[0]);
      }
    });
  };

  setupDropzone(document.getElementById('homeDropzone'));
  setupDropzone(document.getElementById('libraryDropzone'));

  // Paste text modal trigger
  document.getElementById('btnPasteText').addEventListener('click', () => {
    document.getElementById('pasteModal').classList.add('active');
  });

  // Paste raw text submission
  document.getElementById('btnSubmitPastedDoc').addEventListener('click', () => {
    const title = document.getElementById('pasteTitleInput').value.trim() || 'My Document';
    const text = document.getElementById('pasteContentInput').value.trim();

    if (!text) {
      alert("Please enter some text to practice.");
      return;
    }

    const chapters = splitTextIntoChapters(cleanBookText(text));
    const newDoc = {
      id: `doc-${Date.now()}`,
      title: title,
      author: "Pasted Text",
      format: "TXT",
      chapters: chapters
    };

    appState.documents.unshift(newDoc);
    appState.currentDocId = newDoc.id;
    appState.currentChapterId = newDoc.chapters[0].id;
    persistState();
    resetPracticeSession();
    document.getElementById('pasteModal').classList.remove('active');
    switchView('practice');
  });

  // Quick toggle on-screen keyboard
  document.getElementById('btnToggleKeyboard').addEventListener('click', () => {
    appState.settings.showVirtualKeyboard = !appState.settings.showVirtualKeyboard;
    applySettings();
    persistState();
    const current = getCurrentChapter();
    if (current) {
      const nextChar = appState.session.currentIndex < current.chapter.text.length
        ? current.chapter.text[appState.session.currentIndex]
        : null;
      updateVirtualKeyboardTarget(nextChar);
    }
  });

  // Typing Canvas Keystrokes
  const canvasBox = document.getElementById('typingCanvasBox');
  const hiddenInput = document.getElementById('keystrokeInput');

  canvasBox.addEventListener('click', () => {
    hiddenInput.focus();
  });

  const updatePauseButtonLabel = (text) => {
    const textEl = document.getElementById('btnPauseSessionText');
    if (textEl) textEl.textContent = text;
    else document.getElementById('btnPauseSession').textContent = text;
  };

  window.addEventListener('keydown', (e) => {
    // Esc to Pause / Resume
    if (e.key === 'Escape') {
      if (appState.session.status === 'active') {
        appState.session.status = 'paused';
        updatePauseButtonLabel('Resume (Esc)');
      } else if (appState.session.status === 'paused') {
        appState.session.status = 'active';
        updatePauseButtonLabel('Pause (Esc)');
      }
      return;
    }

    // Capture typing only when in Practice view and no modal is active
    const isPracticeActive = document.getElementById('viewPractice').classList.contains('active');
    const isModalOpen = document.querySelector('.modal-overlay.active');
    if (!isPracticeActive || isModalOpen) return;

    if (e.key === 'Backspace' || e.key.length === 1) {
      e.preventDefault();
      handleKeystroke(e.key);
    }
  });

  // Pause button
  document.getElementById('btnPauseSession').addEventListener('click', () => {
    if (appState.session.status === 'active') {
      appState.session.status = 'paused';
      updatePauseButtonLabel('Resume (Esc)');
    } else {
      appState.session.status = 'active';
      updatePauseButtonLabel('Pause (Esc)');
      document.getElementById('typingCanvasBox').focus();
    }
  });

  // Restart button
  document.getElementById('btnRestartSession').addEventListener('click', () => {
    resetPracticeSession();
    renderPracticeView();
    document.getElementById('typingCanvasBox').focus();
  });

  // Refresh Stats
  document.getElementById('btnRefreshStats').addEventListener('click', () => {
    renderStatsDashboard();
  });

  // Generate Targeted Drill
  document.getElementById('btnGenerateDrill').addEventListener('click', () => {
    generateTargetedDrill();
  });

  // Modal open/close handlers
  document.getElementById('btnOpenSettings').addEventListener('click', () => {
    document.getElementById('settingsModal').classList.add('active');
  });

  document.getElementById('btnOpenSearch').addEventListener('click', () => {
    document.getElementById('searchModal').classList.add('active');
    document.getElementById('searchQueryInput').focus();
  });

  document.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-close');
      document.getElementById(modalId).classList.remove('active');
    });
  });

  // Settings changes: Appearance
  document.getElementById('settingTheme').addEventListener('change', (e) => {
    appState.settings.theme = e.target.value;
    applySettings();
    persistState();
  });

  document.getElementById('settingFont').addEventListener('change', (e) => {
    appState.settings.fontFamily = e.target.value;
    applySettings();
    persistState();
  });

  document.getElementById('settingFontSize').addEventListener('change', (e) => {
    appState.settings.fontSize = e.target.value;
    applySettings();
    persistState();
  });

  document.getElementById('settingCaret').addEventListener('change', (e) => {
    appState.settings.caretStyle = e.target.value;
    applySettings();
    persistState();
  });

  document.getElementById('settingErrorMode').addEventListener('change', (e) => {
    appState.settings.errorHandling = e.target.value;
    persistState();
  });

  // Settings changes: Audio & Animation Toggles
  document.getElementById('settingSound').addEventListener('change', (e) => {
    appState.settings.soundEnabled = e.target.checked;
    persistState();
  });

  document.getElementById('settingShowKeyboard').addEventListener('change', (e) => {
    appState.settings.showVirtualKeyboard = e.target.checked;
    applySettings();
    persistState();
  });

  document.getElementById('settingKeyAnimations').addEventListener('change', (e) => {
    appState.settings.keyAnimations = e.target.checked;
    applySettings();
    persistState();
  });

  document.getElementById('settingFingerGuide').addEventListener('change', (e) => {
    appState.settings.showFingerGuide = e.target.checked;
    applySettings();
    persistState();
  });

  // Settings changes: Typing Leniency
  document.getElementById('settingIgnoreCase').addEventListener('change', (e) => {
    appState.settings.ignoreCase = e.target.checked;
    persistState();
    renderPracticeView();
  });

  document.getElementById('settingLenientPunctuation').addEventListener('change', (e) => {
    appState.settings.lenientPunctuation = e.target.checked;
    persistState();
    renderPracticeView();
  });

  // In-Document Search
  document.getElementById('searchQueryInput').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    const resultsContainer = document.getElementById('searchResultsList');
    resultsContainer.innerHTML = '';
    if (!q) return;

    let matchCount = 0;
    appState.documents.forEach(doc => {
      doc.chapters.forEach(ch => {
        const text = ch.text;
        let matchIdx = text.toLowerCase().indexOf(q);
        while (matchIdx !== -1 && matchCount < 10) {
          const start = Math.max(0, matchIdx - 20);
          const end = Math.min(text.length, matchIdx + q.length + 20);
          const snippet = text.slice(start, end);

          const item = document.createElement('div');
          item.className = 'doc-card';
          item.style.marginBottom = '8px';
          item.innerHTML = `
            <div style="font-size:0.8rem; color:var(--accent); font-weight:600;">${escapeHtml(doc.title)} — ${escapeHtml(ch.title)}</div>
            <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:4px;">...${escapeHtml(snippet)}...</div>
          `;
          item.onclick = () => {
            appState.currentDocId = doc.id;
            appState.currentChapterId = ch.id;
            resetPracticeSession();
            appState.session.currentIndex = matchIdx;
            document.getElementById('searchModal').classList.remove('active');
            switchView('practice');
          };
          resultsContainer.appendChild(item);
          matchCount++;
          matchIdx = text.toLowerCase().indexOf(q, matchIdx + 1);
        }
      });
    });

    if (matchCount === 0) {
      resultsContainer.innerHTML = `<div style="color:var(--text-muted); font-size:0.88rem; padding:10px;">No occurrences found.</div>`;
    }
  });

  // Completion modal action buttons
  const btnCompRestart = document.getElementById('btnCompletionRestart');
  if (btnCompRestart) {
    btnCompRestart.addEventListener('click', () => {
      document.getElementById('completionModal').classList.remove('active');
      resetPracticeSession();
      renderPracticeView();
      document.getElementById('typingCanvasBox').focus();
    });
  }

  const btnCompNext = document.getElementById('btnCompletionNext');
  if (btnCompNext) {
    btnCompNext.addEventListener('click', () => {
      document.getElementById('completionModal').classList.remove('active');
      const current = getCurrentChapter();
      if (current && current.doc && current.doc.chapters) {
        const currIdx = current.doc.chapters.findIndex(c => c.id === current.chapter.id);
        if (currIdx >= 0 && currIdx + 1 < current.doc.chapters.length) {
          appState.currentChapterId = current.doc.chapters[currIdx + 1].id;
        }
      }
      resetPracticeSession();
      renderPracticeView();
      document.getElementById('typingCanvasBox').focus();
    });
  }

});

