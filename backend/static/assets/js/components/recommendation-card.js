/**
 * components/recommendation-card.js
 * Builds a single recommendation card (certification, project, or resource).
 * Pure DOM construction — no innerHTML — since item fields originate from
 * AI-generated content and must be treated as untrusted text.
 */
import { el } from "../dom-utils.js";

export function buildRecCard(item) {
    const top = el("div", { class: "rec-card__top" }, [
        el("h3", { class: "rec-card__title" }, [item.title || "Untitled"]),
    ]);
    if (item.level) {
        top.appendChild(el("span", { class: "badge" }, [item.level]));
    }

    const card = el("article", { class: "rec-card" }, [top]);

    if (item.description) {
        card.appendChild(el("p", { class: "rec-card__desc" }, [item.description]));
    }

    if (item.url) {
        let safeHref = null;
        try {
            const parsed = new URL(item.url, window.location.origin);
            if (parsed.protocol === "https:" || parsed.protocol === "http:") {
                safeHref = parsed.href;
            }
        } catch {
            safeHref = null;
        }
        if (safeHref) {
            card.appendChild(
                el(
                    "a",
                    { href: safeHref, target: "_blank", rel: "noopener noreferrer", class: "form__hint" },
                    ["View resource →"]
                )
            );
        }
    }

    return card;
}