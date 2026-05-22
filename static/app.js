const uploadArea = document.getElementById("uploadArea");
const fileInput = document.getElementById("fileInput");
const statusMessage = document.getElementById("statusMessage");
const targetSection = document.getElementById("targetSection");
const targetColumnSelect = document.getElementById("targetColumn");
const startTrainingBtn = document.getElementById("startTrainingBtn");
const chartSection = document.getElementById("chartSection");
const metricsSection = document.getElementById("metricsSection");
const previewSection = document.getElementById("previewSection");
const previewHead = document.getElementById("previewHead");
const previewBody = document.getElementById("previewBody");

let currentUploadId = null;
let currentJobId = null;
let currentTargetColumn = null;
let allCharts = {};

Chart.defaults.color = "#666666";
Chart.defaults.font.family =
  "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
Chart.defaults.font.size = 11;

uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.style.backgroundColor = "#e8e8e8";
});

uploadArea.addEventListener("dragleave", () => {
  uploadArea.style.backgroundColor = "";
});

uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.style.backgroundColor = "";
  if (e.dataTransfer.files.length) handleFileUpload(e.dataTransfer.files[0]);
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) handleFileUpload(e.target.files[0]);
});

startTrainingBtn.addEventListener("click", startTraining);

targetColumnSelect.addEventListener("change", (e) => {
  currentTargetColumn = e.target.value;
  startTrainingBtn.disabled = !currentTargetColumn;
});

async function handleFileUpload(file) {
  if (!file.name.endsWith(".csv")) {
    showStatus("Загрузите файл в формате CSV", "error");
    return;
  }

  hideStatus();
  showStatus("Загрузка и обработка файла...", "loading");

  document
    .querySelectorAll("[id*='Section']")
    .forEach((el) => el.classList.add("hidden"));

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload/file", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Ошибка сервера");

    const data = await response.json();
    currentUploadId = data.upload_id;
    currentTargetColumn = null;

    showStatus("Файл загружен. Выберите целевую переменную.", "success");
    populateTargetColumns(data.columns || []);
    if (data.preview && Array.isArray(data.preview)) {
      renderPreview(data.columns || [], data.preview);
    } else {
      previewSection.classList.add("hidden");
    }
  } catch (error) {
    showStatus("Ошибка: " + error.message, "error");
  }
}

function renderPreview(columns, rows) {
  previewHead.innerHTML = "";
  previewBody.innerHTML = "";

  const headerRow = document.createElement("tr");
  columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headerRow.appendChild(th);
  });
  previewHead.appendChild(headerRow);

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((cell) => {
      const td = document.createElement("td");
      td.textContent = cell ?? "";
      tr.appendChild(td);
    });
    previewBody.appendChild(tr);
  });

  previewSection.classList.remove("hidden");
}

function populateTargetColumns(columns) {
  targetColumnSelect.innerHTML = "";
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = "Выберите переменную";
  targetColumnSelect.appendChild(defaultOption);

  columns.forEach((col) => {
    const option = document.createElement("option");
    option.value = col;
    option.textContent = col;
    targetColumnSelect.appendChild(option);
  });

  startTrainingBtn.disabled = true;
  targetSection.classList.remove("hidden");
}

