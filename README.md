# Wind Forecast Intelligence — UK Day-Ahead Analytics

> 🌐 **Live Deployed Application:** [Wind Forecast Intelligence | UK Day-Ahead Analytics](https://wind-forecast-omega.vercel.app/)

A complete, production-grade analytics web application built for UK electricity utilities purchasing power in the Day-Ahead wholesale market. The application ingests genuine wind generation actuals and rolling forecasts from the **Elexon BMRS Open Data API**, matches delivery periods strictly respecting day-ahead purchase decision cutoffs, and quantifies forecast errors using transparent statistical metrics.

## Application Screenshots

### Live Elexon BMRS Analysis (January 2026)
![Wind Forecast Intelligence Dashboard Overview](docs/images/dashboard_overview.png)
*Figure 1: Wind Forecast Intelligence Dashboard displaying genuine January 2026 Elexon BMRS observations (1,488 half-hour settlement periods), interactive KPI summary cards, Forecast vs. Actual overlay timeline with zoom brush, signed error distribution chart, and the settlement period audit table.*

### Synthetic Demo Mode & Offline Fixtures
![Synthetic Demo Mode and Offline Verification](docs/images/demo_mode.png)
*Figure 2: Synthetic Demo Mode activated via the header toggle. Renders deterministic edge cases, missing data flags, and provides an offline fallback without modifying the production API path.*

---

## 1. Business Problem & Procurement Context

An electricity utility purchasing power in the UK wholesale day-ahead market (EPEX SPOT / Nord Pool UK Day-Ahead auctions) must estimate how much electricity to purchase beyond expected renewable self-generation. 

* **The Problem:** Wind generation is intermittent and weather-dependent. Forecast errors create substantial procurement and financial risk:
  * **Overforecasting ($Forecast > Actual$, Positive Bias):** The utility procures too little wholesale power, leading to an unexpected short position that must be settled in the Balancing Mechanism at volatile, elevated system cashout prices.
  * **Underforecasting ($Forecast < Actual$, Negative Bias):** The utility purchases surplus power that physically spills or must be sold off in intraday markets at distress discounts.
* **The Solution:** This application helps trading and procurement teams:
  1. Freeze and analyze the latest wind generation forecast available before the day-ahead auction cutoff.
  2. Compare that selected forecast with subsequently observed actual wind outturn.
  3. Quantify forecast error magnitude, direction, and risk with transparent metrics.

---

## 2. Data Provider & API Schema Documentation

All data is ingested from the **Elexon Insights Solution (BMRS) API** (`https://data.elexon.co.uk/bmrs/api/v1`):

### A. Actual Generation Dataset: `FUELHH`
* **Documentation & Endpoint:** `GET /datasets/FUELHH/stream` ([Elexon API Docs](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream))
* **Granularity:** Half-hourly delivery periods (Settlement Periods 1 to 48/50).
* **Applied Query Parameters:** `settlementDateFrom=YYYY-MM-DD`, `settlementDateTo=YYYY-MM-DD`, `fuelType=WIND`
* **Key Fields Used:**
  * `startTime`: UTC ISO 8601 delivery period start timestamp.
  * `generation`: Observed outturn in Megawatts (MW).
  * `fuelType`: Filtered for `"WIND"`.
  * `settlementDate`: UK settlement date (YYYY-MM-DD).
  * `settlementPeriod`: Settlement period number (1 to 48/50).

### B. Forecast Dataset: `WINDFOR`
* **Documentation & Endpoint:** `GET /datasets/WINDFOR/stream` ([Elexon API Docs](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream))
* **Granularity:** Hourly target delivery periods issued at rolling intervals throughout the day.
* **Applied Query Parameters:** `publishDateTimeFrom=...`, `publishDateTimeTo=...`
* **Key Fields Used:**
  * `startTime`: Target forecast delivery period timestamp.
  * `publishTime`: Timestamp when National Grid ESO published this specific forecast revision.
  * `generation`: Predicted wind generation in Megawatts (MW).

### Time Resolution Alignment
* While `FUELHH` outturns are published every 30 minutes, `WINDFOR` is issued by ESO on clock-hour boundaries.
* The application supports two documented matching strategies via `resolution_matching`:
  1. `hourly_block` (Default, market convention): Maps the hourly ESO forecast across both half-hour settlement periods in that hour ($HH$:00 and $HH$:30).
  2. `exact_timestamp`: Strictly pairs only $HH$:00 periods, reporting $HH$:30 periods honestly as `MISSING_FORECAST` with zero silent discarding.

---

## 3. Critical Forecast Selection Logic & Look-Ahead Bias Prevention

1. **Separation of Concepts:**
   * **Target Delivery Period ($T_{\text{delivery}}$):** The half-hour window when power physically flows.
   * **Forecast Publication Time ($T_{\text{pub}}$):** The timestamp when the forecast was issued by National Grid ESO.
   * **Purchase Decision Cutoff ($T_{\text{cutoff}}$):** The trading gate closure deadline.

2. **Cutoff Assumption & Market Alignment:**
   * **Configured Default:** `day_ahead_fixed` at **11:00 UK local time on Day D-1**.
   * **Market Rationale:** 11:00 London local time corresponds to the order submission gate closure of the UK Day-Ahead wholesale power auction (EPEX SPOT UK Day-Ahead Auction).
   * **Timezone Normalization:** Implemented using `zoneinfo.ZoneInfo("Europe/London")` to account for Greenwich Mean Time (GMT, UTC+0) and British Summer Time (BST, UTC+1). On clock change dates, 11:00 BST translates to 10:00 UTC.

3. **Selection Rule & Look-Ahead Prevention:**
   * A forecast record $f$ for target period $T_{\text{delivery}}$ is eligible if and only if:
     $$f.publishTime \le T_{\text{cutoff}}$$
   * **Strict Look-Ahead Bias Exclusion:** Any forecast published after $T_{\text{cutoff}}$ (such as late afternoon updates or real-time intraday adjustments) is excluded.
   * **Latest Eligible Selection:** Among all eligible candidates, the record with $\max(f.publishTime)$ is selected.
   * **Transparent Status Reporting:** Every period in the time grid is tracked as `VALID_PAIR`, `MISSING_FORECAST`, `MISSING_ACTUAL`, or `MISSING_BOTH`.

---

## 4. Accuracy Metrics & Formulation

Calculated across all $N$ valid pairs:
* **Error:** $e_i = Forecast_i - Actual_i$ (MW)
* **Absolute Error:** $|e_i| = |Forecast_i - Actual_i|$ (MW)
* **MAE (Mean Absolute Error):**
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |e_i| \quad (\text{MW})$$
* **RMSE (Root Mean Squared Error):**
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} e_i^2} \quad (\text{MW})$$
* **Bias (Mean Signed Error):**
  $$\text{Bias} = \frac{1}{N} \sum_{i=1}^{N} e_i \quad (\text{MW})$$
  *(Positive = systematic overforecasting / short imbalance risk; Negative = systematic underforecasting / spill risk)*
