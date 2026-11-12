package ai.noticeme.vehicle

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.launch
import java.time.Instant

class SpeechFailure(message: String) : Exception(message)
interface SpeechPlayer { suspend fun speak(text: String, allowed: () -> Boolean) }

data class ScreenState(
    val feed: Feed? = null, val connected: Boolean = false, val busy: Boolean = false,
    val playing: Boolean = false, val current: Content? = null,
    val message: String = "새로고침을 눌러 소식을 불러오세요.",
)

/** All commands and callbacks are confined to the supplied UI scope. */
class FeedController(
    private val api: ContentApi, private val query: FeedQuery, private val speech: SpeechPlayer,
    private val scope: CoroutineScope, private val now: () -> Instant = Instant::now,
    private val currentQuery: suspend () -> FeedQuery = { query },
    private val render: (ScreenState) -> Unit,
) {
    var state = ScreenState()
        private set
    private var job: Job? = null
    private var generation = 0
    private val consumed = mutableSetOf<String>()
    private fun update(value: ScreenState) { state = value; render(value) }
    private fun cancel() { generation++; job?.cancel(); job = null }

    fun connect() {
        cancel()
        consumed.clear()
        update(ScreenState(busy = true, message = "서버 상태 확인 중…"))
        job = scope.launch {
            try {
                api.health()
                update(state.copy(message = "추천 소식을 불러오는 중…"))
                val feed = api.feed(currentQuery())
                update(ScreenState(feed, connected = true,
                    message = when (feed.dataMode) {
                        "MOCK" -> "시연 데이터"
                        "MIXED" -> "실제 소식과 시연 데이터"
                        else -> "연결됨"
                    }))
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { update(ScreenState(message = userMessage(e))) }
        }
    }

    fun refreshWhenIdle() {
        if (!state.connected || state.busy || state.playing || job?.isActive == true) return
        job = scope.launch {
            try {
                update(state.copy(feed = api.feed(currentQuery())))
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                update(state.copy(message = userMessage(e)))
            }
        }
    }

    fun play() {
        if (!state.connected || state.busy || state.playing) return
        consumed.clear()
        begin(null)
    }
    fun next() {
        if (!state.connected || state.current == null) return
        consumed += state.current!!.id
        begin(null)
    }
    fun replay() {
        if (!state.connected) return
        val id = state.current?.id ?: return
        begin(id)
    }
    fun stop(message: String = "재생을 중단했습니다.") {
        cancel()
        update(state.copy(busy = false, playing = false, message = message))
    }

    private fun begin(replayId: String?) {
        cancel()
        val token = generation
        update(state.copy(busy = true, playing = false, message = "재생할 소식 확인 중…"))
        job = scope.launch {
            try {
                var requestedId = replayId
                while (token == generation) {
                    // Never continue a cached queue on network failure, including replay/skip.
                    val feed = api.feed(currentQuery())
                    update(state.copy(feed = feed))
                    val item = feed.candidates().firstOrNull {
                        (if (requestedId != null) it.id == requestedId else it.id !in consumed) && it.canSpeak(now())
                    }
                    if (item == null) {
                        update(state.copy(busy = false, playing = false, message =
                            if (requestedId != null) "이 항목은 더 이상 재생할 수 없습니다." else "재생할 소식이 없습니다. 새로 연결해 확인하세요."))
                        return@launch
                    }
                    update(state.copy(current = item, busy = true, playing = false))
                    val detail = try { api.detail(item.id) } catch (e: HttpFailure) {
                        if (e.status !in setOf(403, 404, 409)) throw e
                        consumed += item.id
                        if (requestedId != null) {
                            update(state.copy(busy = false, message = userMessage(e)))
                            return@launch
                        }
                        continue
                    }
                    if (detail.id != item.id) throw ContractException()
                    if (!item.canSpeak(now()) || !detail.canSpeak(now())) {
                        consumed += item.id
                        if (requestedId != null) {
                            update(state.copy(busy = false, message = "음성 권한 또는 유효기간이 변경되어 재생하지 않습니다."))
                            return@launch
                        }
                        continue
                    }
                    update(state.copy(current = detail, busy = false, playing = true,
                        message = "재생 중"))
                    speech.speak(detail.brief) { item.canSpeak(now()) && detail.canSpeak(now()) }
                    if (token != generation) return@launch
                    consumed += item.id
                    requestedId = null
                    update(state.copy(busy = true, playing = false, message = "다음 소식 확인 중…"))
                }
            } catch (_: TimeoutCancellationException) {
                update(state.copy(busy = false, playing = false, message = "음성 엔진 응답 시간이 초과되었습니다. 다시 듣기를 눌러 재시도하세요."))
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) {
                if (token == generation) update(state.copy(busy = false, playing = false,
                    connected = e is SpeechFailure, feed = if (e is SpeechFailure) state.feed else null,
                    message = userMessage(e)))
            }
        }
    }
}
