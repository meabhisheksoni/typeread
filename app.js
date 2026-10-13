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
  companion: {
    enabled: true,
    speechEnabled: true,
    persona: 'byte', // 'byte', 'pip', 'mochi'
    emotion: 'neutral', // 'neutral', 'typing', 'streak', 'error', 'idle', 'victory'
    streak: 0,
    maxStreak: 0,
    lastKeystrokeTime: 0,
    idleTimer: null,
    errorTimer: null
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
// Toon Companion Procedural SVG & Reactive Emotion Engine
// ============================================================

function playCompanionChirp(type = 'poke') {
  if (!appState.settings.soundEnabled) return;
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const now = audioCtx.currentTime;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (type === 'poke') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(520, now);
      osc.frequency.exponentialRampToValueAtTime(1040, now + 0.12);
      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
      osc.start(now);
      osc.stop(now + 0.14);
    } else if (type === 'streak') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(659.25, now + 0.07);
      osc.frequency.setValueAtTime(783.99, now + 0.14);
      gain.gain.setValueAtTime(0.035, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    } else if (type === 'victory') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.setValueAtTime(554.37, now + 0.1);
      osc.frequency.setValueAtTime(659.25, now + 0.2);
      osc.frequency.setValueAtTime(880, now + 0.3);
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
      osc.start(now);
      osc.stop(now + 0.5);
    }
  } catch (e) {
    // Ignore audio errors
  }
}

const COMPANION_PHRASES = {
  byte: {
    name: 'Byte',
    neutral: [
      "Let's read and type together! ✨",
      "Ready to dive into the story? 📖",
      "Find your natural reading cadence.",
      "Every character builds your muscle memory."
    ],
    typing: [
      "Smooth typing rhythm! ⚡",
      "Focused and steady! 🎯",
      "Great cadence, keep moving!",
      "Word by word, you've got this!"
    ],
    streak: [
      "Blazing streak! 🔥",
      "Unstoppable reading momentum! 🌟",
      "In the zone! Keep soaring! 🚀",
      "Phenomenal rhythm! ⚡"
    ],
    error: [
      "All good, breathe and reset! 💡",
      "No rush, precision builds speed.",
      "Just a tiny bump, keep going!",
      "Focus on the next letter."
    ],
    idle: [
      "Taking a breather? ☕",
      "Rest those fingers a moment~",
      "Whenever you're ready to type! ✨"
    ],
    victory: [
      "Chapter conquered! Incredible work! 🏆",
      "Flawless finish! That was brilliant! 🎉",
      "You crushed that chapter! 🥳"
    ],
    poke: [
      "Boop! Byte at your service! 🤓",
      "I believe in your typing flow! 🌟",
      "Keep that great focus going!"
    ]
  },
  pip: {
    name: 'Pip',
    neutral: [
      "Systems nominal. Ready to type! 🤖",
      "Loading chapter buffers... Let's go! 💾",
      "Neural link established. Start typing! ⚡"
    ],
    typing: [
      "Processing keystrokes at speed! ⚡",
      "Data stream aligned! 🎯",
      "Optimized rhythm detected! 🔋",
      "Buffer clearing smoothly!"
    ],
    streak: [
      "OVERCLOCK ENGAGED! 🔥",
      "Maximum overdrive streak! 🚀",
      "Precision algorithm at 100%! 🌟",
      "Hyper-speed typing unlocked! ⚡"
    ],
    error: [
      "Glitch corrected! Recalibrating... 🔧",
      "Minor packet loss, resuming stream!",
      "Keep steady, pipeline recovering!"
    ],
    idle: [
      "Entering standby mode... 💤",
      "Awaiting next input interrupt... ⏳",
      "Low power cycle. Ready when you are!"
    ],
    victory: [
      "Chapter successfully compiled! 🏆",
      "Mission accomplished! 100% complete! 🚀",
      "Peak throughput achieved! 🎉"
    ],
    poke: [
      "*BEEP BOOP* Pip online! ⚡",
      "Diagnostic: Your skills are improving! 📈",
      "High five, typing operator! 🤖"
    ]
  },
  mochi: {
    name: 'Mochi',
    neutral: [
      "Meow! Let's read this book together! 🐾",
      "Purring and ready for typing! ✨",
      "Warm paws, ready fingers! 🐱"
    ],
    typing: [
      "Paws moving so fast! 🐾⚡",
      "Pounce on those letters! 🎯",
      "Such a smooth rhythm, purr~ 🎵",
      "You're doing amazing!"
    ],
    streak: [
      "SUPER STREAK! ZOOMIES ACTIVATED! 🔥",
      "Paws on fire! Look at you go! 🌟",
      "Purr-fect accuracy streak! 🐱💖",
      "Nothing can stop these paws! 🚀"
    ],
    error: [
      "Oopsie daisy! Shake it off! 🐾",
      "Land on your feet, try again! 💖",
      "Take your time, little friend!"
    ],
    idle: [
      "Curled up for a quick cat nap~ 💤",
      "Cozy break time... purr... ☕",
      "Ready whenever your paws are! ✨"
    ],
    victory: [
      "YAY! We finished the chapter! 🥳🎉",
      "Trophy unlocked! Extra treats for everyone! 🏆",
      "You're the master reader-typer! 🐾💖"
    ],
    poke: [
      "Purr~ *headbutts your finger* 🐱",
      "Meow! Cheering for you always! 💖",
      "Let's get that high score! 🐾"
    ]
  }
};

