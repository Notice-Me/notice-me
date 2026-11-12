from .models import Content, DataMode, RightsStatus, Verification


def tts_allowed(item: Content) -> bool:
    return (
        item.rights_status == RightsStatus.TTS_ALLOWED
        and item.rights_evidence_url is not None
        and item.verification_status in (Verification.VERIFIED, Verification.SIMULATED)
    )


def voice_allowed(item: Content) -> bool:
    """MVP playback scope: keep MOCK, allow only attributed Seoul weather in LIVE.

    This is narrower than license clearance. Destination ETA is not travel-time
    verification and this policy must not promote events into recommendations.
    """
    return tts_allowed(item) and (
        item.data_mode == DataMode.MOCK
        or (
            item.weather is not None
            and item.verification_status == Verification.VERIFIED
            and item.provenance.startswith("PUBLIC_API:seoul_citydata;")
        )
    )
