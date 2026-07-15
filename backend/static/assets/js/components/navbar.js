/**
 * components/navbar.js
 * Renders the sticky top bar and keeps its step-progress display in sync
 * with app state.
 */
import { el, loadIcon } from "../dom-utils.js";
import { CONFIG } from "../config.js";

export async function mountNavbar(container, { onLogoClick }) {
    const logoMark = await loadIcon("icon-roadmap", "navbar__logo-mark");

    const progressFill = el("div", { class: "navbar__progress-fill" });
    const progressLabel = el("span", { class: "navbar__progress-label" }, ["Step 1 of 3"]);
    const progressTrack = el("div", { class: "navbar__progress-track" }, [progressFill]);

    const stepEls = CONFIG.STEPS.map((step) =>
        el("span", { class: "navbar__step", dataset: { stepId: step.id } }, [
            el("span", { class: "navbar__step-dot" }),
            step.label,
        ])
    );

    const nav = el("nav", { class: "navbar", "aria-label": "Progress" }, [
        el(
            "button",
            { type: "button", class: "navbar__logo", onClick: onLogoClick, "aria-label": "Skopos home" },
            [logoMark, "Skopos"]
        ),
        el("div", { class: "navbar__progress", id: "navbar-progress" }, [progressTrack, progressLabel]),
        el("div", { class: "navbar__steps" }, stepEls),
        el("span", { class: "navbar__version" }, ["v1.0"]),
    ]);

    container.appendChild(nav);

    window.addEventListener("scroll", () => {
        nav.classList.toggle("navbar--scrolled", window.scrollY > 4);
    });

    return {
        setStep(stepIndex) {
            const progressWrap = nav.querySelector("#navbar-progress");
            const stepsWrap = nav.querySelector(".navbar__steps");
            if (stepIndex === null) {
                progressWrap.classList.add("u-hidden");
                stepsWrap.classList.add("u-hidden");
                return;
            }
            progressWrap.classList.remove("u-hidden");
            stepsWrap.classList.remove("u-hidden");

            const total = CONFIG.STEPS.length;
            const pct = ((stepIndex + 1) / total) * 100;
            progressFill.style.width = `${pct}%`;
            progressLabel.textContent = `Step ${stepIndex + 1} of ${total}`;

            stepEls.forEach((stepEl, i) => {
                stepEl.classList.toggle("navbar__step--active", i === stepIndex);
                stepEl.classList.toggle("navbar__step--done", i < stepIndex);
            });
        },
    };
}