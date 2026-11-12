from datetime import timedelta

import httpx
import pytest

from app.models import RightsStatus
from app.providers.base import ProviderError, SafeHTTP
from app.providers.events import SeoulEvents, TourEvents
from app.providers.news import NewsProvider
from app.providers.seoul import SeoulCity, SeoulIncidents


@pytest.mark.parametrize(
    "status,code",
    [(401, "AUTH_REQUIRED"), (403, "ACCESS_DENIED"), (429, "RATE_LIMITED"), (500, "HTTP_ERROR")],
)
async def test_api_error_sanitized(status, code):
    http = SafeHTTP("test", transport=httpx.MockTransport(lambda r: httpx.Response(status)))
    with pytest.raises(ProviderError) as caught:
        await http.json("https://provider.invalid/?apiKey=do-not-leak")
    assert caught.value.code == code
    assert "do-not-leak" not in str(caught.value)


async def test_timeout_and_bad_json_reported_without_keys():
    def timeout(request):
        raise httpx.ReadTimeout("secret-url?apiKey=hidden", request=request)

    http = SafeHTTP("test", transport=httpx.MockTransport(timeout))
    with pytest.raises(ProviderError, match="TIMEOUT") as caught:
        await http.json("https://provider.invalid/")
    assert "hidden" not in str(caught.value)
    http = SafeHTTP("test", transport=httpx.MockTransport(lambda r: httpx.Response(200, text="bad json")))
    with pytest.raises(ProviderError, match="INVALID_JSON"):
        await http.json("https://provider.invalid/")


async def test_seoul_application_error_with_http200_not_success(now):
    provider = SeoulEvents(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"RESULT": {"CODE": "ERROR-500", "MESSAGE": "source failure"}})
        )
    )
    with pytest.raises(ProviderError, match="ERROR-500"):
        await provider.collect(now)


async def test_seoul_event_fields_and_unknown_update_not_fetch_time(now):
    row = {
        "TITLE": "과학 전시",
        "CODENAME": "전시/미술",
        "STRTDATE": "2026-11-11 00:00:00.0",
        "END_DATE": "2026-11-12 00:00:00.0",
        "LAT": "37.5",
        "LOT": "127.0",
        "PLACE": "공식 행사장",
        "HMPG_ADDR": "https://culture.seoul.go.kr/event/123",
        "RGSTDATE": "2026-11-01",
    }
    provider = SeoulEvents(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200,
                json={
                    "culturalEventInfo": {"RESULT": {"CODE": "INFO-000"}, "row": [row], "list_total_count": 1}
                },
            )
        )
    )
    items, meta = await provider.collect(now)
    assert len(items) == 1 and meta["raw_count"] == 1
    item = items[0]
    assert item.latitude == 37.5 and item.longitude == 127
    assert item.updated_at is None and item.fetched_at == now
    assert item.expires_at.hour == 15 and item.expires_at.utcoffset() == timedelta(0)
    assert item.rights_status == RightsStatus.TTS_ALLOWED


async def test_city_weather_source_time_and_expiry(now):
    xml = """<SeoulRtd.citydata><RESULT><RESULT.CODE>INFO-000</RESULT.CODE></RESULT>
    <CITYDATA><AREA_NM>광화문·덕수궁</AREA_NM><WEATHER_STTS><WEATHER_STTS>
    <WEATHER_TIME>2026-11-11 09:00</WEATHER_TIME><TEMP>10.0</TEMP>
    </WEATHER_STTS></WEATHER_STTS></CITYDATA></SeoulRtd.citydata>"""
    provider = SeoulCity(transport=httpx.MockTransport(lambda r: httpx.Response(200, text=xml)))
    items, _ = await provider.collect(now)
    assert items[0].updated_at == now
    assert items[0].expires_at == now + timedelta(hours=1)
    assert items[0].latitude is None


