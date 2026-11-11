package ai.noticeme.vehicle

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.text.Editable
import android.text.InputType
import android.text.TextWatcher
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel

class MainActivity : Activity() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var controller: FeedController? = null
    private lateinit var speech: DeviceSpeechPlayer
    private lateinit var status: TextView
    private lateinit var mode: TextView
    private lateinit var cards: LinearLayout
    private lateinit var diagnostics: TextView
    private lateinit var nowPlaying: TextView
    private lateinit var play: Button
    private lateinit var next: Button
    private lateinit var again: Button
    private lateinit var stop: Button
    private lateinit var address: EditText
    private lateinit var latitude: EditText
    private lateinit var longitude: EditText
    private lateinit var interests: EditText
    private val ink = Color.rgb(234, 242, 245)
    private val muted = Color.rgb(162, 179, 189)
    private val accent = Color.rgb(153, 230, 179)
    private var shownFeed: Feed? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        speech = DeviceSpeechPlayer(this) { controller?.stop("다른 오디오 안내로 재생이 중단되었습니다. 다시 듣기를 누르세요.") }
        val root = column().apply { setPadding(dp(20), dp(16), dp(20), dp(12)) }
        val heading = row()
        heading.addView(label("Notice Me", 28, ink, true), LinearLayout.LayoutParams(0, -2, 1f))
        mode = label("연결 대기", 16, accent, true)
        heading.addView(mode)
        root.addView(heading)
        root.addView(label("내 주변의 소식, 듣기 편한 순서로", 16, muted))

        val scroll = ScrollView(this)
        val body = column()
        scroll.addView(body)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))

        val settings = column().apply { visibility = View.VISIBLE }
        body.addView(button("서버 · 시연 위치 설정") {
            settings.visibility = if (settings.visibility == View.VISIBLE) View.GONE else View.VISIBLE
        })
        address = field("서버 주소", getPreferences(MODE_PRIVATE).getString("server", "http://10.0.2.2:8000")!!,
            InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI, settings)
        val coordinates = row()
        val left = column(); val right = column()
        coordinates.addView(left, LinearLayout.LayoutParams(0, -2, 1f))
        coordinates.addView(right, LinearLayout.LayoutParams(0, -2, 1f))
        val decimal = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_FLAG_DECIMAL or InputType.TYPE_NUMBER_FLAG_SIGNED
        latitude = field("위도", "37.57", decimal, left)
        longitude = field("경도", "126.98", decimal, right)
        settings.addView(coordinates)
        interests = field("관심사 (쉼표로 구분)", "art,science,weather", InputType.TYPE_CLASS_TEXT, settings)
        settings.addView(label("광화문 시연 좌표 · GPS/내비 미연동 · 정차 상태에서 시험하세요.", 14, muted))
        body.addView(settings)
        body.addView(button("연결 / 새로고침") { connect() })
        status = label("", 16, accent)
        status.accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
        body.addView(status)
        body.addView(label("추천 TOP 3", 23, ink, true))
        cards = if (resources.configuration.screenWidthDp >= 840) row() else column()
        body.addView(cards)
        diagnostics = label("", 14, muted)
        body.addView(diagnostics)
        root.addView(label(speech.label, 13, muted))
        nowPlaying = label("재생 대기", 16, ink)
        nowPlaying.maxLines = 2
        root.addView(nowPlaying)
        val controls = row()
        play = button("재생") { controller?.play() }
        next = button("패스") { controller?.next() }
        again = button("다시 듣기") { controller?.replay() }
        stop = button("중단") { controller?.stop() }
        listOf(play, next, again, stop).forEach {
            controls.addView(it, LinearLayout.LayoutParams(0, dp(60), 1f))
        }
        root.addView(controls)
        setContentView(root)
        render(ScreenState())
        val invalidate = object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                controller?.stop()
                controller = null
                render(ScreenState(message = "설정이 변경되었습니다. 연결 / 새로고침을 누르세요."))
            }
            override fun afterTextChanged(s: Editable?) = Unit
        }
        listOf(address, latitude, longitude, interests).forEach { it.addTextChangedListener(invalidate) }
    }

    private fun connect() {
        controller?.stop()
        controller = null
        try {
            val query = FeedQuery(latitude.text.toString().toDoubleOrNull() ?: Double.NaN,
                longitude.text.toString().toDoubleOrNull() ?: Double.NaN,
                interests.text.toString().split(',').map { it.trim() }.filter { it.isNotEmpty() })
            val api = HttpContentApi(address.text.toString())
            getPreferences(MODE_PRIVATE).edit().putString("server", address.text.toString().trim()).apply()
            controller = FeedController(api, query, speech, scope, render = ::render)
            controller!!.connect()
        } catch (e: Exception) { render(ScreenState(message = userMessage(e))) }
    }

    private fun render(state: ScreenState) {
        status.text = state.message
        mode.text = state.feed?.dataMode ?: "연결 대기"
        play.isEnabled = state.connected && !state.busy && !state.playing
        next.isEnabled = state.connected && state.current != null
        again.isEnabled = next.isEnabled
        stop.isEnabled = state.busy || state.playing
        nowPlaying.text = state.current?.let {
            "${if (state.playing) "듣는 중" else "선택한 소식"} · ${it.title} · ${it.dataMode}" +
                if (it.verification == "SIMULATED") " · 모의 자료" else ""
        } ?: "재생 대기 · 재생 버튼을 눌러 시작하세요"
        if (state.feed !== shownFeed || cards.childCount == 0) {
            shownFeed = state.feed
            cards.removeAllViews()
            if (state.feed?.top3.isNullOrEmpty()) {
                cards.addView(label(if (state.connected) "지금 조건에 맞는 새 소식이 없습니다." else "서버에 연결하면 추천 카드가 표시됩니다.", 19, muted))
            } else state.feed!!.top3.forEachIndexed { index, item ->
                val card = column().apply {
                    setPadding(dp(18), dp(16), dp(18), dp(16))
                    background = GradientDrawable().apply { setColor(Color.rgb(28, 41, 51)); cornerRadius = dp(16).toFloat() }
                }
                card.addView(label("0${index + 1}   ${item.dataMode}" + if (item.verification == "SIMULATED") " · 모의 자료" else "", 14, accent, true))
                card.addView(label(item.title, 22, ink, true))
                card.addView(label(item.brief.ifBlank { "제목과 출처만 제공되는 소식입니다." }, 17, ink))
                card.addView(label(item.sourceName, 14, muted))
                card.addView(label(item.sourceUrl, 12, muted))
                card.addView(label(if (item.ttsEligible) "음성 재생 전 자격 재확인" else "화면 전용 · 음성 재생 불가", 13, accent))
                val params = if (cards.orientation == LinearLayout.HORIZONTAL)
                    LinearLayout.LayoutParams(0, -2, 1f) else LinearLayout.LayoutParams(-1, -2)
                params.setMargins(dp(3), dp(8), dp(3), dp(8))
                cards.addView(card, params)
            }
        }
        diagnostics.text = state.feed?.let { feed ->
            val alerts = if (feed.alerts.isEmpty()) "" else "우선 안내 ${feed.alerts.size}건 · " +
                feed.alerts.joinToString(" / ") { it.title + if (it.verification == "SIMULATED") " (모의 자료)" else "" } + "\n"
            alerts + feed.diagnostics.joinToString("\n") { "${it.code} · ${it.message}" }
        } ?: ""
    }

    override fun onStop() {
        controller?.stop("앱이 화면에서 벗어나 재생을 중단했습니다.")
        super.onStop()
    }
    override fun onDestroy() { scope.cancel(); super.onDestroy() }
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()
    private fun column() = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
    private fun row() = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
    private fun label(text: String, size: Int, color: Int, bold: Boolean = false) = TextView(this).apply {
        this.text = text; textSize = size.toFloat(); setTextColor(color)
        setPadding(0, dp(5), 0, dp(5))
        if (bold) setTypeface(typeface, Typeface.BOLD)
    }
    private fun button(text: String, action: () -> Unit) = Button(this).apply {
        this.text = text; isAllCaps = false; minHeight = dp(56)
        setOnClickListener { action() }
    }
    private fun field(title: String, value: String, type: Int, parent: LinearLayout): EditText {
        parent.addView(label(title, 14, muted))
        return EditText(this).apply {
            inputType = type; setSingleLine(true); setText(value); textSize = 17f
            minHeight = dp(52); setTextColor(ink); contentDescription = title
            importantForAutofill = View.IMPORTANT_FOR_AUTOFILL_NO
            parent.addView(this, LinearLayout.LayoutParams(-1, -2))
        }
    }
}
