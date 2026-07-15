/**
 * form.js
 * Wires the DOM wizard form to state + validators. Owns nothing about
 * submission transport (that's api-client.js) — only collects and
 * validates a profile, then hands off via onSubmit.
 */
import { CONFIG } from "./config.js";
import { qs, qsa } from "./dom-utils.js";
import { getState, updateProfile, setFieldError, setState } from "./state.js";
import * as validators from "./validators.js";
import { createChipInput } from "./components/chip-input.js";
import { createStepWizard } from "./components/step-wizard.js";
import { renderReview } from "./renderer.js";

const FIELD_VALIDATORS = {
    currentRole: validators.validateCurrentRole,
    experienceLevel: validators.validateExperienceLevel,
    skills: validators.validateSkills,
    careerGoal: validators.validateCareerGoal,
    interests: validators.validateInterests,
    targetTimeline: validators.validateTargetTimeline,
    hoursPerWeek: validators.validateHoursPerWeek,
    learningStyle: validators.validateLearningStyle,
};

const LABELS = {
    experienceLevel: {
        student: "Student",
        "0-2": "0–2 years",
        "3-5": "3–5 years",
        "6-10": "6–10 years",
        "10+": "10+ years",
    },
    targetTimeline: { "3mo": "3 months", "6mo": "6 months", "1yr": "1 year", "2yr+": "2+ years" },
    learningStyle: {
        "self-paced": "Self-paced",
        structured: "Structured courses",
        "project-based": "Project-based",
        mixed: "Mixed",
    },
};

export function initForm(root, { onSubmit }) {
    const form = qs(root, "#profile-form");
    const stepEls = CONFIG.STEPS.map((s) => qs(root, `#step-${s.id}`));
    const wizard = createStepWizard(stepEls);

    const submitBtn = qs(root, "#submit-btn");

    wireTextField(root, "currentRole", "input-currentRole");
    wireSegmented(root, "experienceLevel");
    wireSegmented(root, "targetTimeline");
    wireSegmented(root, "learningStyle");
    wireTextarea(root);
    wireRange(root);

    const skillsChips = createChipInput(qs(root, "#chip-mount-skills"), {
        initialValues: getState().profile.skills,
        max: CONFIG.LIMITS.SKILLS_MAX,
        placeholder: "e.g. React, Figma, SQL",
        fieldLabel: "Add a skill",
        validateLabel: validators.validateChipLabel,
        onChange: (values) => {
            updateProfile({ skills: values });
            showFieldError(root, "skills", validators.validateSkills(values));
        },
    });

    const interestsChips = createChipInput(qs(root, "#chip-mount-interests"), {
        initialValues: getState().profile.interests,
        max: CONFIG.LIMITS.INTERESTS_MAX,
        placeholder: "e.g. accessibility, ML infra",
        fieldLabel: "Add an interest",
        validateLabel: validators.validateChipLabel,
        onChange: (values) => {
            updateProfile({ interests: values });
            showFieldError(root, "interests", validators.validateInterests(values));
        },
    });

    qsa(root, '[data-action="next"]').forEach((btn) =>
        btn.addEventListener("click", () => goToStep(getState().currentStep + 1))
    );
    qsa(root, '[data-action="back"]').forEach((btn) =>
        btn.addEventListener("click", () => goToStep(getState().currentStep - 1))
    );

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const errors = validators.validateFullProfile(getState().profile);
        if (Object.keys(errors).length > 0) {
            Object.entries(errors).forEach(([field, msg]) => showFieldError(root, field, msg));
            const firstStepWithError = CONFIG.STEPS.find((s) =>
                Object.keys(validators.validateStep(s.id, getState().profile)).length > 0
            );
            if (firstStepWithError) goToStep(CONFIG.STEPS.findIndex((s) => s.id === firstStepWithError.id));
            return;
        }
        onSubmit(getState().profile);
    });

    function goToStep(index) {
        const clamped = Math.max(0, Math.min(index, CONFIG.STEPS.length - 1));
        const currentStepId = CONFIG.STEPS[getState().currentStep].id;

        if (clamped > getState().currentStep) {
            const errors = validators.validateStep(currentStepId, getState().profile);
            if (Object.keys(errors).length > 0) {
                Object.entries(errors).forEach(([field, msg]) => showFieldError(root, field, msg));
                return;
            }
        }

        setState({ currentStep: clamped });
        wizard.show(clamped);

        if (CONFIG.STEPS[clamped].id === "review") {
            renderReview(qs(root, "#review-list"), getState().profile, LABELS);
        }

        root.dispatchEvent(new CustomEvent("wizard:stepchange", { detail: { step: clamped } }));
    }

    return {
        setSkillsValues: skillsChips.setValues,
        setInterestsValues: interestsChips.setValues,
        setSubmitting(isSubmitting) {
            submitBtn.disabled = isSubmitting;
            submitBtn.classList.toggle("btn--loading", isSubmitting);
        },
        goToStep,
    };
}

function wireTextField(root, field, inputId) {
    const input = qs(root, `#${inputId}`);
    input.value = getState().profile[field] || "";
    input.addEventListener("input", () => updateProfile({ [field]: input.value }));
    input.addEventListener("blur", () => {
        showFieldError(root, field, FIELD_VALIDATORS[field](input.value));
    });
}

function wireTextarea(root) {
    const textarea = qs(root, "#input-careerGoal");
    const counter = qs(root, "#counter-careerGoal");
    textarea.value = getState().profile.careerGoal || "";
    counter.textContent = `${textarea.value.length} / ${CONFIG.LIMITS.CAREER_GOAL_MAX}`;

    textarea.addEventListener("input", () => {
        updateProfile({ careerGoal: textarea.value });
        counter.textContent = `${textarea.value.length} / ${CONFIG.LIMITS.CAREER_GOAL_MAX}`;
    });
    textarea.addEventListener("blur", () => {
        showFieldError(root, "careerGoal", validators.validateCareerGoal(textarea.value));
    });
}

function wireRange(root) {
    const range = qs(root, "#input-hoursPerWeek");
    const valueLabel = qs(root, "#value-hoursPerWeek");
    range.value = getState().profile.hoursPerWeek;
    valueLabel.textContent = `${range.value} hrs`;

    range.addEventListener("input", () => {
        valueLabel.textContent = `${range.value} hrs`;
        updateProfile({ hoursPerWeek: Number(range.value) });
    });
    range.addEventListener("change", () => {
        showFieldError(root, "hoursPerWeek", validators.validateHoursPerWeek(range.value));
    });
}

function wireSegmented(root, field) {
    const group = qs(root, `[data-field="${field}"]`);
    const buttons = qsa(group, ".segmented__option");
    const current = getState().profile[field];
    buttons.forEach((btn) => btn.setAttribute("aria-pressed", String(btn.dataset.value === current)));

    buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
            buttons.forEach((b) => b.setAttribute("aria-pressed", "false"));
            btn.setAttribute("aria-pressed", "true");
            updateProfile({ [field]: btn.dataset.value });
            showFieldError(root, field, FIELD_VALIDATORS[field](btn.dataset.value));
        });
    });
}

function showFieldError(root, field, message) {
    setFieldError(field, message);
    const errorEl = qs(root, `#error-${field}`);
    const fieldEl = qs(root, `#field-${field}`);
    if (errorEl) errorEl.textContent = message || "";
    if (fieldEl) fieldEl.classList.toggle("form__field--error", Boolean(message));
}