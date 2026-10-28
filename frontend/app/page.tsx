"use client";

import Link from "next/link";
import { TrendingUp, ShieldCheck, Database, Cpu, Search, ArrowRight, BarChart3, Newspaper } from "lucide-react";
import StockSearch from "@/components/StockSearch";

const FEATURED_STOCKS = [
  { symbol: "RELIANCE", name: "Reliance Industries", sector: "Energy", exchange: "NSE" },
  { symbol: "TCS", name: "Tata Consultancy Services", sector: "Information Technology", exchange: "NSE" },
  { symbol: "HDFCBANK", name: "HDFC Bank", sector: "Financial Services", exchange: "NSE" },
  { symbol: "INFY", name: "Infosys", sector: "Information Technology", exchange: "NSE" },
  { symbol: "TATAMOTORS", name: "Tata Motors", sector: "Automobile", exchange: "NSE" },
  { symbol: "SBIN", name: "State Bank of India", sector: "Financial Services", exchange: "NSE" },
  { symbol: "ITC", name: "ITC Limited", sector: "Consumer Goods", exchange: "NSE" },
  { symbol: "BHARTIARTL", name: "Bharti Airtel", sector: "Telecommunication", exchange: "NSE" },
];

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-cyan-500/10 blur-[130px] rounded-full pointer-events-none" />

      <div className="container mx-auto px-4 sm:px-6 pt-16 pb-20">
        {/* Hero Section */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-800/60 bg-cyan-950/40 px-3.5 py-1 text-xs font-semibold text-cyan-400">
            <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
            Indian Equities Intelligence • NSE & BSE
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-100 leading-tight">
            AI Stock Intelligence Platform
          </h1>

          <p className="text-base sm:text-lg text-slate-400 leading-relaxed">
            Real-time Indian market data, automated news ingestion, deterministic financial calculations, and bounded LangGraph conversational research.
          </p>
        </div>

        {/* Search Bar Component */}
        <div className="mb-14">
          <StockSearch autoFocus={true} />
        </div>

        {/* Featured Equities */}
        <div className="max-w-4xl mx-auto mb-16">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
              Featured Indian Blue-Chip Equities
            </h2>
            <span className="text-xs text-slate-500">Click to open dashboard</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {FEATURED_STOCKS.map((stock) => (
              <Link
                key={stock.symbol}
                href={`/stocks/${stock.symbol}`}
                className="group p-4 rounded-2xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 hover:border-cyan-500/50 transition-all shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-slate-100 group-hover:text-cyan-400 transition-colors">
                      {stock.symbol}
                    </span>
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      {stock.exchange}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-1">{stock.name}</p>
                </div>

                <div className="mt-3 flex items-center justify-between text-xs text-cyan-400 font-medium">
                  <span>{stock.sector}</span>
                  <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Core Pillars */}
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 backdrop-blur-sm">
            <div className="h-10 w-10 rounded-xl bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 mb-4">
              <Database className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-slate-100 text-base mb-2">Market Data & Ingestion</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Provider-independent market interface for Upstox & NSE feeds. Automated background ingestion for news and disclosures with SHA-256 deduplication.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 backdrop-blur-sm">
            <div className="h-10 w-10 rounded-xl bg-blue-950 border border-blue-800 flex items-center justify-center text-blue-400 mb-4">
              <Cpu className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-slate-100 text-base mb-2">Deterministic Analytics</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Zero-denominator-safe Python analytics for RSI, SMA, historical volatility, peak-to-trough drawdown, revenue growth, and valuation multiples.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 backdrop-blur-sm">
            <div className="h-10 w-10 rounded-xl bg-emerald-950 border border-emerald-800 flex items-center justify-center text-emerald-400 mb-4">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-slate-100 text-base mb-2">LangGraph RAG & Evaluation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Bounded 10-node research graph with citation validation, prompt-injection defense, and custom benchmark framework measuring Recall@K and latency.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

