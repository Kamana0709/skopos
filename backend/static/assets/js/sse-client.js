/**
 * sse-client.js
 * Manual Server-Sent Events parser over fetch()'s ReadableStream.
 * We can't use the native EventSource here because the request is a POST
 * with a JSON body (the user's profile), and EventSource only supports GET.
 */
import { CONFIG } from "./config.js";

export async function streamRecommendations(url, payload, handlers, signal) {
    const { onEvent, onError, onOpen, onClose } = handlers;

    let response;
    try {
        response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "text/event-stream",
            },
            body: JSON.stringify(payload),
            signal,
        });
    } catch (err) {
        if (err.name === "AbortError") return;
        onError(new Error("Couldn't reach the server. Check your connection and try again."));
        return;
    }

    if (!response.ok || !response.body) {
        const message =
            response.status === 422
                ? "Some of your answers didn't pass validation on the server."
                : response.status >= 500
                    ? "The server hit a problem generating your roadmap."
                    : `Request failed (${response.status}).`;
        onError(new Error(message));
        return;
    }

    onOpen();

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let idleTimer = null;

    const resetIdleTimer = () => {
        clearTimeout(idleTimer);
        idleTimer = setTimeout(() => {
            reader.cancel();
            onError(new Error("The connection went quiet. Please retry."));
        }, CONFIG.SSE.IDLE_TIMEOUT_MS);
    };

    resetIdleTimer();

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            resetIdleTimer();
            buffer += decoder.decode(value, { stream: true });

            const frames = buffer.split("\n\n");
            buffer = frames.pop() ?? "";

            for (const frame of frames) {
                const parsed = parseFrame(frame);
                if (parsed) onEvent(parsed.event, parsed.data);
            }
        }

        if (buffer.trim()) {
            const parsed = parseFrame(buffer);
            if (parsed) onEvent(parsed.event, parsed.data);
        }

        clearTimeout(idleTimer);
        onClose();
    } catch (err) {
        clearTimeout(idleTimer);
        if (err.name === "AbortError") return;
        onError(new Error("The connection was interrupted while generating your roadmap."));
    }
}

function parseFrame(rawFrame) {
    const lines = rawFrame.split("\n").filter((l) => l.length > 0 && !l.startsWith(":"));
    if (lines.length === 0) return null;

    let event = "message";
    const dataLines = [];

    for (const line of lines) {
        const colonIndex = line.indexOf(":");
        const field = colonIndex === -1 ? line : line.slice(0, colonIndex);
        let value = colonIndex === -1 ? "" : line.slice(colonIndex + 1);
        if (value.startsWith(" ")) value = value.slice(1);

        if (field === "event") {
            event = value;
        } else if (field === "data") {
            dataLines.push(value);
        }
    }

    const rawData = dataLines.join("\n");
    let data = rawData;
    try {
        data = rawData ? JSON.parse(rawData) : {};
    } catch {
        // Not JSON — keep as raw string (e.g. a plain "ping" keep-alive).
    }
    return { event, data };
}