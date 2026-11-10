# API contract v1

2026-11-11 initial contract. Base URL `/api/v1`. UTF-8 JSON, timezone-aware ISO 8601 timestamps (UTC output). All additions/changes are recorded below. OpenAPI will be exported after implementation.

## Endpoints

- `GET /health`: service/database health and provider configuration status (no credentials).
- `GET /feed?lat=37.57&lon=126.98&interests=예술&navigation_active=false`
  - required: lat [-90,90], lon [-180,180]
  - interests: repeatable query string, also accepts comma-separated values
  - navigation_active: bool, default false
  - destination_lat/destination_lon: optional pair, valid only as a complete pair
  - eta_minutes: optional nonnegative float, applied only with navigation_active
  - route_points / route_link_ids: optional future-compatible inputs, implementation format recorded below
- `GET /contents/{id}`: stored content, 404 if unknown; expired detail remains readable and marked.
- `POST /contents/{id}/explain`: optional JSON `{ "question": "자세히 알려줘" }`; grounded explanation only for rights-cleared, valid, verified content. Mock/LIVE AI mode is explicit. Unknown id 404, rights blocked 403, stale/unverified content 409.

## Feed response

```json
{"top3":[],"queue":[],"alerts":[],"generated_at":"2026-11-11T00:00:00Z","data_mode":"MOCK"}
```

`top3` maximum 3, score descending. `queue` is separately generated, unlimited item count before ETA budget, only TTS_ALLOWED. Alerts precede queue during playback. Display cards must not be independently sent to TTS. `data_mode`: LIVE (only live contributions), MOCK (only fixtures/simulation), MIXED (both); empty feed uses collection provenance and diagnostics, never silently relabels Mock as LIVE.

Common fields: id, content_type (NEWS/EVENT/EXHIBITION/LIFE/TRAFFIC), title, brief, source_name, source_url, published_at, updated_at, expires_at, latitude, longitude, interest_tags, rights_status (TTS_ALLOWED/LINK_ONLY/LICENSE_UNVERIFIED), verification_status (VERIFIED/UNVERIFIED/SIMULATED), priority.

Extensions will carry per-item data_mode, score and score_reasons, provenance, rights evidence, driving-time verification, traffic impact and freshness. Nullable source update timestamps mean unknown, not fetch time. Source fetch time is separate. Unknown event travel time means excluded; diagnostics explain it.

## Change log

- 2026-11-11: initial contract and directory/bootstrap documentation. No functional backend in bootstrap commit.
