# 10-Minute Video Demo Script: Wind Forecast Intelligence

**Target Duration:** Exactly 10:00 (Split into two 5:00 segments)  
**Format:** Screen recording with voiceover / slide presentation  
**Audience:**  
* **Part 1 (00:00 – 05:00):** Head of Power Trading & Renewable Procurement Analysts  
* **Part 2 (05:00 – 10:00):** Technical Architecture Board & Lead Data Engineers  

---

## Part 1: Customer & Market Analyst Presentation (00:00 – 05:00)

### [00:00 – 01:00] 1. The Commercial Procurement Problem
* **Visual:** Slide / diagram illustrating Day-Ahead power exchange order book, physical delivery curve, and Balancing Mechanism imbalance cashout.
* **Speaker:**
  > "Welcome. If you are an electricity supplier or utility operating in Great Britain, your single largest volume exposure is renewable generation intermittency. In the UK Day-Ahead wholesale market—specifically the EPEX SPOT and Nord Pool auctions—procurement bids must be locked in by **11:00 AM London time on Day D-1** for all 48 half-hour settlement periods of delivery Day D.
  >
  > Every megawatt-hour of wind generation you misjudge creates direct cash risk. If National Grid ESO's wind forecast over-predicts output—which we term **Positive Bias**—your portfolio ends up short. That unhedged deficit falls into the Balancing Mechanism, where system buy prices frequently spike to hundreds of pounds per megawatt-hour. Conversely, under-forecasting leaves you over-procured, forcing distress sales or spill charges.
  >
  > Today, I am demonstrating **Wind Forecast Intelligence**, an analytics dashboard engineered specifically to eliminate look-ahead bias and quantify your day-ahead wind forecast risk using genuine Elexon BMRS market data."

### [01:00 – 02:30] 2. Executive Dashboard Walkthrough & Live Observations
* **Visual:** Screen recording of `http://localhost:5173/`. Cursor hovers over header, live status badge, and KPI cards.
* **Speaker:**
  > "Here is our main operational dashboard, currently connected live to the Elexon BMRS API feeds for the entire month of **January 2026**—representing 1,488 continuous 30-minute delivery periods.
  >
  > Look at our top KPI cards:
  > * Our **Mean Absolute Error (MAE)** is **2,126.1 Megawatts**. In energy terms, that represents over 1,063 MWh of deviation across the national grid in every half-hour block.
  > * Our **Root Mean Squared Error (RMSE)** is **2,620.8 MW**. Because RMSE penalizes large quadratic swings, this tells trading desks that severe forecast misses are clustering around rapid weather transitions.
  > * Most importantly, look at our **Mean Bias**: **+1,840.3 MW**, flagged with our amber overforecasting risk badge. This reveals that across January 2026, the day-ahead forecasts available at auction gate closure systematically over-predicted wind outturn by nearly 1.8 Gigawatts on average. A procurement manager relying blindly on nominal forecasts would have been consistently short in physical delivery."

### [02:30 – 04:00] 3. Interactive Time-Series & Signed Error Deep Dive
* **Visual:** Pan down to the *Forecast vs. Actual* Recharts chart. Drag the brush slider to zoom into January 8–14. Hover over an extreme error spike.
* **Speaker:**
  > "Let's inspect the physical delivery curves. The blue line represents the selected Day-Ahead Forecast published prior to the 11:00 AM cutoff; the teal line represents observed `FUELHH` actual generation outturn.
  >
  > Using the timeline brush, we zoom directly into the second week of January. Hovering over January 10th at 14:00 (Settlement Period 29), we see that National Grid ESO predicted 18,200 MW, but actual outturn dropped to 13,400 MW—a massive 4,800 MW positive imbalance.
  >
  > Below the line chart, our **Signed Error Profile** charts $Forecast - Actual$ around a strict zero baseline. Notice the sea of amber bars above zero during the second and third weeks. This visual signature immediately alerts traders to multi-day synoptic weather stalls where numerical weather prediction models overestimated turbine output."

### [04:00 – 05:00] 4. Settlement Audit Table & Decision Support Scope
* **Visual:** Scroll down to the *Settlement Period Audit Table*. Filter by status 'Valid Pair', search for '2026-01-15', and click 'Export CSV'.
* **Speaker:**
  > "At the bottom of the interface, every individual 30-minute block is audited with full transparency: target delivery timestamp, forecast publication timestamp, configured decision cutoff, forecast MW, actual MW, signed error, and validation status.
  >
  > Analysts can filter by date or missing data, and with one click on **Export CSV**, download the entire audited dataset into Excel or Python models.
  >
  > Crucially, **Wind Forecast Intelligence does not claim to execute automated market trades**. It is an analytical intelligence platform designed to arm your trading desk with empirical error distributions, enabling informed de-biasing, risk-adjusted bid shaping, and hedging strategies before auction gate closure."

---

## Part 2: Technical Architecture & Engineering Review (05:00 – 10:00)

