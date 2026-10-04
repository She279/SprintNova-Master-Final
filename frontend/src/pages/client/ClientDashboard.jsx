import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { dashboardApi } from "../../api/dashboard";

export default function ClientDashboard() {
  const { session } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { dashboardApi.me().then(setData).catch(e => setError(e.message || "Unable to load dashboard")); }, []);
  if (error) return <div className="p-6 text-red-700">{error}</div>;
  if (!data) return <div className="p-6 text-gray-500">Loading project status…</div>;
  const projects = data.projects || [];
  const avg = projects.length ? Math.round(projects.reduce((a,p)=>a+(p.percent_complete||0),0)/projects.length) : 0;
  const active = projects.filter(p => p.status === "active").length;
  const milestones = projects.reduce((a,p)=>a+(p.milestones||[]).filter(m=>m.status!=="completed").length,0);
  return <div className="space-y-6">
    <div className="bg-gradient-to-r from-cyan-600 to-cyan-700 text-white rounded-lg p-6"><h1 className="text-3xl font-bold">Project Status Dashboard</h1><p className="text-cyan-100 mt-2">Welcome, {session?.fullName}. Client-visible project information only.</p></div>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[["Your Projects",projects.length],["Active",active],["Open Milestones",milestones],["Average Progress",`${avg}%`]].map(([l,v])=><div key={l} className="bg-white rounded-lg border p-4"><p className="text-gray-600 text-sm">{l}</p><p className="text-2xl font-bold text-cyan-700 mt-2">{v}</p></div>)}</div>
    <div className="space-y-4">{projects.length === 0 ? <div className="bg-white rounded-lg border p-8 text-center text-gray-500">No client-visible projects are assigned to your account.</div> : projects.map(p=><div key={p.id} className="bg-white rounded-lg border p-5"><div className="flex justify-between"><div><h2 className="font-semibold">{p.name}</h2><p className="text-xs text-gray-500 font-mono">{p.code}</p></div><span className="text-sm capitalize">{p.status.replace('_',' ')}</span></div><div className="mt-4"><div className="flex justify-between text-sm mb-1"><span>Progress</span><span>{p.percent_complete}%</span></div><div className="h-2 bg-gray-200 rounded"><div className="h-2 bg-cyan-600 rounded" style={{width:`${p.percent_complete}%`}}/></div></div><div className="mt-4"><h3 className="text-sm font-medium">Milestones</h3>{(p.milestones||[]).map(m=><div key={m.title} className="flex justify-between text-sm py-2 border-b last:border-0"><span>{m.title}</span><span className="capitalize text-gray-500">{m.status.replace('_',' ')}</span></div>)}</div></div>)}</div>
  </div>;
}
