# Chennai Water Bank

**Bank the Rain. Reduce the Flood. Secure the Future.**

Chennai Water Bank is a browser-based, simulation-driven digital prototype of a distributed urban rainwater management network. It models local “Water Bank” nodes that decide whether calculated runoff should be stored, routed toward an eligible recharge pathway, diverted for safety, or released through controlled discharge.

Every node, rainfall value, quality reading and impact result in the demo is **simulated data**. The prototype does not claim to stop Chennai flooding, represent government measurements, or constitute a validated digital twin.

## Problem

Chennai can face intense storm runoff and local drainage stress while also experiencing dry-period water-security and groundwater pressure. The prototype explores a complementary question: can suitable stormwater be retained closer to where it falls, reducing immediate downstream volume while strengthening local water inventory?

## Solution

Six fictional demonstration nodes represent urban catchments in Velachery, T. Nagar, Adyar, Anna Nagar, Perungudi and Tambaram. A normalized digital sensor simulator supplies rainfall, storage, soil, drain-stress and illustrative quality inputs. An explainable engine applies safety gates, capacity constraints and transparent priority scores before allocating every litre.

## Architecture

![Chennai Water Bank AI Architecture](Docs/architecture.png)

### Dual-path design

**Path A — Authoritative**
Live rainfall, storage, recharge capacity, asset status, GIS, and Water Ledger data flow directly to the Water Bank Orchestrator.

**Path B — Semantic**
Operational WaterEvents are indexed in Moss and retrieved as low-latency semantic context for the four collaborative agents:

- Rain & Risk Agent
- Incident Memory Agent
- Capacity Agent
- Asset & Maintenance Agent

The Orchestrator combines authoritative facts, Moss context, and agent findings before presenting guidance to the AI Command Center.

Human operators retain final decision authority.

## Features

- Premium city command center with simulated KPI cards and a no-key Chennai map
- One-click **Simulate Chennai Storm** network event
- Explainable node-level decisions and active water-routing paths
- Eight-scene closed-loop Physical Process explainer tied to current sensor state, node decisions and litre allocations
- Physical, Digital and Combined views showing simulated telemetry, edge/PLC command translation, actuator motion and sensor verification
- Animated engineering handoff clarifying measure → decide → translate → act → verify roles
- Readable bounded typography across dashboard, metrics, controls, sensors, tooltips and explainer cards
- Six predefined engineering scenarios
- **Try Breaking the System** judge mode with live parameter controls
- Dynamic without-vs-with Water Bank comparison
- Exact equations, scores, assumptions and per-decision mass balance
- Optional Firestore persistence with automatic memory fallback
- Projector-friendly Presentation Mode
- Container and scripts for Google Cloud Run

## Simulation methodology

The built-in storm contains eight 15-minute rainfall-intensity pulses. Each node has a synthetic bias so the same network event generates different local rainfall, tank pressure, soil saturation and drain stress. Perungudi intentionally includes an early contaminated-reading demonstration so the safety override is visible. The simulator is deterministic for repeatable live demos.

These values are plausible synthetic assumptions only; they are not measurements.

## Hydrology assumptions

The transparent runoff-volume model is:

```text
runoff_litres = rainfall_mm × catchment_area_m² × runoff_coefficient
```

because 1 mm of rainfall over 1 m² equals 1 litre. Tank headroom is capacity minus current storage. Estimated interval recharge capacity is the configured hourly capacity multiplied by interval duration and a simple unsaturated-soil factor. This is not a hydraulic drainage model, flood-depth model, calibrated catchment model, or site-specific hydrogeological assessment.

## Decision logic

Decision order is safety, immediate runoff management, useful storage, eligible recharge, then controlled discharge. After safety gates, normalized storage, recharge and discharge priority scores are calculated using weights in `src/config/settings.py`. Scores explain priority; physical availability determines litres.

Possible actions are `STORE`, `RECHARGE`, `STORE_AND_RECHARGE`, `DIVERT`, and `CONTROLLED_DISCHARGE`. Every result includes reason codes, a human explanation, rejected alternatives, constraints, scores and a mass-balanced allocation.

## Water-quality safeguards

Illustrative safety rules use contamination, pH, turbidity and first-flush state:

- detected contamination or out-of-range pH forces diversion;
- first flush blocks direct recharge and is diverted in the demo;
- moderate turbidity can permit storage while blocking recharge;
- only water passing the stricter illustrative screen may be considered for recharge;
- high soil saturation and disabled recharge infrastructure also block recharge.

> Prototype water-quality logic is illustrative and requires certified site-specific testing, treatment design, hydrogeological review and regulatory approval before real-world groundwater recharge.

## Installation

Prerequisites: Python 3.12 or later.

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

No credentials or external services are required in the default demo configuration.

## Running locally

```bash
streamlit run app.py
```

