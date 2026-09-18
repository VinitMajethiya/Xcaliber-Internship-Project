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
    if (stage === 'plan') return <GitCommit className="h-3.5 w-3.5 text-blue-400" />;
    if (stage === 'tool_call') {
      if (title.includes('query_data')) return <Database className="h-3.5 w-3.5 text-amber-400" />;
      if (title.includes('make_chart')) return <BarChart2 className="h-3.5 w-3.5 text-purple-400" />;
      return <Terminal className="h-3.5 w-3.5 text-amber-400" />;
    }
    if (stage === 'tool_result') return <Terminal className="h-3.5 w-3.5 text-emerald-400" />;
    if (stage === 'synthesis') return <Sparkles className="h-3.5 w-3.5 text-sky-400" />;
    if (stage === 'error') return <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />;
    return <GitCommit className="h-3.5 w-3.5 text-slate-400" />;
  };

  const getStageBadge = (stage: string) => {
    switch (stage) {
      case 'plan':
        return 'bg-blue-500/10 text-blue-300 border-blue-500/20';
      case 'tool_call':
        return 'bg-amber-500/10 text-amber-300 border-amber-500/20';
      case 'tool_result':
        return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
      case 'synthesis':
        return 'bg-sky-500/10 text-sky-300 border-sky-500/20';
      case 'error':
        return 'bg-rose-500/10 text-rose-300 border-rose-500/20';
      default:
        return 'bg-slate-500/10 text-slate-300 border-slate-500/20';
    }
  };

  return (
    <div className="my-2.5 overflow-hidden rounded-lg border border-slate-800 bg-[#090d16]/90 shadow-md">
      {/* Header bar */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-medium text-slate-300 transition-colors hover:bg-slate-800/40"
      >
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded bg-blue-500/10 text-blue-400">
            <GitCommit className="h-3.5 w-3.5" />
          </div>
          <span className="font-semibold text-slate-200">Query Execution Plan</span>
          <span className="rounded border border-slate-800 bg-slate-900 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
            {steps.length} {steps.length === 1 ? 'stage' : 'stages'}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-slate-400">
          <span className="text-[10px] uppercase tracking-wider font-mono">
            {isOpen ? 'Collapse' : 'Inspect'}
          </span>
          {isOpen ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        </div>
      </button>

      {/* Expanded Step Trace */}
      {isOpen && (
        <div className="divide-y divide-slate-800/80 border-t border-slate-800 bg-[#070a12] px-3 py-2 text-[11.5px]">
          {steps.map((step, idx) => (
            <div key={idx} className="py-2.5 first:pt-1 last:pb-1">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="mt-0.5">{getStageIcon(step.stage, step.title)}</div>
                  <span className="font-medium text-slate-200">{step.title}</span>
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
                    className="flex items-center gap-1 rounded bg-slate-900 px-1.5 py-0.5 text-[10px] font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  >
                    <Code2 className="h-3 w-3 text-blue-400" />
                    <span>{activeStepIndex === idx ? 'Hide Params' : 'Params'}</span>
                  </button>
                )}
              </div>

              {step.detail && (
                <p className="mt-1 pl-5.5 text-slate-400 leading-relaxed text-[11px]">
                  {step.detail}
                </p>
              )}

              {/* Payload viewer */}
              {activeStepIndex === idx && step.payload && (
                <div className="mt-2 ml-5 overflow-x-auto rounded border border-slate-800/80 bg-black/60 p-2 font-mono text-[10.5px] text-emerald-400">
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
