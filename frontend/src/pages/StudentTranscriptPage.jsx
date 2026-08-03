import { useEffect, useState } from "react";
import api from "../services/api";

const gradeOptions = ["A", "B", "C", "D", "E", "F"];
const semesterOptions = ["First", "Second"];

function levelsBelow(current) {
  const levels = [];
  for (let l = 100; l < current; l += 100) levels.push(l);
  return levels;
}

export default function StudentTranscriptPage() {
  const [entries, setEntries] = useState([]);
  const [courses, setCourses] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [form, setForm] = useState({ course_id: "", semester: "First", grade: "A" });
  const [customMode, setCustomMode] = useState(false);
  const [custom, setCustom] = useState({ code: "", title: "", credit_units: 3, grade: "A", semester: "First", level: "100" });
  const [msg, setMsg] = useState("");
  const [uploaded, setUploaded] = useState(false);

  const load = async () => {
    try {
      const [eRes, cRes, pRes] = await Promise.all([
        api.get("courses/transcript/"),
        api.get("courses/course/"),
        api.get("accounts/profile/"),
      ]);
      setEntries(eRes.data || []);
      setCourses(cRes.data || []);
      setProfile(pRes.data);
      const cl = pRes.data?.current_level;
      if (cl) {
        const levels = levelsBelow(cl);
        setSelectedLevel(levels.length ? String(levels[levels.length - 1]) : null);
      }
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const availableLevels = profile ? levelsBelow(profile.current_level) : [];
  const semesterMap = { "First": 1, "Second": 2 };

  const filteredCourses = courses.filter((c) => {
    if (!profile || !selectedLevel) return true;
    return c.level === Number(selectedLevel) && c.semester === semesterMap[form.semester];
  });

  const gradeToStatus = (grade) => grade === "F" ? "failed" : "passed";

  const submitResult = async (e) => {
    e.preventDefault();
    setMsg("");
    try {
      if (customMode) {
        const match = courses.find((c) => c.code === custom.code);
        if (match) {
          await api.post("courses/transcript/", {
            course_id: match.id, semester: custom.semester,
            grade: custom.grade, status: gradeToStatus(custom.grade),
            credit_points: gradeToPoints(custom.grade),
          });
        } else {
          setMsg("Course code not found in the system. Ask admin to add it first.");
          return;
        }
      } else {
        if (!form.course_id) { setMsg("Please select a course."); return; }
        await api.post("courses/transcript/", {
          course_id: form.course_id, semester: form.semester,
          grade: form.grade, status: gradeToStatus(form.grade),
          credit_points: gradeToPoints(form.grade),
        });
      }
      setMsg("Result saved successfully!");
      setForm({ course_id: "", semester: "First", grade: "A" });
      setCustom({ code: "", title: "", credit_units: 3, grade: "A", semester: "First", level: "100" });
      await load();
    } catch (err) {
      const d = err.response?.data;
      setMsg(d?.detail || Object.values(d || {}).flat().join(" ") || "Could not save result.");
    }
  };

  const creditsEarned = entries.filter((e) => e.status === "passed").reduce((s, e) => s + (e.course?.credit_units || 0), 0);
  const carryoverCount = entries.filter((e) => e.status === "carryover" || e.status === "failed").length;

  if (loading) return <p className="text-sm text-slate-500">Loading transcript…</p>;

  return (
    <div className="space-y-7">
      {/* Header */}
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-bold uppercase tracking-wider text-[#ca8a04]">Academic Records</p>
          <h1 className="mt-1 text-3xl font-black tracking-tight text-black">Transcript & Results</h1>
          <p className="mt-2 text-sm font-medium text-gray-600">
            Add results from any previous level to power the recommendation engine for your current level.
          </p>
        </div>
        <label className="cursor-pointer rounded-2xl border-[3px] border-black bg-black px-5 py-3 text-center text-sm font-black text-white shadow-[5px_5px_0_0_#000] active:shadow-none transition-all">
          <input className="hidden" type="file" accept=".pdf,.jpg,.png" onChange={() => { setUploaded(true); setMsg("Transcript uploaded. Results must still be added below for analysis."); }} />
          {uploaded ? "Uploaded" : "Upload Transcript"}
        </label>
      </section>

      {/* Stats */}
      <section className="grid gap-4 sm:grid-cols-4">
        <article className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]">
          <p className="text-xs font-black uppercase text-gray-500">Credits Earned</p>
          <p className="mt-2 text-3xl font-black text-black">{creditsEarned}</p>
        </article>
        <article className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]">
          <p className="text-xs font-black uppercase text-gray-500">Courses Done</p>
          <p className="mt-2 text-3xl font-black text-black">{entries.filter((e) => e.status === "passed").length}</p>
        </article>
        <article className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]">
          <p className="text-xs font-black uppercase text-gray-500">Carryovers</p>
          <p className="mt-2 text-3xl font-black text-amber-600">{carryoverCount}</p>
        </article>
        <article className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]">
          <p className="text-xs font-black uppercase text-gray-500">Available Courses</p>
          <p className="mt-2 text-3xl font-black text-black">{filteredCourses.length}</p>
        </article>
      </section>

      {/* Add Result Form */}
      <form onSubmit={submitResult} className="rounded-3xl border-[3px] border-black bg-white p-6 shadow-[8px_8px_0_0_#000]">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-black text-black">Add Result</h2>
          <button type="button" onClick={() => { setCustomMode(!customMode); setMsg(""); }}
            className="rounded-xl border-[2px] border-black bg-[#fef9c3] px-4 py-2 text-xs font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all">
            {customMode ? "Pick from courses" : "Add manually"}
          </button>
        </div>

        {msg && (
          <div className="mt-4 rounded-2xl border-[2px] border-black bg-[#fef9c3] p-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000]">
            {msg}
          </div>
        )}

        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {customMode ? (
            <>
              <div>
                <label className="text-xs font-black uppercase text-black">Course Code</label>
                <input value={custom.code} onChange={(e) => setCustom({ ...custom, code: e.target.value })} list="course-codes" placeholder="e.g. CSC 302" className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" required />
                <datalist id="course-codes">
                  {courses.map((c) => <option key={c.id} value={c.code} />)}
                </datalist>
              </div>
              <div>
                <label className="text-xs font-black uppercase text-black">Semester</label>
                <select value={custom.semester} onChange={(e) => setCustom({ ...custom, semester: e.target.value })} className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
                  {semesterOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-black uppercase text-black">Grade</label>
                <select value={custom.grade} onChange={(e) => setCustom({ ...custom, grade: e.target.value })} className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
                  {gradeOptions.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div className="self-end">
                <p className="mt-1.5 rounded-xl border-[2px] border-black bg-gray-50 px-4 py-3 text-sm font-bold text-gray-600 shadow-[3px_3px_0_0_#000]">Status: <span className={`${custom.grade === "F" ? "text-red-600" : "text-green-600"}`}>{custom.grade === "F" ? "Failed" : "Passed"}</span> (auto)</p>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="text-xs font-black uppercase text-black">Level</label>
                <select value={selectedLevel || ""} onChange={(e) => setSelectedLevel(e.target.value)} className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
                  {availableLevels.length === 0 && <option value="">— No previous levels —</option>}
                  {availableLevels.map((l) => <option key={l} value={l}>{l} Level</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-black uppercase text-black">Course</label>
                <select value={form.course_id} onChange={(e) => setForm({ ...form, course_id: e.target.value })} className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
                  <option value="">— Select course —</option>
                  {filteredCourses.map((c) => (
                    <option key={c.id} value={c.id}>{c.code} — {c.title} ({c.credit_units} units)</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-black uppercase text-black">Semester</label>
                <select value={form.semester} onChange={(e) => setForm({ ...form, semester: e.target.value })} className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
                  {semesterOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-black uppercase text-black">Grade</label>
                <select value={form.grade} onChange={(e) => setForm({ ...form, grade: e.target.value })} className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
                  {gradeOptions.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
            </>
          )}
        </div>

        <button type="submit" className="mt-5 rounded-2xl border-[3px] border-black bg-[#ca8a04] px-8 py-3 text-sm font-black text-black shadow-[5px_5px_0_0_#000] active:shadow-none active:translate-x-[5px] active:translate-y-[5px] transition-all hover:bg-[#eab308]">
          Save Result
        </button>
      </form>

      {/* Results table */}
      <section className="overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
        <div className="border-b-[3px] border-black bg-[#fef9c3] px-6 py-4">
          <h2 className="text-lg font-black text-black">Your Results</h2>
          <p className="mt-1 text-sm font-medium text-gray-600">{entries.length} entries</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[580px] text-left text-sm">
            <thead className="bg-black text-xs font-black uppercase tracking-wider text-white">
              <tr>
                <th className="px-6 py-4">Course</th>
                <th className="px-4 py-4">Units</th>
                <th className="px-4 py-4">Semester</th>
                <th className="px-4 py-4">Grade</th>
                <th className="px-6 py-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-10 text-center font-bold text-gray-400">No results yet. Add your first result above.</td></tr>
              ) : (
                entries.map((e) => (
                  <tr key={e.id} className="border-t-[2px] border-black">
                    <td className="px-6 py-4">
                      <p className="font-bold text-black">{e.course?.code}</p>
                      <p className="mt-0.5 text-xs font-medium text-gray-500">{e.course?.title}</p>
                    </td>
                    <td className="px-4 py-4 font-bold text-black">{e.course?.credit_units || "—"}</td>
                    <td className="px-4 py-4 font-medium text-gray-600">{e.semester}</td>
                    <td className={`px-4 py-4 font-black text-lg ${e.grade === "A" ? "text-green-600" : e.grade === "F" ? "text-red-600" : "text-black"}`}>{e.grade}</td>
                    <td className="px-6 py-4">
                      <span className={`rounded-full border-[2px] border-black px-3 py-1 text-xs font-black ${e.status === "passed" ? "bg-green-100 text-green-800" : e.status === "carryover" ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"}`}>
                        {e.status === "passed" ? "Passed" : e.status === "carryover" ? "Carryover" : "Failed"}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function gradeToPoints(grade) {
  const map = { A: 5.0, B: 4.0, C: 3.0, D: 2.0, E: 1.0, F: 0.0 };
  return map[grade] || 0.0;
}
