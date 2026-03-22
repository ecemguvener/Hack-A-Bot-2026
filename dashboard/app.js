const MAX_POINTS = 120;
const EXPECTED_HZ = 10;

const els = {
  wsUrl: document.getElementById("wsUrl"),
  connectBtn: document.getElementById("connectBtn"),
  disconnectBtn: document.getElementById("disconnectBtn"),
  simulateBtn: document.getElementById("simulateBtn"),
  sendConfigBtn: document.getElementById("sendConfigBtn"),
  safeStopBtn: document.getElementById("safeStopBtn"),
  stateRingProgress: document.getElementById("stateRingProgress"),
  stateLabel: document.getElementById("stateLabel"),
  stateScore: document.getElementById("stateScore"),
  chipIntensity: document.getElementById("chipIntensity"),
  chipSafeMode: document.getElementById("chipSafeMode"),
  chipPacketLoss: document.getElementById("chipPacketLoss"),
  chipImuHealth: document.getElementById("chipImuHealth"),
  ftremor: document.getElementById("ftremor"),
  magnitude: document.getElementById("magnitude"),
  fmotor: document.getElementById("fmotor"),
  kfactor: document.getElementById("kfactor"),
  wizardStartBtn: document.getElementById("wizardStartBtn"),
  wizardApplyBtn: document.getElementById("wizardApplyBtn"),
  wizardResult: document.getElementById("wizardResult"),
  wizStep1: document.getElementById("wizStep1"),
  wizStep2: document.getElementById("wizStep2"),
  wizStep3: document.getElementById("wizStep3"),
  recordStartBtn: document.getElementById("recordStartBtn"),
  recordStopBtn: document.getElementById("recordStopBtn"),
  replayBtn: document.getElementById("replayBtn"),
  clearReplayBtn: document.getElementById("clearReplayBtn"),
  replayStatus: document.getElementById("replayStatus"),
  modeInput: document.getElementById("modeInput"),
  kInput: document.getElementById("kInput"),
  intensityInput: document.getElementById("intensityInput"),
  eventLog: document.getElementById("eventLog"),
};

const charts = {
  ft: setupChart(document.getElementById("chartFTremor"), "#2563eb"),
  mag: setupChart(document.getElementById("chartMagnitude"), "#16a34a"),
  baRaw: setupChart(document.getElementById("chartBeforeAfter"), "#2563eb"),
  baAfter: setupChart(document.getElementById("chartBeforeAfter"), "#16a34a"),
};

let ws = null;
let simTimer = null;
let smoothMag = 0;
let packetLossPct = 0;
let totalPackets = 0;
let missedPackets = 0;
let lastPacketMs = 0;
let wizardSuggestedK = null;

const replayState = {
  recording: false,
  playing: false,
  buffer: [],
  timer: null,
};

const ringCircumference = 2 * Math.PI * 88;
els.stateRingProgress.style.strokeDasharray = `${ringCircumference}`;
els.stateRingProgress.style.strokeDashoffset = `${ringCircumference}`;

function setupChart(canvas, color) {
  return { canvas, ctx: canvas.getContext("2d"), color, points: [] };
}

function log(msg) {
  const t = new Date().toLocaleTimeString();
  els.eventLog.textContent = `[${t}] ${msg}\n` + els.eventLog.textContent;
}

