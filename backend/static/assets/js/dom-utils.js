/**
 * dom-utils.js
 * Small, dependency-free DOM helpers. XSS-safe by construction:
 * every text insertion goes through textContent, never innerHTML.
 */

export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") {
      node.className = value;
    } else if (key === "dataset") {
      Object.assign(node.dataset, value);
    } else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (key === "text") {
      node.textContent = value;
    } else if (value === true) {
      node.setAttribute(key, "");
    } else {
      node.setAttribute(key, String(value));
    }
  }
  for (const child of children) {
    append(node, child);
  }
  return node;
}

function append(node, child) {
  if (child === null || child === undefined || child === false) return;
  if (Array.isArray(child)) {
    child.forEach((c) => append(node, c));
    return;
  }
  node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
}

/** Remove all children of a node. */
export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

export function qs(scope, selector) {
  const node = (scope || document).querySelector(selector);
  return node;
}

export function qsa(scope, selector) {
  return Array.from((scope || document).querySelectorAll(selector));
}

/**
 * Load an SVG icon by id from assets/icons/{name}.svg and inline it,
 * so it can inherit color via currentColor. Cached after first fetch.
 * Relative path (no leading slash) so it resolves correctly whether the
 * app is served from a subfolder (Live Server) or the domain root (FastAPI).
 */
const iconCache = new Map();
export async function loadIcon(name, className) {
  if (!iconCache.has(name)) {
    iconCache.set(
      name,
      fetch(`assets/icons/${name}.svg`)
        .then((r) => (r.ok ? r.text() : ""))
        .catch(() => "")
    );
  }
  const markup = await iconCache.get(name);
  const wrapper = el("span", { class: className || "icon" });
  const template = document.createElement("template");
  template.innerHTML = markup.trim();
  const svg = template.content.firstElementChild;
  if (svg) wrapper.appendChild(svg);
  return wrapper;
}

/** Debounce a function by a given delay. */
export function debounce(fn, delay) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/** Very small pub/sub for cross-module UI events (toasts, modals). */
export const bus = new EventTarget();
export function emit(name, detail) {
  bus.dispatchEvent(new CustomEvent(name, { detail }));
}
export function on(name, handler) {
  bus.addEventListener(name, handler);
  return () => bus.removeEventListener(name, handler);
}

/**
 * Minimal, safe markdown-lite renderer for AI-generated text:
 * supports **bold**, *italic*, and line breaks only. Returns DOM nodes,
 * never raw HTML, so there is no injection surface.
 */
export function renderInlineMarkdown(text) {
  const frag = document.createDocumentFragment();
  const lines = String(text ?? "").split("\n");
  lines.forEach((line, i) => {
    if (i > 0) frag.appendChild(document.createElement("br"));
    const tokenPattern = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
    let lastIndex = 0;
    let match;
    while ((match = tokenPattern.exec(line))) {
      if (match.index > lastIndex) {
        frag.appendChild(document.createTextNode(line.slice(lastIndex, match.index)));
      }
      const token = match[0];
      if (token.startsWith("**")) {
        frag.appendChild(el("strong", {}, [token.slice(2, -2)]));
      } else {
        frag.appendChild(el("em", {}, [token.slice(1, -1)]));
      }
      lastIndex = tokenPattern.lastIndex;
    }
    if (lastIndex < line.length) {
      frag.appendChild(document.createTextNode(line.slice(lastIndex)));
    }
  });
  return frag;
}