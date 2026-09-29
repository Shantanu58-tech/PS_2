import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";

import { EngineStatus } from "@/components/EngineStatus";
import { Sidebar } from "@/components/Sidebar";

import "./globals.css";

const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "PRAHARI · Narrative Forensics Console",
  description:
    "Compliance-first narrative forensics for India's code-mixed information space. Team MOGGERS, VIT Pune.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${plexSans.variable} ${plexMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <header className="flex h-12 items-center justify-between border-b border-line bg-panel px-4">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-sm font-medium tracking-[0.3em] text-accent">PRAHARI</span>
            <span className="hidden text-xs text-ink-faint sm:inline">Narrative forensics, not surveillance</span>
          </div>
          <EngineStatus />
        </header>
        <div className="flex flex-1">
          <aside className="w-56 shrink-0 border-r border-line bg-panel">
            <Sidebar />
          </aside>
          <main className="flex-1 overflow-x-hidden p-8">{children}</main>
        </div>
        <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-line bg-panel px-4 py-2 font-mono text-[10px] text-ink-faint">
          <span>SIH26152 · Social Media Analytics · NTRO</span>
          <span>Team MOGGERS, VIT Pune · Team Leader: Om Soma</span>
        </footer>
      </body>
    </html>
  );
}
