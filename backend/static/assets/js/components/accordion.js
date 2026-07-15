/**
 * components/accordion.js
 * Expand/collapse behavior for result section cards on small screens.
 * Desktop disables the collapse via CSS, so this only affects interaction.
 */
export function makeAccordionItem(cardEl, { startExpanded = false } = {}) {
    cardEl.classList.add("accordion__item");
    cardEl.dataset.expanded = String(startExpanded);

    const header = cardEl.querySelector(".card__header");
    if (!header) return;
    header.classList.add("accordion__header");
    header.setAttribute("role", "button");
    header.setAttribute("tabindex", "0");
    header.setAttribute("aria-expanded", String(startExpanded));

    const toggle = () => {
        const next = cardEl.dataset.expanded !== "true";
        cardEl.dataset.expanded = String(next);
        header.setAttribute("aria-expanded", String(next));
    };

    header.addEventListener("click", toggle);
    header.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggle();
        }
    });
}

export function initResultsAccordion(container) {
    container.querySelectorAll(":scope > .card").forEach((card, index) => {
        makeAccordionItem(card, { startExpanded: index === 0 });
    });
}