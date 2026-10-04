import { useState, useEffect } from "react";
import { dailyWorkUpdatesApi } from "../api/daily-work-updates";
import { projectsApi } from "../api/projects";

export function DailyUpdateForm({ onSuccess, existingUpdate }) {
  const [formData, setFormData] = useState({
    project_id: existingUpdate?.project_id || "",
    work_done: existingUpdate?.work_done || "",
    completed_work: existingUpdate?.completed_work || "",
    pending_work: existingUpdate?.pending_work || "",
    blockers: existingUpdate?.blockers || "",
    additional_notes: existingUpdate?.additional_notes || "",
    progress_percentage: existingUpdate?.progress_percentage || 50,
  });

  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  useEffect(() => { projectsApi.list().then(setProjects).catch(() => {}); }, []);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "progress_percentage" ? parseInt(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setIsLoading(true);

    try {
      // Filter out empty project_id
      const submitData = { ...formData };
      if (!submitData.project_id) {
        delete submitData.project_id;
      }

      if (existingUpdate?.id) {
        await dailyWorkUpdatesApi.update(existingUpdate.id, submitData);
      } else {
        await dailyWorkUpdatesApi.create(submitData);
      }

      setSuccess(true);
      setFormData({
        project_id: "",
        work_done: "",
        completed_work: "",
        pending_work: "",
        blockers: "",
        additional_notes: "",
        progress_percentage: 50,
      });

      onSuccess?.();

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.message || "Failed to save daily work update");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        {existingUpdate ? "Update Today's Work" : "Submit Today's Work Update"}
      </h2>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded text-green-800 text-sm">
          Daily work update saved successfully!
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-1">Project</label>
          <select name="project_id" value={formData.project_id} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
            <option value="">Select a project (optional)</option>
            {projects.map((p) => <option key={p.id} value={p.id}>{p.code} — {p.name}</option>)}
          </select>
        </div>

        {/* What did you work on today */}
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-1">
            What did you work on today?
          </label>
          <textarea
            name="work_done"
            value={formData.work_done}
            onChange={handleChange}
            placeholder="Describe the work you performed today..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        {/* What did you complete */}
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-1">
            What did you complete?
          </label>
          <textarea
            name="completed_work"
            value={formData.completed_work}
            onChange={handleChange}
            placeholder="List tasks, features, or items you finished..."
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* What is pending */}
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-1">
            What is still pending?
          </label>
          <textarea
            name="pending_work"
            value={formData.pending_work}
            onChange={handleChange}
            placeholder="List work that still needs to be done..."
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Blockers */}
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-1">
            Any blockers?
          </label>
          <textarea
            name="blockers"
            value={formData.blockers}
            onChange={handleChange}
            placeholder="Describe any obstacles, dependencies, or issues blocking your work..."
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Progress Percentage */}
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-2">
            Progress: <span className="text-blue-600 font-bold">{formData.progress_percentage}%</span>
          </label>
          <input
            type="range"
            name="progress_percentage"
            min="0"
            max="100"
            value={formData.progress_percentage}
            onChange={handleChange}
            className="w-full"
          />
        </div>

        {/* Additional Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-900 mb-1">
            Additional notes (optional)
          </label>
          <textarea
            name="additional_notes"
            value={formData.additional_notes}
            onChange={handleChange}
            placeholder="Any other information or concerns..."
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Submit Button */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
          >
            {isLoading ? (existingUpdate ? "Updating..." : "Submitting...") : existingUpdate ? "Update" : "Submit"}
          </button>
        </div>
      </form>
    </div>
  );
}
