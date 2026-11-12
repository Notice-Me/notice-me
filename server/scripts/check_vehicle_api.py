"""Read-only HTTP checks of the vehicle contract; no server DB or provider API keys needed."""

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import httpx


class CheckFailed(Exception):
    pass


def require(condition, code):
    if not condition:
        raise CheckFailed(code)


def timestamp(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(stamp.tzinfo is not None, "NAIVE_CONTENT_TIME")
    return stamp


def check_playback(feed, now):
    """Check the actual playback path, including alerts and rights evidence."""
    queue, alerts = feed["queue"], feed["alerts"]
    for item in queue:
        require(item["tts_eligible"], "QUEUE_RIGHTS_VIOLATION")
    for item in queue + alerts:
        if not item["tts_eligible"]:
            continue
        require(
            item["rights_status"] == "TTS_ALLOWED"
            and item["rights_evidence_url"]
            and item["verification_status"] in ("VERIFIED", "SIMULATED"),
            "PLAYBACK_RIGHTS_VIOLATION",
        )
        require(timestamp(item["expires_at"]) > now, "PLAYBACK_CONTAINS_EXPIRED_CONTENT")
        if item["data_mode"] == "LIVE":
            weather = item.get("weather") or {}
            require(
                item["content_type"] == "LIFE"
                and weather.get("area_code") == "POI009"
                and weather.get("scope") == "FIXED_OBSERVATION_AREA"
                and weather.get("region")
                and item["provenance"].startswith("PUBLIC_API:seoul_citydata;"),
                "LIVE_PLAYBACK_NOT_WEATHER",
            )
            require(
                now - timedelta(hours=1) < timestamp(weather["observed_at"]) <= now,
                "PLAYBACK_WEATHER_STALE_OR_FUTURE",
            )
        if item["content_type"] == "TRAFFIC":
            traffic = item["traffic"]
            require(
                timestamp(item["fetched_at"]) <= now <= timestamp(item["fetched_at"]) + timedelta(minutes=10)
                and timestamp(traffic["occurred_at"]) <= now < timestamp(traffic["valid_until"])
                and traffic["status"] == "ACTIVE"
                and traffic["match_status"] == "LINK_MATCH",
                "PLAYBACK_TRAFFIC_STALE_OR_UNMATCHED",
            )
    expected = [x["id"] for x in alerts + queue if x["tts_eligible"]]
    require(len(expected) == len(set(expected)), "DUPLICATE_PLAYBACK_ID")
    require(feed["playback_order"] == expected, "PLAYBACK_ORDER_MISMATCH")
    for item in feed["top3"] + queue + alerts:
        if item["rights_status"] != "TTS_ALLOWED":
            require(not item["tts_eligible"] and item["id"] not in expected, "UNCLEARED_CONTENT_PLAYABLE")


def check_api(client, expect_mode=None, demo_route=False):
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "status": "FAILED",
        "checks": [],
        "route_context": "MANUAL_DEMO_LINK" if demo_route else "NO_NAVIGATION",
        "verification_scope": "SERVER_HTTP_ONLY",
        "pleos_sdk_verified": False,
        "vehicle_tts_verified": False,
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
        check_playback(feed, now)
        for group in ("top3", "queue", "alerts"):
            for item in feed[group]:
                require(
                    item["verification_status"] != "SIMULATED" or item["data_mode"] == "MOCK",
                    "SIMULATED_MISLABELED_LIVE",
                )
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
        blocked_news = {
            item["id"]
            for item in feed["top3"]
            if item["content_type"] == "NEWS" and item["rights_status"] != "TTS_ALLOWED"
        }
        if health.json()["configured_data_mode"] in ("MOCK", "MIXED"):
            blocked_news.add("mock:news-anime")
        for content_id in sorted(blocked_news):
            path = "/api/v1/contents/" + quote(content_id, safe="")
            blocked_detail = client.get(path)
            require(
                blocked_detail.status_code == 200 and not blocked_detail.json()["tts_eligible"],
                "UNCLEARED_NEWS_DETAIL_PLAYABLE",
            )
            require(
                client.post(path + "/explain").status_code == 403,
                "UNCLEARED_NEWS_NOT_BLOCKED",
            )
        report["blocked_news_checked"] = len(blocked_news)
        if blocked_news:
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
