"""摄像头管理：后端独占采集 + MJPEG 预览流。

OpenCV 懒加载：未安装或摄像头不可用时，预览流输出"摄像头不可用"占位帧，
不影响其余业务（符合验收 S5 的兜底要求）。
"""

import threading
import time

from app.core.config import CAMERA_HEIGHT, CAMERA_ID, CAMERA_WIDTH, JPEG_QUALITY

try:
    import cv2
    import numpy as np
except Exception:  # noqa: BLE001
    cv2 = None
    np = None


class CameraManager:
    _instance = None

    def __init__(self):
        self.cap = None
        self.lock = threading.Lock()
        self.camera_id = CAMERA_ID

    @classmethod
    def instance(cls) -> "CameraManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def read(self):
        """返回一帧 BGR 图像；摄像头不可用返回 None。"""
        if cv2 is None:
            return None
        with self.lock:
            if self.cap is None:
                self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            if not self.cap.isOpened():
                return None
            ok, frame = self.cap.read()
            return frame if ok else None

    def available(self) -> bool:
        return self.read() is not None

    def release(self):
        with self.lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None


def _placeholder_frame():
    img = np.zeros((CAMERA_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
    cv2.putText(
        img, "Camera unavailable (simulated mode)",
        (40, CAMERA_HEIGHT // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
        (0, 200, 255), 2, cv2.LINE_AA,
    )
    return img


def _overlay(frame, detections):
    for d in detections:
        try:
            x1, y1, x2, y2 = [int(v) for v in d.region.split(",")]
        except Exception:  # noqa: BLE001
            continue
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame, f"{d.label} {d.confidence:.2f}", (x1, max(0, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA,
        )
    return frame


def mjpeg_frames(get_provider, log_hook=None):
    """生成 MJPEG 帧流。

    get_provider(): 返回当前 DetectionProvider（会话未开启也应可预览）。
    log_hook(detections, frame_no): 会话开启且有检出时写识别日志（路由层节流）。
    """
    cam = CameraManager.instance()
    while True:
        if cv2 is None:
            time.sleep(1)
            continue
        frame = cam.read()
        if frame is None:
            frame = _placeholder_frame()
        provider = get_provider()
        detections = []
        try:
            if provider is not None and provider.status().get("available"):
                detections = provider.detect(frame)
                if detections:
                    frame = _overlay(frame, detections)
                    if log_hook:
                        log_hook(detections, getattr(provider, "frame_no", 0))
        except Exception:  # noqa: BLE001
            detections = []
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        if not ok:
            time.sleep(0.05)
            continue
        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
            + buf.tobytes()
            + b"\r\n"
        )
        time.sleep(0.06)  # ~15fps
