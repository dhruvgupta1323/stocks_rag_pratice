"use client";

import Link from "next/link";
import { TrendingUp, BarChart2, ShieldCheck, Search, Activity } from "lucide-react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
            <TrendingUp className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-slate-100 tracking-tight">AI Stock Intelligence</span>
              <span className="rounded bg-cyan-950 px-1.5 py-0.5 text-[10px] font-semibold text-cyan-400 border border-cyan-800/50">NSE/BSE</span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Indian Equities • Deterministic Analytics • LangGraph RAG</p>
          </div>
        </Link>

        <nav className="flex items-center gap-2 sm:gap-4">
          <Link
            href="/"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-900 transition-colors"
          >
            <Search className="h-4 w-4 text-slate-400" />
            <span className="hidden sm:inline">Search Equities</span>
          </Link>

          <Link
            href="/stocks/RELIANCE"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-900 transition-colors"
          >
            <Activity className="h-4 w-4 text-slate-400" />
            <span className="hidden sm:inline">Dashboard</span>
          </Link>

          <Link
            href="/evaluation"
            className="flex items-center gap-1.5 rounded-lg bg-slate-900 border border-slate-800 px-3 py-2 text-sm font-medium text-cyan-400 hover:bg-slate-800 hover:text-cyan-300 transition-colors shadow-sm"
          >
            <ShieldCheck className="h-4 w-4 text-cyan-400" />
            <span>AI Evaluation</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}

