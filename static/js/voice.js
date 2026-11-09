/**
 * SunoLocal - Web Speech API Multilingual Voice Engine
 * Supports 6 Languages:
 * 1. Kannada (kn-IN)
 * 2. Telugu (te-IN)
 * 3. Tamil (ta-IN)
 * 4. Malayalam (ml-IN)
 * 5. Hindi (hi-IN)
 * 6. English (en-IN)
 *
 * ARCHITECTURAL DESIGN:
 * - Zero circular / recursive calls.
 * - loadVoices() strictly retrieves and stores voices.
 * - getVoiceForLanguage() strictly queries stored voices without side effects.
 * - getVoiceDiagnostics() strictly inspects current state without mutating or reloading.
 * - notifyDiagnostics() broadcasts already-computed diagnostics to listeners.
 * - Never silently reads regional language text using an English voice!
 */

class VoiceEngine {
  constructor() {
    this.synth = window.speechSynthesis || null;
    this.voices = [];
    this.currentUtterance = null;
    this.isPlaying = false;
    this.isPaused = false;
    this.playbackStatus = "stopped"; // "stopped", "playing", "paused", "error"
    this.currentRate = 1.0;
    this.currentLang = "English";
    this.currentText = "";
    this.currentTitle = "";
    this.activeVoice = null;
    this.listeners = [];

    // Language code map
    this.LANG_CODES = {
      "English": "en-IN",
      "Kannada": "kn-IN",
      "Telugu": "te-IN",
      "Tamil": "ta-IN",
      "Malayalam": "ml-IN",
      "Hindi": "hi-IN"
    };

    this.KANNADA_MISSING_MESSAGE = "Kannada voice is not available on this device. Please install a Kannada speech voice or open in Microsoft Edge (which includes natural Indian voices).";
    this.ENGLISH_MISSING_MESSAGE = "English voice is not available on this device. Please check your browser audio/speech settings.";

    if (this.synth) {
      // 1. Initial voice load (safe, non-recursive)
      this.loadVoices();

      // 2. Safe asynchronous listener on voiceschanged event
      if (typeof this.synth.onvoiceschanged !== "undefined") {
        this.synth.onvoiceschanged = () => {
          this.loadVoices();
          this.notifyDiagnostics();
        };
      }

      // 3. Fallback polling for Chromium browsers
      let pollCount = 0;
      const pollTimer = setInterval(() => {
        pollCount++;
        if (this.voices.length > 0 || pollCount >= 8) {
          clearInterval(pollTimer);
          if (this.voices.length === 0) {
            this.loadVoices();
          }
          this.notifyDiagnostics();
        } else {
          this.loadVoices();
          if (this.voices.length > 0) {
            this.notifyDiagnostics();
            clearInterval(pollTimer);
          }
        }
      }, 250);
    } else {
      console.warn("[VoiceEngine] Browser does not support window.speechSynthesis.");
    }
  }

  /**
   * Pure voice retrieval and storage.
   * No circular calls.
   */
  loadVoices() {
    if (!this.synth) {
      this.voices = [];
      return [];
    }
    try {
      const list = this.synth.getVoices();
      if (Array.isArray(list) && list.length > 0) {
        this.voices = list;
      }
    } catch (err) {
      console.error("[VoiceEngine] Error in loadVoices():", err);
    }
    return this.voices;
  }

  refreshVoices() {
    this.loadVoices();
    this.notifyDiagnostics();
  }

  normalizeLanguage(lang) {
    if (!lang) return "English";
    const l = String(lang).trim().toLowerCase();
    if (l.startsWith("kn") || l.includes("kannada") || l.includes("ಕನ್ನಡ")) return "Kannada";
    if (l.startsWith("te") || l.includes("telugu") || l.includes("తెలుగు")) return "Telugu";
    if (l.startsWith("ta") || l.includes("tamil") || l.includes("தமிழ்")) return "Tamil";
    if (l.startsWith("ml") || l.includes("malayalam") || l.includes("മലയാളം")) return "Malayalam";
    if (l.startsWith("hi") || l.includes("hindi") || l.includes("हिन्दी")) return "Hindi";
    return "English";
  }

