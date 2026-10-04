import { apiRequest } from "./client";

export const codeReviewsApi = {
  list: (projectId) => apiRequest(`/api/v1/projects/${projectId}/code-reviews`),
  create: (projectId, payload) => apiRequest(`/api/v1/projects/${projectId}/code-reviews`, { method: "POST", body: payload }),
  update: (projectId, id, payload) => apiRequest(`/api/v1/projects/${projectId}/code-reviews/${id}`, { method: "PATCH", body: payload }),
};

export const buildsApi = {
  list: (projectId) => apiRequest(`/api/v1/projects/${projectId}/builds`),
  create: (projectId, payload) => apiRequest(`/api/v1/projects/${projectId}/builds`, { method: "POST", body: payload }),
  update: (projectId, id, payload) => apiRequest(`/api/v1/projects/${projectId}/builds/${id}`, { method: "PATCH", body: payload }),
};