### [05:00 – 06:15] 1. Full-Stack Architecture & Data Ingestion
* **Visual:** Architecture diagram in slide / terminal showing FastAPI backend, Pydantic models, and HTTPX client.
* **Speaker:**
  > "Moving to the technical implementation. The platform is designed with a strict separation of concerns across a modern, decoupled full-stack architecture:
  > * The backend is powered by **Python 3.11, FastAPI, Pandas, and Pydantic v2**.
  > * The frontend is built on **React 19, TypeScript, Vite, Tailwind CSS, and Recharts**.
  >
  > For data ingestion, we interface directly with the **Elexon BMRS Open Data API**:
  > * For actuals, we stream from `/datasets/FUELHH/stream`, filtering for fuel type `WIND`.
  > * For forecasts, we query `/datasets/WINDFOR/stream`, capturing rolling revisions from National Grid ESO.
  >
  > Our `BMRSClient` utilizes asynchronous HTTPX with exponential backoff retries, connection timeouts, and a persistent local JSON disk cache in `backend/data/cache`. When a query for January 2026 is executed the first time, all 18,688 forecast revisions and 1,488 actual outturns are fetched in 5.7 seconds. Subsequent queries execute from cache in **340 milliseconds**, completely insulating trading operations from upstream Elexon latency or downtime."

### [06:15 – 07:45] 2. Forecast Selection Engine & Look-Ahead Bias Prevention
* **Visual:** Code walkthrough of `backend/app/services/forecast_selector.py` showing `compute_decision_cutoff` and `match_and_analyze_forecasts`.
* **Speaker:**
  > "The most analytically critical requirement of this project is **strict forecast selection without look-ahead bias**.
  >
  > We cleanly separate three distinct timestamps:
  > 1. `delivery_start_time`: When power is delivered.
  > 2. `publish_time`: When the forecast was published by ESO.
  > 3. `decision_cutoff_time`: When trading decisions must be frozen.
  >
  > For our default Day-Ahead Auction cutoff, our engine calculates the cutoff as **11:00 AM UK local time on Day D-1**. We explicitly normalize between UTC and `Europe/London` using Python's `zoneinfo` module. In winter (GMT), 11:00 London time is 11:00 UTC. During British Summer Time (BST), it automatically shifts to 10:00 UTC, perfectly respecting clock transitions.
  >
  > For every delivery period, our selection algorithm strictly filters:
  > $$\text{Candidate Forecasts where } \text{publishTime} \le \text{decision\_cutoff}$$
  > Any forecast published after cutoff—such as intraday updates or real-time measurements—is strictly rejected. Among eligible forecasts, we select the one with the maximum publication timestamp: the freshest information available to the trader prior to gate closure.
  >
  > Furthermore, we identified an analytical nuance during API inspection: ESO issues `WINDFOR` at 60-minute resolution, while `FUELHH` is 30-minute. Our engine provides two modes: `hourly_block` (standard wholesale mapping where hour $H$ covers both half-hours) and `exact_timestamp` (which marks :30 periods as `MISSING_FORECAST`)."

### [07:45 – 09:00] 3. Testing Rigor & Synthetic Fixture Demo Mode
* **Visual:** Terminal executing `pytest backend/tests -v` (showing 23 tests passing) and `npm run build` in `frontend`.
* **Speaker:**
  > "Analytical correctness is verified by comprehensive, deterministic automated testing. Let's run our test suite:
  >
  > As you see on screen, **all 23 pytest tests pass in 1.36 seconds**.
  > * We verify MAE, RMSE, Bias, and WAPE against known, hand-calculated mathematical benchmarks.
  > * We test zero-denominator handling: if actual wind generation sums to zero, WAPE returns `null` rather than crashing with division-by-zero.
  > * We test daylight saving transitions, duplicate record deduplication, missing actuals, and post-cutoff forecast rejection.
  >
  > In the frontend, our TypeScript production build passes with **zero lint or type errors**.
  >
  > Furthermore, per assignment requirements, we maintain a dedicated **Demo Mode** using deterministic synthetic fixtures. If Elexon API access is interrupted or an offline demonstration is required, the user can toggle Demo Mode in the header. The UI immediately displays an amber warning banner clearly stating that synthetic simulated values are active, ensuring synthetic figures are never misrepresented as genuine Elexon observations."

### [09:00 – 10:00] 4. Containerization, Deployment & Summary
* **Visual:** Open `docker-compose.yml`, `backend/Dockerfile`, and `frontend/Dockerfile`. Browser tab showing frontend running.
* **Speaker:**
  > "For deployment, the entire application is containerized with production-ready multi-stage Dockerfiles:
  > * `backend/Dockerfile` builds a hardened Python 3.11 slim image with curl healthchecks and unbuffered logging.
  > * `frontend/Dockerfile` uses multi-stage compilation: Node 22 builds the static Vite bundle, and an alpine Nginx server handles SPA routing, gzip compression, and reverse-proxying `/api` requests.
  > * `docker-compose.yml` orchestrates both services with healthcheck dependencies and mounts `./backend/data/cache` for persistent caching.
  > * For cloud deployment, the frontend is configured with `vercel.json` rewrites for Vercel, and the backend is ready for deployment to any container platform like Render, Railway, or AWS App Runner with dynamic CORS origins.
  >
  > In conclusion, **Wind Forecast Intelligence** delivers an analytically bulletproof, look-ahead-bias-free, and enterprise-grade forecasting dashboard for UK electricity procurement. Thank you."
