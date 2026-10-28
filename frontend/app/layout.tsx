import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "AI Stock Intelligence Platform | Indian Equities (NSE & BSE)",
  description: "Automated Indian Equity Intelligence, Real-time Market Data, Financial Analytics & LangGraph Research Assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-slate-900 bg-slate-950/90 py-6 text-center text-xs text-slate-500">
          <div className="container mx-auto px-4">
            AI Stock Intelligence Platform • Indian Equities (NSE/BSE) • Deterministic Calculations & Grounded LangGraph Research
          </div>
        </footer>
      </body>
    </html>
  );
}

