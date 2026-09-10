# 1. Title Page

# CHENNAI WATER BANK

## Evidence-Based Technical Development Write-up and Software Engineering Report

**Document purpose:** Academic project documentation, technical viva and review, placement or interview discussion, software architecture review, engineering evaluation, stakeholder presentation, and future maintenance.

**Codebase audited:** `C:\Users\User\Documents\ChatGPT\Chennai Water Bank`

**Audit date:** 17 August 2026

**Repository revision:** Initial uncommitted Git worktree; no commit hash is available.

**Author / institution:** Not specified in the repository.

**System status:** Simulation-driven software prototype. No physical IoT sensor, PLC, pump, motorized valve, or installed Chennai Water Bank node is connected.

---

## Evidence classification used in this report

Every technical passage is governed by the evidence label printed at its start:

- **VERIFIED FROM CODE** — directly established by current source code, data files, automated tests, or execution of the current code.
- **VERIFIED FROM CONFIGURATION** — established by requirements, runtime, Streamlit, Docker, environment, or deployment configuration.
- **VERIFIED FROM VERSION HISTORY** — would require commits, tags, blame, or diffs. No statement in this report uses this label because the repository has no commits.
- **INFERRED FROM IMPLEMENTATION** — a careful engineering interpretation of the code, not a documented historical fact.
- **PROPOSED FUTURE ARCHITECTURE** — a recommended deployment design that is not implemented today.

Where a paragraph mixes present and future concerns, the classification is stated again at the point of transition. Runtime validation is included under **VERIFIED FROM CODE** because it records the behavior obtained by executing the audited code. Supplied development-session evidence is identified explicitly and is never represented as Git history.

---

# 2. Executive Summary

**VERIFIED FROM CODE.** Chennai Water Bank is a browser-based, simulation-driven prototype for exploring distributed urban rainwater management. It represents six fictional demonstration nodes, calculates runoff volumes, classifies simulated water quality, screens eligibility for storage and modelled recharge, allocates every incoming litre to storage, modelled recharge, safety diversion, or controlled discharge, and displays the result through nine Streamlit pages.

The current implementation is a Python 3.12 Streamlit application. Its principal engineering strength is the separation between physical-domain concepts and software responsibilities:

```text
Physical concept                         Current software responsibility
Rainfall and catchment                  Generate or accept normalized readings
First-flush isolation                   Apply a deterministic safety gate
Filtration / quality checking           Classify simulated turbidity, pH and contamination
Storage tank                            Enforce finite headroom
Recharge pathway                        Screen interval capacity and soil saturation
Controlled downstream discharge        Account explicitly for residual volume
Sensors and actuator                    Explain future closed-loop integration visually
```

**VERIFIED FROM CODE.** The decision engine is not machine learning. It applies transparent rules, centralized prototype thresholds, normalized priority scores, and physical-capacity constraints. Safety checks occur before beneficial routing. Unsafe or first-flush water is prevented from direct recharge. `Allocation.mass_balance_error_l` makes conservation visible for every decision.

**VERIFIED FROM CODE.** The Physical Process page consumes the same `DecisionResult` and simulated `SensorState` used elsewhere. Python inserts those values into a 713-line HTML/CSS/JavaScript template. The JavaScript controls eight presentation scenes, route highlighting, packets, tank-level animation, and simulated actuator motion; it does not perform a second hydrology or decision calculation.

**VERIFIED FROM CONFIGURATION.** The default backend is seeded in-process memory. An optional Firestore adapter uses Application Default Credentials and falls back to memory if initialization or a health read fails. A Dockerfile targets Python 3.12 on Cloud Run, runs as a non-root user, exposes port 8080, and includes a Streamlit health check.

**VERIFIED FROM CODE.** Validation on 17 August 2026 produced 28 passing tests in 2.73 seconds, successful bytecode compilation, a clean Streamlit startup and health response, HTTP 200 responses for all nine route URLs, and no broken installed requirements. Visual browser-console inspection could not be repeated during this audit because the browser-control security layer rejected the localhost URL; this limitation is recorded rather than bypassed.

**INFERRED FROM IMPLEMENTATION.** The project is well suited to a judge-facing engineering prototype because it prioritizes determinism, explainability, failure-resistant demo behavior, and visible scientific limitations. It is not yet a production water-control system. Real deployment would require calibrated field data, certified water-quality and hydrogeological work, a secure ingestion service, an industrial edge controller or PLC, interlocks, fail-safe local control, authenticated commands, physical actuators, commissioning, and regulatory approval.

# 3. Problem Statement

**VERIFIED FROM CODE.** The problem encoded by the application is the coexistence of intense local storm runoff, finite drainage capacity, and the value of retaining suitable rainwater closer to where it falls. The software explores whether a distributed node can capture runoff, separate first flush, apply an illustrative quality screen, store suitable water, route eligible water toward a modelled recharge pathway, and release unavoidable residual water through a controlled downstream path.

The application deliberately does not calculate flood depth, drainage-pipe hydraulics, travel time, tidal backwater, damage, watershed routing, or city-wide hydraulic interactions. It therefore reports **estimated immediate runoff retained at the modelled catchment**, not flooding prevented.

**VERIFIED FROM CODE.** The implementation addresses two related but different systems:

1. **Physical water system.** Proposed civil, plumbing, treatment, storage, recharge, drainage, sensing, electrical, and mechanical infrastructure through which actual water would move.
2. **Chennai Water Bank software.** A digital layer that normalizes readings, calculates simplified runoff, applies deterministic safety and capacity logic, simulates a distributed network, explains route decisions, aggregates volume outcomes, and visualizes a possible controller-actuator feedback loop.

The present repository proves the second system and illustrates the first. It does not prove installed physical infrastructure.

# 4. Objectives

**VERIFIED FROM CODE.** The implemented objectives are:

1. Represent distributed Water Bank nodes with catchment, storage, and recharge parameters.
2. Provide deterministic synthetic sensor values for repeatable demonstrations.
3. Convert rainfall depth into estimated runoff volume with explicit units.
4. Apply contamination, pH, turbidity, and first-flush gates before beneficial routing.
5. Constrain storage and modelled recharge by finite configured capacity.
6. Allocate all incoming runoff without negative quantities or unaccounted volume.
7. Explain selected and rejected routing alternatives.
8. Compare multiple node responses to the same rainfall profile.
9. Aggregate stored, recharged, diverted, controlled-discharge, retained, and downstream volumes.
10. Provide a Scenario Lab for repeatable and manual stress tests.
11. Explain the physical-to-digital-to-physical loop without claiming live hardware.
12. Preserve a replaceable `SensorDataSource` boundary for future adapters.
13. Remain usable without credentials through seeded memory mode.
14. Remain deployable as a Python 3.12 Streamlit container.

**INFERRED FROM IMPLEMENTATION.** Likely stakeholder objectives are rapid technical demonstration, judge interrogation of assumptions, non-engineer comprehension, and a credible path from simulation to a pilot. No separate signed requirements specification is present, so these stakeholder motives are interpretations rather than historical facts.

# 5. System Overview

**VERIFIED FROM CODE.** A user enters the system through `app.py`, which configures the Streamlit page, renders simulation disclosures in the sidebar, and opens the Command Center. Streamlit discovers the numbered modules under `pages/` and exposes the remaining eight views through its built-in multipage navigation.

```text
User / reviewer
      |
      v
Streamlit multipage interface
      |
      +--> Command Center / Node / Scenario / Network / Impact views
      +--> Decision / Architecture / About documentation views
      +--> Physical Process iframe explainer
      |
      v
Streamlit runtime state and cache
      |
      +--> deterministic DigitalSensorSimulator
      +--> scenario runner
      |
      v
Hydrology + quality gates + DecisionEngine
      |
      v
DecisionResult + Allocation + ImpactSnapshot
      |
      +--> charts, tables, maps, text explanations and animation
      +--> memory repository or optional Firestore node repository
```

**VERIFIED FROM CODE.** The full deterministic network event contains eight rainfall-intensity pulses and six nodes, producing 48 `SimulationStep` records. The simulator deep-copies repository nodes, so tank updates during one run do not mutate the stored baseline objects.

**VERIFIED FROM CODE.** Executing the current eight-pulse network produced 1,036,746.82 L of modelled runoff: 279,122.62 L stored, 9,489.71 L routed toward modelled recharge, 39,716.24 L diverted, and 708,418.25 L assigned to controlled discharge. The resulting estimated immediate retention was 288,612.33 L, or 27.84%. These are deterministic prototype outputs from the current configuration, not field measurements.

# 6. Physical Water-Management Process

**VERIFIED FROM CODE.** The Physical Process page preserves the following conceptual chain:

```text
RAINFALL
   |
   v
ROOF / CATCHMENT
   |
   v
FIRST FLUSH
   |
   v
FILTRATION
   |
   v
QUALITY GATE
   |
   v
MOTORIZED ROUTER
   |
   +--> STORE
   +--> MODELLED RECHARGE
   +--> SAFETY DIVERSION / CONTROLLED DISCHARGE
```

The stages have different levels of numerical implementation:

| Stage | Physical meaning | Current software representation | Numerical status |
|---|---|---|---|
| Rainfall | Water arriving at the catchment | Scenario depth or deterministic intensity profile | Calculated / simulated |
| Roof / catchment | Surface collection and conveyance | Area and runoff coefficient | Calculated |
| First flush | Initial pollutant-bearing runoff isolated from beneficial routing | Boolean `first_flush_active`; direct recharge is blocked and the demo diverts it | Rule-based; no first-flush volume model |
| Filtration | Physical treatment before routing | Animated illustrative treatment train | Visual only; no filter-loss or treatment-performance equation |
| Quality gate | Suitability screen | Contamination, pH, and turbidity classification | Deterministic illustrative rules |
| Motorized router | Valve or routing mechanism | Command mapping and animation | Simulated presentation; no hardware I/O |
| Store | Finite tank or sump | Headroom and stored allocation | Calculated |
| Modelled recharge | Engineered trench, pit, or well | Interval capacity × unsaturated-soil factor | Simplified capacity screen only |
| Downstream path | Treatment, diversion, or controlled release | Residual allocation | Calculated volume; no pipe hydraulics |

**VERIFIED FROM CODE.** Recharge means routing already screened water toward an engineered infiltration or recharge structure so that water may percolate into the subsurface. In this project it is always described as **modelled recharge**. The calculation is not evidence that a Chennai site can accept the water. Certified site-specific water testing, treatment design, geotechnical and hydrogeological assessment, civil design, and regulatory approval remain mandatory.

# 7. Software Requirements

## 7.1 Functional requirements

**VERIFIED FROM CODE.** The implemented functional requirements are:

