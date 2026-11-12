package ai.noticeme.vehicle

import android.content.Context
import android.content.pm.PackageManager
import ai.pleos.playground.navi.constants.NaviMode
import ai.pleos.playground.navi.data.CurrentLocationInfo
import ai.pleos.playground.navi.data.DestinationInfo
import ai.pleos.playground.navi.data.RouteStateInfo
import ai.pleos.playground.navi.helper.NaviHelper
import ai.pleos.playground.navi.helper.listener.NaviHelperEventListener
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.withTimeoutOrNull

internal suspend fun readNavigationContext(context: Context): NavigationContext? {
    if (context.checkSelfPermission("pleos.car.permission.NAVI_ROUTE") != PackageManager.PERMISSION_GRANTED) return null

    val helper = try { NaviHelper(context) } catch (_: Exception) { return null }
    val connected = CompletableDeferred<Boolean>()
    val location = CompletableDeferred<CurrentLocationInfo>()
    val route = CompletableDeferred<RouteStateInfo>()
    val destination = CompletableDeferred<DestinationInfo>()
    val listener = object : NaviHelperEventListener {
        override fun onCurrentLocationInfo(currentLocationInfo: CurrentLocationInfo) {
            location.complete(currentLocationInfo)
        }

        override fun onRouteStateInfo(routeStateInfo: RouteStateInfo) {
            route.complete(routeStateInfo)
        }

        override fun onDestinationInfo(destinationInfo: DestinationInfo) {
            destination.complete(destinationInfo)
        }
    }
    var registered = false
    try {
        helper.initialize(onConnected = { connected.complete(true) }, onFailed = { connected.complete(false) })
        if (withTimeoutOrNull(2_500) { connected.await() } != true) return null
        helper.addListener(listener)
        registered = true
        helper.getCurrentLocationInfo()
        val current = withTimeoutOrNull(2_000) { location.await() } ?: return null
        val point = coordinates(current.latitude, current.longitude) ?: return null
        val region = current.address?.trim()?.takeIf { it.isNotEmpty() }
            ?.split(Regex("\\s+"))?.take(2)?.joinToString(" ")
        val target = withTimeoutOrNull(1_500) {
            helper.getRouteStateInfo()
            val mode = route.await().naviMode
            if (mode != NaviMode.ROUTE_GUIDING && mode != NaviMode.SIMULATION_GUIDING) return@withTimeoutOrNull null
            helper.getDestinationInfo()
            destination.await()
        }
        val destinationPoint = target?.let { coordinates(it.latitude, it.longitude) }
        return NavigationContext(
            point, region, destinationPoint, target?.name?.takeIf { it.isNotBlank() },
            target?.remainTime?.takeIf { destinationPoint != null && it in 0..86_400 },
        )
    } catch (e: CancellationException) {
        throw e
    } catch (_: Exception) {
        return null
    } finally {
        if (registered) runCatching { helper.removeListener(listener) }
        runCatching { helper.release() }
    }
}

private fun coordinates(latitude: Double, longitude: Double): MapPoint? {
    if (latitude == 0.0 && longitude == 0.0) return null
    return runCatching { MapPoint(latitude, longitude) }.getOrNull()
}
