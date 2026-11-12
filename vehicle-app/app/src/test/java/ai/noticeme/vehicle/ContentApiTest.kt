package ai.noticeme.vehicle

import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.*
import org.junit.Test
import java.time.Instant

class ContentApiTest {
    private val content = """{
      "id":"가/나 ?","title":"제목","brief":"","source_name":"출처","source_url":"https://example.org",
      "content_type":"NEWS","data_mode":"LIVE","expires_at":"2026-11-12T00:00:00+09:00",
      "fetched_at":"2026-11-11T12:00:00Z","published_at":null,"latitude":null,"longitude":null,
      "unknown_future_field":{"new":true}
    }"""
    @Test fun `nullable and extra fields parse without granting missing permissions`() {
        val parsed = FeedJson.detail(content)
        assertNull(parsed.publishedAt)
        assertEquals(Instant.parse("2026-11-11T15:00:00Z"), parsed.expiresAt)
        assertFalse(parsed.canSpeak(Instant.parse("2026-11-11T13:00:00Z")))
        assertEquals("", parsed.brief)
    }
    @Test fun `malformed required fields do not become an empty feed`() {
        for (bad in listOf("{}", "[]", "not json", """{"top3":[],"queue":[],"alerts":[],"data_mode":"MOCK"}""")) {
            assertThrows(ContractException::class.java) { FeedJson.feed(bad) }
        }
        assertThrows(ContractException::class.java) { FeedJson.detail(content.replace("2026-11-12T00:00:00+09:00", "2026-11-12T00:00:00")) }
    }
    @Test fun `empty feed is successful`() {
        assertTrue(FeedJson.feed("""{"top3":[],"queue":[],"alerts":[],"playback_order":[],"data_mode":"MOCK"}""").top3.isEmpty())
    }
    @Test fun `query and opaque id use proper encoding`() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            val api = HttpContentApi(server.url("/").toString())
            server.enqueue(MockResponse().setBody("""{"status":"ok","database":"ok","configured_data_mode":"MOCK"}"""))
            assertEquals("MOCK", api.health())
            assertEquals("/api/v1/health", server.takeRequest().path)
            server.enqueue(MockResponse().setBody("""{"top3":[],"queue":[],"alerts":[],"playback_order":[],"data_mode":"MOCK"}"""))
            api.feed(FeedQuery(37.57, 126.98, listOf("미술/전시", "science")))
            val url = server.takeRequest().requestUrl!!
            assertEquals(listOf("미술/전시", "science"), url.queryParameterValues("interests"))
            assertEquals("false", url.queryParameter("navigation_active"))
            assertNull(url.queryParameter("destination_lat"))
            assertNull(url.queryParameter("eta_minutes"))
            server.enqueue(MockResponse().setBody(content))
            api.detail("가/나 ?")
            assertEquals("가/나 ?", server.takeRequest().requestUrl!!.pathSegments.last())
        }
    }
    @Test fun `active destination sends a complete coordinate pair`() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            server.enqueue(MockResponse().setBody("""{"top3":[],"queue":[],"alerts":[],"playback_order":[],"data_mode":"MOCK"}"""))
            HttpContentApi(server.url("/").toString()).feed(
                FeedQuery(37.57, 126.98, listOf("art"), MapPoint(37.485, 127.036), etaMinutes = 25.5),
            )
            val url = server.takeRequest().requestUrl!!
            assertEquals("37.57", url.queryParameter("lat"))
            assertEquals("126.98", url.queryParameter("lon"))
            assertEquals("true", url.queryParameter("navigation_active"))
            assertEquals("37.485", url.queryParameter("destination_lat"))
            assertEquals("127.036", url.queryParameter("destination_lon"))
            assertEquals("25.5", url.queryParameter("eta_minutes"))
            assertNull(url.queryParameter("route_link_ids"))
        }
    }
    @Test fun `HTTP error status is preserved without raw body`() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            for (status in listOf(403, 404, 409, 422, 500)) {
                server.enqueue(MockResponse().setResponseCode(status).setBody("private server details"))
                try { HttpContentApi(server.url("/").toString()).health(); fail("expected failure") }
                catch (e: HttpFailure) { assertEquals(status, e.status); assertFalse(userMessage(e).contains("private")) }
            }
        }
    }
    @Test fun `invalid base urls are rejected`() {
        for (url in listOf("0.0.0.0", "http://0.0.0.0:8000", "http://user:secret@host", "https://host/api/v1", "https://host?key=secret")) {
            assertThrows(IllegalArgumentException::class.java) { HttpContentApi(url) }
        }
    }
}
