import { apiRequest } from "./client";

export const bugsApi = {
  list: (projectId, params = {}) => apiRequest(`/api/v1/projects/${projectId}/bugs`, { params }),
  create: (projectId, payload) => apiRequest(`/api/v1/projects/${projectId}/bugs`, { method: "POST", body: payload }),
  update: (projectId, id, payload) => apiRequest(`/api/v1/projects/${projectId}/bugs/${id}`, { method: "PATCH", body: payload }),
  listComments: (projectId, id) => apiRequest(`/api/v1/projects/${projectId}/bugs/${id}/comments`),
  addComment: (projectId, id, body) => apiRequest(`/api/v1/projects/${projectId}/bugs/${id}/comments`, { method: "POST", body: { body } }),
  history: (projectId, id) => apiRequest(`/api/v1/projects/${projectId}/bugs/${id}/history`),
};
