import { apiRequest } from "./client";

export const documentsApi = {
  list: (projectId) => apiRequest(`/api/v1/projects/${projectId}/documents`),
  create: (projectId, payload) => apiRequest(`/api/v1/projects/${projectId}/documents`, { method: "POST", body: payload }),
  update: (projectId, id, payload) => apiRequest(`/api/v1/projects/${projectId}/documents/${id}`, { method: "PATCH", body: payload }),
  remove: (projectId, id) => apiRequest(`/api/v1/projects/${projectId}/documents/${id}`, { method: "DELETE" }),
};
