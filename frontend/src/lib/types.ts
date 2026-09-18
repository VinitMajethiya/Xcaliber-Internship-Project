export type ReasoningStage = 'plan' | 'tool_call' | 'tool_result' | 'synthesis' | 'error';

export interface ReasoningStep {
  stage: ReasoningStage;
  title: string;
  detail: string;
  payload?: Record<string, any> | null;
}

export interface DatasetProfile {
  dataset_name: string;
  total_rows: number;
  total_columns: number;
  columns: string[];
  dtypes: Record<string, string>;
  date_range: {
    min_date: string;
    max_date: string;
    years: number[];
  };
  categories: Record<string, string[]>;
  metrics_summary: Record<string, {
    min: number;
    max: number;
    mean: number;
    total: number;
  }>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  reasoning_trace?: ReasoningStep[];
  chart_spec?: Record<string, any> | null;
  tool_results?: any[];
  timestamp: string;
  isStreaming?: boolean;
}

export interface ThreadSummary {
  id: string;
  title: string;
  updated_at: string;
}
