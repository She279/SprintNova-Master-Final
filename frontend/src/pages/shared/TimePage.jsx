
import { useEffect, useState } from "react";
import { workSessionApi } from "../../api/work-sessions";
import { useWorkSession } from "../../context/WorkSessionContext";

export default function TimePage() {
  const {
    workSession,
    elapsedSeconds,
    startSession,
    stopSession,
  } = useWorkSession();

  const [total, setTotal] = useState(null);

  useEffect(() => {
    workSessionApi
      .getTodayTotal()
      .then(setTotal)
      .catch(() => {});
  }, [workSession]);

  const h = Math.floor(elapsedSeconds / 3600);
  const m = Math.floor((elapsedSeconds % 3600) / 60);
  const s = elapsedSeconds % 60;

  return (
    <div className="space-y-5">
      <h1 className="font-display text-2xl font-semibold">
        Work Time
      </h1>

      <div className="bg-white border rounded-lg p-8 text-center">
        <div className="text-5xl font-mono">
          {String(h).padStart(2, "0")}:
          {String(m).padStart(2, "0")}:
          {String(s).padStart(2, "0")}
        </div>

        <p className="text-sm text-muted mt-2">
          Backend-backed active session
        </p>

        <div className="mt-5">
          {workSession ? (
            <button
              onClick={stopSession}
              className="px-5 py-2 rounded bg-red-600 text-white"
            >
              Stop Session
            </button>
          ) : (
            <button
              onClick={startSession}
              className="px-5 py-2 rounded bg-accent text-white"
            >
              Start Session
            </button>
          )}
        </div>

        <p className="text-sm mt-4">
          Today total: {total?.formatted || "00:00"}
        </p>
      </div>
    </div>
  );
}