- load a seeded network of demonstration nodes;
- display rainfall, capacity, storage, soil, drain-stress, flow, quality, and route values;
- simulate a repeatable multi-pulse rainfall event;
- calculate runoff for each node and pulse;
- screen water quality and first flush;
- calculate available storage and eligible modelled recharge volume;
- produce a deterministic route and litre allocation;
- expose reason codes, scores, rejected alternatives, constraints, and mass balance;
- support predefined and manually configured scenarios;
- display node maps, tables, stacked bars, area charts, a donut chart, and before/after volume comparison;
- provide start, pause-label, reset, and full-event controls;
- animate an eight-scene physical/digital/control explanation;
- support Physical, Digital, and Combined visualization modes;
- preserve visible simulation and recharge warnings;
- load optional Firestore nodes while falling back safely to memory.

## 7.2 Non-functional requirements

**VERIFIED FROM CODE AND CONFIGURATION.** The code supports the following non-functional qualities:

- **Determinism:** fixed rainfall profiles and node-specific synthetic biases produce repeatable results.
- **Safety ordering:** quality and first-flush gates precede beneficial routing.
- **Scientific honesty:** disclosures identify simulated data, prototype estimates, fictional demonstration nodes, and recharge limitations.
- **Maintainability:** models, calculations, rules, persistence, simulation, and UI live in separate packages.
- **Resilience:** memory fallback prevents an unavailable Firestore service from blanking the demo.
- **Accessibility support:** the explainer uses labels, focusable sensor tooltips, an `aria-live` scene panel, semantic controls, and a reduced-motion media query.
- **Responsive presentation:** wide Streamlit layout, bounded font sizes, responsive grids, and a Presentation Mode are implemented.
- **Deployability:** the container listens on `0.0.0.0:$PORT`, runs as a non-root user, and exposes a health check.

**INFERRED FROM IMPLEMENTATION.** Formal response-time, availability, throughput, browser-support, accessibility-conformance, and recovery-time targets were not documented. The current network is small enough that algorithmic performance is not a practical constraint, but this has not been established by a load test.

# 8. Programs, Languages and Technologies Used

## 8.1 Python

**VERIFIED FROM CONFIGURATION.** The audited virtual environment uses Python 3.12.13, and the Docker image is based on `python:3.12-slim`.

**Purpose and use.** Python implements domain models, simulation, hydrology, rules, decision logic, persistence adapters, impact aggregation, page controllers, and tests. Dataclasses make data contracts explicit, enums constrain route and quality states, abstract base classes define replaceable input and repository boundaries, and standard-library validation protects numerical domains.

## 8.2 Streamlit

**VERIFIED FROM CONFIGURATION.** `requirements.txt` declares `streamlit>=1.39,<2`; the audited environment contains 1.61.1.

**Purpose and use.** Streamlit provides the multipage browser interface, navigation, session state, cache, widgets, charts, tables, metrics, sidebar, theme configuration, and iframe embedding. It suits a prototype because Python domain logic and interactive UI can be developed in one process.

## 8.3 pandas

**VERIFIED FROM CONFIGURATION.** The declared range is `pandas>=2.2,<3`; version 2.3.3 was installed.

**Purpose and use.** pandas builds node, event, formula, summary, and analytics tables and prepares grouped data for Plotly charts.

## 8.4 Plotly

**VERIFIED FROM CONFIGURATION.** The declared range is `plotly>=5.24,<7`; version 6.9.0 was installed.

**Purpose and use.** Plotly renders the no-key node map, allocation donut, before/after bar, priority bar, network area chart, and node-level stacked impact chart.

## 8.5 HTML, CSS and JavaScript

**VERIFIED FROM CODE.** Custom CSS in `src/ui/theme.py` defines the dark navy/teal visual system. A standalone HTML/CSS/JavaScript template in `src/ui/templates/physical_process.html` implements the closed-loop explainer inside a Streamlit iframe. JavaScript manages only view and animation state.

## 8.6 Google Cloud Firestore client

**VERIFIED FROM CONFIGURATION.** `google-cloud-firestore>=2.19,<3` is declared; 2.28.1 was installed.

**Purpose and use.** The optional adapter reads and writes node documents and can save whitelisted event collections. It uses Application Default Credentials; no service-account file is stored in the repository.

## 8.7 pytest

**VERIFIED FROM CONFIGURATION.** `pytest>=8.3,<10` is declared; 9.1.1 was installed.

**Purpose and use.** pytest verifies units, validation, safety overrides, scenario families, allocation invariants, simulator abstraction, impact aggregation, command mapping, explainer disclosures, and persistence fallback.

## 8.8 NumPy

**VERIFIED FROM CONFIGURATION AND CODE.** `numpy>=2.0,<3` is declared and 2.5.2 was installed, but no application, script, or test imports NumPy. It is therefore a configured but currently unused direct dependency.

## 8.9 Docker and Google Cloud Run configuration

**VERIFIED FROM CONFIGURATION.** `Dockerfile` and Bash/PowerShell scripts configure source-based Cloud Run deployment. The image runs Streamlit as a non-root user, exposes port 8080, and performs a health request against `/_stcore/health`.

**VERIFIED FROM CODE.** Docker and `gcloud` executables were not available in the audited local environment, so no container build or Cloud Run deployment was executed.

## 8.10 Git

**VERIFIED FROM CONFIGURATION.** Git 2.55.0.windows.3 was available and a `.git` worktree exists. However, `main` has no commits, every project file is untracked, no remote is configured, and `git log` reports that the branch has no commits. Git cannot provide development milestones or historical diffs for this report.

# 9. Development Environment

**VERIFIED FROM CONFIGURATION.** The audited environment was Windows with PowerShell, a project-local `.venv`, and Python 3.12.13. The application was reachable on port 8501, while a separate clean validation instance was started on `127.0.0.1:8511` and then stopped after its health check succeeded.

The project can be installed and run with:

```powershell
cd "C:\Users\User\Documents\ChatGPT\Chennai Water Bank"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

**VERIFIED FROM CONFIGURATION.** No IDE metadata proves that VS Code, PyCharm, or another editor was used. No `package.json`, `tsconfig.json`, Node build, Ruff, Flake8, mypy, coverage, pre-commit, or GitHub Actions configuration exists. These tools are therefore not presented as part of the verified development environment.

# 10. Project Folder Structure

**VERIFIED FROM CODE.** Simplified audited tree:

```text
Chennai Water Bank/
├── app.py
├── README.md
├── requirements.txt
├── pytest.ini
├── Dockerfile
├── .env.example
├── .streamlit/
│   └── config.toml
├── data/
│   └── demo_nodes.json
├── pages/
│   ├── 01_command_center.py
│   ├── 02_node_intelligence.py
│   ├── 03_scenario_lab.py
│   ├── 04_network_simulation.py
│   ├── 05_impact_analytics.py
│   ├── 06_decision_explainer.py
│   ├── 07_solution_architecture.py
│   ├── 08_about_solution.py
│   └── 09_physical_process.py
├── scripts/
│   ├── seed_demo_data.py
│   ├── deploy_cloud_run.ps1
│   └── deploy_cloud_run.sh
├── src/
│   ├── config/settings.py
│   ├── decision/{engine,explainer,rules}.py
│   ├── hydrology/{runoff,storage,recharge}.py
│   ├── impact/calculator.py
│   ├── models/{node,sensor_state,decision,scenario}.py
│   ├── persistence/{repository,memory_repository,firestore_repository}.py
│   ├── simulation/{rainfall,scenarios,simulator}.py
│   └── ui/
│       ├── command_center.py
│       ├── components.py
│       ├── physical_process.py
│       ├── runtime.py
│       ├── scenario_controls.py
│       ├── theme.py
│       └── templates/physical_process.html
└── tests/
    ├── test_decision_engine.py
    ├── test_impact.py
    ├── test_persistence.py
    ├── test_physical_process.py
    ├── test_recharge.py
    ├── test_runoff.py
    ├── test_scenarios.py
    └── test_storage.py
