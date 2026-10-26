import React from 'react';
import { Activity, TrendingUp, TrendingDown, CheckCircle2, AlertCircle, Percent, Zap } from 'lucide-react';
import { AccuracyMetrics, MissingDataSummary } from '../types';

interface KpiCardsProps {
  metrics: AccuracyMetrics;
  missingSummary: MissingDataSummary;
  analysisPeriod: { start_date: string; end_date: string; total_days: number };
}

export const KpiCards: React.FC<KpiCardsProps> = ({
  metrics,
  missingSummary,
  analysisPeriod,
}) => {
  const isPositiveBias = metrics.bias_mw > 0;
  const isZeroBias = metrics.bias_mw === 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* 1. Mean Absolute Error (MAE) */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Mean Absolute Error
            </span>
            <Activity className="w-4 h-4 text-brand-600" />
          </div>
          <div className="flex items-baseline space-x-1.5">
            <span className="text-2xl font-bold font-mono text-slate-900 tracking-tight">
              {metrics.mae_mw.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
            </span>
            <span className="text-xs font-semibold text-slate-500">MW</span>
          </div>
        </div>
        <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>Lower is better</span>
          <span className="font-mono text-slate-600">{(metrics.mae_mw * 0.5).toLocaleString(undefined, { maximumFractionDigits: 0 })} MWh/period</span>
        </div>
      </div>

      {/* 2. Root Mean Squared Error (RMSE) */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Root Mean Squared Error
            </span>
            <Zap className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="flex items-baseline space-x-1.5">
            <span className="text-2xl font-bold font-mono text-slate-900 tracking-tight">
              {metrics.rmse_mw.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
            </span>
            <span className="text-xs font-semibold text-slate-500">MW</span>
          </div>
        </div>
        <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>Penalizes large swings</span>
          <span className="font-mono text-slate-600">
            +{Math.max(0, metrics.rmse_mw - metrics.mae_mw).toLocaleString(undefined, { maximumFractionDigits: 0 })} MW vs MAE
          </span>
        </div>
      </div>

      {/* 3. Mean Bias */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Mean Bias (Signed Error)
            </span>
            {isPositiveBias ? (
              <TrendingUp className="w-4 h-4 text-amber-600" />
            ) : isZeroBias ? (
              <Activity className="w-4 h-4 text-slate-400" />
            ) : (
              <TrendingDown className="w-4 h-4 text-sky-600" />
            )}
          </div>
          <div className="flex items-baseline space-x-2">
            <span className={`text-2xl font-bold font-mono tracking-tight ${
              isPositiveBias ? 'text-amber-700' : isZeroBias ? 'text-slate-900' : 'text-sky-700'
            }`}>
              {metrics.bias_mw > 0 ? `+${metrics.bias_mw.toFixed(1)}` : metrics.bias_mw.toFixed(1)}
            </span>
            <span className="text-xs font-semibold text-slate-500">MW</span>
          </div>
        </div>
        <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500">Direction:</span>
          <span className={`px-2 py-0.5 rounded-full font-semibold text-2xs ${
            isPositiveBias
              ? 'bg-amber-100 text-amber-800'
              : isZeroBias
              ? 'bg-slate-100 text-slate-700'
              : 'bg-sky-100 text-sky-800'
          }`}>
            {isPositiveBias ? 'Overforecasting (Short risk)' : isZeroBias ? 'Zero Bias' : 'Underforecasting (Spill risk)'}
          </span>
        </div>
      </div>

      {/* 4. Valid Pairs & WAPE */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Valid Pairs & WAPE
            </span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-slate-900 tracking-tight">
              {metrics.sample_count.toLocaleString()}
            </span>
            <span className="text-xs text-slate-500">
              / {missingSummary.total_expected_periods} ({missingSummary.data_completeness_pct}%)
            </span>
          </div>
        </div>
        <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>WAPE Error:</span>
          <span className="font-mono font-semibold text-slate-900">
            {metrics.wape_pct !== null ? `${metrics.wape_pct.toFixed(2)}%` : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
};
