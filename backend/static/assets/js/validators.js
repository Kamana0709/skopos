/**
 * validators.js
 * Pure functions — no DOM access. Each returns "" (valid) or an error string.
 * Mirrors CONFIG.LIMITS exactly so client-side rules never drift from config.
 */
import { CONFIG } from "./config.js";

const { LIMITS } = CONFIG;

export function validateCurrentRole(value) {
    if (!value || !value.trim()) return "Tell us your current role, even if it's \"student\".";
    return "";
}

export function validateExperienceLevel(value) {
    if (!value) return "Pick the option closest to your experience.";
    return "";
}

export function validateSkills(skills) {
    if (skills.length > LIMITS.SKILLS_MAX) {
        return `You've added ${skills.length} skills — the max is ${LIMITS.SKILLS_MAX}. Remove a few to continue.`;
    }
    return "";
}

export function validateCareerGoal(value) {
    const len = (value || "").trim().length;
    if (len === 0) return "Tell us what you're aiming for — this shapes your whole roadmap.";
    if (len < LIMITS.CAREER_GOAL_MIN) {
        return `A bit more detail helps — at least ${LIMITS.CAREER_GOAL_MIN} characters (${len}/${LIMITS.CAREER_GOAL_MIN}).`;
    }
    if (len > LIMITS.CAREER_GOAL_MAX) {
        return `That's a bit long — keep it under ${LIMITS.CAREER_GOAL_MAX} characters (${len}/${LIMITS.CAREER_GOAL_MAX}).`;
    }
    return "";
}

export function validateInterests(interests) {
    if (interests.length < LIMITS.INTERESTS_MIN) {
        return "Add at least one interest so we know where to point your roadmap.";
    }
    if (interests.length > LIMITS.INTERESTS_MAX) {
        return `That's ${interests.length} interests — the max is ${LIMITS.INTERESTS_MAX}.`;
    }
    return "";
}

export function validateTargetTimeline(value) {
    if (!value) return "Choose a target timeline.";
    return "";
}

export function validateHoursPerWeek(value) {
    const n = Number(value);
    if (!Number.isFinite(n) || n < LIMITS.HOURS_MIN || n > LIMITS.HOURS_MAX) {
        return `Enter a number between ${LIMITS.HOURS_MIN} and ${LIMITS.HOURS_MAX}.`;
    }
    return "";
}

export function validateLearningStyle(value) {
    if (!value) return "Pick the style that fits you best.";
    return "";
}

export function validateChipLabel(label) {
    const trimmed = (label || "").trim();
    if (!trimmed) return "";
    if (trimmed.length > LIMITS.CHIP_LABEL_MAX) {
        return `Keep each entry under ${LIMITS.CHIP_LABEL_MAX} characters.`;
    }
    return "";
}

export function validateStep(stepId, profile) {
    const errors = {};
    const set = (field, error) => {
        if (error) errors[field] = error;
    };

    if (stepId === "background") {
        set("currentRole", validateCurrentRole(profile.currentRole));
        set("experienceLevel", validateExperienceLevel(profile.experienceLevel));
        set("skills", validateSkills(profile.skills));
    } else if (stepId === "goals") {
        set("careerGoal", validateCareerGoal(profile.careerGoal));
        set("interests", validateInterests(profile.interests));
    } else if (stepId === "availability") {
        set("targetTimeline", validateTargetTimeline(profile.targetTimeline));
        set("hoursPerWeek", validateHoursPerWeek(profile.hoursPerWeek));
        set("learningStyle", validateLearningStyle(profile.learningStyle));
    }
    return errors;
}

export function validateFullProfile(profile) {
    return {
        ...validateStep("background", profile),
        ...validateStep("goals", profile),
        ...validateStep("availability", profile),
    };
}