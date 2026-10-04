import { apiRequest } from "./client";

export const clientsApi = {
  list: () => apiRequest("/api/v1/clients"),
  create: (payload) => apiRequest("/api/v1/clients", { method: "POST", body: payload }),
  get: (id) => apiRequest(`/api/v1/clients/${id}`),
  update: (id, payload) => apiRequest(`/api/v1/clients/${id}`, { method: "PATCH", body: payload }),
};
