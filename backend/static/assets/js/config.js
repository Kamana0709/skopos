/**
 * config.js
 * Single source of truth for app-wide constants, endpoints, and field limits.
 * No other module should hardcode a URL, a limit number, or a timing value.
 */

export const CONFIG = Object.freeze({
  API_BASE: "http://localhost:8000", // same-origin; FastAPI serves the static frontend, so relative paths are correct
  ENDPOINTS: Object.freeze({
    RECOMMENDATIONS_STREAM: "/api/v1/recommendations/stream",
  }),

  SSE: Object.freeze({
    RECONNECT_ATTEMPTS: 0, // per PRD: no auto-reconnect, surface a retry action instead
    IDLE_TIMEOUT_MS: 30000, // if no event arrives for this long, treat the stream as stalled
  }),

  LIMITS: Object.freeze({
    SKILLS_MIN: 0,
    SKILLS_MAX: 30,
    INTERESTS_MIN: 1,
    INTERESTS_MAX: 15,
    CAREER_GOAL_MIN: 10,
    CAREER_GOAL_MAX: 500,
    HOURS_MIN: 1,
    HOURS_MAX: 80,
    CHIP_LABEL_MAX: 40,
  }),

  STORAGE_KEYS: Object.freeze({
    DRAFT_PROFILE: "skopos:draft-profile", // non-PII form draft only; never store results or identifiers
  }),

  TOAST_DURATION_MS: 4000,

  STEPS: Object.freeze([
    { id: "background", label: "Background" },
    { id: "goals", label: "Goals" },
    { id: "availability", label: "Availability" },
    { id: "review", label: "Review" },
  ]),

  RESULT_SECTIONS: Object.freeze([
    { id: "summary", label: "Summary", icon: "icon-career" },
    { id: "skillGaps", label: "Skill Gaps", icon: "icon-skill-gap" },
    { id: "roadmap", label: "Roadmap", icon: "icon-roadmap" },
    { id: "certifications", label: "Certifications", icon: "icon-certification" },
    { id: "projects", label: "Projects", icon: "icon-project" },
    { id: "resources", label: "Resources", icon: "icon-resource" },
  ]),
});