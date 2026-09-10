import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..core.db import SessionLocal
from ..core.runtime import runtime
from ..models import RecognitionLog
from engine.camera import CameraManager, mjpeg_frames
from engine.detector import manager as provider_manager

router = APIRouter(prefix="/api/camera", tags=["camera"])


def _get_provider():
    try:
        return provider_manager.get(runtime.provider_name)
    except KeyError:
        return None


def _log_hook(detections, frame_no):
    """会话开启时写识别日志（1 秒节流，counted=False 仅作链路演示）。"""
    if runtime.session_id is None:
        return
    now = time.time()
    if now - runtime.last_log_ts < 1.0:
        return
    runtime.last_log_ts = now
    db = SessionLocal()
    try:
        for d in detections[:5]:  # 每秒最多 5 条，避免刷库
            db.add(RecognitionLog(
                session_id=runtime.session_id,
                frame_no=frame_no,
                provider=runtime.provider_name,
                label=d.label,
                confidence=d.confidence,
                region=d.region,
                counted=False,
            ))
        db.commit()
    finally:
        db.close()


@router.get("/stream")
def stream():
    return StreamingResponse(
        mjpeg_frames(_get_provider, _log_hook),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/status")
def status():
    return {
        "camera_available": CameraManager.instance().available(),
        "provider": runtime.provider_name,
    }
