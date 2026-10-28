"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Loader2,
  Bot,
  User,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  HelpCircle,
  Clock,
  Sparkles,
} from "lucide-react";
import { askQuestion, AskQuestionResponse, Citation } from "@/lib/api";

interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  responseObj?: AskQuestionResponse;
  timestamp: string;
}

interface ResearchChatProps {
  symbol: string;
  companyName: string;
  instrumentId: string;
}

export default function ResearchChat({ symbol, companyName, instrumentId }: ResearchChatProps) {
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: "welcome",
      role: "assistant",
      content: `Hello! I am your AI Research Assistant for ${companyName} (${symbol}). Ask me about latest quotes, technical indicators (RSI, SMA), FY24 financials, or recent news and announcements.`,
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (questionText?: string) => {
    const q = (questionText || input).trim();
    if (!q || loading) return;

    const userMsg: MessageItem = {
      id: String(Date.now()),
      role: "user",
      content: q,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response = await askQuestion(q, symbol, conversationId);
      setConversationId(response.conversation_id);

      const assistantMsg: MessageItem = {
        id: String(Date.now() + 1),
        role: "assistant",
        content: response.direct_answer,
        responseObj: response,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || "Failed to retrieve evidence-backed answer");
    } finally {
      setLoading(false);
    }
  };

  const sampleQuestions = [
    `What is the current trading quote and day range for ${symbol}?`,
    `What is the 14-day RSI and 20-day SMA for ${symbol}?`,
    `What was ${symbol}'s reported revenue, profit, and PE ratio?`,
    `What are the recent news and corporate announcements for ${symbol}?`,
  ];

  return (
    <div className="flex flex-col h-[650px] rounded-2xl border border-slate-800 bg-slate-900/80 backdrop-blur-md overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950/70 px-5 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/20">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              LangGraph Research Assistant
              <span className="flex items-center gap-1 rounded-full bg-emerald-950 border border-emerald-800/60 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
                <CheckCircle2 className="h-3 w-3" /> Grounded
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Active Context: <span className="font-semibold text-slate-200">{symbol}</span> • Verifiable Citations
            </p>
          </div>
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="h-8 w-8 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 shrink-0 mt-0.5">
                <Bot className="h-4 w-4" />
              </div>
            )}

            <div
              className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed shadow-md ${
                msg.role === "user"
                  ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-tr-none"
                  : "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none"
              }`}
            >
              <div className="whitespace-pre-line font-medium">{msg.content}</div>

              {/* Supporting Facts Breakdown */}
              {msg.responseObj && msg.responseObj.supporting_facts.length > 0 && (
                <div className="mt-3.5 pt-3 border-t border-slate-800/80">
                  <div className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                    <Sparkles className="h-3 w-3" /> Supporting Numerical Facts:
                  </div>
                  <ul className="space-y-1 text-xs text-slate-300">
                    {msg.responseObj.supporting_facts.map((fact, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-cyan-400 shrink-0">•</span>
                        <span>{fact}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Verified Citations */}
              {msg.responseObj && msg.responseObj.citations.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-slate-800/80">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                    <ExternalLink className="h-3 w-3" /> Source Citations:
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {msg.responseObj.citations.map((c, idx) => (
                      <a
                        key={idx}
                        href={c.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 rounded bg-slate-900 border border-slate-800 px-2 py-1 text-[11px] text-cyan-300 hover:text-cyan-200 hover:border-slate-700 transition-colors"
                      >
                        <span className="font-medium truncate max-w-[150px]">{c.publisher || c.title}</span>
                        <ExternalLink className="h-2.5 w-2.5 opacity-70" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Limitations / Stale Warnings */}
              {msg.responseObj && msg.responseObj.limitations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-slate-800/80">
                  <div className="flex items-center gap-1 text-[11px] font-medium text-amber-400/90">
                    <AlertTriangle className="h-3 w-3 shrink-0" />
                    <span>{msg.responseObj.limitations.join(" • ")}</span>
                  </div>
                </div>
              )}

              <div className="mt-2 text-[10px] text-slate-500 text-right">{msg.timestamp}</div>
            </div>

            {msg.role === "user" && (
              <div className="h-8 w-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300 shrink-0 mt-0.5">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="h-8 w-8 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 shrink-0">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl rounded-tl-none bg-slate-950 border border-slate-800 p-4 shadow-md flex items-center gap-3 text-slate-400 text-sm">
              <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
              <span>Routing question through LangGraph research workflow...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-900/60 bg-red-950/30 p-3 text-xs text-red-400 flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Questions */}
      {messages.length <= 2 && (
        <div className="px-4 py-2 border-t border-slate-800/60 bg-slate-950/40">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <HelpCircle className="h-3 w-3" /> Suggested Research Prompts:
          </p>
          <div className="flex gap-1.5 overflow-x-auto pb-1">
            {sampleQuestions.map((sq, i) => (
              <button
                key={i}
                onClick={() => handleSend(sq)}
                className="rounded-lg bg-slate-900 border border-slate-800 px-2.5 py-1 text-xs text-slate-300 hover:border-cyan-500 hover:text-cyan-400 transition-colors whitespace-nowrap"
              >
                {sq}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3.5 border-t border-slate-800 bg-slate-950/80 flex items-center gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Ask about ${symbol}'s quote, RSI, revenue, news, or comparison...`}
          disabled={loading}
          className="flex-1 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2.5 text-white font-medium shadow-md shadow-cyan-500/20 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </button>
      </form>
    </div>
  );
}