async def test_news_official_parameters_no_unlicensed_body_or_summary(now):
    calls = []

    def respond(request):
        calls.append(request)
        if request.url.path.endswith("/details"):
            return httpx.Response(
                200,
                json={
                    "data": {
                        "uuid": "123",
                        "title": "과학 뉴스",
                        "original_url": "https://paper.example/123",
                        "publisher": "언론사",
                        "published_at": now.isoformat(),
                        "body": "must not persist",
                        "incipit": "not licensed",
                    }
                },
            )
        return httpx.Response(
            200,
            json={
                "data": [{"uuid": "123", "title": "과학 뉴스"}],
                "meta": {"returned": 1, "has_more": False},
            },
        )

    p = NewsProvider("freenews", "fake-key", transport=httpx.MockTransport(respond))
    p.http.min_interval = 0
    result = await p.search("과학", now - timedelta(days=1), now)
    assert calls[0].headers["x-api-key"] == "fake-key"
    assert calls[0].url.params["in_title"] == "과학" and "q" not in calls[0].url.params
    assert "body" not in result["rows"][0]
    item = p.normalize(result["rows"], now, "과학")[0]
    assert item.rights_status == RightsStatus.LICENSE_UNVERIFIED and item.brief == ""
    assert "must not persist" not in item.model_dump_json()


async def test_comparator_parameter_contract_and_gnews_free_delay(now):
    captured = []

    def respond(r):
        captured.append(r)
        return httpx.Response(200, json={"data": [], "articles": [], "totalArticles": 0})

    for name in ("thenewsapi", "gnews"):
        p = NewsProvider(name, "fake", transport=httpx.MockTransport(respond))
        await p.search("예술", now - timedelta(days=1), now, include_details=False)
    assert captured[0].url.params["limit"] == "3"
    assert captured[0].url.params["language"] == "ko"
    assert "lang" not in captured[1].url.params and "country" not in captured[1].url.params
    assert captured[1].url.params["to"] == (now - timedelta(hours=12)).isoformat()


async def test_tour_auth_xml_is_failure_even_http200(now):
    p = TourEvents(
        "",
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200,
                text="<OpenAPI_ServiceResponse><returnReasonCode>30</returnReasonCode></OpenAPI_ServiceResponse>",
            )
        ),
    )
    with pytest.raises(ProviderError, match="AUTH_OR_GATEWAY_ERROR"):
        await p.collect(now, probe=True)


async def test_no_data_incident_is_empty_not_fake_alert(now):
    p = SeoulIncidents(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, text="<RESULT><CODE>INFO-200</CODE></RESULT>")
        )
    )
    items, meta = await p.collect(now)
    assert items == [] and meta["raw_count"] == 0


async def test_missing_key_does_not_attempt_network(now):
    def fail(request):
        pytest.fail("network must not be attempted without key")

    p = NewsProvider("freenews", "", transport=httpx.MockTransport(fail))
    with pytest.raises(ProviderError, match="MISSING_KEY"):
        await p.search("예술", now - timedelta(days=1), now)


async def test_real_shape_lowercase_incident_and_hhmm_time(now):
    xml = """<AccInfo><RESULT><CODE>INFO-000</CODE></RESULT><row><acc_id>one</acc_id>
    <occr_date>20261111</occr_date><occr_time>1000</occr_time>
    <exp_clr_date>20261112</exp_clr_date><exp_clr_time>060000</exp_clr_time>
    <link_id>123</link_id><acc_info>도로 공사</acc_info>
    <grs80tm_x>206076</grs80tm_x><grs80tm_y>446245</grs80tm_y></row></AccInfo>"""
    p = SeoulIncidents(transport=httpx.MockTransport(lambda r: httpx.Response(200, text=xml)))
    items, _ = await p.collect(now)
    assert len(items) == 1 and items[0].published_at.hour == 1  # 10:00 KST == 01:00 UTC
    assert items[0].traffic.link_namespace == "SEOUL_TOPIS"
    assert items[0].traffic.native_x == 206076 and items[0].latitude is None


async def test_gnews_missing_key_http400_is_auth_failure():
    http = SafeHTTP(
        "gnews",
        transport=httpx.MockTransport(
            lambda r: httpx.Response(400, json={"errors": ["No API key was sent. Add your API key."]})
        ),
    )
    with pytest.raises(ProviderError, match="AUTH_REQUIRED"):
        await http.get("https://gnews.io/api/v4/search")
