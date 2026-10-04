import { useEffect, useState } from "react";
import { attachmentsApi } from "../../../api/attachments";
import { Button } from "../../../components/ui/Button";
import { Alert } from "../../../components/ui/Feedback";

export default function AttachmentsTab({ projectId }) {
  const [items, setItems] = useState([]); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function load(){ try{setItems(await attachmentsApi.list(projectId));}catch(e){setError(e.message);} }
  useEffect(()=>{load();},[projectId]);
  async function upload(e){ const file=e.target.files?.[0]; if(!file)return; setBusy(true); setError(""); try{await attachmentsApi.upload(projectId,file); await load();}catch(err){setError(err.message);}finally{setBusy(false); e.target.value="";} }
  async function download(item){ try{const url=await attachmentsApi.download(projectId,item.id); const a=document.createElement("a"); a.href=url; a.download=item.original_name; a.click(); URL.revokeObjectURL(url);}catch(e){setError(e.message);} }
  async function remove(id){ try{await attachmentsApi.remove(projectId,id); await load();}catch(e){setError(e.message);} }
  return <div className="space-y-4">
    <div className="rounded-lg border border-line bg-white p-4 flex items-center justify-between">
      <div><h3 className="font-display font-semibold text-sm">Project files</h3><p className="text-xs text-muted mt-1">Authenticated project attachments up to 10 MB.</p></div>
      <label className="cursor-pointer"><span className="inline-flex items-center rounded-md bg-ink px-3 py-2 text-xs text-white">{busy?"Uploading…":"Upload file"}</span><input type="file" className="hidden" onChange={upload} disabled={busy}/></label>
    </div>
    {error && <Alert>{error}</Alert>}
    {items.length===0 ? <p className="text-sm text-muted">No project files yet.</p> : <div className="divide-y divide-line rounded-lg border border-line bg-white">{items.map(i=><div key={i.id} className="p-4 flex items-center justify-between gap-4"><div><p className="text-sm font-medium">{i.original_name}</p><p className="text-xs text-muted">{Math.ceil(i.size_bytes/1024)} KB · {i.content_type||"file"}</p></div><div className="flex gap-2"><Button onClick={()=>download(i)}>Download</Button><Button onClick={()=>remove(i.id)}>Delete</Button></div></div>)}</div>}
  </div>;
}
