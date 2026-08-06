import { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";

const navigation = [
  { label: "Overview", to: "/dashboard/student/overview", icon: "01" },
  { label: "Academic profile", to: "/dashboard/student/profile", icon: "02" },
  { label: "Recommendations", to: "/dashboard/student/recommendations", icon: "03" },
  { label: "AI academic assistant", to: "/dashboard/student/chat", icon: "04" },
  { label: "Messages & Support", to: "/dashboard/student/messages", icon: "05" },
  { label: "Transcript & results", to: "/dashboard/student/transcript", icon: "06" },
];

function NavItems({ onNavigate }) {
  return (
    <nav className="space-y-1" aria-label="Student navigation">
      {navigation.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          onClick={onNavigate}
          className={({ isActive }) =>
            `group flex items-center gap-3 rounded-xl border-[2px] px-3 py-3 text-sm font-black transition-all ${
              isActive
                ? "border-[#facc15] bg-[#facc15] text-black shadow-[3px_3px_0_0_#fff]"
                : "border-transparent text-gray-300 hover:border-zinc-700 hover:bg-zinc-900 hover:text-white"
            }`
          }
        >
          <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md border border-current/30 text-[10px] font-black">{item.icon}</span>
          <span className="min-w-0 truncate">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export default function StudentLayout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  // Close the drawer on navigation so the new page is actually visible.
  useEffect(() => setMenuOpen(false), [location.pathname]);

  // Prevent the page behind the drawer from scrolling underneath it.
  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuOpen]);

  useEffect(() => {
    const onKeyDown = (e) => e.key === "Escape" && setMenuOpen(false);
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

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
        {/* Sidebar - desktop */}
        <aside className="hidden w-[270px] shrink-0 flex-col border-r-[3px] border-black bg-black px-5 py-7 lg:flex">
          <div className="flex items-center gap-3 px-2">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border-[2px] border-[#facc15] bg-black text-sm font-black text-[#facc15]">TA</div>
            <div className="min-w-0">
              <p className="font-black tracking-tight text-white">TO-AAS</p>
              <p className="truncate text-xs font-bold text-gray-400">Academic workspace</p>
            </div>
          </div>

          <div className="mt-10">
            <NavItems />
          </div>

          <div className="mt-auto rounded-2xl border-[2px] border-zinc-700 bg-zinc-900 p-4">
            <p className="text-sm font-black text-white">Need guidance?</p>
            <p className="mt-1 text-xs font-bold leading-5 text-gray-400">Your academic advisor is available for course-plan reviews.</p>
            <NavLink to="/dashboard/student/messages" className="mt-3 inline-block text-xs font-black text-[#facc15] underline underline-offset-4">Message advisor →</NavLink>
          </div>
          <button onClick={signOut} className="mt-5 px-3 text-left text-sm font-black text-gray-400 transition hover:text-red-400">Sign out</button>
        </aside>

        {/* Sidebar - mobile drawer */}
        {menuOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button
              className="absolute inset-0 h-full w-full bg-black/60"
              aria-label="Close navigation"
              onClick={() => setMenuOpen(false)}
            />
            <aside className="absolute left-0 top-0 flex h-full w-[82%] max-w-[300px] flex-col overflow-y-auto border-r-[3px] border-black bg-black px-5 py-7">
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border-[2px] border-[#facc15] bg-black text-sm font-black text-[#facc15]">TA</div>
                  <div className="min-w-0">
                    <p className="font-black tracking-tight text-white">TO-AAS</p>
                    <p className="truncate text-xs font-bold text-gray-400">Academic workspace</p>
                  </div>
                </div>
                <button
                  onClick={() => setMenuOpen(false)}
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border-[2px] border-zinc-700 text-lg font-black text-white"
                  aria-label="Close navigation"
                >
                  ×
                </button>
              </div>

              <div className="mt-8">
                <NavItems onNavigate={() => setMenuOpen(false)} />
              </div>

              <button onClick={signOut} className="mt-8 px-3 text-left text-sm font-black text-gray-400 transition hover:text-red-400">Sign out</button>
            </aside>
          </div>
        )}

        {/* Main */}
        <section className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between gap-3 border-b-[3px] border-black bg-white px-4 sm:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <button
                onClick={() => setMenuOpen(true)}
                className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border-[2px] border-black text-black shadow-[2px_2px_0_0_#000] transition-all active:shadow-none lg:hidden"
                aria-label="Open navigation"
                aria-expanded={menuOpen}
              >
                <span className="space-y-[3px]">
                  <span className="block h-[2px] w-5 bg-black" />
                  <span className="block h-[2px] w-5 bg-black" />
                  <span className="block h-[2px] w-5 bg-black" />
                </span>
              </button>
              <div className="font-black tracking-tight text-black lg:hidden">TO-AAS</div>
              <p className="hidden text-sm font-bold text-gray-600 lg:block">Student decision-support workspace</p>
            </div>

            <div className="flex shrink-0 items-center gap-2 sm:gap-3">
              <button className="hidden h-9 w-9 place-items-center rounded-full border-[2px] border-black text-sm font-black text-black shadow-[2px_2px_0_0_#000] sm:grid" aria-label="Notifications">!</button>
              <div className="h-9 w-9 shrink-0 overflow-hidden rounded-full border-[2px] border-black">
                <img className="h-full w-full object-cover" src={user?.profile_photo || "https://i.pravatar.cc/100?img=47"} alt="Profile" />
              </div>
              <div className="hidden min-w-0 sm:block">
                <p className="truncate text-sm font-black text-black">{user?.first_name || "Student"}</p>
                <p className="truncate text-xs font-bold text-gray-500">{user?.username || ""}</p>
              </div>
            </div>
          </header>
          <main className="mx-auto w-full max-w-[1280px] flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
        </section>
      </div>
    </div>
  );
}
