import Link from "next/link";
import { LayoutDashboard, FileSearch, ShieldCheck, Settings, Database } from "lucide-react";

export const Sidebar = () => {
  return (
    <aside className="w-64 h-screen border-r border-white/10 bg-slate-950 flex flex-col p-6 sticky top-0">
      <div className="flex items-center gap-3 mb-10">
        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center font-black text-xl italic shadow-lg shadow-blue-500/20">
          A
        </div>
        <div>
          <h1 className="text-xl font-black tracking-tighter text-white">ATLAS</h1>
          <p className="text-[10px] text-blue-400 font-bold uppercase tracking-widest">Forensic Audit</p>
        </div>
      </div>

      <nav className="flex-1 space-y-2">
        <Link href="/" className="flex items-center gap-3 px-4 py-3 rounded-xl bg-blue-600/10 text-blue-400 font-semibold border border-blue-600/20">
          <LayoutDashboard className="w-5 h-5" />
          Dashboard
        </Link>
        <Link href="/audits" className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/60 hover:text-white hover:bg-white/5 transition-all font-medium">
          <FileSearch className="w-5 h-5" />
          Auditorías
        </Link>
        <Link href="/integrity" className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/60 hover:text-white hover:bg-white/5 transition-all font-medium">
          <ShieldCheck className="w-5 h-5" />
          Integrity Gate
        </Link>
      </nav>

      <div className="mt-auto pt-6 border-t border-white/10 space-y-2">
        <Link href="/settings" className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/40 hover:text-white transition-all font-medium text-sm">
          <Settings className="w-4 h-4" />
          Configuración
        </Link>
        <div className="px-4 py-3 bg-white/5 rounded-xl border border-white/10">
          <div className="flex items-center gap-2 mb-1">
            <Database className="w-3 h-3 text-emerald-400" />
            <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest">Supabase</span>
          </div>
          <p className="text-[10px] text-white/40 font-mono overflow-hidden text-ellipsis">
            {process.env.NEXT_PUBLIC_SUPABASE_URL || "Connected"}
          </p>
        </div>
      </div>
    </aside>
  );
};
