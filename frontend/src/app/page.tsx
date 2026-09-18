'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from '../components/Sidebar';
import { MessageBubble } from '../components/MessageBubble';
import { ChatMessage, DatasetProfile, ReasoningStep } from '../lib/types';
import { checkBackendHealth, fetchDatasetProfile, streamChatQuery } from '../lib/api';
import { Send, Sparkles, Loader2, RefreshCw } from 'lucide-react';

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

    // Add initial welcome assistant message
    setMessages([
      {
        id: 'welcome-1',
        role: 'assistant',
        content:
          "👋 **Welcome to Insight Copilot!**\n\nI am your AI Business Intelligence Analyst connected to the **Global Superstore Sales** dataset (51,290 records, 2011–2014).\n\nAsk me about top products, regional sales, margin analysis, seasonal trends, or anomalies — or pick a suggested inquiry from the sidebar to get started!",
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
        content: "Started a fresh conversation session. How can I help you analyze the dataset?",
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

    // Trigger cold-start spinner if response takes >3 seconds
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
                content: '⚠️ An error occurred while communicating with the backend. Please check your connection or server status.',
              };
            }
            return msg;
          })
        );
      },
    });
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0b0f19]">
      {/* Left Sidebar */}
      <Sidebar
        profile={profile}
        backendHealthy={backendHealthy}
        onSelectPrompt={(p) => handleSend(p)}
        onNewChat={handleNewChat}
      />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Top bar */}
        <header className="h-14 px-6 border-b border-gray-800/80 bg-[#0d1322]/80 backdrop-blur-md flex items-center justify-between flex-shrink-0 z-10">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-200">Global Superstore Sales Analysis</span>
            <span className="text-xs text-gray-500 font-mono">[{threadId.slice(0, 16)}...]</span>
          </div>

          <div className="flex items-center gap-3">
            {isWakingUp && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs animate-pulse">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Waking up the backend service…</span>
              </div>
            )}
            <button
              onClick={handleNewChat}
              title="Reset conversation"
              className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Message stream */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-2">
          <div className="max-w-4xl mx-auto">
            {messages.map((msg, idx) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                isLatest={idx === messages.length - 1}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input box */}
        <div className="p-4 border-t border-gray-800/80 bg-[#0d1322] flex-shrink-0">
          <div className="max-w-4xl mx-auto flex gap-2">
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
              placeholder="Ask a question about sales, categories, regions, or trends (e.g., 'Top 5 sub-categories by sales')..."
              disabled={isLoading}
              className="flex-1 bg-gray-900/90 border border-gray-700/80 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-500 outline-none transition-all shadow-inner disabled:opacity-50"
            />
            <button
              onClick={() => handleSend()}
              disabled={isLoading || !inputQuery.trim()}
              className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-800 disabled:text-gray-500 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all disabled:shadow-none"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span>Send</span>
                  <Send className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
