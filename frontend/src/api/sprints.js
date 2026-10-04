import { apiRequest } from "./client";

export const sprintsApi = {
  list: (projectId) => apiRequest(`/api/v1/projects/${projectId}/sprints`),
  create: (projectId, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/sprints`, { method: "POST", body: payload }),
  get: (projectId, sprintId) => apiRequest(`/api/v1/projects/${projectId}/sprints/${sprintId}`),
  update: (projectId, sprintId, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/sprints/${sprintId}`, { method: "PATCH", body: payload }),
  start: (projectId, sprintId) =>
    apiRequest(`/api/v1/projects/${projectId}/sprints/${sprintId}/start`, { method: "POST" }),
  close: (projectId, sprintId) =>
    apiRequest(`/api/v1/projects/${projectId}/sprints/${sprintId}/close`, { method: "POST" }),
  cancel: (projectId, sprintId) =>
    apiRequest(`/api/v1/projects/${projectId}/sprints/${sprintId}/cancel`, { method: "POST" }),
  burndown: (projectId, sprintId) =>
    apiRequest(`/api/v1/projects/${projectId}/sprints/${sprintId}/burndown`),
  velocity: (projectId) => apiRequest(`/api/v1/projects/${projectId}/sprints/velocity`),
};
