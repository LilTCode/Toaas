import { useEffect, useRef, useState } from "react";
import api from "../services/api";
const prompts = ["Why is CSC 308 a priority?", "Explain my course load", "How can I prepare for CSC 405?"];
export default function StudentChatPage() {
  const [messages, setMessages] = useState([{ role:"assistant", text:"Hello! I can explain your recommendations, prerequisites, carryover courses, and registration plan." }]);
  const [draft, setDraft] = useState(""); const [loading, setLoading] = useState(false); const conversationId = useRef(null); const end = useRef(null);
  useEffect(() => end.current?.scrollIntoView({behavior:"smooth"}), [messages, loading]);
  const send = async (text = draft) => {
    if (!text.trim() || loading) return;
    setMessages(m => [...m, {role:"student", text:text.trim()}]); setDraft(""); setLoading(true);
    try {
      if (!conversationId.current) {
        const r = await api.post("chatbot/conversations/create/");
        if (!r?.data?.id) throw new Error("No conversation id returned");
        conversationId.current = r.data.id;
      }
      const r = await api.post(`chatbot/conversations/${conversationId.current}/messages/`, { content: text.trim() });
      setMessages(m => [...m, {role:"assistant", text: r?.data?.response || "I could not generate a response."}]);
    } catch (err) {
      // A failed create leaves a stale id behind, which makes every later send
      // 404 against a conversation that does not exist.
      if (!conversationId.current) conversationId.current = null;
      const status = err?.response?.status;
      setMessages(m => [...m, {role:"assistant", text:
        status === 401 ? "Your session expired. Please sign in again."
        : "Chatbot temporarily unavailable. Please try again in a moment."}]);
    }
    finally { setLoading(false); }
  };
  return (
    <div className="flex min-h-[calc(100vh-140px)] flex-col overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
      {/* Header */}
      <div className="flex items-center justify-between border-b-[3px] border-black bg-black px-6 py-5 text-white">
        <div>
          <p className="text-sm font-black uppercase tracking-wider text-[#facc15]">AI Academic Assistant</p>
          <p className="mt-1 text-xs font-bold text-gray-300"><span className="mr-2 inline-block h-2 w-2 rounded-full bg-emerald-400" />Online · Academic planning mode</p>
        </div>
        <button className="rounded-xl border-[2px] border-white bg-black px-4 py-2 text-xs font-black text-white shadow-[2px_2px_0_0_#fff] active:shadow-none transition-all" onClick={() => { setMessages([{role:"assistant", text:"New conversation started. What would you like to discuss?"}]); conversationId.current = null; }}>New chat</button>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-5 overflow-y-auto bg-[#f3f1e8] px-6 py-7 sm:px-10">
        {messages.map((message, i) => (
          <div key={i} className={`flex ${message.role === "student" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[82%] rounded-2xl border-[2px] border-black px-5 py-3 text-sm font-bold shadow-[4px_4px_0_0_#000] ${message.role === "student" ? "bg-[#ca8a04] text-black" : "bg-white text-black"}`}>
              {message.text}
            </div>
          </div>
        ))}
        {loading && <div className="w-fit rounded-2xl border-[2px] border-black bg-white px-5 py-3 text-sm font-bold text-gray-500 shadow-[3px_3px_0_0_#000]">Thinking…</div>}
        <div ref={end} />
      </div>

      {/* Input */}
      <div className="border-t-[3px] border-black bg-white p-5">
        <div className="mb-3 flex gap-2 overflow-x-auto">
          {prompts.map(p => <button key={p} onClick={() => send(p)} className="shrink-0 rounded-xl border-[2px] border-black bg-white px-3 py-1.5 text-xs font-bold text-black shadow-[2px_2px_0_0_#000] active:shadow-none hover:bg-[#fef9c3] transition-all">{p}</button>)}
        </div>
        <form className="flex gap-3" onSubmit={e => { e.preventDefault(); send(); }}>
          <input value={draft} onChange={e => setDraft(e.target.value)} placeholder="Ask about your academic plan…" className="min-w-0 flex-1 rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" />
          <button className="rounded-xl border-[2px] border-black bg-black px-5 py-3 text-sm font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none transition-all disabled:opacity-50" disabled={loading}>Send</button>
        </form>
      </div>
    </div>
  );
}
