/**
 * components/toast.js
 * Transient, non-blocking notifications.
 */
import { el } from "../dom-utils.js";
import { CONFIG } from "../config.js";

let region = null;

function ensureRegion() {
    if (region) return region;
    region = el("div", { class: "toast-region", role: "status", "aria-live": "polite" });
    document.body.appendChild(region);
    return region;
}

export function showToast(message, type = "info") {
    const host = ensureRegion();
    const toast = el("div", { class: `toast toast--${type}` }, [message]);
    host.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, CONFIG.TOAST_DURATION_MS);
}