For a Cloud Run-equivalent local port:

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8080
```

## Running tests

```bash
pytest
python -m compileall app.py pages src
```

The suite verifies runoff units, physical capacity limits, recharge restrictions, safety overrides, expected scenario families, nonnegative allocations, mass balance, simulator abstraction, impact aggregation and persistence fallback.

## Demo instructions

1. Open **Command Center**; the dashboard is populated immediately in `DEMO_MODE=true`.
2. Click **SIMULATE CHENNAI STORM**.
3. Point out that different nodes store, recharge, divert or discharge according to local state.
4. Open **Node Intelligence** to show the reason codes and highlighted water route.
5. Open **Physical Process**, select **Play System Story**, and follow the eight scenes from rainfall through telemetry, software decision, controller command, actuator movement and feedback verification.
6. Use **Physical**, **Digital**, and **Combined** views or turn **Show Data Flow** off to separate the water infrastructure from the software/control layer.
7. In **Scenario Lab**, select **Heavy rain + contaminated first flush** and verify that recharge is blocked.
8. Select **Extreme rain + storage full + soil saturated** and verify controlled discharge.
9. Use **Manual stress test** so the judge can change conditions.
10. Open **Impact Analytics** and compare calculated immediate downstream runoff.

### Hackathon demonstration script

> “We are not claiming to eliminate Chennai floods. We are demonstrating how distributed intelligence can keep a measurable portion of suitable rainwater from becoming immediate runoff. Every litre is calculated, every safety intervention is visible, and every decision can be challenged.”

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `DATA_BACKEND` | `memory` | `memory` or `firestore` |
| `DEMO_MODE` | `true` | Enables seeded, no-login, zero-service demo behavior |
| `PORT` | `8080` in container | HTTP port honored by the Docker command |
| `GOOGLE_CLOUD_PROJECT` | unset | Optional Firestore project |
| `FIRESTORE_DATABASE` | `(default)` | Optional Firestore database name |

Copy `.env.example` for reference, but do not commit `.env` or service-account JSON files.

## Firestore setup

1. Create a Firestore Native Mode database in the target project and preferred region.
2. Run the service with a dedicated service account granted the minimum Firestore data permissions required for the collections below.
3. Use Application Default Credentials; never bundle a key in the image.
4. Set `DATA_BACKEND=firestore` and `GOOGLE_CLOUD_PROJECT`.
5. Run `python scripts/seed_demo_data.py` in an authenticated environment if the database is empty.

Collections: `nodes`, `simulation_runs`, `node_events`, `decisions`, and `impact_snapshots`. If initialization or a health read fails, the app deliberately falls back to seeded memory mode.

## Deploying to Cloud Run

The image runs Streamlit on `0.0.0.0` and `${PORT:-8080}` as a non-root user.

Current demonstration deployment (19 August 2026):

- Project: `chennai-water-bank`
- Service: `chennai-water-bank`
- Region: `asia-south1`
- Revision: `chennai-water-bank-00001-qw2`
- URL: <https://chennai-water-bank-1032997828322.asia-south1.run.app>
- Runtime mode: seeded in-memory simulation (`DATA_BACKEND=memory`, `DEMO_MODE=true`); no physical IoT sensors or actuators are connected.

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud run deploy chennai-water-bank \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars DATA_BACKEND=memory,DEMO_MODE=true
```

Or set `GOOGLE_CLOUD_PROJECT` and run `scripts/deploy_cloud_run.sh`; PowerShell users can run `scripts/deploy_cloud_run.ps1 -ProjectId YOUR_PROJECT_ID`. Cloud deployment and IAM require access to the destination GCP account and are intentionally not performed by the application.

For Firestore mode, use a dedicated Cloud Run service account rather than a downloaded key and grant only the required Firestore access. Keep public unauthenticated access only for the time-limited hackathon demo if appropriate.

## Limitations

- No physical IoT sensors or verified Chennai datasets are connected.
- Demonstration locations do not represent installed infrastructure.
- The runoff model omits time of concentration, pipe capacity, topography, tides and coupled catchment hydraulics.
- Recharge estimates do not prove local infiltration, aquifer suitability or water-quality compliance.
- Retained litres do not equal flood depth, damage, or flooding prevented.
- Distributed Water Bank nodes cannot absorb unlimited extreme rainfall and do not replace municipal drainage, wetlands, reservoirs, watershed management or flood-control infrastructure.

## Future IoT integration

Rain gauges, level sensors, flow meters, soil-moisture probes and certified water-quality instruments can connect through an ESP32 or edge gateway over MQTT/HTTPS. An ingestion adapter normalizes messages into the existing `SensorDataSource` contract so the same safety and decision engine remains in place.

The Physical Process page illustrates that future control boundary explicitly: field sensors report through an edge controller or PLC; software evaluates safety and capacity rules; commands return through that controller and a motor driver or relay to a motorized valve; position, flow and destination sensors then verify the result. All devices, packets and commands shown in the current demo remain simulated.

## Future AI roadmap

The current product is **explainable rules + engineering calculations**, not machine learning. Future validated data could support rainfall forecasting, runoff prediction, anomaly detection, storage optimization, predictive valve scheduling and network-wide allocation optimization. Any learned model should remain behind safety gates and expose uncertainty.

