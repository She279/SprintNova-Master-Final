import { apiRequest } from "./client";

export const dailyWorkUpdatesApi = {
  create: (updateData) =>
    apiRequest("/api/v1/daily-updates", {
      method: "POST",
      body: updateData,
    }),

  getTodayUpdate: () =>
    apiRequest("/api/v1/daily-updates/me/today", { method: "GET" }),

  checkPending: () =>
    apiRequest("/api/v1/daily-updates/me/pending", { method: "GET" }),

  getHistory: (startDate, endDate, limit = 30, skip = 0) => {
    let url = `/api/v1/daily-updates/me/history?limit=${limit}&skip=${skip}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    return apiRequest(url, { method: "GET" });
  },

  update: (updateId, updateData) =>
    apiRequest(`/api/v1/daily-updates/${updateId}`, {
      method: "PUT",
      body: updateData,
    }),

  getAnalysis: (updateId) =>
    apiRequest(`/api/v1/daily-updates/${updateId}/analysis`, { method: "GET" }),

  triggerAnalysis: (updateId) =>
    apiRequest(`/api/v1/daily-updates/${updateId}/analyze`, { method: "POST" }),

  getTeamUpdates: () =>
    apiRequest("/api/v1/daily-updates/team/today", { method: "GET" }),
};
