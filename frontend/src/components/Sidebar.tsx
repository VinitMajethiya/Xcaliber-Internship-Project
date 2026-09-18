'use client';

import React from 'react';
import { DatasetProfile } from '../lib/types';
import {
  Database,
  Calendar,
  Layers,
  PlusCircle,
  Activity,
  BarChart3,
  TrendingUp,
  Truck,
  AlertOctagon,
  Server,
  Cpu,
} from 'lucide-react';

interface SidebarProps {
  profile: DatasetProfile | null;
  backendHealthy: boolean | null;
  onSelectPrompt: (prompt: string) => void;
  onNewChat: () => void;
}

const CATEGORIZED_PROMPTS = [
  {
    category: 'Revenue & Rankings',
    icon: TrendingUp,
    prompts: [
      'What were the top 3 product categories by payment value?',
      'Plot monthly payment value for 2017',
    ],
  },
  {
    category: 'Logistics & Geography',
    icon: Truck,
    prompts: [
      'Compare SP and RJ customer states by freight value and delivery time',
      'What was the total revenue in São Paulo?',
    ],
  },
  {
    category: 'Anomalies & Seasonality',
    icon: AlertOctagon,
    prompts: [
      'Is there a seasonal trend in bed_bath_table orders?',
      'Summarize anything unusual or anomalous in payment values',
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  profile,
  backendHealthy,
  onSelectPrompt,
  onNewChat,
}) => {
  return (
    <aside className="w-80 h-full border-r border-slate-800/80 bg-[#0d131f] flex flex-col justify-between flex-shrink-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-blue-600/10 border border-blue-500/30 flex items-center justify-center">
              <BarChart3 className="h-4 w-4 text-blue-400" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-white tracking-wide">Insight Copilot</h1>
              <p className="text-[10.5px] font-mono text-slate-400">BI Analyst Workspace</p>
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
            <Activity className="h-3 w-3" />
            <span>{backendHealthy === true ? 'Live' : backendHealthy === false ? 'Offline' : 'Connecting'}</span>
          </div>
        </div>

        {/* New Session Button */}
        <button
          onClick={onNewChat}
          className="mt-3.5 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800/70 px-3 py-2 text-xs font-medium text-slate-200 transition-colors hover:bg-slate-700 hover:text-white shadow-sm"
        >
          <PlusCircle className="h-3.5 w-3.5 text-blue-400" />
          <span>New Analysis Thread</span>
        </button>
      </div>

      {/* Categorized Starters */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        <div className="flex items-center justify-between text-[11px] font-mono uppercase tracking-wider text-slate-400">
          <span>Inquiry Templates</span>
        </div>

        {CATEGORIZED_PROMPTS.map((group, gIdx) => {
          const Icon = group.icon;
          return (
            <div key={gIdx} className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400">
                <Icon className="h-3.5 w-3.5 text-blue-400" />
                <span>{group.category}</span>
              </div>
              <div className="space-y-1">
                {group.prompts.map((prompt, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => onSelectPrompt(prompt)}
                    className="w-full rounded-md border border-slate-800/80 bg-slate-900/50 px-2.5 py-1.5 text-left text-[11.5px] text-slate-300 transition-all hover:border-blue-500/40 hover:bg-slate-800/60 hover:text-white"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Dataset & Architecture Telemetry Card */}
      <div className="p-3.5 border-t border-slate-800/80 bg-[#090d16] text-[11px] space-y-2">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-slate-400">
          <span className="flex items-center gap-1">
            <Database className="h-3 w-3 text-blue-400" />
            <span>Dataset Telemetry</span>
          </span>
          <span className="text-emerald-400 font-semibold">112,650 Rows</span>
        </div>

        <div className="rounded border border-slate-800 bg-slate-900/80 p-2 space-y-1 font-mono text-[10.5px]">
          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1 text-slate-400">
              <Layers className="h-3 w-3 text-slate-500" /> Schema:
            </span>
            <span>19 Columns (Olist)</span>
          </div>

          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1 text-slate-400">
              <Calendar className="h-3 w-3 text-slate-500" /> Period:
            </span>
            <span>2016 – 2018</span>
          </div>

          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1 text-slate-400">
              <Server className="h-3 w-3 text-slate-500" /> Checkpoint:
            </span>
            <span className="text-blue-400">Neon Postgres</span>
          </div>

          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1 text-slate-400">
              <Cpu className="h-3 w-3 text-slate-500" /> Model:
            </span>
            <span className="text-emerald-400">gemini-3.6-flash</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
