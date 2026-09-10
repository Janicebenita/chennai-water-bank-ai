# Chennai Water Bank — Agent Guidance

This repository is a judge-facing sustainability prototype. Preserve these invariants in every change.

## Scientific honesty

- Never remove `SIMULATED DATA`, `PROTOTYPE ESTIMATE`, or demonstration-node labels.
- Never fabricate GCC readings, Chennai rainfall observations, groundwater levels, installed locations, water-quality measurements, or measured flood reduction.
- Never claim the product stops flooding or is a validated digital twin of Chennai.
- Say “estimated immediate runoff retained at the modelled catchment,” not “flooding prevented.”
- Keep the certified site-testing warning visible wherever recharge is explained.

## Engineering invariants

- Preserve the `SensorDataSource` boundary so physical MQTT/HTTPS adapters can replace the simulator without changing business logic.
- Keep safety gates deterministic and ahead of routing scores. Unsafe and first-flush water must never be directly recharged.
- Keep runoff, storage, recharge, allocation, impact, and persistence logic modular.
- Keep thresholds and decision weights centralized in `src/config/settings.py`; do not scatter magic numbers.
- Preserve mass balance and nonnegative allocations. Storage and recharge must never exceed configured capacity.
- Maintain safe fallback from unavailable Firestore to seeded memory mode.

## Delivery discipline

- Run `pytest` after code changes and add tests for changed decision or hydrology behavior.
- Verify `python -m compileall app.py pages src` and Streamlit startup for UI changes.
- Maintain Python 3.12 and Cloud Run compatibility on `0.0.0.0:$PORT`.
- Do not add credentials, service-account files, unnecessary dependencies, paid APIs, authentication, LLM calls, ML claims, or infrastructure beyond this hackathon scope.
- Document material behavior or deployment changes in `README.md`.
- Keep the interface presentation-friendly, accessible, and resilient to empty data.