## Chennai Water Bank AI

### Existing Water Bank product

The original simulator, hydrology, safety gates, mass-balanced allocation,
impact calculations, GIS view, scenarios and persistence fallback remain the
authoritative product. The AI path is additive and never issues actuator
commands.

### Moss integration

`MossSemanticMemory` is the sole Moss-specific adapter. It uses the official
Python SDK to create or update a WaterEvent index, load that index into the
Cloud Run process and perform bounded semantic retrieval. Moss is disabled by
default. No live Moss claim should be made until a configured account has
successfully completed an end-to-end retrieval test.

### Architecture

```text
Authoritative Water Bank facts ─────────────────────────┐
                                                       │
Meaningful simulated event → WaterEvent → Moss context │
                                      ↓                │
                       Four advisory agents ───────────┤
                                                       ↓
                                            WaterBankOrchestrator
                                                       ↓
                                    Existing Command Center + human review
```

### Authoritative live facts vs semantic context

Current rainfall, storage, recharge capacity, water quality, GIS and allocation
values always come from the structured Water Bank models. Moss stores only
derived WaterEvents and returns contextual evidence. Neither semantic results
nor agent findings can overwrite authoritative facts.

### WaterEvents

A WaterEvent contains a stable event ID, timestamp, asset and zone IDs, event
type, operational summary, risk context, action, outcome, semantic text, source
references and metadata. Events generated from the built-in simulator are
explicitly labelled `SIMULATED DATA` and never presented as Chennai history.

### Four collaborative agents

- **Rain & Risk:** evaluates current simulated rainfall, drain stress and safety context.
- **Incident Memory:** reports only WaterEvents actually retrieved from Moss.
- **Capacity:** uses authoritative numeric tank and recharge capacity.
- **Asset & Maintenance:** combines configured asset state with retrieved context and clearly reports missing physical inspection data.

The agents are typed, transparent advisory modules. No external generative LLM
or autonomous control system is introduced.

### Water Bank Orchestrator

The orchestrator keeps three inputs separate: authoritative facts, Moss semantic
context and agent findings. Independent agents run concurrently, individual
failures are isolated, and the resulting recommendation always defaults to
human approval state `pending`.

### Running locally

Baseline mode requires no Moss account:

```bash
streamlit run app.py
```

### Environment variables

| Variable | Default | Purpose |
|---|---:|---|
| `MOSS_ENABLED` | `false` | Enable real Moss indexing and retrieval |
| `MOSS_PROJECT_ID` | unset | Moss project identifier |
| `MOSS_PROJECT_KEY` | unset | Moss project credential; store securely |
| `MOSS_INDEX_NAME` | `chennai-water-bank-events` | WaterEvent index |
| `MOSS_TOP_K` | `4` | Bounded retrieval result count, clamped to 1–10 |

### Moss setup

1. Create a Moss project and obtain its project ID and project key.
2. Supply credentials through local environment variables or Google Secret Manager.
3. Set `MOSS_ENABLED=true`.
4. Start the application and run Collaborative Analysis for a meaningful simulated event.
5. Confirm that the panel reports `AVAILABLE`, evidence records and measured retrieval latency.

Never commit the project key or place it in a Docker image.

### Tests

The AI tests cover WaterEvent generation, real SDK data contracts through an
injected client, indexing, retrieval, disabled mode, Moss failure fallback,
agent outputs, failure isolation, immutable authoritative facts, measured
latency and pending human approval. Run the complete suite with `pytest`.

### Latency measurement

Moss retrieval, each agent, orchestration and total request durations are
measured with a high-resolution monotonic timer. The UI displays measured
values exactly; it does not contain hard-coded latency claims.

### Failure and fallback behavior

- Moss disabled: the original Water Bank continues unchanged.
- Missing Moss credentials: semantic context is unavailable; startup continues.
- Moss indexing/retrieval failure: no historical evidence is fabricated.
- Individual agent failure: other findings and authoritative facts remain available.
- No physical or verified data: the limitation remains visible.

### Cloud Run deployment

Production must not be overwritten during initial validation. First deploy to a
separate staging service and bind `MOSS_PROJECT_KEY` from Secret Manager. Stop
and obtain explicit approval before any Cloud Run command.

### Demo scenario

Run the existing simulated Chennai storm, open Collaborative AI, choose a
fictional node and run analysis. Demonstrate the unchanged structured facts,
Moss evidence status, four findings, measured timings, limitations and pending
human review in 60–90 seconds.

### Human-in-the-loop safety

Accept, Reject and Request More Evidence update only the presentation workflow.
They do not control valves, pumps, gates or physical recharge equipment. Human
Water Operations remains the final authority.

### Known limitations

- No physical Chennai sensor, incident or maintenance feed is connected.
- Simulator-generated Moss documents are demonstrations, not historical incidents.
- Real Moss latency depends on the configured index, Cloud Run instance and network.
- The current production memory backend is not durable across instance restarts.
