'use client';

import React from 'react';
import { ChatMessage } from '../lib/types';
import { ReasoningPanel } from './ReasoningPanel';
import { User, Sparkles, Loader2 } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
  isLatest?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isLatest = false }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3.5 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center flex-shrink-0 mt-1">
          <Sparkles className="w-4 h-4 text-indigo-400" />
        </div>
      )}

      <div className={`max-w-[85%] md:max-w-[75%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-indigo-600 text-white rounded-br-sm shadow-lg shadow-indigo-600/20'
              : 'bg-[#141d2e] text-gray-200 border border-gray-800 rounded-bl-sm shadow-md'
          }`}
        >
          {/* Reasoning trace collapsible */}
          {!isUser && message.reasoning_trace && message.reasoning_trace.length > 0 && (
            <ReasoningPanel steps={message.reasoning_trace} defaultExpanded={isLatest} />
          )}

          {/* Main message text */}
          <div className="whitespace-pre-wrap font-sans text-[13.5px]">
            {message.content}
          </div>

          {/* Streaming loader indicator */}
          {message.isStreaming && !message.content && (
            <div className="flex items-center gap-2 text-xs text-indigo-400 py-1">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Analyzing query and exploring dataset...</span>
            </div>
          )}
        </div>

        <span className="text-[10px] text-gray-500 mt-1 px-1">
          {message.timestamp}
        </span>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-gray-800 border border-gray-700 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-4 h-4 text-gray-300" />
        </div>
      )}
    </div>
  );
};
