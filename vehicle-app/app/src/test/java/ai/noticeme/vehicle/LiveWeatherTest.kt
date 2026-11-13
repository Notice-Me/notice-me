package ai.noticeme.vehicle

import org.junit.Assert.*
import org.junit.Test
import java.time.Instant

class LiveWeatherTest {
    private val now = Instant.parse("2026-11-13T00:00:00Z")
    private fun weather() = item().copy(
        dataMode = "LIVE", verification = "VERIFIED", contentType = "LIFE",
        fetchedAt = now, expiresAt = now.plusSeconds(3600),
        weather = Weather("POI009", "광화문·덕수궁", now, "FIXED_OBSERVATION_AREA"),
        provenance = "PUBLIC_API:seoul_citydata;KOGL_TYPE1;weather_fields_only",
    )
    @Test fun `only attributed fresh live weather can speak while mock still works`() {
        val w = weather()
        assertTrue(w.canSpeak(now))
        assertTrue(item().canSpeak(Instant.parse("2026-11-11T12:00:00Z")))
        for (blocked in listOf(w.copy(contentType = "NEWS"), w.copy(contentType = "EVENT"),
            w.copy(weather = null), w.copy(provenance = "UNKNOWN"), w.copy(rightsEvidence = null))) {
            assertFalse(blocked.canSpeak(now))
        }
    }
    @Test fun `old future or untrusted weather never reaches speech`() {
        val w = weather()
        for (blocked in listOf(w.copy(expiresAt = now), w.copy(fetchedAt = now.plusSeconds(1)),
            w.copy(verification = "UNVERIFIED"), w.copy(rightsStatus = "LICENSE_UNVERIFIED"),
            w.copy(weather = w.weather!!.copy(observedAt = now.minusSeconds(3600))),
            w.copy(weather = w.weather!!.copy(observedAt = now.plusSeconds(1))))) {
            assertFalse(blocked.canSpeak(now))
        }
    }
    @Test fun `weather observation parses without treating the request position as its region`() {
        val parsed = FeedJson.detail("""{
          "id":"weather","title":"날씨","brief":"합성 테스트","source_name":"서울특별시",
          "source_url":"https://data.seoul.go.kr","content_type":"LIFE","data_mode":"LIVE",
          "verification_status":"VERIFIED","tts_eligible":true,"rights_status":"TTS_ALLOWED",
          "rights_evidence_url":"https://data.seoul.go.kr","provenance":"PUBLIC_API:seoul_citydata;test",
          "fetched_at":"2026-11-13T00:00:00Z","expires_at":"2026-11-13T01:00:00Z",
          "weather":{"area_code":"POI009","region":"광화문·덕수궁","observed_at":"2026-11-13T09:00:00+09:00","scope":"FIXED_OBSERVATION_AREA"}
        }""")
        assertEquals(now, parsed.weather!!.observedAt)
        assertEquals("광화문·덕수궁", parsed.weather!!.region)
        assertTrue(parsed.canSpeak(now))
    }
    @Test fun `navigation reuses only recent callbacks and rejects invalid points`() {
        val manual = FeedQuery(37.57, 126.98, listOf("weather"))
        val nav = NavigationContext(MapPoint(35.0, 129.0), "테스트 지역", MapPoint(35.1, 129.1), "테스트 목적지", 120, now)
        assertEquals(2.0, nav.applyTo(manual, now).etaMinutes!!, 0.0)
        assertEquals(35.0, nav.applyTo(manual, now).latitude, 0.0)
        assertEquals(manual, nav.copy(receivedAt = now.minusSeconds(30)).applyTo(manual, now))
        assertEquals(manual, nav.copy(receivedAt = now.plusSeconds(1)).applyTo(manual, now))
        assertThrows(IllegalArgumentException::class.java) { MapPoint(Double.NaN, 129.0) }
    }
    @Test fun `destination cancellation removes old destination and ETA`() {
        val previous = FeedQuery(37.57, 126.98, listOf("weather"), MapPoint(35.0, 129.0), 20.0)
        val cancelled = NavigationContext(MapPoint(37.57, 126.98), null, null, null, 120, now, "INACTIVE")
        val next = cancelled.applyTo(previous, now)
        assertNull(next.destination)
        assertNull(next.etaMinutes)
    }
}