function generateAvatarSvg(persona = 'byte', emotion = 'neutral', streak = 0) {
  const isPip = persona === 'pip';
  const isMochi = persona === 'mochi';

  let defs = '';
  let content = '';

  if (isPip) {
    defs = `
      <defs>
        <linearGradient id="pipHeadGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#06b6d4"/>
          <stop offset="100%" stop-color="#0891b2"/>
        </linearGradient>
        <linearGradient id="pipScreenGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#090d16"/>
          <stop offset="100%" stop-color="#161f30"/>
        </linearGradient>
        <filter id="pipGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur"/>
          <feComposite in="SourceGraphic" in2="blur" operator="over"/>
        </filter>
      </defs>
    `;

    const antennaGlow = (emotion === 'streak' || emotion === 'victory') ? '#f59e0b' : (emotion === 'error' ? '#ef4444' : '#22d3ee');
    const antennaPulse = (emotion === 'streak') ? 'class="toon-aura"' : '';

    let screenContent = '';
    if (emotion === 'typing') {
      screenContent = `
        <path d="M 43 51 L 51 56 L 43 61" stroke="#38bdf8" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M 77 51 L 69 56 L 77 61" stroke="#38bdf8" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <line x1="55" y1="70" x2="57" y2="70" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="59" y1="68" x2="61" y2="68" stroke="#38bdf8" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="63" y1="70" x2="65" y2="70" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
      `;
    } else if (emotion === 'streak') {
      screenContent = `
        <polygon points="47,48 49,53 54,53 50,57 52,62 47,59 42,62 44,57 40,53 45,53" fill="#fbbf24" filter="url(#pipGlow)"/>
        <polygon points="73,48 75,53 80,53 76,57 78,62 73,59 68,62 70,57 66,53 71,53" fill="#fbbf24" filter="url(#pipGlow)"/>
        <rect x="50" y="68" width="20" height="5" rx="2.5" fill="#fbbf24"/>
      `;
    } else if (emotion === 'error') {
      screenContent = `
        <path d="M 42 50 L 52 60 M 52 50 L 42 60" stroke="#f43f5e" stroke-width="3" stroke-linecap="round"/>
        <path d="M 68 50 L 78 60 M 78 50 L 68 60" stroke="#f43f5e" stroke-width="3" stroke-linecap="round"/>
        <path d="M 50 70 L 54 67 L 58 72 L 62 67 L 66 72 L 70 70" stroke="#f43f5e" stroke-width="2.2" fill="none" stroke-linecap="round"/>
      `;
    } else if (emotion === 'idle') {
      screenContent = `
        <line x1="42" y1="56" x2="52" y2="56" stroke="#0ea5e9" stroke-width="3" stroke-linecap="round"/>
        <line x1="68" y1="56" x2="78" y2="56" stroke="#0ea5e9" stroke-width="3" stroke-linecap="round"/>
        <circle cx="60" cy="70" r="2.5" fill="#0ea5e9" opacity="0.6"/>
      `;
    } else if (emotion === 'victory') {
      screenContent = `
        <path d="M 41 57 L 47 50 L 53 57" stroke="#22d3ee" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M 67 57 L 73 50 L 79 57" stroke="#22d3ee" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M 52 67 Q 60 76 68 67" stroke="#fbbf24" stroke-width="3" fill="none" stroke-linecap="round"/>
      `;
    } else {
      screenContent = `
        <g class="toon-blink-eye">
          <rect x="43" y="49" width="9" height="14" rx="4.5" fill="#22d3ee"/>
          <rect x="68" y="49" width="9" height="14" rx="4.5" fill="#22d3ee"/>
        </g>
        <path d="M 55 70 Q 60 74 65 70" stroke="#22d3ee" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      `;
    }

    content = `
      <g class="avatar-body-group">
        <line x1="60" y1="28" x2="60" y2="13" stroke="#475569" stroke-width="4" stroke-linecap="round"/>
        <circle cx="60" cy="11" r="6" fill="${antennaGlow}" ${antennaPulse}/>
        <rect x="17" y="52" width="9" height="18" rx="4.5" fill="#334155"/>
        <rect x="94" y="52" width="9" height="18" rx="4.5" fill="#334155"/>
        <rect x="24" y="27" width="72" height="68" rx="20" fill="url(#pipHeadGrad)" stroke="#0e7490" stroke-width="2"/>
        <rect x="33" y="38" width="54" height="44" rx="12" fill="url(#pipScreenGrad)" stroke="#1e293b" stroke-width="2"/>
        ${screenContent}
        <path d="M 46 95 L 74 95 L 68 103 L 52 103 Z" fill="#334155"/>
      </g>
    `;
  } else if (isMochi) {
    defs = `
      <defs>
        <linearGradient id="mochiHeadGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#ffedd5"/>
          <stop offset="100%" stop-color="#fed7aa"/>
        </linearGradient>
      </defs>
    `;

    let faceDetails = '';
    if (emotion === 'typing') {
      faceDetails = `
        <circle cx="46" cy="59" r="6" fill="#1c1917"/><circle cx="48" cy="56" r="2.2" fill="#ffffff"/><circle cx="44" cy="62" r="1" fill="#ffffff"/>
        <circle cx="74" cy="59" r="6" fill="#1c1917"/><circle cx="76" cy="56" r="2.2" fill="#ffffff"/><circle cx="72" cy="62" r="1" fill="#ffffff"/>
        <path d="M 54 72 Q 60 76 66 72" stroke="#7c2d12" stroke-width="2.2" fill="none" stroke-linecap="round"/>
        <ellipse cx="38" cy="94" rx="9" ry="6" fill="#fff7ed" stroke="#fed7aa" stroke-width="1.5"/>
        <ellipse cx="82" cy="94" rx="9" ry="6" fill="#fff7ed" stroke="#fed7aa" stroke-width="1.5"/>
      `;
    } else if (emotion === 'streak') {
      faceDetails = `
        <polygon points="46,50 48,55 53,56 49,60 50,65 46,62 42,65 43,60 39,56 44,55" fill="#f59e0b"/>
        <polygon points="74,50 76,55 81,56 77,60 78,65 74,62 70,65 71,60 67,56 72,55" fill="#f59e0b"/>
        <path d="M 53 72 Q 60 84 67 72 Z" fill="#e11d48"/>
      `;
    } else if (emotion === 'error') {
      faceDetails = `
        <circle cx="45" cy="57" r="7.5" fill="#ffffff" stroke="#7c2d12" stroke-width="2"/>
        <circle cx="45" cy="57" r="2.5" fill="#1c1917"/>
        <circle cx="75" cy="57" r="7.5" fill="#ffffff" stroke="#7c2d12" stroke-width="2"/>
        <circle cx="75" cy="57" r="2.5" fill="#1c1917"/>
        <path d="M 52 74 Q 56 71 60 74 Q 64 77 68 74" stroke="#7c2d12" stroke-width="2.2" fill="none" stroke-linecap="round"/>
        <path d="M 90 48 C 90 44 94 40 96 40 C 98 40 102 44 102 48 C 102 52 96 54 90 48 Z" fill="#38bdf8"/>
      `;
    } else if (emotion === 'idle') {
      faceDetails = `
        <path d="M 40 60 Q 46 55 52 60" stroke="#7c2d12" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <path d="M 68 60 Q 74 55 80 60" stroke="#7c2d12" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <path d="M 55 72 Q 60 75 65 72" stroke="#7c2d12" stroke-width="2" fill="none" stroke-linecap="round"/>
        <text x="89" y="38" font-size="12" fill="#fb923c" font-weight="bold" font-family="sans-serif">z</text>
      `;
    } else if (emotion === 'victory') {
      faceDetails = `
        <path d="M 39 58 Q 46 49 53 58" stroke="#7c2d12" stroke-width="3" fill="none" stroke-linecap="round"/>
        <path d="M 67 58 Q 74 49 81 58" stroke="#7c2d12" stroke-width="3" fill="none" stroke-linecap="round"/>
        <path d="M 52 70 Q 56 75 60 70 Q 64 75 68 70 Z" fill="#e11d48"/>
        <circle cx="28" cy="26" r="4.5" fill="#f59e0b"/>
        <circle cx="92" cy="26" r="4.5" fill="#ec4899"/>
      `;
    } else {
      faceDetails = `
        <g class="toon-blink-eye">
          <circle cx="46" cy="58" r="6" fill="#1c1917"/><circle cx="48" cy="55" r="2.2" fill="#ffffff"/>
          <circle cx="74" cy="58" r="6" fill="#1c1917"/><circle cx="76" cy="55" r="2.2" fill="#ffffff"/>
        </g>
        <path d="M 54 73 Q 57 77 60 73 Q 63 77 66 73" stroke="#7c2d12" stroke-width="2.2" fill="none" stroke-linecap="round"/>
      `;
    }

    content = `
      <g class="avatar-body-group">
        <polygon points="26,46 34,18 51,36" fill="#fb923c"/>
        <polygon points="31,43 36,25 47,37" fill="#fda4af"/>
        <polygon points="69,36 86,18 94,46" fill="#fb923c"/>
        <polygon points="73,37 84,25 89,43" fill="#fda4af"/>
        <ellipse cx="60" cy="65" rx="38" ry="32" fill="url(#mochiHeadGrad)" stroke="#f97316" stroke-width="1.5"/>
        <line x1="21" y1="64" x2="35" y2="66" stroke="#7c2d12" stroke-width="2" stroke-linecap="round"/>
        <line x1="19" y1="72" x2="35" y2="71" stroke="#7c2d12" stroke-width="2" stroke-linecap="round"/>
        <line x1="85" y1="66" x2="99" y2="64" stroke="#7c2d12" stroke-width="2" stroke-linecap="round"/>
        <line x1="85" y1="71" x2="101" y2="72" stroke="#7c2d12" stroke-width="2" stroke-linecap="round"/>
        <polygon points="57,66 63,66 60,69" fill="#f43f5e"/>
        <circle cx="36" cy="71" r="5" fill="#fb7185" opacity="0.4"/>
        <circle cx="84" cy="71" r="5" fill="#fb7185" opacity="0.4"/>
        ${faceDetails}
      </g>
    `;
  } else {
    // byte (default)
    defs = `
      <defs>
        <linearGradient id="byteHeadGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#818cf8"/>
          <stop offset="100%" stop-color="#4f46e5"/>
        </linearGradient>
      </defs>
    `;

    let faceDetails = '';
    if (emotion === 'typing') {
      faceDetails = `
        <path d="M 39 45 L 53 43" stroke="#312e81" stroke-width="3" stroke-linecap="round"/>
        <path d="M 67 43 L 81 45" stroke="#312e81" stroke-width="3" stroke-linecap="round"/>
        <circle cx="48" cy="59" r="5.5" fill="#0f172a"/><circle cx="50" cy="57" r="2" fill="#ffffff"/>
        <circle cx="72" cy="59" r="5.5" fill="#0f172a"/><circle cx="74" cy="57" r="2" fill="#ffffff"/>
        <path d="M 55 76 Q 60 73 65 76" stroke="#1e1b4b" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      `;
    } else if (emotion === 'streak') {
      faceDetails = `
        <path d="M 38 41 Q 46 36 54 41" stroke="#312e81" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <path d="M 66 41 Q 74 36 82 41" stroke="#312e81" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <polygon points="46,50 48,55 53,56 49,60 50,65 46,62 42,65 43,60 39,56 44,55" fill="#fde047" stroke="#ca8a04" stroke-width="0.8"/>
        <polygon points="74,50 76,55 81,56 77,60 78,65 74,62 70,65 71,60 67,56 72,55" fill="#fde047" stroke="#ca8a04" stroke-width="0.8"/>
        <path d="M 52 74 Q 60 86 68 74 Z" fill="#e11d48"/>
        <rect x="57" y="74" width="6" height="3" rx="1" fill="#ffffff"/>
      `;
    } else if (emotion === 'error') {
      faceDetails = `
        <path d="M 38 42 L 52 46" stroke="#312e81" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M 68 46 L 82 42" stroke="#312e81" stroke-width="2.5" stroke-linecap="round"/>
        <circle cx="46" cy="58" r="7.5" fill="#ffffff" stroke="#1e1b4b" stroke-width="1.8"/>
        <circle cx="46" cy="58" r="2.5" fill="#0f172a"/>
        <circle cx="74" cy="58" r="7.5" fill="#ffffff" stroke="#1e1b4b" stroke-width="1.8"/>
        <circle cx="74" cy="58" r="2.5" fill="#0f172a"/>
        <path d="M 52 77 Q 56 73 60 77 Q 64 81 68 77" stroke="#1e1b4b" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <path d="M 88 42 C 88 38 92 34 94 34 C 96 34 100 38 100 42 C 100 46 94 48 88 42 Z" fill="#38bdf8"/>
      `;
    } else if (emotion === 'idle') {
      faceDetails = `
        <path d="M 40 60 Q 46 54 52 60" stroke="#1e1b4b" stroke-width="3" fill="none" stroke-linecap="round"/>
        <path d="M 68 60 Q 74 54 80 60" stroke="#1e1b4b" stroke-width="3" fill="none" stroke-linecap="round"/>
        <path d="M 55 75 Q 60 78 65 75" stroke="#1e1b4b" stroke-width="2" fill="none" stroke-linecap="round"/>
        <text x="88" y="38" font-size="11" font-weight="bold" fill="#a5b4fc" opacity="0.8">z</text>
        <text x="96" y="28" font-size="14" font-weight="bold" fill="#818cf8" opacity="0.9">Z</text>
      `;
    } else if (emotion === 'victory') {
      faceDetails = `
        <path d="M 39 58 Q 46 50 53 58" stroke="#1e1b4b" stroke-width="3.2" fill="none" stroke-linecap="round"/>
        <path d="M 67 58 Q 74 50 81 58" stroke="#1e1b4b" stroke-width="3.2" fill="none" stroke-linecap="round"/>
        <path d="M 51 73 Q 60 87 69 73 Z" fill="#e11d48"/>
        <polygon points="48,22 60,7 72,22" fill="#f59e0b" stroke="#d97706" stroke-width="1.5"/>
        <circle cx="60" cy="6" r="3.5" fill="#ef4444"/>
      `;
    } else {
      faceDetails = `
        <path d="M 38 43 Q 46 40 54 44" stroke="#312e81" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <path d="M 66 44 Q 74 40 82 43" stroke="#312e81" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <g class="toon-blink-eye">
          <circle cx="47" cy="58" r="5" fill="#0f172a"/><circle cx="49" cy="56" r="1.8" fill="#ffffff"/>
          <circle cx="73" cy="58" r="5" fill="#0f172a"/><circle cx="75" cy="56" r="1.8" fill="#ffffff"/>
        </g>
        <path d="M 54 75 Q 60 80 66 75" stroke="#1e1b4b" stroke-width="2.5" fill="none" stroke-linecap="round"/>
      `;
    }

    content = `
      <g class="avatar-body-group">
        <path d="M 60 25 C 60 14 70 10 72 15 C 74 21 66 19 64 25" fill="none" stroke="#a5b4fc" stroke-width="3.5" stroke-linecap="round"/>
        <circle cx="72" cy="15" r="5" fill="#fde047" class="toon-aura"/>
        <circle cx="60" cy="62" r="38" fill="url(#byteHeadGrad)" stroke="#4338ca" stroke-width="1.5"/>
        <circle cx="34" cy="69" r="6" fill="#f43f5e" opacity="0.35"/>
        <circle cx="86" cy="69" r="6" fill="#f43f5e" opacity="0.35"/>
        <circle cx="46" cy="58" r="15" fill="rgba(255,255,255,0.2)" stroke="#1e1b4b" stroke-width="3"/>
        <circle cx="74" cy="58" r="15" fill="rgba(255,255,255,0.2)" stroke="#1e1b4b" stroke-width="3"/>
        <line x1="61" y1="58" x2="59" y2="58" stroke="#1e1b4b" stroke-width="3.5"/>
        <path d="M 31 56 L 22 52" stroke="#1e1b4b" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M 89 56 L 98 52" stroke="#1e1b4b" stroke-width="2.5" stroke-linecap="round"/>
        ${faceDetails}
      </g>
    `;
  }

  return `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">${defs}${content}</svg>`;
}

