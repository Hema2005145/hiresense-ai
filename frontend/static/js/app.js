/**
 * HireSense AI — frontend application shell.
 *
 * Phase 2 only wires up a minimal API client and a health check ping
 * so the static frontend/backend integration is proven end-to-end
 * before any feature UI is built. Later modules add real screens
 * (upload forms, dashboard, mock interview) on top of `apiRequest`.
 */

const API_BASE_URL = "/api/v1";

/**
 * Thin fetch wrapper shared by every future frontend module.
 * Centralizes the base URL, JSON handling, and error-envelope
 * parsing (matching the {"error": {code, message, details}} shape
 * every backend error returns) so individual feature scripts don't
 * each reimplement fetch error handling.
 *
 * @param {string} path - path relative to API_BASE_URL, e.g. "/health"
 * @param {RequestInit} [options]
 * @returns {Promise<any>}
 */
async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      (body && body.error && body.error.message) ||
      `Request to ${path} failed with status ${response.status}`;
    throw new Error(message);
  }

  return body;
}

async function checkApiHealth() {
  const badge = document.getElementById("api-status-badge");
  if (!badge) return;

  try {
    const data = await apiRequest("/health");
    badge.textContent = `API online (${data.environment})`;
    badge.classList.remove("bg-secondary", "bg-danger");
    badge.classList.add("bg-success");
  } catch (error) {
    badge.textContent = "API unreachable";
    badge.classList.remove("bg-secondary", "bg-success");
    badge.classList.add("bg-danger");
    console.error("Health check failed:", error);
  }
}

document.addEventListener("DOMContentLoaded", checkApiHealth);
