package ai.noticeme.vehicle

import com.google.gson.JsonObject
import com.google.gson.JsonParser
import java.time.Instant
import java.time.OffsetDateTime

data class FeedQuery(val latitude: Double, val longitude: Double, val interests: List<String>) {
    init {
        require(latitude.isFinite() && latitude in -90.0..90.0) { "위도는 -90~90이어야 합니다." }
        require(longitude.isFinite() && longitude in -180.0..180.0) { "경도는 -180~180이어야 합니다." }
        require(interests.size <= 30) { "관심사는 30개 이하로 입력하세요." }
    }
}

data class Traffic(val occurredAt: Instant, val validUntil: Instant, val status: String)
data class Content(
    val id: String, val title: String, val brief: String, val sourceName: String,
    val sourceUrl: String, val contentType: String, val dataMode: String,
    val verification: String, val ttsEligible: Boolean, val rightsStatus: String,
    val rightsEvidence: String?, val expiresAt: Instant, val fetchedAt: Instant,
    val publishedAt: Instant?, val traffic: Traffic?, val isExpired: Boolean = false,
) {
    fun canSpeak(now: Instant): Boolean =
        ttsEligible && !isExpired && brief.isNotBlank() && rightsStatus == "TTS_ALLOWED" &&
            !rightsEvidence.isNullOrBlank() && verification in setOf("VERIFIED", "SIMULATED") &&
            dataMode in setOf("LIVE", "MOCK") && (verification != "SIMULATED" || dataMode == "MOCK") &&
            expiresAt > now && (publishedAt == null || publishedAt <= now) && fetchedAt <= now &&
            (contentType != "TRAFFIC" || (traffic != null && traffic.status == "ACTIVE" &&
                traffic.occurredAt <= now && now < traffic.validUntil &&
                fetchedAt >= now.minusSeconds(600)))
}
data class Diagnostic(val code: String, val message: String)
data class Feed(
    val top3: List<Content>, val queue: List<Content>, val alerts: List<Content>,
    val playbackOrder: List<String>, val dataMode: String, val diagnostics: List<Diagnostic>,
) {
    // Only queue/alerts grant eligibility. A display-only card is never a fallback.
    fun candidates(): List<Content> {
        val grouped = (alerts + queue).groupBy { it.id }
        return playbackOrder.distinct().mapNotNull { id -> grouped[id]?.singleOrNull() }
    }
}

class ContractException : Exception("API 응답 형식이 연동 계약과 다릅니다. 서버 응답을 확인하세요.")

object FeedJson {
    private fun JsonObject.text(key: String): String = get(key)?.let {
        if (!it.isJsonPrimitive || !it.asJsonPrimitive.isString) throw ContractException()
        it.asString
    } ?: throw ContractException()
    private fun JsonObject.optionalText(key: String): String? =
        if (!has(key) || get(key).isJsonNull) null else text(key)
    private fun JsonObject.flag(key: String, default: Boolean = false): Boolean = get(key)?.let {
        if (!it.isJsonPrimitive || !it.asJsonPrimitive.isBoolean) throw ContractException()
        it.asBoolean
    } ?: default
    private fun JsonObject.time(key: String): Instant = OffsetDateTime.parse(text(key)).toInstant()
    private fun JsonObject.list(key: String) = getAsJsonArray(key) ?: throw ContractException()
    private inline fun <T> parse(raw: String, block: (JsonObject) -> T): T = try {
        block(JsonParser.parseString(raw).asJsonObject)
    } catch (_: Exception) { throw ContractException() }

    fun health(raw: String): String = parse(raw) {
        if (it.text("status") != "ok" || it.text("database") != "ok") throw ContractException()
        it.text("configured_data_mode")
    }
    fun feed(raw: String): Feed = parse(raw) { o ->
        val cards = o.list("top3").map { content(it.asJsonObject) }
        if (cards.size > 3) throw ContractException()
        Feed(cards, o.list("queue").map { content(it.asJsonObject) },
            o.list("alerts").map { content(it.asJsonObject) },
            o.list("playback_order").map {
                if (!it.isJsonPrimitive || !it.asJsonPrimitive.isString) throw ContractException()
                it.asString
            }, o.text("data_mode"),
            o.getAsJsonArray("diagnostics")?.map {
                Diagnostic(it.asJsonObject.text("code"), it.asJsonObject.text("message"))
            } ?: emptyList())
    }
    fun detail(raw: String): Content = parse(raw) { content(it) }
    private fun content(o: JsonObject): Content = with(o) {
        Content(text("id").also { if (it.isBlank()) throw ContractException() }, text("title"),
            optionalText("brief") ?: "", text("source_name"), text("source_url"), text("content_type"),
            text("data_mode"), optionalText("verification_status") ?: "UNVERIFIED", flag("tts_eligible"),
            optionalText("rights_status") ?: "LICENSE_UNVERIFIED", optionalText("rights_evidence_url"),
            time("expires_at"), time("fetched_at"),
            optionalText("published_at")?.let { OffsetDateTime.parse(it).toInstant() },
            get("traffic")?.takeUnless { it.isJsonNull }?.asJsonObject?.let {
                Traffic(it.time("occurred_at"), it.time("valid_until"), it.text("status"))
            }, flag("is_expired"))
    }
}
