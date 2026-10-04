import { apiRequest } from "./client";

export const notificationsApi = {
  list: (unreadOnly = false) => apiRequest("/api/v1/notifications", { params: { unread_only: unreadOnly } }),
  markRead: (id) => apiRequest(`/api/v1/notifications/${id}/read`, { method: "PATCH" }),
  markAllRead: () => apiRequest("/api/v1/notifications/mark-all-read", { method: "POST" }),
};
