import { NavLink, useNavigate } from "react-router-dom";

const navigation = [
  { label: "Overview", to: "/dashboard/student/overview", icon: "01" },
  { label: "Academic profile", to: "/dashboard/student/profile", icon: "02" },
  { label: "Recommendations", to: "/dashboard/student/recommendations", icon: "03" },
  { label: "AI academic assistant", to: "/dashboard/student/chat", icon: "04" },
  { label: "Messages & Support", to: "/dashboard/student/messages", icon: "05" },
  { label: "Transcript & results", to: "/dashboard/student/transcript", icon: "06" },
];

export default function StudentLayout({ children }) {
  const navigate = useNavigate();

  const signOut = () => {
    localStorage.removeItem("toaas_access_token");
    localStorage.removeItem("toaas_refresh_token");
    navigate("/auth");
  };

  const user = (() => {
    try {
      const raw = localStorage.getItem("toaas_user");
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  })();

  return (
    <div className="min-h-screen bg-[#f3f1e8] text-black">
      <div className="mx-auto flex min-h-screen max-w-[1600px]">
        {/* Sidebar */}
        <aside className="hidden w-[270px] shrink-0 flex-col border-r-[3px] border-black bg-black px-5 py-7 lg:flex">
          <div className="flex items-center gap-3 px-2">
            <div className="grid h-10 w-10 place-items-center rounded-xl border-[2px] border-[#facc15] bg-black text-sm font-black text-[#facc15]">TA</div>
            <div>
              <p className="font-black tracking-tight text-white">TO-AAS</p>
              <p className="text-xs font-bold text-gray-400">Academic workspace</p>
            </div>
          </div>

          <nav className="mt-10 space-y-1" aria-label="Student navigation">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `group flex items-center gap-3 rounded-xl border-[2px] px-3 py-3 text-sm font-black transition-all ${
                    isActive
                      ? "border-[#facc15] bg-[#facc15] text-black shadow-[3px_3px_0_0_#fff]"
                      : "border-transparent text-gray-300 hover:border-zinc-700 hover:bg-zinc-900 hover:text-white"
                  }`
                }
              >
                <span className="grid h-6 w-6 place-items-center rounded-md border border-current/30 text-[10px] font-black">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="mt-auto rounded-2xl border-[2px] border-zinc-700 bg-zinc-900 p-4">
            <p className="text-sm font-black text-white">Need guidance?</p>
            <p className="mt-1 text-xs font-bold leading-5 text-gray-400">Your academic advisor is available for course-plan reviews.</p>
            <NavLink to="/dashboard/student/messages" className="mt-3 inline-block text-xs font-black text-[#facc15] underline underline-offset-4">Message advisor →</NavLink>
          </div>
          <button onClick={signOut} className="mt-5 px-3 text-left text-sm font-black text-gray-400 transition hover:text-red-400">Sign out</button>
        </aside>

        {/* Main */}
        <section className="min-w-0 flex-1">
          <header className="flex h-[76px] items-center justify-between border-b-[3px] border-black bg-white px-5 sm:px-8">
            <div className="lg:hidden font-black tracking-tight text-black">TO-AAS</div>
            <div className="hidden lg:block"><p className="text-sm font-bold text-gray-600">Student decision-support workspace</p></div>
            <div className="flex items-center gap-3">
              <button className="grid h-9 w-9 place-items-center rounded-full border-[2px] border-black text-sm font-black text-black shadow-[2px_2px_0_0_#000]" aria-label="Notifications">!</button>
              <div className="h-9 w-9 overflow-hidden rounded-full border-[2px] border-black">
                <img className="h-full w-full object-cover" src={user?.profile_photo || "https://i.pravatar.cc/100?img=47"} alt="Profile" />
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-black text-black">{user?.first_name || "Student"}</p>
                <p className="text-xs font-bold text-gray-500">{user?.username || ""}</p>
              </div>
            </div>
          </header>
          <main className="mx-auto max-w-[1280px] p-5 sm:p-8">{children}</main>
        </section>
      </div>
    </div>
  );
}