async function startTraining() {
  if (!currentTargetColumn || !currentUploadId) {
    showStatus("Не выбраны данные для обучения", "error");
    return;
  }

  showStatus("Запуск обучения модели...", "loading");
  startTrainingBtn.disabled = true;

  try {
    const response = await fetch(`/api/training/start/${currentUploadId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_column: currentTargetColumn }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Ошибка запуска обучения");
    }

    const data = await response.json();
    currentJobId = data.job_id;
    await pollJobStatus(currentJobId);
  } catch (error) {
    showStatus("Ошибка запуска: " + error.message, "error");
    startTrainingBtn.disabled = false;
  }
}

async function pollJobStatus(jobId) {
  const MAX_ATTEMPTS = 300;
  const INTERVAL = 2000;

  for (let i = 0; i < MAX_ATTEMPTS; i++) {
    try {
      const response = await fetch(`/api/training/status/${jobId}`);
      if (!response.ok) continue;

      const data = await response.json();

      if (data.status === "completed") {
        showStatus("Обучение завершено успешно.", "success");

        await Promise.all([
          loadModelMetrics(jobId),
          loadChartData(currentUploadId),
          loadModelCharts(jobId),
        ]);

        startTrainingBtn.disabled = false;
        return;
      }

      if (data.status === "failed") {
        showStatus("Ошибка обучения модели", "error");
        startTrainingBtn.disabled = false;
        return;
      }
    } catch (error) {
      console.error("Poll error:", error);
    }

    await new Promise((r) => setTimeout(r, INTERVAL));
  }

  startTrainingBtn.disabled = false;
}

async function loadChartData(uploadId) {
  try {
    const response = await fetch(`/api/visualization/chart-data/${uploadId}`);
    if (!response.ok) return;

    const data = await response.json();
    renderStatisticsChart(data);
    chartSection.classList.remove("hidden");
  } catch (error) {
    console.error("Error loading chart data:", error);
  }
}

function renderStatisticsChart(data) {
  const canvasId = "statsChart";
  destroyChart(canvasId);

  const ctx = document.getElementById(canvasId).getContext("2d");
  const labels = data.columns || [];
  const meanValues = labels.map((col) => data.statistics[col]?.mean || 0);
  const stdValues = labels.map((col) => data.statistics[col]?.std || 0);

  allCharts[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Среднее",
          data: meanValues,
          backgroundColor: "#000000",
          borderColor: "#000000",
          borderWidth: 1,
        },
        {
          label: "Стд. отклонение",
          data: stdValues,
          backgroundColor: "#666666",
          borderColor: "#666666",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            padding: 16,
            usePointStyle: true,
            pointStyle: "rect",
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "#e8e8e8" },
          ticks: { padding: 8 },
        },
        x: {
          grid: { display: false },
          ticks: {
            maxRotation: 45,
            minRotation: 45,
            padding: 8,
          },
        },
      },
    },
  });
}

async function loadModelMetrics(jobId) {
  try {
    const response = await fetch(`/api/visualization/model-metrics/${jobId}`);
    if (!response.ok) return;

    const data = await response.json();
    document.getElementById("modelAccuracy").textContent =
      (data.accuracy * 100).toFixed(2) + "%";
    document.getElementById("modelMSE").textContent =
      data.mse?.toFixed(4) || "N/A";
    document.getElementById("trainingFeatures").textContent =
      data.features_used;

    metricsSection.classList.remove("hidden");
  } catch (error) {
    console.error("Error loading model metrics:", error);
  }
}

async function loadModelCharts(jobId) {
  try {
    const response = await fetch(`/api/visualization/model-charts/${jobId}`);
    if (!response.ok) return;

    const data = await response.json();

    if (data.feature_importance) {
      renderImportanceChart(data.feature_importance);
      document.getElementById("importanceSection").classList.remove("hidden");
    }

    if (data.actual && data.predicted) {
      renderScatterChart(data.actual, data.predicted);
      document.getElementById("scatterSection").classList.remove("hidden");
    }

    if (data.residuals) {
      renderResidualsChart(data.residuals);
      document.getElementById("residualsSection").classList.remove("hidden");
    }
  } catch (error) {
    console.error("Error loading model charts:", error);
  }
}

function renderImportanceChart(importanceData) {
  const canvasId = "importanceChart";
  destroyChart(canvasId);

  const ctx = document.getElementById(canvasId).getContext("2d");

  allCharts[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: importanceData.columns,
      datasets: [
        {
          label: "Важность",
          data: importanceData.values,
          backgroundColor: "#000000",
          borderColor: "#000000",
          borderWidth: 1,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      layout: { padding: { left: 10, right: 20, top: 10, bottom: 10 } },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: "#e8e8e8" },
          ticks: { display: true },
        },
        y: {
          grid: { display: false },
          ticks: { display: true, font: { size: 11 } },
        },
      },
      plugins: { legend: { display: false } },
    },
  });
}

function renderScatterChart(actual, predicted) {
  const canvasId = "scatterChart";
  destroyChart(canvasId);

  const ctx = document.getElementById(canvasId).getContext("2d");
  const points = actual.map((val, i) => ({ x: val, y: predicted[i] }));

  allCharts[canvasId] = new Chart(ctx, {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Прогноз",
          data: points,
          backgroundColor: "#000000",
          pointRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      layout: { padding: { left: 40, right: 20, top: 10, bottom: 40 } },
      scales: {
        x: {
          title: {
            display: true,
            text: "Фактические значения",
            padding: { top: 10 },
          },
          grid: { color: "#e8e8e8" },
          ticks: { display: true },
        },
        y: {
          title: {
            display: true,
            text: "Предсказанные значения",
            padding: { bottom: 10 },
          },
          grid: { color: "#e8e8e8" },
          ticks: { display: true },
        },
      },
      plugins: { legend: { display: false } },
    },
  });
}

function renderResidualsChart(residuals) {
  const canvasId = "residualsChart";
  destroyChart(canvasId);

  const ctx = document.getElementById(canvasId).getContext("2d");

  const bins = 20;
  const min = Math.min(...residuals);
  const max = Math.max(...residuals);
  const binSize = (max - min) / bins;

  const histogram = Array(bins).fill(0);
  residuals.forEach((r) => {
    const binIndex = Math.floor((r - min) / binSize);
    if (binIndex >= 0 && binIndex < bins) histogram[binIndex]++;
  });

  const labels = Array(bins)
    .fill(0)
    .map((_, i) => (min + i * binSize).toFixed(2));

  allCharts[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Частота",
          data: histogram,
          backgroundColor: "#666666",
          borderColor: "#000000",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      layout: { padding: { left: 10, right: 20, top: 10, bottom: 30 } },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: "#e8e8e8" },
          ticks: { display: true },
        },
        x: {
          grid: { display: false },
          ticks: {
            display: true,
            maxRotation: 0,
            autoSkip: true,
            maxTicksLimit: 8,
            padding: 4,
          },
        },
      },
      plugins: { legend: { display: false } },
    },
  });
}

function destroyChart(canvasId) {
  if (allCharts[canvasId] instanceof Chart) {
    allCharts[canvasId].destroy();
  }
}

function showStatus(message, type) {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`;
  statusMessage.classList.remove("hidden");
}

function hideStatus() {
  statusMessage.classList.add("hidden");
}

document.addEventListener("DOMContentLoaded", hideStatus);