function onTelemetry(data, source = "live") {
  updatePacketStats(source);

  const mode = data.mode || "NORMAL";
  const fault = data.fault_flags ?? 0;
  const magRaw = Number(data.tremor_magnitude || 0);
  const k = Number(data.k_factor ?? els.kInput.value ?? 1.2);
  smoothMag = smoothMag === 0 ? magRaw : (0.82 * smoothMag + 0.18 * magRaw);
  const magAfter = Math.max(0, smoothMag / Math.max(k, 1));

  els.ftremor.textContent = num(data.f_tremor_hz, 2);
  els.magnitude.textContent = num(magRaw, 3);
  els.fmotor.textContent = num(data.f_motor_hz, 2);
  els.kfactor.textContent = num(k, 2);

  pushPoint(charts.ft, Number(data.f_tremor_hz || 0));
  pushPoint(charts.mag, magRaw);
  pushPoint(charts.baRaw, magRaw);
  pushPoint(charts.baAfter, magAfter);
  drawOverlayChart(charts.baRaw, charts.baAfter);
  updateStateRing(magRaw);
  updateSafetyPanel({
    mode,
    fault,
    intensityLimit: Number(els.intensityInput.value || 0),
    packetLossPct,
  });

  if (replayState.recording && source === "live") {
    replayState.buffer.push({ ...data, _ts: Date.now() });
    trimReplayBuffer(60_000);
    els.replayStatus.textContent = `Recording... ${replayState.buffer.length} samples`;
  }
}

function pushPoint(chart, y) {
  chart.points.push(y);
  if (chart.points.length > MAX_POINTS) chart.points.shift();
  if (chart === charts.baRaw || chart === charts.baAfter) return;
  drawChart(chart);
}

