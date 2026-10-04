import { apiRequest } from "./client";

export const testCasesApi = {
  list: (projectId, params = {}) => apiRequest(`/api/v1/projects/${projectId}/test-cases`, { params }),
  create: (projectId, payload) => apiRequest(`/api/v1/projects/${projectId}/test-cases`, { method: "POST", body: payload }),
  update: (projectId, id, payload) => apiRequest(`/api/v1/projects/${projectId}/test-cases/${id}`, { method: "PATCH", body: payload }),
  remove: (projectId, id) => apiRequest(`/api/v1/projects/${projectId}/test-cases/${id}`, { method: "DELETE" }),
  execute: (projectId, id, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/test-cases/${id}/executions`, { method: "POST", body: payload }),
  executions: (projectId, id) => apiRequest(`/api/v1/projects/${projectId}/test-cases/${id}/executions`),
};
