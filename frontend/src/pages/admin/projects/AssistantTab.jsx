import { useRef, useState } from "react";
import { assistantApi } from "../../../api/assistant";
import { Input } from "../../../components/ui/Field";
import { Button } from "../../../components/ui/Button";
import { Alert } from "../../../components/ui/Feedback";

const SUGGESTIONS = [
  "Which tasks are overdue?",
  "Which bugs are critical?",
  "What is the current sprint status?",
  "Is the project at risk of delay?",
  "What should we prioritize next?",
  "Who is available today?",
];

export default function AssistantTab({ projectId }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const [asking, setAsking] = useState(false);
  const bottomRef = useRef(null);

  async function ask(q) {
    const text = (q ?? question).trim();
    if (!text) return;
    setError("");
    setQuestion("");
    setMessages((m) => [...m, { role: "user", text }]);
    setAsking(true);
    try {
      const res = await assistantApi.ask(projectId, text);
      setMessages((m) => [...m, { role: "assistant", ...res }]);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (err) {
      setError(err.message || "Could not reach the assistant.");
    } finally {
      setAsking(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    ask();
  }

  return (
    <div className="max-w-2xl">
      <p className="text-xs text-muted mb-4">
        Answers use this project's real data (tasks, bugs, sprints) and any documents you've added — never
        invented information.
      </p>

      {messages.length === 0 && (
        <div className="flex flex-wrap gap-2 mb-5">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => ask(s)}
              className="text-xs px-3 py-1.5 rounded-full border border-line text-ink/70 hover:border-accent hover:text-accent transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="space-y-3 mb-4 max-h-[420px] overflow-y-auto">
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="bg-accent text-white text-sm rounded-lg rounded-br-sm px-3.5 py-2 max-w-[80%]">
                {m.text}
              </div>
            </div>
          ) : (
            <div key={i} className="flex justify-start">
              <div className="bg-white border border-line text-sm rounded-lg rounded-bl-sm px-3.5 py-2.5 max-w-[85%]">
                <p className="text-ink/90">{m.answer}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-[10px] uppercase tracking-wider text-muted">
                    {m.ai_generated ? "Gemini" : "Rule-based"} · {m.retrieval_method === "vector" ? "vector search" : m.retrieval_method === "keyword" ? "keyword search" : "no documents matched"}
                  </span>
                </div>
                {m.sources?.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-line/70 space-y-1">
                    {m.sources.map((s) => (
                      <p key={s.id} className="text-[11px] text-muted">
                        📄 <span className="font-medium">{s.title}</span>
                      </p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )
        )}
        {asking && <p className="text-xs text-muted">Thinking…</p>}
        <div ref={bottomRef} />
      </div>

      {error && <div className="mb-3"><Alert>{error}</Alert></div>}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about this project…"
          className="flex-1"
        />
        <Button type="submit" disabled={asking}>Ask</Button>
      </form>
    </div>
  );
}
