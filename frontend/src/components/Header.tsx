import React from 'react';
import { Wind, Database, Clock, ShieldAlert, Sparkles, RefreshCw } from 'lucide-react';
import { DataMode } from '../types';

interface HeaderProps {
  dataSource: string;
  dataMode: DataMode;
  isDemo: boolean;
  lastRefreshTime: string;
  onRefresh: () => void;
  isLoading: boolean;
  onToggleMode: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  dataSource,
  dataMode,
  isDemo,
  lastRefreshTime,
  onRefresh,
  isLoading,
  onToggleMode,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          {/* Brand & Subtitle */}
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-lg bg-brand-700 flex items-center justify-center text-white shadow-sm ring-2 ring-brand-100">
              <Wind className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                  Wind Forecast Intelligence
                </h1>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                  GB Wholesale Market
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium mt-0.5">
                UK national wind generation forecast analysis & day-ahead purchase decision analytics
              </p>
            </div>
          </div>

          {/* Status Indicators & Action Controls */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Live vs Demo Badge */}
            <div className="flex items-center">
              {isDemo || dataMode === 'demo' ? (
                <div
                  title="Running in Demo Mode with synthetic fixtures. Not genuine Elexon observations."
                  className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200"
                >
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                  <span>Demo Mode (Synthetic)</span>
                </div>
              ) : dataMode === 'cache' ? (
                <div
                  title="Loaded from local verified Elexon BMRS cache"
                  className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200"
                >
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  <span>Elexon BMRS (Cached)</span>
                </div>
              ) : (
                <div
                  title="Direct live stream from Elexon BMRS API"
                  className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200"
                >
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                  <span>Elexon BMRS (Live)</span>
                </div>
              )}
            </div>

            {/* Last Refresh */}
            <div className="hidden sm:flex items-center space-x-1.5 text-xs text-slate-500 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Updated: {lastRefreshTime}</span>
            </div>

            {/* Mode Switcher Toggle */}
            <button
              onClick={onToggleMode}
              disabled={isLoading}
              className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-md border transition-all ${
                isDemo
                  ? 'bg-brand-50 text-brand-700 border-brand-200 hover:bg-brand-100'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-brand-600" />
              <span>{isDemo ? 'Switch to Live API' : 'Switch to Demo Mode'}</span>
            </button>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-brand-700 text-white hover:bg-brand-800 transition-colors shadow-sm disabled:opacity-60"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
