"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "./sidebar";

// These routes render full-screen (no sidebar).
// All 3D immersive pages live here.
const FULL_SCREEN: string[] = ["/", "/dashboard", "/analytics", "/hardware"];

function needsSidebar(pathname: string): boolean {
  if (FULL_SCREEN.includes(pathname)) return false;
  if (pathname === "/audits") return false;
  return true;
}

export function ClientShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (!needsSidebar(pathname)) {
    return <>{children}</>;
  }

  return (
    <>
      <Sidebar />
      <main className="flex-1 overflow-y-auto relative">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
        <div className="relative z-10">{children}</div>
      </main>
    </>
  );
}
