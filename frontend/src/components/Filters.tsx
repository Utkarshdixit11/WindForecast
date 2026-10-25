import React, { useState } from 'react';
import { Calendar, Filter, RotateCcw, HelpCircle, SlidersHorizontal, Info } from 'lucide-react';
import { CutoffType, FilterParams } from '../types';

interface FiltersProps {
  filters: FilterParams;
  onApplyFilters: (newFilters: FilterParams) => void;
  isLoading: boolean;
}

const PRESETS = [
  { label: 'Full Month (Jan 1–31)', start: '2026-01-01', end: '2026-01-31' },
  { label: 'Week 1 (Jan 1–7)', start: '2026-01-01', end: '2026-01-07' },
  { label: 'Week 2 (Jan 8–14)', start: '2026-01-08', end: '2026-01-14' },
  { label: 'Week 3 (Jan 15–21)', start: '2026-01-15', end: '2026-01-21' },
  { label: 'Week 4+ (Jan 22–31)', start: '2026-01-22', end: '2026-01-31' },
];

export const Filters: React.FC<FiltersProps> = ({ filters, onApplyFilters, isLoading }) => {
  const [startDate, setStartDate] = useState(filters.start_date);
  const [endDate, setEndDate] = useState(filters.end_date);
  const [cutoffTimeUk, setCutoffTimeUk] = useState(filters.cutoff_time_uk);
  const [cutoffType, setCutoffType] = useState<CutoffType>(filters.cutoff_type);
  const [resolutionMatching, setResolutionMatching] = useState(filters.resolution_matching);
  const [showExplanation, setShowExplanation] = useState(false);

  const handlePreset = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
    onApplyFilters({
      ...filters,
      start_date: start,
      end_date: end,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onApplyFilters({
      ...filters,
      start_date: startDate,
      end_date: endDate,
      cutoff_type: cutoffType,
      cutoff_time_uk: cutoffTimeUk,
      resolution_matching: resolutionMatching,
    });
  };

  const handleReset = () => {
    const defaultFilters: FilterParams = {
      start_date: '2026-01-01',
      end_date: '2026-01-31',
      cutoff_type: 'day_ahead_fixed',
      cutoff_time_uk: '11:00',
      resolution_matching: 'hourly_block',
    };
    setStartDate(defaultFilters.start_date);
    setEndDate(defaultFilters.end_date);
    setCutoffTimeUk(defaultFilters.cutoff_time_uk);
    setCutoffType(defaultFilters.cutoff_type);
    setResolutionMatching(defaultFilters.resolution_matching);
    onApplyFilters(defaultFilters);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-xs mb-6">
      {/* Top Filter Bar Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3.5 mb-4 border-b border-slate-100 gap-2">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-brand-700" />
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
            Purchase Decision Filters (January 2026 Analysis Period)
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setShowExplanation(!showExplanation)}
          className="text-xs text-brand-700 hover:text-brand-800 font-medium flex items-center space-x-1"
        >
          <Info className="w-3.5 h-3.5" />
          <span>{showExplanation ? 'Hide Methodology Note' : 'Methodology & Cutoff Note'}</span>
        </button>
      </div>

      {/* Explanatory Collapsible Banner */}
      {showExplanation && (
        <div className="mb-4 p-3.5 bg-brand-50 border border-brand-200 rounded-lg text-xs text-brand-950 space-y-1.5 leading-relaxed">
          <div className="font-semibold text-brand-900 flex items-center space-x-1">
            <span>Day-Ahead Wholesale Auction Cutoff Assumption:</span>
          </div>
          <p>
            In Great Britain, day-ahead wholesale electricity auctions (such as EPEX SPOT UK Day-Ahead) close order submission at <strong>11:00 UK local time on Day D-1</strong> for physical delivery across Day D.
          </p>
          <p>
            To prevent look-ahead bias, this dashboard evaluates the <strong>latest eligible forecast published at or prior to the 11:00 D-1 cutoff</strong>. Any forecast published after cutoff is strictly excluded.
          </p>
        </div>
      )}

      {/* Quick Presets */}
      <div className="flex flex-wrap items-center gap-1.5 mb-4">
        <span className="text-xs font-medium text-slate-500 mr-1.5">Presets:</span>
        {PRESETS.map((p) => {
          const isActive = startDate === p.start && endDate === p.end;
          return (
            <button
              key={p.label}
              type="button"
              onClick={() => handlePreset(p.start, p.end)}
              className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                isActive
                  ? 'bg-brand-700 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {p.label}
            </button>
          );
        })}
      </div>

      {/* Form Controls */}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 items-end">
        {/* Start Date */}
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Start Delivery Date
          </label>
          <div className="relative">
            <input
              type="date"
              min="2026-01-01"
              max="2026-01-31"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-md shadow-2xs focus:ring-1 focus:ring-brand-600 focus:border-brand-600"
            />
          </div>
        </div>

        {/* End Date */}
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            End Delivery Date
          </label>
          <div className="relative">
            <input
              type="date"
              min="2026-01-01"
              max="2026-01-31"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-md shadow-2xs focus:ring-1 focus:ring-brand-600 focus:border-brand-600"
            />
          </div>
        </div>

        {/* Cutoff Time UK */}
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Day-Ahead Cutoff (UK Time)
          </label>
          <select
            value={cutoffTimeUk}
            onChange={(e) => setCutoffTimeUk(e.target.value)}
            className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md shadow-2xs bg-white focus:ring-1 focus:ring-brand-600 focus:border-brand-600"
          >
            <option value="11:00">11:00 D-1 (EPEX SPOT UK Auction)</option>
            <option value="12:00">12:00 D-1 (Midday Cutoff)</option>
            <option value="09:00">09:00 D-1 (Early Morning Trading)</option>
            <option value="16:00">16:00 D-1 (Late Day-Ahead)</option>
          </select>
        </div>

        {/* Resolution Strategy */}
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Resolution Matching
          </label>
          <select
            value={resolutionMatching}
            onChange={(e) => setResolutionMatching(e.target.value)}
            className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md shadow-2xs bg-white focus:ring-1 focus:ring-brand-600 focus:border-brand-600"
          >
            <option value="hourly_block">Hourly Block (ESO Hour $\rightarrow$ 30-min HH)</option>
            <option value="exact_timestamp">Exact Timestamp Only (HH:00)</option>
          </select>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 py-2 px-3 bg-brand-700 hover:bg-brand-800 text-white text-xs font-medium rounded-md shadow-xs transition-colors disabled:opacity-60 flex items-center justify-center space-x-1.5"
          >
            <Filter className="w-3.5 h-3.5" />
            <span>Apply Filters</span>
          </button>
          <button
            type="button"
            onClick={handleReset}
            disabled={isLoading}
            title="Reset to January 2026 defaults"
            className="p-2 border border-slate-300 rounded-md text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
