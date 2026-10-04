import { apiRequest } from "./client";

export const dashboardApi = {
  me: () => apiRequest("/api/v1/dashboard"),
  bugStats: (projectId) => apiRequest(`/api/v1/reports/projects/${projectId}/bug-stats`),
  taskCompletion: (projectId) => apiRequest(`/api/v1/reports/projects/${projectId}/task-completion`),
  testingProgress: (projectId) => apiRequest(`/api/v1/reports/projects/${projectId}/testing-progress`),
  projectHealth: (projectId) => apiRequest(`/api/v1/reports/projects/${projectId}/health`),
};
