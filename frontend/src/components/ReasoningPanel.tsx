'use client';

import React, { useState } from 'react';
import { ReasoningStep } from '../lib/types';
import {
  ChevronDown,
  ChevronRight,
  GitCommit,
  Terminal,
  Database,
  BarChart2,
  Sparkles,
  AlertTriangle,
  Code2,
} from 'lucide-react';

interface ReasoningPanelProps {
  steps: ReasoningStep[];
  defaultExpanded?: boolean;
}

export const ReasoningPanel: React.FC<ReasoningPanelProps> = ({ steps, defaultExpanded = false }) => {
  const [isOpen, setIsOpen] = useState(defaultExpanded);
  const [activeStepIndex, setActiveStepIndex] = useState<number | null>(null);

  if (!steps || steps.length === 0) return null;

  const getStageIcon = (stage: string, title: string) => {
    if (stage === 'plan') return <GitCommit className="h-3.5 w-3.5 text-slate-400" />;
    if (stage === 'tool_call') {
      if (title.includes('query_data')) return <Database className="h-3.5 w-3.5 text-slate-300" />;
      if (title.includes('make_chart')) return <BarChart2 className="h-3.5 w-3.5 text-slate-300" />;
      return <Terminal className="h-3.5 w-3.5 text-slate-300" />;
    }
    if (stage === 'tool_result') return <Terminal className="h-3.5 w-3.5 text-emerald-400" />;
    if (stage === 'synthesis') return <Sparkles className="h-3.5 w-3.5 text-slate-300" />;
    if (stage === 'error') return <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />;
    return <GitCommit className="h-3.5 w-3.5 text-slate-400" />;
  };

  const getStageBadge = (stage: string) => {
    switch (stage) {
      case 'plan':
        return 'bg-[#181c24] text-[#8ea0b5] border-[#252c38]';
      case 'tool_call':
        return 'bg-[#1a1c17] text-[#c9b77d] border-[#2f3120]';
      case 'tool_result':
        return 'bg-[#111c16] text-[#7ec29a] border-[#1f382a]';
      case 'synthesis':
        return 'bg-[#161a24] text-[#8da2c0] border-[#232d3d]';
      case 'error':
        return 'bg-[#211414] text-[#d97c7c] border-[#3d2020]';
      default:
        return 'bg-[#16181f] text-[#838c9c] border-[#232731]';
    }
  };

  return (
    <div className="my-2.5 overflow-hidden rounded border border-[#1e232e] bg-[#0e1016] shadow-sm">
      {/* Header bar */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between px-3 py-1.5 text-left text-xs font-medium text-[#8b95a5] transition-colors hover:bg-[#141720]"
      >
        <div className="flex items-center gap-2">
          <div className="flex h-4 w-4 items-center justify-center rounded bg-[#171a22] text-[#8b95a5]">
            <GitCommit className="h-3 w-3" />
          </div>
          <span className="font-medium text-[#c4cbd4] text-[11.5px]">Execution Plan</span>
          <span className="rounded border border-[#1e232e] bg-[#12151c] px-1.5 py-0.2 text-[9.5px] font-mono text-[#6e7a8c]">
            {steps.length} {steps.length === 1 ? 'step' : 'steps'}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-[#5e697a]">
          <span className="text-[9.5px] uppercase tracking-wider font-mono">
            {isOpen ? 'Close' : 'Inspect'}
          </span>
          {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        </div>
      </button>

      {/* Expanded Step Trace */}
      {isOpen && (
        <div className="divide-y divide-[#1b1f28] border-t border-[#1b1f28] bg-[#0a0c10] px-3 py-2 text-[11.5px]">
          {steps.map((step, idx) => (
            <div key={idx} className="py-2 first:pt-1 last:pb-1">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="mt-0.5">{getStageIcon(step.stage, step.title)}</div>
                  <span className="font-medium text-[#c4cbd4]">{step.title}</span>
                  <span
                    className={`rounded border px-1.5 py-0.2 text-[9px] font-mono uppercase tracking-wider ${getStageBadge(
                      step.stage
                    )}`}
                  >
                    {step.stage.replace('_', ' ')}
                  </span>
                </div>

                {step.payload && (
                  <button
                    onClick={() => setActiveStepIndex(activeStepIndex === idx ? null : idx)}
                    className="flex items-center gap-1 rounded border border-[#222733] bg-[#12151c] px-1.5 py-0.5 text-[9.5px] font-mono text-[#7a8799] hover:text-[#c4cbd4] hover:bg-[#181c25]"
                  >
                    <Code2 className="h-3 w-3 text-slate-400" />
                    <span>{activeStepIndex === idx ? 'Hide Params' : 'Params'}</span>
                  </button>
                )}
              </div>

              {step.detail && (
                <p className="mt-1 pl-5.5 text-[#7a8799] leading-relaxed text-[11px]">
                  {step.detail}
                </p>
              )}

              {/* Payload viewer */}
              {activeStepIndex === idx && step.payload && (
                <div className="mt-2 ml-5 overflow-x-auto rounded border border-[#1e232d] bg-[#0d0f14] p-2 font-mono text-[10px] text-[#93c5fd]">
                  <pre>{JSON.stringify(step.payload, null, 2)}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
