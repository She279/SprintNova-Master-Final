import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { authApi } from "../api/auth";
import { setToken, getToken } from "../api/client";

const AuthContext = createContext(null);

function decodeRoleFromStorage() {
  try {
    return JSON.parse(localStorage.getItem("sprintnova_session") || "null");
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => (getToken() ? decodeRoleFromStorage() : null));

  const login = useCallback(async (companyEmail, password) => {
    const data = await authApi.login(companyEmail, password);
    setToken(data.access_token);
    const nextSession = {
      role: data.role,
      fullName: data.full_name,
      mustChangePassword: data.must_change_password,
      companyEmail,
    };
    localStorage.setItem("sprintnova_session", JSON.stringify(nextSession));
    setSession(nextSession);
    return nextSession;
  }, []);

  const completePasswordChange = useCallback(() => {
    setSession((prev) => {
      const next = { ...prev, mustChangePassword: false };
      localStorage.setItem("sprintnova_session", JSON.stringify(next));
      return next;
    });
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    localStorage.removeItem("sprintnova_session");
    setSession(null);
  }, []);

  const value = useMemo(
    () => ({ session, login, logout, completePasswordChange, isAuthenticated: !!session }),
    [session, login, logout, completePasswordChange]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
