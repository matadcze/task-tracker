export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const API_ENDPOINTS = {
  health: "/api/v1/health",
} as const;

export const REQUEST_TIMEOUT_MS = 30000;
export const POLLING_INTERVAL_MS = 2000;

export const APP_NAME = "Task Manager";
export const APP_VERSION = "1.0.0";
