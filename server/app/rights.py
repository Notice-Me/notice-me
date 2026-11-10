from .models import Content, RightsStatus, Verification


def tts_allowed(item: Content) -> bool:
    return (
        item.rights_status == RightsStatus.TTS_ALLOWED
        and item.rights_evidence_url is not None
        and item.verification_status in (Verification.VERIFIED, Verification.SIMULATED)
    )
