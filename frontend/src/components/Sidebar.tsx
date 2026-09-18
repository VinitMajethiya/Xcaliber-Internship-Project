'use client';

import React from 'react';
import { DatasetProfile } from '../lib/types';
import {
  Database,
  Calendar,
  Layers,
  Globe2,
  PlusCircle,
  HelpCircle,
  Activity,
  BarChart3,
} from 'lucide-react';

interface SidebarProps {
  profile: DatasetProfile | null;
  backendHealthy: boolean | null;
  onSelectPrompt: (prompt: string) => void;
  onNewChat: () => void;
}

const STARTER_PROMPTS = [
  'What are the top 5 product categories by total sales in SP?',
  'Compare average delivery days and freight value across customer states.',
  'Analyze quarterly revenue trends across 2017 and 2018.',
  'Is there a correlation between delivery delay and customer review scores?',
];

export const Sidebar: React.FC<SidebarProps> = ({
  profile,
  backendHealthy,
  onSelectPrompt,
  onNewChat,
}) => {
  return (
    <aside className="w-80 h-full border-r border-gray-800/80 bg-[#0d1322] flex flex-col justify-between flex-shrink-0">
      {/* Header & Brand */}
      <div className="p-4 border-b border-gray-800/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-white tracking-wide">Insight Copilot</h1>
              <p className="text-[11px] text-gray-400">AI BI Analyst Agent</p>
            </div>
          </div>

          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium border ${
              backendHealthy === true
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : backendHealthy === false
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}
          >
            <Activity className="w-3 h-3" />
            <span>{backendHealthy === true ? 'Online' : backendHealthy === false ? 'Offline' : 'Connecting'}</span>
          </div>
        </div>

        <button
          onClick={onNewChat}
          className="mt-4 w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-sm transition-colors"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>New Analysis</span>
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 text-xs">
        {/* Dataset Profile Card */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-1.5 text-gray-400 uppercase font-semibold text-[10px] tracking-wider">
            <Database className="w-3 h-3 text-indigo-400" />
            <span>Dataset Overview</span>
          </div>

          {profile ? (
            <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-800 space-y-2 text-gray-300">
              <div className="flex justify-between items-center pb-1.5 border-b border-gray-800/50">
                <span className="text-gray-400">Dataset</span>
                <span className="font-medium text-white text-[11px] truncate max-w-[150px]">{profile.dataset_name}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400 flex items-center gap-1">
                  <Layers className="w-3 h-3 text-gray-500" /> Total Records
                </span>
                <span className="font-semibold text-indigo-300">{profile.total_rows.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400 flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-gray-500" /> Time Span
                </span>
                <span className="text-gray-300 text-[11px]">
                  {profile.date_range.years.join(', ')}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400 flex items-center gap-1">
                  <Globe2 className="w-3 h-3 text-gray-500" /> States & Categories
                </span>
                <span className="text-gray-300 text-[11px]">
                  {(profile.categories.customer_state?.length || profile.categories.Region?.length || 0)} states / {(profile.categories.category?.length || profile.categories.Category?.length || 0)} categories
                </span>
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-gray-900/40 border border-gray-800/60 text-gray-400 text-center animate-pulse">
              Loading dataset profile...
            </div>
          )}
        </div>

        {/* Starter Prompts */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-gray-400 uppercase font-semibold text-[10px] tracking-wider">
            <HelpCircle className="w-3 h-3 text-amber-400" />
            <span>Suggested Inquiries</span>
          </div>
          <div className="space-y-1.5">
            {STARTER_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => onSelectPrompt(prompt)}
                className="w-full text-left p-2.5 rounded-lg bg-gray-900/40 hover:bg-gray-800/70 border border-gray-800/60 hover:border-indigo-500/40 text-gray-300 hover:text-white transition-all text-[11.5px] leading-relaxed"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Footer info */}
      <div className="p-3.5 border-t border-gray-800/60 text-[10px] text-gray-500 flex items-center justify-between">
        <span>LangGraph 1.2.x Agent</span>
        <span>FastAPI + Next.js</span>
      </div>
    </aside>
  );
};