function setCompanionEmotion(emotion, customPhrase = null) {
  const comp = appState.companion;
  if (!comp.enabled) return;

  comp.emotion = emotion;
  const persona = comp.persona || 'byte';
  const phrases = COMPANION_PHRASES[persona] || COMPANION_PHRASES.byte;

  let phrase = customPhrase;
  if (!phrase) {
    const list = phrases[emotion] || phrases.neutral;
    phrase = list[Math.floor(Math.random() * list.length)];
  }

  const avatarBox = document.getElementById('companionAvatarBox');
  if (avatarBox) {
    avatarBox.innerHTML = generateAvatarSvg(persona, emotion, comp.streak);

    avatarBox.classList.remove('avatar-tap', 'avatar-shock', 'avatar-victory', 'avatar-poke');
    void avatarBox.offsetWidth;
    if (emotion === 'typing') {
      avatarBox.classList.add('avatar-tap');
    } else if (emotion === 'error') {
      avatarBox.classList.add('avatar-shock');
    } else if (emotion === 'victory') {
      avatarBox.classList.add('avatar-victory');
    }
  }

  const moodLabel = document.getElementById('companionMoodLabel');
  if (moodLabel) {
    const emotionLabels = {
      neutral: 'Focused',
      typing: 'Flowing',
      streak: 'On Fire 🔥',
      error: 'Refocusing',
      idle: 'Resting ☕',
      victory: 'Victorious 🏆',
      poke: 'Playful ✨'
    };
    moodLabel.textContent = emotionLabels[emotion] || 'Focused';
  }

  const bubbleText = document.getElementById('companionBubbleText');
  if (bubbleText && phrase) {
    bubbleText.textContent = phrase;
  }

  const streakCount = document.getElementById('companionStreakCount');
  const streakBadge = document.getElementById('companionStreakBadge');
  if (streakCount) {
    streakCount.textContent = `${comp.streak} streak`;
  }
  if (streakBadge) {
    if (comp.streak >= 10) {
      streakBadge.classList.add('streak-on-fire');
    } else {
      streakBadge.classList.remove('streak-on-fire');
    }
  }

  const milestoneTag = document.getElementById('companionMilestoneTag');
  if (milestoneTag) {
    if (comp.streak >= 25) milestoneTag.textContent = 'Blazing!';
    else if (comp.streak >= 10) milestoneTag.textContent = 'Streak x' + comp.streak;
    else if (comp.emotion === 'victory') milestoneTag.textContent = 'Mastery!';
    else milestoneTag.textContent = 'Ready';
  }
}

