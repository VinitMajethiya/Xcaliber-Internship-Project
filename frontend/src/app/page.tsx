'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from '../components/Sidebar';
import { MessageBubble } from '../components/MessageBubble';
import { ChatMessage, DatasetProfile, ReasoningStep } from '../lib/types';
import { checkBackendHealth, fetchDatasetProfile, streamChatQuery } from '../lib/api';
import {
  Send,
  Loader2,
  RefreshCw,
  Database,
  BarChart3,
  TrendingUp,
  Truck,
  AlertOctagon,
  Sparkles,
} from 'lucide-react';

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isWakingUp, setIsWakingUp] = useState(false);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [threadId, setThreadId] = useState<string>('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wakingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize session & load profile
  useEffect(() => {
    let savedThread = localStorage.getItem('insight_copilot_thread_id');
    if (!savedThread) {
      savedThread = 'thread_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
      localStorage.setItem('insight_copilot_thread_id', savedThread);
    }
    setThreadId(savedThread);

    const initData = async () => {
      const health = await checkBackendHealth();
      setBackendHealthy(health !== null);

      const prof = await fetchDatasetProfile();
      if (prof) {
        setProfile(prof);
      }
    };
    initData();

    // Add initial professional welcome message
    setMessages([
      {
        id: 'welcome-1',
        role: 'assistant',
        content:
          "### 📊 Insight Copilot: Brazilian E-Commerce Analytics\n\n" +
          "I am your dedicated **AI Business Intelligence Analyst** connected to **112,650 verified customer orders** from the Brazilian E-Commerce (Olist) ecosystem (2016–2018).\n\n" +
          "**Analytical Capabilities:**\n" +
          "- **Volume & Revenue Aggregation**: Category rankings, payment methods, and revenue share.\n" +
          "- **Logistics & Delivery Operations**: Freight cost drivers, shipping transit days, and regional bottlenecks.\n" +
          "- **Statistical Intelligence**: Seasonality testing (CV), IQR outlier anomaly detection, and correlation analysis.\n" +
          "- **Interactive Visualizations**: High-contrast Plotly line, bar, scatter, and area distributions.\n\n" +
          "*Select an analytical template from the sidebar or type a plain English business inquiry below.*",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleNewChat = () => {
    const newThread = 'thread_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
    localStorage.setItem('insight_copilot_thread_id', newThread);
    setThreadId(newThread);
    setMessages([
      {
        id: 'welcome-' + Date.now(),
        role: 'assistant',
        content:
          "### 🔄 Fresh Session Initialized\n\nNew conversational checkpoint started with thread ID `" +
          newThread.slice(0, 16) +
          "...`. What dataset metrics or geographic slices would you like to investigate?",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const handleSend = async (queryToSend?: string) => {
    const query = (queryToSend || inputQuery).trim();
    if (!query || isLoading) return;

    const userMessage: ChatMessage = {
      id: 'msg_' + Date.now(),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const assistantTempId = 'msg_ast_' + (Date.now() + 1);
    const initialAssistantMessage: ChatMessage = {
      id: assistantTempId,
      role: 'assistant',
      content: '',
      reasoning_trace: [],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setInputQuery('');
    setIsLoading(true);

    wakingTimeoutRef.current = setTimeout(() => {
      setIsWakingUp(true);
    }, 3000);

    let accumulatedTrace: ReasoningStep[] = [];

    await streamChatQuery({
      query,
      threadId,
      onSession: () => {
        if (wakingTimeoutRef.current) clearTimeout(wakingTimeoutRef.current);
        setIsWakingUp(false);
      },
      onNodeUpdate: (data) => {
        if (wakingTimeoutRef.current) clearTimeout(wakingTimeoutRef.current);
        setIsWakingUp(false);

        if (data.reasoning_trace && Array.isArray(data.reasoning_trace)) {
          accumulatedTrace = data.reasoning_trace;
        }

        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.id === assistantTempId) {
              return {
                ...msg,
                reasoning_trace: accumulatedTrace,
                content: data.final_answer || msg.content,
              };
            }
            return msg;
          })
        );
      },
      onFinalResult: (data) => {
        if (wakingTimeoutRef.current) clearTimeout(wakingTimeoutRef.current);
        setIsWakingUp(false);

        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.id === assistantTempId) {
              return {
                ...msg,
                isStreaming: false,
                content: data.final_answer || msg.content || 'Analysis complete.',
                reasoning_trace: data.reasoning_trace || accumulatedTrace,
                chart_spec: data.chart_spec,
                tool_results: data.tool_results,
              };
            }
            return msg;
          })
        );
        setIsLoading(false);
      },
      onError: (err) => {
        if (wakingTimeoutRef.current) clearTimeout(wakingTimeoutRef.current);
        setIsWakingUp(false);
        setIsLoading(false);

        setMessages((prev) =>
          prev.map((msg) => {
            if (msg.id === assistantTempId) {
              return {
                ...msg,
                isStreaming: false,
                content:
                  '⚠️ **Execution Error**: Unable to complete analysis with the backend service. Check your connection or verify that Render is awake.',
              };
            }
            return msg;
          })
        );
      },
    });
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#080c14] text-slate-100 font-sans">
      {/* Left Domain Navigation Sidebar */}
      <Sidebar
        profile={profile}
        backendHealthy={backendHealthy}
        onSelectPrompt={(p) => handleSend(p)}
        onNewChat={handleNewChat}
      />

      {/* Main Analytical Canvas */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top Control Bar */}
        <header className="h-14 px-6 border-b border-slate-800/80 bg-[#0d131f]/80 backdrop-blur-md flex items-center justify-between flex-shrink-0 z-10">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-slate-200">
              Olist E-Commerce Analytics Workspace
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 rounded bg-slate-800/80 px-2 py-0.5 text-[10px] font-mono text-slate-400 border border-slate-700/50">
              <Database className="h-3 w-3 text-blue-400" />
              <span>112.6k rows</span>
            </span>
            <span className="hidden md:inline-flex text-xs text-slate-500 font-mono">
              [thread: {threadId.slice(0, 10)}...]
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            {isWakingUp && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs animate-pulse font-mono">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Waking backend service…</span>
              </div>
            )}
            <button
              onClick={handleNewChat}
              title="Reset conversation session"
              className="flex items-center gap-1.5 rounded-lg border border-slate-700/70 bg-slate-800/60 px-2.5 py-1.5 text-xs text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
              <span className="hidden sm:inline font-mono text-[11px]">New Session</span>
            </button>
          </div>
        </header>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-2">
          <div className="max-w-4xl mx-auto">
            {messages.map((msg, idx) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                isLatest={idx === messages.length - 1}
                onSelectPrompt={(p) => handleSend(p)}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Command Bar Input Box */}
        <div className="p-4 border-t border-slate-800/80 bg-[#0d131f] flex-shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="relative flex items-center rounded-xl border border-slate-700/80 bg-slate-900/90 shadow-inner focus-within:border-blue-500 transition-all">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask an analytical question (e.g., 'What were the top 3 product categories by payment value?')..."
                disabled={isLoading}
                className="w-full bg-transparent px-4 py-3.5 text-sm text-slate-100 placeholder-slate-500 outline-none disabled:opacity-50"
              />

              <div className="pr-2 flex items-center gap-2">
                <span className="hidden sm:inline font-mono text-[10px] text-slate-400">
                  Enter ↵
                </span>
                <button
                  onClick={() => handleSend()}
                  disabled={isLoading || !inputQuery.trim()}
                  className="rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white transition-all hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed flex items-center gap-1.5 shadow-md shadow-blue-600/20"
                >
                  {isLoading ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <>
                      <span>Execute</span>
                      <Send className="w-3 h-3" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
