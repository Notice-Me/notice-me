package ai.noticeme.vehicle

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test
import java.io.IOException
import java.time.Instant

private val instant = Instant.parse("2026-11-11T12:00:00Z")
internal fun item(id: String = "a") = Content(id, "제목 $id", "본문 $id", "공공 출처", "https://example.org/source",
    "LIFE", "MOCK", "SIMULATED", true, "TTS_ALLOWED", "https://example.org/license",
    instant.plusSeconds(3600), instant.minusSeconds(30), null, null)
internal fun feed(vararg items: Content) = Feed(items.take(3), items.toList(), emptyList(), items.map { it.id }, "MOCK", emptyList())

private class FakeApi(var latest: Feed = feed(item(), item("b"))) : ContentApi {
    val calls = mutableListOf<String>()
    var detailOverride: Content? = null
    var failure: Exception? = null
    var detailFailure: HttpFailure? = null
    var detailGate: CompletableDeferred<Unit>? = null
    override suspend fun health(): String { calls += "health"; failure?.let { throw it }; return "MOCK" }
    override suspend fun feed(query: FeedQuery): Feed { calls += "feed"; failure?.let { throw it }; return latest }
    override suspend fun detail(id: String): Content {
        calls += "detail:$id"
        detailGate?.await()
        detailFailure?.let { if (id == "a") throw it }
        return detailOverride ?: latest.candidates().first { it.id == id }
    }
}
private class FakeSpeech : SpeechPlayer {
    val spoken = mutableListOf<String>()
    var stopped = 0
    var finish = CompletableDeferred<Unit>()
    override suspend fun speak(text: String, allowed: () -> Boolean) {
        check(allowed())
        spoken += text
        try { finish.await() } finally { stopped++ }
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class FeedControllerTest {
    @Test fun `idle refresh failure clears old cards and playback permission`() = runTest {
        val api = FakeApi(); val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent()
        api.failure = IOException("offline")
        c.refreshWhenIdle(); runCurrent()
        assertFalse(c.state.connected)
        assertNull(c.state.feed)
        c.play(); runCurrent()
        assertTrue(speech.spoken.isEmpty())
    }
    @Test fun `health precedes feed and no autoplay`() = runTest {
        val api = FakeApi(); val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(37.57, 126.98, listOf("art")), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent()
        assertEquals(listOf("health", "feed"), api.calls)
        assertEquals(2, c.state.feed!!.top3.size)
        assertTrue(c.state.connected)
        assertTrue(speech.spoken.isEmpty())
    }
    @Test fun `alerts use playback order and completion advances with fresh feed`() = runTest {
        val a = item("alert"); val b = item("b")
        val api = FakeApi(Feed(listOf(b), listOf(b), listOf(a), listOf("alert", "b"), "MOCK", emptyList()))
        val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent(); c.play(); runCurrent()
        assertEquals(listOf("본문 alert"), speech.spoken)
        val completed = speech.finish
        speech.finish = CompletableDeferred()
        completed.complete(Unit); runCurrent()
        assertEquals(listOf("본문 alert", "본문 b"), speech.spoken)
        assertEquals(listOf("health", "feed", "feed", "detail:alert", "feed", "detail:b"), api.calls)
        c.stop()
    }
    @Test fun `replay revalidates and pass stops before next`() = runTest {
        val api = FakeApi(); val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent(); c.play(); runCurrent(); c.replay(); runCurrent()
        assertEquals(listOf("본문 a", "본문 a"), speech.spoken)
        assertEquals(1, speech.stopped)
        c.next(); runCurrent()
        assertEquals(listOf("본문 a", "본문 a", "본문 b"), speech.spoken)
        assertEquals(2, speech.stopped)
        assertEquals(4, api.calls.count { it == "feed" })
        c.stop(); runCurrent(); assertEquals(3, speech.stopped)
    }
    @Test fun `empty fresh feed never reuses previous queue`() = runTest {
        val api = FakeApi(); val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent(); api.latest = feed(); c.play(); runCurrent()
        assertTrue(speech.spoken.isEmpty()); assertFalse(c.state.playing)
        assertTrue(c.state.feed!!.top3.isEmpty())
    }
    @Test fun `network failure during replay stops and requires reconnection`() = runTest {
        val api = FakeApi(); val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent(); c.play(); runCurrent()
        api.failure = IOException("offline"); c.replay(); runCurrent()
        assertEquals(1, speech.spoken.size); assertEquals(1, speech.stopped)
        assertFalse(c.state.connected); assertNull(c.state.feed)
    }
    @Test fun `revoked detail and removed replay candidate cannot speak`() = runTest {
        val api = FakeApi(); val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent(); c.play(); runCurrent()
        api.detailOverride = item().copy(ttsEligible = false)
        c.replay(); runCurrent()
        assertEquals(1, speech.spoken.size); assertFalse(c.state.playing)
        api.latest = feed(item("b")); c.replay(); runCurrent()
        assertEquals(1, speech.spoken.size)
    }
    @Test fun `blocked detail is skipped and feed refreshed`() = runTest {
        for (status in listOf(403, 404, 409)) {
            val api = FakeApi().apply { detailFailure = HttpFailure(status) }; val speech = FakeSpeech()
            val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
            c.connect(); runCurrent(); c.play(); runCurrent()
            assertEquals(listOf("본문 b"), speech.spoken)
            assertEquals(3, api.calls.count { it == "feed" })
            c.stop(); runCurrent()
        }
    }
    @Test fun `cancel while detail in flight prevents late playback`() = runTest {
        val gate = CompletableDeferred<Unit>()
        val api = FakeApi().apply { detailGate = gate }; val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent(); c.play(); runCurrent(); c.stop(); gate.complete(Unit); runCurrent()
        assertTrue(speech.spoken.isEmpty()); assertFalse(c.state.playing)
    }
    @Test fun `rapid pass and replay do not overlap or revive obsolete requests`() = runTest {
        val api = FakeApi(); val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent(); c.play(); runCurrent()
        c.next(); c.next(); c.replay(); runCurrent()
        assertEquals(2, speech.spoken.size)
        assertEquals(1, speech.stopped)
        c.stop()
    }
    @Test fun `mismatching detail id fails closed`() = runTest {
        val api = FakeApi().apply { detailOverride = item("wrong") }; val speech = FakeSpeech()
        val c = FeedController(api, FeedQuery(0.0, 0.0, emptyList()), speech, backgroundScope, { instant }) {}
        c.connect(); runCurrent(); c.play(); runCurrent()
        assertTrue(speech.spoken.isEmpty()); assertFalse(c.state.connected)
    }
    @Test fun `top3 alone and ambiguous ids are excluded`() {
        val a = item()
        assertTrue(Feed(listOf(a), emptyList(), emptyList(), listOf("a"), "MOCK", emptyList()).candidates().isEmpty())
        assertTrue(Feed(emptyList(), listOf(a), listOf(a), listOf("a"), "MOCK", emptyList()).candidates().isEmpty())
        assertEquals(1, feed(a).copy(playbackOrder = listOf("a", "a", "missing")).candidates().size)
    }
    @Test fun `rights expiry future and stale traffic are rejected`() {
        val a = item()
        assertTrue(a.canSpeak(instant))
        for (blocked in listOf(a.copy(brief = ""), a.copy(rightsEvidence = null),
            a.copy(rightsStatus = "LINK_ONLY"), a.copy(ttsEligible = false), a.copy(verification = "UNVERIFIED"),
            a.copy(dataMode = "LIVE"), a.copy(expiresAt = instant), a.copy(isExpired = true),
            a.copy(publishedAt = instant.plusSeconds(1)), a.copy(fetchedAt = instant.plusSeconds(1)),
            a.copy(contentType = "TRAFFIC"))) assertFalse(blocked.canSpeak(instant))
        val traffic = a.copy(contentType = "TRAFFIC", traffic = Traffic(instant.minusSeconds(10), instant.plusSeconds(60), "ACTIVE"))
        assertTrue(traffic.canSpeak(instant))
        assertFalse(traffic.copy(fetchedAt = instant.minusSeconds(601)).canSpeak(instant))
        assertFalse(traffic.copy(traffic = traffic.traffic!!.copy(status = "CLEARED")).canSpeak(instant))
        assertFalse(traffic.canSpeak(instant.plusSeconds(60)))
    }
}
