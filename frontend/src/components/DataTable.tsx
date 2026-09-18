'use client';

import React, { useState, useMemo } from 'react';
import { Table, Download, Search, ChevronLeft, ChevronRight, FileSpreadsheet } from 'lucide-react';

interface DataTableProps {
  data: Array<Record<string, any>>;
  title?: string;
}

export const DataTable: React.FC<DataTableProps> = ({ data, title = 'Query Dataset' }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const columns = useMemo(() => {
    if (!data || data.length === 0) return [];
    return Object.keys(data[0]);
  }, [data]);

  const filteredData = useMemo(() => {
    if (!searchTerm.trim()) return data;
    const lower = searchTerm.toLowerCase();
    return data.filter((row) =>
      Object.values(row).some((val) =>
        val !== null && val !== undefined && String(val).toLowerCase().includes(lower)
      )
    );
  }, [data, searchTerm]);

  const totalPages = Math.ceil(filteredData.length / pageSize);
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, currentPage, pageSize]);

  const downloadCSV = () => {
    if (!data || data.length === 0) return;
    const headers = columns.join(',');
    const rows = data.map((row) =>
      columns
        .map((col) => {
          const val = row[col];
          if (val === null || val === undefined) return '""';
          const stringVal = String(val).replace(/"/g, '""');
          return `"${stringVal}"`;
        })
        .join(',')
    );
    const csvContent = [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `${title.toLowerCase().replace(/\s+/g, '_')}_export.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!data || data.length === 0) return null;

  return (
    <div className="my-3 rounded-lg border border-slate-800 bg-[#090d16] p-3 text-xs shadow-lg">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 mb-2.5 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded bg-blue-500/10 text-blue-400">
            <FileSpreadsheet className="h-3.5 w-3.5" />
          </div>
          <span className="font-semibold text-slate-200">{title}</span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
            {data.length} records
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Quick Search */}
          <div className="relative">
            <Search className="absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Filter data..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="h-7 w-32 rounded border border-slate-800 bg-slate-900/90 pl-7 pr-2 text-[11px] text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none md:w-44"
            />
          </div>

          {/* Export CSV Button */}
          <button
            onClick={downloadCSV}
            title="Download records as CSV"
            className="flex h-7 items-center gap-1.5 rounded border border-slate-700 bg-slate-800/80 px-2.5 font-medium text-slate-300 transition-colors hover:bg-slate-700 hover:text-white"
          >
            <Download className="h-3 w-3 text-blue-400" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table grid */}
      <div className="overflow-x-auto rounded border border-slate-800/80">
        <table className="w-full text-left font-mono">
          <thead className="bg-[#0f172a] text-[10px] uppercase tracking-wider text-slate-400">
            <tr>
              {columns.map((col) => (
                <th key={col} className="border-b border-slate-800 px-3 py-2 font-semibold">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-[11px] text-slate-300">
            {paginatedData.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                {columns.map((col) => {
                  const val = row[col];
                  const isNumber = typeof val === 'number';
                  return (
                    <td
                      key={col}
                      className={`px-3 py-1.5 ${isNumber ? 'text-right text-emerald-400' : ''}`}
                    >
                      {val !== null && val !== undefined
                        ? isNumber
                          ? val.toLocaleString(undefined, { maximumFractionDigits: 2 })
                          : String(val)
                        : '-'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 text-[11px] text-slate-400">
          <span>
            Page {currentPage} of {totalPages} ({filteredData.length} matches)
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="rounded p-1 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="rounded p-1 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
