import { API_BASE_URL } from "./api";

export type LogLevel = "INFO" | "WARN" | "ERROR";

export interface FrontendLogPayload {
  event: string;
  message: string;
  level?: LogLevel;
  metadata?: Record<string, unknown>;
}

/**
 * Fire-and-forget logging utility that sends client events to the backend
 * and appends them to logs/logs.txt without blocking the UI thread.
 */
export async function logFrontendAction(
  event: string,
  message: string,
  level: LogLevel = "INFO",
  metadata?: Record<string, unknown>
): Promise<void> {
  try {
    const payload: FrontendLogPayload = {
      event,
      message,
      level,
      metadata,
    };

    await fetch(`${API_BASE_URL}/api/v1/logs/event`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {
      // Non-blocking fallback: never disrupt frontend user experience
    });
  } catch {
    // Non-blocking fallback
  }
}
