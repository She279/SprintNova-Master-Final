import { apiRequest } from "./client";

export const projectTemplatesApi = {
  list: () => apiRequest("/api/v1/project-templates"),
  create: (payload) => apiRequest("/api/v1/project-templates", { method: "POST", body: payload }),
  get: (id) => apiRequest(`/api/v1/project-templates/${id}`),
  apply: (id, payload) => apiRequest(`/api/v1/project-templates/${id}/apply`, { method: "POST", body: payload }),
};