  /**
   * Pure search over stored this.voices for any of the 6 languages
   */
  getVoiceForLanguage(langName) {
    if (!this.voices || this.voices.length === 0) return null;
    const norm = this.normalizeLanguage(langName);

    if (norm === "Kannada") {
      // 1. Strict kn-in
      let v = this.voices.find(x => (x.lang || "").toLowerCase().replace("_", "-") === "kn-in");
      if (v) return v;
      // 2. Starts with kn or name contains kannada
      return this.voices.find(x => {
        const l = (x.lang || "").toLowerCase().replace("_", "-");
        const n = (x.name || "").toLowerCase();
        return l.startsWith("kn") || n.includes("kannada") || n.includes("kn-in") || n.includes("ಕನ್ನಡ");
      }) || null;
    }

    if (norm === "Telugu") {
      // 1. Strict te-in
      let v = this.voices.find(x => (x.lang || "").toLowerCase().replace("_", "-") === "te-in");
      if (v) return v;
      // 2. Starts with te or name contains telugu
      return this.voices.find(x => {
        const l = (x.lang || "").toLowerCase().replace("_", "-");
        const n = (x.name || "").toLowerCase();
        return l.startsWith("te") || n.includes("telugu") || n.includes("te-in") || n.includes("తెలుగు");
      }) || null;
    }

    if (norm === "Tamil") {
      // 1. Strict ta-in
      let v = this.voices.find(x => (x.lang || "").toLowerCase().replace("_", "-") === "ta-in");
      if (v) return v;
      // 2. Starts with ta or name contains tamil
      return this.voices.find(x => {
        const l = (x.lang || "").toLowerCase().replace("_", "-");
        const n = (x.name || "").toLowerCase();
        return l.startsWith("ta") || n.includes("tamil") || n.includes("ta-in") || n.includes("தமிழ்");
      }) || null;
    }

    if (norm === "Malayalam") {
      // 1. Strict ml-in
      let v = this.voices.find(x => (x.lang || "").toLowerCase().replace("_", "-") === "ml-in");
      if (v) return v;
      // 2. Starts with ml or name contains malayalam
      return this.voices.find(x => {
        const l = (x.lang || "").toLowerCase().replace("_", "-");
        const n = (x.name || "").toLowerCase();
        return l.startsWith("ml") || n.includes("malayalam") || n.includes("ml-in") || n.includes("മലയാളം");
      }) || null;
    }

    if (norm === "Hindi") {
      // 1. Strict hi-in
      let v = this.voices.find(x => (x.lang || "").toLowerCase().replace("_", "-") === "hi-in");
      if (v) return v;
      // 2. Starts with hi or name contains hindi
      return this.voices.find(x => {
        const l = (x.lang || "").toLowerCase().replace("_", "-");
        const n = (x.name || "").toLowerCase();
        return l.startsWith("hi") || n.includes("hindi") || n.includes("hi-in") || n.includes("हिन्दी");
      }) || null;
    }

    // Default English
    let vEnIn = this.voices.find(x => (x.lang || "").toLowerCase().replace("_", "-") === "en-in");
    if (vEnIn) return vEnIn;
    let vEn = this.voices.find(x => (x.lang || "").toLowerCase().startsWith("en"));
    if (vEn) return vEn;
    return this.voices.find(x => x.default) || this.voices[0] || null;
  }

  // Legacy helper
  getKannadaVoice() {
    return this.getVoiceForLanguage("Kannada");
  }

  getEnglishVoice() {
    return this.getVoiceForLanguage("English");
  }

