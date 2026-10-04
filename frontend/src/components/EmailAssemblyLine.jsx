import { useEffect, useRef, useState } from "react";

/**
 * The signature moment of the employee-creation flow: as soon as the admin
 * has typed a first + last name, this "assembles" the generated company
 * email character by character, like a small build step completing --
 * making the product's core mechanic (auto company-email generation)
 * visible and satisfying rather than an invisible backend detail.
 */
export function EmailAssemblyLine({ email, status }) {
  const [displayed, setDisplayed] = useState("");
  const prevEmail = useRef("");

  useEffect(() => {
    if (!email) {
      setDisplayed("");
      prevEmail.current = "";
      return;
    }
    if (email === prevEmail.current) return;
    prevEmail.current = email;

    setDisplayed("");
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setDisplayed(email.slice(0, i));
      if (i >= email.length) clearInterval(id);
    }, 18);
    return () => clearInterval(id);
  }, [email]);

  return (
    <div className="rounded-md border border-line bg-ink px-4 py-3.5 font-mono text-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] uppercase tracking-wider text-white/40">SprintNova login email</span>
        <StatusDot status={status} />
      </div>
      <div className="text-accent min-h-[1.25rem]">
        {displayed || <span className="text-white/25">waiting for name…</span>}
        {status === "generating" && <span className="animate-pulse">▍</span>}
      </div>
    </div>
  );
}

function StatusDot({ status }) {
  if (status === "generating") {
    return <span className="flex items-center gap-1.5 text-[11px] text-warning"><Dot className="bg-warning animate-pulse" /> generating</span>;
  }
  if (status === "ready") {
    return <span className="flex items-center gap-1.5 text-[11px] text-success"><Dot className="bg-success" /> ready</span>;
  }
  return <span className="flex items-center gap-1.5 text-[11px] text-white/30"><Dot className="bg-white/30" /> idle</span>;
}

function Dot({ className }) {
  return <span className={`h-1.5 w-1.5 rounded-full ${className}`} />;
}
