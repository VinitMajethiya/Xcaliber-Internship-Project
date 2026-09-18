'use client';

import React, { useState } from 'react';
import { ReasoningStep } from '../lib/types';
import { ChevronDown, ChevronRight, Brain, Wrench, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';

interface ReasoningPanelProps {
  steps: ReasoningStep[];
  defaultExpanded?: boolean;
}

export const ReasoningPanel: React.FC<ReasoningPanelProps> = ({ steps, defaultExpanded = false }) => {
  const [isOpen, setIsOpen] = useState(defaultExpanded);

  if (!steps || steps.length === 0) return null;

  const getStageIcon = (stage: string) => {
    switch (stage) {
      case 'plan':
        return <Brain className="w-4 h-4 text-indigo-400" />;
      case 'tool_call':
        return <Wrench className="w-4 h-4 text-amber-400" />;
      case 'tool_result':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'synthesis':
        return <Sparkles className="w-4 h-4 text-sky-400" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-rose-400" />;
      default:
        return <Brain className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStageBadge = (stage: string) => {
    switch (stage) {
      case 'plan':
        return 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20';
      case 'tool_call':
        return 'bg-amber-500/10 text-amber-300 border-amber-500/20';
      case 'tool_result':
        return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
      case 'synthesis':
        return 'bg-sky-500/10 text-sky-300 border-sky-500/20';
      case 'error':
        return 'bg-rose-500/10 text-rose-300 border-rose-500/20';
      default:
        return 'bg-gray-500/10 text-gray-300 border-gray-500/20';
    }
  };

  return (
    <div className="my-2 border border-gray-800/80 rounded-xl bg-gray-900/40 backdrop-blur-md overflow-hidden transition-all duration-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3.5 py-2 text-xs font-medium text-gray-300 hover:text-white hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-indigo-400 animate-pulse" />
          <span>Reasoning & Execution Trace</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            {steps.length} {steps.length === 1 ? 'step' : 'steps'}
          </span>
        </div>
        {isOpen ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
      </button>

      {isOpen && (
        <div className="px-3.5 py-3 border-t border-gray-800/60 space-y-2.5 text-xs">
          {steps.map((step, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-gray-950/60 border border-gray-800/50 flex flex-col gap-1.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-medium text-gray-200">
                  {getStageIcon(step.stage)}
                  <span>{step.title}</span>
                </div>
                <span className={`px-2 py-0.5 text-[10px] rounded-full border uppercase tracking-wider ${getStageBadge(step.stage)}`}>
                  {step.stage}
                </span>
              </div>
              <p className="text-gray-400 text-xs leading-relaxed whitespace-pre-wrap pl-6">
                {step.detail}
              </p>
              {step.payload && Object.keys(step.payload).length > 0 && (
                <div className="mt-1 pl-6">
                  <pre className="p-2 rounded bg-gray-900/90 text-[11px] font-mono text-gray-400 overflow-x-auto border border-gray-800">
                    {JSON.stringify(step.payload, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
