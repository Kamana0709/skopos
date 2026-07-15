/**
 * api-client.js
 * Talks to the backend in terms the rest of the app understands: no fetch()
 * or SSE parsing details leak out of this module.
 */
import { CONFIG } from "./config.js";
import { streamRecommendations } from "./sse-client.js";

function toRequestPayload(profile) {
  return {
    current_role: profile.currentRole.trim(),
    experience_level: profile.experienceLevel,
    skills: profile.skills,
    career_goal: profile.careerGoal.trim(),
    interests: profile.interests,
    target_timeline: profile.targetTimeline,
    hours_per_week: Number(profile.hoursPerWeek),
    learning_style: profile.learningStyle,
  };
}

export function requestRecommendations(profile, callbacks, signal) {
  const url = `${CONFIG.API_BASE}${CONFIG.ENDPOINTS.RECOMMENDATIONS_STREAM}`;
  const payload = toRequestPayload(profile);

  return streamRecommendations(
    url,
    payload,
    {
      onOpen: () => callbacks.onOpen?.(),
      onClose: () => callbacks.onDone?.(),
      onError: (err) => callbacks.onError?.(err.message),
      onEvent: (eventName, data) => {
        switch (eventName) {
          case "section_start":
            callbacks.onSectionStart?.(data);
            break;
          case "section_delta":
            callbacks.onSectionDelta?.(data);
            break;
          case "section_end":
            callbacks.onSectionEnd?.(data);
            break;
          case "done":
            callbacks.onDone?.(data);
            break;
          case "error":
            callbacks.onError?.(typeof data === "string" ? data : data?.message || "Something went wrong generating your roadmap.");
            break;
          default:
            break;
        }
      },
    },
    signal
  );
}