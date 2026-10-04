import { useState } from "react";
import { weeklyAvailabilityApi } from "../api/weekly-availability";

const DEFAULT_SCHEDULE = {
  monday: { start_time: "09:00", end_time: "17:30" },
  tuesday: { start_time: "09:00", end_time: "17:30" },
  wednesday: { start_time: "09:00", end_time: "17:30" },
  thursday: { start_time: "09:00", end_time: "17:30" },
  friday: { start_time: "09:00", end_time: "17:30" },
  saturday: { start_time: null, end_time: null },
  sunday: { start_time: null, end_time: null },
};

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

export function AvailabilitySetupModal({ isOpen, onClose, onSuccess }) {
  const [schedule, setSchedule] = useState(DEFAULT_SCHEDULE);
const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTimeChange = (day, field, value) => {
    setSchedule((prev) => ({
      ...prev,
      [day]: {
        ...prev[day],
        [field]: value,
      },
    }));
  };

  const handleToggleDay = (day) => {
    const current = schedule[day];
    if (current.start_time && current.end_time) {
      // Turn off
      handleTimeChange(day, "start_time", null);
      handleTimeChange(day, "end_time", null);
    } else {
      // Turn on with default times
      handleTimeChange(day, "start_time", "09:00");
      handleTimeChange(day, "end_time", "17:30");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await weeklyAvailabilityApi.setup({
        timezone,
        schedule,
      });
      onSuccess?.();
      onClose?.();
    } catch (err) {
      setError(err.message || "Failed to save availability");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Configure Your Working Hours</h2>
          <p className="text-gray-600 mt-2">
            Set your regular working schedule. This helps with workload planning and availability tracking.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
              {error}
            </div>
          )}

          {/* Timezone */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Timezone
            </label>
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm"
            >
              <option value="UTC">UTC</option>
              <option value="Asia/Kolkata">IST (India)</option>
              <option value="America/New_York">EST (US Eastern)</option>
              <option value="America/Chicago">CST (US Central)</option>
              <option value="America/Denver">MST (US Mountain)</option>
              <option value="America/Los_Angeles">PST (US Pacific)</option>
              <option value="Europe/London">GMT (UK)</option>
              <option value="Europe/Paris">CET (Europe)</option>
              <option value="Asia/Tokyo">JST (Japan)</option>
              <option value="Australia/Sydney">AEST (Australia)</option>
            </select>
          </div>

          {/* Weekly Schedule */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-4">
              Weekly Schedule
            </label>
            <div className="space-y-3">
              {DAYS.map((day) => {
                const daySchedule = schedule[day];
                const isWorking = daySchedule.start_time && daySchedule.end_time;

                return (
                  <div key={day} className="flex items-center gap-4 p-3 bg-gray-50 rounded">
                    <div className="w-24">
                      <button
                        type="button"
                        onClick={() => handleToggleDay(day)}
                        className={`w-full px-3 py-2 rounded text-sm font-medium capitalize transition-colors ${
                          isWorking
                            ? "bg-blue-600 text-white"
                            : "bg-gray-300 text-gray-700"
                        }`}
                      >
                        {day}
                      </button>
                    </div>

                    {isWorking ? (
                      <div className="flex items-center gap-2 flex-1">
                        <input
                          type="time"
                          value={daySchedule.start_time}
                          onChange={(e) => handleTimeChange(day, "start_time", e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
                        />
                        <span className="text-gray-600">to</span>
                        <input
                          type="time"
                          value={daySchedule.end_time}
                          onChange={(e) => handleTimeChange(day, "end_time", e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
                        />
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500 italic flex-1">Day off</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200 text-sm font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
            >
              {isLoading ? "Saving..." : "Save Schedule"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
