import { apiRequest } from "./client";

export const epicsApi = {
  list: (projectId) => apiRequest(`/api/v1/projects/${projectId}/epics`),
  create: (projectId, payload) =>
    apiRequest(`/api/v1/projects/${projectId}/epics`, { method: "POST", body: payload }),
};
