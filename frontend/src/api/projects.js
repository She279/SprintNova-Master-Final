import { apiRequest } from "./client";

export const projectsApi = {
  list: () => apiRequest("/api/v1/projects"),
  create: (payload) => apiRequest("/api/v1/projects", { method: "POST", body: payload }),
  analyzeAbstract: (file) => {
    const body = new FormData();
    body.append("file", file);
    return apiRequest("/api/v1/projects/analyze-abstract", { method: "POST", body });
  },
  get: (id) => apiRequest(`/api/v1/projects/${id}`),
  update: (id, payload) => apiRequest(`/api/v1/projects/${id}`, { method: "PATCH", body: payload }),

  listMembers: (projectId) => apiRequest(`/api/v1/projects/${projectId}/members`),
  addMember: (projectId, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/members`, { method: "POST", body: payload }),
  removeMember: (projectId, memberId) =>
    apiRequest(`/api/v1/projects/${projectId}/members/${memberId}`, { method: "DELETE" }),

  listMilestones: (projectId) => apiRequest(`/api/v1/projects/${projectId}/milestones`),
  createMilestone: (projectId, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/milestones`, { method: "POST", body: payload }),
  updateMilestone: (projectId, milestoneId, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/milestones/${milestoneId}`, { method: "PATCH", body: payload }),

  roadmap: (projectId) => apiRequest(`/api/v1/projects/${projectId}/roadmap`),
  progress: (projectId) => apiRequest(`/api/v1/projects/${projectId}/progress`),
};
