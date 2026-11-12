package ai.noticeme.vehicle

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.withTimeout
import java.util.Locale
import java.util.UUID

class DeviceSpeechPlayer(private val context: Context, private val onFocusLoss: () -> Unit) : SpeechPlayer {
    val label = "일반 Android · 기기 내 한국어 TTS (Pleos 검증 아님)"
    override suspend fun speak(text: String, allowed: () -> Boolean) {
        val initialized = CompletableDeferred<Int>()
        val finished = CompletableDeferred<Unit>()
        val main = Handler(Looper.getMainLooper())
        val tts = TextToSpeech(context.applicationContext) { result -> main.post { initialized.complete(result) } }
        val focus = AudioFocus(context, onFocusLoss)
        val id = UUID.randomUUID().toString()
        try {
            if (withTimeout(10_000) { initialized.await() } != TextToSpeech.SUCCESS)
                throw SpeechFailure("Android TTS 초기화 실패 · 기기의 TTS 엔진을 확인하세요.")
            val voice = tts.voices?.firstOrNull { it.locale.language == Locale.KOREAN.language && !it.isNetworkConnectionRequired }
                ?: throw SpeechFailure("기기 내 한국어 음성이 없습니다. Android TTS 설정에서 한국어 음성을 설치하세요.")
            if (tts.setVoice(voice) == TextToSpeech.ERROR) throw SpeechFailure("한국어 음성을 선택할 수 없습니다.")
            tts.setAudioAttributes(speechAttributes)
            tts.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) = Unit
                override fun onDone(utteranceId: String?) {
                    if (utteranceId == id) main.post { finished.complete(Unit) }
                }
                @Deprecated("Platform callback")
                override fun onError(utteranceId: String?) {
                    if (utteranceId == id) main.post { finished.completeExceptionally(SpeechFailure("Android TTS 재생에 실패했습니다.")) }
                }
                override fun onStop(utteranceId: String?, interrupted: Boolean) {
                    if (utteranceId == id) main.post { finished.completeExceptionally(SpeechFailure("음성 재생이 중단되었습니다.")) }
                }
            })
            focus.acquire()
            if (!allowed()) throw SpeechFailure("정보가 만료되어 재생하지 않습니다. 새로 연결하세요.")
            if (tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, id) == TextToSpeech.ERROR)
                throw SpeechFailure("Android TTS가 재생 요청을 거절했습니다.")
            withTimeout(300_000) { finished.await() }
        } finally {
            tts.setOnUtteranceProgressListener(null)
            tts.stop()
            tts.shutdown()
            focus.release()
        }
    }
}
