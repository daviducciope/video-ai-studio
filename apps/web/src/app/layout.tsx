import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "Video AI Studio",
  description: "MVP locale per storyboard, preview e render mock di video AI.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="it">
      <body>
        <div className="page-shell">
          <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <Link href="/" className="text-2xl font-semibold tracking-tight">
              Video AI Studio
            </Link>
            <nav className="flex items-center gap-3 text-sm">
              <Link href="/" className="btn-secondary">
                Dashboard
              </Link>
              <Link href="/projects/new" className="btn-primary">
                Nuovo progetto
              </Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
