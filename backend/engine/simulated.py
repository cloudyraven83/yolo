"""模拟识别通道（默认）。

真实检测由"演示场景注入"（POST /api/demo/scenario）驱动，
事件直接写入 recognition_log（counted=True），本 Provider 仅作为
通道标识与状态占位，保证业务闭环与模型能力解耦、可确定性验收。
"""

from .detector import DetectionProvider


class SimulatedProvider(DetectionProvider):
    name = "simulated"

    def __init__(self):
        self._loaded = False

    def load(self, cfg: dict = None) -> None:
        self._loaded = True

    def detect(self, frame) -> list:
        return []

    def status(self) -> dict:
        return {
            "name": self.name,
            "available": True,
            "desc": "模拟识别通道：由演示场景注入确定性拿走事件",
        }
