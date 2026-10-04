import { apiRequest } from "./client";

export const assistantApi = {
  ask: (projectId, question) =>
    apiRequest(`/api/v1/projects/${projectId}/assistant/ask`, { method: "POST", body: { question } }),
};
