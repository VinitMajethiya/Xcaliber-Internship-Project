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
  Terminal,
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

    // Initial executive welcome
    setMessages([
      {
        id: 'welcome-1',
        role: 'assistant',
        content:
          "### Olist E-Commerce Analytics Workspace\n\n" +
          "Connected to **112,650 validated customer transactions** (Brazilian E-Commerce, 2016–2018).\n\n" +
          "**Analytical Scope:**\n" +
          "- **Volume & Financials**: Category rankings, payment methods, installments, and revenue share.\n" +
          "- **Logistics & Regional Performance**: Freight metrics, delivery transit days, and cross-state comparisons (e.g. SP vs RJ).\n" +
          "- **Statistical Intelligence**: Seasonality testing (CV), IQR anomaly detection, and correlation analysis.\n" +
          "- **Visualizations**: Dynamic Plotly distributions (line, bar, scatter, area).\n\n" +
          "*Select a template from the left panel or type an analytical query below.*",
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
          "### Fresh Analysis Thread Initialized\n\nCheckpoint registered with thread UUID `" +
          newThread.slice(0, 16) +
          "...`. Specify an analytical inquiry or metric slice to begin.",
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
                  '⚠️ **Execution Error**: Unable to complete analysis with the backend service. Please check your connection.',
              };
            }
            return msg;
          })
        );
      },
    });
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0d0f12] text-[#f1f3f5] font-sans">
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
        <header className="h-12 px-5 border-b border-[#1c212a] bg-[#101319] flex items-center justify-between flex-shrink-0 z-10">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-semibold text-[#f1f3f5] tracking-tight">
              Olist Analytics Workspace
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 rounded border border-[#202532] bg-[#141720] px-2 py-0.5 text-[10px] font-mono text-[#8b95a5]">
              <Database className="h-3 w-3 text-slate-400" />
              <span>112,650 rows</span>
            </span>
            <span className="hidden md:inline-flex text-[11px] text-[#556070] font-mono">
              [thread: {threadId.slice(0, 10)}...]
            </span>
          </div>

          <div className="flex items-center gap-2">
            {isWakingUp && (
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded border border-amber-800/40 bg-amber-950/30 text-amber-400 text-[10.5px] animate-pulse font-mono">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Waking backend…</span>
              </div>
            )}
            <button
              onClick={handleNewChat}
              title="Reset conversation session"
              className="flex items-center gap-1.5 rounded border border-[#242a36] bg-[#141720] px-2.5 py-1 text-xs text-[#9ba4b3] hover:bg-[#1c212c] hover:text-white transition-colors"
            >
              <RefreshCw className="w-3 h-3 text-slate-400" />
              <span className="hidden sm:inline font-mono text-[10.5px]">Reset</span>
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
        <div className="p-3.5 border-t border-[#1c212a] bg-[#101319] flex-shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="relative flex items-center rounded border border-[#252b37] bg-[#141720] focus-within:border-[#384356] transition-all">
              <div className="pl-3.5 flex items-center text-[#556070]">
                <Terminal className="h-3.5 w-3.5" />
              </div>
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
                className="w-full bg-transparent px-3 py-2.5 text-xs text-[#f1f3f5] placeholder-[#5a6575] outline-none disabled:opacity-50"
              />

              <div className="pr-2 flex items-center gap-1.5">
                <span className="hidden sm:inline font-mono text-[9.5px] text-[#556070]">
                  Enter ↵
                </span>
                <button
                  onClick={() => handleSend()}
                  disabled={isLoading || !inputQuery.trim()}
                  className="rounded border border-[#2b3342] bg-[#1c212b] px-3 py-1.5 text-xs font-medium text-[#c4cbd4] transition-all hover:bg-[#252c3a] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 shadow-sm"
                >
                  {isLoading ? (
                    <Loader2 className="w-3 h-3 animate-spin text-slate-300" />
                  ) : (
                    <>
                      <span className="font-mono text-[11px]">Run</span>
                      <Send className="w-2.5 h-2.5" />
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
