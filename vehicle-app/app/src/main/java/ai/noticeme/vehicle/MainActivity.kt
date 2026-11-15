package ai.noticeme.vehicle

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.content.res.ColorStateList
import android.text.TextUtils
import android.text.method.LinkMovementMethod
import android.text.util.Linkify
import android.os.Bundle
import android.text.Editable
import android.text.InputType
import android.text.TextWatcher
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

class MainActivity : Activity() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var controller: FeedController? = null
    private var navigationPoll: Job? = null
    private var etaLabel: String? = null
    private lateinit var tripSummary: LinearLayout
    private lateinit var queueStatus: TextView
    private lateinit var locationStatus: TextView
    private lateinit var useNavigation: CheckBox
    private lateinit var speech: DeviceSpeechPlayer
    private lateinit var status: TextView
    private lateinit var stories: LinearLayout
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
    private val ink = Color.rgb(39, 41, 35)
    private val muted = Color.rgb(91, 94, 82)
    private val accent = Color.rgb(76, 92, 52)
    private val line = Color.rgb(219, 220, 209)
    private val surface = Color.rgb(239, 239, 229)
    private val playerSurface = Color.rgb(38, 41, 33)
    private val playerControl = Color.rgb(63, 67, 54)
    private val playerInk = Color.rgb(245, 245, 235)
    private val playerMuted = Color.rgb(203, 208, 188)
    private var shownFeed: Feed? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        speech = DeviceSpeechPlayer(this) { controller?.stop("다른 오디오 안내로 재생이 중단되었습니다. 다시 듣기를 누르세요.") }
        setContentView(R.layout.activity_notice_feed)
        val root = findViewById<LinearLayout>(R.id.notice_root).apply {
            setBackgroundColor(Color.WHITE)
            setPadding(dp(displaySize(20, 36)), dp(displaySize(8, 14)), dp(displaySize(20, 36)), dp(12))
        }
        val settings = column().apply {
            visibility = View.GONE
            background = rounded(surface)
            setPadding(dp(16), dp(10), dp(16), dp(14))
        }
        val heading = row()
        heading.addView(label("Notice Me", displaySize(27, 42), ink, true), LinearLayout.LayoutParams(0, -2, 1f))
        heading.addView(headerButton("설정") {
            settings.visibility = if (settings.visibility == View.VISIBLE) View.GONE else View.VISIBLE
        })
        val header = findViewById<LinearLayout>(R.id.notice_header)
        header.addView(heading)
        val headerDivider = divider()
        (headerDivider.layoutParams as LinearLayout.LayoutParams).apply {
            topMargin = dp(10)
            bottomMargin = dp(10)
        }
        header.addView(headerDivider)
        val body = findViewById<LinearLayout>(R.id.notice_body)

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
        useNavigation = CheckBox(this).apply {
            text = "내비 위치 사용"
            textSize = displaySize(16, 26).toFloat()
            visibility = if (BuildConfig.FLAVOR == "pleos") View.VISIBLE else View.GONE
            isChecked = BuildConfig.FLAVOR == "pleos" && getPreferences(MODE_PRIVATE).getBoolean("useNavigation", true)
        }
        settings.addView(useNavigation)
        settings.addView(label("내비 위치를 받지 못하면 입력한 좌표를 사용합니다.", displaySize(14, 26), muted))
        settings.addView(label(speech.label, displaySize(14, 26), muted))
        body.addView(settings)
        tripSummary = column().apply {
            background = rounded(surface)
            setPadding(dp(16), dp(9), dp(16), dp(9))
        }
        locationStatus = label("", displaySize(16, 28), ink, true)
        queueStatus = label("", displaySize(14, 24), muted)
        tripSummary.addView(locationStatus)
        tripSummary.addView(queueStatus)
        body.addView(tripSummary, LinearLayout.LayoutParams(-1, -2).apply {
            topMargin = dp(12)
            bottomMargin = dp(6)
        })

        val feedHeading = row()
        feedHeading.addView(label("추천 소식", displaySize(22, 36), ink, true), LinearLayout.LayoutParams(0, -2, 1f))
        feedHeading.addView(headerButton("새로고침") { connect() })
        body.addView(feedHeading)
        status = label("", displaySize(14, 24), muted)
        status.accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
        body.addView(status)
        diagnostics = label("", displaySize(14, 26), accent)
        body.addView(diagnostics)
        stories = column()
        body.addView(stories)

        val player = findViewById<LinearLayout>(R.id.notice_player).apply {
            background = rounded(playerSurface)
            setPadding(dp(12), dp(8), dp(12), dp(10))
        }
        nowPlaying = label("재생 대기", displaySize(18, 25), playerMuted)
        nowPlaying.maxLines = 2
        nowPlaying.ellipsize = TextUtils.TruncateAt.END
        player.addView(nowPlaying)
        val controls = row()
        play = button("재생", primary = true, onPlayer = true) { controller?.play() }
        next = button("다음", onPlayer = true) { controller?.next() }
        again = button("다시 듣기", onPlayer = true) { controller?.replay() }
        stop = button("중단", onPlayer = true) { controller?.stop() }
        val actions = listOf(play, next, again, stop)
        val groups = if (windowWidth < 400) actions.chunked(2) else listOf(actions)
        groups.forEachIndexed { rowIndex, group ->
            val actionRow = if (rowIndex == 0) controls else row()
            group.forEachIndexed { index, control ->
                actionRow.addView(control, LinearLayout.LayoutParams(0, -2, 1f).apply {
                    if (index > 0) marginStart = dp(6)
                })
            }
            player.addView(actionRow, LinearLayout.LayoutParams(-1, -2).apply {
                if (rowIndex > 0) topMargin = dp(6)
            })
        }
        render(ScreenState())
        val invalidate = object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                invalidateFeed()
            }
            override fun afterTextChanged(s: Editable?) = Unit
        }
        listOf(address, latitude, longitude, interests).forEach { it.addTextChangedListener(invalidate) }
        useNavigation.setOnCheckedChangeListener { _, checked ->
            getPreferences(MODE_PRIVATE).edit().putBoolean("useNavigation", checked).apply()
            invalidateFeed()
        }
    }

    private fun invalidateFeed() {
        controller?.stop()
        controller = null
        locationStatus.text = ""
        etaLabel = null
        render(ScreenState(message = "설정이 변경되었습니다. 새로고침을 누르세요."))
    }

    private fun connect() {
        controller?.stop()
        controller = null
        locationStatus.text = ""
        etaLabel = null
        val withNavigation = useNavigation.isChecked
        val server = address.text.toString().trim()
        val manualLatitude = latitude.text.toString().toDoubleOrNull() ?: Double.NaN
        val manualLongitude = longitude.text.toString().toDoubleOrNull() ?: Double.NaN
        val selectedInterests = interests.text.toString().split(',').map { it.trim() }.filter { it.isNotEmpty() }
        try {
            val api = HttpContentApi(server)
            val manual = FeedQuery(manualLatitude, manualLongitude, selectedInterests)
            val queryProvider: suspend () -> FeedQuery = {
                val navigation = (if (withNavigation) readNavigationContext(applicationContext) else null)
                    ?.takeIf { it.isFresh(Instant.now()) }
                etaLabel = navigation?.remainingSeconds?.let { seconds ->
                    if (seconds < 60) "도착까지 1분 미만" else "도착까지 약 ${(seconds + 59) / 60}분"
                }
                locationStatus.text = if (navigation == null) {
                    if (withNavigation) "내비 위치 확인 불가 · 설정 좌표 사용" else "설정 좌표 사용"
                } else {
                    buildString {
                        append(navigation.region ?: "내비 현재 위치")
                        append(when (navigation.routeStatus) {
                            "INACTIVE" -> " · 경로 안내 없음"
                            "SIMULATED" -> " · 모의 주행"
                            "GUIDING" -> " · 경로 안내 중"
                            else -> " · 경로 정보 확인 불가"
                        })
                        navigation.destination?.let { append(" · 목적지 ").append(navigation.destinationName ?: "반영") }
                        if (navigation.destination != null && navigation.remainingSeconds == null) append(" · ETA 확인 불가")
                    }
                }
                navigation?.applyTo(manual, Instant.now()) ?: manual
            }
            getPreferences(MODE_PRIVATE).edit().putString("server", server).apply()
            controller = FeedController(api, manual, speech, scope, currentQuery = queryProvider, render = ::render)
            controller?.connect()
        } catch (e: Exception) {
            render(ScreenState(message = userMessage(e)))
        }
    }

    private fun render(state: ScreenState) {
        status.text = state.message
        queueStatus.text = state.feed?.let { feed ->
            etaLabel?.let { "$it · 음성 큐 ${feed.queue.size}건" }
        }.orEmpty()
        queueStatus.visibility = if (queueStatus.text.isBlank()) View.GONE else View.VISIBLE
        locationStatus.visibility = if (locationStatus.text.isBlank()) View.GONE else View.VISIBLE
        tripSummary.visibility = if (state.feed == null || locationStatus.text.isBlank()) View.GONE else View.VISIBLE
        play.isEnabled = state.connected && !state.busy && !state.playing
        next.isEnabled = state.connected && state.current != null
        again.isEnabled = next.isEnabled
        stop.isEnabled = state.busy || state.playing
        nowPlaying.setTextColor(if (state.playing) playerInk else playerMuted)
        nowPlaying.text = state.current?.let {
            "${if (state.playing) "듣는 중" else "선택한 소식"} · ${it.title}" +
                if (it.verification == "SIMULATED") " · 모의 자료" else ""
        } ?: "재생 대기"
        if (state.feed !== shownFeed || stories.childCount == 0) {
            shownFeed = state.feed
            stories.removeAllViews()
            if (state.feed?.top3.isNullOrEmpty()) {
                if (state.connected) stories.addView(label("추천할 소식이 없습니다.", 18, muted))
            } else state.feed!!.top3.forEach { item ->
                stories.addView(divider())
                val story = column().apply { setPadding(0, dp(displaySize(11, 16)), 0, dp(displaySize(13, 21))) }
                val source = buildList {
                    add(item.sourceName)
                    add(item.dataMode)
                    if ((item.dataMode == "MOCK" || item.verification == "SIMULATED") &&
                        !item.sourceName.contains("모의 자료")) add("모의 자료")
                    if (!item.ttsEligible) add("읽기 전용")
                }.filter { it.isNotBlank() }.joinToString(" · ")
                story.addView(label(source, displaySize(13, 23), muted))
                story.addView(label(item.title, displaySize(22, 40), ink, true).apply {
                    maxLines = 2
                    ellipsize = TextUtils.TruncateAt.END
                })
                item.weather?.let { weather ->
                    story.addView(label("고정 관측 지역 · ${weather.region}", displaySize(14, 26), muted))
                    story.addView(label("관측 ${displayTime(weather.observedAt)} · 유효 ${displayTime(item.expiresAt)}", displaySize(14, 24), muted))
                } ?: story.addView(label(
                    item.publishedAt?.let { "발행 ${displayTime(it)}" } ?: "수집 ${displayTime(item.fetchedAt)}",
                    displaySize(14, 24), muted))
                if (item.brief.isNotBlank() && item.contentType != "NEWS") story.addView(label(item.brief, displaySize(17, 30), ink).apply {
                    maxLines = 3
                    ellipsize = TextUtils.TruncateAt.END
                    setLineSpacing(dp(displaySize(2, 5)).toFloat(), 1f)
                })
                story.addView(label(item.sourceUrl, displaySize(14, 24), accent).apply {
                    maxLines = 1
                    ellipsize = TextUtils.TruncateAt.END
                    Linkify.addLinks(this, Linkify.WEB_URLS)
                    movementMethod = LinkMovementMethod.getInstance()
                })
                stories.addView(story)
            }
        }
        val alerts = state.feed?.alerts.orEmpty()
        val notices = alerts.map {
            val simulation = if (it.verification == "SIMULATED" || it.dataMode == "MOCK") " (모의 자료)" else ""
            "우선 안내 · ${it.title}$simulation"
        }
        val reasons = state.feed?.diagnostics.orEmpty().mapNotNull { diagnostic ->
            when (diagnostic.code) {
                "DRIVING_TIME_UNVERIFIED" -> "행사 · 자동차 이동시간 미확인으로 추천 제외"
                "SOURCE_UNAVAILABLE" -> "일부 원천 데이터 갱신 실패"
                "WEATHER_STALE_OR_FUTURE", "EXPIRED_OR_FUTURE" -> "유효기간을 확인할 수 없는 자료 제외"
                "LIVE_TTS_WEATHER_ONLY" -> "실제 음성 안내는 날씨만 제공"
                "TTS_RIGHTS_BLOCKED" -> "음성 권리 미확인 소식은 읽기 전용"
                else -> null
            }
        }
        val emptyVoice = if (state.connected && state.feed?.dataMode == "LIVE" && state.feed?.queue.isNullOrEmpty())
            listOf("재생 가능한 최신 날씨가 없습니다. 서버 수집 상태를 확인하세요.") else emptyList()
        val messages = (notices + reasons + emptyVoice).distinct()
        diagnostics.text = messages.joinToString("\n")
        diagnostics.visibility = if (messages.isEmpty()) View.GONE else View.VISIBLE
    }

    override fun onStart() {
        super.onStart()
        navigationPoll = scope.launch {
            while (isActive) {
                delay(15_000)
                if (useNavigation.isChecked) controller?.refreshWhenIdle()
            }
        }
    }

    override fun onStop() {
        navigationPoll?.cancel()
        navigationPoll = null
        if (controller == null) render(ScreenState())
        controller?.stop("앱이 화면에서 벗어나 재생을 중단했습니다.")
        super.onStop()
    }
    override fun onDestroy() { scope.cancel(); super.onDestroy() }
    private val windowWidth: Int
        get() = resources.configuration.screenWidthDp

    private fun displaySize(compact: Int, wide: Int): Int = when {
        windowWidth >= 1200 -> wide
        windowWidth >= 600 -> (compact + wide) / 2
        else -> compact
    }
    private fun displayTime(value: Instant): String =
        DateTimeFormatter.ofPattern("MM-dd HH:mm 'KST'").withZone(ZoneId.of("Asia/Seoul")).format(value)

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()
    private fun column() = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
    private fun row() = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
    private fun label(text: String, size: Int, color: Int, bold: Boolean = false) = TextView(this).apply {
        this.text = text; textSize = size.toFloat(); setTextColor(color)
        setPadding(0, dp(5), 0, dp(5))
        if (bold) {
            setTypeface(typeface, Typeface.BOLD)
            letterSpacing = -0.015f
        }
    }
    private fun divider() = View(this).apply {
        setBackgroundColor(line)
        layoutParams = LinearLayout.LayoutParams(-1, dp(1))
        importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
    }
    private fun rounded(color: Int) = GradientDrawable().apply {
        setColor(color)
        cornerRadius = dp(10).toFloat()
    }

    private fun headerButton(text: String, action: () -> Unit) = button(text, action = action).apply {
        // Both header actions reserve enough room for the longer label at the current font scale.
        minWidth = kotlin.math.ceil(paint.measureText("새로고침").toDouble()).toInt() +
            paddingLeft + paddingRight
    }

    private fun button(
        text: String,
        primary: Boolean = false,
        onPlayer: Boolean = false,
        action: () -> Unit,
    ) = Button(this).apply {
        this.text = text
        isAllCaps = false
        textSize = (if (onPlayer) displaySize(21, 30) else displaySize(14, 27)).toFloat()
        minHeight = dp(when {
            !onPlayer -> displaySize(48, 65)
            windowWidth < 400 -> 72
            else -> displaySize(88, 96)
        })
        minWidth = 0
        setPadding(dp(displaySize(8, 16)), 0, dp(displaySize(8, 16)), 0)
        elevation = 0f
        stateListAnimator = null
        val fill = when {
            primary -> accent
            onPlayer -> playerControl
            else -> surface
        }
        val disabledFill = if (onPlayer) playerSurface else surface
        val enabledText = if (onPlayer) playerInk else ink
        val disabledText = if (onPlayer) playerMuted else muted
        val states = arrayOf(intArrayOf(-android.R.attr.state_enabled), intArrayOf())
        val backgrounds = android.graphics.drawable.StateListDrawable().apply {
            addState(states[0], rounded(disabledFill))
            addState(states[1], rounded(fill))
        }
        background = RippleDrawable(ColorStateList.valueOf(0x247F8A73), backgrounds, null)
        backgroundTintList = null
        setTextColor(ColorStateList(states, intArrayOf(disabledText, enabledText)))
        setOnClickListener { action() }
    }
    private fun field(title: String, value: String, type: Int, parent: LinearLayout): EditText {
        parent.addView(label(title, displaySize(14, 26), muted))
        return EditText(this).apply {
            inputType = type; setSingleLine(true); setText(value); textSize = displaySize(17, 32).toFloat()
            minHeight = dp(displaySize(52, 76)); setTextColor(ink); contentDescription = title
            importantForAutofill = View.IMPORTANT_FOR_AUTOFILL_NO
            parent.addView(this, LinearLayout.LayoutParams(-1, -2))
        }
    }
}
