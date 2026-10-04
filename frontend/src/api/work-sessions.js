import { apiRequest } from "./client";

export const workSessionApi = {
  start: () =>
    apiRequest("/api/v1/work-sessions/start", { method: "POST" }),

  getCurrent: () =>
    apiRequest("/api/v1/work-sessions/current", { method: "GET" }),

  stop: (sessionId) =>
    apiRequest(`/api/v1/work-sessions/${sessionId}/stop`, { method: "POST" }),

  getTodayTotal: () =>
    apiRequest("/api/v1/work-sessions/today-total", { method: "GET" }),

  getHistory: (limit = 50, skip = 0) =>
    apiRequest(`/api/v1/work-sessions/history?limit=${limit}&skip=${skip}`, { method: "GET" }),

  getCurrentlyWorking: () =>
    apiRequest("/api/v1/work-sessions/currently-working", { method: "GET" }),
};