function pokeCompanion() {
  const comp = appState.companion;
  const persona = comp.persona || 'byte';
  const phrases = COMPANION_PHRASES[persona] || COMPANION_PHRASES.byte;
  const pokeList = phrases.poke || ["Boop! ✨"];
  const phrase = pokeList[Math.floor(Math.random() * pokeList.length)];

  playCompanionChirp('poke');

  const avatarBox = document.getElementById('companionAvatarBox');
  if (avatarBox) {
    avatarBox.innerHTML = generateAvatarSvg(persona, 'typing', comp.streak);
    avatarBox.classList.remove('avatar-tap', 'avatar-shock', 'avatar-victory', 'avatar-poke');
    void avatarBox.offsetWidth;
    avatarBox.classList.add('avatar-poke');
  }

  const bubbleText = document.getElementById('companionBubbleText');
  if (bubbleText) bubbleText.textContent = phrase;

  const moodLabel = document.getElementById('companionMoodLabel');
  if (moodLabel) moodLabel.textContent = 'Playful ✨';

  clearTimeout(comp.errorTimer);
  comp.errorTimer = setTimeout(() => {
    setCompanionEmotion(comp.streak >= 15 ? 'streak' : 'neutral');
  }, 1600);
}

function switchCompanionPersona(targetPersona = null) {
  const personas = ['byte', 'pip', 'mochi'];
  let currentIdx = personas.indexOf(appState.companion.persona);
  if (currentIdx === -1) currentIdx = 0;

  if (targetPersona && personas.includes(targetPersona)) {
    appState.companion.persona = targetPersona;
  } else {
    appState.companion.persona = personas[(currentIdx + 1) % personas.length];
  }

  persistState();
  updateCompanionDisplay();
  playCompanionChirp('poke');
}