function drawChart(chart) {
  const { ctx, canvas, points, color } = chart;
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "#d1d5db";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = (h / 4) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  if (points.length < 2) return;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = Math.max(max - min, 0.001);

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  points.forEach((p, i) => {
    const x = (i / (MAX_POINTS - 1)) * w;
    const y = h - ((p - min) / span) * h;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function drawOverlayChart(rawChart, afterChart) {
  const canvas = rawChart.canvas;
  const ctx = rawChart.ctx;
  const w = canvas.width;
  const h = canvas.height;
  const pointsA = rawChart.points;
  const pointsB = afterChart.points;
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "#d1d5db";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = (h / 4) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  const all = [...pointsA, ...pointsB];
  if (all.length < 2) return;
  const min = Math.min(...all);
  const max = Math.max(...all);
  const span = Math.max(max - min, 0.001);

  drawLine(ctx, pointsA, rawChart.color, w, h, min, span);
  drawLine(ctx, pointsB, afterChart.color, w, h, min, span);
}

function drawLine(ctx, points, color, w, h, min, span) {
  if (points.length < 2) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  points.forEach((p, i) => {
    const x = (i / (MAX_POINTS - 1)) * w;
    const y = h - ((p - min) / span) * h;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function updateStateRing(magnitude) {
  const score = clamp01(1 - magnitude / 0.8);
  const pct = Math.round(score * 100);
  const state = magnitude < 0.2 ? "STABLE" : magnitude < 0.45 ? "MILD TREMOR" : "SEVERE TREMOR";
  const color = state === "STABLE" ? "#2cff83" : state === "MILD TREMOR" ? "#ffb020" : "#ff4d7a";
  const offset = ringCircumference * (1 - score);
  els.stateRingProgress.style.strokeDashoffset = `${offset}`;
  els.stateRingProgress.style.stroke = color;
  els.stateLabel.textContent = state;
  els.stateScore.textContent = `${pct}%`;
}

function updateSafetyPanel(s) {
  setChip(els.chipIntensity, `INTENSITY ${s.intensityLimit}%`, s.intensityLimit > 85 ? "danger" : s.intensityLimit > 70 ? "warn" : "ok");
  setChip(els.chipSafeMode, `MODE ${s.mode}`, s.mode === "SAFE" ? "warn" : "ok");
  setChip(els.chipPacketLoss, `LOSS ${num(s.packetLossPct, 1)}%`, s.packetLossPct > 15 ? "danger" : s.packetLossPct > 5 ? "warn" : "ok");
  setChip(els.chipImuHealth, `IMU ${s.fault === 0 ? "HEALTHY" : "FAULT"}`, s.fault === 0 ? "ok" : "danger");
}

function setChip(el, text, level) {
  el.textContent = text;
  el.className = `safety-chip ${level}`;
}

function updatePacketStats(source) {
  if (source !== "live") return;
  const now = Date.now();
  totalPackets += 1;
  if (lastPacketMs !== 0) {
    const delta = (now - lastPacketMs) / 1000;
    const expectedPackets = Math.max(1, Math.round(delta * EXPECTED_HZ));
    const missed = Math.max(0, expectedPackets - 1);
    missedPackets += missed;
  }
  lastPacketMs = now;
  packetLossPct = totalPackets === 0 ? 0 : (missedPackets / (missedPackets + totalPackets)) * 100;
}

function connect() {
  disconnect();
  const url = els.wsUrl.value.trim();
  ws = new WebSocket(url);
  ws.onopen = () => {
    log(`Connected to ${url}`);
  };
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "telemetry" || data.f_tremor_hz !== undefined) {
        onTelemetry(data);
      } else {
        log(`Unknown message: ${event.data}`);
      }
    } catch {
      log(`Non-JSON message: ${event.data}`);
    }
  };
  ws.onclose = () => {
    log("Socket closed");
  };
  ws.onerror = () => {
    log("Socket error");
  };
}

function disconnect() {
  if (ws) {
    ws.close();
    ws = null;
  }
  stopSim();
}

function sendConfig(overrides = {}) {
  const payload = {
    type: "config",
    mode: overrides.mode || els.modeInput.value,
    k_factor: Number(overrides.k_factor ?? els.kInput.value),
    intensity_limit: Number(overrides.intensity_limit ?? els.intensityInput.value),
  };

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(payload));
    log(`Sent config: ${JSON.stringify(payload)}`);
  } else {
    log(`Not connected. Config not sent: ${JSON.stringify(payload)}`);
  }
}

function startSim() {
  disconnect();
  let t = 0;
  simTimer = setInterval(() => {
    t += 0.12;
    const ft = 4.8 + Math.sin(t * 0.9) * 0.8;
    const mag = 0.34 + Math.sin(t * 1.5) * 0.09;
    const k = Number(els.kInput.value);
    const mode = els.modeInput.value;
    const data = {
      mode,
      f_tremor_hz: ft,
      tremor_magnitude: Math.max(0.05, mag),
      f_motor_hz: ft * k,
      k_factor: k,
      fault_flags: 0,
    };
    onTelemetry(data, "sim");
  }, 100);
  log("Simulation mode started");
}

function stopSim() {
  if (simTimer) {
    clearInterval(simTimer);
    simTimer = null;
    log("Simulation mode stopped");
  }
}

function num(v, digits) {
  if (v === undefined || v === null || Number.isNaN(Number(v))) return "--";
  return Number(v).toFixed(digits);
}

function clamp01(v) {
  return Math.min(1, Math.max(0, v));
}

function trimReplayBuffer(maxDurationMs) {
  const now = Date.now();
  replayState.buffer = replayState.buffer.filter((x) => now - x._ts <= maxDurationMs);
}

function startRecording() {
  replayState.buffer = [];
  replayState.recording = true;
  els.replayStatus.textContent = "Recording started (max 60s window).";
  log("Session recording started");
}

function stopRecording() {
  replayState.recording = false;
  els.replayStatus.textContent = `Recording stopped. ${replayState.buffer.length} samples saved.`;
  log("Session recording stopped");
}

function replaySession() {
  if (replayState.playing || replayState.buffer.length < 2) {
    els.replayStatus.textContent = replayState.buffer.length < 2 ? "Need more recorded samples." : "Replay already running.";
    return;
  }
  replayState.playing = true;
  disconnect();
  const baseTs = replayState.buffer[0]._ts;
  const samples = replayState.buffer.map((s) => ({ ...s, _offset: s._ts - baseTs }));
  let i = 0;
  els.replayStatus.textContent = "Replay running...";
  log("Session replay started");

  const tick = () => {
    if (i >= samples.length) {
      replayState.playing = false;
      replayState.timer = null;
      els.replayStatus.textContent = "Replay complete.";
      log("Session replay complete");
      return;
    }
    onTelemetry(samples[i], "replay");
    i += 1;
    const delay = i < samples.length ? Math.max(25, samples[i]._offset - samples[i - 1]._offset) : 30;
    replayState.timer = setTimeout(tick, delay);
  };
  tick();
}

function clearReplay() {
  replayState.buffer = [];
  replayState.recording = false;
  if (replayState.timer) clearTimeout(replayState.timer);
  replayState.playing = false;
  els.replayStatus.textContent = "No session recorded.";
  log("Session data cleared");
}

function markWizardStep(stepEl, state) {
  stepEl.className = `wizard-step ${state}`;
}

async function runWizard() {
  wizardSuggestedK = null;
  markWizardStep(els.wizStep1, "active");
  markWizardStep(els.wizStep2, "");
  markWizardStep(els.wizStep3, "");
  els.wizardResult.textContent = "Running baseline capture...";

  const baseline = await captureMagnitude(5000);
  markWizardStep(els.wizStep1, "done");
  markWizardStep(els.wizStep2, "active");
  els.wizardResult.textContent = `Baseline: ${num(baseline, 3)}. Running k sweep...`;

  const kCandidates = [0.8, 1.0, 1.2, 1.4, 1.6];
  const results = [];
  for (const k of kCandidates) {
    els.kInput.value = String(k);
    sendConfig({ k_factor: k, mode: "CALIBRATION" });
    await sleep(1600);
    const val = await captureMagnitude(1200);
    const score = baseline - val;
    results.push({ k, val, score });
  }
  markWizardStep(els.wizStep2, "done");
  markWizardStep(els.wizStep3, "active");

  results.sort((a, b) => b.score - a.score);
  const best = results[0];
  const second = results[1] || best;
  const confidence = clamp01((best.score - second.score + 0.02) / 0.12);
  wizardSuggestedK = best.k;
  els.wizardResult.textContent = `Suggested k: ${best.k.toFixed(2)} | Confidence: ${(confidence * 100).toFixed(0)}%`;
  markWizardStep(els.wizStep3, "done");
  sendConfig({ mode: "NORMAL" });
  log(`Wizard suggested k=${best.k.toFixed(2)} (confidence ${(confidence * 100).toFixed(0)}%)`);
}

function captureMagnitude(durationMs) {
  const points = [];
  const start = Date.now();
  return new Promise((resolve) => {
    const timer = setInterval(() => {
      const v = Number(els.magnitude.textContent);
      if (!Number.isNaN(v)) points.push(v);
      if (Date.now() - start >= durationMs) {
        clearInterval(timer);
        resolve(points.length ? points.reduce((a, b) => a + b, 0) / points.length : 0);
      }
    }, 100);
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

els.connectBtn.addEventListener("click", connect);
els.disconnectBtn.addEventListener("click", disconnect);
els.simulateBtn.addEventListener("click", startSim);
els.sendConfigBtn.addEventListener("click", () => sendConfig());
els.wizardStartBtn.addEventListener("click", runWizard);
els.wizardApplyBtn.addEventListener("click", () => {
  if (!wizardSuggestedK) {
    log("No suggested k yet. Run wizard first.");
    return;
  }
  els.kInput.value = wizardSuggestedK.toFixed(2);
  sendConfig({ k_factor: wizardSuggestedK, mode: "NORMAL" });
  log(`Applied wizard k=${wizardSuggestedK.toFixed(2)}`);
});
els.recordStartBtn.addEventListener("click", startRecording);
els.recordStopBtn.addEventListener("click", stopRecording);
els.replayBtn.addEventListener("click", replaySession);
els.clearReplayBtn.addEventListener("click", clearReplay);
els.safeStopBtn.addEventListener("click", () => {
  sendConfig({ mode: "SAFE", intensity_limit: 0 });
  els.modeInput.value = "SAFE";
});

log("Dashboard ready. Connect WebSocket or start simulation.");
