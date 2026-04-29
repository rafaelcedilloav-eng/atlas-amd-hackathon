import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { ClientShell } from "@/components/layout/client-shell";
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
    <html lang="en" className={`${inter.variable} ${mono.variable} ${spaceGrotesk.variable}`}>
      <body className="bg-amd-black text-white min-h-screen flex font-ui antialiased selection:bg-amd-red selection:text-white">
        <Providers>
          <ClientShell>{children}</ClientShell>
        </Providers>
      </body>
    </html>
  );
}
