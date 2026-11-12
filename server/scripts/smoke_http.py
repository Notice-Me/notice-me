"""Run against already-started local Uvicorn instances after explicit API collection."""

import argparse
import json
from pathlib import Path

import httpx

from app.config import Settings
from app.models import utcnow
from app.storage import Store


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live-url", default="http://127.0.0.1:8765")
    p.add_argument("--mixed-url", default="http://127.0.0.1:8766")
    p.add_argument("--report", type=Path, default=Path("../docs/HTTP_SMOKE_RESULTS.json"))
    args = p.parse_args()
    settings = Settings()
    incidents = [c for c in Store(settings.db_path).all("live") if c.traffic and c.expires_at > utcnow()]
    report = {
        "checked_at": utcnow().isoformat(),
        "transport": "real HTTP to running Uvicorn",
        "route_context": "manually supplied test link, not read from a vehicle",
        "checks": [],
    }
    with httpx.Client(timeout=10) as client:
        health = client.get(args.live_url + "/api/v1/health")
        health.raise_for_status()
        assert health.json()["database"] == "ok"
        report["health_http_status"] = health.status_code
        live_params = {"lat": 37.57, "lon": 126.98, "interests": "생활,날씨"}
        if incidents:
            live_params.update(
                navigation_active="true",
                route_link_ids=incidents[0].traffic.affected_link_ids[0],
                route_link_namespace="SEOUL_TOPIS",
            )
        for label, base_url, params in [
            ("live", args.live_url, live_params),
            (
                "mixed",
                args.mixed_url,
                {
                    "lat": 37.57,
                    "lon": 126.98,
                    "interests": "과학IT,예술,애니메이션,생활",
                    "navigation_active": "true",
                    "route_link_ids": "demo-link-1",
                    "route_link_namespace": "DEMO",
                },
            ),
        ]:
            response = client.get(base_url + "/api/v1/feed", params=params)
            response.raise_for_status()
            data = response.json()
            assert data["data_mode"] == label.upper(), data["data_mode"]
            assert 0 < len(data["top3"]) <= 3
            assert data["queue"]
            assert all(c["rights_status"] == "TTS_ALLOWED" for c in data["queue"])
            if label == "mixed":
                assert len(data["queue"]) > 3
                assert data["alerts"][0]["verification_status"] == "SIMULATED"
            if incidents and label == "live":
                assert data["alerts"] and all(x["data_mode"] == "LIVE" for x in data["alerts"])
            queue_id = data["queue"][0]["id"]
            detail = client.get(base_url + "/api/v1/contents/" + queue_id)
            assert detail.status_code == 200
            explain = client.post(
                base_url + "/api/v1/contents/" + queue_id + "/explain", json={"question": "자세히"}
            )
            assert explain.status_code == 200 and explain.json()["ai_mode"] == "MOCK"
            report["checks"].append(
                {
                    "scenario": label,
                    "feed_http_status": response.status_code,
                    "data_mode": data["data_mode"],
                    "top3_count": len(data["top3"]),
                    "queue_count": len(data["queue"]),
                    "alert_count": len(data["alerts"]),
                    "detail_http_status": detail.status_code,
                    "explain_http_status": explain.status_code,
                    "ai_mode": explain.json()["ai_mode"],
                    "item_modes": sorted(
                        {x["data_mode"] for group in ("top3", "queue", "alerts") for x in data[group]}
                    ),
                    "diagnostics": data["diagnostics"],
                }
            )
            example = Path("../docs/examples")
            example.mkdir(parents=True, exist_ok=True)
            (example / (label + "-feed.json")).write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        openapi = client.get(args.live_url + "/openapi.json")
        openapi.raise_for_status()
        Path("../docs/openapi.json").write_text(
            json.dumps(openapi.json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
