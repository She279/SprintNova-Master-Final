import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useWorkSession } from "../../context/WorkSessionContext";
import { workSessionApi } from "../../api/work-sessions";
import { dailyWorkUpdatesApi } from "../../api/daily-work-updates";
import { DailyUpdateForm } from "../../components/DailyUpdateForm";
import { AnalysisDisplay } from "../../components/AnalysisDisplay";

export default function DeveloperDashboard() {
  const { session } = useAuth();
  const { elapsedSeconds, isActive, startSession, stopSession } = useWorkSession();
  const [todayTotal, setTodayTotal] = useState(null);
  const [todayUpdate, setTodayUpdate] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setError(null);
      const total = await workSessionApi.getTodayTotal();
      setTodayTotal(total);

      const update = await dailyWorkUpdatesApi.getTodayUpdate();
      setTodayUpdate(update);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    loadData();
  };

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg p-6">
        <h1 className="text-3xl font-bold">Good morning, {session?.fullName?.split(" ")[0]}!</h1>
        <p className="text-blue-100 mt-2">Track your work and stay focused on tasks</p>
      </div>

      {/* Work Session Card */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Work Session</h2>
        {isActive ? (
          <div className="text-center">
            <div className="text-6xl font-mono font-bold text-blue-600 mb-4">
              {formatTime(elapsedSeconds)}
            </div>
            <p className="text-gray-600 mb-4">Work session active</p>
            <button
              onClick={() => stopSession()}
              className="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700 font-medium"
            >
              Stop Session
            </button>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-gray-600 mb-4">No active work session</p>
            <button
              onClick={() => startSession()}
              className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-medium"
            >
              Start Work Session
            </button>
          </div>
        )}
      </div>

      {/* Today's Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Today's Work Time</p>
          <p className="text-2xl font-bold text-gray-900 mt-2">
            {todayTotal ? formatTime(todayTotal.total_minutes * 60) : "--:--:--"}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Session Status</p>
          <p className="text-2xl font-bold text-gray-900 mt-2">
            {isActive ? (
              <span className="text-green-600">Active</span>
            ) : (
              <span className="text-gray-600">Inactive</span>
            )}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Daily Progress</p>
          <p className="text-2xl font-bold text-gray-900 mt-2">
            {todayUpdate?.progress_percentage || 0}%
          </p>
        </div>
      </div>

      {/* Today's Work Update */}
      {!showForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Today's Work Summary</h2>
            {!todayUpdate && (
              <button
                onClick={() => setShowForm(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
              >
                Add Update
              </button>
            )}
          </div>

          {loading ? (
            <div className="text-gray-600">Loading...</div>
          ) : error ? (
            <div className="text-red-600">{error}</div>
          ) : todayUpdate ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-medium text-gray-900 mb-1">Work Done</h3>
                  <p className="text-gray-600 text-sm">{todayUpdate.work_done || "Not reported"}</p>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-1">Progress</h3>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${todayUpdate.progress_percentage}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      {todayUpdate.progress_percentage}%
                    </span>
                  </div>
                </div>
              </div>

              {todayUpdate.completed_work && (
                <div className="p-3 bg-green-50 border border-green-200 rounded">
                  <h3 className="font-medium text-green-900 text-sm">✓ Completed</h3>
                  <p className="text-green-800 text-sm mt-1">{todayUpdate.completed_work}</p>
                </div>
              )}

              {todayUpdate.pending_work && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <h3 className="font-medium text-yellow-900 text-sm">⏳ Pending</h3>
                  <p className="text-yellow-800 text-sm mt-1">{todayUpdate.pending_work}</p>
                </div>
              )}

              {todayUpdate.blockers && (
                <div className="p-3 bg-red-50 border border-red-200 rounded">
                  <h3 className="font-medium text-red-900 text-sm">⚠️ Blockers</h3>
                  <p className="text-red-800 text-sm mt-1">{todayUpdate.blockers}</p>
                </div>
              )}

              <button
                onClick={() => setShowForm(true)}
                className="mt-4 px-4 py-2 bg-gray-100 text-gray-900 rounded hover:bg-gray-200 text-sm font-medium"
              >
                Edit Update
              </button>
            </div>
          ) : (
            <div className="text-center p-6 bg-gray-50 rounded">
              <p className="text-gray-600 mb-4">No work update submitted yet</p>
              <button
                onClick={() => setShowForm(true)}
                className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium"
              >
                Submit Today's Update
              </button>
            </div>
          )}
        </div>
      )}

      {/* Daily Update Form */}
      {showForm && (
        <div>
          <DailyUpdateForm
            existingUpdate={todayUpdate}
            onSuccess={handleFormSuccess}
          />
          <button
            onClick={() => setShowForm(false)}
            className="mt-4 px-4 py-2 bg-gray-100 text-gray-900 rounded hover:bg-gray-200 text-sm font-medium"
          >
            Cancel
          </button>
        </div>
      )}

      {/* AI Analysis */}
      {todayUpdate?.analysis && (
        <AnalysisDisplay analysis={todayUpdate.analysis} />
      )}

      {/* Quick Navigation */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Navigation</h2>
        <div className="grid grid-cols-4 gap-3">
          <button className="px-4 py-3 border border-gray-300 rounded hover:bg-gray-50 text-sm font-medium text-gray-900">
            My Tasks
          </button>
          <button className="px-4 py-3 border border-gray-300 rounded hover:bg-gray-50 text-sm font-medium text-gray-900">
            Current Sprint
          </button>
          <button className="px-4 py-3 border border-gray-300 rounded hover:bg-gray-50 text-sm font-medium text-gray-900">
            Code Reviews
          </button>
          <button className="px-4 py-3 border border-gray-300 rounded hover:bg-gray-50 text-sm font-medium text-gray-900">
            Availability
          </button>
        </div>
      </div>
    </div>
  );
}
