# CrisisMind — Multi-Crisis AI Decision Platform

> **"CrisisMind doesn't just monitor a crisis. It predicts what happens next and helps responders decide what to do."**

## Quick Start Instructions

### 1. Run the Python FastAPI Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
The backend starts at `http://localhost:8000`.
Interactive Swagger API Documentation: `http://localhost:8000/docs`

### 2. Run the React + Vite Frontend
```bash
cd frontend
npm install
npm run dev
```
The frontend starts at `http://localhost:3000`.

## New: SQL database + Google Maps

**1. Backend (SQL):** `cd backend && cp .env.example .env` — then run `python main.py`.
The SQL schema is in `backend/database/schema.sql` (tables: `users`, `sessions`, `incident_reports`, `action_log`, `simulation_runs`, `integrity_ledger`). It is applied automatically on startup; the DB file is `backend/crisismind.db`. Change it with `DATABASE_PATH` in `backend/.env`.

**2. Frontend (Google Maps key):** `cd frontend && cp .env.example .env` — paste your key in `VITE_GOOGLE_MAPS_API_KEY=` (enable *Maps JavaScript API* in Google Cloud), set `VITE_MAP_CENTER_LAT/LNG` to your city, then `npm install && npm run dev`.

**What gets saved per user:** account (PBKDF2-hashed password), incident reports with map location, every approved action, and every What-If simulation run. See them on the **My Data** page.

## 15 Fully Working Core Pages Included
1. **Command Centre** — Executive 5-second judge demo overview (NOW -> +60m, Recommended / Avoid / Backup)
2. **Live Crisis Map / Digital Twin** — 2D & 3D tilt tactical canvas with real-time risk zones & fleet vectors
3. **Crisis Detection** — Anomaly detection across IoT sensors, acoustic sensors, and citizen feeds
4. **Future Risk Forecast** — Temporal predictions at NOW, +15, +30, +45, +60 minutes
5. **Crisis Cascade** — Interactive failure propagation graph: Fire -> Road Closure -> Traffic Jam -> Ambulance Delay -> Hospital Overload
6. **Smart Route Intelligence** — Turn-by-turn clearance, blockage probability, and vehicle class authorization
7. **What-If Simulator** — Tactical sandbox with live risk recalculation & strategy comparisons
8. **AI Recommendations** — Explainable decision engine: What is happening -> What will happen next -> Recommended actions
9. **Emergency Resources** — Live fleet deployment (Fire engines, HazMat, Ambulances, Recon Drones)
10. **Hospitals & Shelters** — Surge capacity, ICU bed tracking, and diversion rules
11. **Alerts** — CAP-standard multi-channel broadcast center (Cell broadcast, Sirens, Radio)
12. **Data Intelligence / Source Trust** — Multi-sensor contradiction resolver with reliability weighting
13. **Integrity Ledger** — Cryptographic SHA-256 tamper-evident audit ledger
14. **Analytics** — KPI dashboards: -43% ETA improvement, -37% casualty risk reduction
15. **Incident Autopsy** — Root cause analysis, missed warnings, and counterfactual retrospective

## Multi-Crisis Scenarios
- **Fire**: Chemical Warehouse Battery Explosion (Default)
- **Flood**: Flash Flood & Dam Levee Breach
- **Road Accident**: 18-Wheeler Fuel Tanker Highway Pileup
- **Chemical Incident**: Anhydrous Ammonia High-Pressure Rupture
- **Crowd Emergency**: Stadium Stampede & Concourse Choke
- **Storm**: Supercell Microburst & 138 km/h Wind Shear

Built for emergency response teams, defense crisis centers, and municipal civil protection.
