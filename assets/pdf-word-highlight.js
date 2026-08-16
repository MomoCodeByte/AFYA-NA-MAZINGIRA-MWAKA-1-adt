(function () {
  "use strict";

  var synth = window.speechSynthesis;
  if (!synth || !window.SpeechSynthesisUtterance) return;

  var nativeSpeak = synth.speak.bind(synth);
  var activeWord = null;
  var reading = false;
  var fallbackTimer = null;
  var currentSegments = [];
  var currentSegment = 0;
  var currentRate = 1;
  var currentVolume = 1;
  var panel = null;
  var recordedAudio = null;
  var recordedEntry = null;
  var recordedCue = 0;
  var timingsPromise = null;

  function normalize(value) {
    return String(value || "").toLocaleLowerCase("sw-TZ").replace(/[^a-z0-9\u00c0-\u024f]+/g, "");
  }

  function words() {
    return Array.prototype.slice.call(document.querySelectorAll(".pdf-word"));
  }

  function clear() {
    if (activeWord) activeWord.classList.remove("pdf-word-active");
    activeWord = null;
  }

  function stopReading() {
    reading = false;
    synth.cancel();
    if (fallbackTimer) window.clearInterval(fallbackTimer);
    fallbackTimer = null;
    if (recordedAudio) recordedAudio.pause();
    clear();
  }

  function findStart(text, pageWords) {
    var utteranceWords = String(text || "").trim().split(/\s+/).map(normalize).filter(Boolean);
    if (!utteranceWords.length) return 0;
    for (var i = 0; i < pageWords.length; i += 1) {
      if (normalize(pageWords[i].textContent) === utteranceWords[0]) return i;
    }
    return 0;
  }

  function oneSwahiliVoice() {
    var available = synth.getVoices();
    return available.find(function (voice) { return /rehema/i.test(voice.name) && /^sw[-_]TZ$/i.test(voice.lang); }) ||
      available.find(function (voice) { return /rehema/i.test(voice.name); }) ||
      available.find(function (voice) { return /^sw[-_]TZ$/i.test(voice.lang); }) ||
      available.find(function (voice) { return /^sw([_-]|$)/i.test(voice.lang); }) ||
      available.find(function (voice) { return /female|zira|susan|samantha/i.test(voice.name); }) ||
      available[0] || null;
  }

  synth.speak = function (utterance) {
    if (!utterance) return;
    synth.cancel();

    var pageWords = words();
    var start = findStart(utterance.text, pageWords);
    var spoken = String(utterance.text || "");
    var voice = oneSwahiliVoice();
    if (voice) utterance.voice = voice;
    utterance.lang = "sw-TZ";
    document.documentElement.dataset.readerVoice = voice ? voice.name + " (" + voice.lang + ")" : "sw-TZ default";

    utterance.addEventListener("boundary", function (event) {
      if (event.name && event.name !== "word") return;
      var before = spoken.slice(0, event.charIndex);
      var offset = (before.match(/\S+/g) || []).length;
      var target = pageWords[start + offset];
      if (!target) return;
      clear();
      target.classList.add("pdf-word-active");
      activeWord = target;
    });
    var fallbackIndex = start;
    if (fallbackTimer) window.clearInterval(fallbackTimer);
    fallbackTimer = window.setInterval(function () {
      if (!reading || fallbackIndex >= pageWords.length) return;
      clear();
      pageWords[fallbackIndex].classList.add("pdf-word-active");
      activeWord = pageWords[fallbackIndex];
      fallbackIndex += 1;
    }, 360);
    utterance.addEventListener("end", function () {
      if (fallbackTimer) window.clearInterval(fallbackTimer);
      fallbackTimer = null;
      if (reading && currentSegment + 1 < currentSegments.length) {
        currentSegment += 1;
        window.setTimeout(speakCurrentSegment, 80);
      } else {
        stopReading();
      }
    }, { once: true });
    utterance.addEventListener("error", stopReading, { once: true });
    nativeSpeak(utterance);
  };

  function pageSegments() {
    var nodes = Array.prototype.slice.call(document.querySelectorAll(".accessible-transcript [data-id]"));
    var footerIndex = nodes.findIndex(function (node) { return /AFYA NA MAZINGIRA MWAKA 1\.indd/i.test(node.textContent); });
    if (footerIndex >= 0) {
      nodes = nodes.slice(0, footerIndex);
      var last = nodes[nodes.length - 1];
      if (last && /^\d+$/.test(last.textContent.trim())) nodes.pop();
    }
    return nodes.map(function (node) { return node.textContent.trim(); }).filter(Boolean);
  }

  function speakCurrentSegment() {
    if (!reading || !currentSegments[currentSegment]) return;
    var utterance = new SpeechSynthesisUtterance(currentSegments[currentSegment]);
    utterance.rate = currentRate;
    utterance.volume = currentVolume;
    synth.speak(utterance);
  }

  function loadRecordedEntry() {
    var page = String(Number(document.querySelector('meta[name="page-section-id"]').content));
    if (window.__validatorEnhancedPage && page !== "3" && page !== "8" && page !== "9" && page !== "10" && page !== "13" && page !== "15" && page !== "30" && page !== "38" && page !== "42" && page !== "44" && page !== "46" && page !== "49" && page !== "53" && page !== "56" && page !== "58" && page !== "60" && page !== "61" && page !== "62" && page !== "65") return Promise.resolve(null);
    if (!timingsPromise) {
      timingsPromise = fetch("./content/rehema/timecodes.json?v=36")
        .then(function (response) { return response.ok ? response.json() : {}; })
        .catch(function () { return {}; });
    }
    return timingsPromise.then(function (all) { return all[page] || null; });
  }

  function highlightRecordedWord() {
    if (!recordedAudio || !recordedEntry) return;
    var cues = recordedEntry.words || [];
    while (recordedCue + 1 < cues.length && Number(cues[recordedCue + 1].start) <= recordedAudio.currentTime + 0.03) recordedCue += 1;
    while (recordedCue > 0 && Number(cues[recordedCue].start) > recordedAudio.currentTime + 0.03) recordedCue -= 1;
    var cue = cues[recordedCue] || {};
    var target;
    if (cue.targetPatch !== undefined) {
      target = document.querySelectorAll('[data-validator-patch="' + cue.targetPatch + '"] .validator-display-word')[Number(cue.targetWord || 0)];
    } else if (cue.targetImage) {
      clear();
      return;
    } else {
      target = words()[Number(cue.sourceIndex || 0)];
    }
    if (!target || target === activeWord) return;
    clear();
    target.classList.add("pdf-word-active");
    activeWord = target;
  }

  function playRecorded(entry) {
    recordedEntry = entry;
    document.documentElement.dataset.readerVoice = entry.voice || "Recorded page audio";
    recordedCue = 0;
    if (!recordedAudio || !recordedAudio.src.endsWith("/" + entry.audio)) {
      recordedAudio = new Audio("./content/rehema/" + entry.audio + "?v=" + (entry.version || 7));
      recordedAudio.dataset.singleReaderAudio = "1";
      recordedAudio.addEventListener("timeupdate", highlightRecordedWord);
      recordedAudio.addEventListener("ended", stopReading);
    }
    recordedAudio.playbackRate = currentRate;
    recordedAudio.volume = currentVolume;
    reading = true;
    recordedAudio.play();
  }

  function startReading() {
    currentSegments = pageSegments();
    if (!currentSegments.length) return;
    loadRecordedEntry().then(function (entry) {
      if (entry && entry.audio) playRecorded(entry);
      else { reading = true; speakCurrentSegment(); }
    });
  }

  function ensurePanel() {
    if (panel) return panel;
    panel = document.createElement("div");
    panel.className = "single-voice-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "Vidhibiti vya kusoma kwa sauti");
    panel.innerHTML =
      '<button type="button" data-voice-action="previous" aria-label="Nenda kwenye sauti iliyopita">&#9198;</button>' +
      '<button type="button" data-voice-action="play" aria-label="Cheza au simamisha">&#9654;</button>' +
      '<button type="button" data-voice-action="next" aria-label="Nenda kwenye sauti inayofuata">&#9197;</button>' +
      '<button type="button" data-voice-action="stop" aria-label="Simamisha">&#9632;</button>' +
      '<button type="button" data-voice-action="speed" aria-label="Kasi ya kucheza">1&times;</button>' +
      '<label aria-label="Sauti">&#128266;<input data-voice-volume type="range" min="0" max="1" step="0.1" value="1"></label>';
    document.body.appendChild(panel);
    panel.addEventListener("click", function (event) {
      var control = event.target.closest("[data-voice-action]");
      if (!control) return;
      var action = control.dataset.voiceAction;
      if (action === "play") {
        if (reading) stopReading();
        else if (recordedAudio && recordedEntry) { reading = true; recordedAudio.play(); }
        else startReading();
      }
      if (action === "stop") { stopReading(); currentSegment = 0; if (recordedAudio) recordedAudio.currentTime = 0; }
      if (action === "previous") {
        if (recordedAudio && recordedEntry) { recordedCue = Math.max(0, recordedCue - 1); recordedAudio.currentTime = Number(recordedEntry.words[recordedCue].start || 0); }
        else { stopReading(); currentSegment = Math.max(0, currentSegment - 1); reading = true; speakCurrentSegment(); }
      }
      if (action === "next") {
        if (recordedAudio && recordedEntry) { recordedCue = Math.min(recordedEntry.words.length - 1, recordedCue + 1); recordedAudio.currentTime = Number(recordedEntry.words[recordedCue].start || 0); }
        else { stopReading(); currentSegment = Math.min(Math.max(0, currentSegments.length - 1), currentSegment + 1); reading = true; speakCurrentSegment(); }
      }
      if (action === "speed") {
        var rates = [0.75, 1, 1.25, 1.5];
        currentRate = rates[(rates.indexOf(currentRate) + 1) % rates.length];
        control.textContent = currentRate + "×";
        if (recordedAudio) recordedAudio.playbackRate = currentRate;
        else if (reading) { stopReading(); reading = true; speakCurrentSegment(); }
      }
    });
    panel.querySelector("[data-voice-volume]").addEventListener("input", function (event) {
      currentVolume = Number(event.target.value);
      if (recordedAudio) recordedAudio.volume = currentVolume;
      else if (reading) { stopReading(); reading = true; speakCurrentSegment(); }
    });
    return panel;
  }

  document.addEventListener("click", function (event) {
    var button = event.target && event.target.closest ? event.target.closest("button") : null;
    if (!button) return;
    var label = String(button.getAttribute("aria-label") || button.title || "");
    if (!/(text to speech|maandishi kwa sauti)/i.test(label)) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    var controls = ensurePanel();
    controls.classList.toggle("is-open");
    if (controls.classList.contains("is-open") && !reading) startReading();
    if (!controls.classList.contains("is-open")) stopReading();
  }, true);

  window.addEventListener("beforeunload", stopReading);
}());