  /**
   * Diagnostic snapshot across all 6 languages
   */
  getVoiceDiagnostics() {
    const knVoice = this.getVoiceForLanguage("Kannada");
    const teVoice = this.getVoiceForLanguage("Telugu");
    const taVoice = this.getVoiceForLanguage("Tamil");
    const mlVoice = this.getVoiceForLanguage("Malayalam");
    const hiVoice = this.getVoiceForLanguage("Hindi");
    const enVoice = this.getVoiceForLanguage("English");

    const activeVoice = this.getVoiceForLanguage(this.currentLang);

    return {
      isSupported: !!this.synth,
      voicesCount: this.voices.length,
      voices: this.voices.map(v => {
        const l = (v.lang || "").toLowerCase().replace("_", "-");
        return {
          name: v.name,
          lang: v.lang,
          default: !!v.default,
          localService: !!v.localService
        };
      }),
      languages: {
        Kannada: { voice: knVoice, isAvailable: !!knVoice, code: "kn-IN", nativeName: "ಕನ್ನಡ" },
        Telugu: { voice: teVoice, isAvailable: !!teVoice, code: "te-IN", nativeName: "తెలుగు" },
        Tamil: { voice: taVoice, isAvailable: !!taVoice, code: "ta-IN", nativeName: "தமிழ்" },
        Malayalam: { voice: mlVoice, isAvailable: !!mlVoice, code: "ml-IN", nativeName: "മലയാളം" },
        Hindi: { voice: hiVoice, isAvailable: !!hiVoice, code: "hi-IN", nativeName: "हिन्दी" },
        English: { voice: enVoice, isAvailable: !!enVoice, code: "en-IN", nativeName: "English" }
      },
      // Backwards compatibility keys
      kannadaVoice: knVoice ? { name: knVoice.name, lang: knVoice.lang } : null,
      englishVoice: enVoice ? { name: enVoice.name, lang: enVoice.lang } : null,
      isKannadaAvailable: !!knVoice,
      activeLanguage: this.currentLang,
      activeVoiceName: activeVoice ? activeVoice.name : "None",
      playbackStatus: this.playbackStatus,
      isPlaying: this.isPlaying,
      isPaused: this.isPaused
    };
  }

  notifyDiagnostics() {
    const diag = this.getVoiceDiagnostics();
    for (let i = 0; i < this.listeners.length; i++) {
      try {
        this.listeners[i](diag);
      } catch (err) {
        console.error("[VoiceEngine] Listener error:", err);
      }
    }
  }

  onVoiceChange(callback) {
    if (typeof callback === "function") {
      this.listeners.push(callback);
      try {
        callback(this.getVoiceDiagnostics());
      } catch (e) {
        console.error("[VoiceEngine] onVoiceChange error:", e);
      }
    }
  }