* **WAPE (Weighted Absolute Percentage Error):**
  $$\text{WAPE} = \frac{\sum_{i=1}^{N} |e_i|}{\sum_{i=1}^{N} Actual_i} \times 100\%$$
  *(If $\sum Actual_i = 0$, WAPE is safely returned as `null` with no division-by-zero error)*
* **Why MAPE is Omitted:** Mean Absolute Percentage Error ($\frac{1}{N} \sum \frac{|F - A|}{A}$) divides by actual generation in each period. When actual wind drops near 0 MW, MAPE creates infinite or distorted percentage spikes. WAPE provides an industry-standard volume-weighted error.

---

## 5. Technology Stack & System Architecture

### A. Technology Stack
* **Frontend:** React 19, Vite, TypeScript, Tailwind CSS, Recharts, Lucide Icons.
* **Backend:** Python 3.11, FastAPI, Pandas, HTTPX (async client with exponential backoff retries), Pydantic v2.
* **Testing:** Pytest, Pytest-Asyncio (deterministic fixtures with zero external network dependencies).
* **Containerization:** Docker multi-stage builds and Docker Compose with healthchecks.

### B. System Architecture Diagram

```mermaid
graph TD
    subgraph Browser ["Client Layer (React 19 + TypeScript + Vite)"]
        UI["Dashboard Page"]
        Filters["Purchase Filters (Cutoff / Presets)"]
        Cards["KPI Summary Cards (MAE / RMSE / Bias / WAPE)"]
        Charts["Forecast vs Actual & Signed Error Charts"]
        Table["Settlement Audit Table (CSV Export)"]
        UI --> Filters
        UI --> Cards
        UI --> Charts
        UI --> Table
    end

    subgraph Backend ["FastAPI Application (Python 3.11)"]
        Routes["API Endpoints (/api/analysis, /api/health)"]
        Coordinator["Analysis Coordinator Pipeline"]
        Selector["Forecast Selector (Look-Ahead Bias Elimination)"]
        MetricsEngine["Metrics Engine (MAE, RMSE, Bias, WAPE)"]
        Routes --> Coordinator
        Coordinator --> Selector
        Coordinator --> MetricsEngine
    end

    subgraph DataLayer ["Data & Ingestion Layer"]
        BMRSClient["Resilient BMRS Client (Async HTTPX)"]
        DiskCache[("Local Disk Cache (backend/data/cache/)")]
        ElexonAPI["Elexon BMRS Open Data API"]
        
        Coordinator --> BMRSClient
        BMRSClient <-->|Fast Read / Write| DiskCache
        BMRSClient <-->|Stream / Fallback| ElexonAPI
    end

    UI -->|REST JSON Requests| Routes
```

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        BROWSER / CLIENT LAYER                          │
│  React 19 + TypeScript + Vite + Tailwind CSS + Recharts (Port 5173)   │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTP REST Requests (/api/analysis)
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND LAYER                           │
│              Python 3.11 + FastAPI + Pydantic v2 (Port 8000)          │
│                                                                        │
│  ┌─────────────────────────┐          ┌─────────────────────────────┐  │
│  │   Forecast Selector     │          │       Metrics Engine        │  │
│  │ (Cutoff & Look-Ahead)   │          │    (MAE, RMSE, Bias, WAPE)  │  │
│  └───────────▲─────────────┘          └──────────────▲──────────────┘  │
│              │                                       │                 │
│  ┌───────────┴───────────────────────────────────────┴──────────────┐  │
│  │                    Analysis Coordinator Pipeline                  │  │
│  └─────────────────────────────────▲────────────────────────────────┘  │
│                                    │                                   │
│  ┌─────────────────────────────────┴────────────────────────────────┐  │
│  │                BMRS Ingestion Client (Async HTTPX)                │  │
│  └───────────────┬───────────────────────────────────▲──────────────┘  │
└──────────────────┼───────────────────────────────────┼─────────────────┘
                   │ Cache Miss (Fetch)                │ Read
                   ▼                                   │