function toggleCompanionSpeech() {
  appState.companion.speechEnabled = !appState.companion.speechEnabled;
  persistState();
  updateCompanionDisplay();
}

function updateCompanionDisplay() {
  const comp = appState.companion;
  const stage = document.getElementById('companionStage');
  if (stage) {
    if (comp.enabled) {
      stage.classList.remove('companion-hidden');
    } else {
      stage.classList.add('companion-hidden');
    }
  }

  const bubble = document.getElementById('companionBubble');
  const btnMute = document.getElementById('btnToggleCompanionMute');
  if (bubble) {
    if (comp.speechEnabled) {
      bubble.classList.remove('bubble-hidden');
    } else {
      bubble.classList.add('bubble-hidden');
    }
  }
  if (btnMute) {
    if (comp.speechEnabled) {
      btnMute.classList.remove('muted');
      btnMute.title = "Mute companion speech encouragements";
    } else {
      btnMute.classList.add('muted');
      btnMute.title = "Unmute companion speech encouragements";
    }
  }

  const personaNameEl = document.getElementById('avatarPersonaName');
  if (personaNameEl) {
    const names = { byte: 'Byte', pip: 'Pip', mochi: 'Mochi' };
    personaNameEl.textContent = names[comp.persona] || 'Byte';
  }

  const personaSelect = document.getElementById('settingAvatarPersona');
  if (personaSelect) personaSelect.value = comp.persona;

  const showAvatarCheck = document.getElementById('settingShowAvatar');
  if (showAvatarCheck) showAvatarCheck.checked = comp.enabled;

  const speechCheck = document.getElementById('settingAvatarSpeech');
  if (speechCheck) speechCheck.checked = comp.speechEnabled;

  setCompanionEmotion(comp.emotion || 'neutral');
}

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

      // Make virtual keys fully interactive for mouse clicks and touch taps
      keyEl.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        let keyToSend = charVal;
        if (charVal === ' ' || item.key === 'Space') keyToSend = ' ';
        else if (charVal === 'enter' || item.key === 'Enter') keyToSend = 'Enter';
        else if (charVal === 'backspace' || item.key === 'Backspace') keyToSend = 'Backspace';
        else if (charVal === 'tab' || charVal === 'caps' || charVal === 'shift') return;

        handleKeystroke(keyToSend);
      });

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
  const fingerKey = expectedChar === '\n' ? 'right-pinky' : (FINGER_MAP[charLower] || FINGER_MAP[expectedChar] || 'thumb');
  const info = FINGER_INFO[fingerKey] || { name: 'Index Finger', label: 'Index', hand: 'Touch Guide' };

  // Update target preview text & badge
  const previewBadge = document.getElementById('fingerGuideBadge');
  const previewText = document.getElementById('targetKeyPreview');
  const leniencyTag = document.getElementById('leniencyIndicator');

  const displayKey = expectedChar === ' ' ? 'SPACE' : (expectedChar === '\n' ? 'ENTER' : expectedChar.toUpperCase());
  if (previewBadge) previewBadge.textContent = info.name;
  if (previewText) previewText.innerHTML = `Target Key: <strong>${escapeHtml(displayKey)}</strong>`;

  if (leniencyTag) {
    if (expectedChar === '\n') {
      leniencyTag.textContent = "Enter or Space";
      leniencyTag.style.display = "inline-block";
    } else if (appState.settings.lenientPunctuation && PUNCTUATION_SET.has(expectedChar)) {
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
  } else if (expectedChar === '\n') {
    targetKeyEl = document.querySelector('.key[data-key="enter"]');
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

  const charLower = (key || '').toLowerCase();
  let keyEl = null;
  if (key === ' ' || charLower === 'space') keyEl = document.querySelector('.key[data-key=" "]');
  else if (key === '\n' || charLower === 'enter') keyEl = document.querySelector('.key[data-key="enter"]');
  else if (charLower === 'backspace') keyEl = document.querySelector('.key[data-key="backspace"]');
  else {
    keyEl = document.querySelector(`.key[data-key="${charLower}"]`);
    if (!keyEl) keyEl = document.querySelector(`.key[data-sub="${key}"]`);
  }

  if (keyEl) {
    keyEl.classList.add('key-pressed');
    setTimeout(() => {
      keyEl.classList.remove('key-pressed');
    }, 120);
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

    const savedCompanion = localStorage.getItem('typeread_companion');
    if (savedCompanion) {
      try {
        const parsed = JSON.parse(savedCompanion);
        appState.companion = {
          ...appState.companion,
          enabled: parsed.enabled !== undefined ? parsed.enabled : true,
          speechEnabled: parsed.speechEnabled !== undefined ? parsed.speechEnabled : true,
          persona: parsed.persona || 'byte'
        };
      } catch (err) {}
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
    localStorage.setItem('typeread_companion', JSON.stringify({
      enabled: appState.companion.enabled,
      speechEnabled: appState.companion.speechEnabled,
      persona: appState.companion.persona
    }));
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

  // Update Companion UI
  updateCompanionDisplay();
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
  appState.companion.streak = 0;
  clearTimeout(appState.companion.idleTimer);
  clearTimeout(appState.companion.errorTimer);
  setCompanionEmotion('neutral', "Fresh start! Let's conquer this chapter 📖");
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
// Keystroke Hot Path Evaluator & Companion Emotional Reactor
// ============================================================

function onKeystrokeSuccess() {
  appState.companion.streak++;
  if (appState.companion.streak > appState.companion.maxStreak) {
    appState.companion.maxStreak = appState.companion.streak;
  }
  if (appState.companion.streak === 15 || appState.companion.streak === 30 || appState.companion.streak === 50) {
    playCompanionChirp('streak');
  }
  clearTimeout(appState.companion.errorTimer);
  const emotion = appState.companion.streak >= 15 ? 'streak' : 'typing';
  setCompanionEmotion(emotion);

  clearTimeout(appState.companion.idleTimer);
  appState.companion.idleTimer = setTimeout(() => {
    if (appState.session.status === 'active' || appState.session.status === 'idle') {
      setCompanionEmotion('idle');
    }
  }, 4200);
}

function onKeystrokeError() {
  appState.companion.streak = 0;
  clearTimeout(appState.companion.errorTimer);
  setCompanionEmotion('error');
  appState.companion.errorTimer = setTimeout(() => {
    setCompanionEmotion('neutral');
  }, 1400);

  clearTimeout(appState.companion.idleTimer);
  appState.companion.idleTimer = setTimeout(() => {
    if (appState.session.status === 'active' || appState.session.status === 'idle') {
      setCompanionEmotion('idle');
    }
  }, 4200);
}

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

  // Handle Enter / Newline normalization
  let inputKey = key;
  if (key === 'Enter') inputKey = '\n';

  // Ignore non-printable keys
  if (inputKey !== '\n' && inputKey.length !== 1) return;

  // Start timer on first keystroke
  if (appState.session.status !== 'active') {
    appState.session.status = 'active';
    appState.session.startTime = Date.now();
  }

  const expectedChar = text[idx];

  // Helper for flexible character matching (case, quotes, dashes, whitespace)
  const areEquivalentChars = (a, b) => {
    if (a === b) return true;
    if (appState.settings.ignoreCase && a.toLowerCase() === b.toLowerCase()) return true;
    // Quotes leniency (straight vs smart single and double quotes)
    if ("'\u2018\u2019`".includes(a) && "'\u2018\u2019`".includes(b)) return true;
    if ('"\u201c\u201d«»'.includes(a) && '"\u201c\u201d«»'.includes(b)) return true;
    // Dashes leniency (hyphen, en-dash, em-dash)
    if ('-\u2013\u2014_'.includes(a) && '-\u2013\u2014_'.includes(b)) return true;
    // Whitespace leniency (space, non-breaking space, tab)
    if (' \u00a0\t'.includes(a) && ' \u00a0\t'.includes(b)) return true;
    return false;
  };

  // ------------------------------------------------------------------
  // Rule 0: Newline / Paragraph Transition Handling
  // ------------------------------------------------------------------
  if (expectedChar === '\n' || expectedChar === '\r') {
    // If user pressed Enter, newline, or Space: accept and advance past all consecutive newlines!
    if (inputKey === '\n' || inputKey === ' ') {
      appState.session.keystrokes.push({
        expected: expectedChar,
        typed: inputKey,
        correct: true,
        skipped: false,
        timestamp: Date.now()
      });
      appState.session.currentIndex++;
      while (appState.session.currentIndex < text.length && 
             (text[appState.session.currentIndex] === '\n' || text[appState.session.currentIndex] === '\r')) {
        appState.session.currentIndex++;
      }
      playKeySound(false);
      animateKeyPressed(inputKey === '\n' ? 'Enter' : 'Space');
      onKeystrokeSuccess();
      renderPracticeView();
      if (appState.session.currentIndex >= text.length) finishSession();
      return;
    }

    // If user directly typed the next letter (e.g. typing 'W' in 'We' or 'R' in 'Readers' across newlines/spaces)
    let lookahead = idx;
    while (lookahead < text.length && (text[lookahead] === '\n' || text[lookahead] === '\r' || text[lookahead] === ' ' || PUNCTUATION_SET.has(text[lookahead]))) {
      lookahead++;
    }
    if (lookahead < text.length && areEquivalentChars(inputKey, text[lookahead])) {
      appState.session.currentIndex = lookahead + 1;
      appState.session.keystrokes.push({
        expected: text[lookahead],
        typed: inputKey,
        correct: true,
        skipped: false,
        timestamp: Date.now()
      });
      playKeySound(false);
      animateKeyPressed(inputKey);
      onKeystrokeSuccess();
      renderPracticeView();
      if (appState.session.currentIndex >= text.length) finishSession();
      return;
    }
  }

  // ------------------------------------------------------------------
  // Rule 1: Lenient Punctuation (Space skips punctuation without errors)
  // ------------------------------------------------------------------
  if (appState.settings.lenientPunctuation && PUNCTUATION_SET.has(expectedChar)) {
    // User pressed space on punctuation: skip punctuation gracefully!
    if (inputKey === ' ') {
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
      onKeystrokeSuccess();
      renderPracticeView();

      if (appState.session.currentIndex >= text.length) {
        finishSession();
      }
      return;
    }

    // If user typed the next word letter directly (e.g. typing 'w' or 'r' across punctuation and spaces)
    let lookahead = idx;
    while (lookahead < text.length && (PUNCTUATION_SET.has(text[lookahead]) || text[lookahead] === ' ')) {
      lookahead++;
    }
    if (lookahead < text.length && areEquivalentChars(inputKey, text[lookahead])) {
      appState.session.currentIndex = lookahead + 1;
      appState.session.keystrokes.push({
        expected: text[lookahead],
        typed: inputKey,
        correct: true,
        skipped: false,
        timestamp: Date.now()
      });
      playKeySound(false);
      animateKeyPressed(inputKey);
      onKeystrokeSuccess();
      renderPracticeView();

      if (appState.session.currentIndex >= text.length) {
        finishSession();
      }
      return;
    }
  }

  // ------------------------------------------------------------------
  // Rule 2: Character Evaluation with Case & Equivalent Leniency
  // ------------------------------------------------------------------
  const isCorrect = areEquivalentChars(inputKey, expectedChar);

  // Audio feedback
  playKeySound(!isCorrect);
  animateKeyPressed(inputKey);

  // Error handling modes & companion reaction
  if (!isCorrect) {
    onKeystrokeError();
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
  } else {
    onKeystrokeSuccess();
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
    typed: inputKey,
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

  // Companion Victory Cheer & Celebration Animation
  setCompanionEmotion('victory', "Incredible completion! 🎉");
  playCompanionChirp('victory');
  const completionAvatarBox = document.getElementById('completionAvatarBox');
  if (completionAvatarBox) {
    completionAvatarBox.innerHTML = generateAvatarSvg(appState.companion.persona, 'victory', appState.companion.streak);
    completionAvatarBox.classList.add('avatar-victory');
  }

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
    .replace(/[\u00a0\u2000-\u200b\u202f]/g, ' ')
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

  if (hiddenInput) {
    hiddenInput.addEventListener('input', () => {
      const val = hiddenInput.value;
      if (val) {
        for (const ch of val) {
          handleKeystroke(ch);
        }
        hiddenInput.value = '';
      }
    });
  }

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

    // Do not intercept browser shortcuts like Ctrl+R, Ctrl+W, Ctrl+C, Ctrl+V, etc.
    if (e.ctrlKey || e.altKey || e.metaKey) return;

    if (e.key === 'Backspace' || e.key === 'Enter' || e.key.length === 1) {
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

  // Settings changes: Companion Toggles & Persona
  const settingShowAvatar = document.getElementById('settingShowAvatar');
  if (settingShowAvatar) {
    settingShowAvatar.addEventListener('change', (e) => {
      appState.companion.enabled = e.target.checked;
      persistState();
      updateCompanionDisplay();
    });
  }

  const settingAvatarSpeech = document.getElementById('settingAvatarSpeech');
  if (settingAvatarSpeech) {
    settingAvatarSpeech.addEventListener('change', (e) => {
      appState.companion.speechEnabled = e.target.checked;
      persistState();
      updateCompanionDisplay();
    });
  }

  const settingAvatarPersona = document.getElementById('settingAvatarPersona');
  if (settingAvatarPersona) {
    settingAvatarPersona.addEventListener('change', (e) => {
      switchCompanionPersona(e.target.value);
    });
  }

  // Interactive Companion Controls
  const companionAvatarWrap = document.getElementById('companionAvatarWrap');
  if (companionAvatarWrap) {
    companionAvatarWrap.addEventListener('click', () => {
      pokeCompanion();
    });
  }

  const btnSwitchAvatar = document.getElementById('btnSwitchAvatar');
  if (btnSwitchAvatar) {
    btnSwitchAvatar.addEventListener('click', () => {
      switchCompanionPersona();
    });
  }

  const btnToggleCompanionMute = document.getElementById('btnToggleCompanionMute');
  if (btnToggleCompanionMute) {
    btnToggleCompanionMute.addEventListener('click', () => {
      toggleCompanionSpeech();
    });
  }

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

