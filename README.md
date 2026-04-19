# Guardian of the Gulf Solution

Guardian of the Gulf is a modular prototype for an intelligent fishing guidance platform focused on the Gulf of Gabes.

This implementation contains:

- a modular FastAPI backend
- a React + TypeScript frontend
- a first MVP intelligence layer for:
  - zone scoring
  - zone recommendation
  - eco-routing
  - lunar guidance
  - safety/SOS context
  - go / caution / no-go departure decision

## Structure

```text
solution/
  backend/
  frontend/
```

## Backend

Main modules:

- `app/domain`: Gabes ports, species profiles, seeded zones
- `app/models`: API and domain response models
- `app/services`: scoring, recommendation, lunar, routing, safety, bathymetry, regulations, fleet, community reports
- `app/db` and `app/repositories`: SQLite persistence for auth, fisherman profiles, fleet positions, and reports
- `app/api/routes`: endpoint layer

Bathymetry data:

- `backend/data/bathymetry/carte_marine_tunisie.nc`
- source used by the backend: GEBCO offline NetCDF grid
- used for point depth lookup, local slope estimation, and zone depth enrichment

Regulatory map data reused from TraeFishing:

- `backend/data/regulation_maps/carte_tunisie_bleu.PNG`
- `backend/data/regulation_maps/carte_tunisie_bleu_foncee.PNG`
- `backend/data/regulation_maps/carte_tunisie_mauve.PNG`
- `backend/data/regulation_maps/carte_true_gulf_gabes.PNG`
- `backend/data/regulation_maps/carte_true_gulf_tunis.PNG`
- `backend/data/regulation_maps/carte_trois_bleu_tunisie.PNG`

Important MVP endpoints:

- `GET /api/v1/admin/overview`
- `GET /api/v1/zones/heatmap`
- `GET /api/v1/zones/recommend`
- `GET /api/v1/route/optimize`
- `GET /api/v1/lunar/today`
- `GET /api/v1/pollution/point`
- `GET /api/v1/pollution/zone/{zone_id}`
- `GET /api/v1/pollution/overview`
- `GET /api/v1/satellite/point`
- `GET /api/v1/satellite/zone/{zone_id}`
- `GET /api/v1/sonar/status`
- `POST /api/v1/sonar/predict`
- `GET /api/v1/weather/point`
- `GET /api/v1/weather/port/{port_id}`
- `GET /api/v1/safety/status`
- `GET /api/v1/safety/status/me`
- `POST /api/v1/safety/check-in`
- `POST /api/v1/safety/sos`
- `GET /api/v1/safety/events/me`
- `GET /api/v1/bathymetry/depth`
- `GET /api/v1/mission/briefing`
- `GET /api/v1/mission/history`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `PUT /api/v1/auth/profile`
- `GET /api/v1/mission/briefing/me`
- `GET /api/v1/mission/history/me`
- `POST /api/v1/fleet/position`
- `GET /api/v1/fleet/active`
- `GET /api/v1/fleet/load/{zone_id}`
- `POST /api/v1/reports/submit`
- `GET /api/v1/reports/recent`
- `GET /api/v1/reports/nearby`
- `GET /api/v1/reports/zone/{zone_id}`
- `GET /api/v1/regulations/check`
- `GET /api/v1/regulations/check/me`

Run backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend

Frontend goals:

- React-based
- mobile-first
- premium map-first UX
- low-text, field-ready interface
- fallback data if backend is unavailable
- real Leaflet mission map
- PWA installability and offline-aware behavior
- browser GPS with last known position fallback

Run frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend is configured to query the backend at:

- `http://127.0.0.1:8000/api/v1`

## Admin Dashboard

The solution now includes a dedicated territorial/admin dashboard.

Frontend path:

- `/admin`

Backend endpoint:

- `GET /api/v1/admin/overview`

This admin view is designed for:

- cooperative operators
- territorial monitoring staff
- safety supervisors
- demo juries who need to see the system-level impact, not only a single fisherman view

It currently aggregates:

- active fleet pressure
- open SOS incidents
- stressed zones
- recent mission decisions
- recent community reports
- source freshness / data health

## Default Admin Login

For local demo convenience, the backend now seeds a default admin user at startup.

Default local admin credentials:

- email: `admin@gulf.local`
- password: `GuardianAdmin123!`

Important:

- this is a local demo credential and should be changed before any real deployment
- admin access is recognized from configured admin emails
- the seed can be controlled through `.env`

Relevant environment variables:

- `ADMIN_SEED_ENABLED=true`
- `ADMIN_SEED_EMAIL=admin@gulf.local`
- `ADMIN_SEED_PASSWORD=GuardianAdmin123!`
- `ADMIN_EMAILS=admin@gulf.local`

## Frontend Experience

The current frontend is no longer a static dashboard mock. It includes:

- a real Leaflet-based operational map
- mission overlays for:
  - recommended zone
  - alternative zones
  - route corridor
  - Ghannouch pollution plume
  - live or cached fisherman position
- a React PWA shell with:
  - installable manifest
  - service worker
  - cached app shell
  - cached viewed map sectors for offline reuse
- offline-first field actions:
  - queued safety `check-in`
  - queued `SOS`
  - queued community reports
- browser geolocation support with:
  - live GPS tracking when available
  - cached last known position fallback
  - automatic position injection into safety and report actions

Important note on offline maps:

- the current map offline mode caches sectors that were already viewed
- it is not yet a fully prepacked MBTiles/Gabes tile bundle
- this is strong enough for MVP/demo use, but not yet the final terrain-grade offline map strategy

## SQLite Auth and Profile

The backend now creates a local SQLite database automatically at:

- `backend/data/guardian_of_gulf.db`

