import { apiRequest } from "./client";

export const tasksApi = {
  list: (projectId, params = {}) => apiRequest(`/api/v1/projects/${projectId}/tasks`, { params }),
  create: (projectId, payload) => apiRequest(`/api/v1/projects/${projectId}/tasks`, { method: "POST", body: payload }),
  update: (projectId, taskId, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/tasks/${taskId}`, { method: "PATCH", body: payload }),
  remove: (projectId, taskId) =>
    apiRequest(`/api/v1/projects/${projectId}/tasks/${taskId}`, { method: "DELETE" }),
  listComments: (projectId, taskId) => apiRequest(`/api/v1/projects/${projectId}/tasks/${taskId}/comments`),
  addComment: (projectId, taskId, body) =>
    apiRequest(`/api/v1/projects/${projectId}/tasks/${taskId}/comments`, { method: "POST", body: { body } }),
  history: (projectId, taskId) => apiRequest(`/api/v1/projects/${projectId}/tasks/${taskId}/history`),
};
