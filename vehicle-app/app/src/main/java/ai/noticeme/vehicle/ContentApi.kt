package ai.noticeme.vehicle

import kotlinx.coroutines.suspendCancellableCoroutine
import okhttp3.Call
import okhttp3.Callback
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

interface ContentApi {
    suspend fun health(): String
    suspend fun feed(query: FeedQuery): Feed
    suspend fun detail(id: String): Content
}
class HttpFailure(val status: Int) : IOException("HTTP $status")

class HttpContentApi(baseUrl: String) : ContentApi {
    private val base = baseUrl.trim().toHttpUrlOrNull()?.also {
        require(it.username.isEmpty() && it.password.isEmpty() && it.query == null &&
            it.fragment == null && it.encodedPath == "/" && it.host != "0.0.0.0") {
            "서버 주소만 입력하세요. 예: http://10.0.2.2:8000"
        }
    } ?: throw IllegalArgumentException("http:// 또는 https://로 시작하는 서버 주소를 입력하세요.")
    private val client = OkHttpClient.Builder().connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS).callTimeout(15, TimeUnit.SECONDS)
        .followRedirects(false).followSslRedirects(false).build()

    override suspend fun health() = FeedJson.health(get(endpoint("health").build()))
    override suspend fun feed(query: FeedQuery): Feed {
        val url = endpoint("feed").addQueryParameter("lat", query.latitude.toString())
            .addQueryParameter("lon", query.longitude.toString())
            .addQueryParameter("navigation_active", (query.destination != null).toString())
        query.destination?.let {
            url.addQueryParameter("destination_lat", it.latitude.toString())
            url.addQueryParameter("destination_lon", it.longitude.toString())
        }
        query.etaMinutes?.let { url.addQueryParameter("eta_minutes", it.toString()) }
        query.interests.forEach { url.addQueryParameter("interests", it) }
        return FeedJson.feed(get(url.build()))
    }
    override suspend fun detail(id: String) =
        FeedJson.detail(get(endpoint("contents").addPathSegment(id).build()))
    private fun endpoint(name: String) = base.newBuilder().addPathSegments("api/v1").addPathSegment(name)
    private suspend fun get(url: HttpUrl): String = suspendCancellableCoroutine { continuation ->
        val call = client.newCall(Request.Builder().url(url).header("Accept", "application/json").build())
        continuation.invokeOnCancellation { call.cancel() }
        call.enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                if (continuation.isActive) continuation.resumeWithException(e)
            }
            override fun onResponse(call: Call, response: Response) {
                val result = runCatching {
                    response.use {
                        if (it.code != 200) throw HttpFailure(it.code)
                        it.body?.string() ?: throw ContractException()
                    }
                }
                if (continuation.isActive) result.fold(continuation::resume, continuation::resumeWithException)
            }
        })
    }
}

fun userMessage(error: Exception): String = when (error) {
    is HttpFailure -> when (error.status) {
        403 -> "HTTP 403 · 음성 이용 권한이 없어 재생하지 않습니다."
        404 -> "HTTP 404 · 콘텐츠 또는 API 주소를 찾을 수 없습니다."
        409 -> "HTTP 409 · 만료되거나 갱신된 정보입니다. 새로 연결하세요."
        422 -> "HTTP 422 · 좌표와 관심사 요청 형식을 확인하세요."
        else -> "HTTP ${error.status} · 서버 응답을 확인한 뒤 다시 연결하세요."
    }
    is ContractException, is IllegalArgumentException, is SpeechFailure -> error.message ?: "처리할 수 없습니다."
    is IOException -> "서버 연결 실패 · 주소, 동일 네트워크, 포트와 debug HTTP 허용 주소를 확인하세요."
    else -> "처리 중 오류가 발생했습니다. 다시 연결하세요."
}
