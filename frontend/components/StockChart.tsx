"use client";

import { useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  CartesianGrid,
} from "recharts";
import { PriceBar } from "@/lib/api";

interface StockChartProps {
  bars: PriceBar[];
  symbol: string;
  currency?: string;
  isPositive?: boolean;
}

export default function StockChart({ bars, symbol, currency = "INR", isPositive = true }: StockChartProps) {
  const [range, setRange] = useState<number>(60);

  const formattedData = bars.slice(-range).map((b) => {
    const d = new Date(b.timestamp);
    return {
      date: `${d.getDate()} ${d.toLocaleString("en-US", { month: "short" })}`,
      close: b.close,
      open: b.open,
      high: b.high,
      low: b.low,
      volume: b.volume,
    };
  });

  const minPrice = formattedData.length > 0 ? Math.min(...formattedData.map((d) => d.low)) * 0.995 : 0;
  const maxPrice = formattedData.length > 0 ? Math.max(...formattedData.map((d) => d.high)) * 1.005 : 100;

  const strokeColor = isPositive ? "#10b981" : "#ef4444";
  const fillColor = isPositive ? "#10b981" : "#ef4444";

  return (
    <div className="w-full rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <h3 className="font-semibold text-slate-100 flex items-center gap-2">
            Historical Price Performance ({symbol})
          </h3>
          <p className="text-xs text-slate-400">Daily OHLCV trading bars with volume</p>
        </div>

        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          {[
            { label: "1M", days: 22 },
            { label: "3M", days: 60 },
            { label: "6M", days: 120 },
            { label: "ALL", days: 365 },
          ].map((item) => (
            <button
              key={item.label}
              onClick={() => setRange(item.days)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors ${
                range === item.days
                  ? "bg-slate-800 text-cyan-400 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {formattedData.length > 0 ? (
        <div className="space-y-2">
          {/* Main Price Area Chart */}
          <div className="h-64 sm:h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={fillColor} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={fillColor} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: "#334155" }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  domain={[minPrice, maxPrice]}
                  stroke="#64748b"
                  fontSize={11}
                  tickLine={false}
                  axisLine={{ stroke: "#334155" }}
                  tickFormatter={(val) => `₹${val.toFixed(0)}`}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="rounded-xl border border-slate-700 bg-slate-950/95 p-3 shadow-xl backdrop-blur-md text-xs">
                          <p className="font-bold text-slate-200 mb-1">{data.date}</p>
                          <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-slate-300">
                            <div>Close: <span className="font-semibold text-slate-100">₹{data.close.toFixed(2)}</span></div>
                            <div>Open: <span className="font-semibold text-slate-100">₹{data.open.toFixed(2)}</span></div>
                            <div>High: <span className="font-semibold text-emerald-400">₹{data.high.toFixed(2)}</span></div>
                            <div>Low: <span className="font-semibold text-red-400">₹{data.low.toFixed(2)}</span></div>
                            <div className="col-span-2 text-slate-400 mt-1">Volume: {data.volume.toLocaleString()}</div>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke={strokeColor}
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#priceGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Volume Sub-Chart */}
          <div className="h-20 w-full pt-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={formattedData} margin={{ top: 0, right: 10, left: -15, bottom: 0 }}>
                <YAxis hide={true} />
                <Bar dataKey="volume" fill="#3b82f6" opacity={0.5} radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
          No historical price bars available for charting.
        </div>
      )}
    </div>
  );
}

