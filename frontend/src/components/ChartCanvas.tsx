'use client';

import React, { useEffect, useRef, useState } from 'react';
import { BarChart2, Maximize2, Minimize2, AlertCircle, Download } from 'lucide-react';

interface ChartCanvasProps {
  spec: Record<string, any> | null;
  title?: string;
}

export const ChartCanvas: React.FC<ChartCanvasProps> = ({ spec, title }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);

  useEffect(() => {
    if (!spec || !containerRef.current) return;

    let isMounted = true;

    const renderPlot = async () => {
      try {
        setRenderError(null);
        const PlotlyModule = await import('plotly.js-dist-min');
        const Plotly = PlotlyModule.default || PlotlyModule;

        if (!isMounted || !containerRef.current) return;

        const data = spec.data || [];
        const baseLayout = spec.layout || {};

        const mergedLayout = {
          ...baseLayout,
          title: undefined, // Handled in component header
          autosize: true,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'rgba(18, 22, 29, 0.5)',
          font: {
            family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            size: 11,
            color: '#828e9f',
            ...baseLayout.font,
          },
          margin: {
            l: 50,
            r: 25,
            t: 15,
            b: 40,
            ...baseLayout.margin,
          },
        };

        const config = {
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: [
            'lasso2d',
            'select2d',
            'sendDataToCloud',
            'hoverCompareCartesian',
          ],
        };

        await (Plotly as any).newPlot(containerRef.current, data, mergedLayout, config);

        const handleResize = () => {
          if (containerRef.current && (Plotly as any).Plots) {
            (Plotly as any).Plots.resize(containerRef.current);
          }
        };

        window.addEventListener('resize', handleResize);

        return () => {
          window.removeEventListener('resize', handleResize);
          if (containerRef.current && (Plotly as any).purge) {
            (Plotly as any).purge(containerRef.current);
          }
        };
      } catch (err: any) {
        console.error('Failed to render Plotly chart:', err);
        if (isMounted) {
          setRenderError(err?.message || 'Unable to render chart visual');
        }
      }
    };

    renderPlot();

    return () => {
      isMounted = false;
    };
  }, [spec, isExpanded, title]);

  const handleDownloadPNG = async () => {
    if (!containerRef.current) return;
    try {
      const PlotlyModule = await import('plotly.js-dist-min');
      const Plotly = PlotlyModule.default || PlotlyModule;
      await (Plotly as any).downloadImage(containerRef.current, {
        format: 'png',
        width: 1200,
        height: 700,
        filename: `${(title || 'insight_chart').toLowerCase().replace(/\s+/g, '_')}`,
      });
    } catch (e) {
      console.error('Export PNG failed:', e);
    }
  };

  if (!spec) return null;

  return (
    <div
      className={`my-3.5 rounded border border-[#1e232e] bg-[#0c0f14] p-3 shadow-sm transition-all duration-200 ${
        isExpanded ? 'ring-1 ring-[#3b82f6]' : ''
      }`}
    >
      {/* Chart Header Bar */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#1b202a]">
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded bg-[#161a22] text-slate-300">
            <BarChart2 className="h-3.5 w-3.5" />
          </div>
          <span className="text-xs font-semibold text-[#d1d7e0]">
            {title || spec.layout?.title?.text || 'Visualization'}
          </span>
          <span className="rounded border border-[#1e232e] bg-[#12151c] px-1.5 py-0.2 text-[9px] font-mono uppercase tracking-wider text-[#7a8799]">
            Dynamic Spec
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handleDownloadPNG}
            title="Download Chart as PNG"
            className="flex items-center gap-1 rounded border border-[#222733] bg-[#12151c] px-2 py-0.5 text-[10.5px] font-mono text-[#8b95a5] transition-colors hover:bg-[#181c25] hover:text-[#f1f3f5]"
          >
            <Download className="h-3 w-3 text-slate-400" />
            <span className="hidden sm:inline">Export PNG</span>
          </button>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? 'Collapse chart' : 'Expand chart'}
            className="rounded border border-[#222733] bg-[#12151c] p-1 text-[#8b95a5] hover:bg-[#181c25] hover:text-[#f1f3f5] transition-colors"
          >
            {isExpanded ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
          </button>
        </div>
      </div>

      {/* Error state */}
      {renderError ? (
        <div className="flex items-center gap-2 p-2.5 text-xs text-rose-300 bg-rose-950/20 border border-rose-900/30 rounded">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{renderError}</span>
        </div>
      ) : (
        /* Plotly DOM Container */
        <div
          ref={containerRef}
          style={{ height: isExpanded ? '520px' : '330px' }}
          className="w-full transition-all duration-200"
        />
      )}
    </div>
  );
};
