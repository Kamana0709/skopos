/**
 * components/modal.js
 * Minimal accessible confirm-style modal: traps focus, closes on Escape
 * or overlay click, restores focus to the trigger element on close.
 */
import { el } from "../dom-utils.js";

export function confirmModal({ title, body, confirmLabel = "Confirm", cancelLabel = "Cancel" }) {
    return new Promise((resolve) => {
        const previouslyFocused = document.activeElement;

        const close = (result) => {
            overlay.remove();
            document.removeEventListener("keydown", onKeydown);
            if (previouslyFocused instanceof HTMLElement) previouslyFocused.focus();
            resolve(result);
        };

        const onKeydown = (e) => {
            if (e.key === "Escape") close(false);
            if (e.key === "Tab") {
                const focusable = dialog.querySelectorAll("button");
                const list = Array.from(focusable);
                const first = list[0];
                const last = list[list.length - 1];
                if (e.shiftKey && document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        };

        const dialog = el(
            "div",
            {
                class: "modal",
                role: "alertdialog",
                "aria-modal": "true",
                "aria-labelledby": "modal-title",
                "aria-describedby": "modal-body",
            },
            [
                el("h2", { id: "modal-title", class: "modal__title" }, [title]),
                el("p", { id: "modal-body", class: "modal__body" }, [body]),
                el("div", { class: "modal__actions" }, [
                    el("button", { type: "button", class: "btn btn--secondary", onClick: () => close(false) }, [cancelLabel]),
                    el("button", { type: "button", class: "btn btn--danger", onClick: () => close(true) }, [confirmLabel]),
                ]),
            ]
        );

        const overlay = el("div", { class: "modal-overlay", onClick: (e) => { if (e.target === overlay) close(false); } }, [dialog]);
        document.body.appendChild(overlay);
        document.addEventListener("keydown", onKeydown);
        dialog.querySelector(".btn--secondary").focus();
    });
}