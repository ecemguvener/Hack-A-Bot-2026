const MAX_POINTS = 120;

const els = {
  wsUrl: document.getElementById("wsUrl"),
  connectBtn: document.getElementById("connectBtn"),
  disconnectBtn: document.getElementById("disconnectBtn"),
  simulateBtn: document.getElementById("simulateBtn"),
  sendConfigBtn: document.getElementById("sendConfigBtn"),
  safeStopBtn: document.getElementById("safeStopBtn"),
  linkStatus: document.getElementById("linkStatus"),
  modeStatus: document.getElementById("modeStatus"),
  faultStatus: document.getElementById("faultStatus"),
  ftremor: document.getElementById("ftremor"),
  magnitude: document.getElementById("magnitude"),
  fmotor: document.getElementById("fmotor"),
  kfactor: document.getElementById("kfactor"),
  axis: document.getElementById("axis"),
  motor: document.getElementById("motor"),
  modeInput: document.getElementById("modeInput"),
  kInput: document.getElementById("kInput"),
  intensityInput: document.getElementById("intensityInput"),
  eventLog: document.getElementById("eventLog"),
};

const charts = {
  ft: setupChart(document.getElementById("chartFTremor"), "#2563eb"),
  mag: setupChart(document.getElementById("chartMagnitude"), "#16a34a"),
  fm: setupChart(document.getElementById("chartFMotor"), "#ea580c"),
};

let ws = null;
let simTimer = null;

function setupChart(canvas, color) {
  return { canvas, ctx: canvas.getContext("2d"), color, points: [] };
}

function log(msg) {
  const t = new Date().toLocaleTimeString();
  els.eventLog.textContent = `[${t}] ${msg}\n` + els.eventLog.textContent;
}

function setPill(el, text, cls) {
  el.textContent = text;
  el.className = `pill ${cls}`;
}

function onTelemetry(data) {
  const mode = data.mode || "NORMAL";
  const fault = data.fault_flags ?? 0;

  els.ftremor.textContent = num(data.f_tremor_hz, 2);
  els.magnitude.textContent = num(data.tremor_magnitude, 3);
  els.fmotor.textContent = num(data.f_motor_hz, 2);
  els.kfactor.textContent = num(data.k_factor, 2);
  els.axis.textContent = `${data.dominant_axis || "?"}${data.axis_sign === -1 ? "-" : data.axis_sign === 1 ? "+" : ""}`;
  els.motor.textContent = String(data.selected_motor_id ?? "--");

  setPill(els.modeStatus, `MODE: ${mode}`, mode === "CALIBRATION" ? "pill-warn" : "pill");
  setPill(els.faultStatus, `FAULT: ${fault === 0 ? "NONE" : fault}`, fault === 0 ? "pill" : "pill-danger");

  pushPoint(charts.ft, Number(data.f_tremor_hz || 0));
  pushPoint(charts.mag, Number(data.tremor_magnitude || 0));
  pushPoint(charts.fm, Number(data.f_motor_hz || 0));
}

function pushPoint(chart, y) {
  chart.points.push(y);
  if (chart.points.length > MAX_POINTS) chart.points.shift();
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

function connect() {
  disconnect();
  const url = els.wsUrl.value.trim();
  ws = new WebSocket(url);
  ws.onopen = () => {
    setPill(els.linkStatus, "CONNECTED", "pill-ok");
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
    setPill(els.linkStatus, "DISCONNECTED", "pill-warn");
    log("Socket closed");
  };
  ws.onerror = () => {
    setPill(els.linkStatus, "ERROR", "pill-danger");
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
      dominant_axis: ["X", "Y", "Z"][Math.floor((t * 2) % 3)],
      axis_sign: Math.sin(t) > 0 ? 1 : -1,
      selected_motor_id: Math.sin(t) > 0 ? 2 : 1,
      f_motor_hz: ft * k,
      k_factor: k,
      fault_flags: 0,
    };
    onTelemetry(data);
  }, 100);
  setPill(els.linkStatus, "SIMULATING", "pill-warn");
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

els.connectBtn.addEventListener("click", connect);
els.disconnectBtn.addEventListener("click", disconnect);
els.simulateBtn.addEventListener("click", startSim);
els.sendConfigBtn.addEventListener("click", () => sendConfig());
els.safeStopBtn.addEventListener("click", () => {
  sendConfig({ mode: "SAFE", intensity_limit: 0 });
  els.modeInput.value = "SAFE";
});

log("Dashboard ready. Connect WebSocket or start simulation.");
