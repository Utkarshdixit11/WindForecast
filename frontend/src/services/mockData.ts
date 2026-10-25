import { AnalysisResponse } from '../types';

/**
 * Deterministic synthetic mock response matching backend schema.
 * Clearly separated and labeled as synthetic fixture / demo data.
 */
export const mockAnalysisResponse: AnalysisResponse = {
  analysis_period: {
    start_date: '2026-01-01',
    end_date: '2026-01-03',
    total_days: 3,
  },
  data_source: 'Synthetic Fixture (Demo Mode - Not Genuine Elexon Observations)',
  data_mode: 'demo',
  is_demo: true,
  decision_cutoff_config: {
    cutoff_type: 'day_ahead_fixed',
    cutoff_time_uk: '11:00',
    relative_hours_lead: 24,
    resolution_matching: 'hourly_block',
    rationale:
      'Default cutoff represents 11:00 London local time on Day D-1, aligning with standard UK Day-Ahead power exchange order submission deadlines (EPEX SPOT / Nord Pool GB). Any forecast published after this cutoff is excluded to prevent look-ahead bias.',
  },
  metrics: {
    sample_count: 142,
    mae_mw: 845.5,
    rmse_mw: 1042.8,
    bias_mw: 320.4,
    wape_pct: 7.82,
    total_actual_mwh: 768240.0,
    total_forecast_mwh: 791020.0,
    mape_note:
      'MAPE (Mean Absolute Percentage Error) is intentionally omitted because actual wind generation frequently approaches zero MW during calm periods, which causes division-by-zero or mathematically distorted percentage spikes. WAPE is provided instead as an industry-standard volume-weighted metric.',
  },
  missing_data_summary: {
    total_expected_periods: 144,
    valid_pair_count: 142,
    missing_forecast_count: 1,
    missing_actual_count: 1,
    missing_both_count: 0,
    data_completeness_pct: 98.61,
  },
  time_series: Array.from({ length: 144 }, (_, i) => {
    const day = Math.floor(i / 48) + 1;
    const periodInDay = (i % 48) + 1;
    const hour = Math.floor((periodInDay - 1) / 2);
    const minute = (periodInDay - 1) % 2 === 0 ? '00' : '30';
    const dateStr = `2026-01-0${day}`;
    const timeStr = `${String(hour).padStart(2, '0')}:${minute}:00`;
    const dtUtc = `${dateStr}T${timeStr}Z`;
    const dtUk = `${dateStr}T${timeStr}+00:00`;
    const cutoffUtc = `2026-01-0${day - 1 === 0 ? '31' : day - 1}T11:00:00Z`;

    // Synthetic base wind curve
    const cycle = Math.sin((i / 48) * 2 * Math.PI) * 4500;
    const harmonic = Math.cos((i / 24) * 2 * Math.PI) * 1800;
    const actual = Math.max(800, Math.round(10500 + cycle + harmonic));

    // Edge case 1: Period 45 has missing forecast
    if (i === 45) {
      return {
        delivery_start_time: dtUtc,
        delivery_start_time_uk: dtUk,
        settlement_date: dateStr,
        settlement_period: periodInDay,
        decision_cutoff_time: cutoffUtc,
        forecast_publish_time: null,
        forecast_generation_mw: null,
        actual_generation_mw: actual,
        error_mw: null,
        absolute_error_mw: null,
        status: 'MISSING_FORECAST',
      };
    }

    // Edge case 2: Period 80 has missing actual
    if (i === 80) {
      const forecast = Math.round(actual * 1.05);
      return {
        delivery_start_time: dtUtc,
        delivery_start_time_uk: dtUk,
        settlement_date: dateStr,
        settlement_period: periodInDay,
        decision_cutoff_time: cutoffUtc,
        forecast_publish_time: `${dateStr}T09:30:00Z`,
        forecast_generation_mw: forecast,
        actual_generation_mw: null,
        error_mw: null,
        absolute_error_mw: null,
        status: 'MISSING_ACTUAL',
      };
    }

    // Normal valid pairs with realistic forecast noise
    const noise = Math.sin(i * 1.3) * 650 + (i % 2 === 0 ? 300 : -200);
    const forecast = Math.round(Math.max(500, actual + noise));
    const error = forecast - actual;
    const absError = Math.abs(error);

    return {
      delivery_start_time: dtUtc,
      delivery_start_time_uk: dtUk,
      settlement_date: dateStr,
      settlement_period: periodInDay,
      decision_cutoff_time: cutoffUtc,
      forecast_publish_time: `${dateStr}T09:30:00Z`,
      forecast_generation_mw: forecast,
      actual_generation_mw: actual,
      error_mw: error,
      absolute_error_mw: absError,
      status: 'VALID_PAIR',
    };
  }),
  warnings: [
    'DEMO MODE ACTIVE: Using synthetic test fixture. Figures do not represent genuine Elexon observations.',
  ],
};
