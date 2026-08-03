import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const COGNITIVE_DIMS = ["abstract_reasoning", "logical_reasoning", "theoretical_knowledge", "quantitative_calculation", "practical_application"];
const DIM_LABELS = { abstract_reasoning: "Abstract", logical_reasoning: "Logical", theoretical_knowledge: "Theoretical", quantitative_calculation: "Quantitative", practical_application: "Practical" };

export default function AdminDashboardPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState("courses");
  const [messages, setMessages] = useState([]);
  const [selected, setSelected] = useState(null);
  const [replies, setReplies] = useState([]);
  const [replyText, setReplyText] = useState("");
  const [replying, setReplying] = useState(false);
  const endRef = useRef(null);
  const [courses, setCourses] = useState([]);
  const [students, setStudents] = useState([]);
  const [editingCourse, setEditingCourse] = useState(null);
  const [showCourseForm, setShowCourseForm] = useState(false);
  const [courseForm, setCourseForm] = useState({ code: "", title: "", credit_units: 3, level: 100, semester: 1, department_classification: "Computer Science", description: "", major_topics: "", learning_objectives: "", abstract_reasoning: 20, logical_reasoning: 20, theoretical_knowledge: 20, quantitative_calculation: 20, practical_application: 20 });
  const [msg, setMsg] = useState("");
  const [classifying, setClassifying] = useState(false);
  const [showExcelUpload, setShowExcelUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const loadCourses = async () => { try { const r = await api.get("courses/course/"); setCourses(r.data); } catch { /* ignore */ } };
  const loadMessages = async () => { try { const r = await api.get("advisories/staff/messages/"); setMessages(r.data); } catch { /* ignore */ } };
  const loadStudents = async () => { try { const r = await api.get("advisories/students/"); setStudents(r.data); } catch { /* ignore */ } };

  useEffect(() => { loadCourses(); loadMessages(); loadStudents(); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [replies]);

  const selectMessage = (msg) => { setSelected(msg); setReplies(msg.replies || []); setReplyText(""); };
  const sendReply = async () => {
    if (!replyText.trim() || !selected) return; setReplying(true);
    try { const r = await api.post(`advisories/staff/messages/${selected.id}/reply/`, { content: replyText }); setReplies((prev) => [...prev, r.data]); setReplyText(""); const u = await api.get("advisories/staff/messages/"); setMessages(u.data); } finally { setReplying(false); }
  };

  const autoClassify = async () => {
    if (!courseForm.title.trim()) { setMsg("Enter a course title first."); return; }
    setClassifying(true);
    try {
      const r = await api.post("courses/course/auto_classify/", {
        title: courseForm.title, description: courseForm.description,
        major_topics: courseForm.major_topics, learning_objectives: courseForm.learning_objectives,
      });
      setCourseForm((prev) => ({ ...prev, ...r.data }));
      setMsg("Cognitive profile auto-classified.");
    } catch { setMsg("Auto-classify failed."); } finally { setClassifying(false); }
  };

  const submitCourse = async (e) => {
    e.preventDefault();
    const total = COGNITIVE_DIMS.reduce((s, d) => s + (parseInt(courseForm[d]) || 0), 0);
    if (total !== 100) { setMsg(`Cognitive percentages must total 100 (currently ${total}).`); return; }
    try {
      if (editingCourse) {
        await api.put(`courses/course/${editingCourse}/`, courseForm);
        setMsg("Course updated.");
      } else {
        await api.post("courses/course/", courseForm);
        setMsg("Course created.");
      }
      setShowCourseForm(false); setEditingCourse(null); setCourseForm({ code: "", title: "", credit_units: 3, level: 100, semester: 1, department_classification: "Computer Science", description: "", major_topics: "", learning_objectives: "", abstract_reasoning: 20, logical_reasoning: 20, theoretical_knowledge: 20, quantitative_calculation: 20, practical_application: 20 });
      loadCourses();
    } catch (err) { setMsg(err.response?.data?.detail || "Error saving course."); }
  };

  const editCourse = (c) => { setEditingCourse(c.id); setCourseForm({ code: c.code, title: c.title, credit_units: c.credit_units, level: c.level, semester: c.semester, department_classification: c.department_classification, description: c.description || "", major_topics: c.major_topics || "", learning_objectives: c.learning_objectives || "", abstract_reasoning: c.abstract_reasoning, logical_reasoning: c.logical_reasoning, theoretical_knowledge: c.theoretical_knowledge, quantitative_calculation: c.quantitative_calculation, practical_application: c.practical_application }); setShowCourseForm(true); };
  const deleteCourse = async (id) => { if (!confirm("Delete this course?")) return; await api.delete(`courses/course/${id}/`); loadCourses(); };

  const handleExcelUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true); setUploadResult(null);
    const fd = new FormData();
    fd.append("file", file);
    fd.append("default_programme", "Computer Science");
    try {
      const r = await api.post("courses/course/upload_excel/", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setUploadResult(r.data);
      loadCourses();
    } catch (err) { setUploadResult({ error: err.response?.data?.detail || "Upload failed." }); } finally { setUploading(false); e.target.value = ""; }
  };

  const signOut = () => { localStorage.clear(); navigate("/auth"); };

  return (
    <div className="min-h-screen bg-[#f3f1e8] p-4 lg:p-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-sm font-black uppercase tracking-wider text-[#ca8a04]">TO-AAS</p>
            <h1 className="text-3xl font-black tracking-tight text-black">Admin Portal</h1>
            <p className="text-sm font-bold text-gray-500">{courses.length} courses · {students.length} students · {messages.length} messages</p>
          </div>
          <button onClick={signOut} className="rounded-xl border-[2px] border-black bg-white px-4 py-2 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-red-50">Sign out</button>
        </div>

        {/* Stats */}
        <section className="mb-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]"><p className="text-xs font-black uppercase text-gray-500">Courses</p><p className="mt-2 text-3xl font-black text-black">{courses.length}</p></div>
          <div className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]"><p className="text-xs font-black uppercase text-gray-500">Students</p><p className="mt-2 text-3xl font-black text-black">{students.length}</p></div>
          <div className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]"><p className="text-xs font-black uppercase text-gray-500">Unread Messages</p><p className="mt-2 text-3xl font-black text-[#ca8a04]">{messages.filter(m => !m.read).length}</p></div>
        </section>

        {/* Tabs */}
        <div className="mb-6 flex gap-2">
          {["courses", "students", "messages"].map((t) => (
            <button key={t} onClick={() => { setTab(t); setSelected(null); }} className={`rounded-xl border-[2px] border-black px-5 py-2.5 text-sm font-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all ${tab === t ? "bg-black text-white" : "bg-white text-black hover:bg-gray-100"}`}>{t === "courses" ? "Course Management" : t === "students" ? "Students & Advisors" : "Support Messages"}</button>
          ))}
        </div>

        {msg && <div className="mb-4 rounded-2xl border-[2px] border-black bg-[#fef9c3] p-4 text-sm font-bold text-black shadow-[3px_3px_0_0_#000]">{msg}</div>}

        {/* Course Management */}
        {tab === "courses" && (
          <section className="overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
            <div className="flex items-center justify-between border-b-[3px] border-black bg-[#fef9c3] px-6 py-4">
              <h2 className="text-lg font-black text-black">All Courses ({courses.length})</h2>
              <div className="flex gap-2">
                <button onClick={() => setShowExcelUpload(!showExcelUpload)} className="rounded-xl border-[2px] border-black bg-white px-4 py-2 text-xs font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none hover:bg-gray-100">{showExcelUpload ? "Cancel" : "Upload Excel"}</button>
                <button onClick={() => { setShowCourseForm(!showCourseForm); setShowExcelUpload(false); setEditingCourse(null); setCourseForm({ code: "", title: "", credit_units: 3, level: 100, semester: 1, department_classification: "Computer Science", description: "", major_topics: "", learning_objectives: "", abstract_reasoning: 20, logical_reasoning: 20, theoretical_knowledge: 20, quantitative_calculation: 20, practical_application: 20 }); }} className="rounded-xl border-[2px] border-black bg-black px-4 py-2 text-xs font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none">{showCourseForm ? "Cancel" : "+ Add Course"}</button>
              </div>
            </div>

            {/* Excel Upload */}
            {showExcelUpload && (
              <div className="border-b-[3px] border-black p-6">
                <h3 className="text-sm font-black text-black mb-3">Upload Courses via Excel</h3>
                <p className="text-xs font-bold text-gray-500 mb-3">Required columns: code, title, credit_units, level, semester. Optional: description, major_topics, learning_objectives, department_classification. Cognitive profiles are auto-computed via greedy algorithm.</p>
                <label className="inline-block cursor-pointer rounded-xl border-[2px] border-black bg-white px-5 py-2.5 text-sm font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none hover:bg-gray-100">
                  {uploading ? "Uploading…" : "Choose Excel File"}
                  <input type="file" accept=".xlsx,.xls" onChange={handleExcelUpload} className="hidden" disabled={uploading} />
                </label>
                {uploadResult && (
                  <div className="mt-3 rounded-xl border-[2px] border-black p-4 text-sm font-bold bg-[#fef9c3]">
                    {uploadResult.error ? <p className="text-red-600">{uploadResult.error}</p> : (
                      <p>{uploadResult.created} courses created. {uploadResult.errors?.length > 0 && <span className="text-red-600">{uploadResult.errors.length} errors.</span>}</p>
                    )}
                    {uploadResult.errors?.length > 0 && (
                      <ul className="mt-2 text-xs text-red-600 list-disc pl-4">{uploadResult.errors.map((e, i) => <li key={i}>{e}</li>)}</ul>
                    )}
                  </div>
                )}
              </div>
            )}

            {showCourseForm && (
              <form onSubmit={submitCourse} className="border-b-[3px] border-black p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-black text-black">{editingCourse ? "Edit Course" : "Add Course"}</h3>
                  <button type="button" onClick={autoClassify} disabled={classifying} className="rounded-xl border-[2px] border-black bg-[#fef9c3] px-4 py-1.5 text-xs font-black text-black shadow-[2px_2px_0_0_#000] active:shadow-none disabled:opacity-50">{classifying ? "…" : "Auto-Classify Cognitive Profile"}</button>
                </div>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <div><label className="text-[10px] font-black uppercase text-black">Code</label><input value={courseForm.code} onChange={e => setCourseForm({...courseForm, code: e.target.value})} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none focus:bg-[#fef9c3]" required /></div>
                  <div><label className="text-[10px] font-black uppercase text-black">Title</label><input value={courseForm.title} onChange={e => setCourseForm({...courseForm, title: e.target.value})} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none focus:bg-[#fef9c3]" required /></div>
                  <div><label className="text-[10px] font-black uppercase text-black">Units</label><input type="number" value={courseForm.credit_units} onChange={e => setCourseForm({...courseForm, credit_units: parseInt(e.target.value)})} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none focus:bg-[#fef9c3]" /></div>
                  <div><label className="text-[10px] font-black uppercase text-black">Level</label><select value={courseForm.level} onChange={e => setCourseForm({...courseForm, level: parseInt(e.target.value)})} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none">{[100,200,300,400].map(l => <option key={l} value={l}>{l}L</option>)}</select></div>
                  <div><label className="text-[10px] font-black uppercase text-black">Semester</label><select value={courseForm.semester} onChange={e => setCourseForm({...courseForm, semester: parseInt(e.target.value)})} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none"><option value={1}>First</option><option value={2}>Second</option></select></div>
                  <div><label className="text-[10px] font-black uppercase text-black">Programme</label><select value={courseForm.department_classification} onChange={e => setCourseForm({...courseForm, department_classification: e.target.value})} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none"><option value="Computer Science">Computer Science</option><option value="Software Engineering">Software Engineering</option><option value="Cyber Security">Cyber Security</option><option value="General">General</option></select></div>
                  <div className="sm:col-span-2 lg:col-span-3"><label className="text-[10px] font-black uppercase text-black">Description</label><textarea value={courseForm.description} onChange={e => setCourseForm({...courseForm, description: e.target.value})} rows={2} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none focus:bg-[#fef9c3]" /></div>
                  <div className="sm:col-span-2 lg:col-span-3"><label className="text-[10px] font-black uppercase text-black">Major Topics</label><textarea value={courseForm.major_topics} onChange={e => setCourseForm({...courseForm, major_topics: e.target.value})} rows={2} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none focus:bg-[#fef9c3]" /></div>
                  <div className="sm:col-span-2 lg:col-span-3"><label className="text-[10px] font-black uppercase text-black">Learning Objectives</label><textarea value={courseForm.learning_objectives} onChange={e => setCourseForm({...courseForm, learning_objectives: e.target.value})} rows={2} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none focus:bg-[#fef9c3]" /></div>
                  {COGNITIVE_DIMS.map(d => (
                    <div key={d}><label className="text-[10px] font-black uppercase text-black">{DIM_LABELS[d]} (%)</label><input type="number" value={courseForm[d]} onChange={e => setCourseForm({...courseForm, [d]: parseInt(e.target.value) || 0})} className="mt-1 block w-full rounded-xl border-[2px] border-black px-3 py-2 text-sm font-bold shadow-[2px_2px_0_0_#000] outline-none focus:bg-[#fef9c3]" /></div>
                  ))}
                </div>
                <p className="mt-2 text-xs font-bold text-gray-500">Total cognitive: {COGNITIVE_DIMS.reduce((s, d) => s + (parseInt(courseForm[d]) || 0), 0)}% (must be 100)</p>
                <button type="submit" className="mt-4 rounded-xl border-[2px] border-black bg-[#ca8a04] px-6 py-2.5 text-sm font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none">{editingCourse ? "Update Course" : "Create Course"}</button>
              </form>
            )}

            <div className="divide-y-[2px] divide-black max-h-[500px] overflow-y-auto">
              {courses.map(c => (
                <div key={c.id} className="flex items-center justify-between px-6 py-3 hover:bg-gray-50">
                  <div className="flex items-center gap-4 min-w-0 flex-1">
                    <span className="rounded-xl border-[2px] border-black bg-[#fef9c3] px-3 py-1 text-xs font-black shrink-0">{c.code}</span>
                    <div className="min-w-0">
                      <p className="text-sm font-bold text-black truncate">{c.title}</p>
                      <p className="text-[10px] font-bold text-gray-500">{c.level}L · Sem {c.semester} · {c.credit_units} units · {c.department_classification}</p>
                    </div>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button onClick={() => editCourse(c)} className="rounded-lg border-[2px] border-black bg-white px-3 py-1 text-[10px] font-black shadow-[2px_2px_0_0_#000] active:shadow-none hover:bg-[#fef9c3]">Edit</button>
                    <button onClick={() => deleteCourse(c.id)} className="rounded-lg border-[2px] border-black bg-white px-3 py-1 text-[10px] font-black shadow-[2px_2px_0_0_#000] active:shadow-none hover:bg-red-50">Delete</button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Students */}
        {tab === "students" && (
          <section className="overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
            <div className="border-b-[3px] border-black bg-[#fef9c3] px-6 py-4">
              <h2 className="text-lg font-black text-black">All Students ({students.length})</h2>
            </div>
            <div className="divide-y-[2px] divide-black max-h-[500px] overflow-y-auto">
              {students.length === 0 ? <p className="p-5 text-sm font-bold text-gray-400">No students registered.</p> : students.map(s => (
                <div key={s.id} className="flex items-center gap-4 px-6 py-4">
                  <div className="grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-full border-[2px] border-black bg-[#fef9c3] text-sm font-black">{s.profile_photo ? <img src={s.profile_photo} alt="" className="h-full w-full object-cover" /> : (s.first_name?.[0]||"S")+(s.last_name?.[0]||"")}</div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-black text-black truncate">{s.full_name || s.email}</p>
                    <p className="text-xs font-bold text-gray-500 truncate">{s.username} · {s.programme_display?.replace("B.Sc. ", "") || "—"}</p>
                  </div>
                  <span className="shrink-0 text-xs font-bold text-gray-500">{s.current_level}L</span>
                  <span className="shrink-0 text-xs font-bold text-gray-500">CGPA: {s.cgpa.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Support Messages */}
        {tab === "messages" && (
          <div className="flex min-h-[500px] flex-col overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000] lg:flex-row">
              <aside className="border-b-[3px] border-black lg:w-80 lg:border-b-0 lg:border-r-[3px] lg:rounded-bl-3xl overflow-hidden">
              <div className="border-b-[3px] border-black bg-[#fef9c3] p-5">
                <h2 className="text-lg font-black text-black">Support Messages</h2>
                <p className="mt-1 text-xs font-bold text-gray-600">{messages.filter(m => !m.read).length} unread</p>
              </div>
              <div className="max-h-[500px] overflow-y-auto divide-y-[2px] divide-black">
                {messages.length === 0 ? <p className="p-5 text-sm font-bold text-gray-400">No messages.</p> : messages.map(m => (
                  <button key={m.id} onClick={() => selectMessage(m)} className={`w-full p-4 text-left transition-all ${selected?.id === m.id ? "bg-[#fef9c3]" : "bg-white hover:bg-gray-50"}`}>
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-black text-black truncate">{m.student_name}</p>
                      <div className="flex items-center gap-2">{!m.read && <span className="h-2 w-2 rounded-full bg-red-500" />}<span className="text-[10px] font-bold text-gray-400">{new Date(m.created_at).toLocaleDateString()}</span></div>
                    </div>
                    <p className="mt-0.5 text-xs font-bold text-gray-600 truncate">{m.subject}</p>
                    <p className="text-xs text-gray-400 truncate">{m.body}</p>
                  </button>
                ))}
              </div>
            </aside>
            <section className="flex flex-1 flex-col">
              {selected ? (
                <>
                  <header className="border-b-[3px] border-black bg-black p-5 text-white">
                    <p className="text-xs font-black uppercase tracking-wider text-[#facc15]">{selected.student_name} · {selected.student_email}</p>
                    <h2 className="mt-1 text-lg font-black">{selected.subject}</h2>
                  </header>
                  <div className="flex-1 space-y-4 overflow-y-auto bg-[#f3f1e8] p-6">
                    <div className="flex justify-end"><div className="max-w-[75%] rounded-2xl border-[2px] border-black bg-[#ca8a04] px-5 py-3 text-sm font-bold text-black shadow-[4px_4px_0_0_#000]"><p className="text-[10px] font-black uppercase tracking-wider text-black/60">{selected.student_name}</p><p className="mt-1">{selected.body}</p></div></div>
                    {replies.map(r => (
                      <div key={r.id} className={`flex ${r.sender_type === "staff" ? "justify-start" : "justify-end"}`}><div className={`max-w-[75%] rounded-2xl border-[2px] border-black px-5 py-3 text-sm font-bold shadow-[4px_4px_0_0_#000] ${r.sender_type === "staff" ? "bg-white text-black" : "bg-[#ca8a04] text-black"}`}><p className="text-[10px] font-black uppercase tracking-wider text-gray-500">{r.sender_name || (r.sender_type === "staff" ? "You" : "Student")}</p><p className="mt-1">{r.content}</p></div></div>
                    ))}
                    <div ref={endRef} />
                  </div>
                  <div className="border-t-[3px] border-black bg-white px-4 py-3"><div className="flex gap-3"><input value={replyText} onChange={e => setReplyText(e.target.value)} placeholder="Reply as admin…" className="min-w-0 flex-1 rounded-xl border-[2px] border-black px-4 py-2.5 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" /><button onClick={sendReply} disabled={replying || !replyText.trim()} className="rounded-xl border-[2px] border-black bg-black px-5 py-2.5 text-sm font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none disabled:opacity-50">{replying ? "…" : "Reply"}</button></div></div>
                </>
              ) : (
                <div className="flex flex-1 items-center justify-center p-10 text-center"><div><p className="text-4xl">📋</p><p className="mt-4 text-lg font-black text-black">Support Messages</p><p className="mt-2 text-sm font-bold text-gray-500">Select a message to respond.</p></div></div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
