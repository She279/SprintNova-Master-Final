import { useEffect, useRef, useState } from "react";
import { notificationsApi } from "../api/notifications";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const ref = useRef(null);

  async function load() {
    try {
      setNotifications(await notificationsApi.list());
    } catch {
      /* silent -- notification bell shouldn't break the rest of the UI */
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    const onRealtime = (event) => {
      if (event.detail?.type === "notification.created") load();
    };
    window.addEventListener("sprintnova:realtime", onRealtime);
    return () => {
      clearInterval(interval);
      window.removeEventListener("sprintnova:realtime", onRealtime);
    };
  }, []);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  async function handleMarkRead(id) {
    await notificationsApi.markRead(id);
    load();
  }

  async function handleMarkAllRead() {
    await notificationsApi.markAllRead();
    load();
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative h-9 w-9 flex items-center justify-center rounded-md hover:bg-black/[0.04] transition-colors"
        aria-label="Notifications"
      >
        <BellIcon />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-danger" />
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-lg border border-line bg-white shadow-lg z-20 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-line">
            <span className="text-sm font-medium">Notifications</span>
            {unreadCount > 0 && (
              <button onClick={handleMarkAllRead} className="text-xs text-accent hover:underline">
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 && (
              <p className="text-sm text-muted text-center py-8">You're all caught up.</p>
            )}
            {notifications.map((n) => (
              <button
                key={n.id}
                onClick={() => !n.is_read && handleMarkRead(n.id)}
                className={`w-full text-left px-4 py-3 border-b border-line last:border-0 hover:bg-black/[0.02] transition-colors ${
                  !n.is_read ? "bg-accent-soft/40" : ""
                }`}
              >
                <p className="text-sm font-medium leading-snug">{n.title}</p>
                {n.body && <p className="text-xs text-muted mt-0.5 leading-snug">{n.body}</p>}
                <p className="text-[11px] text-muted/70 mt-1 font-mono">
                  {new Date(n.created_at).toLocaleString()}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function BellIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}
