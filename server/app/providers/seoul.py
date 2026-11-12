from datetime import datetime, timedelta
from urllib.parse import quote

from ..models import (
    Content,
    ContentType,
    DataMode,
    RightsStatus,
    TrafficImpact,
    Verification,
    WeatherObservation,
)
from .base import ProviderError, SafeHTTP, check_seoul_xml, parse_datetime, stable_id

CITY_DOC = "https://data.seoul.go.kr/dataList/OA-21285/F/1/datasetView.do"
INCIDENT_DOC = "https://data.seoul.go.kr/dataList/OA-13315/A/1/datasetView.do"


class SeoulCity:
    name = "seoul_city"

    def __init__(self, key="sample", timeout=10, transport=None):
        self.key = key
        self.http = SafeHTTP(self.name, timeout, transport)

    async def collect(self, now: datetime) -> tuple[list[Content], dict]:
        if not self.key:
            raise ProviderError(self.name, "MISSING_KEY")
        # Official sample supports POI009 (Gwanghwamun/Deoksugung) only.
        root = await self.http.xml(
            f"http://openapi.seoul.go.kr:8088/{quote(self.key, safe='')}/xml/citydata/1/5/POI009"
        )
        check_seoul_xml(root, self.name)
        area = root.findtext(".//CITYDATA/AREA_NM")
        weather = next((x for x in root.findall(".//WEATHER_STTS") if x.findtext("WEATHER_TIME")), None)
        items = []
        if area and weather is not None:
            stamp = parse_datetime(weather.findtext("WEATHER_TIME"), local=True)
            temp = weather.findtext("TEMP")
            if stamp and temp:
                # No coordinates invented from area name; field is explicitly nullable.
                items.append(
                    Content(
                        id="seoul-city:POI009:weather",
                        content_type=ContentType.LIFE,
                        title=f"{area} 날씨",
                        brief=f"서울시 실시간 도시데이터 기준 {area} 기온은 {temp}도입니다. "
                        f"관측 기준시각 {weather.findtext('WEATHER_TIME')}. 출처: 서울특별시.",
                        source_name="서울특별시 실시간 도시데이터",
                        source_url=CITY_DOC,
                        published_at=None,
                        updated_at=stamp,
                        fetched_at=now,
                        expires_at=stamp + timedelta(hours=1),
                        interest_tags=["생활", "날씨"],
                        rights_status=RightsStatus.TTS_ALLOWED,
                        rights_evidence_url=CITY_DOC,
                        verification_status=Verification.VERIFIED,
                        data_mode=DataMode.LIVE,
                        provenance="PUBLIC_API:seoul_citydata;KOGL_TYPE1;weather_fields_only",
                        venue=area,
                        weather=WeatherObservation(area_code="POI009", region=area, observed_at=stamp),
                    )
                )
        # Incident data from this source lacks link IDs. Preserve the capability gap;
        # do not upgrade geographic proximity into a confirmed route impact.
        incident_count = len([x for x in root.findall(".//ACDNT_CNTRL_STTS") if x.findtext("ACDNT_OCCR_DT")])
        return items, {
            "raw_count": 1,
            "weather_available": bool(items),
            "city_incident_count": incident_count,
            "sample_area": "POI009",
            "city_incident_adapter": "DEFERRED_ROUTE_LINKS_MISSING",
        }


class SeoulIncidents:
    name = "seoul_incidents"

    def __init__(self, key="sample", timeout=10, transport=None):
        self.key = key
        self.http = SafeHTTP(self.name, timeout, transport)

    async def collect(self, now: datetime) -> tuple[list[Content], dict]:
        if not self.key:
            raise ProviderError(self.name, "MISSING_KEY")
        limit = 5 if self.key == "sample" else 100
        root = await self.http.xml(
            f"http://openapi.seoul.go.kr:8088/{quote(self.key, safe='')}/xml/AccInfo/1/{limit}/"
        )
        code = root.findtext(".//RESULT.CODE") or root.findtext(".//CODE")
        if code == "INFO-200":
            return [], {"raw_count": 0, "reported_total": 0}
        check_seoul_xml(root, self.name)
        rows = root.findall(".//row")
        items = []
        for row in rows:

            def text(name):
                return (row.findtext(name.lower()) or row.findtext(name) or "").strip()

            def clock(name):
                value = text(name)
                return value + "00" if len(value) == 4 else value.zfill(6)

            start = parse_datetime(text("OCCR_DATE") + clock("OCCR_TIME"), local=True)
            end = parse_datetime(text("EXP_CLR_DATE") + clock("EXP_CLR_TIME"), local=True)
            link, message = text("LINK_ID"), text("ACC_INFO")
            if not start or not end or not link or not message:
                continue

            def number(name):
                try:
                    return float(text(name))
                except ValueError:
                    return None

            # GRS80TM X/Y are not latitude/longitude. EPSG conversion awaits exact official CRS definition.
            items.append(
                Content(
                    id=stable_id("seoul-incident", text("ACC_ID")),
                    content_type=ContentType.TRAFFIC,
                    title=message[:1000],
                    brief=f"서울시 교통 돌발정보: {message[:3500]}. 출처: 서울특별시 TOPIS.",
                    source_name="서울특별시 TOPIS",
                    source_url=INCIDENT_DOC,
                    published_at=start,
                    updated_at=None,
                    fetched_at=now,
                    expires_at=end,
                    rights_status=RightsStatus.TTS_ALLOWED,
                    rights_evidence_url=INCIDENT_DOC,
                    verification_status=Verification.VERIFIED,
                    priority=100,
                    data_mode=DataMode.LIVE,
                    provenance="PUBLIC_API:AccInfo;KOGL_TYPE1;status_derived_from_current_listing_and_end_time",
                    traffic=TrafficImpact(
                        occurred_at=start,
                        valid_until=end,
                        status="ACTIVE",
                        affected_link_ids=[link],
                        link_namespace="SEOUL_TOPIS",
                        extent_description=f"TOPIS 링크 {link}",
                        native_x=number("GRS80TM_X"),
                        native_y=number("GRS80TM_Y"),
                        native_crs="GRS80TM_EPSG_UNVERIFIED",
                    ),
                )
            )
        return items, {
            "raw_count": len(rows),
            "reported_total": root.findtext("list_total_count"),
            "coordinates": "NATIVE_GRS80TM_ONLY; EPSG_UNVERIFIED",
            "status": "DERIVED_FROM_LISTING_AND_EXPIRY; requery within 10 minutes",
        }
