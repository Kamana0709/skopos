/**
 * components/skeleton-loader.js
 * Reusable skeleton placeholder builder.
 */
import { el } from "../dom-utils.js";

export function buildSkeletonCard() {
    return el("div", { class: "skeleton-card", "aria-hidden": "true" }, [
        el("div", { class: "skeleton skeleton-line skeleton-line--title" }),
        el("div", { class: "skeleton skeleton-line skeleton-line--w80" }),
        el("div", { class: "skeleton skeleton-line skeleton-line--w60" }),
    ]);
}

export function buildSkeletonGrid(count) {
    const grid = el("div", { class: "results__sections" });
    for (let i = 0; i < count; i++) {
        grid.appendChild(el("div", { class: "card" }, [buildSkeletonCard()]));
    }
    return grid;
}