  /**
   * Speaks text in any of the 6 languages.
   * STRICT SAFETY: Never silently reads regional language text using an English voice!
   */
  speak(text, lang = "English", title = "Audio Briefing", onEndCallback = null) {
    if (!this.synth) {
      this.showNotice("Speech synthesis is not supported on this device/browser.", "danger");
      return;
    }

    // Stop ongoing speech
    this.stop();

    const normalizedLang = this.normalizeLanguage(lang);
    this.currentLang = normalizedLang;
    this.currentText = text || "";
    this.currentTitle = title || "Audio Briefing";

    const targetVoice = this.getVoiceForLanguage(normalizedLang);
    const targetCode = this.LANG_CODES[normalizedLang] || "en-IN";

    // STRICT CHECK: For regional languages (and English if no voices), verify voice availability
    if (normalizedLang === "Kannada" && !targetVoice) {
      this.isPlaying = false;
      this.isPaused = false;
      this.playbackStatus = "stopped";
      this.activeVoice = null;

      const missingMsg = "Kannada voice is not available on this device. Please install a Kannada speech voice or open in Microsoft Edge (which includes natural Indian voices).";
      console.warn(`[VoiceEngine] Speech halted: No Kannada (${targetCode}) voice installed.`);

      this.showNotice(missingMsg, "danger", true, "Kannada");
      this.updateDockUI(false, false, title, "Kannada");
      this.updateDetailControls(false, false);
      this.notifyDiagnostics();

      if (typeof onEndCallback === "function") {
        onEndCallback({ error: "voice_missing", language: "Kannada", message: missingMsg });
      }
      return;
    }

    if (normalizedLang !== "English" && !targetVoice) {
      this.isPlaying = false;
      this.isPaused = false;
      this.playbackStatus = "stopped";
      this.activeVoice = null;

      const missingMsg = `${normalizedLang} voice is not available on this device. Please install a ${normalizedLang} speech voice or open in Microsoft Edge (which includes natural Indian voices).`;
      console.warn(`[VoiceEngine] Speech halted: No ${normalizedLang} (${targetCode}) voice installed.`);

      this.showNotice(missingMsg, "danger", true, normalizedLang);
      this.updateDockUI(false, false, title, normalizedLang);
      this.updateDetailControls(false, false);
      this.notifyDiagnostics();

      if (typeof onEndCallback === "function") {
        onEndCallback({ error: "voice_missing", language: normalizedLang, message: missingMsg });
      }
      return;
    }

    if (normalizedLang === "English" && this.voices.length > 0 && !targetVoice) {
      this.isPlaying = false;
      this.isPaused = false;
      this.playbackStatus = "stopped";
      this.activeVoice = null;

      const missingMsg = "English voice is not available on this device. Please check your browser audio/speech settings.";
      console.warn(`[VoiceEngine] Speech halted: No English voice found.`);

      this.showNotice(missingMsg, "danger", true, "English");
      this.updateDockUI(false, false, title, "English");
      this.updateDetailControls(false, false);
      this.notifyDiagnostics();

      if (typeof onEndCallback === "function") {
        onEndCallback({ error: "voice_missing", language: "English", message: missingMsg });
      }
      return;
    }

    this.activeVoice = targetVoice;

    if (!text || text.trim() === "") {
      this.showNotice("No text provided for audio narration.", "warning");
      return;
    }

    this.hideNotice();

    try {
      this.currentUtterance = new SpeechSynthesisUtterance(text);
      this.currentUtterance.rate = this.currentRate;
      this.currentUtterance.pitch = 1.0;

      if (this.activeVoice) {
        this.currentUtterance.voice = this.activeVoice;
        this.currentUtterance.lang = this.activeVoice.lang || targetCode;
      } else {
        this.currentUtterance.lang = targetCode;
      }

      this.isPlaying = true;
      this.isPaused = false;
      this.playbackStatus = "playing";

      this.currentUtterance.onstart = () => {
        this.isPlaying = true;
        this.isPaused = false;
        this.playbackStatus = "playing";
        this.updateDockUI(true, false, this.currentTitle, normalizedLang);
        this.updateDetailControls(true, false);
        this.notifyDiagnostics();
      };

      this.currentUtterance.onpause = () => {
        this.isPaused = true;
        this.playbackStatus = "paused";
        this.updateDockUI(true, true, this.currentTitle, normalizedLang);
        this.updateDetailControls(true, true);
        this.notifyDiagnostics();
      };

      this.currentUtterance.onresume = () => {
        this.isPaused = false;
        this.playbackStatus = "playing";
        this.updateDockUI(true, false, this.currentTitle, normalizedLang);
        this.updateDetailControls(true, false);
        this.notifyDiagnostics();
      };

      this.currentUtterance.onend = () => {
        this.isPlaying = false;
        this.isPaused = false;
        this.playbackStatus = "stopped";
        this.updateDockUI(false, false);
        this.updateDetailControls(false, false);
        this.notifyDiagnostics();
        if (typeof onEndCallback === "function") {
          onEndCallback({ success: true });
        }
      };

      this.currentUtterance.onerror = (e) => {
        console.error("[VoiceEngine] SpeechSynthesis error:", e);
        this.isPlaying = false;
        this.isPaused = false;
        this.playbackStatus = "error";
        this.updateDockUI(false, false);
        this.updateDetailControls(false, false);
        this.notifyDiagnostics();
        if (typeof onEndCallback === "function") {
          onEndCallback({ error: e });
        }
      };

      setTimeout(() => {
        if (this.synth) {
          this.synth.speak(this.currentUtterance);
        }
      }, 35);

    } catch (err) {
      console.error("[VoiceEngine] Error in speak():", err);
      this.isPlaying = false;
      this.isPaused = false;
      this.playbackStatus = "error";
      this.updateDockUI(false, false);
      this.updateDetailControls(false, false);
      this.notifyDiagnostics();
    }
  }

