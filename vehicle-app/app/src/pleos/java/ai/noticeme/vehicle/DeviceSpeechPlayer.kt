package ai.noticeme.vehicle

import android.content.Context
import android.os.Handler
import android.os.Looper
import ai.pleos.playground.tts.TextToSpeech
import ai.pleos.playground.tts.constant.ErrorType
import ai.pleos.playground.tts.constant.Mode
import ai.pleos.playground.tts.listener.EventListener
import ai.pleos.playground.tts.listener.OnInitializeListener
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.withTimeout
import java.util.Locale

class DeviceSpeechPlayer(private val context: Context, private val onFocusLoss: () -> Unit) : SpeechPlayer {
    val label = "Pleos · 기기 내 한국어 TTS"
    override suspend fun speak(text: String, allowed: () -> Boolean) {
        // A fresh SDK session isolates delayed stop/done events from a skipped utterance.
        val tts = TextToSpeech(context.applicationContext, Mode.ON_DEVICE)
        val initialized = CompletableDeferred<Unit>()
        val finished = CompletableDeferred<Unit>()
        val main = Handler(Looper.getMainLooper())
        val focus = AudioFocus(context, onFocusLoss)
        val listener = object : EventListener {
            override fun onReady() = Unit
            override fun onStart() = Unit
            override fun onUpdatedRms(rms: Double) = Unit
            override fun onDone() { main.post { finished.complete(Unit) } }
            override fun onStop() { main.post { finished.completeExceptionally(SpeechFailure("음성 재생이 중단되었습니다.")) } }
            override fun onError(errorType: ErrorType) {
                main.post { finished.completeExceptionally(SpeechFailure("Pleos TTS 오류: $errorType")) }
            }
        }
        try {
            tts.initialize(object : OnInitializeListener {
                override fun onSuccess() { main.post { initialized.complete(Unit) } }
                override fun onFailure(errorType: ErrorType) {
                    main.post { initialized.completeExceptionally(SpeechFailure("Pleos TTS 초기화 실패: $errorType · Pleos 기기와 TTS 권한을 확인하세요.")) }
                }
            })
            withTimeout(10_000) { initialized.await() }
            tts.addEventListener(listener)
            tts.setLocale(Locale.KOREA)
            tts.setAudioAttributes(speechAttributes)
            focus.acquire()
            if (!allowed()) throw SpeechFailure("정보가 만료되어 재생하지 않습니다. 새로 연결하세요.")
            tts.speak(text, true)
            withTimeout(300_000) { finished.await() }
        } finally {
            // Also runs on skip, replay, backgrounding, timeout and focus loss.
            runCatching { tts.removeEventListener(listener) }
            runCatching { tts.stop() }
            runCatching { tts.release() }
            focus.release()
        }
    }
}
