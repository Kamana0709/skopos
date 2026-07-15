/**
 * state.js
 * Central, in-memory app state. No PII persists beyond the tab; only a
 * non-identifying draft of form answers is cached to localStorage so a
 * refresh mid-wizard doesn't lose work.
 */
import { CONFIG } from "./config.js";

const listeners = new Set();

function createInitialProfile() {
    return {
        currentRole: "",
        experienceLevel: "",
        skills: [],
        careerGoal: "",
        interests: [],
        targetTimeline: "",
        hoursPerWeek: 10,
        learningStyle: "",
    };
}

const state = {
    view: "landing",
    currentStep: 0,
    profile: createInitialProfile(),
    fieldErrors: {},
    streamStatus: "idle",
    streamError: null,
    sections: {},
    requestId: null,
};

export function getState() {
    return state;
}

export function setState(patch) {
    Object.assign(state, patch);
    notify();
}

export function updateProfile(patch) {
    Object.assign(state.profile, patch);
    notify();
    persistDraft();
}

export function setFieldError(field, message) {
    if (message) {
        state.fieldErrors = { ...state.fieldErrors, [field]: message };
    } else {
        const { [field]: _drop, ...rest } = state.fieldErrors;
        state.fieldErrors = rest;
    }
    notify();
}

export function resetForNewSession() {
    state.view = "landing";
    state.currentStep = 0;
    state.profile = createInitialProfile();
    state.fieldErrors = {};
    state.streamStatus = "idle";
    state.streamError = null;
    state.sections = {};
    state.requestId = null;
    clearDraft();
    notify();
}

export function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
}

function notify() {
    listeners.forEach((fn) => fn(state));
}

function persistDraft() {
    try {
        localStorage.setItem(CONFIG.STORAGE_KEYS.DRAFT_PROFILE, JSON.stringify(state.profile));
    } catch {
        // Storage can fail (private browsing, quota). Non-fatal — draft is a convenience only.
    }
}

export function restoreDraft() {
    try {
        const raw = localStorage.getItem(CONFIG.STORAGE_KEYS.DRAFT_PROFILE);
        if (!raw) return false;
        const parsed = JSON.parse(raw);
        state.profile = { ...createInitialProfile(), ...parsed };
        return true;
    } catch {
        return false;
    }
}

export function clearDraft() {
    try {
        localStorage.removeItem(CONFIG.STORAGE_KEYS.DRAFT_PROFILE);
    } catch {
        // ignore
    }
}