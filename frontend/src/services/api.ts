import { AnalysisResponse, FilterParams } from '../types';
import { mockAnalysisResponse } from './mockData';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Fetch forecast accuracy analysis directly from the FastAPI backend.
 *
 * In the normal production path:
 * - Always calls the live backend API.
 * - Throws genuine HTTP and network errors so the UI displays errors honestly.
 * - Does NOT mask backend failures with development mock data.
 *
 * Mock fixtures are only used if the user explicitly activates demo mode AND the backend is unreachable.
 */
export async function fetchAnalysis(params: FilterParams): Promise<AnalysisResponse> {
  const queryParams = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
    cutoff_type: params.cutoff_type,
    cutoff_time_uk: params.cutoff_time_uk,
    resolution_matching: params.resolution_matching,
  });

  if (params.force_mode) {
    queryParams.append('force_mode', params.force_mode);
  }

  const url = `${API_BASE_URL}/api/analysis?${queryParams.toString()}`;

  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMsg = `HTTP ${response.status} Error`;
      try {
        const errorJson = JSON.parse(errorText);
        if (errorJson.detail) {
          errorMsg = Array.isArray(errorJson.detail)
            ? errorJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
            : String(errorJson.detail);
        }
      } catch {
        if (errorText) errorMsg = `${errorMsg}: ${errorText}`;
      }
      throw new Error(errorMsg);
    }

    const data: AnalysisResponse = await response.json();
    return data;
  } catch (err: any) {
    // If the user explicitly requested demo mode and the backend is unreachable, provide the mock fixture
    if (params.force_mode === 'demo') {
      console.warn('Backend offline in demo mode. Falling back to local synthetic mock fixture.');
      return {
        ...mockAnalysisResponse,
        warnings: [
          'DEMO MODE (Client Offline Fixture): Backend is unreachable. Displaying deterministic local test fixture.',
        ],
      };
    }

    // In normal production path: rethrow genuine error without masking
    throw err;
  }
}

/**
 * Fetch service metadata from backend.
 */
export async function fetchMetadata(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/metadata`);
  if (!response.ok) {
    throw new Error(`Failed to load metadata: HTTP ${response.status}`);
  }
  return await response.json();
}
