/**
 * Client-side router — expanded in Phase 1+ when auth pages are added.
 */

const routes = {
  "/": renderHome,
};

/**
 * Navigate to a path and render the corresponding view.
 * @param {string} path
 */
export function navigate(path) {
  window.history.pushState({}, "", path);
  renderRoute(path);
}

/**
 * Render the route matching the current path.
 * @param {string} [path]
 */
export function renderRoute(path) {
  const currentPath = path || window.location.pathname;
  const handler = routes[currentPath] || routes["/"];
  if (handler) {
    handler();
  }
}

/**
 * Initialize the router with popstate listener.
 */
export function initRouter() {
  window.addEventListener("popstate", () => renderRoute());
}

/**
 * Home view — Phase 0 landing is static HTML; this hook is for future SPA routes.
 */
function renderHome() {
  // Landing page content is static in index.html for Phase 0
}
