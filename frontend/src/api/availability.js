import { apiRequest } from "./client";

export const availabilityApi = {
  setMine: (payload) => apiRequest("/api/v1/availability/me", { method: "PUT", body: payload }),
  mine: (start, end) => apiRequest("/api/v1/availability/me", { params: { start, end } }),
  team: (start, end, userIds) =>
    apiRequest("/api/v1/availability/team", { params: { start, end, user_ids: userIds.join(",") } }),
};
