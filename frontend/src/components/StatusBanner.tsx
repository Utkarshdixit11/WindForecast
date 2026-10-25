import React from 'react';
import { AlertTriangle, Info, CheckCircle2 } from 'lucide-react';
import { DataMode } from '../types';

interface StatusBannerProps {
  warnings: string[];
  isDemo: boolean;
  dataMode: DataMode;
  dataSource: string;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({
  warnings,
  isDemo,
  dataMode,
  dataSource,
}) => {
  if (warnings.length === 0 && !isDemo) {
    return null;
  }

  return (
    <div className="space-y-2 mb-6">
      {/* Explicit Demo Warning */}
      {isDemo && (
        <div className="flex items-start space-x-3 p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold text-amber-950">Synthetic Fixture Demo Mode Active:</span>
            <p className="text-amber-800 leading-relaxed">
              The values currently rendered are generated from small, deterministic synthetic fixtures designed for offline validation.
              They are <strong>not genuine Elexon observations</strong> and should not be used for commercial wholesale power transactions.
            </p>
          </div>
        </div>
      )}

      {/* Operational Warnings */}
      {warnings.length > 0 && !isDemo && (
        <div className="flex items-start space-x-3 p-3.5 bg-slate-100 border border-slate-200 rounded-xl text-slate-800 text-xs">
          <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-900">Data Quality & Completeness Notes:</span>
            <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-600">
              {warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
