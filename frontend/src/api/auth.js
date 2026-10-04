import { apiRequest } from "./client";

export const authApi = {
  login: (company_email, password) =>
    apiRequest("/api/v1/auth/login", { method: "POST", body: { company_email, password }, auth: false }),

  changePassword: (current_password, new_password, confirm_new_password) =>
    apiRequest("/api/v1/auth/change-password", {
      method: "POST",
      body: { current_password, new_password, confirm_new_password },
    }),

  forgotPassword: (company_email) =>
    apiRequest("/api/v1/auth/forgot-password", { method: "POST", body: { company_email }, auth: false }),

  verifyOtp: (company_email, otp) =>
    apiRequest("/api/v1/auth/verify-otp", { method: "POST", body: { company_email, otp }, auth: false }),

  resetPassword: (company_email, otp, new_password, confirm_new_password) =>
    apiRequest("/api/v1/auth/reset-password", {
      method: "POST",
      body: { company_email, otp, new_password, confirm_new_password },
      auth: false,
    }),
};
