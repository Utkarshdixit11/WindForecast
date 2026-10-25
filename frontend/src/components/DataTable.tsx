import React, { useState, useMemo } from 'react';
import { Download, Search, ChevronLeft, ChevronRight, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { PeriodAnalysisRecord, PeriodStatus } from '../types';

interface DataTableProps {
  records: PeriodAnalysisRecord[];
}

export const DataTable: React.FC<DataTableProps> = ({ records }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // Filtered dataset
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      // Status filter
      if (statusFilter !== 'ALL' && r.status !== statusFilter) {
        return false;
      }
      // Search term (date, period, or timestamp)
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const matchesDate = r.settlement_date.toLowerCase().includes(term);
        const matchesPeriod = String(r.settlement_period).includes(term);
        const matchesTime = r.delivery_start_time.toLowerCase().includes(term);
        const matchesStatus = r.status.toLowerCase().includes(term);
        if (!matchesDate && !matchesPeriod && !matchesTime && !matchesStatus) {
          return false;
        }
      }
      return true;
    });
  }, [records, statusFilter, searchTerm]);

  // Pagination
  const totalPages = Math.ceil(filteredRecords.length / pageSize) || 1;
  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRecords.slice(start, start + pageSize);
  }, [filteredRecords, currentPage, pageSize]);

  // Export to CSV
  const handleExportCsv = () => {
    const headers = [
      'delivery_start_time_utc',
      'delivery_start_time_uk',
      'settlement_date',
      'settlement_period',
      'decision_cutoff_time_utc',
      'forecast_publish_time_utc',
      'selected_forecast_mw',
      'actual_generation_mw',
      'signed_error_mw',
      'absolute_error_mw',
      'status',
    ];

    const rows = filteredRecords.map((r) => [
      r.delivery_start_time,
      r.delivery_start_time_uk,
      r.settlement_date,
      r.settlement_period,
      r.decision_cutoff_time,
      r.forecast_publish_time || '',
      r.forecast_generation_mw ?? '',
      r.actual_generation_mw ?? '',
      r.error_mw ?? '',
      r.absolute_error_mw ?? '',
      r.status,
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `wind_forecast_accuracy_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderStatusBadge = (status: PeriodStatus) => {
    switch (status) {
      case 'VALID_PAIR':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <CheckCircle className="w-3 h-3 mr-1 text-emerald-600" />
            Valid Pair
          </span>
        );
      case 'MISSING_FORECAST':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3 h-3 mr-1 text-amber-600" />
            Missing Forecast
          </span>
        );
      case 'MISSING_ACTUAL':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-semibold bg-rose-50 text-rose-800 border border-rose-200">
            <Clock className="w-3 h-3 mr-1 text-rose-600" />
            Missing Actual
          </span>
        );
      case 'MISSING_BOTH':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-semibold bg-slate-100 text-slate-700">
            Missing Both
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Table Header and Controls */}
      <div className="p-4 sm:p-5 border-b border-slate-100">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">
              Settlement Period Audit Table
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Inspect forecast publication time, cutoff deadlines, outturns, and signed error for each 30-minute block
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search date or period..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="text-xs pl-8 pr-3 py-1.5 border border-slate-300 rounded-md shadow-2xs focus:ring-1 focus:ring-brand-600 focus:border-brand-600"
              />
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="text-xs px-2.5 py-1.5 border border-slate-300 rounded-md bg-white shadow-2xs focus:ring-1 focus:ring-brand-600"
            >
              <option value="ALL">All Statuses</option>
              <option value="VALID_PAIR">Valid Pairs Only</option>
              <option value="MISSING_FORECAST">Missing Forecast Only</option>
              <option value="MISSING_ACTUAL">Missing Actual Only</option>
            </select>

            {/* Export CSV */}
            <button
              onClick={handleExportCsv}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-md shadow-2xs transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
          <thead className="bg-slate-50 text-slate-600 font-semibold">
            <tr>
              <th scope="col" className="px-3.5 py-3">Delivery Time (UTC)</th>
              <th scope="col" className="px-3.5 py-3">Period</th>
              <th scope="col" className="px-3.5 py-3">Forecast Published</th>
              <th scope="col" className="px-3.5 py-3">Decision Cutoff</th>
              <th scope="col" className="px-3.5 py-3 text-right">Forecast (MW)</th>
              <th scope="col" className="px-3.5 py-3 text-right">Actual (MW)</th>
              <th scope="col" className="px-3.5 py-3 text-right">Signed Error</th>
              <th scope="col" className="px-3.5 py-3 text-right">Abs Error</th>
              <th scope="col" className="px-3.5 py-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {paginatedRecords.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-slate-500">
                  No records match the current filter criteria.
                </td>
              </tr>
            ) : (
              paginatedRecords.map((r, index) => {
                const isOver = (r.error_mw ?? 0) > 0;
                const isUnder = (r.error_mw ?? 0) < 0;

                return (
                  <tr key={`${r.delivery_start_time}-${index}`} className="hover:bg-slate-50/80 transition-colors">
                    {/* Delivery Time */}
                    <td className="px-3.5 py-2.5 font-mono whitespace-nowrap text-slate-900 font-medium">
                      {r.delivery_start_time.replace('T', ' ').slice(0, 16)}Z
                    </td>

                    {/* Settlement Period */}
                    <td className="px-3.5 py-2.5 font-mono text-slate-600 whitespace-nowrap">
                      SP {r.settlement_period}
                    </td>

                    {/* Published */}
                    <td className="px-3.5 py-2.5 font-mono text-slate-500 whitespace-nowrap">
                      {r.forecast_publish_time ? (
                        <span>{r.forecast_publish_time.replace('T', ' ').slice(0, 16)}Z</span>
                      ) : (
                        <span className="text-slate-400 italic">None prior to cutoff</span>
                      )}
                    </td>

                    {/* Cutoff */}
                    <td className="px-3.5 py-2.5 font-mono text-slate-500 whitespace-nowrap">
                      {r.decision_cutoff_time.replace('T', ' ').slice(0, 16)}Z
                    </td>

                    {/* Forecast MW */}
                    <td className="px-3.5 py-2.5 font-mono text-right font-medium text-brand-700 whitespace-nowrap">
                      {r.forecast_generation_mw !== null ? r.forecast_generation_mw.toLocaleString() : '—'}
                    </td>

                    {/* Actual MW */}
                    <td className="px-3.5 py-2.5 font-mono text-right font-medium text-teal-800 whitespace-nowrap">
                      {r.actual_generation_mw !== null ? r.actual_generation_mw.toLocaleString() : '—'}
                    </td>

                    {/* Signed Error */}
                    <td
                      className={`px-3.5 py-2.5 font-mono text-right font-semibold whitespace-nowrap ${
                        isOver ? 'text-amber-700' : isUnder ? 'text-sky-700' : 'text-slate-600'
                      }`}
                    >
                      {r.error_mw !== null ? (isOver ? `+${r.error_mw.toLocaleString()}` : r.error_mw.toLocaleString()) : '—'}
                    </td>

                    {/* Absolute Error */}
                    <td className="px-3.5 py-2.5 font-mono text-right text-slate-700 whitespace-nowrap">
                      {r.absolute_error_mw !== null ? r.absolute_error_mw.toLocaleString() : '—'}
                    </td>

                    {/* Status Badge */}
                    <td className="px-3.5 py-2.5 text-center whitespace-nowrap">
                      {renderStatusBadge(r.status)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3.5 border-t border-slate-100 bg-slate-50 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
        <div>
          Showing <span className="font-semibold text-slate-800">{filteredRecords.length > 0 ? (currentPage - 1) * pageSize + 1 : 0}</span> to{' '}
          <span className="font-semibold text-slate-800">{Math.min(currentPage * pageSize, filteredRecords.length)}</span> of{' '}
          <span className="font-semibold text-slate-800">{filteredRecords.length}</span> records
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5">
            <span>Rows:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="text-xs px-2 py-1 border border-slate-300 rounded bg-white"
            >
              <option value={15}>15</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded border border-slate-300 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-mono">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded border border-slate-300 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
