"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2, TrendingUp, Clock, AlertCircle } from "lucide-react";
import { searchStocks, StockSearchResult } from "@/lib/api";

interface StockSearchProps {
  onSelect?: (stock: StockSearchResult) => void;
  autoFocus?: boolean;
}

export default function StockSearch({ onSelect, autoFocus = false }: StockSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [exchange, setExchange] = useState<string | undefined>(undefined);
  const [results, setResults] = useState<StockSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentStocks, setRecentStocks] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("recent_stocks");
      if (stored) {
        setRecentStocks(JSON.parse(stored));
      }
    } catch {
      // ignore localStorage errors
    }
  }, []);

  const saveRecent = (symbol: string) => {
    try {
      const updated = [symbol, ...recentStocks.filter((s) => s !== symbol)].slice(0, 5);
      setRecentStocks(updated);
      localStorage.setItem("recent_stocks", JSON.stringify(updated));
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setError(null);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await searchStocks(query, exchange);
        setResults(data);
        if (data.length === 0) {
          setError(`No equities found matching "${query}" on ${exchange || "NSE/BSE"}`);
        }
      } catch (err: any) {
        setError(err.message || "Failed to search stocks");
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query, exchange]);

  const handleSelect = (stock: StockSearchResult) => {
    saveRecent(stock.symbol);
    if (onSelect) {
      onSelect(stock);
    } else {
      router.push(`/stocks/${stock.symbol}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && query.trim()) {
      e.preventDefault();
      if (results.length > 0) {
        handleSelect(results[0]);
      } else {
        const cleanSym = query.trim().toUpperCase();
        handleSelect({
          instrument_id: `${exchange || "NSE"}_EQ|${cleanSym}`,
          company_id: "",
          name: `${cleanSym} Limited`,
          symbol: cleanSym,
          exchange: exchange || "NSE",
          sector: "Equities",
          industry: "Equities",
          currency: "INR",
        });
      }
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="relative">
        <div className="flex items-center rounded-2xl border border-slate-700/80 bg-slate-900/90 shadow-2xl backdrop-blur-md px-4 py-3 focus-within:border-cyan-500 focus-within:ring-2 focus-within:ring-cyan-500/20 transition-all">
          <Search className="h-5 w-5 text-slate-400 mr-3 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type any stock symbol or name (e.g. TONBO, ZOMATO, TATAPOWER, RELIANCE) & press Enter..."
            autoFocus={autoFocus}
            className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm sm:text-base outline-none"
          />
          {loading && <Loader2 className="h-5 w-5 text-cyan-400 animate-spin shrink-0 ml-2" />}

          <div className="flex items-center gap-1 ml-3 border-l border-slate-800 pl-3 shrink-0">
            {["ALL", "NSE", "BSE"].map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setExchange(ex === "ALL" ? undefined : ex)}
                className={`px-2 py-1 text-xs font-semibold rounded-md transition-colors ${
                  (ex === "ALL" && !exchange) || exchange === ex
                    ? "bg-cyan-500 text-slate-950"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
              >
                {ex}
              </button>
            ))}
            {query.trim().length > 0 && (
              <button
                type="button"
                onClick={() => {
                  if (results.length > 0) handleSelect(results[0]);
                  else {
                    const clean = query.trim().toUpperCase();
                    handleSelect({
                      instrument_id: `${exchange || "NSE"}_EQ|${clean}`,
                      company_id: "",
                      name: `${clean} Limited`,
                      symbol: clean,
                      exchange: exchange || "NSE",
                      sector: "Equities",
                      industry: "Equities",
                      currency: "INR",
                    });
                  }
                }}
                className="ml-1 px-3 py-1 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-md transition-colors"
              >
                Go
              </button>
            )}
          </div>
        </div>

        {/* Results Dropdown */}
        {query.trim().length > 0 && (
          <div className="absolute left-0 right-0 mt-2 z-50 rounded-2xl border border-slate-800 bg-slate-900/95 shadow-2xl backdrop-blur-xl overflow-hidden max-h-96 overflow-y-auto">
            <div className="p-2 border-b border-slate-800/80">
              <button
                onClick={() => {
                  const cleanSym = query.trim().toUpperCase();
                  handleSelect({
                    instrument_id: `${exchange || "NSE"}_EQ|${cleanSym}`,
                    company_id: "",
                    name: `Open Instant Intelligence for ${cleanSym}`,
                    symbol: cleanSym,
                    exchange: exchange || "NSE",
                    sector: "Equities",
                    industry: "Equities",
                    currency: "INR",
                  });
                }}
                className="w-full flex items-center justify-between p-2.5 rounded-xl bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-800/60 transition-colors text-left group"
              >
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-cyan-400 shrink-0" />
                  <span className="text-xs sm:text-sm font-semibold text-cyan-300">
                    Open instant intelligence dashboard for &quot;{query.trim().toUpperCase()}&quot;
                  </span>
                </div>
                <span className="text-[10px] text-cyan-300 font-bold px-2 py-0.5 rounded bg-cyan-900 border border-cyan-700 shrink-0">
                  Press Enter ↵
                </span>
              </button>
            </div>

            {results.length > 0 ? (
              <div className="p-2 divide-y divide-slate-800/60">
                {results.map((stock) => (
                  <button
                    key={`${stock.exchange}-${stock.symbol}`}
                    onClick={() => handleSelect(stock)}
                    className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/80 transition-colors text-left group"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-100 group-hover:text-cyan-400 transition-colors">
                          {stock.symbol}
                        </span>
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          {stock.exchange}
                        </span>
                        <span className="text-xs text-slate-400 hidden sm:inline">• {stock.sector}</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{stock.name}</p>
                    </div>

                    {stock.last_price !== undefined && stock.last_price !== null && (
                      <div className="text-right shrink-0">
                        <div className="text-sm font-semibold text-slate-100">
                          ₹{stock.last_price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </div>
                        <div className="text-[11px] text-slate-500">{stock.currency}</div>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            ) : error ? (
              <div className="p-6 text-center text-sm text-slate-400 flex flex-col items-center gap-2">
                <AlertCircle className="h-6 w-6 text-amber-500" />
                <p>{error}</p>
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* Recently Viewed Stocks */}
      {recentStocks.length > 0 && query.trim().length === 0 && (
        <div className="mt-4 flex items-center gap-2 flex-wrap">
          <span className="flex items-center gap-1 text-xs text-slate-500 font-medium">
            <Clock className="h-3 w-3" /> Recent:
          </span>
          {recentStocks.map((sym) => (
            <button
              key={sym}
              onClick={() => router.push(`/stocks/${sym}`)}
              className="rounded-lg bg-slate-900 border border-slate-800 px-2.5 py-1 text-xs font-medium text-slate-300 hover:border-cyan-500 hover:text-cyan-400 transition-colors flex items-center gap-1"
            >
              <TrendingUp className="h-3 w-3 text-cyan-500" />
              {sym}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

