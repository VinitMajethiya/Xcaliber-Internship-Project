'use client';

import React from 'react';
import { DatasetProfile } from '../lib/types';
import {
  Database,
  Calendar,
  Layers,
  Plus,
  Activity,
  BarChart2,
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
    <aside className="w-80 h-full border-r border-[#1e232d] bg-[#101319] flex flex-col justify-between flex-shrink-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#1c212a]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded border border-[#272e3a] bg-[#171b23] flex items-center justify-center text-slate-300">
              <BarChart2 className="h-4 w-4 text-slate-300" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-[#f1f3f5] tracking-tight">Insight Copilot</h1>
              <p className="text-[10.5px] font-mono text-[#768294]">BI Workspace</p>
            </div>
          </div>

          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono border ${
              backendHealthy === true
                ? 'bg-emerald-950/30 text-emerald-400 border-emerald-800/40'
                : backendHealthy === false
                ? 'bg-rose-950/30 text-rose-400 border-rose-800/40'
                : 'bg-amber-950/30 text-amber-400 border-amber-800/40'
            }`}
          >
            <Activity className="h-3 w-3" />
            <span>{backendHealthy === true ? 'ONLINE' : backendHealthy === false ? 'OFFLINE' : 'CONNECTING'}</span>
          </div>
        </div>

        {/* New Session Button */}
        <button
          onClick={onNewChat}
          className="mt-3.5 flex w-full items-center justify-center gap-1.5 rounded border border-[#262c38] bg-[#151921] px-3 py-1.5 text-xs font-medium text-[#c4cbd4] transition-colors hover:bg-[#1d222d] hover:text-white shadow-sm"
        >
          <Plus className="h-3.5 w-3.5 text-slate-400" />
          <span>New Analysis Thread</span>
        </button>
      </div>

      {/* Categorized Starters */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        <div className="text-[10px] font-mono uppercase tracking-wider text-[#636f82]">
          Inquiry Templates
        </div>

        {CATEGORIZED_PROMPTS.map((group, gIdx) => {
          const Icon = group.icon;
          return (
            <div key={gIdx} className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#7e8b9f]">
                <Icon className="h-3.5 w-3.5 text-slate-400" />
                <span>{group.category}</span>
              </div>
              <div className="space-y-1">
                {group.prompts.map((prompt, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => onSelectPrompt(prompt)}
                    className="w-full rounded border border-[#1e232d] bg-[#13161d] px-2.5 py-1.5 text-left text-[11.5px] text-[#9ba4b3] transition-all hover:border-[#2f3747] hover:bg-[#181c25] hover:text-white"
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
      <div className="p-3.5 border-t border-[#1c212a] bg-[#0c0e13] text-[11px] space-y-2">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-[#636f82]">
          <span className="flex items-center gap-1">
            <Database className="h-3 w-3 text-slate-400" />
            <span>Dataset Telemetry</span>
          </span>
          <span className="text-[#8ba2be] font-medium">112,650 Rows</span>
        </div>

        <div className="rounded border border-[#1e232d] bg-[#11141a] p-2 space-y-1 font-mono text-[10.5px]">
          <div className="flex items-center justify-between text-[#8b95a5]">
            <span className="flex items-center gap-1 text-[#616c7d]">
              <Layers className="h-3 w-3" /> Schema:
            </span>
            <span className="text-[#c4cbd4]">19 Cols (Olist)</span>
          </div>

          <div className="flex items-center justify-between text-[#8b95a5]">
            <span className="flex items-center gap-1 text-[#616c7d]">
              <Calendar className="h-3 w-3" /> Period:
            </span>
            <span className="text-[#c4cbd4]">2016 – 2018</span>
          </div>

          <div className="flex items-center justify-between text-[#8b95a5]">
            <span className="flex items-center gap-1 text-[#616c7d]">
              <Server className="h-3 w-3" /> Checkpoint:
            </span>
            <span className="text-slate-300">Neon Postgres</span>
          </div>

          <div className="flex items-center justify-between text-[#8b95a5]">
            <span className="flex items-center gap-1 text-[#616c7d]">
              <Cpu className="h-3 w-3" /> Model:
            </span>
            <span className="text-emerald-400">gemini-3.6-flash</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
