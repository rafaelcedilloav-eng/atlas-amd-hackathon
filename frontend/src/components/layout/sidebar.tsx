import Link from "next/link";
import { LayoutDashboard, FileSearch, ShieldCheck, Settings, Database, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";

export const Sidebar = () => {
  return (
    <aside className="w-64 h-screen border-r border-amd-gray-800 bg-amd-black flex flex-col p-6 sticky top-0">
      {/* Brand Header */}
      <div className="flex items-center gap-3 mb-12">
        <div className="w-11 h-11 bg-amd-red rounded flex items-center justify-center font-black text-2xl italic shadow-[0_0_20px_rgba(237,28,36,0.3)] text-white">
          A
        </div>
        <div>
          <h1 className="text-2xl font-black tracking-tighter text-white leading-none">ATLAS</h1>
          <p className="text-[10px] text-amd-red font-black uppercase tracking-[0.2em] mt-1">Forensic_Audit</p>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-3">
        <p className="text-[10px] font-mono text-amd-gray-500 uppercase tracking-widest px-4 mb-4">Core_Systems</p>
        
        <Link 
          href="/" 
          className="flex items-center gap-3 px-4 py-3 rounded bg-amd-red/10 text-amd-red font-bold border border-amd-red/20 group hover:bg-amd-red/20 transition-all duration-300"
        >
          <LayoutDashboard className="w-5 h-5 group-hover:scale-110 transition-transform" />
          <span className="text-sm uppercase tracking-tight">Dashboard</span>
        </Link>
        
        <Link 
          href="/audits" 
          className="flex items-center gap-3 px-4 py-3 rounded text-amd-gray-300 hover:text-white hover:bg-amd-gray-900 border border-transparent hover:border-amd-gray-800 transition-all duration-300 font-medium group"
        >
          <FileSearch className="w-5 h-5 group-hover:text-amd-red transition-colors" />
          <span className="text-sm uppercase tracking-tight">Auditorías</span>
        </Link>
        
        <Link 
          href="/integrity" 
          className="flex items-center gap-3 px-4 py-3 rounded text-amd-gray-300 hover:text-white hover:bg-amd-gray-900 border border-transparent hover:border-amd-gray-800 transition-all duration-300 font-medium group"
        >
          <ShieldCheck className="w-5 h-5 group-hover:text-amd-red transition-colors" />
          <span className="text-sm uppercase tracking-tight">Integrity Gate</span>
        </Link>
      </nav>

      {/* System Status Section */}
      <div className="mt-auto pt-6 border-t border-amd-gray-800 space-y-4">
        <div className="px-4 py-4 bg-amd-gray-950 rounded border border-amd-gray-800 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-[2px] h-0 bg-amd-red group-hover:h-full transition-all duration-500" />
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="w-3 h-3 text-amd-red" />
            <span className="text-[10px] text-white font-bold uppercase tracking-widest">Hardware_Status</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[9px] font-mono text-amd-gray-500">AMD_MI300X</span>
            <span className="text-[9px] font-mono text-accent-success">ACTIVE</span>
          </div>
          <div className="h-1 bg-amd-gray-800 rounded-full mt-2 overflow-hidden">
            <div className="h-full bg-amd-red w-[64%] shadow-[0_0_8px_rgba(237,28,36,0.4)]" />
          </div>
        </div>

        <div className="px-4 py-3 bg-amd-gray-950/50 rounded border border-amd-gray-900">
          <div className="flex items-center gap-2 mb-1">
            <Database className="w-3 h-3 text-accent-success" />
            <span className="text-[10px] text-accent-success font-bold uppercase tracking-widest">Supabase_DB</span>
          </div>
          <p className="text-[9px] font-mono text-amd-gray-600 truncate">
            {process.env.NEXT_PUBLIC_SUPABASE_URL?.replace("https://", "") || "connected.atlas.io"}
          </p>
        </div>

        <Link href="/settings" className="flex items-center gap-3 px-4 py-2 text-amd-gray-500 hover:text-amd-red transition-all font-medium text-xs uppercase tracking-tighter">
          <Settings className="w-4 h-4" />
          Configuración_del_Sistema
        </Link>
      </div>
    </aside>
  );
};
