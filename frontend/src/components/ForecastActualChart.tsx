import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Brush,
} from 'recharts';
import { PeriodAnalysisRecord } from '../types';

interface ForecastActualChartProps {
  data: PeriodAnalysisRecord[];
}

export const ForecastActualChart: React.FC<ForecastActualChartProps> = ({ data }) => {
  // Format chart data
  const chartData = useMemo(() => {
    return data.map((d) => {
      // Format x-axis label: "02 Jan 12:00"
      const dateObj = new Date(d.delivery_start_time);
      const day = dateObj.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', timeZone: 'UTC' });
      const time = dateObj.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC' });
      const label = `${day} ${time}`;

      return {
        ...d,
        label,
        forecast: d.forecast_generation_mw,
        actual: d.actual_generation_mw,
      };
    });
  }, [data]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const point: PeriodAnalysisRecord & { label: string } = payload[0].payload;
      const forecastVal = point.forecast_generation_mw;
      const actualVal = point.actual_generation_mw;
      const errorVal = point.error_mw;

      return (
        <div className="bg-white border border-slate-200 shadow-lg rounded-lg p-3 text-xs font-sans min-w-[240px]">
          <div className="border-b border-slate-100 pb-2 mb-2">
            <div className="font-bold text-slate-900">{point.label} (UTC)</div>
            <div className="text-slate-500 text-2xs mt-0.5">
              Settlement Period: {point.settlement_period} | UK Date: {point.settlement_date}
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="flex items-center text-brand-700 font-medium">
                <span className="w-2.5 h-2.5 rounded-full bg-brand-600 inline-block mr-1.5"></span>
                Day-Ahead Forecast:
              </span>
              <span className="font-mono font-bold text-slate-900">
                {forecastVal !== null ? `${forecastVal.toLocaleString()} MW` : 'Missing'}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="flex items-center text-teal-800 font-medium">
                <span className="w-2.5 h-2.5 rounded-full bg-teal-600 inline-block mr-1.5"></span>
                Actual Generation:
              </span>
              <span className="font-mono font-bold text-slate-900">
                {actualVal !== null ? `${actualVal.toLocaleString()} MW` : 'Missing'}
              </span>
            </div>

            {errorVal !== null && (
              <div className="flex justify-between items-center pt-1.5 border-t border-slate-100">
                <span className="text-slate-500 font-medium">Signed Error:</span>
                <span
                  className={`font-mono font-bold ${
                    errorVal > 0 ? 'text-amber-700' : errorVal < 0 ? 'text-sky-700' : 'text-slate-700'
                  }`}
                >
                  {errorVal > 0 ? `+${errorVal.toLocaleString()} MW` : `${errorVal.toLocaleString()} MW`}
                </span>
              </div>
            )}
          </div>

          <div className="mt-2.5 pt-2 border-t border-slate-100 text-2xs text-slate-400 space-y-0.5 font-mono">
            <div>Cutoff: {point.decision_cutoff_time.replace('T', ' ').slice(0, 16)}Z</div>
            {point.forecast_publish_time && (
              <div>Published: {point.forecast_publish_time.replace('T', ' ').slice(0, 16)}Z</div>
            )}
            <div>Status: {point.status}</div>
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
            Wind Generation: Selected Day-Ahead Forecast vs Observed Actual Outturn
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Half-hourly delivery profile across GB national transmission system (MW)
          </p>
        </div>
        <div className="flex items-center space-x-3 text-xs">
          <span className="inline-flex items-center text-slate-600">
            <span className="w-3 h-0.5 bg-brand-600 mr-1.5"></span>
            Selected Forecast (11:00 D-1)
          </span>
          <span className="inline-flex items-center text-slate-600">
            <span className="w-3 h-0.5 bg-teal-600 mr-1.5"></span>
            Actual FUELHH Outturn
          </span>
        </div>
      </div>

      <div className="w-full h-80 sm:h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 15, left: 0, bottom: 25 }}>
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
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              unit=" MW"
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="forecast"
              name="Day-Ahead Forecast"
              stroke="#026fc3"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 1, stroke: '#ffffff' }}
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual Outturn"
              stroke="#0d9488"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 1, stroke: '#ffffff' }}
              connectNulls={false}
            />
            {chartData.length > 48 && (
              <Brush
                dataKey="label"
                height={24}
                stroke="#cbd5e1"
                fill="#f8fafc"
                startIndex={0}
                endIndex={Math.min(chartData.length - 1, 96)}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
