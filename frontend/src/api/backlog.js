import { apiRequest } from "./client";

export const backlogApi = {
  list: (projectId, params = {}) => apiRequest(`/api/v1/projects/${projectId}/backlog`, { params }),
  create: (projectId, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/backlog`, { method: "POST", body: payload }),
  update: (projectId, storyId, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/backlog/${storyId}`, { method: "PATCH", body: payload }),
  remove: (projectId, storyId) =>
    apiRequest(`/api/v1/projects/${projectId}/backlog/${storyId}`, { method: "DELETE" }),
  reorder: (projectId, storyIdsInOrder) =>
    apiRequest(`/api/v1/projects/${projectId}/backlog/reorder`, {
      method: "POST",
      body: { story_ids_in_order: storyIdsInOrder },
    }),
  assignToSprint: (projectId, storyId, sprintId) =>
    apiRequest(`/api/v1/projects/${projectId}/backlog/${storyId}/sprint`, {
      method: "PATCH",
      body: { sprint_id: sprintId },
    }),
};
