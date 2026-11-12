package ai.noticeme.vehicle

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.os.Handler
import android.os.Looper

val speechAttributes: AudioAttributes = AudioAttributes.Builder()
    .setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build()

class AudioFocus(context: Context, onLoss: () -> Unit) {
    private val manager = context.getSystemService(AudioManager::class.java)
    private var active = false
    private val request = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT)
        .setAudioAttributes(speechAttributes).setWillPauseWhenDucked(true)
        .setOnAudioFocusChangeListener({ change ->
            if (active && (change == AudioManager.AUDIOFOCUS_LOSS ||
                change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT ||
                change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK)) onLoss()
        }, Handler(Looper.getMainLooper())).build()
    fun acquire() {
        if (manager.requestAudioFocus(request) != AudioManager.AUDIOFOCUS_REQUEST_GRANTED)
            throw SpeechFailure("다른 오디오가 사용 중입니다. 잠시 뒤 다시 듣기를 누르세요.")
        active = true
    }
    fun release() { active = false; manager.abandonAudioFocusRequest(request) }
}
