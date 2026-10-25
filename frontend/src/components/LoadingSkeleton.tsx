import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="space-y-6 animate-pulse">
      {/* KPI Skeletons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-white rounded-xl border border-slate-200 p-4">
            <div className="h-3.5 bg-slate-200 rounded w-1/2 mb-3"></div>
            <div className="h-8 bg-slate-200 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-slate-100 rounded w-1/3"></div>
          </div>
        ))}
      </div>

      {/* Main Chart Skeleton */}
      <div className="h-96 bg-white rounded-xl border border-slate-200 p-6 flex flex-col justify-between">
        <div className="space-y-2">
          <div className="h-4 bg-slate-200 rounded w-1/4"></div>
          <div className="h-3 bg-slate-100 rounded w-1/3"></div>
        </div>
        <div className="h-64 bg-slate-100 rounded-lg flex items-center justify-center text-xs text-slate-400">
          Loading Elexon BMRS time-series data...
        </div>
      </div>

      {/* Error Chart Skeleton */}
      <div className="h-64 bg-white rounded-xl border border-slate-200 p-6">
        <div className="h-4 bg-slate-200 rounded w-1/4 mb-4"></div>
        <div className="h-44 bg-slate-100 rounded-lg"></div>
      </div>
    </div>
  );
};

export const EmptyState: React.FC<{ onReset: () => void }> = ({ onReset }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-xs my-6">
      <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-400">
        !
      </div>
      <h3 className="text-base font-bold text-slate-900 mb-1">No Delivery Periods Found</h3>
      <p className="text-xs text-slate-500 max-w-md mx-auto mb-4">
        No forecast or outturn records matched the selected January 2026 filter range.
        Ensure start and end dates fall within the target decision window.
      </p>
      <button
        onClick={onReset}
        className="px-4 py-2 bg-brand-700 hover:bg-brand-800 text-white text-xs font-semibold rounded-md shadow-xs transition-colors"
      >
        Reset to January 2026 Full Month
      </button>
    </div>
  );
};
