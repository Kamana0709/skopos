/**
 * renderer.js
 * Turns section state into DOM. Every text value goes through textContent
 * or renderInlineMarkdown — never innerHTML — since section content
 * originates from the AI model and must be treated as untrusted.
 */
import { el, clear, renderInlineMarkdown } from "./dom-utils.js";
import { CONFIG } from "./config.js";
import { buildRecCard } from "./components/recommendation-card.js";

export function renderSectionSkeletons(container) {
  clear(container);
  CONFIG.RESULT_SECTIONS.forEach((section) => {
    const card = el("section", {
      class: "card",
      id: `section-${section.id}`,
      "aria-busy": "true",
      dataset: { sectionId: section.id },
    });
    card.appendChild(
      el("div", { class: "card__header" }, [
        el("h2", { class: "card__title" }, [section.label]),
      ])
    );
    const body = el("div", { class: "card__body", dataset: { role: "section-body" } }, [
      el("div", { class: "skeleton-card" }, [
        el("div", { class: "skeleton skeleton-line skeleton-line--title" }),
        el("div", { class: "skeleton skeleton-line skeleton-line--w80" }),
        el("div", { class: "skeleton skeleton-line skeleton-line--w60" }),
      ]),
    ]);
    card.appendChild(body);
    container.appendChild(card);
  });
}

export function beginSection(container, sectionId) {
  const card = container.querySelector(`#section-${sectionId}`);
  if (!card) return;
  card.setAttribute("aria-busy", "true");
  const body = card.querySelector('[data-role="section-body"]');
  clear(body);
  const textTarget = el("p", { class: "stream-cursor" });
  body.appendChild(textTarget);
}

export function appendSectionDelta(container, sectionId, delta) {
  const card = container.querySelector(`#section-${sectionId}`);
  if (!card) return;
  const body = card.querySelector('[data-role="section-body"]');

  if (delta && typeof delta === "object" && delta.item) {
    let grid = body.querySelector(".card-grid");
    if (!grid) {
      const textNode = body.querySelector(".stream-cursor");
      if (textNode) textNode.remove();
      grid = el("div", { class: "card-grid" });
      body.appendChild(grid);
    }
    grid.appendChild(buildRecCard(delta.item));
    return;
  }

  const text = typeof delta === "string" ? delta : delta?.text ?? "";
  if (!text) return;
  let textTarget = body.querySelector(".stream-cursor");
  if (!textTarget) {
    textTarget = el("p", { class: "stream-cursor" });
    body.appendChild(textTarget);
  }
  textTarget.appendChild(renderInlineMarkdown(text));
}

export function endSection(container, sectionId) {
  const card = container.querySelector(`#section-${sectionId}`);
  if (!card) return;
  card.setAttribute("aria-busy", "false");
  const cursor = card.querySelector(".stream-cursor");
  if (cursor) cursor.classList.remove("stream-cursor");
  if (!card.querySelector('[data-role="section-body"]').children.length) {
    card.querySelector('[data-role="section-body"]').appendChild(
      el("p", { class: "form__hint" }, ["Nothing to show here for your profile."])
    );
  }
}

export function renderReview(container, profile, labels) {
  clear(container);
  const rows = [
    ["Current role", profile.currentRole],
    ["Experience", labels.experienceLevel[profile.experienceLevel] || profile.experienceLevel],
    ["Skills", profile.skills.join(", ") || "—"],
    ["Career goal", profile.careerGoal],
    ["Interests", profile.interests.join(", ")],
    ["Target timeline", labels.targetTimeline[profile.targetTimeline] || profile.targetTimeline],
    ["Hours per week", `${profile.hoursPerWeek} hrs/week`],
    ["Learning style", labels.learningStyle[profile.learningStyle] || profile.learningStyle],
  ];
  rows.forEach(([label, value]) => {
    container.appendChild(
      el("div", { class: "review__row" }, [
        el("span", { class: "form__label" }, [label]),
        el("span", {}, [value || "—"]),
      ])
    );
  });
}