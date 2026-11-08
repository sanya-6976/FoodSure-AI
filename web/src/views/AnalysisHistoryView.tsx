import React, { useState } from 'react';
import {
  Search,
  Filter,
  FileText,
  Download,
  Trash2,
  Calendar,
  Microscope,
  CheckCircle2,
  AlertTriangle,
  ArrowUpDown,
  RefreshCw,
} from 'lucide-react';
import { HistoryRecord, Language, AnalysisResult, NavPage } from '../types';
import { translations } from '../i18n';

interface AnalysisHistoryViewProps {
  history: HistoryRecord[];
  lang: Language;
  onViewReport: (result: AnalysisResult) => void;
  onDeleteRecord: (id: string) => Promise<void>;
  onNavigate: (page: NavPage) => void;
}

export const AnalysisHistoryView: React.FC<AnalysisHistoryViewProps> = ({
  history,
  lang,
  onViewReport,
  onDeleteRecord,
  onNavigate,
}) => {
  const t = translations[lang];

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pure' | 'adulterated'>('all');
  const [classFilter, setClassFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date_desc' | 'date_asc' | 'level_desc'>('date_desc');

  // Filter and sort
  const filtered = history
    .filter((item) => {
      const matchSearch =
        item.sample_id.toLowerCase().includes(search.toLowerCase()) ||
        item.sample_name.toLowerCase().includes(search.toLowerCase()) ||
        item.batch_id.toLowerCase().includes(search.toLowerCase());
      const matchStatus =
        statusFilter === 'all'
          ? true
          : statusFilter === 'pure'
          ? item.is_pure
          : !item.is_pure;
      const matchClass =
        classFilter === 'all' ? true : item.predicted_class === classFilter;
      return matchSearch && matchStatus && matchClass;
    })
    .sort((a, b) => {
      if (sortBy === 'date_desc') {
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      }
      if (sortBy === 'date_asc') {
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      }
      if (sortBy === 'level_desc') {
        return (b.predicted_percentage || 0) - (a.predicted_percentage || 0);
      }
      return 0;
    });

  const handleExportCsv = () => {
    const headers = [
      'Record_ID',
      'Timestamp',
      'Sample_ID',
      'Batch_ID',
      'Predicted_Class',
      'Regression_Estimate',
      'Status',
    ];
    const rows = filtered.map((item) => [
      item.id,
      item.timestamp,
      item.sample_id,
      item.batch_id,
      item.predicted_class,
      item.predicted_percentage !== null ? item.predicted_percentage : '',
      item.status,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `foodsure_analysis_history_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* ── Top Header ─────────────────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-[#EEF5F0] text-[#1E5232] text-[11px] font-semibold mb-1.5">
            Audit Trail
          </div>
          <h2 className="text-[20px] font-bold text-[#112619] tracking-tight">
            Analysis History & Verified Screening Records
          </h2>
          <p className="text-[13px] text-[#557161] mt-0.5">
            Total of {history.length} physical and uploaded turmeric spectroscopic screenings recorded.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCsv}
            disabled={filtered.length === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#F6FAF7] hover:bg-[#EEF5F0] disabled:opacity-50 text-[#1A4228] border border-[#DCE5DF] text-[12px] font-semibold rounded-xl transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={() => onNavigate('analyze')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[#153822] hover:bg-[#0E2818] text-white text-[12px] font-bold rounded-xl shadow-xs transition-colors"
          >
            <Microscope className="w-3.5 h-3.5" />
            <span>New Analysis</span>
          </button>
        </div>
      </div>

      {/* ── Filter Bar ──────────────────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-xl border border-[#E3E9E5] p-4 shadow-xs flex flex-wrap items-center justify-between gap-3 text-[12px]">
        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-[#738E7F] absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Sample or Batch ID..."
            className="w-full pl-9 pr-3 py-1.5 bg-[#F6FAF7] border border-[#DCE5DF] rounded-lg text-[12px] text-[#1A3324] placeholder-[#81998C] focus:outline-none focus:border-[#153822] focus:bg-white transition-all"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#6C8578] font-semibold text-[11px]">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="px-2 py-1 bg-[#F6FAF7] border border-[#DCE5DF] rounded-lg text-[12px] text-[#1B3B28] font-medium focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="pure">Pure Turmeric (0%)</option>
              <option value="adulterated">Adulterated (1%–9%)</option>
            </select>
          </div>

          {/* Class Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-[#6C8578] font-semibold text-[11px]">Class:</span>
            <select
              value={classFilter}
              onChange={(e) => setClassFilter(e.target.value)}
              className="px-2 py-1 bg-[#F6FAF7] border border-[#DCE5DF] rounded-lg text-[12px] text-[#1B3B28] font-medium focus:outline-none"
            >
              <option value="all">All Tiers</option>
              <option value="0%">0%</option>
              <option value="1%">1%</option>
              <option value="2%">2%</option>
              <option value="3%">3%</option>
              <option value="5%">5%</option>
              <option value="7%">7%</option>
              <option value="9%">9%</option>
            </select>
          </div>

          {/* Sort Control */}
          <div className="flex items-center gap-1.5">
            <ArrowUpDown className="w-3.5 h-3.5 text-[#6C8578]" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-2 py-1 bg-[#F6FAF7] border border-[#DCE5DF] rounded-lg text-[12px] text-[#1B3B28] font-medium focus:outline-none"
            >
              <option value="date_desc">Newest First</option>
              <option value="date_asc">Oldest First</option>
              <option value="level_desc">Highest Adulteration</option>
            </select>
          </div>
        </div>
      </div>

      {/* ── Table Container ─────────────────────────────────────────────── */}
      <div className="bg-[#FFFFFF] rounded-2xl border border-[#E3E9E5] shadow-xs overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-[#698476] text-[13px]">
            No analysis records match your current filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[12px]">
              <thead>
                <tr className="bg-[#FAFDFB] border-b border-[#E3E9E5] text-[#557161] font-bold">
                  <th className="py-3 px-4">Record ID</th>
                  <th className="py-3 px-4">Sample / Batch</th>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Classification</th>
                  <th className="py-3 px-4">RF Regressor (% w/w)</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EEF3F0]">
                {filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-[#F9FCFA] transition-colors">
                    <td className="py-3 px-4 font-mono text-[11px] text-[#698476]">
                      {item.id}
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-bold text-[#142C1D]">{item.sample_id}</div>
                      <div className="text-[10px] text-[#637E6F]">{item.batch_id}</div>
                    </td>

                    <td className="py-3 px-4 text-[#4B6656]">
                      {new Date(item.timestamp).toLocaleDateString()}{' '}
                      <span className="text-[10px] text-[#7E998B]">
                        {new Date(item.timestamp).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </td>

                    <td className="py-3 px-4 font-bold text-[#153822]">
                      {item.predicted_class}
                    </td>

                    <td className="py-3 px-4 font-mono font-bold text-[#1F412B]">
                      {item.predicted_percentage !== null
                        ? `${item.predicted_percentage.toFixed(2)}%`
                        : '—'}
                    </td>

                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                          item.is_pure
                            ? 'bg-[#E5F5EB] text-[#1E7D46]'
                            : 'bg-[#FFF3E0] text-[#B86B14]'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            item.is_pure ? 'bg-[#1E7D46]' : 'bg-[#B86B14]'
                          }`}
                        />
                        {item.status}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => onViewReport(item.result_data)}
                          className="px-2.5 py-1 bg-[#EEF5F0] hover:bg-[#E0EDE4] text-[#164126] font-semibold rounded-lg text-[11px] transition-colors inline-flex items-center gap-1"
                        >
                          <FileText className="w-3 h-3" />
                          <span>Report</span>
                        </button>

                        <button
                          onClick={() => onDeleteRecord(item.id)}
                          title="Delete from local history"
                          className="p-1 text-[#8F2626] hover:bg-[#FDF2F2] rounded-lg transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
