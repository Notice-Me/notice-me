"""Read-only HTTP checks of the vehicle contract; no server DB or provider API keys needed."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import httpx


class CheckFailed(Exception):
    pass


def require(condition, code):
    if not condition:
        raise CheckFailed(code)


def check_api(client, expect_mode=None, demo_route=False):
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "FAILED",
        "checks": [],
        "route_context": "MANUAL_DEMO_LINK" if demo_route else "NO_NAVIGATION",
    }
    try:
        health = client.get("/api/v1/health")
        require(health.status_code == 200 and health.json()["database"] == "ok", "HEALTH_FAILED")
        report["checks"].append("health:200")
        params = {"lat": 37.57, "lon": 126.98, "interests": "art,science,anime,weather"}
        if demo_route:
            params.update(navigation_active="true", route_link_ids="demo-link-1", route_link_namespace="DEMO")
        response = client.get("/api/v1/feed", params=params)
        require(response.status_code == 200, "FEED_FAILED")
        feed = response.json()
        report.update(
            data_mode=feed["data_mode"],
            top3_count=len(feed["top3"]),
            queue_count=len(feed["queue"]),
            alert_count=len(feed["alerts"]),
            diagnostics=feed["diagnostics"],
        )
        require(feed["data_mode"] in ("MOCK", "LIVE", "MIXED"), "INVALID_DATA_MODE")
        if expect_mode:
            require(feed["data_mode"] == expect_mode, "DATA_MODE_MISMATCH")
        require(0 < len(feed["top3"]) <= 3 and feed["queue"], "NO_ELIGIBLE_TTS_CONTENT")
        now = datetime.now(UTC)
        for item in feed["queue"]:
            require(item["rights_status"] == "TTS_ALLOWED" and item["tts_eligible"], "QUEUE_RIGHTS_VIOLATION")
            expiry = datetime.fromisoformat(item["expires_at"].replace("Z", "+00:00"))
            require(expiry.tzinfo is not None and expiry > now, "QUEUE_CONTAINS_EXPIRED_CONTENT")
        for group in ("top3", "queue", "alerts"):
            for item in feed[group]:
                require(
                    item["verification_status"] != "SIMULATED" or item["data_mode"] == "MOCK",
                    "SIMULATED_MISLABELED_LIVE",
                )
        spoken = {x["id"] for x in feed["queue"] + feed["alerts"] if x["tts_eligible"]}
        require(set(feed["playback_order"]) <= spoken, "UNKNOWN_PLAYBACK_ID")
        report["checks"].append("feed:200;mode/rights/expiry/playback_checked")
        identifier = quote(feed["queue"][0]["id"], safe="")
        detail = client.get("/api/v1/contents/" + identifier)
        require(detail.status_code == 200 and detail.json()["tts_eligible"], "DETAIL_FAILED_OR_STALE")
        report["checks"].append("detail:200")
        explanation = client.post("/api/v1/contents/" + identifier + "/explain", json={"question": "자세히"})
        require(explanation.status_code == 200, "EXPLAIN_FAILED")
        report["ai_mode"] = explanation.json()["ai_mode"]
        report["checks"].append("explain:200;ai_mode_recorded")
        require(client.get("/api/v1/contents/contract-check-unknown-id").status_code == 404, "MISSING_404")
        require(client.get("/api/v1/feed", params={"lat": 91, "lon": 127}).status_code == 422, "MISSING_422")
        report["checks"].append("errors:404/422")
        if health.json()["configured_data_mode"] in ("MOCK", "MIXED"):
            require(
                client.post("/api/v1/contents/mock:news-anime/explain").status_code == 403,
                "UNCLEARED_NEWS_NOT_BLOCKED",
            )
            report["checks"].append("uncleared_news:403")
        spec_response = client.get("/openapi.json")
        require(spec_response.status_code == 200, "OPENAPI_FAILED")
        spec = spec_response.json()
        for path, method in [
            ("/api/v1/health", "get"),
            ("/api/v1/feed", "get"),
            ("/api/v1/contents/{content_id}", "get"),
            ("/api/v1/contents/{content_id}/explain", "post"),
        ]:
            schema = spec["paths"][path][method]["responses"]["200"]["content"]["application/json"]["schema"]
            require("$ref" in schema, "UNTYPED_RESPONSE:" + path)
        report["checks"].append("openapi:four_typed_responses")
        report["status"] = "SUCCESS"
    except CheckFailed as error:
        report["code"] = str(error)
    except httpx.HTTPError:
        report["code"] = "HTTP_NETWORK_OR_TIMEOUT"
    except (ValueError, KeyError, TypeError):
        report["code"] = "INVALID_RESPONSE_SHAPE"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--expect-mode", choices=["MOCK", "LIVE", "MIXED"])
    parser.add_argument("--demo-route", action="store_true", help="Use an explicitly synthetic route link")
    parser.add_argument("--report", type=Path, default=Path("reports/vehicle-api-check.json"))
    args = parser.parse_args()
    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=10, follow_redirects=False) as client:
        report = check_api(client, args.expect_mode, args.demo_route)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "SUCCESS" else 1)


if __name__ == "__main__":
    main()
