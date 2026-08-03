import { useEffect, useState } from "react";
import api from "../services/api";

const starterPrompts = [
  "Explain my recommended courses",
  "Help me plan my next semester",
  "What prerequisites should I review?",
];

export default function AssistantPopup() {
  const [open, setOpen] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);

  const ensureConversation = async () => {
    if (conversationId) return;
    setLoading(true);
    try {
      const response = await api.post("chatbot/conversations/create/");
      const createdMessages = response.data.messages?.length
        ? response.data.messages
        : [{ id: "welcome", sender_role: "system", content: "Hello! I can explain your recommendations and help you plan your next semester. Ask me anything." }];
      setConversationId(response.data.id);
      setMessages(createdMessages);
    } catch {
      setMessages([{ id: "error", sender_role: "system", content: "The chatbot is temporarily unavailable." }]);
    } finally { setLoading(false); }
  };

  useEffect(() => {
    const handleOpen = () => { setOpen(true); if (!conversationId) ensureConversation(); };
    window.addEventListener("assistant:open", handleOpen);
    return () => window.removeEventListener("assistant:open", handleOpen);
  }, [conversationId]);

  const handleSend = async (event) => {
    event.preventDefault();
    if (!draft.trim() || !conversationId) return;
    const studentMsg = { id: `s-${Date.now()}`, sender_role: "student", content: draft.trim() };
    setMessages((cur) => [...cur, studentMsg]);
    setDraft("");
    setLoading(true);
    try {
      const response = await api.post(`chatbot/conversations/${conversationId}/messages/`, { content: studentMsg.content });
      setMessages((cur) => [...cur, { id: `a-${Date.now()}`, sender_role: "system", content: response.data.response || "I could not generate a reply." }]);
    } catch {
      setMessages((cur) => [...cur, { id: `a-${Date.now()}`, sender_role: "system", content: "The chatbot could not answer that request." }]);
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 w-full max-w-md rounded-3xl border-[3px] border-black bg-white p-5 shadow-[8px_8px_0_0_#000]">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-wider text-[#ca8a04]">AI Assistant</p>
          <h3 className="text-lg font-black text-black">Academic advisor bot</h3>
        </div>
        <button onClick={() => { if (!open) { setOpen(true); if (!conversationId) ensureConversation(); } else setOpen(false); }}
          className="rounded-xl border-[2px] border-black bg-white px-3 py-2 text-xs font-black text-black shadow-[2px_2px_0_0_#000] active:shadow-none transition-all">
          {open ? "Hide" : "Open"}
        </button>
      </div>

      {open ? (
        <div className="mt-4 space-y-4">
          <div className="max-h-[320px] space-y-3 overflow-y-auto rounded-2xl border-[2px] border-black bg-[#f3f1e8] p-3">
            {messages.length ? (
              messages.map((message) => (
                <div key={message.id} className={`rounded-2xl border-[2px] border-black px-4 py-2.5 text-sm font-bold shadow-[3px_3px_0_0_#000] ${message.sender_role === "student" ? "ml-auto max-w-[85%] bg-[#ca8a04] text-black" : "mr-auto max-w-[85%] bg-white text-black"}`}>
                  {message.content}
                </div>
              ))
            ) : (
              <p className="text-sm font-bold text-gray-600">Your chat will appear here.</p>
            )}
            {loading && <p className="text-sm font-bold text-gray-500">Thinking…</p>}
          </div>

          <div className="flex flex-wrap gap-2">
            {starterPrompts.map((prompt) => (
              <button key={prompt} onClick={() => setDraft(prompt)}
                className="rounded-xl border-[2px] border-black bg-white px-3 py-1.5 text-xs font-bold text-black shadow-[2px_2px_0_0_#000] active:shadow-none hover:bg-[#fef9c3] transition-all">
                {prompt}
              </button>
            ))}
          </div>

          <form className="space-y-3" onSubmit={handleSend}>
            <input className="w-full rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" placeholder="Ask about your plan…" value={draft} onChange={(e) => setDraft(e.target.value)} />
            <button className="w-full rounded-2xl border-[2px] border-black bg-black py-3 text-sm font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none transition-all" type="submit">Send</button>
          </form>
        </div>
      ) : (
        <p className="mt-4 text-sm font-bold text-gray-500">The assistant is ready. Open it to ask about your course plan.</p>
      )}
    </div>
  );
}
