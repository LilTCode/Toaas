import { useEffect, useState } from "react";
import api from "../services/api";

const programmeLabel = { computer_science: "B.Sc. Computer Science", software_engineering: "B.Sc. Software Engineering", cyber_security: "B.Sc. Cyber Security" };
const strengths = [["logical_reasoning", "Logical reasoning"], ["abstract_reasoning", "Abstract reasoning"], ["theoretical_knowledge", "Theoretical knowledge"], ["quantitative_calculation", "Quantitative calculation"], ["practical_application", "Practical application"]];

const photoCache = new Map();

export default function StudentProfilePage() {
  const [profile, setProfile] = useState(null); const [cognitive, setCognitive] = useState({}); const [editing, setEditing] = useState(false); const [saving, setSaving] = useState(false); const [message, setMessage] = useState("");
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const load = async () => { try { const [p, c] = await Promise.all([api.get("accounts/profile/"), api.get("advisories/profile/")]); setProfile(p.data); setCognitive(c.data); } catch { setMessage("Unable to load your saved profile."); } };
  useEffect(() => { load(); }, []);
  const save = async e => {
    e.preventDefault(); setSaving(true);
    try {
      const fd = new FormData();
      fd.append("first_name", profile.first_name || "");
      fd.append("last_name", profile.last_name || "");
      fd.append("programme", profile.programme || "");
      fd.append("current_level", profile.current_level || 100);
      fd.append("current_semester", profile.current_semester || 1);
      if (photoFile) fd.append("profile_photo", photoFile);
      const {data} = await api.put("accounts/profile/", fd);
      setProfile(data);
      localStorage.setItem("toaas_user", JSON.stringify(data));
      setEditing(false); setPhotoFile(null); setPhotoPreview(null);
      photoCache.delete("profile_photo");
      setMessage("Profile saved.");
      await api.get("advisories/activity/");
    } catch (err) {
      const detail = err.response?.data ? JSON.stringify(err.response.data) : err.message;
      setMessage("Could not save: " + detail);
    }
    finally { setSaving(false); }
  };
  if (!profile) return <p className="text-sm font-bold text-gray-500">Loading profile…</p>;

  const photoSrc = photoPreview || profile.profile_photo || "https://i.pravatar.cc/160?img=47";

  return (
    <div className="space-y-7">
      {/* Header */}
      <section className="flex flex-col gap-5 rounded-3xl border-[3px] border-black bg-white p-6 shadow-[8px_8px_0_0_#000] sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="relative">
            <img className="h-20 w-20 rounded-2xl border-[3px] border-black object-cover shadow-[3px_3px_0_0_#000]" src={photoSrc} alt={`${profile.first_name} ${profile.last_name}`}/>
            {editing && (
              <label className="absolute -bottom-1 -right-1 grid h-6 w-6 cursor-pointer place-items-center rounded-full border-[2px] border-black bg-[#ca8a04] text-[10px] font-black text-black shadow-[2px_2px_0_0_#000] hover:bg-[#eab308]">
                ✏️
                <input className="hidden" type="file" accept="image/*" onChange={e => {
                  const file = e.target.files[0];
                  if (file) { setPhotoFile(file); setPhotoPreview(URL.createObjectURL(file)); }
                }} />
              </label>
            )}
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-wider text-[#ca8a04]">Academic Profile</p>
            <h1 className="mt-1 text-2xl font-black text-black">{profile.first_name} {profile.last_name}</h1>
            <p className="mt-1 text-sm font-bold text-gray-500">{profile.username} · {programmeLabel[profile.programme]}</p>
          </div>
        </div>
        <button onClick={()=>{setEditing(!editing); if (editing) { setPhotoFile(null); setPhotoPreview(null); }}} className="rounded-xl border-[2px] border-black bg-white px-4 py-2.5 text-sm font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-[#fef9c3]">
          {editing ? "Cancel" : (profile.profile_photo ? "✏️ Edit profile" : "✏️ Set up profile")}
        </button>
      </section>

      {/* Edit form */}
      {editing && (
        <form onSubmit={save} className="grid gap-4 rounded-3xl border-[3px] border-black bg-white p-6 shadow-[8px_8px_0_0_#000] sm:grid-cols-2">
          <label className="text-xs font-black uppercase text-black">First name
            <input value={profile.first_name || ""} onChange={e=>setProfile({...profile,first_name:e.target.value})} className="mt-1.5 block w-full rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" />
          </label>
          <label className="text-xs font-black uppercase text-black">Last name
            <input value={profile.last_name || ""} onChange={e=>setProfile({...profile,last_name:e.target.value})} className="mt-1.5 block w-full rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" />
          </label>
          <label className="text-xs font-black uppercase text-black">Programme
            <select value={profile.programme} onChange={e=>setProfile({...profile,programme:e.target.value})} className="mt-1.5 block w-full rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
              <option value="computer_science">B.Sc. Computer Science</option>
              <option value="software_engineering">B.Sc. Software Engineering</option>
              <option value="cyber_security">B.Sc. Cyber Security</option>
            </select>
          </label>
          <label className="text-xs font-black uppercase text-black">Current level
            <select value={profile.current_level} onChange={e=>setProfile({...profile,current_level:Number(e.target.value)})} className="mt-1.5 block w-full rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
              {[100,200,300,400].map(x=><option key={x} value={x}>{x} Level</option>)}
            </select>
          </label>
          <label className="text-xs font-black uppercase text-black">Current semester
            <select value={profile.current_semester} onChange={e=>setProfile({...profile,current_semester:Number(e.target.value)})} className="mt-1.5 block w-full rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
              <option value={1}>First semester</option>
              <option value={2}>Second semester</option>
            </select>
          </label>
          <div>
            <label className="text-xs font-black uppercase text-black">Profile Photo</label>
            <div className="mt-1.5 flex items-center gap-3">
              <label className="flex-1 cursor-pointer rounded-xl border-[2px] border-black bg-[#fef9c3] px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none hover:bg-white transition-all">
                {photoFile ? photoFile.name : (profile.profile_photo ? "Change photo" : "Choose file")}
                <input className="hidden" type="file" accept="image/*" onChange={e => {
                  const file = e.target.files[0];
                  if (file) { setPhotoFile(file); setPhotoPreview(URL.createObjectURL(file)); }
                }} />
              </label>
              {photoFile && (
                <button type="button" onClick={() => { setPhotoFile(null); setPhotoPreview(null); }}
                  className="rounded-xl border-[2px] border-black bg-white px-3 py-3 text-xs font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all">
                  Clear
                </button>
              )}
            </div>
          </div>
          <button disabled={saving} className="w-fit rounded-xl border-[2px] border-black bg-[#ca8a04] px-5 py-2.5 text-sm font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all">{saving ? "Saving…" : "💾 Save changes"}</button>
        </form>
      )}

      {/* Details grid */}
      <section className="grid gap-6 xl:grid-cols-[.85fr_1.15fr]">
        <article className="rounded-3xl border-[3px] border-black bg-white p-6 shadow-[8px_8px_0_0_#000]">
          <h2 className="text-lg font-black text-black">Academic standing</h2>
          <dl className="mt-5 space-y-4 text-sm">
            {[["Programme", programmeLabel[profile.programme]], ["Current level", `${profile.current_level} Level`], ["Semester", profile.current_semester === 1 ? "First" : "Second"], ["Session", profile.session]].map(([k, v]) => (
              <div key={k} className="flex justify-between border-b-[2px] border-black pb-3">
                <dt className="text-xs font-black uppercase text-gray-500">{k}</dt>
                <dd className="font-bold text-black">{v}</dd>
              </div>
            ))}
          </dl>
        </article>
        <article className="rounded-3xl border-[3px] border-black bg-white p-6 shadow-[8px_8px_0_0_#000]">
          <h2 className="text-lg font-black text-black">Learning strengths</h2>
          <p className="mt-1 text-sm font-bold text-gray-500">Calculated from your submitted results and course cognitive demands.</p>
          <div className="mt-6 space-y-4">
            {strengths.map(([key,label]) => {
              const score=Math.round(cognitive[key] || 0);
              return (
                <div key={key}>
                  <div className="flex justify-between text-xs font-black uppercase">
                    <span className="text-black">{label}</span>
                    <span className="text-gray-500">{score}%</span>
                  </div>
                  <div className="mt-1 h-3 rounded-full border-[2px] border-black bg-white">
                    <div className="h-full rounded-full bg-[#ca8a04] transition-all duration-700" style={{width:`${score}%`}}/>
                  </div>
                </div>
              );
            })}
          </div>
        </article>
      </section>

      {message && <p className="rounded-2xl border-[2px] border-black bg-[#fef9c3] p-4 text-sm font-bold text-black shadow-[3px_3px_0_0_#000]">{message}</p>}
    </div>
  );
}