Stored data includes:

- fisherman account
- password hash
- boat profile
- license type
- fuel capacity and consumption
- fishing gears
- target species
- emergency contacts
- local bearer-like session tokens
- fleet position history
- zone saturation snapshots derived from active boats
- community field reports from fishermen

## Dynamic Fleet and Reports

The backend now includes two product differentiators:

- live fleet load estimation from SQLite position updates
- community reporting that can improve or penalize a zone

Mission briefing now also produces an operational departure decision:

- `GO`
- `CAUTION`
- `NO_GO`

This decision combines:

- regulation status
- route risk and shallow bathymetry
- marine weather severity
- safety readiness

Mission briefings are now also persisted in SQLite with:

- mission history per request
- latest recommendation trace
- source freshness metadata for weather, satellite, pollution, fleet, regulation, and bathymetry

Zone scoring now combines:

- legal status
- pollution risk
- bathymetry
- bathymetric slope
- marine weather and sea-state readiness
- route distance
- lunar factor
- dynamic fleet saturation
- recent community catch or hazard reports

## Marine Weather

Weather is now implemented from the reusable StormGlass logic found in `traefishing/app/routes/zone_checker.py`.

- live source when `STORMGLASS_API_KEY` is configured
- safe fallback forecast when the key is absent or the API is unavailable
- data exposed for both coordinates and known departure ports
- mission briefing now includes weather for the recommended fishing zone

Set the API key before running the backend if you want live marine weather:

```bash
set STORMGLASS_API_KEY=your_key_here
```

## Copernicus Marine Satellite

Satellite and model-driven ocean context is now wired through Copernicus Marine.

- SST dataset: `SST_MED_SST_L4_NRT_OBSERVATIONS_010_004_a_V2`
- chlorophyll dataset: `cmems_obs-oc_med_bgc-plankton_nrt_l3-multi-1km_P1D`
- turbidity dataset: `cmems_obs_oc_med_bgc_tur-spm-chl_nrt_l4-hr-mosaic_P1D-m`
- salinity dataset: `cmems_mod_med_phy-sal_anfc_4.2km-2D_PT1H-m`
- currents dataset: `cmems_mod_med_phy-cur_anfc_4.2km-2D_PT1H-m`

The backend uses the official Copernicus Marine toolbox approach for authenticated subsetting and point extraction, with safe fallback logic when credentials or dependencies are missing.

Satellite observations are also cached in SQLite so repeated requests for the same zone do not trigger unnecessary remote subsetting.

## Weather Persistence

Marine weather forecasts are now persisted in SQLite, not only cached in memory.

- weather snapshots survive process restarts
- repeated requests can reuse recent persisted forecasts
- forecast history is now available in the local data layer

## Pollution Data Layer

The backend now includes a first structured pollution layer with:

- contamination source registry
- pollution observation table
- plume history table
- time-based plume propagation using weather, currents, and nearby pollution reports

This pollution layer is also connected to zone scoring, so pollution pressure is no longer only a static seed.

Set credentials before running the backend if you want live Copernicus access:

```bash
set COPERNICUSMARINE_SERVICE_USERNAME=your_username
set COPERNICUSMARINE_SERVICE_PASSWORD=your_password
```

These satellite signals now help score zones alongside:

- law and closures
- weather and sea state
- bathymetry
- surface salinity for coastal water mass stability
- real turbidity for coastal water quality and plume pressure
- fleet saturation
- community reporting

## Optional Sonar Module

The backend now exposes an optional sonar inference module for fishermen who have a compatible sensor.

- model file expected by default: `solution/sonar_best_model.pkl`
- optional scaler file: `solution/sonar_scaler.pkl`
- raw input: `60` normalized sonar bands
- engineered input: `11` extra features, for `71` total model features

Endpoints:

- `GET /api/v1/sonar/status`
- `POST /api/v1/sonar/predict`

The sonar module returns:

- `Rock` vs `Mine/Fish Target`
- confidence score
- estimated bearing in degrees + cardinal direction
- relative distance band
- engineered sonar features used in the prediction

Important note:

- `bearing` and `distance` are physics-inspired proxies from the training notebook, not GPS coordinates
- if `sonar_scaler.pkl` is absent, the service still runs in a degraded mode and assumes incoming sonar values already match the normalized training distribution

## Safety Workflow

Safety is now more than a passive status endpoint.

- authenticated fishermen can send a `check-in`
- authenticated fishermen can trigger an `SOS`
- safety events are persisted in SQLite
- safety events also feed the fleet trace with the reported location
- safety status for a logged-in fisherman now reflects the last check-in and open incidents
- SMS delivery through Twilio is supported for `check-in` and `SOS` when enabled in `.env`

Required SMS environment variables:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_SMS_FROM_NUMBER`
- `SMS_NOTIFICATIONS_ENABLED=true`
- optional `TWILIO_ALERT_TO_NUMBERS=+216..., +216...`

## Fleet Balancing

Fleet balancing is now more predictive than a simple live boat count.

- active fleet positions still contribute to zone load
- recent mission recommendations are also counted as inbound pressure
- zone pressure blends active boats and recent assignments to reduce herd behavior

## MVP User Story

A fisherman departing from Zarrat opens the app, sees a premium heatmap of the Gulf of Gabes, receives a recommended zone that avoids pollution and congestion, gets a route estimate, checks lunar fishing guidance, and can trigger an SOS flow.

## Notes

- The backend uses seeded domain data and rule-based logic for the MVP.
- The frontend is React-based and mobile-first.
- The architecture is intentionally modular so real satellite, fleet, auth, and legal data can be integrated later.
- The current implementation uses seeded data and rule-based logic to keep the MVP coherent and demo-ready.