```

The separation is purposeful: domain code under `src/` has no dependency on page filenames; `pages/` composes domain and reusable UI functions; `data/` carries seed configuration; `tests/` checks invariants; and deployment concerns remain at the root or under `scripts/`.

# 11. Software Architecture

**VERIFIED FROM CODE.** The application is a modular monolith. There is one Streamlit process, not a separately deployed frontend and backend.

```text
PRESENTATION LAYER
pages/*.py, src/ui/*.py, Plotly, physical_process.html
                         |
                         v
APPLICATION/RUNTIME LAYER
src/ui/runtime.py, src/ui/scenario_controls.py
                         |
             +-----------+-----------+
             v                       v
SIMULATION LAYER                  DECISION LAYER
DigitalSensorSimulator           rules.py + DecisionEngine
rainfall.py + scenarios.py       explainable DecisionResult
             |                       |
             +-----------+-----------+
                         v
DOMAIN CALCULATION LAYER
runoff.py, storage.py, recharge.py, impact/calculator.py
                         |
                         v
MODEL LAYER
WaterBankNode, SensorState, ScenarioDefinition,
SimulationStep, Allocation, DecisionResult, ImpactSnapshot
                         |
                         v
PERSISTENCE BOUNDARY
Repository -> MemoryRepository or FirestoreRepository
```

**VERIFIED FROM CODE.** Important boundaries are:

- `SensorDataSource.read(node, step_index) -> SensorState` decouples the simulator from a future telemetry adapter.
- `Repository` decouples UI/runtime node loading from memory or Firestore.
- `DecisionEngine.evaluate(...) -> DecisionResult` encapsulates routing policy.
- `Allocation` encapsulates conservation and downstream/retained properties.
- `physical_process_animation(...)` consumes a decision and readings but does not mutate domain state.

**INFERRED FROM IMPLEMENTATION.** This architecture likely evolved from the need to keep a live demo reliable while showing a credible deployment path. That is an architectural inference, not a reconstruction from commits.

## 11.1 APIs and data exchange

**VERIFIED FROM CODE.** The current version does not expose a dedicated REST, GraphQL, FastAPI, Flask, or WebSocket application API. Browser interaction is handled by Streamlit's own protocol. Domain layers exchange Python objects, and the Physical Process renderer transfers one JSON payload into its embedded iframe.

The optional Firestore adapter uses the Firestore Python client directly from the server process; it is not an HTTP endpoint owned by this project. Consequently there is no project endpoint inventory with methods and URLs to document.

**PROPOSED FUTURE ARCHITECTURE.** A real telemetry deployment would require explicit ingestion and command APIs with authenticated schemas, validation, timestamps, quality flags, command IDs, acknowledgements, and audit events. Those endpoints do not exist today.

## 11.2 Database and persistence model

**VERIFIED FROM CODE.** Default mode is not a database: `MemoryRepository` loads `data/demo_nodes.json` into an in-process dictionary keyed by `node_id`, returns deep copies, and stores transient events in lists. Process termination discards those events.

The optional Firestore node schema is derived from `WaterBankNode`:

```text
node_id, name, zone, latitude, longitude,
catchment_area_m2, runoff_coefficient,
storage_capacity_l, current_storage_l,
recharge_capacity_l_per_hour, recharge_available
```

Firestore collection `nodes` uses `node_id` as document ID when seeded. The adapter also permits `simulation_runs`, `node_events`, `decisions`, and `impact_snapshots`; their payload is a generic dictionary, and no formal schema or relationship is defined in current source. The UI does not call `save_event()`.

## 11.3 Evidence-constrained development journey

**INFERRED FROM IMPLEMENTATION.** Because no commits exist, an actual chronological narrative cannot be proven. The following is a dependency-ordered reconstruction of how such a working version is logically assembled, not a claim about dates or developer actions:

1. define the problem boundary and simulated-data disclosures;
2. model nodes, sensor state, decisions, allocations, and scenarios;
3. implement unit-aware runoff, storage, and recharge functions;
4. implement quality gates before route allocation;
5. add the deterministic sensor simulator and six-node event loop;
6. add impact aggregation and mass-balance checks;
7. add repository boundaries and seeded demo resilience;
8. compose Streamlit command, node, scenario, network, impact, explainer, architecture, and about pages;
9. add the physical/digital closed-loop animation using existing state;
10. add regression tests, container configuration, and Cloud Run scripts;
11. refine readability and strengthen scenario-to-animation telemetry.

This sequence explains technical dependencies for maintenance and viva discussion while preserving the absence of version-history evidence.

# 12. Module-by-Module Development

## 12.1 Command Center

**VERIFIED FROM CODE.**

- **Purpose:** give a network-level operational summary.
- **User input:** Simulate, Start, Pause, Reset, and a displayed speed selector.
- **Processing:** `load_nodes()`, `get_active_steps()`, `run_full_storm()`, `latest_steps()`, and `network_impact()`.
- **Output:** ten KPI cards, map, route donut, intervention count, node table, before/after chart, and final report.
- **Files:** `app.py`, `pages/01_command_center.py`, `src/ui/command_center.py`, `src/ui/runtime.py`, `src/ui/components.py`.
- **Dependencies:** Streamlit state/cache, pandas, Plotly, simulation, impact model, and repository.

The initial page uses four simulated pulses so it is populated immediately; a full run replaces that baseline with eight pulses in session state.

## 12.2 Node Intelligence

**VERIFIED FROM CODE.**

- **Purpose:** inspect the latest decision for one demonstration node.
- **User input:** node selection.
- **Processing:** chooses the latest `SimulationStep`, derives tank and allocation metrics, and forwards the same result into the physical-process renderer.
- **Output:** selected action, reasons, rejected alternatives, six state metrics, quality table, route diagram, four allocation metrics, animation, constraints, and mass balance.
- **Files:** `pages/02_node_intelligence.py`, `src/ui/components.py`, `src/ui/physical_process.py`.

## 12.3 Scenario Lab

**VERIFIED FROM CODE.**

- **Purpose:** challenge the rules with predefined or manual conditions.
- **User input:** scenario selection or sliders/toggles for rainfall, catchment, coefficient, tank, recharge, soil, drain stress, turbidity, pH, first flush, and recharge availability.
- **Processing:** creates a `ScenarioDefinition`, calls `run_scenario()`, then evaluates runoff and routing.
- **Output:** decision, routing flow, allocation metrics, priority scores, reasons, and displayed equations.
- **Files:** `pages/03_scenario_lab.py`, `src/simulation/scenarios.py`, `src/ui/scenario_controls.py`.

`dataclasses.replace` derives manual scenarios from a known base, and `st.session_state["manual_scenario"]` preserves the last submitted case across Streamlit reruns.

## 12.4 Network Simulation

**VERIFIED FROM CODE.**

- **Purpose:** demonstrate different node outcomes under one shared rainfall profile.
- **User input:** Run full network event.
- **Processing:** six deep-copied nodes × eight pulses; each pulse reads synthetic sensors, converts intensity to depth, calculates runoff, evaluates routing, and updates only tank storage.
- **Output:** node map, retained/downstream area chart, current action/quality/tank/soil table, and network volume caption.
- **Files:** `pages/04_network_simulation.py`, `src/simulation/simulator.py`, `src/ui/runtime.py`.

## 12.5 Impact Analytics

**VERIFIED FROM CODE.**

- **Purpose:** aggregate where modelled runoff went.
- **User input:** none beyond whichever storm state is active.
- **Processing:** converts decisions to `ImpactSnapshot` objects and sums their fields.
- **Output:** received, stored, modelled-recharge and retention KPIs; without/with comparison; engineering interpretation; stacked node chart.
- **Files:** `pages/05_impact_analytics.py`, `src/impact/calculator.py`, `src/ui/components.py`.

The page states that retained litres are not equivalent to flood depth, damage avoided, or flooding prevented.

## 12.6 Decision Explainer

**VERIFIED FROM CODE.**

- **Purpose:** expose the safety hierarchy, equations, score formulas, thresholds, mass balance, assumptions, and limitations.
- **User input:** expand/collapse limitations.
- **Processing:** static constants in `src/decision/explainer.py` and centralized settings.
- **Output:** decision order, formula tables, prototype thresholds, and scientific warning.
- **Files:** `pages/06_decision_explainer.py`, `src/decision/explainer.py`, `src/config/settings.py`.

## 12.7 Solution Architecture

**VERIFIED FROM CODE.**

- **Purpose:** distinguish current simulator architecture from a future sensor gateway.
- **User input:** none.
- **Processing:** documentation-only page.
- **Output:** current flow, future ingestion boundary, rules-versus-future-AI distinction, and persistence explanation.
- **Files:** `pages/07_solution_architecture.py`.

## 12.8 About Solution

**VERIFIED FROM CODE.**

- **Purpose:** explain the problem, principle, scope, non-claims, and a 60-second demonstration sequence.
- **User input:** none.
- **Processing:** documentation-only page.
- **Output:** capability and limitation statements with the recharge safety notice.
- **Files:** `pages/08_about_solution.py`.

## 12.9 Physical Process

**VERIFIED FROM CODE.**

- **Purpose:** connect physical water movement, simulated sensing, software decisions, control translation, actuator motion, and feedback.
- **User input:** routing demonstration; Play, Pause, Restart, Next Step; view mode; data-flow toggle; fullscreen explainer.
- **Processing:** `run_scenario()` produces the values and `DecisionResult`; Python safely replaces template tokens; JavaScript runs a deterministic eight-scene presentation state machine.
- **Output:** physical and digital layers, sensors, telemetry packets, software stages, controller/relay/actuator chain, route animation, feedback status, legend, and disclosures.
- **Files:** `pages/09_physical_process.py`, `src/ui/physical_process.py`, `src/ui/templates/physical_process.html`.

# 13. Simulation Model

## 13.1 Rainfall profile

**VERIFIED FROM CODE.** `CHENNAI_STORM_PROFILE_MM_HR` contains:

```text
(8, 22, 48, 82, 108, 76, 42, 18) mm/hr
```

At the configured 15-minute interval, `rainfall_depth_for_interval()` multiplies intensity by `15/60`. These values are deterministic assumptions, not Chennai observations.

## 13.2 Synthetic node differentiation

**VERIFIED FROM CODE.** `DigitalSensorSimulator.read()` derives a stable node bias from the character codes in `node_id`. It modifies intensity by at most approximately ±6%, advances soil saturation by six percentage points per step plus positive bias, and derives drain stress from rainfall intensity and the node’s current tank percentage. Values are clamped to physical percentage ranges.

Perungudi node `WB-PER-05` is intentionally marked contaminated at steps 0, 1, and the last step. Contaminated readings use turbidity 42 NTU and pH 6.2; ordinary first flush uses 18 NTU; later non-contaminated readings use 3.2 NTU and pH 7.2. This is a demonstration mechanism, not measured quality data.

## 13.3 Network time step

**VERIFIED FROM CODE.** For each pulse and node, the simulator:

1. obtains a `SensorState`;
2. converts intensity into interval rainfall depth;
3. calculates runoff litres;
4. calls `DecisionEngine.evaluate()` with the interval length;
5. increases `current_storage_l` by the stored allocation, capped at capacity;
6. records `storage_before_l` and `storage_after_l` in `SimulationStep`.

Soil state is generated from step number rather than updated from recharge allocation. Modelled recharge does not create a subsurface storage state. These are material simplifications.

## 13.4 Predefined scenarios

**VERIFIED FROM CODE.** Six `ScenarioDefinition` objects cover moderate storage, heavy rain with recharge, contaminated first flush, exhausted capacity, multiple retention paths, and dry readiness. Executing the current scenarios produced:

| Scenario | Runoff L | Action | Stored L | Recharged L | Diverted L | Controlled L |
|---|---:|---|---:|---:|---:|---:|
| Moderate storage | 6,912.00 | STORE | 6,912.00 | 0.00 | 0.00 | 0.00 |
| Heavy / nearly full | 41,000.00 | STORE_AND_RECHARGE | 3,000.00 | 14,752.94 | 0.00 | 23,247.06 |
| Contaminated first flush | 17,850.00 | DIVERT | 0.00 | 0.00 | 17,850.00 | 0.00 |
| Capacity exhausted | 90,720.00 | CONTROLLED_DISCHARGE | 0.00 | 0.00 | 0.00 | 90,720.00 |
| Multiple retention | 28,080.00 | STORE_AND_RECHARGE | 12,000.00 | 6,635.29 | 0.00 | 9,444.71 |
| Dry readiness | 0.00 | STORE readiness state | 0.00 | 0.00 | 0.00 | 0.00 |

All six reported a mass-balance error of 0.0 L in the audited execution.

# 14. Core Algorithms and Calculations

## 14.1 Rainfall depth

**VERIFIED FROM CODE.**

```text
rainfall_depth_mm = rainfall_intensity_mm_hr × interval_minutes / 60
```

The predefined Scenario Lab directly supplies event `rainfall_mm`; the network simulator derives interval depth from intensity.

## 14.2 Runoff volume

**VERIFIED FROM CODE.**

```text
runoff_l = rainfall_depth_mm × catchment_area_m2 × runoff_coefficient
```

The identity is valid because 1 mm over 1 m² equals 1 litre. The coefficient is constrained to 0–1. This is a volume estimate, not a flow-routing model.

## 14.3 Storage headroom

**VERIFIED FROM CODE.**

```text
available_storage_l = max(0, capacity_l - min(current_l, capacity_l))
stored_l = min(incoming_l, available_storage_l)
```

`WaterBankNode.__post_init__()` also clamps current storage between zero and capacity.

## 14.4 Modelled recharge screen

**VERIFIED FROM CODE.** Recharge availability is zero if infrastructure is disabled, quality is not eligible, first flush is active, or soil saturation reaches the 85% block threshold. Otherwise:

```text
soil_factor = max(0, 1 - soil_saturation_percent / saturation_block_percent)
eligible_recharge_l = capacity_l_per_hour × interval_minutes / 60 × soil_factor
```

For example, 12,000 L/h over 30 minutes at 42.5% soil saturation with an 85% block threshold gives a factor of 0.5 and an eligible volume of 3,000 L. This exact case is tested.

## 14.5 Mass balance

**VERIFIED FROM CODE.**

```text
incoming_l
= stored_l
 + recharged_l
 + diverted_l
 + controlled_discharge_l
```

`mass_balance_error_l` is incoming minus those four outputs. Parametrized tests assert an absolute error below `1e-7` for all predefined scenarios, and the network test applies the same invariant to every step.

## 14.6 Impact aggregation

**VERIFIED FROM CODE.**

```text
retained_l = stored_l + recharged_l
immediate_downstream_l = diverted_l + controlled_discharge_l + overflow_l
retention_percentage = 100 × retained_l / stormwater_received_l
```

`overflow_l` exists in `ImpactSnapshot` but is never populated by the current simulation; residual safe water is represented as controlled discharge.

# 15. Decision and Routing Logic

## 15.1 Safety order

**VERIFIED FROM CODE.** `DecisionEngine.evaluate()` executes in this order:

1. reject negative incoming volume;
2. classify quality;
3. compute storage and recharge availability and explanatory scores;
4. divert all water if contamination, pH, or turbidity makes it unsafe;
5. divert all water if first flush is active;
6. return readiness mode for zero inflow;
7. for storage-only quality, fill available tank headroom and divert the residual;
8. for safe water, allocate across storage, modelled recharge, and controlled discharge;
9. generate reasons, rejected alternatives, constraints, priority, and mass balance.

## 15.2 Quality rules

**VERIFIED FROM CODE.**

| Condition | Classification | Routing consequence |
|---|---|---|
| `contamination_detected` | `UNSAFE_DIVERT` | all incoming water diverted |
| pH below 6.5 or above 8.5 | `UNSAFE_DIVERT` | all incoming water diverted |
| first flush active | `SUITABLE_FOR_STORAGE_ONLY` from classifier, followed by explicit first-flush diversion in engine | all incoming water diverted in this prototype |
| turbidity ≤ 5 NTU | `SAFE_FOR_RECHARGE` | storage/recharge may be considered |
| 5 < turbidity ≤ 25 NTU | `SUITABLE_FOR_STORAGE_ONLY` | recharge blocked; tank first, residual diverted |
| turbidity > 25 NTU | `UNSAFE_DIVERT` | all incoming water diverted |

These are illustrative prototype thresholds, not regulatory approval or treatment certification.

## 15.3 Safe allocation

**VERIFIED FROM CODE.** Safe water is allocated as follows:

- no storage headroom: use eligible recharge, then controlled discharge;
- no recharge capacity: use storage, then controlled discharge;
- tank below 75% and entire inflow fits: store all;
- otherwise initially store 35% when tank is at least 75%, or 60% below 75%;
- recharge the next available portion;
- use remaining tank headroom if recharge was insufficient;
- assign the residual to controlled discharge.

The scores explain priority but do not directly optimize litre allocation.

## 15.4 Priority scores

**VERIFIED FROM CODE.** Inputs are clamped to 0–1. The current formulas are:

```text
storage = 0.45 × storage_ratio
        + 0.35 × drain_stress
        + 0.20 × tank_headroom

recharge = 0.40 × recharge_ratio
         + 0.25 × unsaturated_soil
         + 0.20 × drain_stress
         + 0.15 × tank_pressure

discharge = 0.45 × capacity_pressure
          + 0.35 × soil_saturation
          + 0.20 × drain_stress
```

`retention` is the larger of storage and recharge scores. If no recharge volume is available, recharge score is forced to zero.

# 16. State Management

**VERIFIED FROM CODE.** Streamlit’s rerun model is the application state-management mechanism.

| State or cache | Location | Purpose |
|---|---|---|
| cached repository | `@st.cache_resource` in `src/ui/runtime.py` | avoid rebuilding the selected repository on every rerun |
| cached baseline steps | `@st.cache_data` | provide a four-pulse populated default dashboard |
| `storm_steps` | `st.session_state` | hold the full active event after simulation |
| `storm_complete` | `st.session_state` | control completion report visibility |
| `storm_running` | `st.session_state` | display a running/ready label |
| `manual_scenario` | `st.session_state` in Scenario Lab | preserve the submitted manual case |
| current iframe scene | JavaScript variables in iframe | presentation-only scene, timer, tank, and router state |

When a user runs the storm, Python generates a new list of 48 steps, stores it in `storm_steps`, and Streamlit reruns dependent pages against that session state. Maps, charts, tables, KPIs, and impact values are derived from the same list. The iframe receives a snapshot of current values and cannot update Python session state.

**VERIFIED FROM CODE.** No Redux, React Context, Zustand, client-side store, event bus, or independent browser simulation engine exists.

# 17. UI and Visualization Development

**VERIFIED FROM CODE.** The application uses Streamlit’s wide layout with a reusable sidebar and shared CSS. `configure_page()` sets title, icon, wide layout, and expanded navigation; `render_sidebar_context()` provides Presentation Mode and persistent simulation disclosures.

Reusable functions include:

- `hero()` — title, subtitle, simulated-data pill, and prototype badge;
- `kpi_card()` — bounded metric card;
- `section_heading()` — consistent section label and description;
- `decision_card()` — selected action and explanation;
- `routing_flow()` — active route in a compact flow diagram;
- `latest_steps()` — one current record per node;
- `node_map()` — node location and decision markers;
- `before_after_chart()` — immediate downstream comparison;
- `safety_notice()` — certified site-testing warning.

**VERIFIED FROM CODE.** Color semantics are consistent: cyan/teal for data and interface emphasis, blue for water/storage, green for modelled recharge or verified state, amber for discharge or caution, and red for unsafe diversion. Plotly charts use transparent backgrounds to integrate with the theme.

**INFERRED FROM IMPLEMENTATION.** The dark engineering visual language appears selected to support projector demonstrations and to distinguish signals, routes, and states. No design brief records that rationale, so it is an inference.

**VERIFIED FROM CODE.** Current typography uses bounded CSS `clamp()` values for page headings, hero titles, KPI values, decision text, and Streamlit metrics. The Physical Process template includes responsive grids at 1180, 850, and 560 pixels and a reduced-motion rule. A full WCAG audit, keyboard test, screen-reader test, and device matrix are not present.

# 18. Physical Process Animation

## 18.1 Data binding

**VERIFIED FROM CODE.** `pages/09_physical_process.py` selects a real `ScenarioDefinition`, calls `run_scenario()`, calculates post-routing tank percentage, and passes rainfall, turbidity, pH, flow, storage headroom, soil, drain stress, quality, and `DecisionResult` into `physical_process_animation()`.

`physical_process_animation()` clamps percentages, formats values, maps reason codes to readable text, HTML-escapes inserted strings, serializes scene data as JSON, replaces `<` with `\u003c`, and raises an error if a template token remains unresolved.

## 18.2 Command mapping

**VERIFIED FROM CODE.** The visual command mapping is:

| Decision | Simulated command | Router target | Visual angle |
|---|---|---|---:|
| STORE | `ROUTE_TO_STORE` | STORE | -42° |
| RECHARGE | `ROUTE_TO_RECHARGE` | RECHARGE | 0° |
| STORE_AND_RECHARGE | `SPLIT_STORE_RECHARGE` | SPLIT | -12° |
| DIVERT | `ISOLATE_AND_DIVERT` | DIVERT | 42° |
| CONTROLLED_DISCHARGE | `OPEN_CONTROLLED_DISCHARGE` | DISCHARGE | 42° |

These strings do not leave the browser or reach physical hardware.

## 18.3 Eight-scene state machine

**VERIFIED FROM CODE.** A single `scenes` array defines the deterministic story:

| Scene | Title | Duration |
|---:|---|---:|
| 1 | PHYSICAL PROCESS | 4.2 s |
| 2 | SENSE | 4.2 s |
| 3 | COMMUNICATE | 4.2 s |
| 4 | ANALYZE | 4.7 s |
| 5 | DECISION | 4.7 s |
| 6 | SOFTWARE COMMANDS HARDWARE | 4.3 s |
| 7 | MECHANICAL ACTION | 5.0 s |
| 8 | FEEDBACK / VERIFICATION | 6.5 s |

`setScene()` clears previous timers, sets Combined mode, updates title/caption/step indicator, resets simulated readings, animates the actuator in scene 7, and marks the command verified in scene 8. `pause()`, `restart`, and `next` all call `clearTimers()`, reducing duplicate-timer risk.

## 18.4 Engineering distinction

**VERIFIED FROM CODE.** The visual explicitly displays:

```text
SENSOR / MEASURE
    physical reading -> telemetry upward

SOFTWARE / DECIDE
    deterministic safety and capacity decision

EDGE / PLC / TRANSLATE
    command validation, interlocks, motor driver or relay

ACTUATOR / ACT
    electrical power changes motorized valve position

FEEDBACK / VERIFY
    flow and router-position readings return to software
```

The web application is never shown as directly powering the motor.

## 18.5 Current simulation versus deployment

**VERIFIED FROM CODE.** All sensor nodes, packets, controller states, actuator motion, and feedback values are simulated. The template repeatedly displays `NO PHYSICAL IOT SENSOR CONNECTED`, `SIMULATED SENSOR VALUES`, `SIMULATED CONTROL`, and the modelled-recharge warning.

**PROPOSED FUTURE ARCHITECTURE.** In a deployment, physical instruments would produce readings, a PLC or gateway would validate and normalize them, the software would recommend or authorize a route, the PLC would apply local interlocks and energize a driver, and independent position/flow feedback would verify the result.

# 19. Relevant Source Code with Explanation

## 19.1 Runoff calculation

**VERIFIED FROM CODE — `src/hydrology/runoff.py`, `runoff_volume_l()`.**

```python
def runoff_volume_l(
    rainfall_mm: float, catchment_area_m2: float, runoff_coefficient: float
) -> float:
    if rainfall_mm < 0:
        raise ValueError("rainfall_mm cannot be negative")
    if catchment_area_m2 < 0:
        raise ValueError("catchment_area_m2 cannot be negative")
    if not 0 <= runoff_coefficient <= 1:
        raise ValueError("runoff_coefficient must be between 0 and 1")
    return rainfall_mm * catchment_area_m2 * runoff_coefficient
```

**Input.** Rainfall depth in millimetres, catchment area in square metres, and a dimensionless runoff coefficient.

**Processing.** Lines 4–9 reject invalid physical domains. The final multiplication uses the millimetre–square-metre–litre identity.

**Output.** Modelled runoff volume in litres.

**Why required.** Every route allocation needs a single conserved incoming volume.

## 19.2 Recharge capacity screen

**VERIFIED FROM CODE — `src/hydrology/recharge.py`, `recharge_available_l()`.**

```python
if (
    not enabled
    or not quality_allowed
    or first_flush_active
    or soil_saturation_percent >= saturation_block_percent
):
    return 0.0
soil_factor = max(0.0, 1.0 - soil_saturation_percent / saturation_block_percent)
return capacity_l_per_hour * (interval_minutes / 60.0) * soil_factor
```

**Input.** Rated capacity, interval, enabled flag, quality permission, first-flush state, soil saturation, and block threshold.

**Processing.** Non-negotiable gates return zero before any volume is calculated. Eligible capacity is reduced linearly as saturation approaches the block threshold.

**Output.** Maximum modelled recharge volume for the interval.

**Why required.** Recharge must never be presented as unlimited or automatically safe.

## 19.3 Quality gate

**VERIFIED FROM CODE — `src/decision/rules.py`, `evaluate_water_quality()`.**

```python
if state.contamination_detected:
    return WaterQualityStatus.UNSAFE_DIVERT, ("CONTAMINATION_DETECTED",)
if not thresholds.ph_min <= state.ph <= thresholds.ph_max:
    return WaterQualityStatus.UNSAFE_DIVERT, ("PH_OUT_OF_SAFE_RANGE",)
if state.first_flush_active:
    return WaterQualityStatus.SUITABLE_FOR_STORAGE_ONLY, (
        "FIRST_FLUSH_BLOCKS_RECHARGE",
    )
if state.turbidity_ntu <= thresholds.recharge_turbidity_max_ntu:
    return WaterQualityStatus.SAFE_FOR_RECHARGE, ("QUALITY_GATE_PASSED",)
if state.turbidity_ntu <= thresholds.storage_turbidity_max_ntu:
    return WaterQualityStatus.SUITABLE_FOR_STORAGE_ONLY, (
        "TURBIDITY_BLOCKS_RECHARGE",
    )
return WaterQualityStatus.UNSAFE_DIVERT, ("TURBIDITY_UNSAFE",)
```

**Processing.** Conditions are deliberately ordered from decisive safety failures to progressively less restrictive classes. The first satisfied branch returns immediately.

**Output.** A constrained enum and machine-readable reason tuple.

**Why required.** Optimization must never outrank safety.

## 19.4 Capacity-constrained safe allocation

**VERIFIED FROM CODE — `src/decision/engine.py`, `_allocate_safe()`.**

```python
if storage_available <= 0:
    recharged = min(incoming_l, recharge_available)
    return 0.0, recharged, incoming_l - recharged
if recharge_available <= 0:
    stored = min(incoming_l, storage_available)
    return stored, 0.0, incoming_l - stored

if node.storage_percent < 75 and incoming_l <= storage_available:
    return incoming_l, 0.0, 0.0

store_share = 0.35 if node.storage_percent >= 75 else 0.60
stored = min(storage_available, incoming_l * store_share)
recharged = min(incoming_l - stored, recharge_available)
extra_storage = min(
    storage_available - stored, incoming_l - stored - recharged
)
stored += max(0.0, extra_storage)
discharged = max(0.0, incoming_l - stored - recharged)
return stored, recharged, discharged
```

**Input.** Node state, incoming litres, tank headroom, and eligible recharge litres.

**Processing.** Early branches handle unavailable routes. The remaining logic preserves a tank-first preference, creates a split when pressure is higher, backfills unused tank space, and assigns every residual litre to controlled discharge.

**Output.** `(stored, recharged, discharged)`.

**Why required.** It protects capacity and mass balance while keeping the decision explainable.

## 19.5 Replaceable sensor boundary

**VERIFIED FROM CODE — `src/simulation/simulator.py`.**

```python
class SensorDataSource(ABC):
    @abstractmethod
    def read(self, node: WaterBankNode, step_index: int) -> SensorState:
        """Return one normalized reading for a node."""


class DigitalSensorSimulator(SensorDataSource):
    """Deterministic simulated sensor source for repeatable demos and tests."""
```

The business layers consume normalized `SensorState` objects. A future adapter can implement `read()` without altering runoff, routing, impact, or UI contracts. A real deployment would likely require an asynchronous message buffer rather than the step-index signature, but the normalization boundary is already present.

## 19.6 Streamlit state propagation

**VERIFIED FROM CODE — `src/ui/runtime.py`.**

```python
@st.cache_data(show_spinner=False)
def baseline_steps() -> list[SimulationStep]:
    return DigitalSensorSimulator().simulate_network(load_nodes(), steps=4)


def get_active_steps() -> list[SimulationStep]:
    return st.session_state.get("storm_steps", baseline_steps())


def run_full_storm() -> list[SimulationStep]:
    steps = DigitalSensorSimulator().simulate_network(load_nodes())
    st.session_state["storm_steps"] = steps
    st.session_state["storm_complete"] = True
    return steps
```

The baseline enables an immediately populated demo. A full run replaces it for that browser session, and all dependent pages recompute from the same object graph.

## 19.7 Presentation-only animation state

**VERIFIED FROM CODE — `src/ui/templates/physical_process.html`.**

```javascript
const setScene = (index) => {
  clearTimers();
  currentScene = Math.max(0, Math.min(scenes.length - 1, index));
  const scene = scenes[currentScene];
  root.dataset.scene = String(currentScene);
  setMode('combined');
  sceneTitle.textContent = scene.title;
  sceneCaption.textContent = data.captions[currentScene];
  indicator.textContent = `STEP ${currentScene + 1} / ${scenes.length}`;
  if (currentScene < 6) resetPhysicalReadings();
  if (currentScene === 6) animateActuator();
  if (currentScene === 7) showVerification();
};
```

This code changes DOM state only. `data` was already computed by Python. There is no duplicate runoff or routing algorithm in JavaScript.

---

# 20. Testing Methodology

## 20.1 Automated test infrastructure

**VERIFIED FROM CONFIGURATION.** `pytest.ini` limits discovery to `tests/` and adds quiet output. Eight test modules contain 28 collected cases after parametrization.

| Test module | Cases | Verified behavior |
|---|---:|---|
| `test_runoff.py` | 4 | unit identity and rejection of negative depth, negative area, coefficient above 1 |
| `test_storage.py` | 2 | capacity cap and nonnegative headroom |
| `test_recharge.py` | 3 | interval/soil factor, first-flush block, saturation block |
| `test_decision_engine.py` | 10 | unsafe diversion, storage, recharge family, controlled discharge, six-scenario mass balance/nonnegativity |
| `test_scenarios.py` | 2 | `SensorDataSource` implementation and 48-step network invariants |
| `test_impact.py` | 2 | retained formula and network aggregation |
| `test_persistence.py` | 2 | seeded memory and Firestore-failure fallback |
| `test_physical_process.py` | 3 | hardware command mapping, required disclosures/scenes, scenario flow telemetry |

## 20.2 Validation executed for this report

**VERIFIED FROM CODE.** The following commands were executed on 17 August 2026:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall app.py pages src
.\.venv\Scripts\python.exe -m pip check
```

Results:

| Validation | Result |
|---|---|
| pytest | 28 passed in 2.73 s |
| compileall | completed successfully for `app.py`, `pages`, and `src` |
| pip dependency check | no broken requirements found |
| clean Streamlit startup | healthy on `127.0.0.1:8511` |
| existing Streamlit health | `ok` on port 8501 |
| route HTTP checks | `/` and all nine named routes returned 200 |

The route checks prove that the Streamlit server accepts those paths; because Streamlit returns a common bootstrap document, identical response lengths do not prove that every interactive component rendered correctly.

## 20.3 Functional and boundary coverage

**VERIFIED FROM CODE.** Current tests cover zero inflow, negative inputs, a full tank, excess current storage, saturated soil, first flush, contamination, unsuitable pH/turbidity through scenarios, no recharge capacity, mixed retention, and residual discharge. They also check all five final decision actions in the last network pulse.

## 20.4 Testing not present

**VERIFIED FROM CONFIGURATION.** The repository contains no automated browser test, screenshot regression, mobile/device matrix, accessibility scan, load test, coverage report, mutation test, static type check, linter, dependency vulnerability scan, Firestore emulator test, Docker build test, Cloud Run smoke test, hardware-in-loop test, or PLC test.

**VERIFIED FROM CODE.** Browser-console and visual route verification could not be repeated during this audit because the browser-control security policy rejected localhost. The restriction was not bypassed. Existing user-supplied screenshots provide visual context but are not equivalent to a repeatable automated UI test.

# 21. Bugs Observed

## 21.1 Evidence boundary

**VERIFIED FROM CONFIGURATION.** No repository version history, issue tracker, pull request, commit message, tag, or old revision exists. Consequently, the report cannot truthfully claim a dated historical bug sequence or reproduce original source revisions. The first four records below are supported by the supplied development session and current regression evidence; the remaining records are open findings verified directly in the current code.

| ID | Status | Bug / issue | Symptom | Root cause | Fix or disposition | Verification |
|---|---|---|---|---|---|---|
| B-01 | Rectified operationally | Streamlit launched from wrong directory | PowerShell could not find `.\.venv\Scripts\streamlit.exe`; browser showed connection refused | Relative virtual-environment path resolved under `C:\Users\User`, not the project | Change into the project and run its environment | health endpoint and clean startup succeeded |
| B-02 | Rectified operationally | Stale Streamlit process held an earlier function signature | `physical_process_animation()` rejected new `tank_before_percent` argument | long-running process retained older imported module | restart the Streamlit process | current import, startup, compilation, and tests pass |
| B-03 | Rectified in current code | Text too small and some headings disproportionately large | supplied UI was difficult to read | very small fixed template text and earlier responsive density | bounded font scale, larger labels/tooltips, rebalanced headings and grids | current CSS verified; prior visual retest existed in session, but no Git diff is available |
| B-04 | Rectified in current code | Scenario flow sensor could be disconnected from modelled runoff | flow telemetry did not represent scenario volume over duration | scenario state lacked a derived duration-based flow | `incoming_flow_l_per_min = runoff / duration_minutes`, guarded for zero duration | `test_scenario_sensor_flow_matches_current_runoff_and_duration` passes |
| O-01 | Open | Simulation speed selector is cosmetic | `1x`, `5x`, `10x`, and `30x` display different labels but complete with the same delay | loop always executes `time.sleep(0.025)` | connect selected label to duration or remove selector | source inspection |
| O-02 | Open | Pause cannot interrupt the synchronous progress loop meaningfully | pause state is only processed on a Streamlit rerun after the short loop | Python blocks in one request while sleeping and running all pulses | implement incremental reruns/state-machine ticks | source inspection |
| O-03 | Open | Central threshold drift | configuration declares tank-nearly-full at 80%, but allocation splits at hard-coded 75%; high-drain threshold is unused | policy literals and unused settings diverged | replace literal with centralized setting and decide how the drain threshold participates | source inspection |
| O-04 | Open | Mixed-retention downstream path may appear inactive | `STORE_AND_RECHARGE` scenarios can contain controlled discharge, but downstream highlighting is false | `downstream_active` checks action enum rather than `downstream_l > 0` | derive active state from allocated downstream litres | scenario output plus source inspection |
| O-05 | Open | Firestore fallback hides diagnostic cause | demo remains usable but operator cannot see why cloud mode failed | broad `except Exception` discards the exception | structured warning/log while retaining memory fallback | source inspection |
| O-06 | Open improvement | Unused direct NumPy dependency | larger dependency surface without application use | declared but never imported | remove after confirming no transitive deployment requirement | import inventory and `requirements.txt` |

## 21.2 Bugs not claimed

**VERIFIED FROM CODE.** No evidence was found that tank levels exceeded capacity, allocations became negative, mass balance failed, unsafe water was recharged, timers accumulated after pause, or Firestore failure produced an empty screen in the current version. Tests specifically guard these conditions. They must not be described as historical bugs merely because the code prevents them.

# 22. Root-Cause Analysis

## 22.1 B-01 — incorrect working directory

**VERIFIED FROM CODE AND SUPPLIED SESSION EVIDENCE.**

**Observed behavior.** The command was entered at `PS C:\Users\User>`:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

PowerShell searched for `C:\Users\User\.venv\Scripts\streamlit.exe`, while the actual environment and `app.py` were under the project directory. Because the Streamlit server never started, `localhost:8501` refused the connection.

**Root cause.** A relative executable path is resolved against the shell’s current directory. This was an invocation problem, not an application-source defect.

## 22.2 B-02 — stale imported function signature

**VERIFIED FROM SUPPLIED SESSION EVIDENCE AND CURRENT CODE.**

**Observed behavior.** A running process raised a `TypeError` when a page passed `tank_before_percent` to `physical_process_animation()`.

**Root cause.** The page source and renderer source were edited while an older Python process remained active. The page rerun used a newer call site while the process still held an earlier imported function object.

**Why restart worked.** A new interpreter imported the current signature shown in `src/ui/physical_process.py`, lines 68–82, making caller and callee consistent.

## 22.3 B-03 — typography scale

**VERIFIED FROM CURRENT CODE AND SUPPLIED SESSION EVIDENCE.**

**Observed behavior.** Dense labels and very small engineering-card text were unreadable at normal browser zoom, while some headings consumed excessive space.

**Root cause.** The earlier visual treatment over-optimized for density and did not maintain an appropriate lower bound across a wide desktop canvas. No prior committed CSS is available, so exact original declarations cannot be reproduced.

**Current correction.** `src/ui/theme.py` uses bounded `clamp()` values and explicit readable values for headings, metrics, buttons, captions, and mobile breakpoints. The Physical Process template uses responsive grids rather than simply shrinking all text.

## 22.4 B-04 — scenario telemetry derivation

**VERIFIED FROM CURRENT CODE.** A flow sensor value is meaningful only when it is dimensionally linked to volume and duration. Current code derives litres per minute as `runoff / duration_minutes` and returns zero if the duration is zero. A dedicated regression test asserts this relationship.

No old revision establishes the exact previous statement; the report therefore describes the current rectification without inventing an original line.

## 22.5 O-01 and O-02 — synchronous control model

**VERIFIED FROM CODE.** `speed` is interpolated into progress text but never used in timing. The loop sleeps for a fixed 25 ms eight times, then calls `run_full_storm()` once. Streamlit processes button actions on script reruns, so a Pause button cannot interrupt code that is already executing synchronously in the same rerun.

## 22.6 O-03 — policy configuration drift

**VERIFIED FROM CODE.** `DecisionThresholds.tank_nearly_full_percent` equals 80, while `_allocate_safe()` uses 75 in two comparisons. `high_drain_stress_percent` is also never referenced. This weakens the intended single-source-of-truth configuration boundary.

## 22.7 O-04 — action versus allocation

**VERIFIED FROM CODE.** In the visual mapper, `downstream_active` is true only for selected actions `DIVERT` and `CONTROLLED_DISCHARGE`. However, action `STORE_AND_RECHARGE` may still have a nonzero `controlled_discharge_l`. The heavy and multi-retention scenarios demonstrate this. The UI therefore can under-emphasize a real residual route even though the litre label is correct.

# 23. Bug Rectification and Code Changes

## 23.1 Correct local launch

**VERIFIED FROM CODE AND EXECUTION.**

```powershell
cd "C:\Users\User\Documents\ChatGPT\Chennai Water Bank"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Using `python -m streamlit` also ensures that the Streamlit module comes from the selected interpreter. A clean validation instance started successfully on port 8511.

## 23.2 Process restart after interface change

**VERIFIED FROM CURRENT CODE.** No source change is required when the only mismatch is a stale interpreter. The reliable sequence is stop the known development process, restart it from the project environment, reload the page, and verify health before testing interactions.

## 23.3 Current typography correction

**VERIFIED FROM CODE.** Representative corrected declarations include:

```css
h2 { font-size: clamp(1.45rem, 2.1vw, 1.8rem) !important; }
h3 { font-size: clamp(1.2rem, 1.65vw, 1.45rem) !important; }
.hero h1 { font-size: clamp(2rem, 3.2vw, 3.15rem); }
.kpi-value { font-size: clamp(1.35rem, 1.8vw, 1.8rem); }
[data-testid="stMetricValue"] {
  font-size: clamp(1.18rem, 1.7vw, 1.55rem) !important;
}
```

The fix sets minimum and maximum bounds instead of allowing viewport scaling to make text microscopic or oversized.

## 23.4 Current flow telemetry correction

**VERIFIED FROM CODE.**

```python
incoming_flow_l_per_min=(
    runoff / scenario.duration_minutes if scenario.duration_minutes > 0 else 0.0
),
```

**Why it works.** Dividing litres by minutes yields L/min, matches the field name, and avoids divide-by-zero. The Physical Process page converts it to L/s by dividing by 60.

## 23.5 Verification after rectification

**VERIFIED FROM CODE.** The regression suite, compile check, dependency check, startup health, and route HTTP checks all passed in the current working version. No repository commits are available to associate the fixes with dates or hashes.

# 24. Performance and Code Improvements

## 24.1 Improvements present in the current code

**VERIFIED FROM CODE.**

- `_template()` uses `lru_cache(maxsize=1)` so the 63 KB Physical Process template is not reread on every call.
- the selected repository is cached as a Streamlit resource;
- the four-pulse baseline is cached as data;
- simulator nodes are deep-copied so a run does not corrupt seed state;
- charts disable unnecessary mode bars and use small deterministic datasets;
- allocations use early returns, limiting branch complexity;
- string inputs inserted into HTML are escaped and unresolved tokens fail loudly;
- a reduced-motion rule disables repeated visual movement for users who request it.

## 24.2 Code-quality strengths

**VERIFIED FROM CODE.** Strengths include descriptive names, small hydrology functions, typed dataclasses, enums, explicit result objects, centralized quality thresholds and weights, immutable allocation/decision/scenario records, repository and sensor abstractions, clear simulation disclosures, and tests around core invariants.

## 24.3 Areas for improvement

**VERIFIED FROM CODE.**

1. Replace the hard-coded 75% routing boundary with `DecisionThresholds.tank_nearly_full_percent` or document why the two concepts differ.
2. Use or remove `high_drain_stress_percent`, `default_region`, and `demo_mode` where they are currently not behaviorally active.
3. Derive visual route activation from allocation volumes, not only the selected enum.
4. Connect simulation speed to the state machine and make pause genuinely incremental.
5. Add structured logging for Firestore fallback.
6. Remove unused NumPy if no planned module requires it.
7. Format long lines in the decision and Firestore modules and add a formatter/linter configuration.
8. Add static typing validation and coverage reporting.
9. Persist simulation events when Firestore is enabled, or narrow the persistence contract to what the UI actually uses.
10. Separate visualization text constants from the large HTML template if localization or extensive maintenance is expected.

## 24.4 Genuine software-development challenges

**INFERRED FROM IMPLEMENTATION.** The code reveals four principal challenges:

- translating physical water concepts into dimensionally consistent but explainable rules;
- preserving safety and mass balance across combinations of quality and finite capacity;
- making six node responses understandable without claiming hydraulic realism;
- synchronizing a rich animation with server-derived values without creating a second simulation engine.

The current design addresses them with small calculation modules, deterministic gates, immutable result objects, one normalized sensor contract, and a presentation-only state machine.

# 25. Current Limitations

**VERIFIED FROM CODE.**

1. All node, rainfall, flow, soil, drain, and quality values are synthetic.
2. The six named areas are fictional demonstration nodes, not installed locations.
3. No MQTT, HTTPS telemetry adapter, broker, PLC, edge device, or sensor driver exists.
4. No command is transmitted to a real relay, motor driver, pump, or valve.
5. The runoff model is a simple event-volume calculation.
6. The model omits time of concentration, intensity-duration-frequency analysis, pipe capacity, channel routing, topography, tidal effects, infiltration dynamics, evaporation, treatment losses, and connected catchments.
7. First flush is a Boolean condition, not a calculated volume.
8. Filtration is illustrated but not numerically modelled.
9. Quality uses only contamination, pH, and turbidity; no certified sampling, pathogens, metals, hydrocarbons, salinity, conductivity, TDS, or sensor uncertainty is modelled.
10. Modelled recharge is a capacity screen, not a groundwater model or site approval.
11. Soil saturation follows a scripted profile and is not updated from recharge allocation.
12. Tank storage is updated during a simulation, but recharge inventory and downstream hydraulics are not stateful.
13. Priority scores communicate preference but do not solve a mathematical optimization problem.
14. The default memory backend loses events when the process exits.
15. Firestore event methods exist, but the UI currently reads nodes and does not save storm results.
16. There is no authentication or user authorization.
17. Public Cloud Run deployment is configured for a time-limited demo, not a production control system.
18. No calibrated field validation, pilot result, or measured flood reduction exists.
19. No visual regression, accessibility-conformance, security, load, or hardware-in-loop test exists.
20. Retained litres must not be interpreted as flood prevention or damage avoided.

# 26. Proposed IoT / PLC / Mechanical Integration

## 26.1 Proposed deployment architecture

**PROPOSED FUTURE ARCHITECTURE.**

```text
PHYSICAL WATER SYSTEM
rain gauge | level | flow | quality | soil | pressure | valve position
                              |
                              v
LOCAL PLC / EDGE CONTROLLER
scaling | timestamp | quality flags | plausibility | interlocks | local fallback
                              |
                    MQTT or HTTPS over TLS
                              |
                              v
SECURE INGESTION ADAPTER
device identity | schema validation | buffering | deduplication
                              |
                              v
NORMALIZED SENSOR STATE
existing domain contract, extended for real timestamps and quality metadata
                              |
                              v
CHENNAI WATER BANK DECISION SERVICE
safety rules | capacity model | decision | reason | requested setpoint
                              |
                              v
AUTHORIZED COMMAND SERVICE
command ID | target | expiry | signature | acknowledgement requirement
                              |
                    MQTT or HTTPS over TLS
                              |
                              v
PLC / EDGE CONTROLLER
hardwired interlocks | watchdog | manual mode | command validation
                              |
                              v
MOTOR DRIVER / RELAY / VFD
                              |
                              v
MOTORIZED VALVE / ROUTER / PUMP
                              |
                              v
FLOW + POSITION + LEVEL FEEDBACK
                              |
                              +--------------------> next verified cycle
```

## 26.2 Sensor responsibilities

**PROPOSED FUTURE ARCHITECTURE.**

| Instrument | Measures | Decision use | Required engineering controls |
|---|---|---|---|
| rain gauge | intensity and accumulation | incoming event context | calibration, blockage detection, time sync |
| tank level | stored depth/volume | finite headroom | geometry conversion, high-high independent switch |
| flow meter | actual flow | routing and mass-balance verification | range, direction, zero check |
| quality instruments | approved parameters | destination eligibility | certified sampling plan, cleaning, drift alarms |
| soil moisture/saturation | local wetness proxy | recharge eligibility | site-specific sensor placement and interpretation |
| pressure sensor | pipe/pump state | blockage/leak protection | independent alarm thresholds |
| valve position | actual actuator state | command acknowledgement | independent limit switches or encoder |

## 26.3 Controller and actuator responsibilities

**PROPOSED FUTURE ARCHITECTURE.** The software should issue a requested route or setpoint, not raw motor power. The PLC must own electrical interlocks, end stops, conflicting-route prevention, pump dry-run protection, overcurrent response, manual/automatic mode, safe state, and timeout behavior. A command is complete only after position and flow feedback agree with the requested state.

## 26.4 Changes required in the codebase

**PROPOSED FUTURE ARCHITECTURE.**

1. Implement an MQTT/HTTPS adapter behind the `SensorDataSource` concept.
2. Add a message schema with device ID, node ID, timestamp, engineering unit, quality flag, sequence number, and calibration metadata.
3. Separate decision calculation from Streamlit into a testable service or worker when asynchronous telemetry is introduced.
4. Add an authenticated command/acknowledgement model; never emit controls directly from page code.
5. Persist raw telemetry, normalized readings, decisions, commands, acknowledgements, alarms, and operator overrides.
6. Add PLC emulator tests, hardware-in-loop tests, failure injection, and commissioning procedures.
7. Replace prototype thresholds only after field, treatment, hydrogeological, and regulatory validation.

# 27. Security and Safety Considerations

## 27.1 Current prototype

**VERIFIED FROM CONFIGURATION AND CODE.** Positive controls include Streamlit XSRF protection, no credentials committed, Application Default Credentials for optional Firestore, a non-root container user, an event-collection whitelist, input validation, HTML escaping, and deterministic safety gates.

Current risks include unauthenticated application access, `--allow-unauthenticated` in deployment scripts, no user roles, no audit log, no rate limit, no command authorization layer, broad Firestore-fallback exception handling, and no dependency vulnerability scan. These are acceptable only for a bounded demonstration and must not be carried unchanged into physical control.

## 27.2 Future physical system

**PROPOSED FUTURE ARCHITECTURE.** Minimum controls should include:

- unique device identities and per-device credentials;
- TLS, certificate rotation, and broker/API access control;
- signed, expiring, idempotent commands with replay protection;
- role-based operator approval for hazardous modes;
- local PLC interlocks that cannot be bypassed by the web application;
- safe fallback on communication loss, invalid readings, disagreement, or timeout;
- manual override and emergency isolation;
- watchdogs, heartbeat, command acknowledgement, and discrepancy alarms;
- immutable audit records for readings, decisions, commands, changes, and overrides;
- network segmentation between information technology and operational technology;
- secure update, rollback, backup, recovery, and incident-response procedures;
- independent high-level, overflow, pressure, and motor-protection circuits;
- certified process, electrical, civil, treatment, and functional-safety review.

The software must never treat receipt of a command as proof of physical action; independent feedback is required.

# 28. Future Development Roadmap

## Phase 1 — simulation refinement

**PROPOSED FUTURE ARCHITECTURE.** Centralize all routing thresholds, correct the open visualization and speed-control findings, add structured logging, remove unused dependencies, add lint/type/coverage automation, and document units for every field.

## Phase 2 — calibrated engineering model

Add event duration and first-flush volume methods, catchment-specific loss terms, treatment-state representation, recharge recovery state, uncertainty bounds, and comparison against approved field or laboratory data. Retain explicit limitations.

## Phase 3 — bench sensor prototype

Connect a rain input, level sensor, flow meter, simulated quality input, and valve-position feedback to a bench edge controller. Feed normalized telemetry into the unchanged decision core. Do not connect to groundwater recharge.

## Phase 4 — secure gateway and persistence

Introduce device identity, timestamping, buffering, MQTT/HTTPS ingestion, telemetry storage, command acknowledgement, alarms, dashboards, and replayable audit events.

## Phase 5 — actuator test rig

Use a closed recirculating water rig with a PLC, motorized valve, relay/driver, independent limit switches, manual override, fault injection, and hardware-in-loop tests. Require local interlocks to dominate software requests.

## Phase 6 — engineered pilot node

Proceed only after certified water-quality sampling, treatment design, civil/plumbing/electrical design, geotechnical and hydrogeological investigation, regulatory approval, cybersecurity review, commissioning plan, and operating responsibility are established.

## Phase 7 — distributed pilot evaluation

Measure reliability, calibration drift, false decisions, command latency, storage utilization, verified routed volume, maintenance burden, and downstream hydraulic context. Do not extrapolate retained litres directly to flood damage avoided.

## Phase 8 — wider deployment decision

Scale only if pilot evidence, governance, operations, financing, maintenance, data protection, and municipal integration justify it. Network-wide optimization or machine learning should remain behind deterministic safety gates and expose uncertainty.

# 29. Complete System Data Flow

## 29.1 Current Scenario Lab flow

**VERIFIED FROM CODE.**

```text
User selects or edits ScenarioDefinition
        |
        v
run_scenario() constructs WaterBankNode + SensorState
        |
        v
runoff_volume_l(rainfall_mm, area, coefficient)
        |
        v
DecisionEngine.evaluate(node, state, runoff, duration)
        |
        +--> quality / first-flush safety gate
        +--> storage headroom
        +--> modelled recharge availability
        +--> priority scores
        +--> capacity-constrained allocation
        |
        v
DecisionResult
        |
        +--> decision card and reasons
        +--> route diagram and priority chart
        +--> equation panel and mass balance
        +--> Physical Process template values
```

## 29.2 Current network flow

**VERIFIED FROM CODE.**

```text
Seeded demo_nodes.json -> MemoryRepository -> six WaterBankNode objects
        |
        v
DigitalSensorSimulator, eight fixed rainfall pulses
        |
        v
for each pulse and each deep-copied node:
  read synthetic SensorState
  convert intensity to 15-minute depth
  calculate runoff
  evaluate deterministic route
  update tank storage only
  append SimulationStep
        |
        v
48 SimulationStep records -> Streamlit session_state
        |
        +--> latest state per node
        +--> map, KPIs, table, route chart
        +--> impact snapshots and aggregation
        +--> Node Intelligence detail
```

## 29.3 Proposed real closed loop

**PROPOSED FUTURE ARCHITECTURE.**

```text
Rain and physical water condition
        v
Certified sensor
        v
PLC / edge controller validation
        v
Authenticated normalized telemetry
        v
Chennai Water Bank safety and decision service
        v
Authorized, expiring requested route
        v
PLC interlocks and motor driver
        v
Valve / pump / router physically changes water path
        v
Independent flow, level and position feedback
        v
Acknowledged result, alarm or corrective safe action
```

# 30. Software Inventory

**VERIFIED FROM CONFIGURATION.** “Installed” versions below are from the audited `.venv`; “configured” versions come from repository files.

| Technology / program | Configured version | Audited version | Purpose | Where used |
|---|---|---|---|---|
| Python | 3.12 container family | 3.12.13 | all application and test logic | entire project |
| Streamlit | `>=1.39,<2` | 1.61.1 | multipage UI, widgets, state, cache, iframe | `app.py`, `pages/`, `src/ui/` |
| pandas | `>=2.2,<3` | 2.3.3 | tabular transformation and display | pages 02, 04, 05, 06; command center |
| NumPy | `>=2.0,<3` | 2.5.2 | declared; no direct code use | requirements only |
| Plotly | `>=5.24,<7` | 6.9.0 | maps and charts | pages 03–05, components, command center |
| google-cloud-firestore | `>=2.19,<3` | 2.28.1 | optional cloud persistence | `firestore_repository.py` |
| pytest | `>=8.3,<10` | 9.1.1 | automated tests | `tests/` |
| HTML5 | not versioned | browser standard | physical-process structure | template |
| CSS | not versioned | browser standard | theme, responsive layout, animation | theme and template |
| JavaScript | not versioned | browser standard | deterministic presentation state machine | template |
| JSON | not versioned | standard format | demo-node seed and template payload | `data/`, physical renderer |
| Docker | `python:3.12-slim` base | executable unavailable | container packaging | `Dockerfile` |
| Google Cloud Run | no pinned CLI/API version | `gcloud` unavailable | proposed hosting target | deploy scripts / README |
| Git | no minimum version | 2.55.0.windows.3 | worktree present; no commits | `.git` |
| PowerShell | not pinned | environment provided | Windows deployment/startup commands | `.ps1`, local audit |
| Bash | not pinned | not audited | Linux/macOS deployment script | `.sh` |

# 31. Important File Inventory

**VERIFIED FROM CODE.**

| File / component | Purpose | Main dependencies |
|---|---|---|
| `app.py` | default Command Center entry | theme, command center |
| `pages/01_command_center.py` | multipage wrapper | command center, theme |
| `pages/02_node_intelligence.py` | per-node decision and animation | runtime, components, physical renderer |
| `pages/03_scenario_lab.py` | predefined/manual stress tests | scenarios, scenario controls, Plotly |
| `pages/04_network_simulation.py` | multi-pulse distributed response | runtime, pandas, Plotly |
| `pages/05_impact_analytics.py` | aggregate volume analytics | impact/runtime, pandas, Plotly |
| `pages/06_decision_explainer.py` | equations and safety hierarchy | settings, explainer constants |
| `pages/07_solution_architecture.py` | present/future architecture explanation | Streamlit |
| `pages/08_about_solution.py` | scope, non-claims, demo script | shared UI |
| `pages/09_physical_process.py` | scenario-bound closed-loop explainer | scenarios, renderer, decision card |
| `src/config/settings.py` | central thresholds, weights, environment | dataclasses, `os`, cache |
| `src/models/node.py` | catchment and mutable tank state | dataclasses |
| `src/models/sensor_state.py` | normalized simulated/future sensor contract | enum, datetime |
| `src/models/decision.py` | actions, allocations, explanations | enum, dataclasses |
| `src/models/scenario.py` | scenario and simulation-step records | decision and sensor models |
| `src/hydrology/runoff.py` | runoff-volume equation | none beyond Python |
| `src/hydrology/storage.py` | headroom and storage cap | none beyond Python |
| `src/hydrology/recharge.py` | interval recharge capacity screen | none beyond Python |
| `src/decision/rules.py` | quality and first-flush classification | settings, sensor model |
| `src/decision/engine.py` | deterministic allocation and explanations | hydrology, models, settings, rules |
| `src/decision/explainer.py` | display formulas | constants only |
| `src/simulation/rainfall.py` | fixed eight-pulse profile and depth conversion | none beyond Python |
| `src/simulation/scenarios.py` | six predefined cases | scenario model |
| `src/simulation/simulator.py` | sensor abstraction and network loop | decision, runoff, rainfall, models |
| `src/impact/calculator.py` | retained/downstream aggregation | decision model |
| `src/persistence/repository.py` | backend contract and fallback factory | settings, node model |
| `src/persistence/memory_repository.py` | seeded in-process backend | JSON, deepcopy, UUID |
| `src/persistence/firestore_repository.py` | optional cloud adapter | Firestore client, settings |
| `src/ui/runtime.py` | repository/cache/session integration | Streamlit, simulator, impact |
| `src/ui/components.py` | shared cards, map, route and charts | Streamlit, Plotly, models |
| `src/ui/scenario_controls.py` | scenario-to-domain adapter and equations | decision, runoff, Streamlit |
| `src/ui/physical_process.py` | safe token binding and command mapping | Streamlit, HTML/JSON utilities |
| `src/ui/templates/physical_process.html` | complete animated engineering diagram | browser HTML/CSS/JavaScript |
| `src/ui/theme.py` | dark theme and readable scale | Streamlit |
| `data/demo_nodes.json` | six fictional node configurations | memory repository |
| `tests/*.py` | 28 regression and invariant tests | pytest and application modules |
| `Dockerfile` | non-root Streamlit container | Python 3.12 slim, requirements |
| `scripts/seed_demo_data.py` | copy seed nodes into selected backend | repositories |
| deployment scripts | source-based Cloud Run deployment | `gcloud` |

# 32. Code Appendix

## A. Simulation

**VERIFIED FROM CODE — `src/simulation/simulator.py`, `simulate_network()`.**

```python
for step_index in range(step_count):
    for node in working_nodes:
        state = self.read(node, step_index)
        rainfall_depth = rainfall_depth_for_interval(
            state.rainfall_intensity_mm_hr,
            self.settings.simulation_interval_minutes,
        )
        runoff = runoff_volume_l(
            rainfall_depth, node.catchment_area_m2, node.runoff_coefficient
        )
        decision = self.engine.evaluate(
            node, state, runoff,
            interval_minutes=self.settings.simulation_interval_minutes,
        )
```

**Purpose.** Convert one synthetic reading at each node and pulse into a routed decision.

## B. Calculations

**VERIFIED FROM CODE — `src/simulation/rainfall.py`.**

```python
def rainfall_depth_for_interval(intensity_mm_hr, interval_minutes):
    if intensity_mm_hr < 0 or interval_minutes < 0:
        raise ValueError("rainfall intensity and interval cannot be negative")
    return intensity_mm_hr * interval_minutes / 60.0
```

**Purpose.** Maintain consistent hourly-intensity-to-interval-depth units.

## C. Routing

**VERIFIED FROM CODE — `src/decision/engine.py`.**

```python
if quality == WaterQualityStatus.UNSAFE_DIVERT:
    allocation = Allocation(incoming_l=incoming_l, diverted_l=incoming_l)
    return DecisionResult(
        selected_action=DecisionAction.DIVERT,
        priority=1.0,
        reason_codes=safety_reasons + ("SAFETY_GATE_OVERRIDE",),
        human_explanation=(
            "Recharge and beneficial storage were blocked by the prototype "
            "water-quality safety gate. Incoming water is routed away from "
            "recharge for appropriate drainage or treatment."
        ),
        rejected_alternatives={
            "STORE": "Unsafe water is not accepted into the reusable-water tank.",
            "RECHARGE": "The quality safety gate is non-negotiable.",
        },
        constraints=tuple(base_constraints + ["Unsafe water must never be recharged."]),
        scores=scores,
        allocation=allocation,
    )
```

**Purpose.** Terminate decision processing with a non-negotiable safe outcome before capacity preferences can act.

## D. State Management

**VERIFIED FROM CODE — `src/ui/runtime.py`.**

```python
def reset_storm() -> None:
    st.session_state.pop("storm_steps", None)
    st.session_state["storm_complete"] = False
    st.session_state["storm_running"] = False
```

**Purpose.** Remove the full run and return dependent views to cached baseline steps.

## E. UI Components

**VERIFIED FROM CODE — `src/ui/theme.py`.**

```python
def configure_page(title: str, icon: str = "💧") -> None:
    st.set_page_config(
        page_title=f"{title} · Chennai Water Bank",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)
```

**Purpose.** Apply one wide, branded, disclosed presentation surface to every page.

## F. Animation

**VERIFIED FROM CODE — `src/ui/templates/physical_process.html`.**

```javascript
const clearTimers = () => {
  clearTimeout(sceneTimer);
  clearInterval(levelTimer);
  actuatorTimers.forEach(clearTimeout);
  actuatorTimers = [];
};
```

**Purpose.** Prevent old scene, tank, or actuator callbacks from continuing after pause, restart, next, or view change.

## G. Data Visualization

**VERIFIED FROM CODE — `src/ui/components.py`, `before_after_chart()`.** The chart compares total received runoff with immediate downstream volume after modelled retention. It does not chart flood depth or damage.

## H. Error Handling

**VERIFIED FROM CODE — `src/persistence/repository.py`.**

```python
if active.data_backend == "firestore":
    try:
        repository = FirestoreRepository(active)
        repository.health_check()
        return repository
    except Exception:
        pass
return MemoryRepository.from_demo_data()
```

**Purpose.** Preserve a populated demonstration if credentials or Firestore are unavailable. The resilience is useful, but future production code should log the failure without exposing secrets.

# 33. Bug/Fix Appendix

**VERIFIED FROM CODE, CONFIGURATION, AND SUPPLIED SESSION EVIDENCE.** Dates and commit hashes are unavailable because the repository has no commits.

| Bug ID | Module | Date / commit | Observed behavior | Root cause | Fix / status | Affected files | Verification |
|---|---|---|---|---|---|---|---|
| B-01 | local startup | unavailable | Streamlit executable not found; localhost refused | shell in wrong directory | corrected launch path | none | clean startup and health |
| B-02 | Physical Process runtime | unavailable | unexpected keyword argument | stale imported signature in old process | process restart | no source-only fix | compile, startup, tests |
| B-03 | shared UI / explainer | unavailable | unreadable small text and oversized headings | unbalanced fixed scale | bounded responsive scale in current source | `theme.py`, template | code review; session visual evidence |
| B-04 | Scenario Lab telemetry | unavailable | flow not tied to event volume/duration | missing derived flow relationship | runoff divided by positive duration | `scenario_controls.py`, physical-process test | dedicated test passes |
| O-01 | Command Center | unavailable | speed labels do not alter timing | fixed 0.025 s wait | open | `command_center.py` | source inspection |
| O-02 | Command Center | unavailable | pause does not interrupt active synchronous loop | one blocking Streamlit rerun | open | `command_center.py` | source inspection |
| O-03 | Decision Engine | unavailable | config says 80%; engine uses 75%; drain threshold unused | policy drift | open | `settings.py`, `engine.py` | source inspection |
| O-04 | Physical Process | unavailable | split route with residual discharge may not highlight downstream | visual active flag based on action instead of litres | open | `physical_process.py` | scenario output and source inspection |
| O-05 | Persistence | unavailable | cloud failure reason invisible | broad exception suppression | open improvement | `repository.py` | source inspection |
| O-06 | Dependencies | unavailable | unused direct package | NumPy declared without import | open improvement | `requirements.txt` | import inventory |

# 34. Conclusion

**VERIFIED FROM CODE.** Chennai Water Bank is a coherent, working Python/Streamlit sustainability prototype. It contains nine integrated views, six fictional demonstration nodes, a deterministic sensor simulator, explicit hydrology calculations, safety-first route logic, mass-balanced allocations, explainable decisions, network and impact analytics, resilient memory persistence, optional Firestore support, a responsive dark engineering interface, and an eight-scene closed-loop physical/digital explainer.

Its strongest technical properties are separation of concerns, deterministic repeatability, safety gates before optimization, finite-capacity allocation, transparent reason codes and formulas, shared simulation state, a replaceable sensor-source boundary, graceful persistence fallback, and a Physical Process visualization that does not duplicate the decision engine.

**VERIFIED FROM CODE.** The current system remains a simulation. It has no real instruments, field calibration, PLC, motor driver, valve, hydraulic network, certified recharge design, operator security model, or measured Chennai outcome. Its figures are prototype estimates, and its demonstration locations are not installed infrastructure.

**VERIFIED FROM CONFIGURATION.** The current working version passed 28 automated tests, Python compilation, dependency consistency, clean startup, health checks, and route-level HTTP checks. Git history is absent, so the true dated development chronology and original code for earlier bugs cannot be reconstructed. The report has preserved that uncertainty.

**PROPOSED FUTURE ARCHITECTURE.** The next defensible step is not city-scale deployment. It is to correct the open code findings, add engineering-state fidelity and automated quality controls, then build a secured bench-scale sensor/PLC/actuator loop in which the PLC owns interlocks and independent feedback verifies every physical action. Only validated field, treatment, geotechnical, hydrogeological, regulatory, cybersecurity, commissioning, and operating evidence can justify a pilot recharge installation.

The complete principle is:

```text
CURRENT SOFTWARE
simulated water state -> normalized data -> deterministic decision
-> capacity-constrained allocation -> explanation and visualization

FUTURE PHYSICAL LOOP
water -> sensor -> edge/PLC -> authenticated telemetry -> software decision
-> authorized request -> PLC interlocks -> actuator -> water movement
-> independent feedback -> verification or safe alarm
```

Chennai Water Bank should therefore be understood as an explainable digital decision and demonstration layer for a proposed distributed water-management concept—not as the physical water system itself and not as a validated digital twin of Chennai.

