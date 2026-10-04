import { apiRequest } from "./client";

export const weeklyAvailabilityApi = {
  setup: (schedule) =>
    apiRequest("/api/v1/availability/weekly/setup", {
      method: "POST",
      body: schedule,
    }),

  getSchedule: () =>
    apiRequest("/api/v1/availability/weekly/schedule", { method: "GET" }),

  getToday: () => apiRequest("/api/v1/availability/weekly/today", { method: "GET" }),

  isConfigured: () =>
    apiRequest("/api/v1/availability/weekly/is-configured", { method: "GET" }),

  getAvailableHours: (days = 7) =>
    apiRequest(`/api/v1/availability/weekly/available-hours?days=${days}`, {
      method: "GET",
    }),

  getTeamMemberSchedule: (userId) =>
    apiRequest(`/api/v1/availability/weekly/${userId}/schedule`, { method: "GET" }),
};
