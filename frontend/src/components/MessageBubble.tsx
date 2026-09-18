'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '../lib/types';
import { ReasoningPanel } from './ReasoningPanel';
import { ChartCanvas } from './ChartCanvas';
import { DataTable } from './DataTable';
import {
  User,
  Sparkles,
  Loader2,
  Copy,
  Check,
  Table as TableIcon,
  CornerDownRight,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
  isLatest?: boolean;
  onSelectPrompt?: (prompt: string) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isLatest = false,
  onSelectPrompt,
}) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [showRawData, setShowRawData] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Find any tabular query results in tool_results
  const rawTableData = React.useMemo(() => {
    if (!message.tool_results || !Array.isArray(message.tool_results)) return null;
    const queryResult = message.tool_results.find(
      (r) => r && (r.tool === 'query_data' || (r.data && Array.isArray(r.data) && r.data.length > 0))
    );
    if (queryResult && Array.isArray(queryResult.data) && queryResult.data.length > 0) {
      return {
        data: queryResult.data,
        summary: queryResult.summary || 'Query Records',
      };
    }
    return null;
  }, [message.tool_results]);

  // Contextual analytical follow-up chips
  const followUpChips = React.useMemo(() => {
    if (isUser || message.isStreaming || !message.content) return [];
    const lower = message.content.toLowerCase();
    const chips: string[] = [];

    if (lower.includes('category') || lower.includes('product') || lower.includes('payment')) {
      if (!lower.includes('plot monthly') && !message.chart_spec) {
        chips.push('Plot monthly payment value for 2017');
      }
      chips.push('Summarize anything unusual or anomalous in payment values');
    }
    if (lower.includes('são paulo') || lower.includes('sp')) {
      chips.push('What about RJ?');
      chips.push('Compare SP and RJ customer states by freight value and delivery time');
    }
    if (lower.includes('trend') || lower.includes('season')) {
      chips.push('Is there a seasonal trend in bed_bath_table orders?');
    }
    return Array.from(new Set(chips)).slice(0, 2);
  }, [isUser, message.content, message.isStreaming, message.chart_spec]);

  return (
    <div className={`group relative my-4 flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Assistant Avatar */}
      {!isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-600/10 text-blue-400 mt-1 shadow-sm">
          <Sparkles className="h-4 w-4" />
        </div>
      )}

      <div className={`flex max-w-[90%] md:max-w-[82%] flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Bubble container */}
        <div
          className={`relative rounded-xl px-4 py-3.5 text-sm leading-relaxed transition-all duration-150 ${
            isUser
              ? 'rounded-br-sm bg-blue-600 text-white shadow-md shadow-blue-600/10'
              : 'rounded-bl-sm border border-slate-800 bg-[#0d1322] text-slate-200 shadow-md'
          }`}
        >
          {/* Query Execution Plan (Reasoning Trace) */}
          {!isUser && message.reasoning_trace && message.reasoning_trace.length > 0 && (
            <ReasoningPanel steps={message.reasoning_trace} defaultExpanded={isLatest} />
          )}

          {/* Assistant Executive Report (Markdown Rendered) */}
          {!isUser ? (
            <div className="analyst-prose">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ node, ...props }) => (
                    <div className="analyst-table-container">
                      <table className="analyst-table" {...props} />
                    </div>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          ) : (
            <div className="whitespace-pre-wrap font-sans text-[13.5px]">{message.content}</div>
          )}

          {/* Interactive Plotly Chart */}
          {!isUser && message.chart_spec && <ChartCanvas spec={message.chart_spec} />}

          {/* Tabular Raw Data Inspector Drawer */}
          {!isUser && rawTableData && (
            <div className="mt-3 pt-2 border-t border-slate-800/80">
              <button
                onClick={() => setShowRawData(!showRawData)}
                className="flex items-center gap-1.5 rounded border border-slate-800 bg-slate-900/90 px-2.5 py-1 text-[11px] font-mono text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <TableIcon className="h-3 w-3 text-blue-400" />
                <span>{showRawData ? 'Hide Underlying Data Grid' : `View Data Grid (${rawTableData.data.length} rows)`}</span>
              </button>

              {showRawData && <DataTable data={rawTableData.data} title={rawTableData.summary} />}
            </div>
          )}

          {/* Streaming loader indicator */}
          {message.isStreaming && !message.content && (
            <div className="flex items-center gap-2 py-1.5 text-xs text-blue-400">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span className="font-mono text-[11px]">Executing query plan and aggregating records...</span>
            </div>
          )}

          {/* Hover Action Bar (Copy & Timestamp) */}
          {!isUser && message.content && (
            <div className="mt-2.5 flex items-center justify-between pt-1 text-[10px] text-slate-500">
              <span className="font-mono">{message.timestamp}</span>
              <button
                onClick={handleCopy}
                title="Copy response to clipboard"
                className="flex items-center gap-1 text-slate-400 hover:text-slate-200 transition-colors"
              >
                {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          )}
        </div>

        {/* User Timestamp */}
        {isUser && (
          <span className="mt-1 px-1 font-mono text-[10px] text-slate-500">
            {message.timestamp}
          </span>
        )}

        {/* Contextual Smart Analytical Follow-Up Chips */}
        {!isUser && isLatest && followUpChips.length > 0 && onSelectPrompt && (
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span className="flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-slate-400">
              <CornerDownRight className="h-3 w-3 text-blue-400" />
              <span>Suggested Analysis:</span>
            </span>
            {followUpChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => onSelectPrompt(chip)}
                className="flex items-center gap-1 rounded-full border border-slate-800 bg-slate-900/90 px-2.5 py-1 text-[11px] text-slate-300 hover:border-blue-500/40 hover:bg-slate-800 hover:text-white transition-all shadow-sm"
              >
                <TrendingUp className="h-2.5 w-2.5 text-blue-400" />
                <span>{chip}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-slate-300 mt-1 shadow-sm">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
};