┌─────────────────────────────────────┐  ┌─────────────┴───────────────┐
│     ELEXON BMRS OPEN DATA API       │  │    LOCAL PERSISTENT CACHE   │
│  https://data.elexon.co.uk/bmrs/v1 │  │     (backend/data/cache/)   │
│   - /datasets/FUELHH/stream         │  │   - FUELHH_WIND_*.json      │
│   - /datasets/WINDFOR/stream        │  │   - WINDFOR_*.json          │
└─────────────────────────────────────┘  └─────────────────────────────┘
```

### C. Folder Structure

```text
welllass/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py              # GET /api/health, /api/metadata, /api/analysis
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   └── bmrs_client.py         # HTTPX client with retries, timeouts, and disk cache
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── models.py              # Pydantic models for raw feeds, metrics, and responses
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── analysis_service.py    # Pipeline coordinator (live, cache, and demo modes)
│   │   │   ├── forecast_selector.py   # Cutoff determination, look-ahead exclusion, matching
│   │   │   ├── metrics.py             # MAE, RMSE, Bias, WAPE, and energy calculations
│   │   │   └── synthetic_generator.py # Deterministic synthetic datasets
│   │   ├── config.py                  # Settings with environment variable overrides
│   │   └── main.py                    # FastAPI entrypoint with CORS
│   ├── tests/
│   │   ├── conftest.py                # Test fixtures and path setup
│   │   ├── test_api.py                # FastAPI route integration tests
│   │   ├── test_bmrs_client.py        # Client tests: retries, caching, error codes
│   │   ├── test_forecast_selector.py  # Cutoff logic, DST, look-ahead exclusion, matching
│   │   └── test_metrics.py            # Known numerical benchmarks and zero denominator tests
│   ├── data/
│   │   ├── cache/                     # Local disk cache for BMRS streams
│   │   └── fixtures/                  # Offline deterministic fixtures
│   ├── Dockerfile                     # Python 3.11 slim production container
│   └── requirements.txt               # Pinned dependencies
├── frontend/
│   ├── src/
│   │   ├── components/                # Header, Filters, KpiCards, Charts, DataTable, Banners
│   │   ├── pages/                     # Dashboard.tsx
│   │   ├── services/                  # api.ts (typed client) and mockData.ts (demo fixture)
│   │   ├── types/                     # TypeScript interfaces
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css                  # Tailwind styles
│   ├── nginx.conf                     # Production Nginx SPA & proxy config
│   ├── Dockerfile                     # Multi-stage Nginx container
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── vercel.json                    # Vercel deployment rewrites
├── docker-compose.yml                 # Multi-container orchestration
├── .env.example                       # Documented environment variables
├── .gitignore
└── README.md
```

---

## 6. How to Run Locally

### Option A: Local Development (Terminal)

1. **Install backend dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Start the FastAPI backend (Port 8000):**
   ```bash
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. **Install frontend dependencies & start dev server (Port 5173):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the application:**
   * Frontend: [http://localhost:5173/](http://localhost:5173/)
   * Backend OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   * Backend Healthcheck: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Option B: Docker Compose

Ensure Docker Engine is running on your machine:
```bash
docker-compose up --build
```
* **Frontend:** [http://localhost:3000](http://localhost:3000) (Nginx SPA proxying `/api` requests to backend)
* **Backend:** [http://localhost:8000](http://localhost:8000)
* **Persistent Disk Cache:** Mounted to `./backend/data/cache` so Elexon stream responses persist across runs.

---

## 7. Deployment Guide & Live Links

* 🌐 **Live Deployed Frontend (Vercel):** [Wind Forecast Intelligence | UK Day-Ahead Analytics](https://wind-forecast-omega.vercel.app/)

### A. Backend Deployment (Docker Container)
* **Build Context:** Repository Root (`.`)
* **Dockerfile Path:** `backend/Dockerfile`
* **Exposed Port:** `8000`
* **Environment Variables:**
  ```ini
  ELEXON_API_BASE_URL=https://data.elexon.co.uk/bmrs/api/v1
  ELEXON_HTTP_TIMEOUT=30.0
  DEFAULT_START_DATE=2026-01-01
  DEFAULT_END_DATE=2026-01-31
  DEFAULT_CUTOFF_TIME_UK=11:00
  CORS_ORIGINS=https://wind-forecast-omega.vercel.app,http://localhost:3000,http://localhost:5173
  DEBUG=False
  ```
* **Healthcheck:** `GET /api/health`

### B. Frontend Deployment (Vercel)

1. **Live Production URL:** [https://wind-forecast-omega.vercel.app/](https://wind-forecast-omega.vercel.app/)
2. **Vercel Project Setup:**
   * **Root Directory:** `frontend`
   * **Framework Preset:** `Vite`
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist`
3. **Environment Variables in Vercel:**
   ```ini
   VITE_API_URL=https://your-backend-service.onrender.com
   ```
4. **SPA Routing:** `frontend/vercel.json` is configured with rewrites so deep routes navigate to `index.html` without 404 errors.

---

## 8. Accuracy Calculations & Testing Suite

### A. Accuracy Formulations & Market Risk

$$\text{Signed Error}_i = \text{Forecast}_i - \text{Actual}_i \quad (\text{MW})$$

* **Mean Absolute Error (MAE):**
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |\text{Forecast}_i - \text{Actual}_i| \quad (\text{MW})$$
  *Measures average error magnitude. Half-hour volume deviation in MWh is computed as $\text{MAE} \times 0.5\text{ h}$.*
* **Root Mean Squared Error (RMSE):**
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (\text{Forecast}_i - \text{Actual}_i)^2} \quad (\text{MW})$$
  *Heavily penalizes extreme forecast blowouts. The spread $(\text{RMSE} - \text{MAE})$ quantifies error volatility.*
* **Mean Bias (Signed Directional Error):**
  $$\text{Bias} = \frac{1}{N} \sum_{i=1}^{N} (\text{Forecast}_i - \text{Actual}_i) \quad (\text{MW})$$
  *Positive ($>0$) = Overforecasting (Utility under-buys in Day-Ahead; left short at cashout prices).*
  *Negative ($<0$) = Underforecasting (Utility over-buys; surplus power physically spills).*
* **Weighted Absolute Percentage Error (WAPE):**
  $$\text{WAPE} = \frac{\sum_{i=1}^{N} |\text{Forecast}_i - \text{Actual}_i|}{\sum_{i=1}^{N} \text{Actual}_i} \times 100\%$$
  *Normalized against total monthly generation. If $\sum \text{Actual} == 0$, WAPE safely returns `null`.*
* **Why MAPE is Omitted:** When wind generation drops near zero MW, $\frac{|F - A|}{A}$ divides by near-zero, generating false $10,000\%+$ percentage spikes. WAPE is mathematically immune to zero-division distortion.

### B. Automated Test Suite (23 Passing Tests)

The test suite runs with **zero network dependency** using deterministic fixtures:

```bash
python -m pytest backend/tests -v
```

```text
backend/tests/test_api.py::test_health_endpoint PASSED
backend/tests/test_api.py::test_metadata_endpoint PASSED
backend/tests/test_api.py::test_analysis_endpoint_success PASSED
backend/tests/test_api.py::test_analysis_endpoint_invalid_date_range PASSED
backend/tests/test_api.py::test_analysis_demo_mode PASSED
backend/tests/test_api.py::test_analysis_exact_timestamp_matching PASSED
backend/tests/test_bmrs_client.py::test_cache_write_and_read PASSED
backend/tests/test_bmrs_client.py::test_fetch_fuelhh_uses_cache PASSED
backend/tests/test_bmrs_client.py::test_fetch_fuelhh_retry_on_server_error PASSED
backend/tests/test_bmrs_client.py::test_fetch_windfor_network_failure PASSED
backend/tests/test_forecast_selector.py::test_cutoff_calculation_gmt PASSED
backend/tests/test_forecast_selector.py::test_cutoff_calculation_bst PASSED
backend/tests/test_forecast_selector.py::test_strict_lookahead_exclusion PASSED
backend/tests/test_forecast_selector.py::test_latest_eligible_selection PASSED
backend/tests/test_forecast_selector.py::test_hourly_block_resolution_matching PASSED
backend/tests/test_forecast_selector.py::test_exact_timestamp_resolution_matching PASSED
backend/tests/test_forecast_selector.py::test_deduplication_of_records PASSED
backend/tests/test_metrics.py::test_mae_calculation PASSED
backend/tests/test_metrics.py::test_rmse_calculation PASSED
backend/tests/test_metrics.py::test_bias_calculation PASSED
backend/tests/test_metrics.py::test_wape_calculation PASSED
backend/tests/test_metrics.py::test_wape_zero_denominator_safe PASSED
backend/tests/test_metrics.py::test_empty_records_metrics PASSED

============================== 23 passed in 1.36s ==============================
```

---

## 9. Genuine January 2026 Analytical Findings

Ingesting genuine Elexon BMRS observations for the entire month of January 2026 ($N = 1,488$ half-hour periods) with the configured 11:00 D-1 Day-Ahead cutoff yields:
* **Analysis Window:** 2026-01-01 00:00:00Z to 2026-01-31 23:30:00Z ($31 \text{ days} \times 48 \text{ settlement periods}$)
* **Data Completeness:** $100.0\%$ ($1,488 / 1,488$ valid pairs)
* **Mean Absolute Error (MAE):** $2,126.12 \text{ MW}$
* **Root Mean Squared Error (RMSE):** $2,620.80 \text{ MW}$
* **Mean Bias:** $+1,840.30 \text{ MW}$ *(systematic day-ahead overforecasting by National Grid ESO across January 2026)*
* **Weighted Absolute Percentage Error (WAPE):** $18.36\%$
* **Total Wind Energy Delivered:** $8,616,068.5 \text{ MWh}$ (~8.62 TWh)
* **Total Wind Energy Forecasted:** $9,985,249.0 \text{ MWh}$ (~9.99 TWh)

---

## 10. Technical Demo Outline (10 Minutes)

### Part 1 — Customer & Market Analyst Presentation (5 Minutes)
1. **The Commercial Procurement Challenge (1 min):** Wholesale power purchasing in UK day-ahead auction; volume imbalance risks from wind intermittency.
2. **Dashboard Demonstration (2 min):** Real Elexon January 2026 data, MAE ($2,126.1 \text{ MW}$), RMSE ($2,620.8 \text{ MW}$), and Mean Bias ($+1,840.3 \text{ MW}$ short risk).
3. **Interactive Charts & Decision Analysis (1.5 min):** Forecast vs. Actual overlay with zoom brush, Signed Error profile identifying extreme deviation days.
4. **Decision Support Scope (0.5 min):** Empirical error distributions for risk hedging and reserve sizing; transparent decision support without automated trade execution.

### Part 2 — Technical & Architectural Review (5 Minutes)
1. **Architecture & Ingestion (1 min):** FastAPI backend, React 19 frontend, streaming from Elexon BMRS `/FUELHH` and `/WINDFOR` with local disk caching.
2. **Look-Ahead Bias Elimination (1.5 min):** Strict enforcement of 11:00 D-1 wholesale cutoff, GMT/BST timezone translation, and hourly-to-half-hourly resolution matching.
3. **Automated Testing Suite (1.5 min):** 23 pytest tests passing in 1.36s, zero-denominator safety, and deterministic synthetic demo fixtures.
4. **Containerization & Deployment (1 min):** Multi-stage Docker builds, Docker Compose, Nginx reverse proxy, and Vercel cloud configuration.

## 11. Honest Disclosures, Limitations & AI Tool Usage

* **AI Tool Usage:** Antigravity (Google DeepMind agentic coding assistant) was utilized for scaffolding, test generation, and frontend component assembly. All code, analytical logic, schemas, and mathematical metrics were verified.
* **Limitations & Known Edge Cases:**
  * National Grid ESO publishes `WINDFOR` at hourly resolution, while `FUELHH` outturn is half-hourly. The default `hourly_block` strategy maps hourly forecasts to both half-hours; the `exact_timestamp` option provides strict timestamp matching.
  * Elexon BMRS API can experience intermittent rate limits or latency during heavy stream downloads; the local cache ensures high availability once data has been fetched.
* **Deployment Notice:** Local Docker Compose and development servers have been verified. Cloud deployment URLs (Vercel/Render) are ready to be connected with repository credentials.
