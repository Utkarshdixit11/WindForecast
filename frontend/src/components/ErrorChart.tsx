import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from 'recharts';
import { PeriodAnalysisRecord } from '../types';

interface ErrorChartProps {
  data: PeriodAnalysisRecord[];
}

export const ErrorChart: React.FC<ErrorChartProps> = ({ data }) => {
  const chartData = useMemo(() => {
    return data.map((d) => {
      const dateObj = new Date(d.delivery_start_time);
      const day = dateObj.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', timeZone: 'UTC' });
      const time = dateObj.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC' });
      const label = `${day} ${time}`;

      return {
        ...d,
        label,
        error: d.error_mw,
      };
    });
  }, [data]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item: PeriodAnalysisRecord & { label: string } = payload[0].payload;
      const errorVal = item.error_mw;

      if (errorVal === null) {
        return (
          <div className="bg-white border border-slate-200 shadow-md rounded-lg p-2.5 text-xs">
            <div className="font-bold text-slate-800">{item.label}</div>
            <div className="text-slate-500 mt-1">Status: {item.status}</div>
          </div>
        );
      }

      const isOver = errorVal > 0;
      return (
        <div className="bg-white border border-slate-200 shadow-md rounded-lg p-2.5 text-xs font-sans min-w-[200px]">
          <div className="font-bold text-slate-900 border-b border-slate-100 pb-1.5 mb-1.5">
            {item.label} (SP {item.settlement_period})
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-600">Signed Error:</span>
            <span className={`font-mono font-bold ${isOver ? 'text-amber-700' : 'text-sky-700'}`}>
              {isOver ? `+${errorVal.toLocaleString()} MW` : `${errorVal.toLocaleString()} MW`}
            </span>
          </div>
          <div className="flex justify-between items-center text-2xs text-slate-500 mt-1">
            <span>Forecast: {item.forecast_generation_mw?.toLocaleString()} MW</span>
            <span>Actual: {item.actual_generation_mw?.toLocaleString()} MW</span>
          </div>
          <div className="mt-1.5 pt-1 border-t border-slate-100 text-2xs text-slate-400">
            {isOver ? 'Overforecast (Short risk in auction)' : 'Underforecast (Spill / excess)'}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-xs mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 pb-3 border-b border-slate-100 gap-2">
        <div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight">
            Signed Forecast Error Profile ($Forecast - Actual$)
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Positive error indicates overforecasting (amber); negative indicates underforecasting (sky blue)
          </p>
        </div>
        <div className="flex items-center space-x-3 text-xs">
          <span className="inline-flex items-center text-amber-800 font-medium">
            <span className="w-2.5 h-2.5 rounded-sm bg-amber-500 mr-1.5"></span>
            Overforecast (&gt; 0 MW)
          </span>
          <span className="inline-flex items-center text-sky-800 font-medium">
            <span className="w-2.5 h-2.5 rounded-sm bg-sky-500 mr-1.5"></span>
            Underforecast (&lt; 0 MW)
          </span>
        </div>
      </div>

      <div className="w-full h-56 sm:h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 15, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="label"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              interval="preserveStartEnd"
              minTickGap={40}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
              unit=" MW"
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="#64748b" strokeWidth={1.5} />
            <Bar dataKey="error" maxBarSize={10}>
              {chartData.map((entry, index) => {
                const val = entry.error ?? 0;
                return (
                  <Cell
                    key={`cell-${index}`}
                    fill={val >= 0 ? '#f59e0b' : '#0ea5e9'}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
