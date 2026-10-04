import { apiRequest } from "./client";

export const employeesApi = {
  previewCompanyEmail: (first_name, last_name) =>
    apiRequest("/api/v1/employees/preview-company-email", { params: { first_name, last_name } }),

  create: (payload) => apiRequest("/api/v1/employees", { method: "POST", body: payload }),

  list: () => apiRequest("/api/v1/employees"),

  get: (id) => apiRequest(`/api/v1/employees/${id}`),

  setStatus: (id, is_active) =>
    apiRequest(`/api/v1/employees/${id}/status`, { method: "PATCH", body: { is_active } }),

  loginHistory: (id) => apiRequest(`/api/v1/employees/${id}/login-history`),
};
