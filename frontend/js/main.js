/**
 * Application entry point — Phase 0.
 */

import { checkHealth, checkReadiness } from "./api.js";
import { initRouter } from "./router.js";

/**
 * Render system status on the landing page.
 */
async function loadSystemStatus() {
  const container = document.getElementById("status-content");
  if (!container) return;

  try {
    const [health, readiness] = await Promise.allSettled([
      checkHealth(),
      checkReadiness(),
    ]);

    let html = "";

    if (health.status === "fulfilled") {
      const data = health.value;
      html += statusRow("API", "ok", `${data.service} v${data.version} (${data.environment})`);
    } else {
      html += statusRow("API", "error", "Unreachable");
    }

    if (readiness.status === "fulfilled") {
      const data = readiness.value;
      const dbStatus = data.database?.status || "error";
      const redisStatus = data.redis?.status || "error";
      html += statusRow("Database", dbStatus, data.database?.message || "Unknown");
      html += statusRow("Redis", redisStatus, data.redis?.message || "Unknown");
      html += statusRow("Overall", data.status === "ready" ? "ok" : "error", data.status);
    } else {
      html += statusRow("Dependencies", "error", "Readiness check failed");
    }

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="alert alert--error">Failed to load status: ${err.message}</div>`;
  }
}

/**
 * Build a status row HTML string.
 * @param {string} label
 * @param {"ok"|"error"|"pending"} status
 * @param {string} message
 * @returns {string}
 */
function statusRow(label, status, message) {
  const dotClass =
    status === "ok" ? "status-dot--ok" : status === "error" ? "status-dot--error" : "status-dot--pending";
  return `
    <div class="landing__status-item">
      <span><span class="status-dot ${dotClass}"></span>${label}</span>
      <span>${message}</span>
    </div>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  initRouter();
  loadSystemStatus();
});
