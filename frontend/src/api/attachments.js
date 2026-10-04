import { apiRequest, getToken } from "./client";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
export const attachmentsApi = {
  list: (projectId) => apiRequest(`/api/v1/projects/${projectId}/attachments`),
  upload: async (projectId, file) => {
    const form = new FormData(); form.append("file", file);
    const res = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/attachments`, { method: "POST", headers: { Authorization: `Bearer ${getToken()}` }, body: form });
    const data = await res.json(); if (!res.ok) throw new Error(data.detail || "Upload failed"); return data;
  },
  download: async (projectId, id) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/projects/${projectId}/attachments/${id}/download`, { headers: { Authorization: `Bearer ${getToken()}` } });
    if (!res.ok) throw new Error("Download failed"); const blob = await res.blob(); return URL.createObjectURL(blob);
  },
  remove: (projectId, id) => apiRequest(`/api/v1/projects/${projectId}/attachments/${id}`, { method: "DELETE" }),
};