  pause() {
    if (this.synth && this.synth.speaking && !this.synth.paused) {
      this.synth.pause();
      this.isPaused = true;
      this.playbackStatus = "paused";
      this.updateDockUI(true, true, this.currentTitle, this.currentLang);
      this.updateDetailControls(true, true);
      this.notifyDiagnostics();
    }
  }

  resume() {
    if (this.synth && this.synth.paused) {
      this.synth.resume();
      this.isPaused = false;
      this.playbackStatus = "playing";
      this.updateDockUI(true, false, this.currentTitle, this.currentLang);
      this.updateDetailControls(true, false);
      this.notifyDiagnostics();
    } else if (this.currentText && !this.isPlaying) {
      this.speak(this.currentText, this.currentLang, this.currentTitle);
    }
  }

  stop() {
    if (this.synth) {
      this.synth.cancel();
    }
    this.isPlaying = false;
    this.isPaused = false;
    this.playbackStatus = "stopped";
    this.updateDockUI(false, false);
    this.updateDetailControls(false, false);
    this.notifyDiagnostics();
  }

  setRate(rate) {
    this.currentRate = parseFloat(rate) || 1.0;
    if (this.isPlaying && !this.isPaused && this.currentText) {
      const text = this.currentText;
      const lang = this.currentLang;
      const title = this.currentTitle;
      this.stop();
      this.speak(text, lang, title);
    }
  }

