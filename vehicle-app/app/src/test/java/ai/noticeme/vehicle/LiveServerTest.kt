package ai.noticeme.vehicle

import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.time.Instant

/** Opt-in contract test against a running MOCK server. This does not verify vehicle audio. */
class LiveServerTest {
    @Test fun `real health feed and detail match the Android client contract`() = runBlocking {
        val base = System.getenv("NOTICE_TEST_BASE_URL")
        assumeTrue("Set NOTICE_TEST_BASE_URL for the local MOCK server integration test", !base.isNullOrBlank())
        val api = HttpContentApi(base!!)
        assertEquals("MOCK", api.health())
        val feed = api.feed(FeedQuery(37.57, 126.98, listOf("art", "science", "weather")))
        assertEquals(3, feed.top3.size)
        assertTrue(feed.candidates().isNotEmpty())
        for (candidate in feed.candidates()) {
            val detail = api.detail(candidate.id)
            assertEquals(candidate.id, detail.id)
            assertTrue(candidate.canSpeak(Instant.now()))
            assertTrue(detail.canSpeak(Instant.now()))
            assertTrue(detail.brief.isNotBlank())
        }
    }
}
