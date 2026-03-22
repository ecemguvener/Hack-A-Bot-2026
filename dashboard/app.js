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
  safetyScore: document.getElementById("safetyScore"),
  riskMeterFill: document.getElementById("riskMeterFill"),
  safetyState: document.getElementById("safetyState"),
  safetyHint: document.getElementById("safetyHint"),
  ftremor: document.getElementById("ftremor"),
  magnitude: document.getElementById("magnitude"),
  fmotor: document.getElementById("fmotor"),
  kfactor: document.getElementById("kfactor"),
  modeInput: document.getElementById("modeInput"),
  kInput: document.getElementById("kInput"),
  intensityInput: document.getElementById("intensityInput"),
  eventLog: document.getElementById("eventLog"),
};

const charts = {
  ft: setupChart(document.getElementById("chartFTremor"), "#cc2cad"),
  mag: setupChart(document.getElementById("chartMagnitude"), "#cdaadd"),
  baRaw: setupChart(document.getElementById("chartBeforeAfter"), "#cc2cad"),
  baAfter: setupChart(document.getElementById("chartBeforeAfter"), "#cdaadd"),
};

let ws = null;
let simTimer = null;
let smoothMag = 0;
let packetLossPct = 0;
let totalPackets = 0;
let missedPackets = 0;
let lastPacketMs = 0;

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
  const intensityLevel = s.intensityLimit > 85 ? "danger" : s.intensityLimit > 70 ? "warn" : "ok";
  const modeLevel = s.mode === "SAFE" ? "warn" : "ok";
  const lossLevel = s.packetLossPct > 15 ? "danger" : s.packetLossPct > 5 ? "warn" : "ok";
  const imuLevel = s.fault === 0 ? "ok" : "danger";

  setChip(els.chipIntensity, "INTENSITY LIMIT", `${s.intensityLimit}%`, intensityLevel);
  setChip(els.chipSafeMode, "OPERATING MODE", s.mode, modeLevel);
  setChip(els.chipPacketLoss, "RF PACKET LOSS", `${num(s.packetLossPct, 1)}%`, lossLevel);
  setChip(els.chipImuHealth, "IMU STATUS", s.fault === 0 ? "HEALTHY" : "FAULT", imuLevel);

  const risk = riskScoreFromLevels([intensityLevel, modeLevel, lossLevel, imuLevel]);
  const score = Math.max(0, 100 - risk);
  els.safetyScore.textContent = `${score}%`;
  els.safetyScore.className = `safety-score ${score >= 85 ? "ok" : score >= 65 ? "warn" : "danger"}`;
  els.riskMeterFill.style.width = `${score}%`;
  els.riskMeterFill.className = `risk-meter-fill ${score >= 85 ? "ok" : score >= 65 ? "warn" : "danger"}`;

  const state = score >= 85 ? "STATE: SAFE" : score >= 65 ? "STATE: CAUTION" : "STATE: CRITICAL";
  const hint = buildSafetyHint({ intensityLevel, modeLevel, lossLevel, imuLevel });
  els.safetyState.textContent = state;
  els.safetyState.className = `safety-state ${score >= 85 ? "ok" : score >= 65 ? "warn" : "danger"}`;
  els.safetyHint.textContent = hint;
}

function setChip(el, label, value, level) {
  el.innerHTML = `<span class="chip-label">${label}</span><span class="chip-value">${value}</span>`;
  el.className = `safety-chip ${level}`;
}

function riskScoreFromLevels(levels) {
  return levels.reduce((sum, level) => {
    if (level === "danger") return sum + 35;
    if (level === "warn") return sum + 15;
    return sum;
  }, 0);
}

function buildSafetyHint(levels) {
  if (levels.imuLevel === "danger") return "IMU fault detected. Switch to SAFE mode and verify sensor wiring.";
  if (levels.lossLevel === "danger") return "High RF packet loss. Reduce distance/noise and check module power.";
  if (levels.intensityLevel === "danger") return "Intensity is very high. Lower intensity limit to reduce user risk.";
  if (levels.modeLevel === "warn") return "SAFE mode active. Resume NORMAL when diagnostics are stable.";
  if (levels.lossLevel === "warn") return "RF link quality is moderate. Keep transmitter orientation consistent.";
  if (levels.intensityLevel === "warn") return "Intensity near upper bound. Monitor comfort during calibration.";
  return "All systems in safe range. Continue calibration or live demo.";
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

els.connectBtn.addEventListener("click", connect);
els.disconnectBtn.addEventListener("click", disconnect);
els.simulateBtn.addEventListener("click", startSim);
els.sendConfigBtn.addEventListener("click", () => sendConfig());
els.safeStopBtn.addEventListener("click", () => {
  sendConfig({ mode: "SAFE", intensity_limit: 0 });
  els.modeInput.value = "SAFE";
});

log("Dashboard ready. Connect WebSocket or start simulation.");
