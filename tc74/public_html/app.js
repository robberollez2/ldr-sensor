// app.js

let client = null;
let mqttConfig = null;

// DOM referenties
const statusPill = document.getElementById("status-pill");
const statusText = document.getElementById("status-text");
const topicLabel = document.getElementById("topic-label-value");
const reconnectBtn = document.getElementById("reconnect-btn");
const tempValueSpan = document.getElementById("temp-value");
const lastUpdateSpan = document.getElementById("last-update");

// Google Charts variabelen
let gaugeChart, gaugeData, gaugeOptions;
let lineChart, lineData, lineOptions;

// Max aantal punten in de grafiek
const MAX_POINTS = 25;

// 1) Config ophalen uit .env via PHP endpoint
async function fetchMqttConfig() {
  const resp = await fetch("mqtt-config.php");
  if (!resp.ok) {
    throw new Error("Kan mqtt-config.php niet ophalen");
  }
  const cfg = await resp.json();

  if (cfg.error) {
    throw new Error(cfg.error);
  }

  if (!cfg.brokerUrl || !cfg.topic) {
    throw new Error("MQTT_BROKER_URL en MQTT_TOPIC moeten in .env staan");
  }

  mqttConfig = cfg;

  topicLabel.textContent = cfg.topic;

  return cfg;
}

// 2) Logging helper
function logMessage(text, topic, payload) {
  const line = document.createElement("div");
  line.className = "message-line";

  if (topic !== undefined && payload !== undefined) {
    line.innerHTML =
      `[${new Date().toLocaleTimeString()}] ` +
      `<span class="topic">${topic}</span> → ` +
      `<span class="payload">${payload}</span>`;
  } else {
    line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
  }
}

// 3) Status helpers
function setStatus(text, type = "default") {
  statusText.textContent = text;
  statusPill.classList.remove("connected", "error");

  if (type === "connected") {
    statusPill.classList.add("connected");
  } else if (type === "error") {
    statusPill.classList.add("error");
  }
}

// 4) Temperatuur parsing
function parseTemperature(payload) {
  // Probeer eerst JSON: { "temperature": 21.5 }
  try {
    const obj = JSON.parse(payload);
    if (typeof obj.temperature === "number") {
      return obj.temperature;
    }
  } catch (e) {
    // geen geldige JSON, negeren
  }

  // Probeer gewoon een nummer (ook "21,3" -> 21.3)
  const num = parseFloat(String(payload).replace(",", "."));
  if (!isNaN(num)) {
    return num;
  }
  return null;
}

// 5) Charts initialiseren
function initCharts() {
  // Gauge
  gaugeData = google.visualization.arrayToDataTable([
    ["Label", "Value"],
    ["Temp", 0],
  ]);

  gaugeOptions = {
    width: "100%",
    height: 200,
    min: 0,
    max: 40,
    redFrom: 30,
    redTo: 40,
    yellowFrom: 23,
    yellowTo: 30,
    minorTicks: 5,
  };

  gaugeChart = new google.visualization.Gauge(document.getElementById("gauge"));

  // Lijngrafiek
  lineData = new google.visualization.DataTable();
  lineData.addColumn("datetime", "Tijd");
  lineData.addColumn("number", "Temperatuur (°C)");

  lineOptions = {
    legend: { position: "none" },
    hAxis: {
      title: "Tijd",
      format: "HH:mm:ss",
      textStyle: { color: "#9ca3af" },
      titleTextStyle: { color: "#9ca3af" },
    },
    vAxis: {
      title: "°C",
      textStyle: { color: "#9ca3af" },
      titleTextStyle: { color: "#9ca3af" },
    },
    backgroundColor: "transparent",
    chartArea: { left: 50, right: 20, top: 20, bottom: 40 },
  };

  lineChart = new google.visualization.LineChart(
    document.getElementById("chart")
  );

  redrawCharts();
}

function redrawCharts() {
  if (gaugeChart && gaugeData) {
    gaugeChart.draw(gaugeData, gaugeOptions);
  }
  if (lineChart && lineData) {
    lineChart.draw(lineData, lineOptions);
  }
}

// 6) Temperatuur updaten in UI + charts
function updateTemperature(temp) {
  tempValueSpan.textContent = temp.toFixed(1).replace(".", ",");
  lastUpdateSpan.textContent = new Date().toLocaleTimeString();

  if (gaugeData) {
    gaugeData.setValue(0, 1, temp);
  }

  const now = new Date();
  if (lineData) {
    lineData.addRow([now, temp]);
    if (lineData.getNumberOfRows() > MAX_POINTS) {
      lineData.removeRow(0);
    }
  }

  redrawCharts();
}

// 7) MQTT connectie opzetten
function connectMqtt() {
  if (!mqttConfig) return;

  // Oude client netjes afsluiten
  if (client) {
    try {
      client.end(true);
    } catch (e) {
      console.warn("Oude MQTT client kon niet sluiten:", e);
    }
    client = null;
  }

  setStatus("Verbinden...", "default");
  logMessage("Verbinden met broker: " + mqttConfig.brokerUrl);

  const options = {
    username: mqttConfig.username || undefined,
    password: mqttConfig.password || undefined,
    clean: true,
    reconnectPeriod: 2000,
  };

  client = mqtt.connect(mqttConfig.brokerUrl, options);

  client.on("connect", () => {
    setStatus("Verbonden", "connected");
    logMessage(
      "Verbonden met broker, subscriben op topic: " + mqttConfig.topic
    );

    client.subscribe(mqttConfig.topic, (err) => {
      if (err) {
        setStatus("Fout bij subscriben", "error");
        logMessage("❌ Fout bij subscriben: " + err.message);
      } else {
        logMessage("✅ Geabonneerd op " + mqttConfig.topic);
      }
    });
  });

  client.on("message", (recvTopic, payloadBuf) => {
    const payload = payloadBuf.toString();
    logMessage(null, recvTopic, payload);

    const temp = parseTemperature(payload);
    if (temp !== null) {
      updateTemperature(temp);
    }
  });

  client.on("error", (err) => {
    setStatus("Fout: " + err.message, "error");
    logMessage("❌ MQTT error: " + err.message);
  });

  client.on("reconnect", () => {
    setStatus("Opnieuw verbinden...", "default");
    logMessage("🔄 Reconnect poging...");
  });

  client.on("close", () => {
    setStatus("Verbinding gesloten", "default");
    logMessage("Verbinding gesloten");
  });
}

// 8) Start-flow: config ophalen, charts laden, dan MQTT verbinden
async function start() {
  try {
    setStatus("Config ophalen...", "default");
    await fetchMqttConfig();
    setStatus("Config geladen, charts initialiseren...", "default");

    google.charts.load("current", { packages: ["gauge", "corechart"] });
    google.charts.setOnLoadCallback(() => {
      initCharts();
      connectMqtt();
    });
  } catch (e) {
    console.error(e);
    setStatus("Config fout: " + e.message, "error");
    logMessage("❌ Config fout: " + e.message);
  }
}

// Reconnect knop
reconnectBtn.addEventListener("click", () => {
  logMessage("🔄 Handmatig opnieuw verbinden aangevraagd");
  connectMqtt();
});

// Start als de pagina geladen is
window.addEventListener("DOMContentLoaded", start);
