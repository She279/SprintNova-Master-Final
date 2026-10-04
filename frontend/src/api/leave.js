import { apiRequest } from "./client";

export const leaveApi = {
  create: (payload) => apiRequest("/api/v1/leave-requests", { method: "POST", body: payload }),
  mine: () => apiRequest("/api/v1/leave-requests/me"),
  all: (status) => apiRequest("/api/v1/leave-requests", { params: { status } }),
  decide: (id, approve, reviewNote) =>
    apiRequest(`/api/v1/leave-requests/${id}/decide`, {
      method: "PATCH",
      body: { approve, review_note: reviewNote },
    }),
};
