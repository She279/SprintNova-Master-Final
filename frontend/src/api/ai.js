import { apiRequest } from "./client";

export const aiApi = {
  commandCenter: () => apiRequest("/api/v1/ai/command-center"),
  simulate: (payload) => apiRequest("/api/v1/ai/simulate", { method: "POST", body: payload }),
  workloadSummary: () => apiRequest("/api/v1/ai/workload-summary"),
  teamAllocation: (projectId) => apiRequest(`/api/v1/ai/projects/${projectId}/team-allocation`),
  sprintPlanning: (projectId) => apiRequest(`/api/v1/ai/projects/${projectId}/sprint-planning`),
  taskRisk: (projectId) => apiRequest(`/api/v1/ai/projects/${projectId}/task-risk`),
  qualityRisk: (projectId) => apiRequest(`/api/v1/ai/projects/${projectId}/quality-risk`),
  completionPrediction: (projectId) => apiRequest(`/api/v1/ai/projects/${projectId}/completion-prediction`),
};