  showNotice(message, type = "warning", isMissing = false, lang = "") {
    const banner = document.getElementById("tts-notice-banner");
    if (banner) {
      banner.className = `alert alert-${type} shadow-sm d-flex align-items-center gap-2 mb-3`;
      banner.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill fs-5 flex-shrink-0"></i>
        <div class="flex-grow-1">
          <strong>Audio Notice:</strong> ${message}
          ${isMissing ? `<div class="mt-2"><button type="button" class="btn btn-sm btn-dark" data-bs-toggle="modal" data-bs-target="#voiceDiagnosticModal"><i class="bi bi-gear-fill me-1"></i> How to enable ${lang} voice on Windows / Edge / Chrome</button></div>` : ''}
        </div>
        <button type="button" class="btn-close" onclick="this.parentElement.classList.add('d-none')"></button>
      `;
      banner.classList.remove("d-none");
    }

    if (typeof showToast === "function") {
      showToast(message, type);
    } else {
      console.warn("[VoiceEngine Alert]", message);
    }
  }

  hideNotice() {
    const banner = document.getElementById("tts-notice-banner");
    if (banner) {
      banner.classList.add("d-none");
    }
  }

  updateDetailControls(isPlaying, isPaused) {
    const playBtn = document.getElementById("detail-play-btn");
    const playLabel = document.getElementById("detail-play-label");
    const playIcon = playBtn ? playBtn.querySelector("i") : null;

    if (!playBtn) return;

    if (isPlaying && !isPaused) {
      if (playLabel) playLabel.textContent = "Pause Audio";
      if (playIcon) playIcon.className = "bi bi-pause-circle-fill fs-5";
      playBtn.className = "btn btn-warning px-4 py-2 d-flex align-items-center gap-2";
    } else if (isPaused) {
      if (playLabel) playLabel.textContent = "Resume Audio";
      if (playIcon) playIcon.className = "bi bi-play-circle-fill fs-5";
      playBtn.className = "btn btn-success px-4 py-2 d-flex align-items-center gap-2";
    } else {
      if (playLabel) playLabel.textContent = "Play Full Audio Report";
      if (playIcon) playIcon.className = "bi bi-play-circle-fill fs-5";
      playBtn.className = "btn btn-primary-custom px-4 py-2 d-flex align-items-center gap-2";
    }
  }

  updateDockUI(isActive, isPaused, title = "", lang = "English") {
    const dock = document.getElementById("global-audio-dock");
    const playBtn = document.getElementById("audio-dock-toggle-btn");
    const titleElem = document.getElementById("audio-dock-title");
    const langElem = document.getElementById("audio-dock-lang");
    const pulseElem = document.getElementById("audio-dock-pulse");

    if (!dock) return;

    if (isActive) {
      dock.style.display = "flex";
      if (titleElem) titleElem.textContent = title;
      if (langElem) {
        const code = this.LANG_CODES[lang] || "en-IN";
        langElem.textContent = `${lang} (${code})`;
        langElem.className = lang === "English" ? "badge bg-secondary mb-1" : "badge bg-warning text-dark mb-1";
      }

      if (playBtn) {
        playBtn.innerHTML = isPaused ? '<i class="bi bi-play-fill fs-5"></i>' : '<i class="bi bi-pause-fill fs-5"></i>';
        playBtn.setAttribute("aria-label", isPaused ? "Resume Audio" : "Pause Audio");
      }

      if (pulseElem) {
        pulseElem.style.display = isPaused ? "none" : "block";
      }
    } else {
      dock.style.display = "none";
    }
  }
}

// Global Singleton Instance
window.sunoVoice = new VoiceEngine();

/**
 * Renders the Multilingual Voice Diagnostic Section
 */
function renderVoiceDiagnostics(diag) {
  const container = document.getElementById("voice-diagnostic-content");
  if (!container) return;

  const langCards = Object.entries(diag.languages || {}).map(([langName, info]) => {
    const badge = info.isAvailable
      ? `<span class="badge bg-success small"><i class="bi bi-check-circle-fill me-1"></i> Available</span>`
      : `<span class="badge bg-danger small"><i class="bi bi-x-circle-fill me-1"></i> Not Installed</span>`;
    
    const voiceText = info.isAvailable
      ? `<div class="small text-truncate mt-1 text-secondary" title="${info.voice.name}">Voice: <strong>${info.voice.name}</strong></div>`
      : `<div class="small text-danger mt-1">Requires ${info.code} speech pack</div>`;

    return `
      <div class="col-md-4 col-sm-6">
        <div class="p-3 border rounded-3 bg-white h-100 shadow-sm">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="fw-bold">${langName} (${info.nativeName})</span>
            ${badge}
          </div>
          <div class="small text-muted">Code: <code>${info.code}</code></div>
          ${voiceText}
        </div>
      </div>
    `;
  }).join("");

  let voicesRows = "";
  if (!diag.voices || diag.voices.length === 0) {
    voicesRows = `<tr><td colspan="4" class="text-center text-muted py-3">No voices detected yet. Click "Refresh Voices" or reload the page.</td></tr>`;
  } else {
    diag.voices.forEach((v, idx) => {
      voicesRows += `
        <tr>
          <td>${idx + 1}</td>
          <td>${v.name} ${v.default ? '<span class="badge bg-secondary ms-1">Default</span>' : ''}</td>
          <td><span class="badge bg-light text-dark border">${v.lang}</span></td>
          <td>${v.localService ? 'Local (Offline)' : 'Remote / Cloud'}</td>
        </tr>
      `;
    });
  }

  container.innerHTML = `
    <!-- Top 6 Languages Status -->
    <h6 class="fw-bold text-uppercase text-secondary small mb-2">Multilingual Voice Availability (6 Languages)</h6>
    <div class="row g-2 mb-4">
      ${langCards}
    </div>

    <!-- Active Voice & Controls -->
    <div class="p-3 border rounded-3 bg-white mb-4 d-flex justify-content-between align-items-center">
      <div>
        <span class="small text-muted fw-bold d-block">Active Language & Voice:</span>
        <span class="fs-6 fw-bold text-primary">${diag.activeLanguage} &mdash; ${diag.activeVoiceName}</span>
      </div>
      <div class="small text-secondary">
        Total browser voices loaded: <strong>${diag.voicesCount}</strong>
      </div>
    </div>

    <!-- Interactive Test Buttons for All 6 Languages -->
    <div class="p-3 border rounded-3 bg-light mb-4">
      <h6 class="fw-bold mb-2">Test Voice Output (All 6 Languages):</h6>
      <div class="d-flex flex-wrap gap-2">
        <button type="button" class="btn btn-outline-primary btn-sm" onclick="window.sunoVoice.speak('Hello! Welcome to SunoLocal. English voice is working.', 'English', 'English Test')">
          <i class="bi bi-volume-up me-1"></i> English
        </button>
        <button type="button" class="btn btn-outline-warning btn-sm text-dark fw-bold" onclick="window.sunoVoice.speak('ನಮಸ್ಕಾರ, ಸುನೋ ಲೋಕಲ್ ಕನ್ನಡ ಧ್ವನಿ ಯಶಸ್ವಿಯಾಗಿ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿದೆ.', 'Kannada', 'Kannada Test')">
          <i class="bi bi-volume-up-fill me-1"></i> ಕನ್ನಡ (Kannada)
        </button>
        <button type="button" class="btn btn-outline-info btn-sm text-dark" onclick="window.sunoVoice.speak('నమస్కారం, సునో లోకల్ తెలుగు వాయిస్ విజయవంతంగా పనిచేస్తోంది.', 'Telugu', 'Telugu Test')">
          <i class="bi bi-volume-up-fill me-1"></i> తెలుగు (Telugu)
        </button>
        <button type="button" class="btn btn-outline-success btn-sm" onclick="window.sunoVoice.speak('வணக்கம், சுனோ லோக்கல் தமிழ் குரல் வெற்றிகரமாக செயல்படுகிறது.', 'Tamil', 'Tamil Test')">
          <i class="bi bi-volume-up-fill me-1"></i> தமிழ் (Tamil)
        </button>
        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="window.sunoVoice.speak('നമസ്കാരം, സുനോ ലോക്കൽ മലയാളം ശബ്ദം വിജയകരമായി പ്രവർത്തിക്കുന്നു.', 'Malayalam', 'Malayalam Test')">
          <i class="bi bi-volume-up-fill me-1"></i> മലയാളം (Malayalam)
        </button>
        <button type="button" class="btn btn-outline-danger btn-sm" onclick="window.sunoVoice.speak('नमस्कार, सुनो लोकल हिन्दी वाणी सफलतापूर्वक कार्य कर रही है।', 'Hindi', 'Hindi Test')">
          <i class="bi bi-volume-up-fill me-1"></i> हिन्दी (Hindi)
        </button>
        <button type="button" class="btn btn-dark btn-sm ms-auto" onclick="window.sunoVoice.stop()">
          <i class="bi bi-stop-fill me-1"></i> Stop Test
        </button>
      </div>
    </div>

    <!-- Edge / Windows Setup Guide -->
    <div class="alert alert-info small p-3 mb-4">
      <h6 class="fw-bold mb-1"><i class="bi bi-browser-edge me-1"></i> Recommended for Instant Voice Support on Windows:</h6>
      <p class="mb-1">
        Open SunoLocal in <strong>Microsoft Edge</strong>. Edge includes high-definition Microsoft Natural online voices pre-configured for Indian languages (Kannada, Telugu, Tamil, Malayalam, Hindi, and English) with zero installation required!
      </p>
      <div class="small text-muted">
        For Google Chrome or offline support, install the corresponding language speech pack in <em>Windows Settings &rarr; Time & Language &rarr; Language & Region &rarr; Add a language</em>.
      </div>
    </div>

    <!-- Available Voices Table -->
    <div class="d-flex justify-content-between align-items-center mb-2">
      <h6 class="fw-bold mb-0">Detected Browser Voices (${diag.voicesCount})</h6>
      <button type="button" class="btn btn-sm btn-outline-secondary" onclick="window.sunoVoice.refreshVoices()">
        <i class="bi bi-arrow-clockwise me-1"></i> Refresh Voices
      </button>
    </div>
    <div class="table-responsive" style="max-height: 240px; overflow-y: auto;">
      <table class="table table-sm table-hover small border mb-0">
        <thead class="table-light sticky-top">
          <tr>
            <th style="width: 40px;">#</th>
            <th>Voice Name</th>
            <th>Language Code</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody>
          ${voicesRows}
        </tbody>
      </table>
    </div>
  `;
}

// Wire up event listeners on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  window.sunoVoice.onVoiceChange(renderVoiceDiagnostics);

  // Quick Listen button event listeners for Opportunities AND News Articles
  document.querySelectorAll(".btn-listen-trigger").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const itemId = btn.getAttribute("data-id");
      const itemType = btn.getAttribute("data-type") || "opportunity";
      const lang = btn.getAttribute("data-lang") || "English";
      const title = btn.getAttribute("data-title") || "Report";

      // If user clicked non-English and voice is missing, halt directly
      const normLang = window.sunoVoice.normalizeLanguage(lang);
      if (normLang !== "English" && !window.sunoVoice.getVoiceForLanguage(normLang)) {
        window.sunoVoice.showNotice(
          `${normLang} voice is not available on this device. Please install a ${normLang} speech voice or open in Microsoft Edge.`,
          "danger",
          true,
          normLang
        );
        return;
      }

      btn.disabled = true;
      const originalHtml = btn.innerHTML;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Loading...';

      try {
        const url = itemType === "news" 
          ? `/api/news/listen/${itemId}?lang=${encodeURIComponent(lang)}` 
          : `/api/listen/${itemId}?lang=${encodeURIComponent(lang)}`;

        const response = await fetch(url);
        const data = await response.json();

        if (data.success && data.speech_text) {
          window.sunoVoice.speak(data.speech_text, lang, data.title || title, () => {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
          });
          btn.innerHTML = `<i class="bi bi-volume-up-fill me-1 text-success"></i> Playing (${lang.substring(0, 2)})`;
        } else {
          window.sunoVoice.showNotice("Could not load audio for this item.", "warning");
          btn.innerHTML = originalHtml;
          btn.disabled = false;
        }
      } catch (err) {
        console.error("Error loading audio:", err);
        window.sunoVoice.showNotice("Network error loading audio data.", "danger");
        btn.innerHTML = originalHtml;
        btn.disabled = false;
      }
    });
  });

  // Global Audio Dock Controls
  const toggleBtn = document.getElementById("audio-dock-toggle-btn");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      if (window.sunoVoice.isPaused) {
        window.sunoVoice.resume();
      } else if (window.sunoVoice.isPlaying) {
        window.sunoVoice.pause();
      } else {
        window.sunoVoice.resume();
      }
    });
  }

  const stopBtn = document.getElementById("audio-dock-stop-btn");
  if (stopBtn) {
    stopBtn.addEventListener("click", () => {
      window.sunoVoice.stop();
    });
  }

  const rateSelect = document.getElementById("audio-dock-rate");
  if (rateSelect) {
    rateSelect.addEventListener("change", (e) => {
      window.sunoVoice.setRate(e.target.value);
    });
  }
});
