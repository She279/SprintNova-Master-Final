import { useEffect, useState } from "react";
import { dailyWorkUpdatesApi } from "../../api/daily-work-updates";
import { DailyUpdateForm } from "../../components/DailyUpdateForm";
import { AnalysisDisplay } from "../../components/AnalysisDisplay";

export default function DailyUpdatePage({ teamView = false }) {
  const [today, setToday] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [team, setTeam] = useState(null);
  const [error, setError] = useState("");
  const load = async () => {
    try {
      if (teamView) setTeam(await dailyWorkUpdatesApi.getTeamUpdates());
      else {
        const update = await dailyWorkUpdatesApi.getTodayUpdate();
        setToday(update);
        if (update?.id) setAnalysis(update.analysis || await dailyWorkUpdatesApi.getAnalysis(update.id));
      }
    } catch (e) { setError(e.message || "Unable to load daily updates"); }
  };
  useEffect(() => { load(); }, [teamView]);
  if (error) return <div className="text-red-700">{error}</div>;
  if (teamView) return <div className="space-y-5"><h1 className="font-display text-2xl font-semibold">Team Daily Updates</h1><div className="bg-white border border-line rounded-lg p-5"><p className="text-sm text-muted mb-4">{team?.submitted_count || 0} of {team?.total_team_members || 0} team members submitted today.</p><div className="space-y-2">{Object.entries(team?.team_updates || {}).map(([id,u])=><div key={id} className="p-3 rounded border"><div className="font-medium">Employee #{id}</div><div className="text-sm text-muted">{u ? u.work_done : "Update pending"}</div></div>)}</div></div></div>;
  return <div className="space-y-5"><div><h1 className="font-display text-2xl font-semibold">Daily Work Update</h1><p className="text-sm text-muted mt-1">Submit once per working day. Your update is analyzed against actual assigned work.</p></div><DailyUpdateForm existingUpdate={today} onSuccess={load}/>{analysis && <AnalysisDisplay analysis={analysis}/>}</div>;
}
