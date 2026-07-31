/**
 * API client — Fetch wrapper with base URL, error handling, and JWT support (Phase 1+).
 */

const API_BASE_URL = `${window.location.origin}/api/v1`;

/**
 * @typedef {Object} ApiError
 * @property {string} error_code
 * @property {string} message
 * @property {Object} [details]
 */

/**
 * Perform an API request.
 * @param {string} endpoint - Path relative to API base (e.g. "/health")
 * @param {RequestInit} [options] - Fetch options
 * @returns {Promise<any>}
 */
export async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // JWT token attachment — implemented in Phase 1
  const token = localStorage.getItem("access_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorBody;
    try {
      errorBody = await response.json();
    } catch {
      errorBody = { message: response.statusText, error_code: "HTTP_ERROR" };
    }
    const error = new Error(errorBody.message || "Request failed");
    error.status = response.status;
    error.errorCode = errorBody.error_code;
    error.details = errorBody.details;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

/**
 * GET request helper.
 * @param {string} endpoint
 * @returns {Promise<any>}
 */
export function get(endpoint) {
  return apiRequest(endpoint, { method: "GET" });
}

/**
 * POST request helper.
 * @param {string} endpoint
 * @param {Object} body
 * @returns {Promise<any>}
 */
export function post(endpoint, body) {
  return apiRequest(endpoint, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * Check API liveness.
 * @returns {Promise<Object>}
 */
export function checkHealth() {
  return get("/health");
}

/**
 * Check API readiness (DB + Redis).
 * @returns {Promise<Object>}
 */
export function checkReadiness() {
  return get("/health/ready");
}

export { API_BASE_URL };
