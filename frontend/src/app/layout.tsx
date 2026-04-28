import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { Providers } from "@/components/providers";

const inter = Inter({ 
  subsets: ["latin"], 
  variable: "--font-ui" 
});

const mono = JetBrains_Mono({ 
  subsets: ["latin"], 
  variable: "--font-mono" 
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display"
});

export const metadata: Metadata = {
  title: "ATLAS | Forensic Audit Dashboard",
  description: "Advanced Document Integrity & Fraud Detection powered by AMD MI300X",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className={`${inter.variable} ${mono.variable} ${spaceGrotesk.variable}`}>
      <body className="bg-amd-black text-white min-h-screen flex font-ui antialiased selection:bg-amd-red selection:text-white">
        <Providers>
          <Sidebar />
          <main className="flex-1 overflow-y-auto relative">
            {/* Subtle Grid Overlay */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
            <div className="relative z-10">
              {children}
            </div>
          </main>
        </Providers>
      </body>
    </html>
  );
}
