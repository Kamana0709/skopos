/**
 * main.js
 * App entry point: mounts the navbar, wires the landing page, initializes
 * the form, and orchestrates the loading → streaming → results flow.
 * This is the only module allowed to switch top-level views.
 */
import { CONFIG } from "./config.js";
import { qs, qsa, loadIcon, el, clear } from "./dom-utils.js";
import { getState, setState, updateProfile, resetForNewSession, restoreDraft } from "./state.js";
import { initForm } from "./form.js";
import { requestRecommendations } from "./api-client.js";
import { renderSectionSkeletons, beginSection, appendSectionDelta, endSection } from "./renderer.js";
import { mountNavbar } from "./components/navbar.js";
import { showToast } from "./components/toast.js";
import { confirmModal } from "./components/modal.js";
import { initResultsAccordion } from "./components/accordion.js";

const views = {
    landing: qs(document, "#view-landing"),
    form: qs(document, "#view-form"),
    loading: qs(document, "#view-loading"),
    results: qs(document, "#view-results"),
};

let navbarApi = null;
let formApi = null;
let activeAbortController = null;

async function init() {
    navbarApi = await mountNavbar(qs(document, "#navbar-mount"), {
        onLogoClick: () => goToView("landing"),
    });

    await hydrateIcons(document);

    restoreDraft();

    formApi = initForm(document, { onSubmit: handleSubmit });

    qs(document, "#start-btn").addEventListener("click", () => {
        goToView("form");
        formApi.goToStep(0);
    });

    qs(document, "#copy-btn").addEventListener("click", handleCopy);
    qs(document, "#download-btn").addEventListener("click", handleDownload);
    qs(document, "#start-over-btn").addEventListener("click", handleStartOver);

    document.addEventListener("wizard:stepchange", (e) => {
        navbarApi.setStep(e.detail.step);
    });

    goToView("landing");
}

async function hydrateIcons(scope) {
    const nodes = qsa(scope, "[data-icon]");
    await Promise.all(
        nodes.map(async (node) => {
            const icon = await loadIcon(node.dataset.icon, node.className);
            icon.className = node.className;
            node.replaceWith(icon);
        })
    );
}

function goToView(name) {
    Object.entries(views).forEach(([key, section]) => {
        section.classList.toggle("u-hidden", key !== name);
    });
    setState({ view: name });
    navbarApi.setStep(name === "form" ? getState().currentStep : null);
    const heading = views[name].querySelector("h1, h2");
    if (heading) {
        heading.setAttribute("tabindex", "-1");
        heading.focus();
    }
    window.scrollTo({ top: 0, behavior: "auto" });
}

function clearErrorBanner() {
    clear(qs(document, "#error-banner-slot"));
}

async function showErrorBanner(message, { onRetry } = {}) {
    const slot = qs(document, "#error-banner-slot");
    clear(slot);
    const icon = await loadIcon("icon-error", "error-banner__icon");
    const banner = el("div", { class: "error-banner", role: "alert" }, [
        icon,
        el("div", { class: "error-banner__body" }, [
            el("p", { class: "error-banner__message" }, [message]),
            onRetry
                ? el("div", { class: "error-banner__actions" }, [
                    el("button", { type: "button", class: "btn btn--secondary", onClick: onRetry }, ["Retry"]),
                ])
                : null,
        ]),
    ]);
    slot.appendChild(banner);
}

async function handleSubmit(profile) {
    clearErrorBanner();
    formApi.setSubmitting(true);
    goToView("loading");

    const sectionsContainer = qs(document, "#results-sections");
    renderSectionSkeletons(sectionsContainer);
    setState({ streamStatus: "connecting", sections: {} });

    activeAbortController = new AbortController();

    requestRecommendations(
        profile,
        {
            onOpen: () => setState({ streamStatus: "streaming" }),
            onSectionStart: ({ sectionId }) => {
                beginSection(sectionsContainer, sectionId);
            },
            onSectionDelta: (delta) => {
                appendSectionDelta(sectionsContainer, delta.sectionId, delta);
            },
            onSectionEnd: ({ sectionId }) => {
                endSection(sectionsContainer, sectionId);
            },
            onDone: () => {
                setState({ streamStatus: "done" });
                finishStreaming(sectionsContainer);
            },
            onError: (message) => {
                setState({ streamStatus: "error", streamError: message });
                formApi.setSubmitting(false);
                goToView("form");
                showErrorBanner(message, { onRetry: () => handleSubmit(getState().profile) });
            },
        },
        activeAbortController.signal
    );
}

function finishStreaming(sectionsContainer) {
    formApi.setSubmitting(false);
    const finalContainer = qs(document, "#results-sections-final");
    clear(finalContainer);
    while (sectionsContainer.firstChild) {
        finalContainer.appendChild(sectionsContainer.firstChild);
    }
    initResultsAccordion(finalContainer);
    goToView("results");
    showToast("Your roadmap is ready.", "success");
}

function handleCopy() {
    const text = qsa(document, "#results-sections-final .card")
        .map((card) => {
            const title = card.querySelector(".card__title")?.textContent ?? "";
            const body = card.querySelector('[data-role="section-body"]')?.textContent ?? "";
            return `${title}\n${body}`;
        })
        .join("\n\n");
    navigator.clipboard
        .writeText(text)
        .then(() => showToast("Copied to clipboard.", "success"))
        .catch(() => showToast("Couldn't copy — try selecting the text manually.", "error"));
}

function handleDownload() {
    const text = qsa(document, "#results-sections-final .card")
        .map((card) => {
            const title = card.querySelector(".card__title")?.textContent ?? "";
            const body = card.querySelector('[data-role="section-body"]')?.textContent ?? "";
            return `${title}\n${"=".repeat(title.length)}\n${body}`;
        })
        .join("\n\n");
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = el("a", { href: url, download: "skopos-roadmap.txt" });
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

async function handleStartOver() {
    const confirmed = await confirmModal({
        title: "Start over?",
        body: "This clears your current roadmap and answers. This can't be undone.",
        confirmLabel: "Start over",
        cancelLabel: "Keep my roadmap",
    });
    if (!confirmed) return;
    if (activeAbortController) activeAbortController.abort();
    resetForNewSession();
    location.reload();
}

init();