import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, RotateCcw, RefreshCw } from 'lucide-react';
import { Header } from '../components/Header';
import { Filters } from '../components/Filters';
import { KpiCards } from '../components/KpiCards';
import { ForecastActualChart } from '../components/ForecastActualChart';
import { ErrorChart } from '../components/ErrorChart';
import { DataTable } from '../components/DataTable';
import { StatusBanner } from '../components/StatusBanner';
import { LoadingSkeleton, EmptyState } from '../components/LoadingSkeleton';
import { fetchAnalysis } from '../services/api';
import { AnalysisResponse, FilterParams } from '../types';

export const Dashboard: React.FC = () => {
  const [filters, setFilters] = useState<FilterParams>({
    start_date: '2026-01-01',
    end_date: '2026-01-31',
    cutoff_type: 'day_ahead_fixed',
    cutoff_time_uk: '11:00',
    resolution_matching: 'hourly_block',
  });

  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastRefreshTime, setLastRefreshTime] = useState<string>('Loading...');

  const loadData = useCallback(async (currentFilters: FilterParams) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetchAnalysis(currentFilters);
      setData(response);
      setLastRefreshTime(new Date().toLocaleTimeString('en-GB', { hour12: false }));
    } catch (err: any) {
      console.error('Failed to load analysis:', err);
      setData(null); // Clear data so stale records are not falsely shown during an error
      setErrorMessage(err.message || 'Failed to fetch analysis from backend API.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(filters);
  }, [loadData, filters]);

  const handleApplyFilters = (newFilters: FilterParams) => {
    setFilters(newFilters);
  };

  const handleToggleMode = () => {
    const nextMode = data?.is_demo || filters.force_mode === 'demo' ? 'live' : 'demo';
    const newFilters = {
      ...filters,
      force_mode: nextMode as 'live' | 'demo',
    };
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    const defaultFilters: FilterParams = {
      start_date: '2026-01-01',
      end_date: '2026-01-31',
      cutoff_type: 'day_ahead_fixed',
      cutoff_time_uk: '11:00',
      resolution_matching: 'hourly_block',
    };
    setFilters(defaultFilters);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      <div>
        {/* Top Header */}
        <Header
          dataSource={data?.data_source || 'Elexon BMRS Open Data API'}
          dataMode={data?.data_mode || (filters.force_mode === 'demo' ? 'demo' : 'live')}
          isDemo={data?.is_demo || filters.force_mode === 'demo'}
          lastRefreshTime={lastRefreshTime}
          onRefresh={() => loadData(filters)}
          isLoading={isLoading}
          onToggleMode={handleToggleMode}
        />

        {/* Main Content Area */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Status & Warning Banners */}
          {data && (
            <StatusBanner
              warnings={data.warnings}
              isDemo={data.is_demo}
              dataMode={data.data_mode}
              dataSource={data.data_source}
            />
          )}

          {/* Filter Bar */}
          <Filters
            filters={filters}
            onApplyFilters={handleApplyFilters}
            isLoading={isLoading}
          />

          {/* Honest Error State Card */}
          {errorMessage && (
            <div className="mb-6 p-6 bg-white border border-rose-200 rounded-xl shadow-xs">
              <div className="flex items-start space-x-3.5">
                <div className="p-2 bg-rose-100 rounded-lg text-rose-700 shrink-0 mt-0.5">
                  <AlertCircle className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-bold text-rose-900 tracking-tight">
                    API Request Failed
                  </h3>
                  <p className="text-xs text-rose-800 mt-1 font-mono bg-rose-50 p-2.5 rounded border border-rose-100">
                    {errorMessage}
                  </p>
                  <p className="text-xs text-slate-500 mt-2">
                    Review your parameter configuration or ensure the backend service is operational.
                  </p>
                  <div className="flex items-center space-x-3 mt-4">
                    <button
                      onClick={() => loadData(filters)}
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-rose-700 hover:bg-rose-800 text-white rounded-md text-xs font-semibold shadow-2xs transition-colors"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Retry Request</span>
                    </button>
                    <button
                      onClick={handleResetFilters}
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs font-semibold border border-slate-200 transition-colors"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Reset to Valid Defaults</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Body Content */}
          {isLoading && !data ? (
            <LoadingSkeleton />
          ) : !data && !errorMessage ? (
            <EmptyState onReset={handleResetFilters} />
          ) : data ? (
            <>
              {/* KPI Metrics Summary */}
              <KpiCards
                metrics={data.metrics}
                missingSummary={data.missing_data_summary}
                analysisPeriod={data.analysis_period}
              />

              {/* Main Forecast vs Actual Chart */}
              <ForecastActualChart data={data.time_series} />

              {/* Signed Forecast Error Chart */}
              <ErrorChart data={data.time_series} />

              {/* Detailed Settlement Period Table */}
              <DataTable records={data.time_series} />
            </>
          ) : null}
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-12 py-5 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <span className="font-semibold text-slate-700">Wind Forecast Intelligence</span> — Built for UK wholesale day-ahead electricity procurement.
          </div>
          <div className="flex items-center space-x-4 text-2xs text-slate-400">
            <span>Data Provider: Elexon BMRS Open Data (FUELHH &amp; WINDFOR)</span>
            <span>•</span>
            <span>Cutoff: 11:00 London D-1</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
