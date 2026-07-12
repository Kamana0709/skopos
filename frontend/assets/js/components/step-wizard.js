/**
 * components/step-wizard.js
 * Thin controller around a set of step panels: shows exactly one at a
 * time, applies the reticle "active" treatment, and manages focus.
 */
export function createStepWizard(stepPanels) {
    function show(index) {
        stepPanels.forEach((panel, i) => {
            const isActive = i === index;
            panel.classList.toggle("u-hidden", !isActive);
            panel.classList.toggle("reticle--active", isActive);
            panel.setAttribute("aria-hidden", String(!isActive));
        });
        const heading = stepPanels[index]?.querySelector("h1, h2, h3");
        if (heading) {
            heading.setAttribute("tabindex", "-1");
            heading.focus();
        }
    }

    return { show };
}