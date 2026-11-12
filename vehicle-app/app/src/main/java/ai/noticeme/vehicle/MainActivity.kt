package ai.noticeme.vehicle

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.content.res.ColorStateList
import android.text.TextUtils
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
import android.widget.ScrollView
import android.widget.TextView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

class MainActivity : Activity() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var controller: FeedController? = null
    private var refreshJob: Job? = null
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
    private val paper = Color.rgb(248, 247, 241)
    private val line = Color.rgb(220, 221, 210)
    private var shownFeed: Feed? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        speech = DeviceSpeechPlayer(this) { controller?.stop("다른 오디오 안내로 재생이 중단되었습니다. 다시 듣기를 누르세요.") }
        val root = column().apply {
            setBackgroundColor(paper)
            setPadding(dp(displaySize(22, 36)), dp(12), dp(displaySize(22, 36)), dp(12))
        }
        val settings = column().apply { visibility = View.GONE }
        val heading = row()
        heading.addView(label("Notice Me", displaySize(29, 46), ink, true), LinearLayout.LayoutParams(0, -2, 1f))
        heading.addView(button("설정") {
            settings.visibility = if (settings.visibility == View.VISIBLE) View.GONE else View.VISIBLE
        })
        root.addView(heading)
        root.addView(divider())

        val scroll = ScrollView(this).apply { isFillViewport = true }
        val body = column()
        scroll.addView(body)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))

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
        val feedHeading = row()
        feedHeading.addView(label("추천 소식", displaySize(22, 38), ink, true), LinearLayout.LayoutParams(0, -2, 1f))
        feedHeading.addView(button("새로고침") { connect() })
        body.addView(feedHeading)
        status = label("", displaySize(15, 27), muted)
        status.accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
        body.addView(status)
        locationStatus = label("", displaySize(14, 26), muted)
        body.addView(locationStatus)
        diagnostics = label("", displaySize(14, 27), muted)
        body.addView(diagnostics)
        stories = column()
        body.addView(stories)
        root.addView(divider())
        nowPlaying = label("재생 대기", displaySize(16, 28), ink)
        nowPlaying.maxLines = 2
        nowPlaying.ellipsize = TextUtils.TruncateAt.END
        root.addView(nowPlaying)
        val controls = row()
        play = button("재생", primary = true) { controller?.play() }
        next = button("패스") { controller?.next() }
        again = button("다시 듣기") { controller?.replay() }
        stop = button("중단") {
            refreshJob?.cancel()
            if (controller != null) controller?.stop() else render(ScreenState(message = "새로고침을 중단했습니다."))
        }
        listOf(play, next, again, stop).forEach {
            controls.addView(it, LinearLayout.LayoutParams(0, dp(displaySize(60, 96)), 1f))
        }
        root.addView(controls)
        setContentView(root)
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
        refreshJob?.cancel()
        controller?.stop()
        controller = null
        locationStatus.text = ""
        render(ScreenState(message = "설정이 변경되었습니다. 새로고침을 누르세요."))
    }

    private fun connect() {
        refreshJob?.cancel()
        controller?.stop()
        controller = null
        locationStatus.text = ""
        val withNavigation = useNavigation.isChecked
        val server = address.text.toString().trim()
        val manualLatitude = latitude.text.toString().toDoubleOrNull() ?: Double.NaN
        val manualLongitude = longitude.text.toString().toDoubleOrNull() ?: Double.NaN
        val selectedInterests = interests.text.toString().split(',').map { it.trim() }.filter { it.isNotEmpty() }
        render(ScreenState(busy = true, message = if (withNavigation) "내비 위치 확인 중…" else "서버에 연결 중…"))
        refreshJob = scope.launch {
            try {
                val api = HttpContentApi(server)
                val navigation = if (withNavigation) readNavigationContext(applicationContext) else null
                val query = FeedQuery(
                    navigation?.location?.latitude ?: manualLatitude,
                    navigation?.location?.longitude ?: manualLongitude,
                    selectedInterests,
                    navigation?.destination,
                )
                locationStatus.text = if (navigation == null) {
                    if (withNavigation) "내비 위치 확인 불가 · 설정 좌표 사용" else "설정 좌표 사용"
                } else {
                    buildString {
                        append(navigation.region ?: "내비 현재 위치")
                        navigation.destination?.let { append(" · 목적지 ").append(navigation.destinationName ?: "반영") }
                    }
                }
                getPreferences(MODE_PRIVATE).edit().putString("server", server).apply()
                controller = FeedController(api, query, speech, scope, render = ::render)
                controller?.connect()
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                render(ScreenState(message = userMessage(e)))
            }
        }
    }

    private fun render(state: ScreenState) {
        status.text = state.message
        locationStatus.visibility = if (locationStatus.text.isBlank()) View.GONE else View.VISIBLE
        play.isEnabled = state.connected && !state.busy && !state.playing
        next.isEnabled = state.connected && state.current != null
        again.isEnabled = next.isEnabled
        stop.isEnabled = state.busy || state.playing
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
                val story = column().apply { setPadding(0, dp(displaySize(12, 20)), 0, dp(displaySize(14, 29))) }
                val source = buildList {
                    add(item.sourceName)
                    if (item.dataMode == "MOCK" || item.verification == "SIMULATED") add("모의 자료")
                    if (!item.ttsEligible) add("읽기 전용")
                }.filter { it.isNotBlank() }.joinToString(" · ")
                story.addView(label(source, displaySize(14, 26), muted))
                story.addView(label(item.title, displaySize(22, 42), ink, true))
                if (item.brief.isNotBlank()) story.addView(label(item.brief, displaySize(17, 32), ink).apply {
                    setLineSpacing(dp(displaySize(2, 5)).toFloat(), 1f)
                })
                stories.addView(story)
            }
        }
        val alerts = state.feed?.alerts.orEmpty()
        diagnostics.text = alerts.joinToString("\n") {
            val simulation = if (it.verification == "SIMULATED" || it.dataMode == "MOCK") " (모의 자료)" else ""
            "우선 안내 · ${it.title}$simulation"
        }
        diagnostics.visibility = if (alerts.isEmpty()) View.GONE else View.VISIBLE
    }

    override fun onStop() {
        refreshJob?.cancel()
        if (controller == null) render(ScreenState())
        controller?.stop("앱이 화면에서 벗어나 재생을 중단했습니다.")
        super.onStop()
    }
    override fun onDestroy() { scope.cancel(); super.onDestroy() }
    private val wideScreen: Boolean
        get() = resources.configuration.screenWidthDp >= 840

    private fun displaySize(compact: Int, wide: Int): Int = if (wideScreen) wide else compact

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
    private fun button(text: String, primary: Boolean = false, action: () -> Unit) = Button(this).apply {
        this.text = text
        isAllCaps = false
        textSize = displaySize(14, 29).toFloat()
        minHeight = dp(displaySize(54, 82))
        minWidth = dp(displaySize(56, 128))
        elevation = 0f
        stateListAnimator = null
        backgroundTintList = ColorStateList(
            arrayOf(intArrayOf(-android.R.attr.state_enabled), intArrayOf()),
            intArrayOf(line, if (primary) accent else line),
        )
        setTextColor(ColorStateList(
            arrayOf(intArrayOf(-android.R.attr.state_enabled), intArrayOf()),
            intArrayOf(muted, if (primary) Color.WHITE else ink),
        ))
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
