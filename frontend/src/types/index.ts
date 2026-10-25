/** TypeScript types matching the backend schema and analytical models. */

export type CutoffType = 'day_ahead_fixed' | 'relative_hours';
export type DataMode = 'live' | 'cache' | 'demo';
export type PeriodStatus = 'VALID_PAIR' | 'MISSING_FORECAST' | 'MISSING_ACTUAL' | 'MISSING_BOTH';

export interface ForecastCutoffConfig {
  cutoff_type: CutoffType;
  cutoff_time_uk: string;
  relative_hours_lead: number;
  resolution_matching: string;
  rationale: string;
}

export interface AccuracyMetrics {
  sample_count: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  wape_pct: number | null;
  total_actual_mwh: number;
  total_forecast_mwh: number;
  mape_note: string;
}

export interface MissingDataSummary {
  total_expected_periods: number;
  valid_pair_count: number;
  missing_forecast_count: number;
  missing_actual_count: number;
  missing_both_count: number;
  data_completeness_pct: number;
}

export interface PeriodAnalysisRecord {
  delivery_start_time: string;
  delivery_start_time_uk: string;
  settlement_date: string;
  settlement_period: number;
  decision_cutoff_time: string;
  forecast_publish_time: string | null;
  forecast_generation_mw: number | null;
  actual_generation_mw: number | null;
  error_mw: number | null;
  absolute_error_mw: number | null;
  status: PeriodStatus;
}

export interface AnalysisPeriod {
  start_date: string;
  end_date: string;
  total_days: number;
}

export interface AnalysisResponse {
  analysis_period: AnalysisPeriod;
  data_source: string;
  data_mode: DataMode;
  is_demo: boolean;
  decision_cutoff_config: ForecastCutoffConfig;
  metrics: AccuracyMetrics;
  missing_data_summary: MissingDataSummary;
  time_series: PeriodAnalysisRecord[];
  warnings: string[];
}

export interface FilterParams {
  start_date: string;
  end_date: string;
  cutoff_type: CutoffType;
  cutoff_time_uk: string;
  resolution_matching: string;
  force_mode?: 'live' | 'demo';
}
