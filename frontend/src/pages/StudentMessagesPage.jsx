import { useEffect, useRef, useState } from "react";
import api from "../services/api";
import usePolling from "../hooks/usePolling";

export default function StudentMessagesPage() {
  const [messages, setMessages] = useState([]);
  const [selected, setSelected] = useState(null);
  const [replies, setReplies] = useState([]);
  const [draft, setDraft] = useState("");
  const [subject, setSubject] = useState("");
  const [recipient, setRecipient] = useState("advisor");
  const [sending, setSending] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [replying, setReplying] = useState(false);
  const endRef = useRef(null);

  const load = async () => {
    try {
      const r = await api.get("advisories/messages/");
      setMessages(r.data);
      return r.data;
    } catch { return null; }
  };

  useEffect(() => { load(); }, []);

  // Pull new advisor replies into the open thread without a manual refresh.
  usePolling(async () => {
    const fresh = await load();
    if (!fresh || !selected) return;
    const thread = fresh.find((m) => m.id === selected.id);
    if (!thread) return;
    setSelected(thread);
    setReplies((prev) =>
      (thread.replies?.length ?? 0) === prev.length ? prev : thread.replies || []
    );
  }, 5000);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [replies, selected]);

  const selectMessage = async (msg) => {
    setSelected(msg);
    setReplyText("");
    // Load replies from the API response
    setReplies(msg.replies || []);
  };

  const sendNew = async (e) => {
    e.preventDefault();
    if (!draft.trim() || !subject.trim()) return;
    setSending(true);
    try {
      const r = await api.post("advisories/messages/", { recipient_type: recipient, subject, body: draft });
      // The server may have appended to an existing thread rather than created
      // one, so replace a matching entry instead of prepending a duplicate.
      setMessages((prev) => {
        const rest = prev.filter((m) => m.id !== r.data.id);
        return [r.data, ...rest];
      });
      setDraft("");
      setSubject("");
      // Open the conversation so the student can see their message land.
      setSelected(r.data);
      setReplies(r.data.replies || []);
    } finally { setSending(false); }
  };

  const sendReply = async () => {
    if (!replyText.trim() || !selected) return;
    setReplying(true);
    try {
      const r = await api.post(`advisories/messages/${selected.id}/reply/`, { content: replyText });
      setReplies((prev) => [...prev, r.data]);
      setReplyText("");
      // Refresh message list to update reply_count
      const updated = await api.get("advisories/messages/");
      setMessages(updated.data);
    } finally { setReplying(false); }
  };

  return (
    <div className="flex min-h-[calc(100vh-140px)] flex-col overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000] lg:flex-row">
      {/* LEFT sidebar */}
      <aside className="border-b-[3px] border-black lg:w-80 lg:border-b-0 lg:border-r-[3px]">
        <div className="border-b-[3px] border-black bg-[#fef9c3] p-5">
          <h1 className="text-lg font-black text-black">Messages</h1>
          <p className="mt-1 text-xs font-bold text-gray-600">Advisor & academic office</p>
        </div>
        <div className="max-h-[500px] overflow-y-auto">
          {messages.length === 0 ? (
            <p className="p-5 text-sm font-bold text-gray-400">No messages yet.</p>
          ) : (
            messages.map((m) => (
              <button key={m.id} onClick={() => selectMessage(m)}
                className={`w-full border-b-[2px] border-black p-4 text-left transition-all ${selected?.id === m.id ? "bg-[#fef9c3]" : "bg-white hover:bg-gray-50"}`}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-black text-black capitalize">{m.recipient_type}</p>
                  <div className="flex items-center gap-2">
                    {m.reply_count > 0 && (
                      <span className="rounded-full border-[2px] border-black bg-[#ca8a04] px-2 py-0.5 text-[10px] font-black text-black">{m.reply_count}</span>
                    )}
                    <span className="text-[10px] font-bold text-gray-500">{new Date(m.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <p className="mt-1 text-sm font-bold text-black truncate">{m.subject}</p>
                <p className="mt-0.5 text-xs text-gray-500 truncate">{m.body}</p>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* RIGHT: chat area */}
      <section className="flex min-h-[520px] flex-1 flex-col">
        {selected ? (
          <>
            {/* Thread header */}
            <header className="border-b-[3px] border-black bg-black p-5 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-black uppercase tracking-wider text-[#facc15]">
                    To: {selected.recipient_type === "advisor" ? "Academic Advisor" : "Academic Office"}
                  </p>
                  <h2 className="mt-1 text-lg font-black">{selected.subject}</h2>
                </div>
                <span className="rounded-xl border-[2px] border-white px-3 py-1 text-xs font-black">{new Date(selected.created_at).toLocaleDateString()}</span>
              </div>
            </header>

            {/* Messages */}
            <div className="flex-1 space-y-4 overflow-y-auto bg-[#f3f1e8] p-6">
              {/* Opening message — absent on threads an advisor started */}
              {selected.body && (
                <div className="flex justify-end">
                  <div className="max-w-[75%] rounded-2xl border-[2px] border-black bg-[#ca8a04] px-5 py-3 text-sm font-bold text-black shadow-[4px_4px_0_0_#000]">
                    <p className="text-[10px] font-black uppercase tracking-wider text-black/60">You</p>
                    <p className="mt-1">{selected.body}</p>
                  </div>
                </div>
              )}

              {/* Threaded replies — `reply` is a denormalised copy of the last
                  staff reply and is intentionally not rendered here. */}
              {replies.map((r) => (
                <div key={r.id} className={`flex ${r.sender_type === "student" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[75%] rounded-2xl border-[2px] border-black px-5 py-3 text-sm font-bold shadow-[4px_4px_0_0_#000] ${r.sender_type === "student" ? "bg-[#ca8a04] text-black" : "bg-white text-black"}`}>
                    <p className="text-[10px] font-black uppercase tracking-wider text-gray-500">
                      {r.sender_type === "student" ? "You" : r.sender_name || (selected.recipient_type === "advisor" ? "Advisor" : "Admin")}
                    </p>
                    <p className="mt-1">{r.content}</p>
                  </div>
                </div>
              ))}
              <div ref={endRef} />
            </div>

            {/* Reply input */}
            <div className="border-t-[3px] border-black bg-white p-4">
              <div className="flex gap-3">
                <input
                  value={replyText} onChange={(e) => setReplyText(e.target.value)}
                  placeholder="Type your reply…"
                  className="min-w-0 flex-1 rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]"
                />
                <button onClick={sendReply} disabled={replying || !replyText.trim()}
                  className="rounded-xl border-[2px] border-black bg-black px-5 py-3 text-sm font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none transition-all disabled:opacity-50">
                  {replying ? "…" : "Send"}
                </button>
              </div>
            </div>
          </>
        ) : (
          <>
            {/* New message form */}
            <header className="border-b-[3px] border-black bg-[#fef9c3] p-5">
              <h2 className="text-lg font-black text-black">Send a message</h2>
              <p className="mt-1 text-xs font-bold text-gray-600">Select a thread or start a new conversation.</p>
            </header>
            <form onSubmit={sendNew} className="flex flex-1 flex-col justify-between p-6">
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="text-xs font-black uppercase text-black">To</label>
                    <select value={recipient} onChange={(e) => setRecipient(e.target.value)}
                      className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
                      <option value="advisor">Academic Advisor</option>
                      <option value="administrator">Academic Office / Complaint</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-black uppercase text-black">Subject</label>
                    <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="e.g. Registration plan review"
                      className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" required />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-black uppercase text-black">Message</label>
                  <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={4} placeholder="Write your message here…"
                    className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" required />
                </div>
              </div>
              <button type="submit" disabled={sending}
                className="mt-6 w-fit rounded-2xl border-[3px] border-black bg-[#ca8a04] px-8 py-3 text-sm font-black text-black shadow-[5px_5px_0_0_#000] active:shadow-none active:translate-x-[5px] active:translate-y-[5px] transition-all hover:bg-[#eab308] disabled:opacity-50">
                {sending ? "Sending…" : "Send Message"}
              </button>
            </form>
          </>
        )}
      </section>
    </div>
  );
}
