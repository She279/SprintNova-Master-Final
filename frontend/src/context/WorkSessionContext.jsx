import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { workSessionApi } from "../api/work-sessions";
import { weeklyAvailabilityApi } from "../api/weekly-availability";
import { useAuth } from "./AuthContext";

const WorkSessionContext = createContext(null);

export function WorkSessionProvider({ children }) {
  const [workSession, setWorkSession] = useState(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const { session } = useAuth();

  // Recover/start a backend session whenever authentication becomes available.
  useEffect(() => {
    const initWorkSession = async () => {
      if (!session || session.role === "client" || session.role === "owner_admin") return;
      try {
        const current = await workSessionApi.getCurrent();
        if (current) {
          setWorkSession(current);
          setElapsedSeconds(Math.max(0, Math.floor((Date.now() - new Date(current.started_at).getTime()) / 1000)));
        } else {
          const today = await weeklyAvailabilityApi.getToday();
          if (today.is_working_day) {
            const started = await workSessionApi.start();
            setWorkSession(started);
            setElapsedSeconds(Math.max(0, Math.floor((Date.now() - new Date(started.started_at).getTime()) / 1000)));
          }
        }
      } catch (error) {
        console.error("Failed to load work session:", error);
      }
    };

    initWorkSession();
  }, [session]);

  // Auto-increment timer every second
  useEffect(() => {
    if (!workSession) return;

    const interval = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [workSession]);

  const startSession = useCallback(async () => {
    setIsLoading(true);
    try {
      const session = await workSessionApi.start();
      setWorkSession(session);
      setElapsedSeconds(0);
      return session;
    } catch (error) {
      console.error("Failed to start work session:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const stopSession = useCallback(async () => {
    if (!workSession) return;
    setIsLoading(true);
    try {
      const stoppedSession = await workSessionApi.stop(workSession.id);
      setWorkSession(null);
      setElapsedSeconds(0);
      return stoppedSession;
    } catch (error) {
      console.error("Failed to stop work session:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [workSession]);

  const value = {
    workSession,
    elapsedSeconds,
    isLoading,
    startSession,
    stopSession,
    isActive: !!workSession,
  };

  return (
    <WorkSessionContext.Provider value={value}>
      {children}
    </WorkSessionContext.Provider>
  );
}

export function useWorkSession() {
  const ctx = useContext(WorkSessionContext);
  if (!ctx)
    throw new Error("useWorkSession must be used within WorkSessionProvider");
  return ctx;
}
