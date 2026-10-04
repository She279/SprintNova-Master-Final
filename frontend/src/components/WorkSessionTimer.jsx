import { useEffect, useState } from "react";
import { useWorkSession } from "../context/WorkSessionContext";

function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export function WorkSessionTimer() {
  const { workSession, elapsedSeconds, isLoading, startSession, stopSession, isActive } = useWorkSession();
  const [showConfirm, setShowConfirm] = useState(false);

  const handleStart = async () => {
    try {
      await startSession();
    } catch (error) {
      console.error("Failed to start session:", error);
    }
  };

  const handleStop = async () => {
    try {
      await stopSession();
      setShowConfirm(false);
    } catch (error) {
      console.error("Failed to stop session:", error);
    }
  };

  if (!workSession && !isActive) {
    return (
      <button
        onClick={handleStart}
        disabled={isLoading}
        className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
      >
        {isLoading ? "Starting..." : "Start Work"}
      </button>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center bg-blue-50 px-4 py-2 rounded-lg border border-blue-200">
        <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
        <span className="font-mono font-bold text-blue-900 text-sm">
          {formatTime(elapsedSeconds)}
        </span>
      </div>

      {showConfirm ? (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-700">Stop work session?</span>
          <button
            onClick={handleStop}
            disabled={isLoading}
            className="px-2 py-1 bg-red-600 text-white rounded text-xs font-medium hover:bg-red-700 disabled:opacity-50"
          >
            {isLoading ? "Stopping..." : "Yes"}
          </button>
          <button
            onClick={() => setShowConfirm(false)}
            className="px-2 py-1 bg-gray-300 text-gray-800 rounded text-xs font-medium hover:bg-gray-400"
          >
            No
          </button>
        </div>
      ) : (
        <button
          onClick={() => setShowConfirm(true)}
          className="px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm font-medium"
        >
          Stop
        </button>
      )}
    </div>
  );
}
